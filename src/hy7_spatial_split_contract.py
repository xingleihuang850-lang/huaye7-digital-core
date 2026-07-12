#!/usr/bin/env python3
"""Plan and validate future HY7 spatially separated crop splits.

This utility is for future reruns only. It cannot reconstruct missing crop
coordinates from E0/E1/E2/E3/S3 and must not relabel their internal validation
metrics as spatially independent. A manifest records half-open voxel bounds,
source identity, split regions, buffer/halo, and crop membership; validation
fails closed when any of those facts are absent or inconsistent.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


AXIS_INDEX = {"z": 0, "y": 1, "x": 2}
SPLITS = ("train", "val", "test")
PLANNED_STATUS = "planned_no_crops_recorded"
COMPLETED_STATUS = "completed"


def parse_triplet(value: str, cast=float) -> tuple[Any, Any, Any]:
    parts = value.split(",")
    if len(parts) != 3:
        raise ValueError(f"expected three comma-separated values, got {value!r}")
    return tuple(cast(part) for part in parts)


def make_axis_regions(
    shape_zyx: tuple[int, int, int],
    axis: str,
    val_frac: float,
    test_frac: float,
    buffer_voxels: int,
) -> dict[str, tuple[int, int]]:
    """Reserve high-axis validation/test regions separated by explicit buffers."""
    if axis not in AXIS_INDEX:
        raise ValueError(f"axis must be one of {sorted(AXIS_INDEX)}, got {axis!r}")
    if len(shape_zyx) != 3 or any(int(size) <= 0 for size in shape_zyx):
        raise ValueError(f"shape_zyx must contain three positive dimensions, got {shape_zyx}")
    if not 0.0 < val_frac < 1.0 or not 0.0 < test_frac < 1.0 or val_frac + test_frac >= 1.0:
        raise ValueError("val_frac and test_frac must be positive and sum to less than 1")
    if int(buffer_voxels) != buffer_voxels or buffer_voxels < 0:
        raise ValueError(f"buffer_voxels must be a non-negative integer, got {buffer_voxels}")

    length = int(shape_zyx[AXIS_INDEX[axis]])
    val_len = max(1, math.ceil(length * val_frac))
    test_len = max(1, math.ceil(length * test_frac))
    train_stop = length - val_len - test_len - 2 * int(buffer_voxels)
    if train_stop <= 0:
        raise ValueError("split fractions and buffers leave no train region")
    val_start = train_stop + int(buffer_voxels)
    val_stop = val_start + val_len
    test_start = val_stop + int(buffer_voxels)
    return {
        "train": (0, train_stop),
        "val": (val_start, val_stop),
        "test": (test_start, length),
    }


def _bounds(record: dict[str, Any]) -> tuple[int, int, int, int, int, int]:
    values = record.get("bounds_zyx")
    if not isinstance(values, list) or len(values) != 6:
        raise ValueError(f"crop {record.get('id', '<unknown>')}: bounds_zyx must be [z0,z1,y0,y1,x0,x1]")
    try:
        z0, z1, y0, y1, x0, x1 = (int(value) for value in values)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"crop {record.get('id', '<unknown>')}: bounds must be integers") from exc
    if z0 >= z1 or y0 >= y1 or x0 >= x1:
        raise ValueError(f"crop {record.get('id', '<unknown>')}: bounds must be non-empty half-open intervals")
    return z0, z1, y0, y1, x0, x1


def _intersects(a: tuple[int, int, int, int, int, int], b: tuple[int, int, int, int, int, int]) -> bool:
    return a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3] and a[4] < b[5] and b[4] < a[5]


def _validate_rejected_crops(rejected_crops: Any, seen_ids: set[str], errors: list[str]) -> int:
    if not isinstance(rejected_crops, list):
        errors.append("rejected_crops must be a list")
        return 0
    for crop in rejected_crops:
        if not isinstance(crop, dict):
            errors.append("rejected crop must be an object")
            continue
        crop_id = crop.get("id")
        if not isinstance(crop_id, str) or not crop_id:
            errors.append("rejected crop id is required")
            continue
        if crop_id in seen_ids:
            errors.append(f"duplicate crop id: {crop_id}")
            continue
        seen_ids.add(crop_id)
        try:
            _bounds(crop)
        except ValueError as exc:
            errors.append(str(exc))
        if not isinstance(crop.get("reason"), str) or not crop["reason"].strip():
            errors.append(f"rejected crop {crop_id}: reason is required")
    return len(rejected_crops)


def _validate_completed_evidence(manifest: dict[str, Any], crop_counts: dict[str, int], errors: list[str]) -> None:
    missing_splits = [split for split in SPLITS if not crop_counts[split]]
    if missing_splits:
        errors.append("completed manifest missing accepted crops for: " + ", ".join(missing_splits))
    for crop in manifest["crops"]:
        if not isinstance(crop.get("artifact_id"), str) or not crop["artifact_id"].strip():
            errors.append(f"crop {crop.get('id', '<unknown>')}: artifact_id is required when completed")
    run = manifest.get("run")
    if not isinstance(run, dict):
        errors.append("completed manifest requires run provenance")
    else:
        missing_run = [name for name in ("command", "code_sha", "environment") if not run.get(name)]
        if missing_run:
            errors.append("completed manifest run missing: " + ", ".join(missing_run))
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        errors.append("completed manifest requires artifact evidence")
    else:
        missing_artifacts = [name for name in ("case_mapping", "splits_final_json") if not artifacts.get(name)]
        if missing_artifacts:
            errors.append("completed manifest artifacts missing: " + ", ".join(missing_artifacts))


def validate_split_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate planned or completed source identity, coordinates, and evidence."""
    errors: list[str] = []
    checks: list[str] = []
    source = manifest.get("source") or {}
    required_source = ("id", "relative_path", "sha256", "shape_zyx", "spacing_zyx", "axis_order")
    missing_source = [name for name in required_source if not source.get(name)]
    if missing_source:
        errors.append("source missing: " + ", ".join(missing_source))
        return {"passed": False, "errors": errors, "checks": checks}
    if source["axis_order"] != "zyx":
        errors.append("source.axis_order must be zyx")
    try:
        shape = tuple(int(size) for size in source["shape_zyx"])
        spacing = tuple(float(value) for value in source["spacing_zyx"])
        axis = manifest["split_policy"]["axis"]
        regions = make_axis_regions(
            shape,
            axis,
            float(manifest["split_policy"]["val_frac"]),
            float(manifest["split_policy"]["test_frac"]),
            int(manifest["split_policy"]["buffer_voxels"]),
        )
        if len(spacing) != 3 or any(value <= 0 for value in spacing):
            raise ValueError("spacing_zyx must contain three positive values")
        checks.append("source_and_split_policy_valid")
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f"invalid split policy: {exc}")
        return {"passed": False, "errors": errors, "checks": checks}

    status = manifest.get("status")
    if status not in (PLANNED_STATUS, COMPLETED_STATUS):
        errors.append(f"status must be {PLANNED_STATUS!r} or {COMPLETED_STATUS!r}")
    crops = manifest.get("crops")
    if not isinstance(crops, list):
        errors.append("crops must be a list")
        return {"passed": False, "errors": errors, "checks": checks}
    if status == PLANNED_STATUS and crops:
        errors.append("planned manifest must not contain accepted crops")
    parsed: list[tuple[str, str, tuple[int, int, int, int, int, int]]] = []
    seen_ids: set[str] = set()
    axis_index = AXIS_INDEX[axis]
    for crop in crops:
        crop_id = crop.get("id")
        split = crop.get("split")
        if not isinstance(crop_id, str) or not crop_id:
            errors.append("crop id is required")
            continue
        if crop_id in seen_ids:
            errors.append(f"duplicate crop id: {crop_id}")
            continue
        seen_ids.add(crop_id)
        if split not in SPLITS:
            errors.append(f"crop {crop_id}: split must be one of {SPLITS}")
            continue
        try:
            bounds = _bounds(crop)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        starts = bounds[::2]
        stops = bounds[1::2]
        if any(start < 0 or stop > shape[index] for index, (start, stop) in enumerate(zip(starts, stops))):
            errors.append(f"crop {crop_id}: bounds exceed source shape {shape}")
            continue
        # Keep geometrically valid crops for pairwise checking even when their
        # split label crosses a region; one bad coordinate must not hide overlap.
        parsed.append((crop_id, split, bounds))
        start, stop = bounds[2 * axis_index], bounds[2 * axis_index + 1]
        region_start, region_stop = regions[split]
        if start < region_start or stop > region_stop:
            errors.append(f"crop {crop_id}: {split} bounds [{start},{stop}) cross region [{region_start},{region_stop})")
            continue

    for index, (left_id, left_split, left_bounds) in enumerate(parsed):
        for right_id, right_split, right_bounds in parsed[index + 1:]:
            if left_split != right_split and _intersects(left_bounds, right_bounds):
                errors.append(f"cross-split voxel overlap: {left_id} ({left_split}) vs {right_id} ({right_split})")
    rejected_count = _validate_rejected_crops(manifest.get("rejected_crops"), seen_ids, errors)
    crop_counts = {split: sum(item[1] == split for item in parsed) for split in SPLITS}
    if status == COMPLETED_STATUS:
        _validate_completed_evidence(manifest, crop_counts, errors)
    if not errors:
        if status == PLANNED_STATUS:
            checks.append("planned_no_crops_recorded")
        else:
            checks.extend([
                "crop_bounds_valid",
                "crop_regions_disjoint",
                "no_cross_split_voxel_overlap",
                "completed_evidence_recorded",
            ])
    return {
        "passed": not errors,
        "errors": errors,
        "checks": checks,
        "regions": {name: list(bounds) for name, bounds in regions.items()},
        "crop_counts": crop_counts,
        "rejected_crop_count": rejected_count,
    }


