import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "hy7_stage3_inter_slice_audit",
    ROOT / "src" / "hy7_stage3_inter_slice_audit.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def _source(tmp_path: Path) -> Path:
    arr = np.zeros((10, 6, 6), dtype=np.uint8)
    arr[2, 1:4, 1:4] = 1
    arr[3, 1:4, 1:4] = 1
    arr[4, 3:5, 3:5] = 1
    arr[5, 5, 5] = 1
    p = tmp_path / "candidate.npy"
    np.save(p, arr)
    return p


def test_inter_slice_audit_writes_nine_metadata_files_and_no_arrays(tmp_path):
    src = _source(tmp_path)
    expected = mod.sha256_file(src)
    out = tmp_path / "pkg"
    outputs = mod.write_inter_slice_audit_package(
        out_dir=out,
        candidate_npy=src,
        expected_sha256=expected,
        slice_start=2,
        slice_stop=8,
        source_path="remote:/candidate.npy",
        expected_slice_count=6,
    )
    assert {Path(p).name for p in outputs.values()} == set(mod.REQUIRED_PACKAGE_FILES)
    assert not list(out.glob("*.npy"))
    assert not list(out.glob("*.npz"))
    assert not list(out.glob("*.pt"))

    manifest = json.loads((out / "inter_slice_audit_manifest.json").read_text())
    assert manifest["package_status"] == "METADATA_ONLY_INTER_SLICE_AUDIT"
    assert manifest["execution_authorized_by_gate"] == "ALLOW_METADATA_ONLY_INTER_SLICE_AUDIT_WITH_CONSTRAINTS"
    assert manifest["no_second_smoke_implication"] is True
    assert manifest["no_a2_small_implication"] is True
    assert manifest["candidate_arrays_written"] is False

    axis = (out / "axis_boundary_semantics.md").read_text()
    assert "axis_0_to_slice_stacking_mapping=verified" in axis

    metrics = json.loads((out / "inter_slice_metrics.json").read_text())
    assert metrics["metric_labels_required"]["not_permeability"] is True
    assert metrics["metric_labels_required"]["no_second_smoke_implication"] is True
    assert "adjacent_slice_jaccard_distribution_along_x" in metrics["summary_metrics"]
    assert metrics["raw_pair_values_written"] is False
    assert metrics["raw_per_slice_values_written"] is False


def test_inter_slice_audit_fails_closed_on_hash_mismatch(tmp_path):
    src = _source(tmp_path)
    try:
        mod.write_inter_slice_audit_package(
            out_dir=tmp_path / "bad",
            candidate_npy=src,
            expected_sha256="0" * 64,
            slice_start=2,
            slice_stop=8,
        )
    except mod.AuditContractError as exc:
        assert "sha256 mismatch" in str(exc)
    else:
        raise AssertionError("hash mismatch accepted")


def test_inter_slice_audit_fails_closed_on_axis_ambiguity(tmp_path):
    src = _source(tmp_path)
    expected = mod.sha256_file(src)
    try:
        mod.write_inter_slice_audit_package(
            out_dir=tmp_path / "bad_axis",
            candidate_npy=src,
            expected_sha256=expected,
            slice_start=2,
            slice_stop=9,
            expected_slice_count=6,
        )
    except mod.AuditContractError as exc:
        assert "axis mapping ambiguous" in str(exc)
    else:
        raise AssertionError("axis ambiguity accepted")


def test_inter_slice_audit_source_has_no_heavy_inference_imports():
    text = (ROOT / "src" / "hy7_stage3_inter_slice_audit.py").read_text()
    forbidden = ["import torch", "import tensorflow", "import nnunet"]
    assert not any(token in text for token in forbidden)
