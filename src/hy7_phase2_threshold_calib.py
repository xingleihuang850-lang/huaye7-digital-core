#!/usr/bin/env python
"""M7-v2 阶段二：DDPM 连续输出阈值标定诊断。

目的：把 T=0 二值化换成 T* 阈值（标定到真实孔隙度），分离
    "二值化伪影(可修)" vs "结构真错(需训练)"。

依据（notes/21_阶段二_M7_DDPM_MVP结果.md §3）：
    首疑 = 连续输出在矩阵相(-1)附近有噪声，阈值取 0 时尾巴越过 0 → 散点假孔。
    验证法：重采样保存连续值 → 阈值标定到真实孔隙度 → 看 S₂(r)/Euler 是否对齐。

输入：
    --real      真实测试集 test.npy  (N,H,W) uint8
    --cont      连续输出  samples_continuous.npy  (M,H,W) float32
    --target_phi 真实孔隙度目标（默认 6.4，来自 M7 首基线 meta.json）

输出（--out 目录）：
    calib_result.json   标定阈值 + 两套指标对比
    fig_calib.png       孔隙度分布/S₂(r)/Euler 三联图（T=0 vs T* vs real）
"""
import argparse
import json
import os
import sys

import numpy as np


# ─── 统计工具 ─────────────────────────────────────────────────────────────────

def porosity(stack):
    return stack.reshape(len(stack), -1).mean(1)


def s2_radial(stack, rmax):
    N, H, W = stack.shape
    yy, xx = np.mgrid[0:H, 0:W]
    rr = np.sqrt(np.minimum(yy, H - yy) ** 2 + np.minimum(xx, W - xx) ** 2)
    rbin = rr.astype(int)
    s2_mean = np.zeros(rmax + 1)
    for i in range(N):
        f = np.fft.fft2(stack[i].astype(np.float64))
        ac = np.fft.ifft2(f * np.conj(f)).real / (H * W)
        a = np.zeros(rmax + 1); c = np.zeros(rmax + 1)
        m = rbin <= rmax
        np.add.at(a, rbin[m], ac[m]); np.add.at(c, rbin[m], 1)
        s2_mean += a / np.maximum(c, 1)
    return s2_mean / N


def euler_numbers(stack):
    from skimage.measure import euler_number
    return np.array([euler_number(stack[i].astype(bool), connectivity=1)
                     for i in range(len(stack))])


def eval_set(binary, rmax):
    phi = porosity(binary) * 100
    s2 = s2_radial(binary, rmax)
    euler = euler_numbers(binary)
    return phi, s2, euler


# ─── 阈值标定 ─────────────────────────────────────────────────────────────────

