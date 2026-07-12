#!/usr/bin/env python
"""
S3a: 花页7 Amics 25μm 多矿物 2D 分割 — 构建 nnU-Netv2 数据集。

输入（服务商 Amics «处理图像» 同尺寸配对）:
  202510052_25um_BSE_Image.tif      (H,W,3) 灰度→取通道0 = 训练输入
  202510052_25um_Mineral_Image.tif  (H,W,3) RGB 矿物图 = 标签来源

颜色→矿物映射经 [核] 面积比对粗扫矿物vol%确认（残差<0.05%），
见 experiments/花页7_PlanB_记录/evidence_amics_color_mapping.json。

5 类（用户确认 2026-07-12；磷灰石/白云母按 T0613 论文归金属重矿物）:
  0 背景(白/登记 Unknown)  1 长英质  2 碳酸盐  3 粘土  4 金属重矿物
未登记 RGB 对未来重跑 fail-closed；不再静默归入背景，也不改写历史 S3 标签。

历史路径按列留出最右 --test-frac 宽度，未记录 buffer 或逐瓦片坐标，不能重述为
空间独立验证。未来重跑传 --split-manifest 才启用带 buffer 的 train/val/test 契约，
并保存每个接受/拒绝瓦片和 nnU-Net split 证据。
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
import numpy as np
import tifffile
from PIL import Image
from hy7_spatial_split_contract import COMPLETED_STATUS, PLANNED_STATUS, validate_split_manifest

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
    """Map only the frozen RGB taxonomy; unknown colors fail before dataset creation."""
    if mineral.ndim != 3 or mineral.shape[2] != 3:
        raise ValueError(f"mineral image must have shape [H,W,3], got {mineral.shape}")
    h, w, _ = mineral.shape
    flat = mineral.reshape(-1, 3)
    lbl = np.zeros(flat.shape[0], dtype=np.uint8)
    matched = np.zeros(flat.shape[0], dtype=bool)
    for rgb, cid in COLOR2CLASS.items():
        m = (flat[:, 0] == rgb[0]) & (flat[:, 1] == rgb[1]) & (flat[:, 2] == rgb[2])
        lbl[m] = cid
        matched |= m
    unknown = int((~matched).sum())
    if unknown:
        raise ValueError(f"unregistered RGB values: {unknown}/{flat.shape[0]} pixels; update taxonomy by an explicit research decision")
    leftover = 0.0
    return lbl.reshape(h, w), leftover


def split_for_bounds(regions, axis, bounds):
    axis_index = {"z": 0, "y": 1, "x": 2}[axis]
    start, stop = bounds[2 * axis_index], bounds[2 * axis_index + 1]
    for split, (region_start, region_stop) in regions.items():
        if region_start <= start and stop <= region_stop:
            return split
    return None


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
    ap.add_argument("--split-manifest", default=None,
                    help="未来重跑用 planned spatial contract；提供后按其 train/val/test 区域切分")
    args = ap.parse_args()
    root = Path(args.root)
    bse = tifffile.imread(str(root / f"{args.prefix}_BSE_Image.tif"))
    mineral = tifffile.imread(str(root / f"{args.prefix}_Mineral_Image.tif"))
    assert bse.shape[:2] == mineral.shape[:2], (bse.shape, mineral.shape)
    gray = bse[:, :, 0] if bse.ndim == 3 else bse
    H, W = gray.shape
    print(f"[load] BSE {gray.shape} Mineral {mineral.shape}")

    spatial_manifest = None
    spatial_regions = None
    if args.split_manifest:
        spatial_manifest = json.loads(Path(args.split_manifest).read_text(encoding="utf-8"))
        result = validate_split_manifest(spatial_manifest)
        if not result["passed"] or spatial_manifest.get("status") != PLANNED_STATUS:
            raise SystemExit(f"[x] --split-manifest must be a valid planned contract: {result['errors']}")
        if tuple(spatial_manifest["source"]["shape_zyx"]) != (1, H, W):
            raise SystemExit(f"[x] manifest source shape {spatial_manifest['source']['shape_zyx']} != Amics shape {[1, H, W]}")
        if spatial_manifest["split_policy"]["axis"] != "x":
            raise SystemExit("[x] Amics 2D tiling requires an x-axis spatial split manifest")
        spatial_regions = result["regions"]

    label, leftover = rgb_to_label(mineral)
    print(f"[map] 未登记颜色占比 {leftover*100:.4f}%  (fail-closed)")
    binc = np.bincount(label.ravel(), minlength=5)
    print("[map] 全图类别像素%:", {CLASS_NAMES[i]: round(100*binc[i]/binc.sum(), 3) for i in range(5)})

    t = args.tile
    x_test_start = int(W * (1 - args.test_frac))
    ds = f"Dataset{args.dataset_id}_{args.name}"
    base = Path(args.raw) / ds
    for s in ["imagesTr", "labelsTr", "imagesTs", "labelsTs"]:
        (base / s).mkdir(parents=True, exist_ok=True)

    n_tr = n_ts = n_skip = 0
    accepted, rejected = [], []
    candidate = 0
    for y0 in range(0, H - t + 1, t):
        for x0 in range(0, W - t + 1, t):
            bounds = [0, 1, y0, y0 + t, x0, x0 + t]
            lab = label[y0:y0+t, x0:x0+t]
            cov = (lab != 0).mean()
            if cov < args.min_cov:
                if spatial_manifest:
                    rejected.append({
                        "id": f"candidate_{candidate:06d}", "bounds_zyx": bounds,
                        "reason": "below_min_cov", "coverage": round(float(cov), 6),
                    })
                    candidate += 1
                n_skip += 1
                continue
            img = gray[y0:y0+t, x0:x0+t]
            split = split_for_bounds(spatial_regions, "x", bounds) if spatial_manifest else None
            if spatial_manifest and split is None:
                rejected.append({
                    "id": f"candidate_{candidate:06d}", "bounds_zyx": bounds,
                    "reason": "crosses_split_region_or_buffer", "coverage": round(float(cov), 6),
                })
                candidate += 1
                n_skip += 1
                continue
            is_test = split == "test" if spatial_manifest else x0 >= x_test_start
            split = "Ts" if is_test else "Tr"
            cid = f"HY7A_{y0:05d}_{x0:05d}"
            Image.fromarray(img, mode="L").save(base / f"images{split}" / f"{cid}_0000.png")
            Image.fromarray(lab, mode="L").save(base / f"labels{split}" / f"{cid}.png")
            if spatial_manifest:
                accepted.append({
                    "id": cid, "artifact_id": cid, "split": "test" if is_test else split_for_bounds(spatial_regions, "x", bounds),
                    "bounds_zyx": bounds, "coverage": round(float(cov), 6),
                })
                candidate += 1
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
    if spatial_manifest:
        case_mapping = base / "case_coordinates.json"
        splits_final = base / "splits_final.json"
        spatial_manifest.update({
            "status": COMPLETED_STATUS,
            "crops": accepted,
            "rejected_crops": rejected,
            "run": {
                "command": " ".join(sys.argv),
                "code_sha": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "environment": f"python={sys.version.split()[0]}; tifffile={tifffile.__version__}",
            },
            "artifacts": {"case_mapping": str(case_mapping), "splits_final_json": str(splits_final)},
        })
        result = validate_split_manifest(spatial_manifest)
        if not result["passed"]:
            attempt_path = base / "incomplete_spatial_split_attempt.json"
            attempt_path.write_text(json.dumps({"accepted": accepted, "rejected_crops": rejected}, ensure_ascii=False, indent=2))
            raise SystemExit(f"[x] generated spatial manifest failed validation: {result['errors']}; audit: {attempt_path}")
        mapping = {crop["artifact_id"]: {"split": crop["split"], "bounds_zyx": crop["bounds_zyx"]} for crop in accepted}
        case_mapping.write_text(json.dumps(mapping, ensure_ascii=False, indent=2))
        splits_final.write_text(json.dumps([{
            "train": [crop["artifact_id"] for crop in accepted if crop["split"] == "train"],
            "val": [crop["artifact_id"] for crop in accepted if crop["split"] == "val"],
        }], ensure_ascii=False, indent=2))
        Path(args.split_manifest).write_text(json.dumps(spatial_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[spatial] train/val/test = {result['crop_counts']['train']}/{result['crop_counts']['val']}/{result['crop_counts']['test']} "
              f"rejected={result['rejected_crop_count']} manifest={args.split_manifest}")
    print(f"[done] {base}\n[done] dataset.json: {dj['labels']}")


if __name__ == "__main__":
    main()
