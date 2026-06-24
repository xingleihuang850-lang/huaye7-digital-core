#!/usr/bin/env python
"""
S3a: 花页7 Amics 25μm 多矿物 2D 分割 — 构建 nnU-Net v2 数据集。

输入（服务商 Amics «处理图像» 同尺寸配对）:
  202510052_25um_BSE_Image.tif      (H,W,3) 灰度→取通道0 = 训练输入
  202510052_25um_Mineral_Image.tif  (H,W,3) RGB 矿物图 = 标签来源

颜色→矿物映射经 [核] 面积比对粗扫矿物vol%确认（残差<0.05%），
见 experiments/花页7_PlanB_记录/evidence_amics_color_mapping.json。

5 类（用户确认 2026-06-24；磷灰石/白云母按 T0613 论文归金属重矿物）:
  0 背景(白/Unknown)  1 长英质  2 碳酸盐  3 粘土  4 金属重矿物

防泄漏: 单样品多瓦片有空间相关 → 按列做空间留出，最右 --test-frac 宽度为测试区，
其余为训练区，训练区内再交给 nnU-Net 5 折。固定 seed。
"""
import argparse, json, os
from pathlib import Path
import numpy as np
import tifffile
from PIL import Image

# RGB → class_id（[核] 见 evidence_amics_color_mapping.json）
COLOR2CLASS = {
    (255, 255, 255): 0, (128, 128, 128): 0,                 # 白背景 + Unknown
    (0, 255, 255): 1, (255, 192, 192): 1, (0, 128, 128): 1,  # 斜长石/石英/钾长石 → 长英质
    (192, 192, 255): 2, (128, 128, 255): 2, (255, 192, 128): 2,  # 方解石/白云石/铁白云石 → 碳酸盐
    (85, 107, 47): 3, (0, 192, 0): 3, (45, 83, 53): 3,       # 绿泥石/伊利石/伊蒙混层 → 粘土
    (255, 255, 0): 4, (255, 0, 0): 4, (255, 128, 128): 4, (0, 64, 0): 4,  # 黄铁矿/金红石/磷灰石/白云母 → 金属重矿物
}
CLASS_NAMES = {0: "background", 1: "felsic", 2: "carbonate", 3: "clay", 4: "metallic_heavy"}


def rgb_to_label(mineral):
    """(H,W,3) RGB → (H,W) uint8 label。未登记颜色（多为边界抗锯齿，<0.1%）→ 0，并统计占比。"""
    h, w, _ = mineral.shape
    flat = mineral.reshape(-1, 3)
    lbl = np.zeros(flat.shape[0], dtype=np.uint8)
    matched = np.zeros(flat.shape[0], dtype=bool)
    for rgb, cid in COLOR2CLASS.items():
        m = (flat[:, 0] == rgb[0]) & (flat[:, 1] == rgb[1]) & (flat[:, 2] == rgb[2])
        lbl[m] = cid
        matched |= m
    leftover = (~matched).sum() / flat.shape[0]
    return lbl.reshape(h, w), leftover


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Amics 文件夹")
    ap.add_argument("--raw", required=True, help="nnUNet_raw 根")
    ap.add_argument("--prefix", default="202510052_25um",
                    help="影像文件名前缀(尺度)，配 <prefix>_BSE_Image.tif / <prefix>_Mineral_Image.tif")
    ap.add_argument("--dataset-id", type=int, default=730)
    ap.add_argument("--name", default="HY7_Amics25um_5min")
    ap.add_argument("--tile", type=int, default=256)
    ap.add_argument("--min-cov", type=float, default=0.5, help="瓦片最小矿物(非背景)覆盖率，低于则丢弃(样品外背景)")
    ap.add_argument("--test-frac", type=float, default=0.2, help="最右侧此比例宽度作空间留出测试区")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)

    root = Path(args.root)
    bse = tifffile.imread(str(root / f"{args.prefix}_BSE_Image.tif"))
    mineral = tifffile.imread(str(root / f"{args.prefix}_Mineral_Image.tif"))
    assert bse.shape[:2] == mineral.shape[:2], (bse.shape, mineral.shape)
    gray = bse[:, :, 0] if bse.ndim == 3 else bse
    H, W = gray.shape
    print(f"[load] BSE {gray.shape} Mineral {mineral.shape}")

    label, leftover = rgb_to_label(mineral)
    print(f"[map] 未登记颜色占比 {leftover*100:.4f}%  (→背景)")
    binc = np.bincount(label.ravel(), minlength=5)
    print("[map] 全图类别像素%:", {CLASS_NAMES[i]: round(100*binc[i]/binc.sum(), 3) for i in range(5)})

    t = args.tile
    x_test_start = int(W * (1 - args.test_frac))
    ds = f"Dataset{args.dataset_id}_{args.name}"
    base = Path(args.raw) / ds
    for s in ["imagesTr", "labelsTr", "imagesTs", "labelsTs"]:
        (base / s).mkdir(parents=True, exist_ok=True)

    n_tr = n_ts = n_skip = 0
    for y0 in range(0, H - t + 1, t):
        for x0 in range(0, W - t + 1, t):
            lab = label[y0:y0+t, x0:x0+t]
            cov = (lab != 0).mean()
            if cov < args.min_cov:
                n_skip += 1
                continue
            img = gray[y0:y0+t, x0:x0+t]
            is_test = x0 >= x_test_start
            split = "Ts" if is_test else "Tr"
            cid = f"HY7A_{y0:05d}_{x0:05d}"
            Image.fromarray(img, mode="L").save(base / f"images{split}" / f"{cid}_0000.png")
            Image.fromarray(lab, mode="L").save(base / f"labels{split}" / f"{cid}.png")
            if is_test:
                n_ts += 1
            else:
                n_tr += 1
    print(f"[tile] train={n_tr}  test={n_ts}  skipped(<{args.min_cov}cov)={n_skip}")

    dj = {
        "channel_names": {"0": "BSE"},
        "labels": {v: k for k, v in CLASS_NAMES.items()},
        "numTraining": n_tr,
        "file_ending": ".png",
        "overwrite_image_reader_writer": "NaturalImage2DIO",
    }
    (base / "dataset.json").write_text(json.dumps(dj, ensure_ascii=False, indent=2))
    print(f"[done] {base}\n[done] dataset.json: {dj['labels']}")


if __name__ == "__main__":
    main()
