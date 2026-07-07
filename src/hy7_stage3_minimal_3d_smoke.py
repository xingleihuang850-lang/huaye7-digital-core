#!/usr/bin/env python3
"""HY7 Stage 3 Branch A minimal 3D smoke launcher/package contract.

This module is deliberately conservative. It can write the required 12-file
minimal-smoke package, but it fails closed whenever the frozen qmatch route,
calibration artifact, failed-chunk negative evidence, candidate count, volume
bounds, or physical-proxy consistency checks are not satisfied.

It does not train, fine-tune, create/select checkpoints, run A2, or commit voxel
volumes/weights. Candidate arrays may be supplied by tests or by a future gated
caller; this launcher records metrics/provenance only and never writes .npy,
.npz, or .pt artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from collections import deque
from pathlib import Path
from typing import Any

import numpy as np

DATE = "2026-07-07"
GATE_VERDICT = "ALLOW_MINIMAL_3D_SMOKE_ONLY"
ROUTE_LABEL = "nnUNet ep015_qmatch"
ROUTE_STATUS = "diagnostic_calibrated_route_only"
CALIBRATION_VERSION = "hy7-gray-calibration-qmatch-v1"
FORMAL_ANCHOR = "ep015_all planning_anchor_only"
FAILED_CHUNK_ID = "ep015_chunk000_063"
SCIENTIFIC_STATUS = "diagnostic_smoke_not_evidence"
WORKFLOW_NODE = "HY7-stage3-branch-A-minimal-3d-smoke-launcher"

REQUIRED_PACKAGE_FILES = [
    "branch_a_3d_smoke_manifest.json",
    "branch_a_3d_smoke_readme.md",
    "input_route_manifest.json",
    "candidate_volume_manifest.json",
    "metrics_3d_smoke.json",
    "physical_response_proxy.json",
    "connectivity_semantics.md",
    "s2_boundary_semantics.md",
    "euler_minkowski_status.md",
    "negative_evidence.md",
    "forbidden_claims.txt",
    "hashes.txt",
]

FORBIDDEN_CLAIMS = [
    "A2-small scientific execution",
    "A2-medium execution",
    "full 2D-to-3D reconstruction campaign",
    "training or fine-tuning",
    "checkpoint creation or selection",
    "large volume export as scientific output",
    "HY7 scientific acceptance claim",
    "generative digital-well claim",
    "B2-min final pass claim",
    "qmatch as formal acceptance route",
    "2D x/y penetration interpreted as 3D permeability/connectivity",
    "validated permeability claim from diagnostic proxy fields",
    "condition-response or representativeness claim without future condition gate",
]


class SmokeContractError(ValueError):
    """Raised before package writing when launcher scope constraints are violated."""


def _as_binary_volume(volume: np.ndarray) -> np.ndarray:
    arr = np.asarray(volume, dtype=np.uint8)
    if arr.ndim != 3:
        raise SmokeContractError(f"expected 3D candidate volume, got shape {arr.shape}")
    if any(dim > 128 for dim in arr.shape):
        raise SmokeContractError(f"volume axis hard cap 128 exceeded: shape={arr.shape}")
    return (arr > 0).astype(np.uint8)


def _neighbors6(coord: tuple[int, int, int], shape: tuple[int, int, int]):
    x, y, z = coord
    nx, ny, nz = shape
    for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
        xx, yy, zz = x + dx, y + dy, z + dz
        if 0 <= xx < nx and 0 <= yy < ny and 0 <= zz < nz:
            yield xx, yy, zz


def _components6(volume: np.ndarray) -> list[list[tuple[int, int, int]]]:
    arr = _as_binary_volume(volume)
    seen = np.zeros(arr.shape, dtype=bool)
    components: list[list[tuple[int, int, int]]] = []
    for sx, sy, sz in np.argwhere(arr > 0):
        start = (int(sx), int(sy), int(sz))
        if seen[start]:
            continue
        q: deque[tuple[int, int, int]] = deque([start])
        seen[start] = True
        comp: list[tuple[int, int, int]] = []
        while q:
            cur = q.popleft()
            comp.append(cur)
            for nb in _neighbors6(cur, arr.shape):
                if arr[nb] and not seen[nb]:
                    seen[nb] = True
                    q.append(nb)
        components.append(comp)
    return components


def _component_touches_axis(component: list[tuple[int, int, int]], shape: tuple[int, int, int], axis: int) -> bool:
    coords = [p[axis] for p in component]
    return bool(coords) and min(coords) == 0 and max(coords) == shape[axis] - 1


def _s2_lag1_valid_pairs(volume: np.ndarray) -> dict[str, float]:
    arr = _as_binary_volume(volume).astype(bool)
    pairs = {
        "x": arr[:-1, :, :] & arr[1:, :, :],
        "y": arr[:, :-1, :] & arr[:, 1:, :],
        "z": arr[:, :, :-1] & arr[:, :, 1:],
    }
    return {axis: float(mask.mean()) if mask.size else 0.0 for axis, mask in pairs.items()}


def compute_3d_smoke_metrics(volume: np.ndarray) -> dict[str, Any]:
    arr = _as_binary_volume(volume)
    total = int(arr.size)
    pore = int(arr.sum())
    components = _components6(arr)
    largest = max((len(c) for c in components), default=0)
    percolation = {"x": False, "y": False, "z": False}
    for comp in components:
        for axis, name in enumerate(("x", "y", "z")):
            percolation[name] = percolation[name] or _component_touches_axis(comp, arr.shape, axis)
    pore_basis = float(largest / pore) if pore else 0.0
    total_basis = float(largest / total) if total else 0.0
    return {
        "shape": list(arr.shape),
        "porosity_phi_3d": {"status": "implemented", "value": float(pore / total) if total else 0.0},
        "connected_porosity_ratio_3d": {
            "status": "implemented",
            "connectivity": "pore-phase 6-neighborhood",
            "value": {"pore_voxel_basis": pore_basis, "total_volume_basis": total_basis},
        },
        "percolation_flags_3d": {
            "status": "implemented",
            "computed_before_physical_proxy": True,
            "definition": "one pore-phase connected component touches both opposing faces along axis k",
            "connectivity": "pore-phase 6-neighborhood",
            "value": percolation,
        },
        "largest_connected_component_fraction_3d": {
            "status": "implemented",
            "connectivity": "pore-phase 6-neighborhood",
            "value": {"pore_voxel_basis": pore_basis, "total_volume_basis": total_basis},
        },
        "s2_two_point_correlation_3d": {
            "status": "diagnostic_proxy",
            "boundary_convention": "lag_1_valid_pairs_no_wrap_no_periodic_boundary",
            "axis_mapping": "x/y/z -> ndarray axes 0/1/2",
            "value": {"lag_1_valid_pairs": _s2_lag1_valid_pairs(arr)},
        },
        "euler_characteristic_or_minkowski_3d": {
            "status": "explicitly_de_scoped_fail_closed",
            "reason": "No real 3D Euler/Minkowski phantom validation is present in this launcher.",
        },
    }


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def _environment() -> dict[str, str]:
    return {"python": sys.version.split()[0], "platform": platform.platform(), "numpy": np.__version__}


def _read_calibration_version(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    version = data.get("version") or data.get("calibration_version")
    return str(version) if version is not None else None


def _preflight(calibration_artifact: Path, failed_chunk_record: Path) -> list[str]:
    reasons: list[str] = []
    if not calibration_artifact.exists():
        reasons.append(f"qmatch calibration artifact missing: {calibration_artifact}")
    else:
        version = _read_calibration_version(calibration_artifact)
        if version != CALIBRATION_VERSION:
            reasons.append(f"qmatch calibration version mismatch: got={version!r}, required={CALIBRATION_VERSION}")
    if not failed_chunk_record.exists():
        reasons.append(f"failed chunk evidence record missing: {failed_chunk_record}; required visible negative evidence {FAILED_CHUNK_ID}")
    else:
        text = failed_chunk_record.read_text(encoding="utf-8", errors="replace")
        if FAILED_CHUNK_ID not in text:
            reasons.append(f"failed chunk evidence record does not mention {FAILED_CHUNK_ID}: {failed_chunk_record}")
    return reasons


def _validate_static_scope(route_label: str, calibration_version: str, candidate_count: int) -> None:
    if route_label != ROUTE_LABEL:
        raise SmokeContractError(f"route_label must be {ROUTE_LABEL}, got {route_label!r}")
    if calibration_version != CALIBRATION_VERSION:
        raise SmokeContractError(f"calibration_version must be {CALIBRATION_VERSION}, got {calibration_version!r}")
    if candidate_count > 3:
        raise SmokeContractError(f"candidate_count_max=3 exceeded: {candidate_count}")


def _physical_proxy(metrics: dict[str, Any] | None, override: dict[str, float] | None) -> tuple[dict[str, Any], list[str]]:
    if metrics is None:
        return (
            {
                "status": "NOT_EXECUTED_FAIL_CLOSED",
                "method_name": "percolation_supported_flow_proxy",
                "qualitative_only_flag": True,
                "units_or_unitless_status": "unitless diagnostic proxy only",
                "assumptions": ["No candidate metrics available; no physical proxy computed."],
                "axis_labels": ["x", "y", "z"],
                "consistency_with_percolation": "not_evaluated",
                "per_axis_flow_proxy": {"x": 0.0, "y": 0.0, "z": 0.0},
                "forbidden_claims": ["validated permeability", "scientific physical response"],
            },
            [],
        )
    percolation = metrics["percolation_flags_3d"]["value"]
    flow = override if override is not None else {axis: (1.0 if percolates else 0.0) for axis, percolates in percolation.items()}
    reasons = [f"positive_flow_proxy_on_non_percolating_axis:{axis}" for axis, value in flow.items() if value > 0 and not percolation.get(axis, False)]
    status = "FAIL_CLOSED_PHYSICAL_PROXY_CONTRADICTION" if reasons else "DIAGNOSTIC_PROXY_CONSISTENT_WITH_PERCOLATION"
    return (
        {
            "status": status,
            "method_name": "percolation_supported_flow_proxy",
            "qualitative_only_flag": True,
            "units_or_unitless_status": "unitless diagnostic proxy only; not permeability",
            "assumptions": [
                "Per-axis flow proxy can be positive only when the same axis percolates under 6-neighborhood pore connectivity.",
                "Connected porosity is a topology diagnostic, not validated permeability.",
            ],
            "axis_labels": ["x", "y", "z"],
            "per_axis_flow_proxy": {axis: float(flow.get(axis, 0.0)) for axis in ("x", "y", "z")},
            "consistency_with_percolation": "fail_closed" if reasons else "consistent_by_construction",
            "fail_closed_reasons": reasons,
            "forbidden_claims": ["validated permeability", "scientific physical response"],
        },
        reasons,
    )


def _readme_text(package_status: str) -> str:
    return f"""# HY7 Stage 3 Branch A minimal 3D smoke package

