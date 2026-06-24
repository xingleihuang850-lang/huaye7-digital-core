#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
花页7 Plan B —— E3：把同网格 sus+pore 做成 nnU-Net v2 数据集（受控对照）。

目的：复刻 codex 的 nnU-Net 协议（同样 N 个 192³ 子块、2 相 background/pore），
**只把图像源从 2024³裁剪 换成同网格 sus.raw** → 看 nnU-Net 是否也从 dice≈0 翻身。
若翻身，则钉死"病根是配准、不是模型"（隔离模型变量）。

标签：pore.raw==0 → 1(pore)，其余 → 0(background，含基质与柱塞外)。
子块限制在柱塞内(sus>0 占比高)。图像=sus 灰度(CT 通道)。

在 hy7-linux (env nnunet_t28, 有 SimpleITK) 上运行：
  python src/hy7_planb_make_nnunet.py --scale ct28 \
      --root ~/HXL/HY7_source/吉林大学数据报告归总 --layout source \
      --did 722 --n 20 --patch 192 --out ~/HXL/HY7_planb/nnunet/nnUNet_raw
"""
import os, json, argparse
import numpy as np
import SimpleITK as sitk

from hy7_planb_io import ScaleVolumes, IGNORE


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", default="ct28")
    ap.add_argument("--root", default=None); ap.add_argument("--layout", default=None)
    ap.add_argument("--did", type=int, default=722, help="nnU-Net 数据集 ID")
    ap.add_argument("--name", default=None)
    ap.add_argument("--n", type=int, default=20, help="子块数（对齐 codex 的 20）")
    ap.add_argument("--patch", type=int, default=192)
    ap.add_argument("--min-pore", type=float, default=0.01, help="子块最小孔隙占比")
    ap.add_argument("--min-valid", type=float, default=0.85, help="子块最小柱塞内占比")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", required=True, help="nnUNet_raw 根目录")
    a = ap.parse_args()

    name = a.name or f"HY7_CT{ '2p8um' if a.scale=='ct28' else '14um'}_2phase_samegrid"
    ds = f"Dataset{a.did:03d}_{name}"
    base = os.path.join(a.out, ds)
    imgs = os.path.join(base, "imagesTr"); labs = os.path.join(base, "labelsTr")
    os.makedirs(imgs, exist_ok=True); os.makedirs(labs, exist_ok=True)

    sv = ScaleVolumes(a.scale, root=a.root, layout=a.layout, norm_samples=0)
    P = a.patch; rng = np.random.default_rng(a.seed)
    nz, ny, nx = sv.dims
    kept, tries = 0, 0
    pore_fracs = []
    while kept < a.n and tries < a.n * 200:
        tries += 1
        z = int(rng.integers(0, nz - P)); y = int(rng.integers(0, ny - P)); x = int(rng.integers(0, nx - P))
        ic = np.asarray(sv.img[z:z+P, y:y+P, x:x+P]).copy()
        pc = np.asarray(sv.pore[z:z+P, y:y+P, x:x+P])
        valid = (ic > 0).mean()
        if valid < a.min_valid:
            continue
        lbl = (pc == sv.pore_val).astype(np.uint8)        # 1=pore, 0=其余
        pf = float(lbl.mean())
        if pf < a.min_pore:
            continue
        cid = f"HY7_{kept:03d}"
        # SimpleITK：数组轴序 (z,y,x)；spacing 设 1
        im = sitk.GetImageFromArray(ic.astype(np.float32)); im.SetSpacing((1.0, 1.0, 1.0))
        lm = sitk.GetImageFromArray(lbl);                   lm.SetSpacing((1.0, 1.0, 1.0))
        sitk.WriteImage(im, os.path.join(imgs, f"{cid}_0000.nii.gz"))
        sitk.WriteImage(lm, os.path.join(labs, f"{cid}.nii.gz"))
        pore_fracs.append(round(pf, 4)); kept += 1

    dj = {"channel_names": {"0": "CT"},
          "labels": {"background": 0, "pore": 1},
          "numTraining": kept, "file_ending": ".nii.gz", "name": name,
          "reference": ("HY7 %s same-grid sus(image)+pore==0(label); 对照 codex 2024^3裁剪Dataset712; "
                        "Plan B 同网格免裁剪。" % a.scale)}
    json.dump(dj, open(os.path.join(base, "dataset.json"), "w"), ensure_ascii=False, indent=2)
    print(f">> {ds}: {kept} 子块 {P}^3 → {base}")
    print(f"   孔隙占比 min/mean/max = {min(pore_fracs):.4f}/{np.mean(pore_fracs):.4f}/{max(pore_fracs):.4f}")
    print(f"   dataset.json: 2 相 background/pore, channel CT")


if __name__ == "__main__":
    main()
