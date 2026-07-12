#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
花页7 Plan B —— 体素 IO / 解码 / 在线 patch 采样（numpy-only，不依赖 torch）。

Plan B：放弃跨尺度原图配准，直接用服务商「处理图像」里**同一网格**的
组件体（sus/pore/feng，天然共配准）做「灰度→3 相」分割。本模块是底座：
  · 维度注册 + np.memmap 惰性读（不把 4GB 塞进内存）；
  · 两套路径布局：本机扁平拷贝(local) / Linux 原始嵌套(source)——同一套代码
    在 Mac 和 hy7-linux 上都能定位文件；
  · 用已核校总孔隙度**自动反推**相标记值（不写死）；
  · 合成 3 相标签 + 在线随机 patch 采样（训练直接吃完整体素，无需预烤数据集）。

路径来源（按优先级）：--root 参数 > 环境变量 HY7_VOL_ROOT > 本机默认 data/hy7_volumes。
布局：--layout 参数 > 环境变量 HY7_VOL_LAYOUT > "local"。

用法：
  .venv/bin/python src/hy7_planb_io.py inspect
  .venv/bin/python src/hy7_planb_io.py sample --scale ct14 --patch 64 --n 5
  # Linux 上指到原始数据，无需本机拷贝：
  HY7_VOL_ROOT=/home/user/HXL/HY7_source/吉林大学数据报告归总 HY7_VOL_LAYOUT=source \
    python src/hy7_planb_io.py inspect --key ct14_sus
