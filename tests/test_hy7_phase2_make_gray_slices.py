import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SPEC = importlib.util.spec_from_file_location(
    "hy7_phase2_make_gray_slices",
    ROOT / "src" / "hy7_phase2_make_gray_slices.py",
)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_normalize_gray_clips_percentiles_and_maps_to_minus1_1():
    x = np.array([[0, 45, 115, 205, 255]], dtype=np.uint8)
    y = mod.normalize_gray(x, clip_low=45, clip_high=205)

    assert y.dtype == np.float32
    assert np.allclose(y, [[-1.0, -1.0, -0.125, 1.0, 1.0]])


def test_tiles_from_gray_preserves_pairing_and_filters_invalid_tiles():
    img = np.arange(16, dtype=np.uint8).reshape(4, 4) + 50
    pore = np.zeros((4, 4), dtype=bool)
    pore[0, 0] = True
    valid = np.ones((4, 4), dtype=bool)
    valid[2:, 2:] = False

    gray, paired = mod.tiles_from_gray(
        img,
        pore,
        valid,
        tile=2,
        min_valid=0.999,
        clip_low=50,
        clip_high=65,
    )

    assert gray.shape == (3, 2, 2)
    assert paired.shape == (3, 2, 2)
    assert paired.dtype == np.uint8
    assert paired[0, 0, 0] == 1
    assert np.all(gray >= -1.0)
    assert np.all(gray <= 1.0)
