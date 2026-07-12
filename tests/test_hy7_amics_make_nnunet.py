import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SPEC = importlib.util.spec_from_file_location("hy7_amics_make_nnunet", ROOT / "src" / "hy7_amics_make_nnunet.py")
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_rgb_taxonomy_maps_registered_colors_and_rejects_unknown_rgb():
    mineral = np.array([[[255, 255, 255], [0, 255, 255], [192, 192, 255], [85, 107, 47], [255, 255, 0]]], dtype=np.uint8)
    labels, leftover = mod.rgb_to_label(mineral)
    assert labels.tolist() == [[0, 1, 2, 3, 4]]
    assert leftover == 0.0

    mineral[0, 0] = [1, 2, 3]
    with pytest.raises(ValueError, match="unregistered RGB"):
        mod.rgb_to_label(mineral)
