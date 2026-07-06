#!/usr/bin/env python3
"""Audit HY7 B2-min design-entry constraints.

This module is deliberately lightweight: it checks manifests, constrained
selection summaries, and design/report wording for the calibrated B2-min
no-retraining boundary approved by the rock gate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

CALIBRATION_VERSION = "hy7-gray-calibration-qmatch-v1"
MAIN_CHECKPOINT = "ep015"
ORIG_RAW_STATUS = "known_fail"
FULL_BATCH_VARIANT = "ep015_all"

FORBIDDEN_CLAIMS = [
    "B1.1 unconditional pass",
    "ORIG raw passed",
    "qmatch optional",
    "selected chunk represents full model performance",
    "无条件通过",
    "ORIG raw 通过",
    "qmatch 可选",
    "B2-min 通过",
    "新训练已批准",
    "selected chunk 可以代表整体模型表现",
]

REQUIRED_MANIFEST_FORBIDDEN = {
    "unconditional_b1_1_pass_claim",
    "orig_raw_pass_claim",
    "second_b1_1_topology_rescue",
    "gate_relaxation",
    "implicit_qmatch",
}

REQUIRED_SELECTION_FORBIDDEN = {
    "no_retraining",
    "no_second_b1_1_topology_rescue",
    "no_gate_relaxation",
    "orig_raw_pass_claim",
    "explicit_qmatch_required",
}


def _result(errors: list[str], checks: list[str]) -> dict[str, Any]:
    return {"passed": not errors, "errors": errors, "checks": checks}


def audit_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    checks: list[str] = []
    if manifest.get("main_checkpoint") != MAIN_CHECKPOINT:
        errors.append("manifest.main_checkpoint must be ep015")
    else:
        checks.append("main_checkpoint_ep015")
    if manifest.get("calibration_version") != CALIBRATION_VERSION:
        errors.append("manifest.calibration_version must be hy7-gray-calibration-qmatch-v1")
    else:
        checks.append("calibration_version_explicit")
    if manifest.get("orig_raw_status") != ORIG_RAW_STATUS:
        errors.append("manifest.orig_raw_status must be known_fail")
    else:
        checks.append("orig_raw_known_fail")
    forbidden = set(manifest.get("forbidden") or [])
    missing = sorted(REQUIRED_MANIFEST_FORBIDDEN - forbidden)
    if missing:
        errors.append("manifest.forbidden missing: " + ", ".join(missing))
    else:
        checks.append("manifest_forbidden_constraints_present")
    return _result(errors, checks)


def audit_selection_summary(summary: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    checks: list[str] = []
    if summary.get("calibration_version") != CALIBRATION_VERSION:
        errors.append("selection.calibration_version must be hy7-gray-calibration-qmatch-v1")
    else:
        checks.append("selection_calibration_explicit")
    forbidden = set(summary.get("forbidden") or [])
    missing = sorted(REQUIRED_SELECTION_FORBIDDEN - forbidden)
    if missing:
        errors.append("selection.forbidden missing: " + ", ".join(missing))
    else:
        checks.append("selection_forbidden_constraints_present")
    rows = list(summary.get("rows") or [])
    variants = {row.get("variant") for row in rows}
    if FULL_BATCH_VARIANT not in variants:
        errors.append("selection.rows must include full-batch ep015_all")
    else:
        checks.append("full_batch_anchor_present")
    failed = [row for row in rows if not row.get("pass_gate")]
    if not failed:
        errors.append("selection.rows must include at least one failed/rejected row")
    else:
        checks.append("failed_selection_rows_visible")
    selected = summary.get("selected") or {}
    if selected.get("variant") == FULL_BATCH_VARIANT:
        errors.append("selection.selected must not use ep015_all as selected chunk triage row")
    elif selected.get("variant"):
        checks.append("selected_chunk_is_separate_from_full_batch")
    else:
        errors.append("selection.selected.variant is required")
    return _result(errors, checks)


def _is_prohibition_context(line: str) -> bool:
    lower = line.lower().strip()
    return bool(
        lower.startswith("-")
        or "forbidden" in lower
        or "prohibited" in lower
        or "do not" in lower
        or "not write" in lower
        or "禁止" in lower
        or "不得" in lower
    )


def audit_design_text(text: str) -> dict[str, Any]:
    errors: list[str] = []
    checks: list[str] = []
    for claim in FORBIDDEN_CLAIMS:
        claim_lower = claim.lower()
        unsafe_lines = [
            line.strip()
            for line in text.splitlines()
            if claim_lower in line.lower() and not _is_prohibition_context(line)
        ]
        if unsafe_lines:
            errors.append(f"forbidden claim present: {claim}")
    required_phrases = {
        "conditional_pass_boundary": "CONDITIONAL_PASS",
        "qmatch_explicit": CALIBRATION_VERSION,
        "full_batch_anchor": FULL_BATCH_VARIANT,
        "triage_only": "triage_only",
        "orig_raw_known_fail": "known_fail",
        "failed_row_visible": "ep015_chunk000_063",
        "formal_route_visible": "formal512 ep015@phi6.4",
        "nnunet_route_visible": "nnUNet ep015_qmatch",
    }
    for check, phrase in required_phrases.items():
        if phrase not in text:
            errors.append(f"design text missing required phrase: {phrase}")
        else:
            checks.append(check)
    if "no new training" not in text and "no training" not in text:
        errors.append("design text must state no new training")
    else:
        checks.append("no_new_training_boundary")
    return _result(errors, checks)


def audit_design_entry(manifest: dict[str, Any], selection: dict[str, Any], design_text: str) -> dict[str, Any]:
    parts = [audit_manifest(manifest), audit_selection_summary(selection), audit_design_text(design_text)]
    errors: list[str] = []
    checks: list[str] = []
    for part in parts:
        errors.extend(part["errors"])
        checks.extend(part["checks"])
    return _result(errors, checks)


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit HY7 B2-min design-entry constraints")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--selection-summary", required=True)
    parser.add_argument("--design-text", required=True)
    args = parser.parse_args(argv)
    result = audit_design_entry(
        _load_json(args.manifest),
        _load_json(args.selection_summary),
        Path(args.design_text).read_text(encoding="utf-8"),
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
