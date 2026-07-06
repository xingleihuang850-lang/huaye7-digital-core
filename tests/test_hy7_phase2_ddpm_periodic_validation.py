import importlib.util
from pathlib import Path
from types import SimpleNamespace

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


def test_formal_proxy_summary_uses_eval_style_metrics_and_flags_fast_formal_disagreement():
    gray = np.array([
        [[-1.0, -0.8, 0.7, 0.6],
         [0.2, 0.4, 0.8, 0.9],
         [-0.9, 0.9, 1.0, 0.5],
         [0.3, 0.2, -0.7, -0.6]],
        [[-0.95, 0.1, 0.2, 0.3],
         [0.4, -0.85, 0.5, 0.6],
         [0.7, 0.8, -0.75, 0.9],
         [1.0, 0.6, 0.5, -0.65]],
    ], dtype=np.float32)
    gray_ref = gray.copy()
    real = np.array([
        [[1, 1, 0, 0],
         [0, 0, 0, 0],
         [1, 0, 0, 0],
         [0, 0, 1, 1]],
        [[1, 0, 0, 0],
         [0, 1, 0, 0],
         [0, 0, 1, 0],
         [0, 0, 0, 1]],
    ], dtype=np.uint8)

    summary = mod.periodic_validation_summary(
        gray,
        gray_reference=gray_ref,
        real_pore=real,
        checkpoint="ckpt_ep020.pt",
        epoch=20,
        porosity_targets=[25.0, 37.5],
        formal_proxy=True,
        formal_rmax=3,
        gates={"maxcc_max": 1.0, "euler_rel_tol": 10.0},
    )

    assert summary["selected"]["proxy"] == "formal"
    assert summary["fast_proxy"]["selected"]["proxy"] == "fast"
    assert summary["formal_proxy"]["rmax"] == 3
    assert summary["formal_proxy"]["metric_target"]["maxcc"] == 0.325
    assert len(summary["formal_proxy"]["threshold_candidates"]) == 2
    formal_candidate = summary["formal_proxy"]["threshold_candidates"][0]
    assert {"x_penetrate", "y_penetrate", "maxcc"}.issubset(formal_candidate)
    assert formal_candidate["maxcc"] >= 0.0
    assert summary["selection_status"] in {"accepted", "needs_formal_resample", "rejected"}


def test_soft_pore_regularizer_uses_train_only_threshold_and_records_targets():
    try:
        import torch
        if not hasattr(torch, "from_numpy"):
            return
    except ModuleNotFoundError:
        return
    train = torch.from_numpy(np.linspace(-1.0, 1.0, 2 * 1 * 4 * 4, dtype=np.float32).reshape(2, 1, 4, 4))
    args = SimpleNamespace(
        soft_phi_lambda=0.01,
        soft_s2_lambda=0.02,
        soft_pore_phi=25.0,
        soft_pore_tau=0.1,
        soft_s2_lags="1,2",
        soft_reg_ref_n=2,
    )

    reg = mod._build_soft_pore_regularizer(train, args, "cpu")

    assert reg is not None
    assert reg["lambda_phi"] == 0.01
    assert reg["lambda_s2"] == 0.02
    assert reg["lags"] == [1, 2]
    assert reg["ref_n"] == 2
    assert np.isclose(reg["threshold"], mod.threshold_for_porosity(train.numpy(), 25.0))
    assert reg["s2_target"].shape[0] == 4


def test_soft_pore_regularization_loss_is_differentiable():
    try:
        import torch
        if not hasattr(torch, "from_numpy"):
            return
    except ModuleNotFoundError:
        return
    x0 = torch.tensor([[[[-0.5, 0.2], [0.1, -0.8]]]], dtype=torch.float32, requires_grad=True)
    reg = {
        "threshold": 0.0,
        "tau": 0.2,
        "lambda_phi": 0.1,
        "lambda_s2": 0.1,
        "lambda_euler": 0.0,
        "lambda_maxcc": 0.0,
        "phi_ref": torch.tensor(0.5),
        "s2_target": torch.zeros(2),
        "lags": [1],
    }

    loss, parts = mod._soft_pore_regularization_loss(x0, reg)
    loss.backward()

    assert float(loss.detach()) >= 0.0
    assert {"soft_phi", "soft_s2", "weighted"}.issubset(parts)
    assert x0.grad is not None


def test_soft_topology_proxy_targets_euler_and_maxcc_differentiably():
    try:
        import torch
        if not hasattr(torch, "from_numpy"):
            return
    except ModuleNotFoundError:
        return
    train = torch.tensor([
        [[[-1.0, 0.8, 0.8, 0.8],
          [0.8, -1.0, 0.8, 0.8],
          [0.8, 0.8, -1.0, 0.8],
          [0.8, 0.8, 0.8, -1.0]]],
    ], dtype=torch.float32)
    args = SimpleNamespace(
        soft_phi_lambda=0.0,
        soft_s2_lambda=0.0,
        soft_euler_lambda=0.3,
        soft_maxcc_lambda=0.4,
        soft_pore_phi=25.0,
        soft_pore_tau=0.08,
        soft_s2_lags="1",
        soft_reg_ref_n=1,
        soft_maxcc_scales="2,4",
    )

    reg = mod._build_soft_pore_regularizer(train, args, "cpu")
    assert reg is not None
    assert reg["lambda_euler"] == 0.3
    assert reg["lambda_maxcc"] == 0.4
    assert reg["euler_target"].ndim == 0
    assert reg["maxcc_target"].ndim == 0

    x0 = torch.zeros((1, 1, 4, 4), dtype=torch.float32, requires_grad=True)
    loss, parts = mod._soft_pore_regularization_loss(x0, reg)
    loss.backward()

    assert float(loss.detach()) >= 0.0
    assert {"soft_euler", "soft_maxcc", "weighted"}.issubset(parts)
    assert x0.grad is not None
