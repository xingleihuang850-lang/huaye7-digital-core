#!/usr/bin/env python3
"""Validate Stage3 A2-small design evidence without authorizing execution.

This tool reads only a lightweight JSON declaration. It never loads arrays,
generates phantoms, reconstructs volumes, trains, samples, or writes remote
files. A passing result means only that a future research gate can review the
declared prerequisites; it is not an A2 execution authorization.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REQUIRED_PHANTOMS = {
    "all_solid", "all_pore", "isolated_voxel", "straight_channel_x",
    "straight_channel_y", "straight_channel_z", "two_disconnected_blobs",
    "hollow_cube_shell_or_cavity", "torus_like_ring", "asymmetric_s2_boundary",
    "sparse_random_seeded_toy",
}
REQUIRED_SCALES = {"8^3", "16^3", "32^3"}
REQUIRED_ROUTE = {
    "formal_route": "threshold_formal_full_batch",
    "formal_anchor": "ep015_all",
    "diagnostic_route": "nnUNet ep015_qmatch",
    "triage_policy": "triage_only",
    "failed_chunk": "ep015_chunk000_063",
}
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _result(errors: list[str], checks: list[str]) -> dict[str, Any]:
    return {
        "passed": not errors,
        "errors": errors,
        "checks": checks,
        "verdict": "READY_FOR_FUTURE_GATE_REVIEW_ONLY" if not errors else "NOT_READY_FOR_GATE_REVIEW",
        "execution_authorized": False,
    }


def _require_sha256(value: Any, name: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        errors.append(f"{name} must be a lowercase SHA-256 hex digest")


def validate_a2_preflight(declaration: dict[str, Any]) -> dict[str, Any]:
    """Check all A2 design prerequisites while hard-coding no execution authority."""
    errors: list[str] = []
    checks: list[str] = []
    if not isinstance(declaration, dict):
        return _result(["preflight declaration must be an object"], checks)
    if declaration.get("status") != "A2_DESIGN_ONLY_PRE_GATE_REVIEW":
        errors.append("status must be A2_DESIGN_ONLY_PRE_GATE_REVIEW")
    if declaration.get("execution_authorized") is not False:
        errors.append("execution_authorized must be false")
    if declaration.get("scientific_status") != "design_only_not_evidence":
        errors.append("scientific_status must be design_only_not_evidence")

    source = declaration.get("source_identity")
    if not isinstance(source, dict):
        errors.append("source_identity must be an object")
    else:
        for field in ("input_slice_manifest_sha256", "cross_scale_registration_sha256"):
            _require_sha256(source.get(field), f"source_identity.{field}", errors)
        if source.get("axis_order") != "zyx":
            errors.append("source_identity.axis_order must be zyx")
        channels = source.get("condition_channels")
        if not isinstance(channels, list) or not channels:
            errors.append("source_identity.condition_channels must be a non-empty list")
        elif all(isinstance(channel, dict) and channel.get("name") and channel.get("units") and SHA256.fullmatch(str(channel.get("source_sha256", ""))) for channel in channels):
            checks.append("source_identity_declared")
        else:
            errors.append("every condition channel requires name, units, and source_sha256")

    route = declaration.get("route_constraints")
    if not isinstance(route, dict):
        errors.append("route_constraints must be an object")
    else:
        for field, expected in REQUIRED_ROUTE.items():
            if route.get(field) != expected:
                errors.append(f"route_constraints.{field} must be {expected}")
        if route.get("orig_raw_status") != "known_fail":
            errors.append("route_constraints.orig_raw_status must be known_fail")
        if route.get("qmatch_version") != "hy7-gray-calibration-qmatch-v1":
            errors.append("route_constraints.qmatch_version must be hy7-gray-calibration-qmatch-v1")
        if not errors:
            checks.append("route_constraints_declared")

    phantom = declaration.get("phantom_validation")
    if not isinstance(phantom, dict):
        errors.append("phantom_validation must be an object")
    else:
        missing = sorted(REQUIRED_PHANTOMS - set(phantom.get("completed_families") or []))
        if missing:
            errors.append("phantom_validation missing families: " + ", ".join(missing))
        missing_scales = sorted(REQUIRED_SCALES - set(phantom.get("completed_scales") or []))
        if missing_scales:
            errors.append("phantom_validation missing scales: " + ", ".join(missing_scales))
        if phantom.get("deterministic_regeneration") is not True:
            errors.append("phantom_validation.deterministic_regeneration must be true")
        if not missing and not missing_scales and phantom.get("deterministic_regeneration") is True:
            checks.append("phantom_suite_declared")

    metrics = declaration.get("metrics")
    required_metrics = {"phi_3d", "s2_3d", "connected_porosity_3d", "percolation_xyz", "largest_component_dual_denominator"}
    if not isinstance(metrics, dict) or not required_metrics.issubset({name for name, status in metrics.items() if status == "phantom_validated"}):
        errors.append("metrics must mark required 3D metrics as phantom_validated")
    elif metrics.get("euler_minkowski_3d") not in {"phantom_validated", "explicitly_de_scoped_fail_closed"}:
        errors.append("metrics.euler_minkowski_3d must be phantom_validated or explicitly_de_scoped_fail_closed")
    else:
        checks.append("metric_semantics_declared")
    return _result(errors, checks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args(argv)
    declaration = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = validate_a2_preflight(declaration)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
