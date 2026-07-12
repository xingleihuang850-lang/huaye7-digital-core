#!/usr/bin/env python3
"""Package HY7 calibrated B2-min baseline evidence.

This does not launch training. It records the frozen B1.1 conditional-pass
checkpoint and the calibrated/qmatch evidence required before B2-min work.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

STATUS = "calibrated_b2_min_candidate"
CALIBRATION_VERSION = "hy7-gray-calibration-qmatch-v1"
MAIN_CHECKPOINT = "ep015"
ORIG_RAW_STATUS = "known_fail"


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def _find_row(rows: list[dict[str, Any]], variant: str) -> dict[str, Any] | None:
    for row in rows:
        if row.get("variant") == variant:
            return row
    return None


def _require_number(value: Any, name: str) -> float:
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def _require_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")
    return value


def _require_row(rows: Any, variant: str, fields: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("evidence rows must be a list of objects")
    row = _find_row(rows, variant)
    if row is None:
        raise ValueError(f"evidence rows missing required variant: {variant}")
    for field in fields:
        if field not in row:
            raise ValueError(f"evidence row {variant} missing: {field}")
    return row


def summarize_evidence(formal512: dict[str, Any], nnunet: dict[str, Any], qmatch_generalization: dict[str, Any]) -> dict[str, Any]:
    if not all(isinstance(data, dict) for data in (formal512, nnunet, qmatch_generalization)):
        raise ValueError("formal512, nnunet, and qmatch generalization evidence must be JSON objects")
    formal_phi64 = formal512.get("phi64")
    if not isinstance(formal_phi64, dict):
        raise ValueError("formal512 missing required object: phi64")
    for field in ("s2_rmse", "euler", "maxcc"):
        _require_number(formal_phi64.get(field), f"formal512.phi64.{field}")
    _require_bool(formal_phi64.get("passed_gate"), "formal512.phi64.passed_gate")
    nn_ep015 = _require_row(nnunet.get("rows"), "ep015_qmatch", ("phi", "s2_rmse", "euler", "maxcc", "reverse_fail"))
    for field in ("phi", "s2_rmse", "euler", "maxcc"):
        _require_number(nn_ep015[field], f"nnunet.ep015_qmatch.{field}")
    _require_bool(nn_ep015["reverse_fail"], "nnunet.ep015_qmatch.reverse_fail")
    gen_even = _require_row(qmatch_generalization.get("rows"), "ep015_qmatch_even", ("pass_gate", "euler"))
    gen_odd = _require_row(qmatch_generalization.get("rows"), "ep015_qmatch_odd", ("pass_gate", "euler"))
    for row, variant in ((gen_even, "even"), (gen_odd, "odd")):
        _require_bool(row["pass_gate"], f"qmatch_generalization.{variant}.pass_gate")
        _require_number(row["euler"], f"qmatch_generalization.{variant}.euler")
    return {
        "formal512_ep015_phi64": {
            "s2_rmse": formal_phi64.get("s2_rmse"),
            "euler": formal_phi64.get("euler"),
            "maxcc": formal_phi64.get("maxcc"),
            "passed_gate": formal_phi64.get("passed_gate"),
        },
        "nnunet_ep015_qmatch": {
            "phi": nn_ep015.get("phi"),
            "s2_rmse": nn_ep015.get("s2_rmse"),
            "euler": nn_ep015.get("euler"),
            "maxcc": nn_ep015.get("maxcc"),
            "reverse_fail": nn_ep015.get("reverse_fail"),
        },
        "qmatch_generalization_ep015": {
            "even_pass": gen_even.get("pass_gate"),
            "odd_pass": gen_odd.get("pass_gate"),
            "even_euler": gen_even.get("euler"),
            "odd_euler": gen_odd.get("euler"),
        },
    }


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    paths = {
        "checkpoint": Path(args.checkpoint),
        "formal512": Path(args.formal512),
        "nnunet": Path(args.nnunet),
        "qmatch_generalization": Path(args.qmatch_generalization),
        "calibration_module": Path(args.calibration_module),
    }
    missing = [str(p) for p in paths.values() if not p.exists()]
    if missing:
        raise FileNotFoundError("missing required files: " + ", ".join(missing))
    formal = _load_json(paths["formal512"])
    nnunet = _load_json(paths["nnunet"])
    qgen = _load_json(paths["qmatch_generalization"])
    files = {name: {"path": str(path), "sha256": sha256_file(path)} for name, path in paths.items()}
    return {
        "status": STATUS,
        "main_checkpoint": MAIN_CHECKPOINT,
        "calibration_version": CALIBRATION_VERSION,
        "orig_raw_status": ORIG_RAW_STATUS,
        "allowed_next_step": "calibrated_b2_min_baseline_or_constrained_selection",
        "forbidden": [
            "unconditional_b1_1_pass_claim",
            "orig_raw_pass_claim",
            "second_b1_1_topology_rescue",
            "gate_relaxation",
            "implicit_qmatch",
        ],
        "files": files,
        "evidence_summary": summarize_evidence(formal, nnunet, qgen),
    }


def write_package(manifest: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "b2_min_manifest.json"
    readme_path = out / "b2_min_readme.md"
    hashes_path = out / "hashes.txt"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    readme_path.write_text(render_readme(manifest), encoding="utf-8")
    hashes = []
    for path in [manifest_path, readme_path]:
        hashes.append(f"{sha256_file(path)}  {path.name}")
    hashes_path.write_text("\n".join(hashes) + "\n", encoding="utf-8")
    return {"manifest": str(manifest_path), "readme": str(readme_path), "hashes": str(hashes_path)}


def render_readme(manifest: dict[str, Any]) -> str:
    ev = manifest["evidence_summary"]
    return f"""# HY7 Calibrated B2-min Baseline Package

Status: `{manifest['status']}`

Main checkpoint: `{manifest['main_checkpoint']}`

Required calibration: `{manifest['calibration_version']}`

ORIG raw status: `{manifest['orig_raw_status']}`

## Evidence summary

Formal512 ep015@φ6.4:

```json
{json.dumps(ev['formal512_ep015_phi64'], indent=2)}
```

nnUNet ep015_qmatch:

```json
{json.dumps(ev['nnunet_ep015_qmatch'], indent=2)}
```

qmatch generalization ep015:

```json
{json.dumps(ev['qmatch_generalization_ep015'], indent=2)}
```

## Forbidden

""" + "\n".join(f"- {x}" for x in manifest["forbidden"]) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Package HY7 calibrated B2-min baseline evidence")
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--formal512", required=True)
    p.add_argument("--nnunet", required=True)
    p.add_argument("--qmatch-generalization", required=True)
    p.add_argument("--calibration-module", required=True)
    p.add_argument("--out", required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    manifest = build_manifest(args)
    outputs = write_package(manifest, args.out)
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
