import importlib.util
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('hy7_phase2_ddpm', ROOT / 'src' / 'hy7_phase2_ddpm.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_make_intensity_calibration_none_is_identity():
    train = np.array([[-1.0, 0.0, 1.0]], dtype=np.float32)
    cal = mod.make_intensity_calibration(train, mode='none')
    assert cal['mode'] == 'none'
    out = mod.apply_intensity_calibration(train, cal)
    inv = mod.invert_intensity_calibration(out, cal)
    np.testing.assert_allclose(out, train)
    np.testing.assert_allclose(inv, train)


def test_train_moments_calibration_matches_reference_mean_std():
    train = np.array([[-1.0, -0.5, 0.0, 0.5]], dtype=np.float32)
    sample = np.array([[-1.0, -0.8, -0.6, -0.4]], dtype=np.float32)
    cal = mod.make_intensity_calibration(train, mode='train-moments')

    corrected = mod.apply_intensity_calibration(sample, cal)

    assert abs(float(corrected.mean()) - float(train.mean())) < 1e-6
    assert abs(float(corrected.std()) - float(train.std())) < 1e-6
    assert corrected.dtype == np.float32


def test_train_moments_calibration_clips_to_minus1_1():
    train = np.array([[-0.2, 0.0, 0.2]], dtype=np.float32)
    sample = np.array([[-100.0, 0.0, 100.0]], dtype=np.float32)
    cal = mod.make_intensity_calibration(train, mode='train-moments')

    corrected = mod.apply_intensity_calibration(sample, cal)

    assert corrected.min() >= -1.0
    assert corrected.max() <= 1.0


def test_invalid_intensity_calibration_mode_fails_closed():
    train = np.array([[-1.0, 0.0, 1.0]], dtype=np.float32)
    try:
        mod.make_intensity_calibration(train, mode='bogus')
    except ValueError as e:
        assert 'unknown intensity calibration mode' in str(e)
    else:
        raise AssertionError('expected ValueError')
