#!/usr/bin/env python3
"""Read-only deployment audit for the HY7 macOS/Linux code boundary.

The local Git checkout is the only managed source. This tool compares only
declared small Python files with their approved remote target path by running
remote ``sha256sum`` through SSH. It never invokes rsync, scp, shell redirection,
or a remote write command.

Policy:
  - PlanB Stage-1 files target ``HY7_planb/src``.
  - Stage-2 data/DDPM/B1/B2 package files target ``HY7_planb/phase2``.
  - Statistics/reporting, B2 audit/handoff, and Stage-3 files are local-only.

``sync_allowed`` only means a mapped remote target differs and could be synced
after explicit human approval. This program cannot perform that sync.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REMOTE_ROOT = "/home/user/HXL/HY7_planb"
DEFAULT_REMOTE_ALIAS = "hy7-linux-lan"


@dataclass(frozen=True)
class DeploymentTarget:
    filename: str
    stage: str
    remote_subdir: str | None
    rationale: str


PHASE1_SRC = (
    "hy7_mpl_cjk.py",
    "hy7_planb_io.py",
    "hy7_planb_check_alignment.py",
    "hy7_planb_verify_nonleak.py",
    "hy7_planb_dataset.py",
    "hy7_planb_train.py",
    "hy7_planb_make_nnunet.py",
    "hy7_ct14_make_nnunet_3phase.py",
    "hy7_amics_make_nnunet.py",
)
PHASE2_RUNTIME = (
    "hy7_phase2_make_slices.py",
    "hy7_phase2_make_gray_slices.py",
    "hy7_phase2_ddpm.py",
    "hy7_phase2_eval.py",
    "hy7_phase2_threshold_calib.py",
    "hy7_gray_calibration.py",
    "hy7_b2_min_select.py",
    "hy7_b2_min_package.py",
)
LOCAL_ONLY = (
    "etl_build_warehouse.py",
    "hy7_etl.py",
    "verify_hy7.py",
    "verify_integrity.py",
    "hy7_figures.py",
    "hy7_make_excel.py",
    "hy7_make_word.py",
    "hy7_make_ppt.py",
    "make_figures.py",
    "make_excel.py",
    "make_word.py",
    "make_ppt.py",
    "hy7_b2_min_audit.py",
    "hy7_b2_min_handoff.py",
    "hy7_stage3_minimal_3d_smoke.py",
    "hy7_stage3_inter_slice_audit.py",
    "hy7_stage3_branch_a_a1_toy.py",
    "hy7_remote_sync_audit.py",
)

DEPLOYMENT_MAP = tuple(
    DeploymentTarget(name, "phase1_planb", "src", "Stage-1 PlanB remote runtime")
    for name in PHASE1_SRC
) + tuple(
    DeploymentTarget(name, "phase2_ddpm_b1_b2", "phase2", "Stage-2 managed runtime")
    for name in PHASE2_RUNTIME
) + tuple(
    DeploymentTarget(name, "local_only", None, "No approved remote deployment target")
    for name in LOCAL_ONLY
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _parse_sha256(stdout: str) -> str | None:
    fields = stdout.strip().split()
    if fields and len(fields[0]) == 64 and all(ch in "0123456789abcdef" for ch in fields[0].lower()):
        return fields[0].lower()
    return None


def remote_sha256(
    remote_alias: str,
    remote_path: str,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, str | None]:
    """Run only ``sha256sum`` remotely and normalize its read-only result."""
    completed = runner(
        ["ssh", "-o", "BatchMode=yes", remote_alias, "sha256sum", remote_path],
        capture_output=True,
        text=True,
        check=False,
    )
    digest = _parse_sha256(completed.stdout)
    if completed.returncode == 0 and digest:
        return {"status": "ok", "sha256": digest, "detail": None}
    detail = (completed.stderr or completed.stdout or f"ssh exit {completed.returncode}").strip()
    if "No such file" in detail or "cannot open" in detail:
        return {"status": "missing", "sha256": None, "detail": detail}
    return {"status": "error", "sha256": None, "detail": detail}


def audit_deployment(
    local_root: str | Path = ROOT,
    remote_alias: str = DEFAULT_REMOTE_ALIAS,
    remote_root: str = DEFAULT_REMOTE_ROOT,
    targets: Sequence[DeploymentTarget] = DEPLOYMENT_MAP,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    """Compare declared files only; no result can cause a remote modification."""
    local_root = Path(local_root)
    records: list[dict[str, Any]] = []
    for target in targets:
        local_path = local_root / "src" / target.filename
        record: dict[str, Any] = {
            "filename": target.filename,
            "stage": target.stage,
            "local_path": str(local_path),
            "remote_path": None,
            "local_sha256": None,
            "remote_sha256": None,
            "status": None,
            "sync_allowed": False,
            "requires_manual_approval": False,
            "rationale": target.rationale,
        }
        if not local_path.is_file():
            record["status"] = "local_source_missing"
            records.append(record)
            continue
        record["local_sha256"] = sha256_file(local_path)
        if target.remote_subdir is None:
            record["status"] = "local_only"
            records.append(record)
            continue

        remote_path = f"{remote_root.rstrip('/')}/{target.remote_subdir}/{target.filename}"
        record["remote_path"] = remote_path
        remote = remote_sha256(remote_alias, remote_path, runner)
        record["remote_sha256"] = remote["sha256"]
        if remote["status"] == "missing":
            record["status"] = "remote_target_missing"
            record["rationale"] = target.rationale + "; target creation is not approved by this audit"
        elif remote["status"] == "error":
            record["status"] = "remote_audit_error"
            record["detail"] = remote["detail"]
        elif record["local_sha256"] == remote["sha256"]:
            record["status"] = "in_sync"
        else:
            record["status"] = "manual_review_required"
            record["sync_allowed"] = True
            record["requires_manual_approval"] = True
            record["rationale"] = target.rationale + "; SHA differs, compare intent and approve deployment explicitly"
        records.append(record)

    declared = {target.filename for target in targets}
    local_files = {path.name for path in (local_root / "src").glob("*.py")}
    summary = {status: sum(row["status"] == status for row in records) for status in sorted({row["status"] for row in records})}
    return {
        "contract_version": 1,
        "mode": "read_only_sha_audit",
        "remote_alias": remote_alias,
        "remote_root": remote_root,
        "records": records,
        "summary": summary,
        "unmapped_local_files": sorted(local_files - declared),
        "auto_sync": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only HY7 local/remote SHA deployment audit")
    parser.add_argument("--local-root", default=str(ROOT))
    parser.add_argument("--remote-alias", default=DEFAULT_REMOTE_ALIAS)
    parser.add_argument("--remote-root", default=DEFAULT_REMOTE_ROOT)
    args = parser.parse_args(argv)
    report = audit_deployment(args.local_root, args.remote_alias, args.remote_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