def calibrate_threshold(continuous, target_phi_pct, n_sweep=400):
    """在连续值输出上二分搜索阈值，使平均孔隙度 ≈ target_phi_pct。"""
    lo, hi = float(continuous.min()), float(continuous.max())
    for _ in range(50):   # 二分 50 次精度 ≈ (hi-lo)/2^50 ≈ 机器精度
        mid = (lo + hi) / 2
        phi = (continuous > mid).reshape(len(continuous), -1).mean() * 100
        if phi > target_phi_pct:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ─── 主流程 ───────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="M7-v2 阈值标定诊断")
    ap.add_argument("--real", required=True, help="真实测试集 test.npy (uint8)")
    ap.add_argument("--cont", required=True, help="连续采样 samples_continuous.npy (float32)")
    ap.add_argument("--out", required=True, help="输出目录")
    ap.add_argument("--target_phi", type=float, default=6.4,
                    help="真实孔隙度目标 %%（默认 6.4，来自 M7 meta.json test phi mean）")
    ap.add_argument("--n", type=int, default=512, help="各取前 N 张")
    ap.add_argument("--rmax", type=int, default=48)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    from scipy.stats import ks_2samp, wasserstein_distance
    rng = np.random.default_rng(a.seed)
    os.makedirs(a.out, exist_ok=True)

    real = np.load(a.real)
    cont = np.load(a.cont)
    def take(s): return s[rng.choice(len(s), min(a.n, len(s)), replace=False)]
    real = take(real)
    cont = take(cont)

    # T=0 二值化（M7 首基线）
    bin_t0 = (cont > 0).astype(np.uint8)

    # T* 标定到目标孔隙度
    T_star = calibrate_threshold(cont, a.target_phi)
    bin_tstar = (cont > T_star).astype(np.uint8)
    print(f"[calib] T*={T_star:.4f}  (target φ={a.target_phi:.2f}%)")

    # 评估三组
    phi_real, s2_real, euler_real = eval_set(real, a.rmax)
    phi_t0,   s2_t0,   euler_t0   = eval_set(bin_t0, a.rmax)
    phi_ts,   s2_ts,   euler_ts   = eval_set(bin_tstar, a.rmax)

    def stats(phi, euler, s2, ref_phi, ref_euler, ref_s2):
        return {
            "phi_mean": round(float(phi.mean()), 3),
            "phi_median": round(float(np.median(phi)), 3),
            "phi_KS_p": round(float(ks_2samp(phi, ref_phi).pvalue), 4),
            "phi_wasserstein": round(float(wasserstein_distance(phi, ref_phi)), 4),
            "euler_mean": round(float(euler.mean()), 2),
            "euler_wasserstein": round(float(wasserstein_distance(euler, ref_euler)), 3),
            "S2_rmse": round(float(np.sqrt(np.mean((s2 - ref_s2) ** 2))), 5),
        }

    result = {
        "command": " ".join(sys.argv),
        "T_star": round(T_star, 5),
        "target_phi_pct": a.target_phi,
        "n": int(min(a.n, len(cont))),
        "real":  {"phi_mean": round(float(phi_real.mean()), 3),
                  "euler_mean": round(float(euler_real.mean()), 2),
                  "S2_at0": round(float(s2_real[0]), 4)},
        "T0":    stats(phi_t0,  euler_t0,  s2_t0,  phi_real, euler_real, s2_real),
        "Tstar": stats(phi_ts,  euler_ts,  s2_ts,  phi_real, euler_real, s2_real),
        "verdict": None,   # 填写后
    }

    # 判读：φ 对齐后 S₂/Euler 分别改善多少。S₂ 改善只能说明阈值伪影被修复；
    # 若 Euler 同时变差，必须保留“连通性真错”的结论，不能写成 S₂/Euler 都改善。
    s2_improve = result["T0"]["S2_rmse"] - result["Tstar"]["S2_rmse"]
    euler_improve = abs(result["T0"]["euler_wasserstein"]) - abs(result["Tstar"]["euler_wasserstein"])
    if s2_improve > 0.001 and euler_improve <= -1:
        verdict = "阈值伪影已修但连通性真错仍在：S₂ 明显改善，Euler 变差 → 下一步修聚集/连通性"
    elif s2_improve > 0.001 and euler_improve > 1:
        verdict = "阈值伪影为主：标定后 S₂ 与 Euler 同时改善 → 先采用 T* 口径再评估残差"
    elif s2_improve > 0.001:
        verdict = "阈值伪影已修：S₂ 明显改善；Euler 改善有限 → 继续检查连通性"
    else:
        verdict = "结构真错为主：标定后改善有限 → 需加 epoch / 改表征 / 换损失"
    result["verdict"] = verdict
    print(f"[verdict] {verdict}")

    json.dump(result, open(os.path.join(a.out, "calib_result.json"), "w"),
              ensure_ascii=False, indent=2)

    # 图
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    r = np.arange(a.rmax + 1)
    fig, ax = plt.subplots(1, 3, figsize=(15, 4))

    for phi, lbl, c in [(phi_real, "real", "#4f81bd"), (phi_t0, "gen T=0", "#c0504d"),
                        (phi_ts, f"gen T*={T_star:.3f}", "#9bbb59")]:
        ax[0].hist(phi, bins=30, alpha=0.5, label=lbl, color=c, density=True)
    ax[0].set_title("Porosity %"); ax[0].set_xlabel("φ %"); ax[0].legend(fontsize=8)

    for s2, lbl, c in [(s2_real, "real", "#4f81bd"), (s2_t0, "gen T=0", "#c0504d"),
                       (s2_ts, f"gen T*", "#9bbb59")]:
        ax[1].plot(r, s2, label=lbl, color=c)
    ax[1].set_title(f"S₂(r)  T0 rmse={result['T0']['S2_rmse']:.4f}  T* rmse={result['Tstar']['S2_rmse']:.4f}")
    ax[1].set_xlabel("r (px)"); ax[1].legend(fontsize=8)

    for euler, lbl, c in [(euler_real, "real", "#4f81bd"), (euler_t0, "gen T=0", "#c0504d"),
                          (euler_ts, "gen T*", "#9bbb59")]:
        ax[2].hist(euler, bins=30, alpha=0.5, label=lbl, color=c, density=True)
    ax[2].set_title("Euler χ (connectivity)"); ax[2].set_xlabel("χ per tile"); ax[2].legend(fontsize=8)

    plt.suptitle(f"M7-v2 Threshold Calibration  T*={T_star:.4f}", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(a.out, "fig_calib.png"), dpi=120)
    plt.close()

    print(f"""
[summary]
  real   φ={phi_real.mean():.2f}%  Euler={euler_real.mean():.1f}
  T=0    φ={phi_t0.mean():.2f}%   Euler={euler_t0.mean():.1f}  S2 rmse={result['T0']['S2_rmse']:.4f}
  T*     φ={phi_ts.mean():.2f}%   Euler={euler_ts.mean():.1f}  S2 rmse={result['Tstar']['S2_rmse']:.4f}
  → {a.out}/calib_result.json  fig_calib.png
""")


if __name__ == "__main__":
    main()
