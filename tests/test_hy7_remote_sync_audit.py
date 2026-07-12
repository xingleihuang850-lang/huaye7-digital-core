import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hy7_remote_sync_audit", ROOT / "src" / "hy7_remote_sync_audit.py")
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def target(filename, remote_subdir):
    return mod.DeploymentTarget(filename, "test", remote_subdir, "test target")


def write_source(tmp_path, name, content="print('x')\n"):
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    path = src / name
    path.write_text(content, encoding="utf-8")
    return path


def test_phase_mapping_keeps_stage2_out_of_remote_src():
    by_name = {entry.filename: entry for entry in mod.DEPLOYMENT_MAP}
    assert by_name["hy7_planb_train.py"].remote_subdir == "src"
    assert by_name["hy7_phase2_ddpm.py"].remote_subdir == "phase2"
    assert by_name["hy7_phase2_make_gray_slices.py"].remote_subdir == "phase2"
    assert by_name["hy7_b2_min_audit.py"].remote_subdir is None
    assert by_name["hy7_stage3_minimal_3d_smoke.py"].remote_subdir is None


def test_audit_marks_matching_and_different_targets_without_syncing(tmp_path):
    source = write_source(tmp_path, "toy.py")
    local_sha = mod.sha256_file(source)
    calls = []

    def runner(command, **_kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, f"{local_sha}  {command[-1]}\n", "")

    report = mod.audit_deployment(tmp_path, "test-host", "/remote", [target("toy.py", "phase2")], runner)
    row = report["records"][0]
    assert row["status"] == "in_sync"
    assert row["sync_allowed"] is False
    assert calls[0][:4] == ["ssh", "-o", "BatchMode=yes", "test-host"]
    assert "rsync" not in calls[0]
    assert "scp" not in calls[0]

    def different_runner(command, **_kwargs):
        return subprocess.CompletedProcess(command, 0, f"{'0' * 64}  {command[-1]}\n", "")

    report = mod.audit_deployment(tmp_path, "test-host", "/remote", [target("toy.py", "phase2")], different_runner)
    row = report["records"][0]
    assert row["status"] == "manual_review_required"
    assert row["sync_allowed"] is True
    assert row["requires_manual_approval"] is True


def test_audit_blocks_missing_targets_and_skips_ssh_for_local_only(tmp_path):
    write_source(tmp_path, "toy.py")

    def missing_runner(command, **_kwargs):
        return subprocess.CompletedProcess(command, 1, "", f"sha256sum: {command[-1]}: No such file")

    report = mod.audit_deployment(tmp_path, "test-host", "/remote", [target("toy.py", "phase2")], missing_runner)
    row = report["records"][0]
    assert row["status"] == "remote_target_missing"
    assert row["sync_allowed"] is False

    def should_not_run(*_args, **_kwargs):
        raise AssertionError("local-only files must not contact SSH")

    report = mod.audit_deployment(tmp_path, "test-host", "/remote", [target("toy.py", None)], should_not_run)
    row = report["records"][0]
    assert row["status"] == "local_only"
    assert row["remote_path"] is None
