import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hy7_b2_min_select", ROOT / "src" / "hy7_b2_min_select.py")
assert SPEC is not None
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def test_candidate_score_prefers_gate_passing_lower_s2_then_euler_distance():
    rows = [
        {"variant": "bad", "s2_rmse": 0.004, "euler": 130.0, "maxcc": 0.05, "phi": 6.4, "pass_gate": False},
        {"variant": "pass_far", "s2_rmse": 0.001, "euler": 135.0, "maxcc": 0.06, "phi": 6.4, "pass_gate": True},
        {"variant": "pass_near", "s2_rmse": 0.001, "euler": 120.0, "maxcc": 0.06, "phi": 6.4, "pass_gate": True},
    ]
    selected = mod.select_best_candidate(rows)
    assert selected["variant"] == "pass_near"
    assert selected["selection_reason"] == "passed_gate_min_score"


def test_make_candidates_splits_indices_without_dropping_tail():
    candidates = mod.make_chunk_candidates(total=10, chunk_size=4, prefix="ep015")
    assert candidates == [
        {"variant": "ep015_chunk000_003", "start": 0, "stop": 4},
        {"variant": "ep015_chunk004_007", "start": 4, "stop": 8},
        {"variant": "ep015_chunk008_009", "start": 8, "stop": 10},
        {"variant": "ep015_all", "start": 0, "stop": 10},
    ]


def test_build_summary_marks_best_candidate_and_forbidden_policy():
    rows = [
        {"variant": "a", "s2_rmse": 0.002, "euler": 118.0, "maxcc": 0.066, "phi": 6.2, "pass_gate": True},
        {"variant": "b", "s2_rmse": 0.002, "euler": 120.0, "maxcc": 0.066, "phi": 6.2, "pass_gate": True},
    ]
    summary = mod.build_summary(rows, calibration_version="hy7-gray-calibration-qmatch-v1")
    assert summary["status"] == "calibrated_constrained_selection_smoke"
    assert summary["calibration_version"] == "hy7-gray-calibration-qmatch-v1"
    assert summary["selected"]["variant"] == "b"
    assert "no_retraining" in summary["forbidden"]
    assert "orig_raw_pass_claim" in summary["forbidden"]


def test_evaluation_inputs_reject_unaligned_nonfinite_or_invalid_controls():
    gray = np.zeros((2, 4, 4), dtype=np.float32)
    pore = np.zeros((2, 4, 4), dtype=bool)
    mod.validate_evaluation_inputs(gray, pore, chunk_size=1, phi_target=6.4, rmax=4)
    with pytest.raises(ValueError, match="shapes must match"):
        mod.validate_evaluation_inputs(gray, pore[:1], chunk_size=1, phi_target=6.4, rmax=4)
    gray[0, 0, 0] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        mod.validate_evaluation_inputs(gray, pore, chunk_size=1, phi_target=6.4, rmax=4)
    with pytest.raises(ValueError, match="positive"):
        mod.validate_evaluation_inputs(np.zeros((2, 4, 4)), pore, chunk_size=0, phi_target=6.4, rmax=4)
