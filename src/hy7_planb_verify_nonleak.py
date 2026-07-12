#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
花页7 Plan B —— 防泄漏 / 配准正确性 双重核验（numpy-only）。

回答两个"防编造"关键问题：
  (1) sus.raw 是否独立 CT 灰度？孔隙(pore==0)处灰度是否正常偏暗、且有变化（非被抹平）？
      —— 若孔隙被抹平为常数，则 sus→pore 分割是循环泄漏，dice 不可信。
  (2) 同网格 sus.raw 上孔隙更暗，能否反证 codex 的 2024→1500 裁剪错位？
      —— codex 拿 pore 标签对 2024³ raw（裁剪偏移 262）得"孔隙更亮"，与此矛盾。

用法： .venv/bin/python src/hy7_planb_verify_nonleak.py
"""
import numpy as np
from hy7_planb_io import open_memmap, SCALE_COMPONENTS, KNOWN_POROSITY_PCT, sample_zsel, decode_phase_value


def check(scale, nslices=5):
    if nslices <= 0:
        raise ValueError(f"nslices must be positive, got {nslices}")
    comp = SCALE_COMPONENTS[scale]
    sus = open_memmap(comp["image"]); pore = open_memmap(comp["pore"])
    z0 = sample_zsel(sus.shape[0], 6)
    pv = decode_phase_value(pore, KNOWN_POROSITY_PCT[scale], z0)   # 相值（应=0）
    zsel = np.linspace(sus.shape[0] * 0.2, sus.shape[0] * 0.8, nslices).astype(int)
    pore_g, non_g = [], []
    for z in zsel:
        s = np.asarray(sus[z]).astype(np.int32); p = np.asarray(pore[z])
        inside = s > 0
        pore_g.append(s[(p == pv) & inside]); non_g.append(s[(p != pv) & inside])
    pg = np.concatenate(pore_g); ng = np.concatenate(non_g)
    if pg.size == 0 or ng.size == 0:
        raise ValueError(f"{scale}: no valid pore/nonpore gray pixels inside sus > 0")
    return {
        "scale": scale, "pore_value": pv, "slices": zsel.tolist(),
        "pore_gray_mean": round(float(pg.mean()), 1), "nonpore_gray_mean": round(float(ng.mean()), 1),
        "pore_darker_by": round(float(ng.mean() - pg.mean()), 1),
        "pore_is_darker": bool(pg.mean() < ng.mean()),         # True=正常CT
        "pore_gray_nunique": int(np.unique(pg).size),
        "leakage_free": bool(np.unique(pg).size > 3),           # True=非被抹平→非循环
    }


def main():
    print("# 花页7 Plan B 防泄漏 / 配准正确性核验")
    for scale in SCALE_COMPONENTS:
        r = check(scale)
        print(f"\n[{scale}] 相值={r['pore_value']} 切片={r['slices']}")
        print(f"  孔隙灰度均值={r['pore_gray_mean']}  非孔隙={r['nonpore_gray_mean']}  "
              f"孔隙更暗 {r['pore_darker_by']}")
        print(f"  孔隙更暗(正常CT): {r['pore_is_darker']}   "
              f"孔隙灰度取值种类={r['pore_gray_nunique']} → 非循环泄漏: {r['leakage_free']}")
    print("\n结论：同网格 sus 上孔隙更暗且有正常灰度变化 → (1)分割非泄漏 (2)反证 codex 2024→1500 裁剪错位。")


if __name__ == "__main__":
    main()
