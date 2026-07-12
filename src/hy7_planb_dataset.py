#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
花页7 Plan B —— 分割训练集构建（numpy-only，不依赖 torch）。

从同尺度、同网格的「灰度体 + 相掩膜」采 3D patch，按前景占比筛选，
落成 .npz shards + manifest.json。它是可选的预烤路径；默认 PlanB 训练直接
在线读取体素，不依赖这些 shard。
标签方案（3 相）：0=基质(matrix) / 1=孔隙(pore) / 2=裂缝(fracture)。
相标记值用已核校总孔隙度自动反推（见 hy7_planb_io），不靠猜。

逐 patch 惰性读 memmap 子立方，全程不把 4GB 体素读进内存。

该构建器不创建空间 train/val/test split，也不能证明空间独立性。manifest 仅
记录同体采样坐标、seed 和 shard 对应关系，供未来复核或受控重跑使用。

用法：
  .venv/bin/python src/hy7_planb_dataset.py --scale ct14 --patch 128 --n 400
  .venv/bin/python src/hy7_planb_dataset.py --scale ct28 --patch 96  --n 300 --min-fg 0.01
"""
import os, json, argparse
import numpy as np

from hy7_planb_io import open_memmap, exists, VOLUMES, KNOWN_POROSITY_PCT, validate_patch_size

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTROOT = os.path.join(ROOT, "data", "hy7_planb")

# image=灰度源；pore/frac=相掩膜（frac 可缺）
SCALE_SRC = {
    "ct14": {"image": "ct14_sus", "pore": "ct14_pore", "frac": "ct14_feng"},
    "ct28": {"image": "ct28_sus", "pore": "ct28_pore"},
}

IGNORE = 255


def validate_dataset_args(n, min_fg, bg_keep, shard):
    """Reject invalid sampling controls before opening multi-GB source volumes."""
    if n <= 0 or shard <= 0:
        raise ValueError("--n and --shard must be positive")
    if not 0.0 <= bg_keep <= 1.0 or min_fg < 0.0:
        raise ValueError("--bg-keep must be in [0,1] and --min-fg must be non-negative")


def foreground_fraction(label):
    """Measure pore/fracture fraction over valid voxels, excluding ignore voxels."""
    valid = label != IGNORE
    if not valid.any():
        raise ValueError("cannot measure foreground fraction without valid voxels")
    return float(((label == 1) | (label == 2))[valid].mean())


def decode_phase_value(mm, target_pct, zsel):
    sl = np.stack([np.asarray(mm[z]) for z in zsel])
    vals, counts = np.unique(sl, return_counts=True)
    frac = counts / counts.sum() * 100
    i = int(np.argmin(np.abs(frac - target_pct)))
    return int(vals[i])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", choices=list(SCALE_SRC), required=True)
    ap.add_argument("--patch", type=int, default=128)
    ap.add_argument("--n", type=int, default=400, help="目标 patch 数")
    ap.add_argument("--min-fg", type=float, default=0.005, help="前景(孔隙+裂缝)体素最小占比")
    ap.add_argument("--bg-keep", type=float, default=0.15, help="不达标 patch 仍保留的概率(类平衡)")
    ap.add_argument("--shard", type=int, default=50, help="每个 .npz 存多少 patch")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    try:
        validate_dataset_args(a.n, a.min_fg, a.bg_keep, a.shard)
    except ValueError as exc:
        raise SystemExit(f"[x] {exc}") from exc

    src = SCALE_SRC[a.scale]
    miss = [k for k in src.values() if not exists(k)]
    if miss:
        raise SystemExit(f"[x] 缺体素（拷贝未完成？）：{miss}")

    img = open_memmap(src["image"])
    pore = open_memmap(src["pore"])
    frac = open_memmap(src["frac"]) if "frac" in src else None
    nz, ny, nx = img.shape
    P = validate_patch_size(a.patch, (nz, ny, nx))
    rng = np.random.default_rng(a.seed)

    zsel = np.linspace(nz * 0.15, nz * 0.85, 6).astype(int)
    pore_val = decode_phase_value(pore, KNOWN_POROSITY_PCT[a.scale], zsel)
    frac_val = decode_phase_value(frac, 0.7, zsel) if frac is not None else None
    img_unique = np.unique(np.asarray(img[zsel[len(zsel) // 2]]))
    img_is_grayscale = img_unique.size > 8   # <=8 取值 ≈ 掩膜，灰度应有连续分布

    outdir = os.path.join(OUTROOT, a.scale)
    os.makedirs(outdir, exist_ok=True)

    kept, shard_imgs, shard_lbls, shard_id = 0, [], [], 0
    shard_provenance, shard_coordinates = [], []
    fg_hist, valid_hist = [], []
    img_sum = img_sum2 = img_n = 0.0
    tries, max_tries = 0, a.n * 80
    while kept < a.n and tries < max_tries:
        tries += 1
        z = int(rng.integers(0, nz - P + 1)); y = int(rng.integers(0, ny - P + 1)); x = int(rng.integers(0, nx - P + 1))
        ic = np.asarray(img[z:z+P, y:y+P, x:x+P]).copy()
        pc = np.asarray(pore[z:z+P, y:y+P, x:x+P])
        lbl = np.zeros((P, P, P), np.uint8)             # 0=matrix
        lbl[ic == 0] = IGNORE                           # 柱塞外方角(空气)→忽略，不计 loss
        lbl[pc == pore_val] = 1                          # 孔隙覆盖 ignore（真孔隙即便暗也算）
        if frac is not None:
            fc = np.asarray(frac[z:z+P, y:y+P, x:x+P])
            lbl[fc == frac_val] = 2
        valid = lbl != IGNORE
        valfrac = float(valid.mean())
        if valfrac < 0.5:                               # 主体在圆外的 patch 丢弃
            continue
        fg = foreground_fraction(lbl)                    # 前景=孔隙+裂缝，分母只含有效体素
        if fg < a.min_fg and rng.random() > a.bg_keep:
            continue
        shard_imgs.append(ic); shard_lbls.append(lbl.copy()); shard_coordinates.append([z, y, x])
        fg_hist.append(round(fg, 5)); valid_hist.append(round(valfrac, 4))
        v = ic[valid].astype(np.float64)                # 归一化统计只在有效区
        img_sum += v.sum(); img_sum2 += (v*v).sum(); img_n += v.size
        kept += 1
        if len(shard_imgs) >= a.shard:
            filename = f"patches_{shard_id:04d}.npz"
            np.savez_compressed(os.path.join(outdir, filename),
                                 image=np.stack(shard_imgs), label=np.stack(shard_lbls))
            shard_provenance.append({"file": filename, "count": len(shard_imgs), "coordinates_zyx": shard_coordinates})
            shard_id += 1; shard_imgs, shard_lbls, shard_coordinates = [], [], []
    if kept != a.n:
        raise SystemExit(f"[x] accepted only {kept}/{a.n} patches after {tries} attempts; no manifest was written")
    if shard_imgs:
        filename = f"patches_{shard_id:04d}.npz"
        np.savez_compressed(os.path.join(outdir, filename),
                            image=np.stack(shard_imgs), label=np.stack(shard_lbls))
        shard_provenance.append({"file": filename, "count": len(shard_imgs), "coordinates_zyx": shard_coordinates})
        shard_id += 1

    mean = img_sum / img_n; std = (img_sum2 / img_n - mean * mean) ** 0.5
    manifest = {
        "well": "花页7", "scale": a.scale, "patch": P, "n_patches": kept, "shards": shard_id,
        "label_scheme": {"0": "matrix", "1": "pore", "2": "fracture" if frac is not None else "(无)",
                         "255": "ignore(柱塞外/无效区)"},
        "ignore_index": 255,
        "phase_values": {"pore": pore_val, "fracture": frac_val},
        "image_source": src["image"], "image_is_grayscale": bool(img_is_grayscale),
        "image_unique_vals_sampled": int(img_unique.size),
        "norm": {"mean": round(mean, 3), "std": round(std, 3), "over": "有效区(非ignore)"},
        "fg_fraction": {"min": min(fg_hist) if fg_hist else 0, "max": max(fg_hist) if fg_hist else 0,
                        "mean": round(float(np.mean(fg_hist)), 5) if fg_hist else 0},
        "valid_fraction": {"min": min(valid_hist) if valid_hist else 0,
                            "mean": round(float(np.mean(valid_hist)), 4) if valid_hist else 0},
        "dims_src_zyx": list(img.shape), "tries": tries,
        "sampling": {
            "seed": a.seed, "min_fg": a.min_fg, "bg_keep": a.bg_keep,
            "foreground_denominator": "valid_voxels_only_excluding_ignore",
            "spatial_split_status": "same_volume_sampling_not_a_spatially_independent_split",
        },
        "shard_provenance": shard_provenance,
        "provenance": "服务商处理图像同网格组件体（天然共配准，Plan B）",
        "note_image": ("sus 为灰度体，可直接做 灰度→3相 分割" if img_is_grayscale else
                       "⚠ image 源取值≤8，疑为掩膜而非灰度——Plan B 灰度输入前提需复核"),
    }
    json.dump(manifest, open(os.path.join(outdir, "manifest.json"), "w"), ensure_ascii=False, indent=2)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"\n>> {kept} patch / {shard_id} shard → {os.path.relpath(outdir, ROOT)}/")
    if not img_is_grayscale:
        print("[!] 注意：image 源疑似掩膜，非灰度。落盘后请先看 inspect / align_check 出图确认。")


if __name__ == "__main__":
    main()
