#!/usr/bin/env python
"""M7.3 阶段二：DDPM 生成孔隙结构的参数评估（生成 vs 真实测试集 vs naive baseline）。

依据精读卡②(Mosser2017)：用孔隙度 φ、两点相关 S₂(r)、Euler 特征 χ（连通性）
比较生成样本与真实样本的统计分布——"参数评估而非只看图"。

S₂(r)=P(x∈孔, x+r∈孔)，S₂(0)=φ、r→∞→φ²；本处用 FFT 自相关估计并径向平均。
χ（2D）=连通块数−孔洞数（skimage.euler_number），刻画拓扑连通性。

新增（codex建议）：
  max_cc_frac    最大连通簇占总孔像素的比例 → 连通程度量化
  x/y_penetrate  x/y 方向贯通率（贯通 tile 数/总 tile 数）→ 渗流通道是否存在
  naive_baseline 随机撒点（按均值孔隙度 Bernoulli）→ 判断 DDPM 是否超出零信息量

输出：metrics.json + fig_eval.png（4 联图：孔隙度/S₂/Euler/连通簇）
"""
import argparse, json, os, sys
import numpy as np


# ─── 统计函数 ─────────────────────────────────────────────────────────────────

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


def connectivity_stats(stack):
    """最大连通簇占比 + x/y 方向贯通率。

    max_cc_frac: 每张 tile 里最大连通簇像素数 / 总孔隙像素数（无孔→NaN→排除）。
    x_penetrate: 最大连通簇同时接触左/右边界的 tile 比例（x 方向贯通）。
    y_penetrate: 最大连通簇同时接触上/下边界的 tile 比例（y 方向贯通）。
    """
    from skimage.measure import label
    frac, xpen, ypen = [], [], []
    for img in stack:
        lbl = label(img.astype(bool), connectivity=1)
        if lbl.max() == 0:      # 无孔隙
            frac.append(np.nan); xpen.append(0.0); ypen.append(0.0)
            continue
        sizes = np.bincount(lbl.ravel())
        sizes[0] = 0            # 背景
        largest = np.argmax(sizes)
        cc = (lbl == largest)
        total_pore = img.sum()
        frac.append(cc.sum() / max(total_pore, 1))
        # 贯通判断：最大簇是否接触两侧边界
        xpen.append(float(cc[:, 0].any() and cc[:, -1].any()))
        ypen.append(float(cc[0, :].any() and cc[-1, :].any()))
    frac = np.array(frac)
    return (float(np.nanmean(frac)),
            float(np.nanstd(frac)),
            float(np.mean(xpen)),
            float(np.mean(ypen)))


def naive_baseline(stack, seed=42):
    """Naive baseline：按每张 tile 真实孔隙度独立 Bernoulli 随机撒点。
    输出与 stack 同形状，保留逐 tile 孔隙度均值但无空间结构。
    """
    rng = np.random.default_rng(seed)
    phi = stack.reshape(len(stack), -1).mean(1)   # 各 tile 孔隙度
    H, W = stack.shape[1:]
    result = np.stack(
        [(rng.random((H, W)) < p).astype(np.uint8) for p in phi]
    )
    return result


