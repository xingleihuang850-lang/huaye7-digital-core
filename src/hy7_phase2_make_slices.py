#!/usr/bin/env python
"""M7.1 阶段二：从同网格 ct28(2.8μm) 体提取 2D 二值孔隙切片 → DDPM 训练集。

依据（见 notes/花页7_阶段二_2D扩散_启动设计.md 的 M5★三段依据 / M6）：
- 数据用 E2/E3 已验证可信的同网格 ct28 sus+pore（不引入配准风险）。
- 生成对象 = μm 级基质孔+微裂缝网络的 2D 结构（2.8μm 尺度自觉，承 S3 教训）。
- 防泄漏：沿 z 留出顶部 test-frac 体块为测试区（与训练区空间分离），固定 seed。

输出：train.npy / test.npy 形如 (N,T,T) uint8∈{0,1}（1=孔隙,0=基质）；
      meta.json（计数 + 孔隙度直方图 + 配置），便于评估对账。
"""
import argparse, json, os
import numpy as np
from hy7_planb_io import ScaleVolumes, IGNORE


def slice_label(sv, axis, idx):
    """取某轴第 idx 张 2D 切片的 (灰度, 2相标签)。标签: 0基质/1孔隙/255柱塞外。"""
    if axis == "z":
        ic = np.asarray(sv.img[idx]);       pc = np.asarray(sv.pore[idx])
    elif axis == "y":
        ic = np.asarray(sv.img[:, idx, :]); pc = np.asarray(sv.pore[:, idx, :])
    else:  # x
        ic = np.asarray(sv.img[:, :, idx]); pc = np.asarray(sv.pore[:, :, idx])
    lbl = np.zeros(ic.shape, np.uint8)
    lbl[ic == 0] = IGNORE                 # 圆柱塞外方角(空气)
    lbl[pc == sv.pore_val] = 1            # 真孔隙
    return lbl


def tiles_from(lbl2d, T, min_valid):
    H, W = lbl2d.shape
    out = []
    for y0 in range(0, H - T + 1, T):
        for x0 in range(0, W - T + 1, T):
            lab = lbl2d[y0:y0 + T, x0:x0 + T]
            if (lab != IGNORE).mean() < min_valid:   # 丢掉碰到柱塞边/外的瓦片
                continue
            out.append((lab == 1).astype(np.uint8))   # 二值孔隙结构
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", default="ct28")
    ap.add_argument("--root", required=True)
    ap.add_argument("--layout", default="source")
    ap.add_argument("--tile", type=int, default=256)
    ap.add_argument("--z-step", type=int, default=4, help="主轴切片下采样步长(降 z 相关)")
    ap.add_argument("--axes", default="z", help="采样轴: 'z' 或 'zyx'")
    ap.add_argument("--min-valid", type=float, default=0.999, help="瓦片需≥此比例在柱塞内")
    ap.add_argument("--test-frac", type=float, default=0.2, help="沿 z 顶部留出比例为测试区(防泄漏)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    sv = ScaleVolumes(a.scale, root=a.root, layout=a.layout)
    nz, ny, nx = sv.dims
    T = a.tile
    print(f"[i] {a.scale} dims={sv.dims} pore_val={sv.pore_val} n_cls={sv.n_cls}")
    z_test_start = int(nz * (1 - a.test_frac))
    tr, ts = [], []

    # 主轴 z：训练/测试按 z 分区（空间留出）；附加 y/x 轴只进训练集（增样，且这些切片跨整个 z，
    # 不破坏 z 顶部留出的测试独立性——测试只认 z 顶部块的 z 向切片）。
    for z in range(0, nz, a.z_step):
        tiles = tiles_from(slice_label(sv, "z", z), T, a.min_valid)
        (ts if z >= z_test_start else tr).extend(tiles)
    if "y" in a.axes:
        for y in range(0, ny, a.z_step):
            tr.extend(tiles_from(slice_label(sv, "y", y)[:z_test_start, :], T, a.min_valid))
    if "x" in a.axes:
        for x in range(0, nx, a.z_step):
            tr.extend(tiles_from(slice_label(sv, "x", x)[:z_test_start, :], T, a.min_valid))

    tr = np.stack(tr) if tr else np.zeros((0, T, T), np.uint8)
    ts = np.stack(ts) if ts else np.zeros((0, T, T), np.uint8)
    os.makedirs(a.out, exist_ok=True)
    np.save(os.path.join(a.out, "train.npy"), tr)
    np.save(os.path.join(a.out, "test.npy"), ts)

    def por(stack):
        return (stack.reshape(stack.shape[0], -1).mean(1) * 100) if len(stack) else np.array([0.0])
    ptr, pts = por(tr), por(ts)
    hist_edges = [0, 1, 2, 4, 6, 8, 10, 15, 100]
    meta = {
        "scale": a.scale, "tile": T, "z_step": a.z_step, "axes": a.axes,
        "min_valid": a.min_valid, "test_frac": a.test_frac, "seed": a.seed,
        "n_train": int(len(tr)), "n_test": int(len(ts)),
        "porosity_pct_train": {"mean": round(float(ptr.mean()), 3), "median": round(float(np.median(ptr)), 3),
                               "min": round(float(ptr.min()), 3), "max": round(float(ptr.max()), 3)},
        "porosity_pct_test": {"mean": round(float(pts.mean()), 3), "median": round(float(np.median(pts)), 3)},
        "porosity_hist_train_pct": {f"{hist_edges[i]}-{hist_edges[i+1]}": int(((ptr >= hist_edges[i]) & (ptr < hist_edges[i+1])).sum())
                                    for i in range(len(hist_edges) - 1)},
    }
    with open(os.path.join(a.out, "meta.json"), "w") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"[done] train={len(tr)} test={len(ts)}  孔隙度 train 均值={ptr.mean():.2f}% 中位={np.median(ptr):.2f}%")
    print(f"[done] -> {a.out}/{{train,test}}.npy + meta.json")


if __name__ == "__main__":
    main()
