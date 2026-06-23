#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
花页7 Plan B —— 多尺度对齐自检（numpy + matplotlib，不依赖 torch）。

Plan B 的立论：服务商「处理图像」里的 sus/pore/feng 是**同一处理网格**的产物，
天生共配准，可绕过跨尺度原图配准这个真瓶颈。本脚本把这个前提坐实：
  1. 维度一致性：同尺度各组件体 shape 必须相同；
  2. 标签互斥性：pore 与 feng 的相体素不应大面积重叠；
  3. 视觉对齐：在若干 z 切片上把灰度(sus)与标签(pore/feng)叠加出图，
     人眼即可判断标签是否贴合结构、轴序是否正确（错乱=轴序需调）。

产物：experiments/hy7_planb/align_check/<scale>_z*.png + 一份 summary.json

用法：
  .venv/bin/python src/hy7_planb_check_alignment.py --scale ct14
  .venv/bin/python src/hy7_planb_check_alignment.py --scale ct28 --nslices 5
"""
import os, json, argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from hy7_planb_io import open_memmap, exists, KNOWN_POROSITY_PCT

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "experiments", "hy7_planb", "align_check")

# 每个尺度参与自检的组件体
SCALE_COMPONENTS = {
    "ct14": {"gray": "ct14_sus", "pore": "ct14_pore", "frac": "ct14_feng"},
    "ct28": {"gray": "ct28_sus", "pore": "ct28_pore"},
}


def phase_value(mm, target_pct, sample_z):
    """取若干切片，找占比最接近已知孔隙度的取值 → 该相的标记值。"""
    sl = np.stack([np.asarray(mm[z]) for z in sample_z])
    vals, counts = np.unique(sl, return_counts=True)
    frac = counts / counts.sum() * 100
    i = int(np.argmin(np.abs(frac - target_pct)))
    return int(vals[i]), float(frac[i])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", choices=list(SCALE_COMPONENTS), required=True)
    ap.add_argument("--nslices", type=int, default=6)
    a = ap.parse_args()

    comp = SCALE_COMPONENTS[a.scale]
    missing = [k for k in comp.values() if not exists(k)]
    if missing:
        raise SystemExit(f"[x] 缺体素（拷贝未完成？）：{missing}")

    gray = open_memmap(comp["gray"])
    pore = open_memmap(comp["pore"])
    frac = open_memmap(comp["frac"]) if "frac" in comp else None

    # 1) 维度一致性
    shapes = {comp[k]: open_memmap(comp[k]).shape for k in comp}
    assert len({tuple(s) for s in shapes.values()}) == 1, f"维度不一致：{shapes}"
    nz, ny, nx = gray.shape

    os.makedirs(OUTDIR, exist_ok=True)
    zsel = np.linspace(nz * 0.15, nz * 0.85, a.nslices).astype(int)

    # pore/feng 的相标记值（用已核校孔隙度反推）
    pore_val, pore_frac = phase_value(pore, KNOWN_POROSITY_PCT[a.scale], zsel)
    summary = {"scale": a.scale, "shape_zyx": [nz, ny, nx], "shapes": {k: list(v) for k, v in shapes.items()},
               "pore_value": pore_val, "pore_frac_pct_sampled": round(pore_frac, 4),
               "known_porosity_pct": KNOWN_POROSITY_PCT[a.scale], "slices": zsel.tolist()}
    if frac is not None:
        frac_val, frac_fr = phase_value(frac, 0.7, zsel)   # 裂缝占比小，0.7% 量级仅作种子
        summary["frac_value"] = frac_val
        summary["frac_frac_pct_sampled"] = round(frac_fr, 4)

    # 2) 互斥性 + 3) 叠加出图
    overlap_pcts = []
    for z in zsel:
        g = np.asarray(gray[z]).astype(np.float32)
        pm = np.asarray(pore[z]) == pore_val
        fm = (np.asarray(frac[z]) == summary.get("frac_value")) if frac is not None else np.zeros_like(pm)
        if frac is not None:
            inter = np.logical_and(pm, fm).sum()
            uni = np.logical_or(pm, fm).sum()
            overlap_pcts.append(round(float(inter) / float(uni) * 100, 3) if uni else 0.0)

        fig, ax = plt.subplots(1, 2, figsize=(11, 5.6))
        gn = (g - g.min()) / (np.ptp(g) + 1e-6)
        ax[0].imshow(gn, cmap="gray"); ax[0].set_title(f"{comp['gray']} z={z}"); ax[0].axis("off")
        ax[1].imshow(gn, cmap="gray")
        ov = np.zeros((*pm.shape, 4), np.float32)
        ov[pm] = [1, 0, 0, 0.55]                 # 孔隙=红
        if frac is not None:
            ov[fm] = [0, 0.6, 1, 0.7]            # 裂缝=蓝
        ax[1].imshow(ov); ax[1].set_title("overlay: pore(红) frac(蓝)"); ax[1].axis("off")
        fig.tight_layout()
        fp = os.path.join(OUTDIR, f"{a.scale}_z{z:04d}.png")
        fig.savefig(fp, dpi=110); plt.close(fig)

    if overlap_pcts:
        summary["pore_frac_overlap_pct_per_slice"] = overlap_pcts
        summary["overlap_ok"] = bool(max(overlap_pcts) < 5.0)   # 互斥相重叠应很小
    summary["png_dir"] = os.path.relpath(OUTDIR, ROOT)

    json.dump(summary, open(os.path.join(OUTDIR, f"summary_{a.scale}.json"), "w"),
              ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n>> 叠加图见 {summary['png_dir']}/  —— 人眼确认标签贴合结构、轴序正确。")


if __name__ == "__main__":
    main()