Gate verdict: `{GATE_VERDICT}`
Package status: `{package_status}`
Scientific status: `{SCIENTIFIC_STATUS}`

This package is a diagnostic smoke contract only. It is not A2 execution, not a
scientific acceptance result, and not a generative digital-well claim. The frozen
route is `{ROUTE_LABEL}` with calibration `{CALIBRATION_VERSION}`; formal
`ep015_all` remains `planning_anchor_only`.

If prerequisite evidence or candidate source is absent, the package deliberately
fails closed while still writing the required 12 metadata files. Negative evidence
is retained as useful output rather than hidden.

No voxel arrays, weights, checkpoints, `.npy`, `.npz`, or `.pt` files are written
by this launcher.
"""


def _connectivity_semantics_text() -> str:
    return """# Connectivity semantics

- pore-phase connectivity: 6-neighborhood (face-connected voxels only).
- complementary solid/background connectivity: 26-neighborhood is declared to avoid dual-connectivity ambiguity; this launcher does not claim Euler/Minkowski validation.
- percolation definition: one pore-phase connected component touches both opposing faces along axis k.
- axis mapping: x/y/z -> ndarray axes 0/1/2.
- 2D x/y penetration must not be interpreted as 3D permeability or 3D connectivity.
"""


def _s2_semantics_text() -> str:
    return """# S2 boundary semantics