def build_manifest(
    source_id: str,
    source_path: str,
    source_sha256: str,
    shape_zyx: tuple[int, int, int],
    spacing_zyx: tuple[float, float, float],
    axis: str,
    val_frac: float,
    test_frac: float,
    buffer_voxels: int,
    seed: int,
) -> dict[str, Any]:
    """Create an empty future-rerun plan; accepted crop coordinates must be added later."""
    regions = make_axis_regions(shape_zyx, axis, val_frac, test_frac, buffer_voxels)
    return {
        "schema": "hy7_spatial_split_contract.v1",
        "status": PLANNED_STATUS,
        "source": {
            "id": source_id,
            "relative_path": source_path,
            "sha256": source_sha256,
            "shape_zyx": list(shape_zyx),
            "spacing_zyx": list(spacing_zyx),
            "axis_order": "zyx",
        },
        "split_policy": {
            "axis": axis,
            "val_frac": val_frac,
            "test_frac": test_frac,
            "buffer_voxels": buffer_voxels,
            "seed": seed,
            "regions": {name: list(bounds) for name, bounds in regions.items()},
            "boundary_crop_policy": "reject crops crossing a split region or buffer",
        },
        "crops": [],
        "rejected_crops": [],
        "requirements": [
            "record every accepted and rejected crop with half-open bounds_zyx",
            "record class coverage, normalization source, command, code SHA, and environment",
            "store nnU-Net splits_final.json and case-to-coordinate mapping when applicable",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan or validate a future HY7 spatial split manifest")
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan = subparsers.add_parser("plan")
    plan.add_argument("--source-id", required=True)
    plan.add_argument("--source-path", required=True)
    plan.add_argument("--source-sha256", required=True)
    plan.add_argument("--shape-zyx", required=True, help="e.g. 1600,1620,1620")
    plan.add_argument("--spacing-zyx", required=True, help="e.g. 14,14,14")
    plan.add_argument("--axis", choices=sorted(AXIS_INDEX), required=True)
    plan.add_argument("--val-frac", type=float, default=0.1)
    plan.add_argument("--test-frac", type=float, default=0.2)
    plan.add_argument("--buffer-voxels", type=int, default=0)
    plan.add_argument("--seed", type=int, required=True)
    plan.add_argument("--out", required=True)
    check = subparsers.add_parser("check")
    check.add_argument("--manifest", required=True)
    args = parser.parse_args(argv)

    if args.command == "plan":
        manifest = build_manifest(
            args.source_id,
            args.source_path,
            args.source_sha256,
            parse_triplet(args.shape_zyx, int),
            parse_triplet(args.spacing_zyx, float),
            args.axis,
            args.val_frac,
            args.test_frac,
            args.buffer_voxels,
            args.seed,
        )
        Path(args.out).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"status": manifest["status"], "out": args.out, "regions": manifest["split_policy"]["regions"]}, ensure_ascii=False))
        return 0

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    result = validate_split_manifest(manifest)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
