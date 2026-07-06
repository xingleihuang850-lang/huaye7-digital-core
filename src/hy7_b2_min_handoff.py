#!/usr/bin/env python3
"""Create HY7 B2-min calibrated handoff dry-run bundle.

The bundle is metadata-only: no training, no new sampling, no new checkpoint, and
no large arrays. It packages the frozen ep015/qmatch evidence for downstream
multiscale 3D design handoff.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hy7_b2_min_audit as audit

STATUS = "calibrated_b2_min_handoff_design_dry_run"
CALIBRATION_VERSION = audit.CALIBRATION_VERSION
MAIN_CHECKPOINT = audit.MAIN_CHECKPOINT
ORIG_RAW_STATUS = audit.ORIG_RAW_STATUS
EXECUTION_BOUNDARY = "no_retraining_no_new_sampling_no_scaling_no_new_checkpoint"
ACCEPTANCE_ANCHOR = audit.FULL_BATCH_VARIANT

FORBIDDEN = [
    "unconditional_b1_1_pass_claim",
    "orig_raw_pass_claim",
    "second_b1_1_topology_rescue",
    "gate_relaxation",
    "implicit_qmatch",
]

FORBIDDEN_CLAIM_TEXT = [
    "B1.1 unconditional pass",
    "ORIG raw passed",
    "qmatch optional",
    "selected chunk represents full model performance",
    "B2-min passed",
    "100/200ep scaling approved",
    "new training approved",
]


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _find_row(rows: list[dict[str, Any]], variant: str) -> dict[str, Any]:
    for row in rows:
        if row.get("variant") == variant:
            return row
    raise ValueError(f"missing row: {variant}")


def failure_reasons(row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if float(row.get("s2_rmse", 0.0)) > 0.003:
        reasons.append("S2>0.003")
    if float(row.get("euler", 999.0)) < 115:
        reasons.append("Euler<115")
    if float(row.get("maxcc", 0.0)) > 0.070:
        reasons.append("maxCC>0.070")
    phi = float(row.get("phi", 6.4))
    if not (5.5 <= phi <= 6.8):
        reasons.append("phi_out_of_range")
    return reasons


def build_handoff_manifest(
    baseline_manifest: dict[str, Any],
    selection_summary: dict[str, Any],
    qmatch_manifest_path: str | Path,
    *,
    source_paths: dict[str, str],
) -> dict[str, Any]:
    selected = dict(selection_summary.get("selected") or {})
    return {
        "status": STATUS,
        "main_checkpoint": MAIN_CHECKPOINT,
        "calibration_version": CALIBRATION_VERSION,
        "orig_raw_status": ORIG_RAW_STATUS,
        "execution_boundary": EXECUTION_BOUNDARY,
        "acceptance_anchor": ACCEPTANCE_ANCHOR,
        "selected_chunk_policy": "triage_only",
        "selected_chunk": selected.get("variant"),
        "formal_route": "threshold_formal_full_batch",
        "nnunet_route": "qmatch_nnunet_diagnostic",
        "downstream_target": "multiscale_3d_digital_core_planning",
        "forbidden": FORBIDDEN,
        "source_paths": source_paths,
        "source_sha256": {
            "baseline_manifest": sha256_file(source_paths["baseline_manifest"]),
            "selection_summary": sha256_file(source_paths["selection_summary"]),
            "qmatch_manifest": sha256_file(qmatch_manifest_path),
        },
        "baseline_status": baseline_manifest.get("status"),
        "selection_status": selection_summary.get("status"),
    }


def build_metrics(baseline_manifest: dict[str, Any], selection_summary: dict[str, Any]) -> dict[str, Any]:
    rows = list(selection_summary.get("rows") or [])
    full_batch = _find_row(rows, ACCEPTANCE_ANCHOR)
    evidence = baseline_manifest.get("evidence_summary") or {}
    return {
        "formal_full_batch_ep015_all": full_batch,
        "formal512_ep015_phi64": evidence.get("formal512_ep015_phi64", {}),
        "nnunet_ep015_qmatch": evidence.get("nnunet_ep015_qmatch", {}),
        "qmatch_generalization_ep015": evidence.get("qmatch_generalization_ep015", {}),
        "interpretation": "formal threshold and nnUNet-qmatch routes are both supportive but numerically distinct; do not merge them into one unlabeled metric.",
    }


def build_candidate_rows(selection_summary: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for row in selection_summary.get("rows") or []:
        out = dict(row)
        out["policy"] = "acceptance_anchor" if row.get("variant") == ACCEPTANCE_ANCHOR else "triage_only"
        out["failure_reasons"] = [] if row.get("pass_gate") else failure_reasons(row)
        rows.append(out)
    if not rows:
        raise ValueError("selection summary has no rows")
    _find_row(rows, ACCEPTANCE_ANCHOR)
    selected = (selection_summary.get("selected") or {}).get("variant")
    return {
        "selected_variant": selected,
        "selected_policy": "triage_only",
        "full_batch_variant": ACCEPTANCE_ANCHOR,
        "full_batch_policy": "acceptance_anchor",
        "rows": rows,
    }


def render_readme(manifest: dict[str, Any], metrics: dict[str, Any], candidates: dict[str, Any]) -> str:
    full = metrics["formal_full_batch_ep015_all"]
    nn = metrics["nnunet_ep015_qmatch"]
    return f"""# HY7 B2-min calibrated handoff dry-run bundle