# ─── 主流程 ───────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", required=True, help="real test.npy")
    ap.add_argument("--gen",  required=True, help="generated samples.npy")
    ap.add_argument("--out",  required=True)
    ap.add_argument("--n",    type=int, default=512)
    ap.add_argument("--rmax", type=int, default=48)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    from scipy.stats import ks_2samp, wasserstein_distance
    rng = np.random.default_rng(a.seed)

    real = np.load(a.real); gen = np.load(a.gen)
    def take(s):
        idx = rng.choice(len(s), min(a.n, len(s)), replace=False); return s[idx]
    real, gen = take(real), take(gen)
    naive = naive_baseline(real, seed=a.seed + 1)   # same phi distribution, no structure
    os.makedirs(a.out, exist_ok=True)

    # ── 基础指标 ──
    pr, pg, pn = porosity(real)*100, porosity(gen)*100, porosity(naive)*100
    s2r, s2g, s2n = s2_radial(real, a.rmax), s2_radial(gen, a.rmax), s2_radial(naive, a.rmax)
    er, eg, en = euler_numbers(real), euler_numbers(gen), euler_numbers(naive)

    ks_por = ks_2samp(pr, pg); w_por = wasserstein_distance(pr, pg)
    ks_eul = ks_2samp(er, eg); w_eul = wasserstein_distance(er, eg)
    s2_rmse = float(np.sqrt(np.mean((s2r - s2g)**2)))
    s2_rmse_naive = float(np.sqrt(np.mean((s2r - s2n)**2)))

    # ── 连通性指标 ──
    cc_frac_r, cc_std_r, xp_r, yp_r = connectivity_stats(real)
    cc_frac_g, cc_std_g, xp_g, yp_g = connectivity_stats(gen)
    cc_frac_n, cc_std_n, xp_n, yp_n = connectivity_stats(naive)

    metrics = {
        "command": " ".join(sys.argv),
        "n_real": len(real), "n_gen": len(gen),
        "porosity_pct": {
            "real_mean":   round(float(pr.mean()), 3),
            "gen_mean":    round(float(pg.mean()), 3),
            "naive_mean":  round(float(pn.mean()), 3),
            "KS_stat":     round(float(ks_por.statistic), 4),
            "KS_p":        round(float(ks_por.pvalue), 4),
            "wasserstein": round(float(w_por), 4),
        },
        "euler_chi": {
            "real_mean":   round(float(er.mean()), 2),
            "gen_mean":    round(float(eg.mean()), 2),
            "naive_mean":  round(float(en.mean()), 2),
            "KS_stat":     round(float(ks_eul.statistic), 4),
            "wasserstein": round(float(w_eul), 3),
        },
        "S2_radial": {
            "phi_at_0_real": round(float(s2r[0]), 4),
            "phi_at_0_gen":  round(float(s2g[0]), 4),
            "rmse_gen":      round(s2_rmse, 5),
            "rmse_naive":    round(s2_rmse_naive, 5),
        },
        "connectivity": {
            "max_cc_frac_real":  round(cc_frac_r, 4),
            "max_cc_frac_gen":   round(cc_frac_g, 4),
            "max_cc_frac_naive": round(cc_frac_n, 4),
            "x_penetrate_real":  round(xp_r, 4),
            "x_penetrate_gen":   round(xp_g, 4),
            "x_penetrate_naive": round(xp_n, 4),
            "y_penetrate_real":  round(yp_r, 4),
            "y_penetrate_gen":   round(yp_g, 4),
            "y_penetrate_naive": round(yp_n, 4),
        },
    }
    json.dump(metrics, open(os.path.join(a.out, "metrics.json"), "w"),
              ensure_ascii=False, indent=2)

    # ── 图（英文标签，避免 Linux 缺中文字体） ──
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 4, figsize=(18, 4))

    # 孔隙度
    for phi, lbl, c in [(pr, "real", "#4f81bd"), (pg, "gen", "#c0504d"), (pn, "naive", "#9bbb59")]:
        ax[0].hist(phi, bins=30, alpha=0.5, label=lbl, color=c, density=True)
    ax[0].set_title(f"Porosity % (KS p={ks_por.pvalue:.3f})")
    ax[0].set_xlabel("porosity %"); ax[0].legend(fontsize=8)

    # S₂(r)
    r = np.arange(a.rmax + 1)
    for s2, lbl, c in [(s2r, "real", "#4f81bd"), (s2g, f"gen(rmse={s2_rmse:.4f})", "#c0504d"),
                       (s2n, f"naive(rmse={s2_rmse_naive:.4f})", "#9bbb59")]:
        ax[1].plot(r, s2, label=lbl, color=c)
    ax[1].set_title("Two-point S₂(r)"); ax[1].set_xlabel("r (px, 1px=2.8um)"); ax[1].legend(fontsize=7)

    # Euler
    for eul, lbl, c in [(er, "real", "#4f81bd"), (eg, "gen", "#c0504d"), (en, "naive", "#9bbb59")]:
        ax[2].hist(eul, bins=30, alpha=0.5, label=lbl, color=c, density=True)
    ax[2].set_title("Euler chi (topology)"); ax[2].set_xlabel("chi per tile"); ax[2].legend(fontsize=8)

    # 连通性 bar
    cats = ["real", "gen", "naive"]
    vals_cc  = [cc_frac_r, cc_frac_g, cc_frac_n]
    vals_xp  = [xp_r, xp_g, xp_n]
    vals_yp  = [yp_r, yp_g, yp_n]
    x = np.arange(3); w = 0.25
    ax[3].bar(x - w, vals_cc, w, label="max CC frac", color="#4f81bd", alpha=0.8)
    ax[3].bar(x,     vals_xp, w, label="x-penetrate", color="#c0504d", alpha=0.8)
    ax[3].bar(x + w, vals_yp, w, label="y-penetrate", color="#9bbb59", alpha=0.8)
    ax[3].set_xticks(x); ax[3].set_xticklabels(cats)
    ax[3].set_title("Connectivity metrics"); ax[3].set_ylim(0, 1.05); ax[3].legend(fontsize=7)

    plt.tight_layout()
    plt.savefig(os.path.join(a.out, "fig_eval.png"), dpi=120)
    plt.close()

    print(
        f"[done] porosity real={pr.mean():.2f}% gen={pg.mean():.2f}% naive={pn.mean():.2f}%\n"
        f"       S2 rmse gen={s2_rmse:.4f} naive={s2_rmse_naive:.4f}\n"
        f"       Euler real={er.mean():.1f} gen={eg.mean():.1f} naive={en.mean():.1f}\n"
        f"       max-CC-frac real={cc_frac_r:.3f} gen={cc_frac_g:.3f} naive={cc_frac_n:.3f}\n"
        f"       x-penetrate real={xp_r:.3f} gen={xp_g:.3f} naive={xp_n:.3f}\n"
        f"       -> {a.out}/metrics.json  fig_eval.png"
    )


if __name__ == "__main__":
    main()