"""
import os, sys, json, argparse
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LOCAL_ROOT = os.path.join(ROOT, "data", "hy7_volumes")

# ---- 体素注册表：dims=(nz,ny,nx)（reshape 顺序，z 为切片堆叠方向）-------
# 文件名「1620x1620x1600」按惯例 =(nx,ny,nz)，故 reshape 用 (nz,ny,nx)。
VOLUMES = {
    "ct14_sus":  {"dims": (1600, 1620, 1620), "role": "matrix/灰度", "scale": "ct14"},
    "ct14_pore": {"dims": (1600, 1620, 1620), "role": "pore-label", "scale": "ct14"},
    "ct14_feng": {"dims": (1600, 1620, 1620), "role": "fracture-label", "scale": "ct14"},
    "ct14_orig": {"dims": (2024, 2024, 2024), "role": "原始灰度(异网格)", "scale": "ct14"},
    "ct28_sus":  {"dims": (1500, 1500, 1500), "role": "matrix/灰度", "scale": "ct28"},
    "ct28_pore": {"dims": (1500, 1500, 1500), "role": "pore-label", "scale": "ct28"},
    "ct28_orig": {"dims": (2024, 2024, 2024), "role": "原始灰度(异网格)", "scale": "ct28"},
}

# 本机扁平拷贝布局（data/hy7_volumes/...）
LOCAL_PATHS = {
    "ct14_sus":  "ct14_14um/202510052_1620x1620x1600_8bit_14um_SUS.raw",
    "ct14_pore": "ct14_14um/202510052_1620x1620x1600_8bit_14um_pore.raw",
    "ct14_feng": "ct14_14um/202510052_1620x1620x1600_8bit_14um_FENG.raw",
    "ct14_orig": "ct14_14um/202510052_2024x2024x2024_8bit_14.raw",
    "ct28_sus":  "ct28_2p8um/202510052_5mm_1500c_8bit_2p8um_sus.raw",
    "ct28_pore": "ct28_2p8um/202510052_5mm_1500c_8bit_2p8um_pore.raw",
    "ct28_orig": "ct28_2p8um/202510052_5mm_2024x2024x2024_8bit_2p8.raw",
}
# Linux/外盘 原始嵌套布局（root=…/吉林大学数据报告归总）
SOURCE_PATHS = {
    "ct14_sus":  "微米CT柱塞扫描-14um/处理图像/202510052_1620x1620x1600_8bit_14um_SUS.raw",
    "ct14_pore": "微米CT柱塞扫描-14um/处理图像/202510052_1620x1620x1600_8bit_14um_pore.raw",
    "ct14_feng": "微米CT柱塞扫描-14um/处理图像/202510052_1620x1620x1600_8bit_14um_FENG.raw",
    "ct14_orig": "微米CT柱塞扫描-14um/202510052_2024x2024x2024_8bit_14.raw",
    "ct28_sus":  "微米CT精细扫描-2p8um/处理图像/202510052_5mm_1500c_8bit_2p8um_sus.raw",
    "ct28_pore": "微米CT精细扫描-2p8um/处理图像/202510052_5mm_1500c_8bit_2p8um_pore.raw",
    "ct28_orig": "微米CT精细扫描-2p8um/202510052_5mm_2024x2024x2024_8bit_2p8.raw",
}

# 每个尺度参与分割的组件体（frac 可缺）
SCALE_COMPONENTS = {
    "ct14": {"image": "ct14_sus", "pore": "ct14_pore", "frac": "ct14_feng"},
    "ct28": {"image": "ct28_sus", "pore": "ct28_pore"},
}

# 已核校总孔隙度（src/verify_hy7.py 复现）→ 反推相标记值
KNOWN_POROSITY_PCT = {"ct14": 1.558, "ct28": 7.182}
IGNORE = 255


def resolve_root(root=None):
    return root or os.environ.get("HY7_VOL_ROOT") or DEFAULT_LOCAL_ROOT


def resolve_layout(layout=None):
    return layout or os.environ.get("HY7_VOL_LAYOUT") or "local"


def vol_path(key, root=None, layout=None):
    root = resolve_root(root)
    table = SOURCE_PATHS if resolve_layout(layout) == "source" else LOCAL_PATHS
    return os.path.join(root, table[key])


def exists(key, root=None, layout=None):
    return os.path.isfile(vol_path(key, root, layout))


def open_memmap(key, mode="r", root=None, layout=None):
    """按注册维度打开 uint8 体素为 np.memmap (nz,ny,nx)，字节数核验。"""
    p = vol_path(key, root, layout)
    if not os.path.isfile(p):
        raise FileNotFoundError(f"{key}: 未找到 {p}")
    nz, ny, nx = VOLUMES[key]["dims"]
    expect, actual = nz * ny * nx, os.path.getsize(p)
    if actual != expect:
        raise ValueError(f"{key}: 字节数 {actual} ≠ {nz}x{ny}x{nx}={expect}（维度/ dtype 不符）")
    return np.memmap(p, dtype=np.uint8, mode=mode, shape=(nz, ny, nx))


def sample_zsel(nz, n=6):
    if nz <= 0 or n <= 0:
        raise ValueError(f"nz and n must be positive, got nz={nz}, n={n}")
    return np.linspace(nz * 0.15, nz * 0.85, n).astype(int)


def decode_phase_value(mm, target_pct, zsel):
    """取若干切片，找占比最接近已知孔隙度的取值 → 该相的标记值（不写死）。"""
    if len(zsel) == 0:
        raise ValueError("phase-value decoding requires at least one sampled z slice")
    sl = np.stack([np.asarray(mm[z]) for z in zsel])
    vals, counts = np.unique(sl, return_counts=True)
    frac = counts / counts.sum() * 100
    return int(vals[int(np.argmin(np.abs(frac - target_pct)))])


def build_label(img_c, pore_c, pore_val, frac_c=None, frac_val=None):
    """合成 3 相标签：0 基质 / 1 孔隙 / 2 裂缝 / 255 ignore（柱塞外，孔隙裂缝覆盖之）。"""
    if img_c.shape != pore_c.shape:
        raise ValueError(f"shape mismatch: image={img_c.shape}, pore={pore_c.shape}")
    if frac_c is not None and frac_c.shape != img_c.shape:
        raise ValueError(f"shape mismatch: image={img_c.shape}, fracture={frac_c.shape}")
    if frac_c is not None and frac_val is None:
        raise ValueError("fracture labels require a decoded fracture phase value")
    lbl = np.zeros(img_c.shape, np.uint8)
    lbl[img_c == 0] = IGNORE                 # 圆柱塞外方角(空气)→忽略
    lbl[pore_c == pore_val] = 1              # 真孔隙覆盖 ignore（即便暗）
    if frac_c is not None:
        lbl[frac_c == frac_val] = 2
    return lbl


def validate_patch_size(patch, dims):
    """Reject patches that cannot be sampled without crossing a registered volume boundary."""
    if int(patch) != patch or patch <= 0:
        raise ValueError(f"patch must be a positive integer, got {patch}")
    if len(dims) != 3 or min(dims) <= patch:
        raise ValueError(f"patch={patch} must be smaller than every source dimension {tuple(dims)}")
    return int(patch)


class ScaleVolumes:
    """打开某尺度 image/pore/frac，自动解码相值，提供在线随机 patch 采样。
    训练直接吃完整体素——无需预烤 .npz 数据集。"""

    def __init__(self, scale, root=None, layout=None, norm_samples=24, patch_for_norm=64, seed=0):
        comp = SCALE_COMPONENTS[scale]
        self.scale = scale
        self.img = open_memmap(comp["image"], root=root, layout=layout)
        self.pore = open_memmap(comp["pore"], root=root, layout=layout)
        self.frac = open_memmap(comp["frac"], root=root, layout=layout) if "frac" in comp else None
        self.dims = self.img.shape
        assert self.pore.shape == self.dims, f"维度不一致 {self.pore.shape} vs {self.dims}"
        if self.frac is not None:
            assert self.frac.shape == self.dims
        zsel = sample_zsel(self.dims[0])
        self.pore_val = decode_phase_value(self.pore, KNOWN_POROSITY_PCT[scale], zsel)
        self.frac_val = decode_phase_value(self.frac, 0.7, zsel) if self.frac is not None else None
        self.n_cls = 3 if self.frac is not None else 2
        self.mean, self.std = self._estimate_norm(norm_samples, patch_for_norm, seed)

    def _estimate_norm(self, k, P, seed):
        rng = np.random.default_rng(seed)
        vs = []
        for _ in range(k):
            ic, lbl = self._one(P, rng, min_fg=0.0, bg_keep=1.0)  # 任意位置即可
            vs.append(ic[lbl != IGNORE].astype(np.float64))
        v = np.concatenate(vs) if vs else np.array([0.0, 1.0])
        return float(v.mean()), float(v.std() + 1e-6)

    def _one(self, P, rng, min_fg, bg_keep):
        nz, ny, nx = self.dims
        P = validate_patch_size(P, self.dims)
        z = int(rng.integers(0, nz - P)); y = int(rng.integers(0, ny - P)); x = int(rng.integers(0, nx - P))
        ic = np.asarray(self.img[z:z+P, y:y+P, x:x+P]).copy()
        pc = np.asarray(self.pore[z:z+P, y:y+P, x:x+P])
        fc = np.asarray(self.frac[z:z+P, y:y+P, x:x+P]) if self.frac is not None else None
        lbl = build_label(ic, pc, self.pore_val, fc, self.frac_val)
        return ic, lbl

    def sample(self, P, rng, min_fg=0.005, bg_keep=0.15, max_tries=80, require_frac=False):
        """采一个 patch：要求有效区(非ignore)>50%，并按前景占比筛（类平衡保留少量背景）。
        require_frac=True 时只返回含裂缝(class 2)的 patch（裂缝过采样，兜底返回最近有效 patch）。"""
        last = None
        for _ in range(max_tries):
            ic, lbl = self._one(P, rng, min_fg, bg_keep)
            if (lbl != IGNORE).mean() < 0.5:
                continue
            last = (ic, lbl)
            if require_frac and not (lbl == 2).any():
                continue
            fg = ((lbl == 1) | (lbl == 2)).mean()
            if not require_frac and fg < min_fg and rng.random() > bg_keep:
                continue
            return ic, lbl
        return last if last is not None else (ic, lbl)  # 兜底


# ----------------------------- CLI -----------------------------------------
def inspect_one(key, root, layout):
    meta = VOLUMES[key]
    out = {"key": key, "role": meta["role"], "dims_zyx": meta["dims"], "scale": meta["scale"],
           "path": vol_path(key, root, layout)}
    if not exists(key, root, layout):
        out["status"] = "MISSING"; return out
    mm = open_memmap(key, root=root, layout=layout)
    zsel = sample_zsel(mm.shape[0], 7)
    sl = np.stack([np.asarray(mm[z]) for z in zsel])
    vals, counts = np.unique(sl, return_counts=True)
    frac = counts / counts.sum()
    order = np.argsort(-counts)[:6]
    out.update(status="ok", n_unique_vals=int(vals.size), is_binary_like=bool(vals.size <= 4),
               top_values=[{"val": int(vals[i]), "frac_pct": round(float(frac[i]) * 100, 4)} for i in order])
    if "label" in meta["role"]:
        tgt = KNOWN_POROSITY_PCT.get(meta["scale"])
        out["phase_value_guess"] = int(vals[int(np.argmin(np.abs(frac * 100 - tgt)))])
        out["known_porosity_pct"] = tgt
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["inspect", "ls", "sample"], nargs="?", default="inspect")
    ap.add_argument("--key", default=None)
    ap.add_argument("--scale", default="ct14", choices=list(SCALE_COMPONENTS))
    ap.add_argument("--patch", type=int, default=64)
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--root", default=None); ap.add_argument("--layout", default=None,
                                                             choices=["local", "source"])
    a = ap.parse_args()

    if a.cmd == "ls":
        for k in VOLUMES:
            ok = "OK " if exists(k, a.root, a.layout) else "-- "
            print(f"{ok}{k:11s} {VOLUMES[k]['dims']}  {VOLUMES[k]['role']}")
        return
    if a.cmd == "sample":
        sv = ScaleVolumes(a.scale, root=a.root, layout=a.layout)
        rng = np.random.default_rng(0)
        print(f"[i] scale={a.scale} dims={sv.dims} n_cls={sv.n_cls} "
              f"pore_val={sv.pore_val} frac_val={sv.frac_val} norm=({sv.mean:.1f},{sv.std:.1f})")
        for i in range(a.n):
            ic, lbl = sv.sample(a.patch, rng)
            fg = round(float(((lbl == 1) | (lbl == 2)).mean()) * 100, 3)
            uniq = {int(v): int(c) for v, c in zip(*np.unique(lbl, return_counts=True))}
            print(f"  patch {i}: shape={ic.shape} fg%={fg} label_hist={uniq}")
        return

    keys = [a.key] if a.key else list(VOLUMES)
    report = [inspect_one(k, a.root, a.layout) for k in keys]
    print(json.dumps(report, ensure_ascii=False, indent=2))
    miss = [r["key"] for r in report if r.get("status") == "MISSING"]
    if miss:
        print(f"\n[i] 仍缺 {len(miss)} 个体：{miss}", file=sys.stderr)


if __name__ == "__main__":
    main()
