#!/usr/bin/env python
"""M7.3 阶段二：DDPM 生成孔隙结构的参数评估（生成 vs 真实测试集）。

依据精读卡②(Mosser2017)：用孔隙度 φ、两点相关 S₂(r)、Euler 特征 χ（连通性）
比较生成样本与真实样本的统计分布——"参数评估而非只看图"。

S₂(r)=P(x∈孔, x+r∈孔)，S₂(0)=φ、r→∞→φ²；本处用 FFT 自相关估计并径向平均。
χ（2D）=连通块数−孔洞数（skimage.euler_number），刻画拓扑连通性。
输出：metrics.json + fig_eval.png（孔隙度/φ、S₂(r)、Euler 三联图）。
"""
import argparse, json, os
import numpy as np


def porosity(stack):
    return stack.reshape(len(stack), -1).mean(1)


def s2_radial(stack, rmax):
    """对每张二值图用 FFT 自相关算 S₂(r) 再径向平均，最后跨样本平均。"""
    N = stack.shape[0]
    H, W = stack.shape[1:]
    # 预备径向 bin
    yy, xx = np.mgrid[0:H, 0:W]
    cy, cx = 0, 0
    # 用以 0 为中心的位移（FFT 自相关的 lag 在 (0,0)），取前 rmax 半径
    rr = np.sqrt(np.minimum(yy, H - yy) ** 2 + np.minimum(xx, W - xx) ** 2)
    rbin = rr.astype(int)
    acc = np.zeros(rmax + 1); cnt = np.zeros(rmax + 1)
    s2_mean = np.zeros(rmax + 1)
    for i in range(N):
        f = np.fft.fft2(stack[i].astype(np.float64))
        ac = np.fft.ifft2(f * np.conj(f)).real / (H * W)   # 自相关，lag(0,0)=mean(I^2)=φ
        a = np.zeros(rmax + 1); c = np.zeros(rmax + 1)
        m = rbin <= rmax
        np.add.at(a, rbin[m], ac[m]); np.add.at(c, rbin[m], 1)
        s2_mean += a / np.maximum(c, 1)
    return s2_mean / N


def euler_numbers(stack):
    from skimage.measure import euler_number
    return np.array([euler_number(stack[i].astype(bool), connectivity=1) for i in range(len(stack))])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", required=True, help="真实测试集 test.npy")
    ap.add_argument("--gen", required=True, help="生成 samples.npy")
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=512, help="各取 N 张参与统计(控时)")
    ap.add_argument("--rmax", type=int, default=48)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    from scipy.stats import ks_2samp, wasserstein_distance
    rng = np.random.default_rng(a.seed)

    real = np.load(a.real); gen = np.load(a.gen)
    def take(s):
        idx = rng.choice(len(s), min(a.n, len(s)), replace=False); return s[idx]
    real, gen = take(real), take(gen)
    os.makedirs(a.out, exist_ok=True)

    pr, pg = porosity(real) * 100, porosity(gen) * 100
    s2r, s2g = s2_radial(real, a.rmax), s2_radial(gen, a.rmax)
    er, eg = euler_numbers(real), euler_numbers(gen)

    ks_por = ks_2samp(pr, pg); w_por = wasserstein_distance(pr, pg)
    ks_eul = ks_2samp(er, eg); w_eul = wasserstein_distance(er, eg)
    s2_rmse = float(np.sqrt(np.mean((s2r - s2g) ** 2)))

    metrics = {
        "n_real": len(real), "n_gen": len(gen),
        "porosity_pct": {"real_mean": round(float(pr.mean()), 3), "gen_mean": round(float(pg.mean()), 3),
                         "real_median": round(float(np.median(pr)), 3), "gen_median": round(float(np.median(pg)), 3),
                         "KS_stat": round(float(ks_por.statistic), 4), "KS_p": round(float(ks_por.pvalue), 4),
                         "wasserstein": round(float(w_por), 4)},
        "euler_chi": {"real_mean": round(float(er.mean()), 2), "gen_mean": round(float(eg.mean()), 2),
                      "KS_stat": round(float(ks_eul.statistic), 4), "wasserstein": round(float(w_eul), 3)},
        "S2_radial": {"phi_at_0_real": round(float(s2r[0]), 4), "phi_at_0_gen": round(float(s2g[0]), 4),
                      "rmse_over_r": round(s2_rmse, 5)},
    }
    json.dump(metrics, open(os.path.join(a.out, "metrics.json"), "w"), ensure_ascii=False, indent=2)

    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(14, 4))
    ax[0].hist(pr, bins=30, alpha=0.6, label="real", color="#4f81bd", density=True)
    ax[0].hist(pg, bins=30, alpha=0.6, label="gen", color="#c0504d", density=True)
    ax[0].set_title(f"Porosity % (KS p={ks_por.pvalue:.3f})"); ax[0].set_xlabel("porosity %"); ax[0].legend()
    r = np.arange(a.rmax + 1)
    ax[1].plot(r, s2r, label="real", color="#4f81bd"); ax[1].plot(r, s2g, label="gen", color="#c0504d")
    ax[1].axhline((pr.mean()/100)**2, ls=":", c="gray", lw=1, label="phi^2")
    ax[1].set_title("Two-point S2(r)  rmse=%.4f" % s2_rmse); ax[1].set_xlabel("r (px, 1px=2.8um)"); ax[1].legend()
    ax[2].hist(er, bins=30, alpha=0.6, label="real", color="#4f81bd", density=True)
    ax[2].hist(eg, bins=30, alpha=0.6, label="gen", color="#c0504d", density=True)
    ax[2].set_title("Euler char chi (connectivity)"); ax[2].set_xlabel("chi per tile"); ax[2].legend()
    plt.tight_layout(); plt.savefig(os.path.join(a.out, "fig_eval.png"), dpi=120); plt.close()
    print("[done] porosity real=%.2f%% gen=%.2f%% | S2 rmse=%.4f | Euler real=%.1f gen=%.1f"
          % (pr.mean(), pg.mean(), s2_rmse, er.mean(), eg.mean()))
    print("[done] ->", a.out)


if __name__ == "__main__":
    main()
