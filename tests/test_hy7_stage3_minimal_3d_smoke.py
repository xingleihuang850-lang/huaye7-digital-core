import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "hy7_stage3_minimal_3d_smoke", ROOT / "src" / "hy7_stage3_minimal_3d_smoke.py"
)
assert SPEC is not None
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def _write_preflight_artifacts(tmp_path: Path):
    calibration = tmp_path / "qmatch_manifest.json"
    calibration.write_text(json.dumps({"version": "hy7-gray-calibration-qmatch-v1"}), encoding="utf-8")
    failed_chunk = tmp_path / "failed_chunk_record.md"
    failed_chunk.write_text("visible negative evidence: ep015_chunk000_063 failed/rejected row", encoding="utf-8")
    return calibration, failed_chunk


def _record_for(volume: np.ndarray):
    return {
        "source_path": "test:/candidate.npy", "source_size_bytes": 1, "source_sha256": "a" * 64,
        "source_shape": list(volume.shape), "source_dtype": str(volume.dtype), "shape": list(volume.shape),
        "array_serialized": False,
    }


def test_fail_closed_when_calibration_artifact_missing(tmp_path):
    missing_calibration = tmp_path / "missing_qmatch_manifest.json"
    failed_chunk = tmp_path / "failed_chunk_record.md"
    failed_chunk.write_text("ep015_chunk000_063 visible negative evidence", encoding="utf-8")

    outputs = mod.write_smoke_package(
        out_dir=tmp_path / "pkg",
        calibration_artifact=missing_calibration,
        failed_chunk_record=failed_chunk,
        candidate_volumes=[],
    )

    assert set(Path(path).name for path in outputs.values()) == set(mod.REQUIRED_PACKAGE_FILES)
    manifest = json.loads((tmp_path / "pkg" / "branch_a_3d_smoke_manifest.json").read_text())
    assert manifest["package_status"] == "FAIL_CLOSED_PREFLIGHT"
    assert manifest["smoke_executed"] is False
    assert any("qmatch calibration artifact missing" in item for item in manifest["fail_closed_reasons"])
    negative = (tmp_path / "pkg" / "negative_evidence.md").read_text()
    assert "qmatch calibration artifact missing" in negative


def test_fail_closed_when_failed_chunk_record_missing(tmp_path):
    calibration = tmp_path / "qmatch_manifest.json"
    calibration.write_text(json.dumps({"version": "hy7-gray-calibration-qmatch-v1"}), encoding="utf-8")

    outputs = mod.write_smoke_package(
        out_dir=tmp_path / "pkg",
        calibration_artifact=calibration,
        failed_chunk_record=tmp_path / "missing_failed_chunk.md",
        candidate_volumes=[],
    )

    assert set(Path(path).name for path in outputs.values()) == set(mod.REQUIRED_PACKAGE_FILES)
    manifest = json.loads((tmp_path / "pkg" / "branch_a_3d_smoke_manifest.json").read_text())
    assert manifest["package_status"] == "FAIL_CLOSED_PREFLIGHT"
    assert manifest["smoke_executed"] is False
    assert any("failed chunk evidence record missing" in item for item in manifest["fail_closed_reasons"])
    negative = (tmp_path / "pkg" / "negative_evidence.md").read_text()
    assert "ep015_chunk000_063" in negative


def test_rejects_wrong_route_label(tmp_path):
    calibration, failed_chunk = _write_preflight_artifacts(tmp_path)

    with pytest.raises(ValueError, match="route_label must be nnUNet ep015_qmatch"):
        mod.write_smoke_package(
            out_dir=tmp_path / "pkg",
            calibration_artifact=calibration,
            failed_chunk_record=failed_chunk,
            route_label="ep015_all",
            candidate_volumes=[],
        )


def test_rejects_candidate_count_above_three(tmp_path):
    calibration, failed_chunk = _write_preflight_artifacts(tmp_path)
    vols = [np.zeros((4, 4, 4), dtype=np.uint8) for _ in range(4)]

    with pytest.raises(ValueError, match="candidate_count_max=3"):
        mod.write_smoke_package(
            out_dir=tmp_path / "pkg",
            calibration_artifact=calibration,
            failed_chunk_record=failed_chunk,
            candidate_volumes=vols,
        )


def test_rejects_volume_above_128_cubed(tmp_path):
    calibration, failed_chunk = _write_preflight_artifacts(tmp_path)
    too_large = np.zeros((129, 2, 2), dtype=np.uint8)

    with pytest.raises(ValueError, match="volume axis hard cap 128"):
        mod.write_smoke_package(
            out_dir=tmp_path / "pkg",
            calibration_artifact=calibration,
            failed_chunk_record=failed_chunk,
            candidate_volumes=[too_large],
        )


