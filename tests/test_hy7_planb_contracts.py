import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "src" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


io = load_module("hy7_planb_io")
alignment = load_module("hy7_planb_check_alignment")
nonleak = load_module("hy7_planb_verify_nonleak")
train = load_module("hy7_planb_train")
dataset = load_module("hy7_planb_dataset")


def test_open_memmap_checks_registered_bytes_and_opens_uint8(tmp_path, monkeypatch):
    raw = tmp_path / "toy.raw"
    np.arange(8, dtype=np.uint8).tofile(raw)
    monkeypatch.setattr(io, "VOLUMES", {"toy": {"dims": (2, 2, 2), "role": "toy", "scale": "toy"}})
    monkeypatch.setattr(io, "LOCAL_PATHS", {"toy": "toy.raw"})

    got = io.open_memmap("toy", root=str(tmp_path))
    assert got.shape == (2, 2, 2)
    assert int(got[1, 1, 1]) == 7

    raw.write_bytes(b"\x00")
    with pytest.raises(ValueError, match="字节数"):
        io.open_memmap("toy", root=str(tmp_path))


def test_label_contract_preserves_phase_priority_and_rejects_shape_mismatch():
    image = np.array([[0, 10], [10, 10]], dtype=np.uint8)
    pore = np.array([[0, 255], [255, 255]], dtype=np.uint8)
    frac = np.array([[255, 255], [0, 255]], dtype=np.uint8)

    label = io.build_label(image, pore, 0, frac, 0)
    assert label.tolist() == [[1, 0], [2, 0]]

    with pytest.raises(ValueError, match="shape mismatch"):
        io.build_label(image, pore[:, :1], 0)
    with pytest.raises(ValueError, match="fracture phase"):
        io.build_label(image, pore, 0, frac)


def test_sampling_contract_rejects_empty_z_and_invalid_patch_sizes():
    with pytest.raises(ValueError, match="at least one"):
        io.decode_phase_value(np.zeros((2, 2, 2), dtype=np.uint8), 1.0, [])
    with pytest.raises(ValueError, match="positive"):
        io.sample_zsel(0, 2)
    with pytest.raises(ValueError, match="smaller"):
        io.validate_patch_size(4, (4, 8, 8))
    assert io.validate_patch_size(4, (5, 8, 8)) == 4


def test_alignment_phase_value_requires_samples_and_returns_fraction():
    stack = np.array([[[0, 255], [0, 255]]], dtype=np.uint8)
    value, fraction = alignment.phase_value(stack, 50.0, [0])
    assert value == 0
    assert fraction == 50.0
    with pytest.raises(ValueError, match="at least one"):
        alignment.phase_value(stack, 50.0, [])


def test_nonleak_check_requires_valid_pore_and_nonpore_pixels(monkeypatch):
    sus = np.full((5, 3, 3), 100, dtype=np.uint8)
    pore = np.full((5, 3, 3), 255, dtype=np.uint8)
    pore[:, 1, 1] = 0
    sus[:, 1, 1] = np.array([20, 30, 40, 50, 60], dtype=np.uint8)

    monkeypatch.setattr(nonleak, "SCALE_COMPONENTS", {"toy": {"image": "sus", "pore": "pore"}})
    monkeypatch.setattr(nonleak, "KNOWN_POROSITY_PCT", {"toy": 10.0})
    monkeypatch.setattr(nonleak, "open_memmap", lambda key: sus if key == "sus" else pore)
    monkeypatch.setattr(nonleak, "decode_phase_value", lambda *_: 0)

    result = nonleak.check("toy", nslices=5)
    assert result["pore_is_darker"] is True
    assert result["leakage_free"] is True

    monkeypatch.setattr(nonleak, "open_memmap", lambda _key: np.zeros((5, 3, 3), dtype=np.uint8))
    with pytest.raises(ValueError, match="no valid pore/nonpore"):
        nonleak.check("toy", nslices=5)


def test_training_contract_requires_unet_compatible_patch_and_fraction():
    train.validate_training_args(128, 0.0)
    with pytest.raises(ValueError, match="divisible by 8"):
        train.validate_training_args(130, 0.0)
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        train.validate_training_args(128, 1.1)


def test_dataset_contract_excludes_ignore_from_foreground_and_validates_controls():
    label = np.array([[[dataset.IGNORE, 1], [2, 0]]], dtype=np.uint8)
    assert dataset.foreground_fraction(label) == pytest.approx(2 / 3)
    with pytest.raises(ValueError, match="valid voxels"):
        dataset.foreground_fraction(np.full((1, 1, 1), dataset.IGNORE, dtype=np.uint8))
    dataset.validate_dataset_args(4, 0.01, 0.15, 2)
    with pytest.raises(ValueError, match="positive"):
        dataset.validate_dataset_args(0, 0.01, 0.15, 2)
    with pytest.raises(ValueError, match=r"\[0,1\]"):
        dataset.validate_dataset_args(4, 0.01, 1.1, 2)
