#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
出图：从 DuckDB 读数据，生成数字井筒分析图，存 experiments/figures/。
用法： .venv/bin/python src/make_figures.py
"""
import os
import duckdb
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import hy7_mpl_cjk  # 统一中文字体(两机通用)，取代手写 font.sans-serif
from matplotlib import font_manager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "warehouse.db")
FIG = os.path.join(ROOT, "experiments", "figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams["figure.dpi"] = 130

SEG_BOUNDS = [3439.13, 3439.89, 3440.79, 3441.70, 3442.64, 3443.52]
con = duckdb.connect(DB, read_only=True)
cur = con.execute("SELECT * FROM curves ORDER BY rowid").df()
# rowid 不存在则按读出顺序
cur = con.execute("SELECT * FROM curves").df()

C = {  # key -> (中文, 颜色)
    "matrix_porosity": ("基质孔隙度", "#1f77b4"),
    "total_porosity":  ("总孔隙度",   "#2ca02c"),
    "fracture_porosity":("裂缝孔隙度","#d62728"),
    "total_vug_frac":  ("总孔洞缝率", "#17becf"),
    "vug_fill_rate":   ("孔洞缝充填率","#9467bd"),
    "oil_content":     ("含油率",     "#ff7f0e"),
    "oil_saturation":  ("含油饱和度", "#8c564b"),
    "shale_content":   ("泥质含量",   "#7f7f7f"),
    "diagenetic_min":  ("成岩矿物含量","#bcbd22"),
}


def smooth(y, w=200):
    if len(y) < w: return y
    k = np.ones(w) / w
    return np.convolve(y, k, mode="same")


# ---------- 图1：综合测井道（多道并列，深度为纵轴） ----------
def fig_tracks():
    tracks = ["matrix_porosity","total_porosity","fracture_porosity",
              "oil_content","oil_saturation","shale_content"]
    fig, axes = plt.subplots(1, len(tracks), figsize=(13, 9), sharey=True)
    d = cur["depth_m"].values
    for ax, key in zip(axes, tracks):
        zh, col = C[key]
        v = cur[key].values
        ax.plot(v, d, lw=0.4, color=col, alpha=0.45)
        ax.plot(smooth(v), d, lw=1.8, color=col)
        ax.set_title(zh, fontsize=11)
        ax.grid(alpha=0.3)
        ax.set_xlabel("%")
        for b in SEG_BOUNDS:
            ax.axhline(b, color="0.6", lw=0.6, ls="--")
    axes[0].set_ylabel("深度 (m)")
    axes[0].invert_yaxis()
    fig.suptitle("GJ5-15 数字井筒综合测井道（CT 反演连续曲线，3439.13–3443.52 m）",
                 fontsize=14, y=0.98)
    fig.tight_layout(rect=[0,0,1,0.96])
    p = os.path.join(FIG, "01_well_tracks.png"); fig.savefig(p, bbox_inches="tight"); plt.close(fig)
    return p


# ---------- 图2：分段均值柱状（关键 6 属性） ----------
def fig_segment_bars():
    seg = con.execute("SELECT * FROM segment_stats").df()
    keys = ["matrix_porosity","oil_content","oil_saturation","shale_content","fracture_porosity","vug_fill_rate"]
    labels = ["3439.13-\n3439.89","3439.89-\n3440.79","3440.79-\n3441.70","3441.70-\n3442.64","3442.64-\n3443.52"]
    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    for ax, key in zip(axes.flat, keys):
        zh, col = C[key]
        sub = seg[seg["property"] == key].set_index("segment_label")
        order = ["3439.13-3439.89","3439.89-3440.79","3440.79-3441.70","3441.70-3442.64","3442.64-3443.52"]
        sub = sub.reindex(order)
        vals = [sub.loc[o, "mean"] for o in order]
        ax.bar(range(5), vals, color=col, alpha=0.85)
        ax.set_xticks(range(5)); ax.set_xticklabels(labels, fontsize=7.5)
        ax.set_title(f"{zh}（分段均值 %）", fontsize=11)
        ax.grid(axis="y", alpha=0.3)
        for i, val in enumerate(vals):
            ax.text(i, val, f"{val:.2f}", ha="center", va="bottom", fontsize=8)
    fig.suptitle("GJ5-15 各深度段关键参数均值对比", fontsize=14)
    fig.tight_layout(rect=[0,0,1,0.96])
    p = os.path.join(FIG, "02_segment_bars.png"); fig.savefig(p, bbox_inches="tight"); plt.close(fig)
    return p


# ---------- 图3：孔隙等效直径分布（数量占比 vs 体积占比） ----------
def fig_pore():
    pore = con.execute("SELECT * FROM pore_diameter").df()
    x = np.arange(len(pore)); w = 0.38
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x - w/2, pore["count_fraction"]*100, w, label="按数量占比", color="#1f77b4")
    ax.bar(x + w/2, pore["volume_fraction"]*100, w, label="按体积贡献", color="#ff7f0e")
    ax.set_xticks(x); ax.set_xticklabels(pore["diameter_um"])
    ax.set_xlabel("孔隙等效直径 (μm)"); ax.set_ylabel("占比 (%)")
    ax.set_title("GJ5-15 孔隙等效直径分布：数量 vs 体积贡献", fontsize=13)
    ax.legend(); ax.grid(axis="y", alpha=0.3)
    for i in range(len(pore)):
        ax.text(i-w/2, pore["count_fraction"].iloc[i]*100, f"{pore['count_fraction'].iloc[i]*100:.1f}",
                ha="center", va="bottom", fontsize=8)
        ax.text(i+w/2, pore["volume_fraction"].iloc[i]*100, f"{pore['volume_fraction'].iloc[i]*100:.1f}",
                ha="center", va="bottom", fontsize=8)
    fig.tight_layout()
    p = os.path.join(FIG, "03_pore_diameter.png"); fig.savefig(p, bbox_inches="tight"); plt.close(fig)
    return p


# ---------- 图4：相关性热图 ----------
def fig_corr():
    keys = list(C.keys())
    df = cur[keys]
    corr = df.corr().values
    zh = [C[k][0] for k in keys]
    fig, ax = plt.subplots(figsize=(8.5, 7))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(keys))); ax.set_xticklabels(zh, rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(len(keys))); ax.set_yticklabels(zh, fontsize=9)
    for i in range(len(keys)):
        for j in range(len(keys)):
            ax.text(j, i, f"{corr[i,j]:.2f}", ha="center", va="center",
                    fontsize=7.5, color="black" if abs(corr[i,j])<0.6 else "white")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title("GJ5-15 属性相关性矩阵（逐层 Pearson）", fontsize=13)
    fig.tight_layout()
    p = os.path.join(FIG, "04_correlation.png"); fig.savefig(p, bbox_inches="tight"); plt.close(fig)
    return p


# ---------- 图5：渗透率分段剖面 ----------
def fig_perm():
    perm = con.execute("SELECT * FROM permeability").df()
    mid = (perm["top"] + perm["bottom"]) / 2
    fig, ax = plt.subplots(1, 2, figsize=(9, 7), sharey=True)
    for key, col, lab in [("kh_mD","#1f77b4","水平 Kh"), ("kv_mD","#d62728","垂直 Kv")]:
        # 阶梯填充
        for _, r in perm.iterrows():
            ax[0].plot([r[key], r[key]], [r["top"], r["bottom"]], color=col, lw=2.5)
        ax[0].plot(perm[key], mid, "o", color=col, label=lab)
    ax[0].set_xlabel("渗透率 (mD)"); ax[0].set_ylabel("深度 (m)")
    ax[0].legend(); ax[0].grid(alpha=0.3); ax[0].set_title("水平/垂直渗透率")
    for _, r in perm.iterrows():
        ax[1].plot([r["kh_kv_ratio"]]*2, [r["top"], r["bottom"]], color="#2ca02c", lw=2.5)
    ax[1].plot(perm["kh_kv_ratio"], mid, "o", color="#2ca02c")
    ax[1].set_xlabel("Kh/Kv 各向异性"); ax[1].grid(alpha=0.3); ax[1].set_title("渗透率各向异性")
    for a in ax:
        for b in SEG_BOUNDS: a.axhline(b, color="0.6", lw=0.6, ls="--")
    ax[0].invert_yaxis()
    fig.suptitle("GJ5-15 分段渗透率剖面（CT 反演）", fontsize=13)
    fig.tight_layout(rect=[0,0,1,0.95])
    p = os.path.join(FIG, "05_permeability.png"); fig.savefig(p, bbox_inches="tight"); plt.close(fig)
    return p


# ---------- 图6：储层综合评价道 + 含油饱和度叠加 ----------
def fig_grade():
    grade = con.execute("SELECT * FROM reservoir_grade").df()
    cmap = {"a": "#2ca02c", "b": "#98df8a", "c": "#ffbb78", "d": "#d62728"}
    fig, ax = plt.subplots(1, 2, figsize=(7.5, 8), sharey=True, gridspec_kw={"width_ratios":[1,2]})
    for _, r in grade.iterrows():
        ax[0].axhspan(r["start_depth"], r["end_depth"], color=cmap.get(r["grade"], "0.8"))
        ax[0].text(0.5, (r["start_depth"]+r["end_depth"])/2, r["grade"].upper(),
                   ha="center", va="center", fontsize=10, fontweight="bold")
    ax[0].set_xticks([]); ax[0].set_title("储层\n综合评价", fontsize=11)
    ax[0].set_ylabel("深度 (m)")
    # 含油饱和度曲线
    ax[1].plot(cur["oil_saturation"].values, cur["depth_m"].values, lw=0.4, color="#8c564b", alpha=0.4)
    ax[1].plot(smooth(cur["oil_saturation"].values), cur["depth_m"].values, lw=1.8, color="#8c564b")
    ax[1].set_xlabel("含油饱和度 %"); ax[1].set_title("含油饱和度", fontsize=11); ax[1].grid(alpha=0.3)
    for b in SEG_BOUNDS:
        ax[1].axhline(b, color="0.6", lw=0.6, ls="--")
    ax[0].set_ylim(3443.52, 3439.13)
    handles = [plt.Rectangle((0,0),1,1, color=cmap[g]) for g in ["a","b","c","d"]]
    fig.legend(handles, ["a 优","b 良","c 中","d 差"], loc="lower center", ncol=4, fontsize=9)
    fig.suptitle("GJ5-15 储层评价 vs 含油饱和度", fontsize=13)
    fig.tight_layout(rect=[0,0.04,1,0.95])
    p = os.path.join(FIG, "06_reservoir_grade.png"); fig.savefig(p, bbox_inches="tight"); plt.close(fig)
    return p


if __name__ == "__main__":
    for fn in [fig_tracks, fig_segment_bars, fig_pore, fig_corr, fig_perm, fig_grade]:
        p = fn()
        print("  saved", os.path.relpath(p, ROOT))
    con.close()
    print(">> 全部图表完成")
