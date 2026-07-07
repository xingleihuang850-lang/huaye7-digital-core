#!/usr/bin/env python3
"""HY7 Stage 3 metadata-only inter-slice consistency audit.

Gate boundary: ALLOW_METADATA_ONLY_INTER_SLICE_AUDIT_WITH_CONSTRAINTS.
This launcher reads an existing qmatch diagnostic candidate, verifies its hash,
computes only summary metadata, and writes no voxel arrays.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

REQUIRED_PACKAGE_FILES = [
    "inter_slice_audit_manifest.json",
    "inter_slice_audit_readme.md",
    "input_route_manifest.json",
    "candidate_source_manifest.json",
    "inter_slice_metrics.json",
    "axis_boundary_semantics.md",
    "negative_evidence.md",
    "forbidden_claims.txt",
    "hashes.txt",
]

ROUTE_LABEL = "nnUNet ep015_qmatch"
CALIBRATION_VERSION = "hy7-gray-calibration-qmatch-v1"
EXPECTED_SOURCE_SHA256 = "24655b96b3f50ad14f8c60548afa9e0169babb76c24b605efa870e741502b7b2"

THRESHOLDS = {
    "jaccard_x_median_over_yz_median_lt": 0.25,
    "s2_x_over_min_yz_lt": 0.25,
    "component_persistence_pairwise_median_lt": 0.10,
    "per_slice_pore_count_robust_z_abs_gt": 3.5,
    "zero_or_near_zero_pore_slice_run_ge": 3,
    "threshold_use": "negative_evidence_flagging_only_not_scientific_acceptance",
}


class AuditContractError(ValueError):
    """Raised when the audit must fail closed before metrics/package writing."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _json_dump(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _binary(arr: np.ndarray) -> np.ndarray:
    if arr.ndim != 3:
        raise AuditContractError(f"candidate must be 3D, got shape={arr.shape}")
    return (arr > 0).astype(np.uint8, copy=False)


def _summary(values: np.ndarray) -> dict[str, float | int | None]:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return {"count": 0, "min": None, "p05": None, "median": None, "mean": None, "p95": None, "max": None}
    return {
        "count": int(values.size),
        "min": float(np.min(values)),
        "p05": float(np.percentile(values, 5)),
        "median": float(np.median(values)),
        "mean": float(np.mean(values)),
        "p95": float(np.percentile(values, 95)),
        "max": float(np.max(values)),
    }


def _safe_ratio(num: float, den: float) -> float | None:
    if den == 0:
        return None
    return float(num / den)


def _s2_lag1(volume: np.ndarray) -> dict[str, float]:
    return {
        "x": float(np.mean(volume[:-1, :, :] & volume[1:, :, :])) if volume.shape[0] > 1 else 0.0,
        "y": float(np.mean(volume[:, :-1, :] & volume[:, 1:, :])) if volume.shape[1] > 1 else 0.0,
        "z": float(np.mean(volume[:, :, :-1] & volume[:, :, 1:])) if volume.shape[2] > 1 else 0.0,
    }


