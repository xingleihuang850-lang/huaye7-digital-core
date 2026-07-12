import importlib.util
import sys
import types
from pathlib import Path


def load_mod_with_torch_stub():
    torch = types.ModuleType("torch")
    torch_utils = types.ModuleType("torch.utils")
    torch_utils_data = types.ModuleType("torch.utils.data")
    torch_nn = types.ModuleType("torch.nn")
    torch_nn_functional = types.ModuleType("torch.nn.functional")
    setattr(torch, "no_grad", lambda: (lambda fn: fn))
    setattr(torch, "utils", torch_utils)
    setattr(torch_utils, "data", torch_utils_data)
    setattr(torch_utils_data, "DataLoader", object)
    setattr(torch_utils_data, "TensorDataset", object)
    setattr(torch, "nn", torch_nn)
    setattr(torch_nn, "functional", torch_nn_functional)
    sys.modules.setdefault("torch", torch)
    sys.modules.setdefault("torch.utils", torch_utils)
    sys.modules.setdefault("torch.utils.data", torch_utils_data)
    sys.modules.setdefault("torch.nn", torch_nn)
    sys.modules.setdefault("torch.nn.functional", torch_nn_functional)

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("hy7_phase2_ddpm_metric", root / "src" / "hy7_phase2_ddpm.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_metric_score_prefers_checkpoint_with_balanced_phi_s2_topology():
    mod = load_mod_with_torch_stub()
    target = {"phi": 6.405, "s2_rmse": 0.0, "euler": 127.33, "maxcc": 0.0597}
    weights = {"phi": 1.0, "s2_rmse": 1.0, "euler": 1.0, "maxcc": 1.0}

    final_none = {"name": "final_none", "phi": 6.405, "s2_rmse": 0.002, "euler": 124.52, "maxcc": 0.0680}
    bad_topology = {"name": "best_train_moments", "phi": 3.777, "s2_rmse": 0.00584, "euler": 115.14, "maxcc": 0.1003}

    chosen = mod.select_metric_aware_checkpoint([final_none, bad_topology], target=target, weights=weights)

    assert chosen["name"] == "final_none"
    assert chosen["passed_gate"] is True
    assert chosen["score"] < chosen["candidates"]["best_train_moments"]["score"]


def test_metric_gate_marks_overconnected_checkpoint_as_failed_even_when_score_exists():
    mod = load_mod_with_torch_stub()
    target = {"phi": 6.405, "s2_rmse": 0.0, "euler": 127.33, "maxcc": 0.0597}
    gates = {"maxcc_max": 0.070, "euler_rel_tol": 0.15}
    metrics = {"name": "overconnected", "phi": 5.6, "s2_rmse": 0.0022, "euler": 91.21, "maxcc": 0.0823}

    scored = mod.score_checkpoint_metrics(metrics, target=target, gates=gates)

    assert scored["passed_gate"] is False
    assert "maxcc" in scored["failed_gates"]
    assert "euler" in scored["failed_gates"]


def test_default_gate_requires_s2_phi_euler_and_maxcc_together():
    mod = load_mod_with_torch_stub()
    target = {"phi": 6.405, "s2_rmse": 0.0, "euler": 127.33, "maxcc": 0.0597}
    metrics = {"name": "s2_and_phi_fail", "phi": 7.0, "s2_rmse": 0.004, "euler": 120.0, "maxcc": 0.06}

    scored = mod.score_checkpoint_metrics(metrics, target=target)

    assert scored["passed_gate"] is False
    assert {"s2_rmse", "phi"}.issubset(scored["failed_gates"])
