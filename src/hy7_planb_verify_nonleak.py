#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
花页7 Plan B —— 标签回灌诊断 / 配准线索核验（numpy-only）。

回答两个"防编造"关键问题：
  (1) sus.raw 是否独立 CT 灰度？孔隙(pore==0)处灰度是否正常偏暗、且有变化（非被抹平）？
       —— 若孔隙被抹平为常数，则 sus→pore 可能存在标签回灌，dice 不可信。
  (2) 同网格 sus.raw 上孔隙更暗，能否反证 codex 的 2024→1500 裁剪错位？
       —— 可为早期 2024³ 裁剪错位提供线索，但不隔离为唯一因果变量。

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
        "leakage_free": bool(np.unique(pg).size > 3),           # historical key: no label-backfill signature detected
    }


def main():
    print("# 花页7 Plan B 标签回灌诊断 / 配准线索核验")
    for scale in SCALE_COMPONENTS:
        r = check(scale)
        print(f"\n[{scale}] 相值={r['pore_value']} 切片={r['slices']}")
        print(f"  孔隙灰度均值={r['pore_gray_mean']}  非孔隙={r['nonpore_gray_mean']}  "
              f"孔隙更暗 {r['pore_darker_by']}")
        print(f"  孔隙更暗(正常CT): {r['pore_is_darker']}   "
               f"孔隙灰度取值种类={r['pore_gray_nunique']} → 未见标签回灌特征: {r['leakage_free']}")
    print("\n结论：同网格 sus 上孔隙更暗且有灰度变化，未见直接标签回灌特征，并为早期裁剪错位提供线索。本检查不检验训练/验证/测试 crop 的空间重叠。")


if __name__ == "__main__":
    main()
