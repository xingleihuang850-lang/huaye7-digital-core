#!/usr/bin/env python3
"""Validate a HY7 report provenance declaration without generating a report.

This design-stage validator accepts only a lightweight JSON declaration. It does
not read report inputs, render Office/PPT files, or upgrade scientific wording.
A passing declaration is ready for contract review only; a separate activation
decision is required before any generator consumes it.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SHA256 = re.compile(r"^[0-9a-f]{64}$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EVIDENCE_GRADES = {"XLSX_DIRECT", "XLSX_RECOMPUTED", "REPORT_DIRECT", "INTERPRETIVE", "diagnostic"}
REPORT_TYPES = {"word", "ppt", "excel"}


def _safe_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts


def _sha(value: Any) -> bool:
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def validate_report_declaration(declaration: dict[str, Any]) -> dict[str, Any]:
    """Fail closed for incomplete provenance while never authorizing rendering."""
    errors: list[str] = []
    checks: list[str] = []
    if not isinstance(declaration, dict):
        return {"passed": False, "errors": ["declaration must be an object"], "checks": checks,
                "verdict": "NOT_READY_FOR_CONTRACT_REVIEW", "render_authorized": False}
    if declaration.get("status") != "REPORT_PROVENANCE_DRAFT_NOT_ACTIVE":
        errors.append("status must be REPORT_PROVENANCE_DRAFT_NOT_ACTIVE")
    if declaration.get("render_authorized") is not False:
        errors.append("render_authorized must be false")
    if declaration.get("report_type") not in REPORT_TYPES:
        errors.append("report_type must be one of: word, ppt, excel")
    if not _safe_relative_path(declaration.get("generator_path")) or not _sha(declaration.get("generator_sha256")):
        errors.append("generator_path must be repository-relative and generator_sha256 must be a SHA-256 digest")
    stats = declaration.get("stats_input")
    if not isinstance(stats, dict) or stats.get("path") != "experiments/hy7_stats.json" or not _sha(stats.get("sha256")):
        errors.append("stats_input must declare experiments/hy7_stats.json and its SHA-256")
    else:
        checks.append("stats_input_declared")
    if not DATE.fullmatch(str(declaration.get("as_of", ""))):
        errors.append("as_of must be YYYY-MM-DD")

    evidence = declaration.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append("evidence must be a non-empty list")
    else:
        invalid = [item for item in evidence if not isinstance(item, dict) or not _safe_relative_path(item.get("path")) or not _sha(item.get("sha256")) or item.get("grade") not in EVIDENCE_GRADES]
        if invalid:
            errors.append("every evidence item requires repository-relative path, SHA-256, and allowed grade")
        else:
            checks.append("evidence_grades_declared")

    conclusions = declaration.get("allowed_conclusion_ids")
    if not isinstance(conclusions, list) or not conclusions or not all(isinstance(value, str) and value.startswith("HY7-") for value in conclusions):
        errors.append("allowed_conclusion_ids must be non-empty HY7-* identifiers")
    else:
        checks.append("conclusion_vocabulary_declared")
    outputs = declaration.get("outputs")
    if not isinstance(outputs, list) or not outputs or not all(_safe_relative_path(path) for path in outputs):
        errors.append("outputs must be non-empty repository-relative paths")
    else:
        checks.append("outputs_declared")
    return {
        "passed": not errors,
        "errors": errors,
        "checks": checks,
        "verdict": "READY_FOR_CONTRACT_REVIEW_ONLY" if not errors else "NOT_READY_FOR_CONTRACT_REVIEW",
        "render_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--declaration", type=Path, required=True)
    args = parser.parse_args(argv)
    result = validate_report_declaration(json.loads(args.declaration.read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
