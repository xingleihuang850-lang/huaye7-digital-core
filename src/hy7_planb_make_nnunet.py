#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
花页7 Plan B —— E3：把同网格 sus+pore 做成 nnU-Netv2 数据集（受控对照）。

目的：以同工具的受限对照检验同网格输入是否与更高内部 Dice 一致。历史构建、
训练和空间切分因素未完全受控，因此不将结果归因为唯一因果变量。

历史 E3 结果保持原口径。未来空间独立重跑才传 --split-manifest，并显式指定
--n-train/--n-val/--n-test；该路径会记录坐标、拒绝候选和 nnU-Net split 证据。

标签：pore.raw==0 → 1(pore)，其余 → 0(background，含基质与柱塞外)。
子块限制在柱塞内(sus>0 占比高)。图像=sus 灰度(CT 通道)。

在 hy7-linux (env nnunet_t28, 有 SimpleITK) 上运行：
  python src/hy7_planb_make_nnunet.py --scale ct28 \
      --root ~/HXL/HY7_source/吉林大学数据报告归总 --layout source \
      --did 722 --n 20 --patch 192 --out ~/HXL/HY7_planb/nnunet/nnUNet_raw
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
import numpy as np
import SimpleITK as sitk

from hy7_planb_io import ScaleVolumes, IGNORE
from hy7_spatial_split_contract import COMPLETED_STATUS, PLANNED_STATUS, validate_split_manifest


def load_spatial_plan(path, dims):
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    result = validate_split_manifest(manifest)
    if not result["passed"] or manifest.get("status") != PLANNED_STATUS:
        raise SystemExit(f"[x] --split-manifest must be a valid planned contract: {result['errors']}")
    if tuple(manifest["source"]["shape_zyx"]) != tuple(dims):
        raise SystemExit(f"[x] manifest source shape {manifest['source']['shape_zyx']} != volume shape {dims}")
    return manifest, result["regions"]


def spatial_crop_start(regions, axis, split, dims, patch, rng):
    axis_index = {"z": 0, "y": 1, "x": 2}[axis]
    starts = []
    for index, length in enumerate(dims):
        lower, upper = (regions[split] if index == axis_index else (0, length))
        if upper - lower < patch:
            raise SystemExit(f"[x] {split} region [{lower},{upper}) is smaller than patch {patch}")
        starts.append(int(rng.integers(lower, upper - patch + 1)))
    return tuple(starts)