The diagnostic S2 proxy uses lag-1 valid adjacent voxel pairs independently on x,
y, and z. It does not use periodic wrapping, padding, or cross-boundary pairs.
The boundary label is `lag_1_valid_pairs_no_wrap_no_periodic_boundary`.
"""


def _euler_status_text() -> str:
    return """# Euler / Minkowski status

Status: `explicitly_de_scoped_fail_closed`.

No 3D Euler/Minkowski value is claimed by this launcher because no real phantom
validation for that implementation is present here. Any future use must add
known-answer phantom validation before replacing this fail-closed status.
"""


def _negative_evidence_text(reasons: list[str], metrics: dict[str, Any] | None, physical_reasons: list[str]) -> str:
    non_perc = []
    if metrics is not None:
        flags = metrics["percolation_flags_3d"]["value"]
        non_perc = [axis for axis, ok in flags.items() if not ok]
    lines = [
        "# Negative evidence",
        "",
        f"- failed_chunk_required_visible: {FAILED_CHUNK_ID}",
        f"- formal_anchor_status: {FORMAL_ANCHOR}",
        f"- qmatch_route_status: {ROUTE_STATUS}",
        f"- euler_minkowski: explicitly_de_scoped_fail_closed",
        f"- non_percolating_axes: {non_perc if metrics is not None else 'not_evaluated'}",
        f"- low_connected_porosity: {'not_evaluated' if metrics is None else 'see metrics_3d_smoke.json'}",
        f"- S2_axis_or_boundary_disagreement: boundary convention recorded; no acceptance comparison claimed",
        f"- physical_response_proxy_contradictions: {physical_reasons}",
        f"- formal_vs_qmatch_route_disagreement: formal anchor and qmatch diagnostic path are not merged",
        f"- unreproducible_volume_or_metrics: {'candidate source unresolved' if metrics is None else 'not claimed beyond this diagnostic package'}",
        "",
        "## Fail-closed reasons",
    ]
    if reasons or physical_reasons:
        lines.extend([f"- {reason}" for reason in [*reasons, *physical_reasons]])
    else:
        lines.append("- none at package-writing time; still diagnostic only")
    return "\n".join(lines) + "\n"


def write_smoke_package(
    out_dir: Path,
    calibration_artifact: Path,
    failed_chunk_record: Path,
    candidate_volumes: list[np.ndarray] | None = None,
    route_label: str = ROUTE_LABEL,
    calibration_version: str = CALIBRATION_VERSION,
    physical_flow_proxy: dict[str, float] | None = None,
) -> dict[str, str]:
    """Write the required 12-file package or fail closed.

    `candidate_volumes=None` means no real qmatch-conditioned candidate source was
    resolved by the caller; this writes a complete fail-closed package. A nonempty
    list computes metrics for at most three already-materialized in-memory arrays.
    The launcher never serializes those arrays.
    """
    candidate_count = len(candidate_volumes) if candidate_volumes is not None else 0
    _validate_static_scope(route_label=route_label, calibration_version=calibration_version, candidate_count=candidate_count)

    arrays = [] if candidate_volumes is None else [_as_binary_volume(vol) for vol in candidate_volumes]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    preflight_reasons = _preflight(Path(calibration_artifact), Path(failed_chunk_record))
    selected_metrics: dict[str, Any] | None = None
    metrics_by_candidate: list[dict[str, Any]] = []
    smoke_executed = False
    fail_reasons = list(preflight_reasons)

    if preflight_reasons:
        package_status = "FAIL_CLOSED_PREFLIGHT"
    elif candidate_volumes is None or candidate_count == 0:
        package_status = "FAIL_CLOSED_NO_CANDIDATE_SOURCE"
        fail_reasons.append("candidate source unresolved; no synthetic or invented HY7 candidate data generated")
    else:
        smoke_executed = True
        metrics_by_candidate = [compute_3d_smoke_metrics(vol) for vol in arrays]
        selected_metrics = metrics_by_candidate[0]
        package_status = "DIAGNOSTIC_SMOKE_METADATA_ONLY"

    physical, physical_reasons = _physical_proxy(selected_metrics, physical_flow_proxy)
    if physical_reasons:
        package_status = "FAIL_CLOSED_PHYSICAL_PROXY_CONTRADICTION"

    manifest = {
        "workflow_node": WORKFLOW_NODE,
        "date": DATE,
        "gate_verdict": GATE_VERDICT,
        "package_status": package_status,
        "smoke_executed": smoke_executed,
        "one_run_only": True,
        "candidate_count": candidate_count,
        "candidate_count_max": 3,
        "volume_preferred": "<=64^3",
        "volume_hard_cap_without_further_gate": "<=128^3",
        "route_label": route_label,
        "route_status": ROUTE_STATUS,
        "calibration_version": calibration_version,
        "formal_anchor": FORMAL_ANCHOR,
        "failed_chunk_required": FAILED_CHUNK_ID,
        "scientific_status": SCIENTIFIC_STATUS,
        "not_a_generative_digital_well": True,
        "condition_interface_status": "not_yet_condition_response_test",
        "fail_closed_reasons": [*fail_reasons, *physical_reasons],
        "execution_boundary": {
            "no_a2": True,
            "no_training": True,
            "no_fine_tuning": True,
            "no_checkpoint": True,
            "no_checkpoint_selection": True,
            "no_large_volume_export_as_scientific_output": True,
            "no_hy7_scientific_acceptance_claim": True,
        },
        "source": {"git_commit": _git_commit(), "command": " ".join(sys.argv), "environment": _environment()},
        "required_outputs": REQUIRED_PACKAGE_FILES,
    }

    input_route_manifest = {
        "route_label": route_label,
        "route_status": ROUTE_STATUS,
        "calibration_version": calibration_version,
        "calibration_artifact": str(calibration_artifact),
        "calibration_artifact_exists": Path(calibration_artifact).exists(),
        "formal_anchor": FORMAL_ANCHOR,
        "formal_anchor_use": "planning_anchor_only",
        "failed_chunk": FAILED_CHUNK_ID,
        "failed_chunk_record": str(failed_chunk_record),
        "failed_chunk_visible": Path(failed_chunk_record).exists() and FAILED_CHUNK_ID in Path(failed_chunk_record).read_text(encoding="utf-8", errors="replace"),
        "qmatch_not_formal_acceptance": True,
    }

    candidate_manifest = {
        "candidate_count": candidate_count,
        "candidate_count_max": 3,
        "candidate_arrays_written": False,
        "volume_files_written": [],
        "forbidden_extensions_written": [],
        "candidate_records": [
            {"candidate_index": idx, "shape": list(arr.shape), "volume_axis_hard_cap_128_satisfied": True, "array_serialized": False}
            for idx, arr in enumerate(arrays)
        ],
        "unresolved_candidate_source_fail_closed": candidate_volumes is None or candidate_count == 0,
    }

    metrics = {
        "workflow_node": WORKFLOW_NODE,
        "scientific_status": SCIENTIFIC_STATUS,
        "package_status": package_status,
        "route_label": route_label,
        "calibration_version": calibration_version,
        "percolation_computed_before_physical_proxy": selected_metrics is not None,
        "candidate_metrics": metrics_by_candidate,
        "selected_candidate_index_for_diagnostic_proxy": 0 if selected_metrics is not None else None,
        "euler_minkowski_default": "explicitly_de_scoped_fail_closed",
    }

    outputs = {name: out_dir / name for name in REQUIRED_PACKAGE_FILES}
    _write_json(outputs["branch_a_3d_smoke_manifest.json"], manifest)
    outputs["branch_a_3d_smoke_readme.md"].write_text(_readme_text(package_status), encoding="utf-8")
    _write_json(outputs["input_route_manifest.json"], input_route_manifest)
    _write_json(outputs["candidate_volume_manifest.json"], candidate_manifest)
    _write_json(outputs["metrics_3d_smoke.json"], metrics)
    _write_json(outputs["physical_response_proxy.json"], physical)
    outputs["connectivity_semantics.md"].write_text(_connectivity_semantics_text(), encoding="utf-8")
    outputs["s2_boundary_semantics.md"].write_text(_s2_semantics_text(), encoding="utf-8")
    outputs["euler_minkowski_status.md"].write_text(_euler_status_text(), encoding="utf-8")
    outputs["negative_evidence.md"].write_text(_negative_evidence_text(fail_reasons, selected_metrics, physical_reasons), encoding="utf-8")
    outputs["forbidden_claims.txt"].write_text("\n".join(FORBIDDEN_CLAIMS) + "\n", encoding="utf-8")

    hash_lines = []
    for name in REQUIRED_PACKAGE_FILES:
        if name == "hashes.txt":
            continue
        hash_lines.append(f"{_sha256(outputs[name])}  {name}")
    outputs["hashes.txt"].write_text("\n".join(hash_lines) + "\n", encoding="utf-8")
    return {path.stem: str(path) for path in outputs.values()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--calibration-artifact", required=True, type=Path)
    parser.add_argument("--failed-chunk-record", required=True, type=Path)
    parser.add_argument("--route-label", default=ROUTE_LABEL)
    parser.add_argument("--calibration-version", default=CALIBRATION_VERSION)
    args = parser.parse_args(argv)
    outputs = write_smoke_package(
        out_dir=args.out,
        calibration_artifact=args.calibration_artifact,
        failed_chunk_record=args.failed_chunk_record,
        candidate_volumes=None,
        route_label=args.route_label,
        calibration_version=args.calibration_version,
    )
    print(json.dumps(outputs, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
