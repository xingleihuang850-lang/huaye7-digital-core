import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hy7_b2_min_handoff", ROOT / "src" / "hy7_b2_min_handoff.py")
assert SPEC is not None
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def _write_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _baseline_manifest():
    return {
        "status": "calibrated_b2_min_candidate",
        "main_checkpoint": "ep015",
        "calibration_version": "hy7-gray-calibration-qmatch-v1",
        "orig_raw_status": "known_fail",
        "forbidden": [
            "unconditional_b1_1_pass_claim",
            "orig_raw_pass_claim",
            "second_b1_1_topology_rescue",
            "gate_relaxation",
            "implicit_qmatch",
        ],
        "evidence_summary": {
            "formal512_ep015_phi64": {
                "s2_rmse": 0.00034034164909631633,
                "euler": 120.810546875,
                "maxcc": 0.06408827658203413,
                "passed_gate": True,
            },
            "nnunet_ep015_qmatch": {
                "phi": 5.794930458068848,
                "s2_rmse": 0.0017214588891168259,
                "euler": 116.154296875,
                "maxcc": 0.06510709034871634,
                "reverse_fail": False,
            },
            "qmatch_generalization_ep015": {"even_pass": True, "odd_pass": True},
        },
    }


def _selection_summary():
    return {
        "status": "calibrated_constrained_selection_smoke",
        "calibration_version": "hy7-gray-calibration-qmatch-v1",
        "forbidden": [
            "no_retraining",
            "no_second_b1_1_topology_rescue",
            "no_gate_relaxation",
            "orig_raw_pass_claim",
            "explicit_qmatch_required",
        ],
        "selected": {"variant": "ep015_chunk384_447", "start": 384, "stop": 448, "n": 64, "phi": 6.462860107421875, "s2_rmse": 0.0002106706336130071, "euler": 121.171875, "maxcc": 0.06431804952279352, "pass_gate": True},
        "rows": [
            {
                "variant": "ep015_chunk384_447",
                "start": 384,
                "stop": 448,
                "n": 64,
                "phi": 6.462860107421875,
                "s2_rmse": 0.0002106706336130071,
                "euler": 121.171875,
                "maxcc": 0.06431804952279352,
                "pass_gate": True,
            },
            {
                "variant": "ep015_all",
                "start": 0,
                "stop": 512,
                "n": 512,
                "phi": 6.442654132843018,
                "s2_rmse": 0.0002854642510439182,
                "euler": 121.26953125,
                "maxcc": 0.06397858477862998,
                "pass_gate": True,
            },
            {
                "variant": "ep015_chunk000_063",
                "start": 0,
                "stop": 64,
                "n": 64,
                "phi": 6.435489654541016,
                "s2_rmse": 0.0005247734726096197,
                "euler": 123.953125,
                "maxcc": 0.07163110510281959,
                "pass_gate": False,
            },
        ],
    }


