#!/usr/bin/env python3
"""HY7 phase-2 gray calibration utilities.

This module formalizes the qmatch/gray-calibration step required by the
B1.1 conditional close.  It is deliberately small and deterministic:

- fit a reference empirical CDF from a fixed gray reference array;
- map generated gray values to that reference distribution by quantile rank;
- optionally convert calibrated [-1, 1] gray values to the raw-intensity range
  expected by the HY7 nnUNet 2d reviewer.

No B1.1 topology gate is changed here.  This is inference preprocessing only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

VERSION = "hy7-gray-calibration-qmatch-v1"
RAW_MIN = 45.0
RAW_MAX = 205.0


def load_reference_values(path: str | Path, *, split: str = "all") -> np.ndarray:
    """Load reference gray values as a 1D sorted float32 array.

    split is intentionally simple and reproducible:
    - all: all slices
    - even: even-indexed slices
    - odd: odd-indexed slices
    """
    arr = np.load(path).astype(np.float32)
    if arr.ndim < 2:
        raise ValueError(f"reference array must be at least 2D, got shape={arr.shape}")
    if split == "even":
        arr = arr[::2]
    elif split == "odd":
        arr = arr[1::2]
    elif split != "all":
        raise ValueError("split must be one of: all, even, odd")
    if arr.size == 0:
        raise ValueError(f"reference split {split!r} is empty")
    return np.sort(arr.reshape(-1).astype(np.float32))


def quantile_match(values: np.ndarray, reference_sorted: np.ndarray) -> np.ndarray:
    """Map values to the empirical distribution represented by reference_sorted.

    The mapping is deterministic and rank-preserving. Ties keep stable order via
    mergesort; this matters for reproducibility when gray arrays contain plateaus.
    """
    ref = np.asarray(reference_sorted, dtype=np.float32).reshape(-1)
    if ref.size == 0:
        raise ValueError("reference_sorted must not be empty")
    x = np.asarray(values, dtype=np.float32)
    flat = x.reshape(-1)
    if flat.size == 0:
        raise ValueError("values must not be empty")
    order = np.argsort(flat, kind="mergesort")
    ranks = np.empty_like(order)
    ranks[order] = np.arange(flat.size)
    if flat.size == 1:
        idx = np.array([ref.size // 2], dtype=np.int64)
    else:
        idx = np.rint(ranks.astype(np.float64) / (flat.size - 1) * (ref.size - 1)).astype(np.int64)
    out = ref[np.clip(idx, 0, ref.size - 1)].reshape(x.shape)
    return out.astype(np.float32)


def to_nnunet_raw_intensity(gray: np.ndarray, *, raw_min: float = RAW_MIN, raw_max: float = RAW_MAX) -> np.ndarray:
    """Convert normalized [-1, 1] gray to HY7 nnUNet raw intensity range."""
    g = np.asarray(gray, dtype=np.float32)
    out = (g + 1.0) * ((raw_max - raw_min) / 2.0) + raw_min
    return np.clip(out, raw_min, raw_max).astype(np.float32)


def distribution_stats(values: np.ndarray, reference: np.ndarray) -> dict[str, float]:
    """Small deterministic stats used in manifests and calibration QA."""
    x = np.asarray(values, dtype=np.float32).reshape(-1)
    r = np.asarray(reference, dtype=np.float32).reshape(-1)
    qs = [1, 5, 25, 50, 75, 95, 99]
    out: dict[str, float] = {
        "mean": float(x.mean()),
        "std": float(x.std()),
        "min": float(x.min()),
        "max": float(x.max()),
    }
    xq = np.percentile(x, qs)
    rq = np.percentile(r, qs)
    out["quantile_mae"] = float(np.mean(np.abs(xq - rq)))
    for q, xv, rv in zip(qs, xq, rq):
        out[f"q{q:02d}"] = float(xv)
        out[f"ref_q{q:02d}"] = float(rv)
    return out


def calibrate_array(values: np.ndarray, reference_path: str | Path, *, split: str = "all") -> tuple[np.ndarray, dict[str, Any]]:
    ref_sorted = load_reference_values(reference_path, split=split)
    calibrated = quantile_match(values, ref_sorted)
    manifest = {
        "version": VERSION,
        "method": "empirical_quantile_match_rank_preserving",
        "reference_path": str(reference_path),
        "reference_split": split,
        "input_shape": list(values.shape),
        "input_stats": distribution_stats(values, ref_sorted),
        "calibrated_stats": distribution_stats(calibrated, ref_sorted),
    }
    return calibrated, manifest


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="HY7 deterministic qmatch/gray calibration preprocessing")
    p.add_argument("--input", required=True, help="input generated gray .npy, normalized to [-1, 1]")
    p.add_argument("--reference", required=True, help="reference gray .npy used to fit empirical CDF")
    p.add_argument("--output", required=True, help="output calibrated gray .npy")
    p.add_argument("--split", default="all", choices=["all", "even", "odd"], help="reference split for held-out QA")
    p.add_argument("--manifest", default=None, help="optional JSON manifest path")
    p.add_argument("--raw-output", default=None, help="optional nnUNet raw-intensity .npy output")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    src = Path(args.input)
    values = np.load(src).astype(np.float32)
    calibrated, manifest = calibrate_array(values, args.reference, split=args.split)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.save(out, calibrated)
    manifest.update({"input": str(src), "output": str(out)})
    if args.raw_output:
        raw = to_nnunet_raw_intensity(calibrated)
        raw_out = Path(args.raw_output)
        raw_out.parent.mkdir(parents=True, exist_ok=True)
        np.save(raw_out, raw)
        manifest["raw_output"] = str(raw_out)
        manifest["raw_range"] = [RAW_MIN, RAW_MAX]
    if args.manifest:
        mp = Path(args.manifest)
        mp.parent.mkdir(parents=True, exist_ok=True)
        mp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
