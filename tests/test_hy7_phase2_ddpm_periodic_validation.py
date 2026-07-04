import importlib.util
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hy7_phase2_ddpm_periodic", ROOT / "src" / "hy7_phase2_ddpm.py")
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_gray_validation_stats_include_mean_std_and_ks_against_reference():
    generated = np.array([[[-1.0, -0.5], [0.0, 0.5]]], dtype=np.float32)
    reference = np.array([[[-1.0, -0.25], [0.25, 1.0]]], dtype=np.float32)

    stats = mod.gray_validation_stats(generated, reference)

    assert stats["n"] == 1
    assert stats["mean"] == float(generated.mean())
    assert stats["std"] == float(generated.std())
    assert 0.0 <= stats["ks"] <= 1.0
    assert stats["ks"] > 0.0


def test_threshold_for_porosity_uses_lower_tail_fraction():
    gray = np.array([[[-1.0, -0.5], [0.0, 0.5]]], dtype=np.float32)

    threshold = mod.threshold_for_porosity(gray, 50.0)
    pore = gray <= threshold

    assert threshold == -0.5
    assert pore.mean() == 0.5


def test_binary_pore_metrics_report_phi_euler_maxcc_and_s2_rmse():
    real = np.array([
        [[1, 0, 0],
         [0, 0, 0],
         [0, 0, 1]],
    ], dtype=np.uint8)
    generated = np.array([
        [[1, 1, 0],
         [0, 0, 0],
         [0, 0, 1]],
    ], dtype=np.uint8)

    metrics = mod.binary_pore_metrics(generated, real)

    assert metrics["phi"] == generated.mean() * 100.0
    assert metrics["euler"] == 2.0
    assert metrics["maxcc"] == 2.0 / 9.0
    assert metrics["s2_rmse"] > 0.0


def test_periodic_validation_summary_scores_threshold_candidates():
    gray = np.array([
        [[-1.0, -0.8, 0.7],
         [0.2, 0.4, 0.8],
         [-0.9, 0.9, 1.0]],
    ], dtype=np.float32)
    gray_ref = gray.copy()
    real = np.array([
        [[1, 1, 0],
         [0, 0, 0],
         [1, 0, 0]],
    ], dtype=np.uint8)
    target = {"phi": 33.3333333333, "s2_rmse": 0.0, "euler": 2.0, "maxcc": 2.0 / 9.0}

    summary = mod.periodic_validation_summary(
        gray,
        gray_reference=gray_ref,
        real_pore=real,
        checkpoint="ckpt_ep010.pt",
        epoch=10,
        porosity_targets=[22.2222222222, 33.3333333333],
        metric_target=target,
        gates={"maxcc_max": 0.30, "euler_rel_tol": 0.60},
    )

    assert summary["checkpoint"] == "ckpt_ep010.pt"
    assert summary["epoch"] == 10
    assert len(summary["threshold_candidates"]) == 2
    assert summary["selected"]["porosity_target"] == 33.3333333333
    assert summary["selected"]["passed_gate"] is True