def test_build_handoff_bundle_writes_required_files_and_audit_passes(tmp_path):
    baseline = tmp_path / "b2_min_manifest.json"
    selection = tmp_path / "selection_summary.json"
    qmatch = tmp_path / "qmatch_manifest.json"
    design = tmp_path / "design.md"
    _write_json(baseline, _baseline_manifest())
    _write_json(selection, _selection_summary())
    _write_json(qmatch, {"version": "hy7-gray-calibration-qmatch-v1", "reference_split": "all"})
    design.write_text(
        "CONDITIONAL_PASS hy7-gray-calibration-qmatch-v1 ep015_all triage_only known_fail "
        "ep015_chunk000_063 formal512 ep015@phi6.4 nnUNet ep015_qmatch no new training",
        encoding="utf-8",
    )

    outputs = mod.write_handoff_bundle(
        baseline_manifest_path=baseline,
        selection_summary_path=selection,
        qmatch_manifest_path=qmatch,
        design_text_path=design,
        out_dir=tmp_path / "out",
    )

    expected = {
        "handoff_manifest",
        "handoff_readme",
        "formal_vs_qmatch_metrics",
        "candidate_rows",
        "forbidden_claims",
        "hashes",
        "audit_report",
        "ordered_view_links",
    }
    assert set(outputs) == expected
    for path in outputs.values():
        assert Path(path).exists()

    manifest = json.loads(Path(outputs["handoff_manifest"]).read_text())
    assert manifest["status"] == "calibrated_b2_min_handoff_design_dry_run"
    assert manifest["main_checkpoint"] == "ep015"
    assert manifest["calibration_version"] == "hy7-gray-calibration-qmatch-v1"
    assert manifest["acceptance_anchor"] == "ep015_all"
    assert manifest["selected_chunk_policy"] == "triage_only"
    assert manifest["execution_boundary"] == "no_retraining_no_new_sampling_no_scaling_no_new_checkpoint"

    metrics = json.loads(Path(outputs["formal_vs_qmatch_metrics"]).read_text())
    assert metrics["formal_full_batch_ep015_all"]["variant"] == "ep015_all"
    assert metrics["nnunet_ep015_qmatch"]["reverse_fail"] is False
    assert "do not merge" in metrics["interpretation"]

    rows = json.loads(Path(outputs["candidate_rows"]).read_text())
    failed = [r for r in rows["rows"] if not r["pass_gate"]]
    assert failed[0]["variant"] == "ep015_chunk000_063"
    assert failed[0]["failure_reasons"] == ["maxCC>0.070"]
    assert rows["selected_policy"] == "triage_only"
    assert rows["full_batch_policy"] == "acceptance_anchor"

    audit = json.loads(Path(outputs["audit_report"]).read_text())
    assert audit["passed"] is True
    assert audit["errors"] == []

    readme = Path(outputs["handoff_readme"]).read_text()
    assert "Forbidden claims / do not write" in readme
    assert "ORIG raw passed" in readme
    assert "ep015_all" in readme
    hashes = Path(outputs["hashes"]).read_text()
    assert "handoff_manifest.json" in hashes
    assert "design_text" in manifest["source_sha256"]


def test_handoff_bundle_rejects_missing_full_batch(tmp_path):
    baseline = tmp_path / "b2_min_manifest.json"
    selection = tmp_path / "selection_summary.json"
    qmatch = tmp_path / "qmatch_manifest.json"
    design = tmp_path / "design.md"
    _write_json(baseline, _baseline_manifest())
    bad_selection = _selection_summary()
    bad_selection["rows"] = [r for r in bad_selection["rows"] if r["variant"] != "ep015_all"]
    _write_json(selection, bad_selection)
    _write_json(qmatch, {"version": "hy7-gray-calibration-qmatch-v1"})
    design.write_text("CONDITIONAL_PASS hy7-gray-calibration-qmatch-v1 ep015_all triage_only known_fail ep015_chunk000_063 formal512 ep015@phi6.4 nnUNet ep015_qmatch no new training", encoding="utf-8")

    try:
        mod.write_handoff_bundle(baseline, selection, qmatch, design, tmp_path / "out")
    except ValueError as exc:
        assert "selection.rows must include full-batch ep015_all" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_handoff_bundle_rejects_wrong_qmatch_manifest_version(tmp_path):
    baseline = tmp_path / "b2_min_manifest.json"
    selection = tmp_path / "selection_summary.json"
    qmatch = tmp_path / "qmatch_manifest.json"
    design = tmp_path / "design.md"
    _write_json(baseline, _baseline_manifest())
    _write_json(selection, _selection_summary())
    _write_json(qmatch, {"version": "wrong"})
    design.write_text("no new training", encoding="utf-8")
    try:
        mod.write_handoff_bundle(baseline, selection, qmatch, design, tmp_path / "out")
    except ValueError as exc:
        assert "qmatch manifest version" in str(exc)
    else:
        raise AssertionError("expected ValueError")