def _adjacent_pair_stats(volume: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    jaccard = []
    dice = []
    for i in range(volume.shape[0] - 1):
        a = volume[i].astype(bool)
        b = volume[i + 1].astype(bool)
        inter = int(np.logical_and(a, b).sum())
        union = int(np.logical_or(a, b).sum())
        total = int(a.sum() + b.sum())
        jaccard.append(inter / union if union else 1.0)
        dice.append((2 * inter) / total if total else 1.0)
    return np.asarray(jaccard, dtype=float), np.asarray(dice, dtype=float)


def _longest_true_run(mask: np.ndarray) -> int:
    best = cur = 0
    for value in mask:
        if bool(value):
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def _robust_z(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    median = np.median(values)
    mad = np.median(np.abs(values - median))
    if mad == 0:
        return np.zeros_like(values, dtype=float)
    return 0.6745 * (values - median) / mad


def compute_inter_slice_metrics(volume: np.ndarray) -> dict[str, Any]:
    v = _binary(volume)
    per_slice_counts = v.sum(axis=(1, 2)).astype(float)
    per_slice_porosity = per_slice_counts / float(v.shape[1] * v.shape[2])
    jaccard, dice = _adjacent_pair_stats(v)
    s2 = _s2_lag1(v)
    yz_ref = np.median([s2["y"], s2["z"]])
    s2_x_over_min_yz = _safe_ratio(s2["x"], min(s2["y"], s2["z"])) if min(s2["y"], s2["z"]) else None
    robust = _robust_z(per_slice_counts)
    near_zero = per_slice_counts <= max(1.0, 0.01 * float(v.shape[1] * v.shape[2]))
    overlap_nonzero = []
    for i in range(v.shape[0] - 1):
        overlap_nonzero.append(bool(np.logical_and(v[i], v[i + 1]).sum() > 0))

    # y/z adjacent summaries are in-plane continuity proxies used only as a denominator for negative-evidence flags.
    y_adj = np.mean(v[:, :-1, :] & v[:, 1:, :], axis=(1, 2)) if v.shape[1] > 1 else np.asarray([0.0])
    z_adj = np.mean(v[:, :, :-1] & v[:, :, 1:], axis=(1, 2)) if v.shape[2] > 1 else np.asarray([0.0])
    yz_median = float(np.median([np.median(y_adj), np.median(z_adj)]))
    jaccard_ratio = _safe_ratio(float(np.median(jaccard)) if jaccard.size else 0.0, yz_median)

    flags = {
        "jaccard_x_median_over_yz_median_lt_0.25": jaccard_ratio is not None and jaccard_ratio < 0.25,
        "s2_x_over_min_yz_lt_0.25": s2_x_over_min_yz is not None and s2_x_over_min_yz < 0.25,
        "component_persistence_pairwise_median_lt_0.10": bool(np.median(jaccard) < 0.10) if jaccard.size else True,
        "per_slice_pore_count_robust_z_abs_gt_3.5": bool(np.max(np.abs(robust)) > 3.5) if robust.size else False,
        "zero_or_near_zero_pore_slice_run_ge_3": _longest_true_run(near_zero) >= 3,
    }
    return {
        "metric_labels_required": {
            "status": "diagnostic_metadata_only",
            "not_permeability": True,
            "not_scientific_acceptance": True,
            "not_formal_qmatch_acceptance": True,
            "no_second_smoke_implication": True,
            "no_a2_small_implication": True,
            "low_n_caveat": "64 slices / 63 adjacent pairs for parent run01; descriptive, not confirmatory",
        },
        "boundary_semantics": "lag_1_valid_pairs_no_wrap_no_periodic_boundary",
        "summary_metrics": {
            "per_slice_porosity": _summary(per_slice_porosity),
            "per_slice_pore_count": _summary(per_slice_counts),
            "adjacent_slice_jaccard_distribution_along_x": _summary(jaccard),
            "adjacent_slice_dice_distribution_along_x": _summary(dice),
            "component_persistence_across_adjacent_slices_2d_pairwise_proxy_not_3d_percolation": _summary(jaccard),
            "run_length_of_connected_foreground_across_x_2d_pairwise_proxy_not_3d_percolation": {"longest_overlap_nonzero_run": _longest_true_run(np.asarray(overlap_nonzero, dtype=bool))},
            "s2_lag1_x_y_z_with_boundary_label": s2,
            "s2_anisotropy_ratios": {
                "x_over_y": _safe_ratio(s2["x"], s2["y"]),
                "x_over_z": _safe_ratio(s2["x"], s2["z"]),
                "x_over_min_yz": s2_x_over_min_yz,
            },
            "per_slice_pore_count_robust_z_abs": _summary(np.abs(robust)),
            "zero_or_near_zero_pore_slice_runs": {"longest_run": _longest_true_run(near_zero)},
        },
        "pre_registered_diagnostic_thresholds": THRESHOLDS,
        "negative_evidence_flags": flags,
        "raw_pair_values_written": False,
        "raw_per_slice_values_written": False,
    }


def write_inter_slice_audit_package(
    out_dir: Path,
    candidate_npy: Path,
    expected_sha256: str,
    slice_start: int,
    slice_stop: int,
    source_path: str | None = None,
    expected_slice_count: int = 64,
) -> dict[str, str]:
    candidate_npy = Path(candidate_npy)
    if not candidate_npy.exists():
        raise AuditContractError(f"candidate source missing: {candidate_npy}")
    actual_sha = sha256_file(candidate_npy)
    if actual_sha != expected_sha256:
        raise AuditContractError(f"sha256 mismatch: expected {expected_sha256}, got {actual_sha}")
    if slice_stop <= slice_start:
        raise AuditContractError("slice_stop must be greater than slice_start")
    if (slice_stop - slice_start) != expected_slice_count:
        raise AuditContractError(
            f"axis mapping ambiguous: slice range length {slice_stop - slice_start} != expected {expected_slice_count}"
        )

    arr = np.load(candidate_npy, mmap_mode="r")
    if arr.ndim != 3:
        raise AuditContractError(f"candidate must be 3D, got shape={arr.shape}")
    if slice_start < 0 or slice_stop > arr.shape[0]:
        raise AuditContractError(f"slice range {slice_start}:{slice_stop} outside axis0 length {arr.shape[0]}")
    volume = _binary(np.asarray(arr[slice_start:slice_stop]))
    if volume.shape[0] != expected_slice_count:
        raise AuditContractError(f"axis mapping ambiguous: sliced shape={volume.shape}")

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = {name: out_dir / name for name in REQUIRED_PACKAGE_FILES}
    metrics = compute_inter_slice_metrics(volume)

    manifest = {
        "package_status": "METADATA_ONLY_INTER_SLICE_AUDIT",
        "execution_authorized_by_gate": "ALLOW_METADATA_ONLY_INTER_SLICE_AUDIT_WITH_CONSTRAINTS",
        "scientific_status": "diagnostic_metadata_only_not_evidence",
        "parent_smoke_verdict": "REDESIGN_BEFORE_ANY_A2_SMALL_GATE",
        "no_second_smoke_implication": True,
        "no_a2_small_implication": True,
        "candidate_arrays_written": False,
        "raw_metric_arrays_written": False,
        "required_package_files": REQUIRED_PACKAGE_FILES,
    }
    _json_dump(outputs["inter_slice_audit_manifest.json"], manifest)
    outputs["inter_slice_audit_readme.md"].write_text(
        "# HY7 inter-slice consistency audit\n\n"
        "Metadata-only diagnostic audit. This package does not authorize or imply second smoke, A2-small, scientific acceptance, qmatch formal acceptance, validated permeability, or generative digital-well claims.\n"
        "All distribution metrics are summary statistics only; no per-slice-pair arrays or voxel arrays are written.\n",
        encoding="utf-8",
    )
    _json_dump(outputs["input_route_manifest.json"], {
        "route_label": ROUTE_LABEL,
        "route_status": "diagnostic_calibrated_route_only",
        "calibration_version": CALIBRATION_VERSION,
        "formal_anchor": "ep015_all planning_anchor_only",
        "failed_chunk_visible_negative_evidence": "ep015_chunk000_063",
        "not_a_generative_digital_well": True,
    })
    _json_dump(outputs["candidate_source_manifest.json"], {
        "source_path": source_path or str(candidate_npy),
        "local_materialized_path": str(candidate_npy),
        "source_sha256_verified": actual_sha,
        "expected_sha256": expected_sha256,
        "slice_range": {"start": slice_start, "stop": slice_stop},
        "full_array_shape": list(arr.shape),
        "audit_volume_shape": list(volume.shape),
        "candidate_arrays_written": False,
    })
    _json_dump(outputs["inter_slice_metrics.json"], metrics)
    outputs["axis_boundary_semantics.md"].write_text(
        "# Axis and boundary semantics\n\n"
        "axis_0_to_slice_stacking_mapping=verified\n"
        f"slice_range={slice_start}:{slice_stop}\n"
        f"expected_slice_count={expected_slice_count}\n"
        f"audit_volume_shape={list(volume.shape)}\n"
        "boundary_semantics=lag_1_valid_pairs_no_wrap_no_periodic_boundary\n"
        "fail_closed_on_axis_mapping_ambiguity=true\n",
        encoding="utf-8",
    )
    flag_lines = "\n".join(f"- {k}: {v}" for k, v in metrics["negative_evidence_flags"].items())
    outputs["negative_evidence.md"].write_text(
        "# Negative evidence\n\n"
        "failed_chunk_ep015_chunk000_063 remains visible negative evidence.\n"
        "Audit outcome, pass or fail, has no bearing on parent_smoke_verdict=REDESIGN_BEFORE_ANY_A2_SMALL_GATE and does not reopen or modify that gate.\n\n"
        "## Pre-registered diagnostic flags\n\n"
        f"{flag_lines}\n",
        encoding="utf-8",
    )
    outputs["forbidden_claims.txt"].write_text(
        "second smoke execution without a later strict gate\n"
        "A2-small execution\nA2-medium execution\nfull 2D-to-3D reconstruction campaign\n"
        "training or fine-tuning\ncheckpoint creation or selection\nlarge volume export as scientific output\n"
        "HY7 scientific acceptance claim\nB2-min final pass claim\nqmatch formal acceptance claim\n"
        "validated permeability claim\ngenerative digital-well claim\n"
        "committing .npy/.npz/.pt/weights/checkpoints/voxel arrays\n"
        "Audit outcome, pass or fail, has no bearing on parent_smoke_verdict=REDESIGN_BEFORE_ANY_A2_SMALL_GATE and does not reopen or modify that gate.\n"
        "Imports of torch/tensorflow/nnunet are forbidden for this audit.\n",
        encoding="utf-8",
    )
    hash_lines = []
    for name in REQUIRED_PACKAGE_FILES:
        if name == "hashes.txt":
            continue
        hash_lines.append(f"{sha256_file(outputs[name])}  {name}")
    outputs["hashes.txt"].write_text("\n".join(hash_lines) + "\n", encoding="utf-8")
    return {k: str(v) for k, v in outputs.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--candidate-npy", type=Path, required=True)
    parser.add_argument("--expected-sha256", default=EXPECTED_SOURCE_SHA256)
    parser.add_argument("--slice-start", type=int, default=384)
    parser.add_argument("--slice-stop", type=int, default=448)
    parser.add_argument("--source-path", default=None)
    args = parser.parse_args(argv)
    outputs = write_inter_slice_audit_package(
        out_dir=args.out,
        candidate_npy=args.candidate_npy,
        expected_sha256=args.expected_sha256,
        slice_start=args.slice_start,
        slice_stop=args.slice_stop,
        source_path=args.source_path,
    )
    print(json.dumps({"status": "ok", "outputs": outputs}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
