import argparse
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hy7_b2_min_package", ROOT / "src" / "hy7_b2_min_package.py")
assert SPEC is not None
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def _write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def test_build_manifest_records_conditional_b2_min_contract(tmp_path):
    ckpt = tmp_path / "ckpt_ep015.pt"
    calib = tmp_path / "hy7_gray_calibration.py"
    formal = tmp_path / "formal512_ep015.json"
    nn = tmp_path / "nnunet.json"
    qgen = tmp_path / "qgen.json"
    ckpt.write_bytes(b"checkpoint")
    calib.write_text("VERSION='hy7-gray-calibration-qmatch-v1'", encoding="utf-8")
    _write_json(formal, {"phi64": {"s2_rmse": 0.00034, "euler": 120.81, "maxcc": 0.0641, "passed_gate": True}})
    _write_json(nn, {"rows": [{"variant": "ep015_qmatch", "phi": 5.795, "s2_rmse": 0.00172, "euler": 116.15, "maxcc": 0.0651, "reverse_fail": False}]})
    _write_json(qgen, {"rows": [
        {"variant": "ep015_qmatch_even", "pass_gate": True, "euler": 116.14},
        {"variant": "ep015_qmatch_odd", "pass_gate": True, "euler": 116.17},
    ]})
    args = argparse.Namespace(
        checkpoint=str(ckpt), formal512=str(formal), nnunet=str(nn),
        qmatch_generalization=str(qgen), calibration_module=str(calib), out=str(tmp_path / "out")
    )
    manifest = mod.build_manifest(args)
    assert manifest["status"] == "calibrated_b2_min_candidate"
    assert manifest["main_checkpoint"] == "ep015"
    assert manifest["calibration_version"] == "hy7-gray-calibration-qmatch-v1"
    assert manifest["orig_raw_status"] == "known_fail"
    assert "second_b1_1_topology_rescue" in manifest["forbidden"]
    assert manifest["evidence_summary"]["qmatch_generalization_ep015"]["even_pass"] is True


def test_write_package_outputs_manifest_readme_and_hashes(tmp_path):
    manifest = {
        "status": "calibrated_b2_min_candidate",
        "main_checkpoint": "ep015",
        "calibration_version": "hy7-gray-calibration-qmatch-v1",
        "orig_raw_status": "known_fail",
        "forbidden": ["orig_raw_pass_claim"],
        "evidence_summary": {
            "formal512_ep015_phi64": {"passed_gate": True},
            "nnunet_ep015_qmatch": {"reverse_fail": False},
            "qmatch_generalization_ep015": {"even_pass": True, "odd_pass": True},
        },
        "files": {},
    }
    outputs = mod.write_package(manifest, tmp_path / "pkg")
    for path in outputs.values():
        assert Path(path).exists()
    data = json.loads(Path(outputs["manifest"]).read_text())
    assert data["main_checkpoint"] == "ep015"
    readme = Path(outputs["readme"]).read_text()
    assert "ORIG raw status" in readme
    assert "hy7-gray-calibration-qmatch-v1" in readme
    hashes = Path(outputs["hashes"]).read_text()
    assert "b2_min_manifest.json" in hashes
    assert "b2_min_readme.md" in hashes


def test_summarize_evidence_rejects_missing_or_nonfinite_required_metrics():
    formal = {"phi64": {"s2_rmse": 0.1, "euler": 120.0, "maxcc": 0.06, "passed_gate": True}}
    nn = {"rows": [{"variant": "ep015_qmatch", "phi": 6.0, "s2_rmse": 0.1, "euler": 120.0, "maxcc": 0.06, "reverse_fail": False}]}
    qgen = {"rows": [{"variant": "ep015_qmatch_even", "pass_gate": True, "euler": 120.0}]}
    with pytest.raises(ValueError, match="ep015_qmatch_odd"):
        mod.summarize_evidence(formal, nn, qgen)

    qgen["rows"].append({"variant": "ep015_qmatch_odd", "pass_gate": True, "euler": float("nan")})
    with pytest.raises(ValueError, match="finite number"):
        mod.summarize_evidence(formal, nn, qgen)
