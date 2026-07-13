import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hy7_stage3_a2_preflight", ROOT / "src" / "hy7_stage3_a2_preflight.py")
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def _valid_declaration():
    digest = "a" * 64
    return {
        "status": "A2_DESIGN_ONLY_PRE_GATE_REVIEW",
        "execution_authorized": False,
        "scientific_status": "design_only_not_evidence",
        "source_identity": {
            "input_slice_manifest_sha256": digest,
            "cross_scale_registration_sha256": digest,
            "axis_order": "zyx",
            "condition_channels": [{"name": "gray", "units": "normalized_intensity", "source_sha256": digest}],
        },
        "route_constraints": {
            "formal_route": "threshold_formal_full_batch", "formal_anchor": "ep015_all",
            "diagnostic_route": "nnUNet ep015_qmatch", "triage_policy": "triage_only",
            "failed_chunk": "ep015_chunk000_063", "orig_raw_status": "known_fail",
            "qmatch_version": "hy7-gray-calibration-qmatch-v1",
        },
        "phantom_validation": {
            "completed_families": sorted(mod.REQUIRED_PHANTOMS),
            "completed_scales": sorted(mod.REQUIRED_SCALES),
            "deterministic_regeneration": True,
        },
        "metrics": {
            "phi_3d": "phantom_validated", "s2_3d": "phantom_validated",
            "connected_porosity_3d": "phantom_validated", "percolation_xyz": "phantom_validated",
            "largest_component_dual_denominator": "phantom_validated",
            "euler_minkowski_3d": "explicitly_de_scoped_fail_closed",
        },
    }


def test_complete_design_is_only_ready_for_future_gate_review():
    result = mod.validate_a2_preflight(_valid_declaration())
    assert result["passed"] is True
    assert result["verdict"] == "READY_FOR_FUTURE_GATE_REVIEW_ONLY"
    assert result["execution_authorized"] is False


def test_missing_phantoms_or_route_drift_fail_closed():
    declaration = _valid_declaration()
    declaration["phantom_validation"]["completed_families"] = []
    declaration["route_constraints"]["diagnostic_route"] = "merged"
    result = mod.validate_a2_preflight(declaration)
    assert result["passed"] is False
    assert any("missing families" in error for error in result["errors"])
    assert any("diagnostic_route" in error for error in result["errors"])
