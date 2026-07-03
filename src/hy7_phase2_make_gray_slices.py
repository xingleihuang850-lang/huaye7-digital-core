#!/usr/bin/env python
"""B1 阶段二：从同网格 ct28 sus 体提取灰度 2D 切片 → DDPM 训练集。

输出：
  train.npy      float32, (N, T, T), [-1, 1]
  test.npy       float32, (N, T, T), [-1, 1]
  test_pore.npy  uint8,   (N, T, T), 1=pore, 0=non-pore
  meta.json      数据源、split、归一化、灰度/孔隙分布摘要

设计依据见 notes/26_阶段二_B1灰度介质生成设计.md。
"""
import argparse
import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np

from hy7_planb_io import IGNORE, KNOWN_POROSITY_PCT, VOLUMES, open_memmap, sample_zsel, vol_path


def sha256_file(path, limit=None):
    h = hashlib.sha256()
    n = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
            n += len(chunk)
            if limit and n >= limit:
                break
    return h.hexdigest()


def decode_phase_value(mm, target_pct):
    zsel = sample_zsel(mm.shape[0])
    sl = np.stack([np.asarray(mm[z]) for z in zsel])
    vals, counts = np.unique(sl, return_counts=True)
    frac = counts / counts.sum() * 100
    return int(vals[int(np.argmin(np.abs(frac - target_pct)))])


def normalize_gray(img, clip_low, clip_high):
    """Clip uint8 gray to [clip_low, clip_high] and map linearly to [-1, 1]."""
    if clip_high <= clip_low:
        raise ValueError(f"clip_high must be > clip_low: {clip_low}, {clip_high}")
    x = img.astype(np.float32)
    x = np.clip(x, clip_low, clip_high)
    x = (x - float(clip_low)) / float(clip_high - clip_low)
    return (x * 2.0 - 1.0).astype(np.float32)


def tiles_from_gray(img2d, pore2d, valid2d, tile, min_valid, clip_low, clip_high):
    """Return paired normalized gray tiles and pore tiles from one 2D slice."""
    h, w = img2d.shape
    gray_tiles, pore_tiles = [], []
    for y0 in range(0, h - tile + 1, tile):
        for x0 in range(0, w - tile + 1, tile):
            valid = valid2d[y0:y0 + tile, x0:x0 + tile]
            if float(valid.mean()) < min_valid:
                continue
            gray = img2d[y0:y0 + tile, x0:x0 + tile]
            pore = pore2d[y0:y0 + tile, x0:x0 + tile]
            gray_tiles.append(normalize_gray(gray, clip_low, clip_high))
            pore_tiles.append(pore.astype(np.uint8))
    if not gray_tiles:
        return (np.zeros((0, tile, tile), np.float32),
                np.zeros((0, tile, tile), np.uint8))
    return np.stack(gray_tiles), np.stack(pore_tiles)


def stack_or_empty(xs, shape, dtype):
    return np.concatenate(xs, axis=0) if xs else np.zeros(shape, dtype)


def hist_uint8_from_raw_tiles(arr):
    raw = np.rint((arr.astype(np.float32) + 1.0) * 0.5 * 255.0).clip(0, 255).astype(np.uint8)
    return np.bincount(raw.ravel(), minlength=256).astype(int).tolist()


def pct(a, qs):
    if len(a) == 0:
        return {str(q): None for q in qs}
    return {str(q): round(float(np.percentile(a, q)), 6) for q in qs}


def stack_summary_gray(stack):
    if len(stack) == 0:
        return {"n": 0}
    means = stack.reshape(len(stack), -1).mean(axis=1)
    stds = stack.reshape(len(stack), -1).std(axis=1)
    return {
        "n": int(len(stack)),
        "global_min": round(float(stack.min()), 6),
        "global_max": round(float(stack.max()), 6),
        "tile_mean": pct(means, [0, 1, 5, 50, 95, 99, 100]),
        "tile_std": pct(stds, [0, 1, 5, 50, 95, 99, 100]),
    }