Status: `{manifest['status']}`

B2-min design-entry gate = CONDITIONAL_PASS.

Main checkpoint: `{manifest['main_checkpoint']}`

Required calibration: `{manifest['calibration_version']}`

ORIG raw status: `{manifest['orig_raw_status']}` / known_fail.

Execution boundary: `{manifest['execution_boundary']}` / no new training.

Acceptance anchor: `{manifest['acceptance_anchor']}`.

Selected chunk policy: `triage_only`.

## Formal route

formal512 ep015@phi6.4 and full-batch `ep015_all` are the threshold-formal route.

Full-batch `ep015_all`:

```json
{json.dumps(full, indent=2, ensure_ascii=False)}
```

## nnUNet-qmatch route

nnUNet ep015_qmatch is a calibrated diagnostic route and remains numerically distinct from the formal route.

```json
{json.dumps(nn, indent=2, ensure_ascii=False)}
```

## Candidate rows

Selected chunk `{candidates['selected_variant']}` is triage_only. It is not the acceptance anchor.

Failed/rejected rows remain visible in `candidate_rows.json`; notably `ep015_chunk000_063` failed because maxCC>0.070.

## Forbidden claims / do not write

""" + "\n".join(f"- {x}" for x in FORBIDDEN_CLAIM_TEXT) + "\n"


def write_handoff_bundle(
    baseline_manifest_path: str | Path,
    selection_summary_path: str | Path,
    qmatch_manifest_path: str | Path,
    design_text_path: str | Path,
    out_dir: str | Path,
) -> dict[str, str]:
    baseline_manifest_path = Path(baseline_manifest_path)
    selection_summary_path = Path(selection_summary_path)
    qmatch_manifest_path = Path(qmatch_manifest_path)
    design_text_path = Path(design_text_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    baseline_manifest = _load_json(baseline_manifest_path)
    selection_summary = _load_json(selection_summary_path)
    design_text = design_text_path.read_text(encoding="utf-8")

    preflight = audit.audit_design_entry(baseline_manifest, selection_summary, design_text)
    if not preflight["passed"]:
        raise ValueError("preflight audit failed: " + "; ".join(preflight["errors"]))

    source_paths = {
        "baseline_manifest": str(baseline_manifest_path),
        "selection_summary": str(selection_summary_path),
        "qmatch_manifest": str(qmatch_manifest_path),
        "design_text": str(design_text_path),
    }
    manifest = build_handoff_manifest(baseline_manifest, selection_summary, qmatch_manifest_path, source_paths=source_paths)
    metrics = build_metrics(baseline_manifest, selection_summary)
    candidates = build_candidate_rows(selection_summary)
    readme = render_readme(manifest, metrics, candidates)
    audit_report = audit.audit_design_entry(manifest, selection_summary, readme)
    if not audit_report["passed"]:
        raise ValueError("handoff audit failed: " + "; ".join(audit_report["errors"]))

    paths = {
        "handoff_manifest": out / "handoff_manifest.json",
        "handoff_readme": out / "handoff_readme.md",
        "formal_vs_qmatch_metrics": out / "formal_vs_qmatch_metrics.json",
        "candidate_rows": out / "candidate_rows.json",
        "forbidden_claims": out / "forbidden_claims.txt",
        "audit_report": out / "audit_report.json",
        "ordered_view_links": out / "ordered_view_links.txt",
        "hashes": out / "hashes.txt",
    }
    paths["handoff_manifest"].write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["handoff_readme"].write_text(readme, encoding="utf-8")
    paths["formal_vs_qmatch_metrics"].write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["candidate_rows"].write_text(json.dumps(candidates, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["forbidden_claims"].write_text("\n".join(FORBIDDEN_CLAIM_TEXT) + "\n", encoding="utf-8")
    paths["audit_report"].write_text(json.dumps(audit_report, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["ordered_view_links"].write_text(
        "00_ORDERED_VIEW/05_b2_min_calibrated/00_baseline_package_ep015\n"
        "00_ORDERED_VIEW/05_b2_min_calibrated/01_constrained_selection_smoke_ep015\n",
        encoding="utf-8",
    )
    hash_lines = []
    for key, path in paths.items():
        if key == "hashes":
            continue
        hash_lines.append(f"{sha256_file(path)}  {path.name}")
    paths["hashes"].write_text("\n".join(hash_lines) + "\n", encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Create HY7 B2-min calibrated handoff dry-run bundle")
    p.add_argument("--baseline-manifest", required=True)
    p.add_argument("--selection-summary", required=True)
    p.add_argument("--qmatch-manifest", required=True)
    p.add_argument("--design-text", required=True)
    p.add_argument("--out", required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    outputs = write_handoff_bundle(
        args.baseline_manifest,
        args.selection_summary,
        args.qmatch_manifest,
        args.design_text,
        args.out,
    )
    print(json.dumps(outputs, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
