#!/usr/bin/env python3
"""HY7 Stage 3 Branch A A1 toy metric-plumbing dry-run.

This module is intentionally limited to synthetic known-answer phantoms. It does
not train, sample from a model, create a checkpoint, reconstruct HY7 volumes, or
emit a scientific voxel artifact. Its purpose is to verify 3D metric plumbing and
package shape under the A1 gate verdict `ALLOW_A1_WITH_CONSTRAINTS`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from collections import deque
from pathlib import Path
from typing import Any

import numpy as np

DATE = "2026-07-06"
VERDICT = "ALLOW_A1_WITH_CONSTRAINTS"
ROUTE_LABEL = "synthetic_toy_plumbing"
SCIENTIFIC_STATUS = "not_evidence"
INPUT_TYPE = "synthetic_toy"

FORBIDDEN_CLAIMS = [
    "B2-min final pass claim",
    "B1.1 unconditional pass claim",
    "ORIG raw pass claim",
    "qmatch optional claim / implicit qmatch",
    "selected 64-slice chunk represents full model performance",
    "formal route and nnUNet-qmatch route merged without labels",
    "x/y 2D penetrate proves 3D permeability or 3D connectivity",
    "Stage 3 planning promotion authorizes actual 3D generation",
    "training without a new gate",
    "new sampling from DDPM or any generative model without a new gate",
    "new checkpoint without a new gate",
    "voxel export as scientific output",
    "committing large volumes or weights to git",
    "A2 or real reconstruction without a new explicit gate",
]


def _as_binary_volume(volume: np.ndarray) -> np.ndarray:
    arr = np.asarray(volume, dtype=np.uint8)
    if arr.ndim != 3:
        raise ValueError(f"expected 3D volume, got shape {arr.shape}")
    return (arr > 0).astype(np.uint8)


def known_answer_phantoms(size: int = 8) -> dict[str, np.ndarray]:
    if size < 4:
        raise ValueError("size must be >= 4")
    mid = size // 2
    phantoms: dict[str, np.ndarray] = {}
    phantoms["all_solid"] = np.zeros((size, size, size), dtype=np.uint8)
    phantoms["all_pore"] = np.ones((size, size, size), dtype=np.uint8)
    x_channel = np.zeros((size, size, size), dtype=np.uint8)
    x_channel[:, mid, mid] = 1
    phantoms["x_channel"] = x_channel
    isolated = np.zeros((size, size, size), dtype=np.uint8)
    isolated[mid, mid, mid] = 1
    phantoms["isolated_voxel"] = isolated
    return phantoms


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
    starts = np.argwhere(arr > 0)
    for sx, sy, sz in starts:
        start = (int(sx), int(sy), int(sz))
        if seen[start]:
            continue
        comp: list[tuple[int, int, int]] = []
        q: deque[tuple[int, int, int]] = deque([start])
        seen[start] = True
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
    return min(coords) == 0 and max(coords) == shape[axis] - 1


def _s2_lag1_valid_pairs(volume: np.ndarray) -> dict[str, float]:
    arr = _as_binary_volume(volume).astype(bool)
    pairs = {
        "x": arr[:-1, :, :] & arr[1:, :, :],
        "y": arr[:, :-1, :] & arr[:, 1:, :],
        "z": arr[:, :, :-1] & arr[:, :, 1:],
    }
    return {axis: float(mask.mean()) for axis, mask in pairs.items()}


def compute_3d_metrics(volume: np.ndarray) -> dict[str, Any]:
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
        "porosity_phi_3d": {"status": "implemented", "value": float(pore / total) if total else 0.0},
        "s2_two_point_correlation_3d": {
            "status": "proxy",
            "proxy_name": "lag_1_valid_pairs_no_wrap",
            "axes": ["x", "y", "z"],
            "normalization": "valid adjacent voxel pairs per axis; no periodic wrap",
            "value": {"lag_1_valid_pairs": _s2_lag1_valid_pairs(arr)},
        },
        "connected_porosity_ratio_3d": {
            "status": "implemented",
            "connectivity": "pore-phase 6-neighborhood",
            "value": {"pore_voxel_basis": pore_basis, "total_volume_basis": total_basis},
        },
        "percolation_flags_3d": {
            "status": "implemented",
            "definition": "a single pore-phase connected component touches both opposing faces along axis k",
            "connectivity": "pore-phase 6-neighborhood",
            "value": percolation,
        },
        "largest_connected_component_fraction_3d": {
            "status": "implemented",
            "connectivity": "pore-phase 6-neighborhood",
            "value": {"pore_voxel_basis": pore_basis, "total_volume_basis": total_basis},
        },
        "euler_characteristic_or_minkowski_3d": {
            "status": "NOT_IMPLEMENTED_FAIL_CLOSED",
            "reason": "3D Euler/Minkowski implementation is intentionally not claimed in A1; future implementation must add known-answer tests.",
        },
    }


def validate_known_answer_phantoms(phantoms: dict[str, np.ndarray] | None = None) -> dict[str, Any]:
    phantoms = phantoms or known_answer_phantoms()
    errors: list[str] = []
    metrics = {name: compute_3d_metrics(vol) for name, vol in phantoms.items()}

    def expect(name: str, field: str, got: Any, want: Any):
        if got != want:
            errors.append(f"{name} {field}: got {got!r}, expected {want!r}")

    expect("all_solid", "porosity", metrics["all_solid"]["porosity_phi_3d"]["value"], 0.0)
    expect(
        "all_solid",
        "percolation",
        metrics["all_solid"]["percolation_flags_3d"]["value"],
        {"x": False, "y": False, "z": False},
    )
    expect("all_pore", "porosity", metrics["all_pore"]["porosity_phi_3d"]["value"], 1.0)
    expect(
        "all_pore",
        "percolation",
        metrics["all_pore"]["percolation_flags_3d"]["value"],
        {"x": True, "y": True, "z": True},
    )
    expect(
        "x_channel",
        "percolation",
        metrics["x_channel"]["percolation_flags_3d"]["value"],
        {"x": True, "y": False, "z": False},
    )
    expect(
        "isolated_voxel",
        "percolation",
        metrics["isolated_voxel"]["percolation_flags_3d"]["value"],
        {"x": False, "y": False, "z": False},
    )

    return {"passed": not errors, "errors": errors, "phantom_count": len(phantoms)}


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
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
    }


def _connectivity_semantics_text() -> str:
    return """# HY7 Stage 3 Branch A A1 connectivity semantics

