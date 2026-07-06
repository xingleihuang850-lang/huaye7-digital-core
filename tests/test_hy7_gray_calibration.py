import importlib.util
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hy7_gray_calibration", ROOT / "src" / "hy7_gray_calibration.py")
assert SPEC is not None
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def test_quantile_match_is_rank_preserving_and_matches_reference_values():
    values = np.array([0.2, -1.0, 0.2, 1.0], dtype=np.float32)
    ref = np.array([-0.8, -0.4, 0.3, 0.9], dtype=np.float32)
    out = mod.quantile_match(values, ref)
    assert out.dtype == np.float32
    assert out.shape == values.shape
    assert sorted(out.tolist()) == sorted(ref.tolist())
    # rank preserving: minimum maps to minimum, maximum maps to maximum
    assert out[1] == np.float32(-0.8)
    assert out[3] == np.float32(0.9)


def test_load_reference_values_supports_disjoint_even_odd_splits(tmp_path):
    arr = np.arange(24, dtype=np.float32).reshape(6, 2, 2)
    path = tmp_path / "ref.npy"
    np.save(path, arr)
    even = mod.load_reference_values(path, split="even")
    odd = mod.load_reference_values(path, split="odd")
    assert even.size == odd.size == 12
    assert np.array_equal(even, np.sort(arr[::2].reshape(-1)))
    assert np.array_equal(odd, np.sort(arr[1::2].reshape(-1)))


def test_calibrate_array_writes_reproducible_manifest_fields(tmp_path):
    ref = np.linspace(-1, 1, 12, dtype=np.float32).reshape(3, 2, 2)
    ref_path = tmp_path / "ref.npy"
    np.save(ref_path, ref)
    values = np.array([[[0.5, -0.5], [0.2, 0.1]]], dtype=np.float32)
    out, manifest = mod.calibrate_array(values, ref_path, split="all")
    assert manifest["version"] == mod.VERSION
    assert manifest["method"] == "empirical_quantile_match_rank_preserving"
    assert manifest["reference_split"] == "all"
    assert manifest["input_shape"] == [1, 2, 2]
    assert out.shape == values.shape
    assert manifest["calibrated_stats"]["quantile_mae"] < manifest["input_stats"]["quantile_mae"]


def test_to_nnunet_raw_intensity_clips_to_expected_range():
    gray = np.array([-2.0, -1.0, 0.0, 1.0, 2.0], dtype=np.float32)
    raw = mod.to_nnunet_raw_intensity(gray)
    assert raw.dtype == np.float32
    assert raw.tolist() == [45.0, 45.0, 125.0, 205.0, 205.0]