def finalize_spatial_manifest(path, manifest, accepted, rejected, base):
    case_mapping = base / "case_coordinates.json"
    splits_final = base / "splits_final.json"
    mapping = {crop["artifact_id"]: {"split": crop["split"], "bounds_zyx": crop["bounds_zyx"]} for crop in accepted}
    case_mapping.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    splits_final.write_text(json.dumps([{
        "train": [crop["artifact_id"] for crop in accepted if crop["split"] == "train"],
        "val": [crop["artifact_id"] for crop in accepted if crop["split"] == "val"],
    }], ensure_ascii=False, indent=2), encoding="utf-8")
    manifest.update({
        "status": COMPLETED_STATUS,
        "crops": accepted,
        "rejected_crops": rejected,
        "run": {
            "command": " ".join(sys.argv),
            "code_sha": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "environment": f"python={sys.version.split()[0]}; SimpleITK={sitk.Version_VersionString()}",
        },
        "artifacts": {"case_mapping": str(case_mapping), "splits_final_json": str(splits_final)},
    })
    result = validate_split_manifest(manifest)
    if not result["passed"]:
        raise SystemExit(f"[x] generated spatial manifest failed validation: {result['errors']}")
    Path(path).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


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
    ap.add_argument("--split-manifest", default=None,
                    help="未来重跑用 planned spatial contract；提供后必须同时给三个 split 的目标数")
    ap.add_argument("--n-train", type=int, default=None, help="--split-manifest 时 train 目标子块数")
    ap.add_argument("--n-val", type=int, default=None, help="--split-manifest 时 val 目标子块数")
    ap.add_argument("--n-test", type=int, default=None, help="--split-manifest 时 test 目标子块数")
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
    if a.split_manifest:
        if any(target is None or target <= 0 for target in (a.n_train, a.n_val, a.n_test)):
            raise SystemExit("[x] --split-manifest requires positive --n-train, --n-val, and --n-test")
        os.makedirs(os.path.join(base, "imagesTs"), exist_ok=True)
        os.makedirs(os.path.join(base, "labelsTs"), exist_ok=True)
        manifest, regions = load_spatial_plan(a.split_manifest, sv.dims)
        targets = {"train": a.n_train, "val": a.n_val, "test": a.n_test}
        accepted, rejected, pore_fracs = [], [], []
        candidate = 0
        for split, target in targets.items():
            attempts = 0
            while sum(crop["split"] == split for crop in accepted) < target and attempts < target * 200:
                attempts += 1
                z, y, x = spatial_crop_start(regions, manifest["split_policy"]["axis"], split, sv.dims, P, rng)
                bounds = [z, z + P, y, y + P, x, x + P]
                ic = np.asarray(sv.img[z:z+P, y:y+P, x:x+P]).copy()
                pc = np.asarray(sv.pore[z:z+P, y:y+P, x:x+P])
                valid = float((ic > 0).mean())
                lbl = (pc == sv.pore_val).astype(np.uint8)
                pf = float(lbl.mean())
                if valid < a.min_valid or pf < a.min_pore:
                    rejected.append({
                        "id": f"candidate_{candidate:06d}", "bounds_zyx": bounds,
                        "reason": "below_min_valid" if valid < a.min_valid else "below_min_pore",
                        "proposed_split": split, "valid_fraction": round(valid, 6), "pore_fraction": round(pf, 6),
                    })
                    candidate += 1
                    continue
                cid = f"HY7_{len(accepted):03d}"
                output_split = "Ts" if split == "test" else "Tr"
                im = sitk.GetImageFromArray(ic.astype(np.float32)); im.SetSpacing((1.0, 1.0, 1.0))
                lm = sitk.GetImageFromArray(lbl); lm.SetSpacing((1.0, 1.0, 1.0))
                sitk.WriteImage(im, os.path.join(base, f"images{output_split}", f"{cid}_0000.nii.gz"))
                sitk.WriteImage(lm, os.path.join(base, f"labels{output_split}", f"{cid}.nii.gz"))
                accepted.append({
                    "id": cid, "artifact_id": cid, "split": split, "bounds_zyx": bounds,
                    "valid_fraction": round(valid, 6), "pore_fraction": round(pf, 6),
                })
                pore_fracs.append(pf)
                candidate += 1
            if sum(crop["split"] == split for crop in accepted) < target:
                attempt_path = Path(base) / "incomplete_spatial_split_attempt.json"
                attempt_path.write_text(json.dumps({"accepted": accepted, "rejected_crops": rejected}, ensure_ascii=False, indent=2), encoding="utf-8")
                raise SystemExit(f"[x] {split} accepted fewer than {target}; audit written to {attempt_path}")
        finalize_spatial_manifest(a.split_manifest, manifest, accepted, rejected, Path(base))
        dj = {"channel_names": {"0": "CT"}, "labels": {"background": 0, "pore": 1},
              "numTraining": targets["train"] + targets["val"], "file_ending": ".nii.gz", "name": name,
              "reference": f"HY7 {a.scale} spatial split contract: {a.split_manifest}"}
        Path(base, "dataset.json").write_text(json.dumps(dj, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f">> {ds}: train/val/test = {targets['train']}/{targets['val']}/{targets['test']} → {base}")
        print(f"   accepted={len(accepted)} rejected={len(rejected)}; split manifest completed: {a.split_manifest}")
        return
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