def test_emits_twelve_file_fail_closed_package_when_candidate_source_unresolved(tmp_path):
    calibration, failed_chunk = _write_preflight_artifacts(tmp_path)

    outputs = mod.write_smoke_package(
        out_dir=tmp_path / "pkg",
        calibration_artifact=calibration,
        failed_chunk_record=failed_chunk,
        candidate_volumes=None,
    )

    assert set(Path(path).name for path in outputs.values()) == set(mod.REQUIRED_PACKAGE_FILES)
    for path in outputs.values():
        assert Path(path).exists()
    manifest = json.loads((tmp_path / "pkg" / "branch_a_3d_smoke_manifest.json").read_text())
    assert manifest["package_status"] == "FAIL_CLOSED_NO_CANDIDATE_SOURCE"
    assert manifest["smoke_executed"] is False
    assert manifest["route_label"] == "nnUNet ep015_qmatch"
    assert manifest["calibration_version"] == "hy7-gray-calibration-qmatch-v1"
    assert manifest["execution_boundary"]["no_a2"] is True
    assert manifest["execution_boundary"]["no_training"] is True
    assert manifest["execution_boundary"]["no_checkpoint"] is True

    assert not list((tmp_path / "pkg").glob("*.npy"))
    assert not list((tmp_path / "pkg").glob("*.npz"))
    assert not list((tmp_path / "pkg").glob("*.pt"))
    assert "branch_a_3d_smoke_manifest.json" in (tmp_path / "pkg" / "hashes.txt").read_text()
    assert "forbidden_claims.txt" in (tmp_path / "pkg" / "hashes.txt").read_text()


def test_positive_flow_proxy_on_non_percolating_axis_fails_closed(tmp_path):
    calibration, failed_chunk = _write_preflight_artifacts(tmp_path)
    isolated = np.zeros((8, 8, 8), dtype=np.uint8)
    isolated[4, 4, 4] = 1

    mod.write_smoke_package(
        out_dir=tmp_path / "pkg",
        calibration_artifact=calibration,
        failed_chunk_record=failed_chunk,
        candidate_volumes=[isolated],
        candidate_source_records=[_record_for(isolated)],
        physical_flow_proxy={"x": 0.1, "y": 0.0, "z": 0.0},
    )

    physical = json.loads((tmp_path / "pkg" / "physical_response_proxy.json").read_text())
    manifest = json.loads((tmp_path / "pkg" / "branch_a_3d_smoke_manifest.json").read_text())
    assert physical["status"] == "FAIL_CLOSED_PHYSICAL_PROXY_CONTRADICTION"
    assert "positive_flow_proxy_on_non_percolating_axis:x" in physical["fail_closed_reasons"]
    assert manifest["package_status"] == "FAIL_CLOSED_PHYSICAL_PROXY_CONTRADICTION"
    negative = (tmp_path / "pkg" / "negative_evidence.md").read_text()
    assert "positive_flow_proxy_on_non_percolating_axis:x" in negative


def test_load_candidate_npy_slice_records_external_source_without_serializing_volume(tmp_path):
    volume = np.zeros((12, 8, 8), dtype=np.uint8)
    volume[2:10, 3, 3] = 1
    source = tmp_path / "ep015_qmatch_pore_nnunet2d.npy"
    np.save(source, volume)

    candidate = mod.load_candidate_npy(source, start=2, stop=10, source_path="remote:/canonical/ep015_qmatch_pore_nnunet2d.npy")
    assert candidate.volume.shape == (8, 8, 8)
    assert candidate.record["source_path"] == "remote:/canonical/ep015_qmatch_pore_nnunet2d.npy"
    assert candidate.record["local_materialized_path"] == str(source)
    assert candidate.record["slice_range"] == {"start": 2, "stop": 10}
    assert candidate.record["source_sha256"]
    assert candidate.record["array_serialized"] is False

    calibration, failed_chunk = _write_preflight_artifacts(tmp_path)
    outputs = mod.write_smoke_package(
        out_dir=tmp_path / "pkg",
        calibration_artifact=calibration,
        failed_chunk_record=failed_chunk,
        candidate_volumes=[candidate.volume],
        candidate_source_records=[candidate.record],
    )

    assert set(Path(path).name for path in outputs.values()) == set(mod.REQUIRED_PACKAGE_FILES)
    manifest = json.loads((tmp_path / "pkg" / "branch_a_3d_smoke_manifest.json").read_text())
    assert manifest["package_status"] == "DIAGNOSTIC_SMOKE_METADATA_ONLY"
    assert manifest["smoke_executed"] is True

    candidate_manifest = json.loads((tmp_path / "pkg" / "candidate_volume_manifest.json").read_text())
    assert candidate_manifest["candidate_count"] == 1
    assert candidate_manifest["candidate_records"][0]["source_path"] == "remote:/canonical/ep015_qmatch_pore_nnunet2d.npy"
    assert candidate_manifest["candidate_records"][0]["local_materialized_path"] == str(source)
    assert candidate_manifest["candidate_records"][0]["source_sha256"] == candidate.record["source_sha256"]
    assert candidate_manifest["candidate_records"][0]["array_serialized"] is False
    assert not list((tmp_path / "pkg").glob("*.npy"))
    assert not list((tmp_path / "pkg").glob("*.npz"))
    assert not list((tmp_path / "pkg").glob("*.pt"))


def test_rejects_nonfinite_or_unprovenanced_candidate_volumes(tmp_path):
    calibration, failed_chunk = _write_preflight_artifacts(tmp_path)
    with pytest.raises(ValueError, match="finite numeric"):
        mod.write_smoke_package(tmp_path / "bad", calibration, failed_chunk, candidate_volumes=[np.full((2, 2, 2), np.nan)])
    volume = np.zeros((2, 2, 2), dtype=np.uint8)
    with pytest.raises(ValueError, match="candidate_source_records are required"):
        mod.write_smoke_package(tmp_path / "bad", calibration, failed_chunk, candidate_volumes=[volume])
    record = _record_for(volume)
    record["shape"] = [1, 2, 2]
    with pytest.raises(ValueError, match="shape does not match"):
        mod.write_smoke_package(tmp_path / "bad", calibration, failed_chunk, candidate_volumes=[volume], candidate_source_records=[record])