Status: synthetic toy metric-plumbing only; not HY7 scientific evidence.

- pore-phase connectivity: 6-neighborhood (face-connected voxels only).
- complementary solid connectivity: 26-neighborhood is declared for future Euler/Minkowski work to avoid dual-connectivity ambiguity, but solid components are not used by this A1 implementation.
- percolation definition: a single pore-phase connected component touches both opposing faces along axis k.
- x/y/z axes map to ndarray axes 0/1/2 in the synthetic toy volume.
- 2D x/y penetrate inherited from Stage 2 remains 2D tile-level only and must not be interpreted as 3D permeability or 3D connectivity.
- Euler/Minkowski status: NOT_IMPLEMENTED_FAIL_CLOSED in A1.
"""


def _readme_text() -> str:
    return """# HY7 Stage 3 Branch A A1 toy metric-plumbing dry-run

This package is not HY7 scientific evidence. It only verifies 3D metric code paths and artifact package shape using known-answer synthetic phantoms.

## Gate verdict

`ALLOW_A1_WITH_CONSTRAINTS`

## Boundary

- no training
- no new sampling from any model
- no checkpoint
- no actual 2D→3D reconstruction
- no voxel export as scientific output
- no B2-min final pass claim

## Known-answer phantom suite

The package validates all-solid, all-pore, single x-axis through-channel, and isolated-voxel phantoms. A run that only avoids crashing is not enough; expected porosity/percolation/connectivity values must match known answers.

