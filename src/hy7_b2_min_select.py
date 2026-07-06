#!/usr/bin/env python3
"""Calibrated B2-min constrained selection smoke.

No training happens here.  The script takes generated gray samples from the
frozen B1.1 ep015 candidate, applies documented qmatch calibration, evaluates
pre-registered formal pore metrics on chunks plus the full batch, and records a
single selected candidate by a deterministic score.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hy7_gray_calibration as cal
import hy7_phase2_ddpm as ddpm

STATUS = "calibrated_constrained_selection_smoke"
CALIBRATION_VERSION = cal.VERSION
TARGET_EULER = 120.0

FORBIDDEN = [
    "no_retraining",
    "no_second_b1_1_topology_rescue",
    "no_gate_relaxation",
    "orig_raw_pass_claim",
    "explicit_qmatch_required",
]


def candidate_score(row: dict[str, Any]) -> tuple[int, float, float, float, float]:
    """Sort key: passing candidates first, then closest formal topology fit."""
    failed = 0 if row.get("pass_gate") else 1
    return (
        failed,
        float(row.get("s2_rmse", float("inf"))),
        abs(float(row.get("euler", 0.0)) - TARGET_EULER),
        float(row.get("maxcc", float("inf"))),
        abs(float(row.get("phi", 0.0)) - 6.4),
    )


def select_best_candidate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("no candidates to select")
    selected = dict(min(rows, key=candidate_score))
    selected["selection_reason"] = "passed_gate_min_score" if selected.get("pass_gate") else "no_gate_pass_min_score"
    selected["selection_score"] = list(candidate_score(selected))
    return selected


def make_chunk_candidates(total: int, chunk_size: int, prefix: str) -> list[dict[str, int | str]]:
    if total <= 0:
        raise ValueError("total must be positive")
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    out: list[dict[str, int | str]] = []
    for start in range(0, total, chunk_size):
        stop = min(start + chunk_size, total)
        out.append({"variant": f"{prefix}_chunk{start:03d}_{stop - 1:03d}", "start": start, "stop": stop})
    out.append({"variant": f"{prefix}_all", "start": 0, "stop": total})
    return out


def pass_gate(metrics: dict[str, Any]) -> bool:
    return bool(
        metrics["s2_rmse"] <= 0.003
        and metrics["euler"] >= 115
        and metrics["maxcc"] <= 0.070
        and 5.5 <= metrics["phi"] <= 6.8
    )


def evaluate_candidates(
    gray: np.ndarray,
    reference_gray_path: str | Path,
    real_pore: np.ndarray,
    *,
    chunk_size: int,
    reference_split: str,
    phi_target: float,
    rmax: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    qmatch, manifest = cal.calibrate_array(gray.astype(np.float32), reference_gray_path, split=reference_split)
    rows: list[dict[str, Any]] = []
    for cand in make_chunk_candidates(qmatch.shape[0], chunk_size, "ep015"):
        start = int(cand["start"])
        stop = int(cand["stop"])
        arr = qmatch[start:stop]
        real = real_pore[start:stop]
        threshold = ddpm.threshold_for_porosity(arr, phi_target)
        pore = arr <= threshold
        metrics = ddpm.formal_binary_pore_metrics(pore, real, rmax=rmax)
        row = {
            "variant": str(cand["variant"]),
            "start": start,
            "stop": stop,
            "n": stop - start,
            "phi_target": phi_target,
            "threshold": float(threshold),
            **metrics,
        }
        row["pass_gate"] = pass_gate(row)
        rows.append(row)
    return rows, manifest


def build_summary(rows: list[dict[str, Any]], *, calibration_version: str) -> dict[str, Any]:
    selected = select_best_candidate(rows)
    return {
        "status": STATUS,
        "calibration_version": calibration_version,
        "selection_method": "pass_gate_then_min_s2_then_abs_euler_minus_120_then_maxcc_then_abs_phi_minus_6p4",
        "forbidden": FORBIDDEN,
        "selected": selected,
        "rows": rows,
    }


def write_outputs(summary: dict[str, Any], manifest: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    summary_path = out / "selection_summary.json"
    md_path = out / "selection_summary.md"
    manifest_path = out / "qmatch_manifest.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(summary), encoding="utf-8")
    return {"summary": str(summary_path), "summary_md": str(md_path), "qmatch_manifest": str(manifest_path)}


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# HY7 calibrated B2-min constrained selection smoke",
        "",
        f"Status: `{summary['status']}`",
        f"Calibration: `{summary['calibration_version']}`",
        "",
        "## Selected candidate",
        "",
        "```json",
        json.dumps(summary["selected"], indent=2),
        "```",
        "",
        "## Candidate table",
        "",
        "| variant | n | phi | S2 rmse | Euler | maxCC | pass |",
        "|---|---:|---:|---:|---:|---:|:---:|",
    ]
    for r in summary["rows"]:
        lines.append(
            f"| {r['variant']} | {r.get('n', '')} | {r['phi']:.3f} | {r['s2_rmse']:.5f} | "
            f"{r['euler']:.2f} | {r['maxcc']:.4f} | {r['pass_gate']} |"
        )
    lines.extend(["", "## Forbidden", ""])
    lines.extend(f"- {x}" for x in summary["forbidden"])
    lines.append("")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run calibrated B2-min constrained selection smoke without training")
    p.add_argument("--samples-gray", required=True)
    p.add_argument("--reference-gray", required=True)
    p.add_argument("--real-pore", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--chunk-size", type=int, default=64)
    p.add_argument("--reference-split", default="all", choices=["all", "even", "odd"])
    p.add_argument("--phi-target", type=float, default=6.4)
    p.add_argument("--rmax", type=int, default=48)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    gray = np.load(args.samples_gray).astype(np.float32)
    real_pore = np.load(args.real_pore).astype(bool)
    rows, manifest = evaluate_candidates(
        gray,
        args.reference_gray,
        real_pore,
        chunk_size=args.chunk_size,
        reference_split=args.reference_split,
        phi_target=args.phi_target,
        rmax=args.rmax,
    )
    summary = build_summary(rows, calibration_version=CALIBRATION_VERSION)
    outputs = write_outputs(summary, manifest, args.out)
    print(json.dumps(outputs, indent=2))
    print(json.dumps(summary["selected"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
