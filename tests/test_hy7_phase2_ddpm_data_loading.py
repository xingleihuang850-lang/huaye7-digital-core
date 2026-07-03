import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SPEC = importlib.util.spec_from_file_location(
    "hy7_phase2_ddpm",
    ROOT / "src" / "hy7_phase2_ddpm.py",
)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_load_train_array_maps_uint8_binary_to_minus1_1(tmp_path):
    path = tmp_path / "train.npy"
    np.save(path, np.array([[[0, 1], [1, 0]]], dtype=np.uint8))

    x = mod.load_train_array(path)

    assert tuple(x.shape) == (1, 1, 2, 2)
    assert str(x.dtype).endswith("float32")
    assert np.allclose(x.numpy()[:, 0], [[[-1.0, 1.0], [1.0, -1.0]]])


def test_load_train_array_preserves_float_gray_already_scaled_to_minus1_1(tmp_path):
    path = tmp_path / "train.npy"
    arr = np.array([[[-1.0, -0.25], [0.5, 1.0]]], dtype=np.float32)
    np.save(path, arr)

    x = mod.load_train_array(path)

    assert tuple(x.shape) == (1, 1, 2, 2)
    assert np.allclose(x.numpy()[:, 0], arr)


def test_load_train_array_rejects_float_gray_outside_minus1_1(tmp_path):
    path = tmp_path / "train.npy"
    np.save(path, np.array([[[0.0, 2.0]]], dtype=np.float32))

    try:
        mod.load_train_array(path)
    except ValueError as e:
        assert "[-1,1]" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_postprocess_samples_binary_thresholds_continuous_values():
    cont = np.array([[[-0.2, 0.0, 0.3]]], dtype=np.float32)

    out = mod.postprocess_samples(cont, mode="binary")

    assert out.dtype == np.uint8
    assert out.tolist() == [[[0, 0, 1]]]


def test_postprocess_samples_gray_preserves_clipped_float_values():
    cont = np.array([[[-2.0, -0.5, 0.25, 2.0]]], dtype=np.float32)

    out = mod.postprocess_samples(cont, mode="gray")

    assert out.dtype == np.float32
    assert np.allclose(out, [[[-1.0, -0.5, 0.25, 1.0]]])
