import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hy7_b2_min_audit", ROOT / "src" / "hy7_b2_min_audit.py")
assert SPEC is not None
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def _valid_manifest():
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
    }


def _valid_selection():
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
        "selected": {"variant": "ep015_chunk384_447", "n": 64, "pass_gate": True},
        "rows": [
            {"variant": "ep015_chunk384_447", "n": 64, "pass_gate": True, "maxcc": 0.0643},
            {"variant": "ep015_all", "n": 512, "pass_gate": True, "maxcc": 0.0640},
            {"variant": "ep015_chunk000_063", "n": 64, "pass_gate": False, "maxcc": 0.07163110510281959},
        ],
    }


def test_audit_valid_manifest_selection_and_design_text_passes():
    text = """
    B2-min design-entry gate = CONDITIONAL_PASS.
    main checkpoint ep015 with hy7-gray-calibration-qmatch-v1.
    ep015_all is the full-batch acceptance_anchor.
    ep015_chunk384_447 is triage_only only.
    ORIG raw remains known_fail. no new training / no scaling / no new checkpoint.
    ep015_chunk000_063 failed because maxCC>0.070.
    formal512 ep015@phi6.4 differs from nnUNet ep015_qmatch.
    """
    result = mod.audit_design_entry(_valid_manifest(), _valid_selection(), text)
    assert result["passed"] is True
    assert result["errors"] == []
    assert "failed_selection_rows_visible" in result["checks"]


def test_manifest_requires_explicit_qmatch_ep015_and_known_fail_orig():
    manifest = _valid_manifest()
    manifest["calibration_version"] = "implicit"
    result = mod.audit_manifest(manifest)
    assert result["passed"] is False
    assert "manifest.calibration_version must be hy7-gray-calibration-qmatch-v1" in result["errors"]

    manifest = _valid_manifest()
    manifest["orig_raw_status"] = "passed"
    result = mod.audit_manifest(manifest)
    assert result["passed"] is False
    assert "manifest.orig_raw_status must be known_fail" in result["errors"]


def test_selection_requires_full_batch_anchor_and_failed_rows_visible():
    selection = _valid_selection()
    selection["rows"] = [r for r in selection["rows"] if r["variant"] != "ep015_all"]
    result = mod.audit_selection_summary(selection)
    assert result["passed"] is False
    assert "selection.rows must include full-batch ep015_all" in result["errors"]

    selection = _valid_selection()
    selection["rows"] = [r for r in selection["rows"] if r.get("pass_gate")]
    result = mod.audit_selection_summary(selection)
    assert result["passed"] is False
    assert "selection.rows must include at least one failed/rejected row" in result["errors"]


def test_forbidden_claim_lint_catches_unsafe_wording():
    bad = "B1.1 unconditional pass; ORIG raw passed; qmatch optional; selected chunk represents full model performance"
    result = mod.audit_design_text(bad)
    assert result["passed"] is False
    assert any("B1.1 unconditional pass" in e for e in result["errors"])
    assert any("ORIG raw passed" in e for e in result["errors"])
    assert any("qmatch optional" in e for e in result["errors"])
    assert any("selected chunk represents full model performance" in e for e in result["errors"])


def test_forbidden_claim_lint_allows_explicit_prohibited_claim_lists():
    text = """
    B2-min design-entry gate = CONDITIONAL_PASS.
    hy7-gray-calibration-qmatch-v1, ep015_all, triage_only, known_fail.
    ep015_chunk000_063 failed because maxCC>0.070.
    formal512 ep015@phi6.4 differs from nnUNet ep015_qmatch.
    no new training.

    Forbidden claims / do not write:
    - B1.1 unconditional pass
    - ORIG raw passed
    - qmatch optional
    - selected chunk represents full model performance
    """
    result = mod.audit_design_text(text)
    assert result["passed"] is True
    assert result["errors"] == []