## Toy volume policy

No toy volume is committed. This package contains metrics and provenance only. If future toy arrays are materialized, they must remain untracked or outside git and be recorded only by path/hash/size.

## Euler status

3D Euler/Minkowski is explicitly `NOT_IMPLEMENTED_FAIL_CLOSED`; it is not omitted or silently treated as passing.
"""


def write_a1_package(out_dir: Path, size: int = 8, seed: int = 20260706) -> dict[str, str]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    phantoms = known_answer_phantoms(size=size)
    validation = validate_known_answer_phantoms(phantoms)
    if not validation["passed"]:
        raise ValueError(f"known-answer phantom validation failed: {validation['errors']}")

    metrics = {
        "workflow_node": "HY7-stage3-branch-A-A1-toy-metric-plumbing",
        "date": DATE,
        "verdict": VERDICT,
        "input_type": INPUT_TYPE,
        "scientific_status": SCIENTIFIC_STATUS,
        "route_label": ROUTE_LABEL,
        "volume_size": [size, size, size],
        "voxel_spacing": "synthetic_no_physical_spacing",
        "seed": seed,
        "toy_generator": "deterministic_known_answer_phantoms",
        "known_answer_phantom_suite": validation,
        "toy_metrics": {name: compute_3d_metrics(vol) for name, vol in phantoms.items()},
    }

    manifest = {
        "workflow_node": "HY7-stage3-branch-A-A1-toy-metric-plumbing",
        "date": DATE,
        "verdict": VERDICT,
        "input_type": INPUT_TYPE,
        "scientific_status": SCIENTIFIC_STATUS,
        "route_label": ROUTE_LABEL,
        "purpose": "verify 3D metric code paths and artifact package shape only",
        "volume_size": [size, size, size],
        "voxel_spacing": "synthetic_no_physical_spacing",
        "seed": seed,
        "toy_generator": "deterministic_known_answer_phantoms",
        "volume_committed_to_git": False,
        "toy_volume_path": None,
        "execution_boundary": {
            "no_training": True,
            "no_new_sampling_from_model": True,
            "no_checkpoint": True,
            "no_actual_2d_to_3d_reconstruction": True,
            "no_hy7_scientific_claim": True,
        },
        "source": {"git_commit": _git_commit(), "command": " ".join(sys.argv), "environment": _environment()},
        "required_outputs": [
            "branch_a_a1_manifest.json",
            "branch_a_a1_readme.md",
            "metrics_3d_toy.json",
            "connectivity_semantics.md",
            "forbidden_claims.txt",
            "hashes.txt",
        ],
    }

    outputs = {
        "branch_a_a1_manifest": out_dir / "branch_a_a1_manifest.json",
        "branch_a_a1_readme": out_dir / "branch_a_a1_readme.md",
        "metrics_3d_toy": out_dir / "metrics_3d_toy.json",
        "connectivity_semantics": out_dir / "connectivity_semantics.md",
        "forbidden_claims": out_dir / "forbidden_claims.txt",
        "hashes": out_dir / "hashes.txt",
    }

    _write_json(outputs["branch_a_a1_manifest"], manifest)
    outputs["branch_a_a1_readme"].write_text(_readme_text(), encoding="utf-8")
    _write_json(outputs["metrics_3d_toy"], metrics)
    outputs["connectivity_semantics"].write_text(_connectivity_semantics_text(), encoding="utf-8")
    outputs["forbidden_claims"].write_text("\n".join(FORBIDDEN_CLAIMS) + "\n", encoding="utf-8")

    hash_lines = []
    for key, path in outputs.items():
        if key == "hashes":
            continue
        hash_lines.append(f"{_sha256(path)}  {path.name}")
    outputs["hashes"].write_text("\n".join(hash_lines) + "\n", encoding="utf-8")

    return {key: str(path) for key, path in outputs.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260706)
    args = parser.parse_args(argv)
    outputs = write_a1_package(args.out, size=args.size, seed=args.seed)
    print(json.dumps(outputs, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