def stack_summary_pore(stack):
    if len(stack) == 0:
        return {"n": 0}
    phi = stack.reshape(len(stack), -1).mean(axis=1) * 100
    return {
        "n": int(len(stack)),
        "phi_pct_mean": round(float(phi.mean()), 6),
        "phi_pct_median": round(float(np.median(phi)), 6),
        "phi_pct": pct(phi, [0, 1, 5, 50, 95, 99, 100]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", default="ct28", choices=["ct28"])
    ap.add_argument("--root", required=True)
    ap.add_argument("--layout", default="source", choices=["local", "source"])
    ap.add_argument("--tile", type=int, default=128)
    ap.add_argument("--z-step", type=int, default=6)
    ap.add_argument("--axes", default="z", choices=["z"])
    ap.add_argument("--min-valid", type=float, default=0.999)
    ap.add_argument("--test-frac", type=float, default=0.2)
    ap.add_argument("--clip-low", type=float, default=45.0)
    ap.add_argument("--clip-high", type=float, default=205.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--hash-prefix-mib", type=int, default=256)
    a = ap.parse_args()

    t0 = time.time()
    img = open_memmap(f"{a.scale}_sus", root=a.root, layout=a.layout)
    pore_raw = open_memmap(f"{a.scale}_pore", root=a.root, layout=a.layout)
    if img.shape != pore_raw.shape:
        raise ValueError(f"shape mismatch: sus={img.shape}, pore={pore_raw.shape}")
    pore_val = decode_phase_value(pore_raw, KNOWN_POROSITY_PCT[a.scale])
    nz, _, _ = img.shape
    z_test_start = int(nz * (1 - a.test_frac))

    train_gray, test_gray, test_pore = [], [], []
    train_pore_for_meta = []
    for z in range(0, nz, a.z_step):
        g = np.asarray(img[z])
        p = (np.asarray(pore_raw[z]) == pore_val)
        valid = (g != 0) | p
        gray_tiles, pore_tiles = tiles_from_gray(g, p, valid, a.tile, a.min_valid, a.clip_low, a.clip_high)
        if z >= z_test_start:
            test_gray.append(gray_tiles)
            test_pore.append(pore_tiles)
        else:
            train_gray.append(gray_tiles)
            train_pore_for_meta.append(pore_tiles)

    tr = stack_or_empty(train_gray, (0, a.tile, a.tile), np.float32)
    ts = stack_or_empty(test_gray, (0, a.tile, a.tile), np.float32)
    tp = stack_or_empty(test_pore, (0, a.tile, a.tile), np.uint8)
    trp = stack_or_empty(train_pore_for_meta, (0, a.tile, a.tile), np.uint8)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "train.npy", tr)
    np.save(out / "test.npy", ts)
    np.save(out / "test_pore.npy", tp)

    src_sus = Path(vol_path(f"{a.scale}_sus", a.root, a.layout))
    src_pore = Path(vol_path(f"{a.scale}_pore", a.root, a.layout))
    hash_limit = a.hash_prefix_mib * 1024 * 1024
    meta = {
        "task": "B1 gray sus slices",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "scale": a.scale,
        "source": {
            "sus_path": str(src_sus),
            "sus_size_bytes": src_sus.stat().st_size,
            "sus_mtime": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(src_sus.stat().st_mtime)),
            "sus_sha256_first_mib": a.hash_prefix_mib,
            "sus_sha256_first": sha256_file(src_sus, hash_limit),
            "pore_path": str(src_pore),
            "pore_size_bytes": src_pore.stat().st_size,
            "pore_mtime": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(src_pore.stat().st_mtime)),
            "pore_sha256_first_mib": a.hash_prefix_mib,
            "pore_sha256_first": sha256_file(src_pore, hash_limit),
        },
        "volume": {"dims_zyx": list(VOLUMES[f"{a.scale}_sus"]["dims"]), "dtype": "uint8"},
        "valid_mask_rule": "(sus != 0) OR (pore == pore_val); pore overrides outside-air zeros",
        "pore_val": int(pore_val),
        "split": {
            "tile": a.tile,
            "z_step": a.z_step,
            "axes": a.axes,
            "min_valid": a.min_valid,
            "test_frac": a.test_frac,
            "seed": a.seed,
            "z_test_start": z_test_start,
        },
        "normalization": {
            "policy": "clip then linear map to [-1,1]",
            "clip_low": a.clip_low,
            "clip_high": a.clip_high,
            "source_probe": "experiments/花页7_PlanB_记录/phase2/b1_gray_sus/probe_20260703/",
        },
        "outputs": {
            "train": {"path": str(out / "train.npy"), "shape": list(tr.shape), "dtype": str(tr.dtype)},
            "test": {"path": str(out / "test.npy"), "shape": list(ts.shape), "dtype": str(ts.dtype)},
            "test_pore": {"path": str(out / "test_pore.npy"), "shape": list(tp.shape), "dtype": str(tp.dtype)},
        },
        "gray_summary": {"train": stack_summary_gray(tr), "test": stack_summary_gray(ts)},
        "pore_summary": {"train_reference": stack_summary_pore(trp), "test_pore": stack_summary_pore(tp)},
        "elapsed_sec": round(time.time() - t0, 3),
    }
    with open(out / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(json.dumps({
        "out": str(out),
        "n_train": int(len(tr)),
        "n_test": int(len(ts)),
        "test_pore_phi_mean": meta["pore_summary"]["test_pore"].get("phi_pct_mean"),
        "clip": [a.clip_low, a.clip_high],
        "elapsed_sec": meta["elapsed_sec"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
