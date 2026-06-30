#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""花页7 多尺度图表 → experiments/hy7_figures/。用法： .venv/bin/python src/hy7_figures.py"""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import hy7_mpl_cjk  # 统一中文字体(两机通用,自动选 Noto/PingFang)，取代手写 font.sans-serif

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ST = json.load(open(os.path.join(ROOT, "experiments", "hy7_stats.json"), encoding="utf-8"))
FIG = os.path.join(ROOT, "experiments", "hy7_figures"); os.makedirs(FIG, exist_ok=True)
plt.rcParams["figure.dpi"] = 145
plt.rcParams["font.size"] = 14          # 整体字号放大
plt.rcParams["axes.titlesize"] = 16
plt.rcParams["axes.labelsize"] = 14
plt.rcParams["xtick.labelsize"] = 12.5
plt.rcParams["ytick.labelsize"] = 12.5
plt.rcParams["legend.fontsize"] = 12.5
TEAL="#1C7293"; AMBER="#E8A33D"; NAVY="#10233A"; DEEP="#0E4A66"


def fig_porosity():
    poro = ST["porosity_total"]          # 仅总孔隙度尺度（FIB-SEM 的 1.52% 是有机质占比，不计入）
    labels = [f"{p['scale']}\n{p['res']}" for p in poro]
    vals = [p["porosity"] for p in poro]
    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.bar(range(len(vals)), vals, color=[AMBER if v==max(vals) else TEAL for v in vals])
    ax.set_xticks(range(len(vals))); ax.set_xticklabels(labels, fontsize=12.5)
    ax.set_ylabel("总孔隙度 (%)"); ax.set_title("花页7 多尺度总孔隙度（非单调 = 尺度效应/REV）")
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v}%", ha="center", va="bottom", fontsize=14, fontweight="bold")
    ax.set_ylim(0, max(vals)*1.15); ax.grid(axis="y", alpha=0.3)
    ax.plot(range(len(vals)), vals, color=NAVY, lw=1, ls="--", marker="o", ms=5, alpha=0.6)
    fig.tight_layout(); p=os.path.join(FIG,"01_porosity.png"); fig.savefig(p,bbox_inches="tight"); plt.close(fig); return p


def fig_minerals():
    coarse = sorted(ST["minerals"]["coarse_25um"], key=lambda d: -d["pct"])
    names = [d["mineral"] for d in coarse]; vals = [d["pct"] for d in coarse]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios":[1.45,1]})
    y = list(range(len(names)))[::-1]
    ax1.barh(y, vals, color=TEAL)
    ax1.set_yticks(y); ax1.set_yticklabels(names, fontsize=12)
    for yy, v in zip(y, vals): ax1.text(v+0.3, yy, f"{v}", va="center", fontsize=11)
    ax1.set_xlabel("含量 (%)"); ax1.set_title("矿物组成（Amics 粗扫 25μm）", fontsize=15)
    ax1.set_xlim(0, max(vals)*1.12); ax1.grid(axis="x", alpha=0.3)
    # 环形图：百分比放扇形正中（fully inside），名称走图例（outside），不再半里半外
    g = ST["lithology_groups"]
    keys=["长英质","碳酸盐","黏土","黄铁矿","其它"]; gv=[g[k] for k in keys]
    cols=[TEAL,AMBER,"#7BA88B","#B0573A","#C9C9C9"]
    ax2.pie(gv, colors=cols, startangle=90,
            autopct=lambda p: f"{p:.1f}%" if p>=4 else "",
            pctdistance=0.79, wedgeprops={"width":0.42,"edgecolor":"white","linewidth":1.5},
            textprops={"fontsize":14,"color":"white","fontweight":"bold"})
    ax2.set_title("岩性归组", fontsize=15)
    ax2.legend([f"{k}  {v}%" for k,v in zip(keys,gv)], loc="lower center",
               bbox_to_anchor=(0.5,-0.16), ncol=2, fontsize=12, frameon=False, handlelength=1.2)
    fig.suptitle("花页7 矿物组成 —— 钙质长英质页岩、黏土低", fontsize=17, y=1.0)
    fig.tight_layout(rect=[0,0,1,0.96]); p=os.path.join(FIG,"02_minerals.png"); fig.savefig(p,bbox_inches="tight"); plt.close(fig); return p


def fig_pore_radius():
    panels = [("ct14","微米CT 14μm","μm"),("ct28","微米CT 2.8μm","μm"),
              ("nano65","纳米CT 65nm","μm"),("fib","FIB-SEM 8.589nm","nm")]
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    for ax,(k,title,unit) in zip(axes.flat, panels):
        pr = ST["scale_data"][k]["pore_radius"]
        bins=[d["bin"] for d in pr]; vol=[d["v1"] for d in pr]; cnt=[d["v2"] for d in pr]
        x=np.arange(len(bins)); w=0.4
        ax.bar(x-w/2, vol, w, label="体积占比", color=TEAL)
        ax.bar(x+w/2, cnt, w, label="个数占比", color=AMBER)
        ax.set_xticks(x); ax.set_xticklabels(bins, rotation=40, ha="right", fontsize=11)
        ax.set_title(f"{title}  孔隙半径分布 ({unit})", fontsize=14)
        ax.set_ylabel("%"); ax.grid(axis="y", alpha=0.3); ax.legend(fontsize=12)
    fig.suptitle("花页7 各尺度孔隙半径分布：体积 vs 个数", fontsize=17)
    fig.tight_layout(rect=[0,0,1,0.96]); p=os.path.join(FIG,"03_pore_radius.png"); fig.savefig(p,bbox_inches="tight"); plt.close(fig); return p


def fig_coordination():
    fig, ax = plt.subplots(figsize=(10, 5.6))
    scales=[("ct14","14μm",TEAL),("ct28","2.8μm",AMBER),("nano65","65nm",DEEP),("fib","FIB-SEM","#B0573A")]
    for k,lab,col in scales:
        co=ST["scale_data"][k]["coordination"]
        n=[float(d["bin"]) for d in co]; cnt=[d["v2"] for d in co]
        ax.plot(n, cnt, marker="o", ms=6, lw=2, label=lab, color=col)
    ax.set_xlabel("配位数（孔隙连接的喉道数）"); ax.set_ylabel("个数占比 (%)")
    ax.set_title("花页7 各尺度孔隙配位数分布（连通性）")
    ax.set_xlim(-0.5, 12); ax.grid(alpha=0.3); ax.legend()
    ax.text(0.98,0.93,"配位数集中在低值（0 为最大占比）→ 连通性整体偏弱",transform=ax.transAxes,
            ha="right",va="top",fontsize=12.5,color=NAVY,style="italic")
    fig.tight_layout(); p=os.path.join(FIG,"04_coordination.png"); fig.savefig(p,bbox_inches="tight"); plt.close(fig); return p


def fig_maps():
    md = ST["maps_dist"]
    fig, ax = plt.subplots(figsize=(10, 5.6))
    for name,col in [("有机孔隙","#B0573A"),("无机孔隙",TEAL)]:
        if name in md and md[name]:
            r=[d["r_nm"] for d in md[name]]; p=[d["pct"] for d in md[name]]
            ax.plot(r,p,marker="o",ms=6,lw=2,label=name,color=col)
    ax.set_xlabel("孔隙半径 (nm)"); ax.set_ylabel("分布占比 (%)")
    ax.set_title("花页7 Maps SEM(10nm) 有机 vs 无机 孔隙半径分布")
    ax.grid(alpha=0.3); ax.legend()
    ax.text(0.98,0.93,"无机孔隙为主体（面占比 70%）",transform=ax.transAxes,
            ha="right",va="top",fontsize=13,color=NAVY,style="italic")
    fig.tight_layout(); p=os.path.join(FIG,"05_maps.png"); fig.savefig(p,bbox_inches="tight"); plt.close(fig); return p


def fig_ladder():
    """多尺度阶梯：每个尺度独立一行(名称放 y 轴标签，绝不重叠)，φ 标在点正上方。"""
    order=["amics","ct14","ct28","nano65","maps10","fib"]   # 粗 → 细
    meta={s["key"]:s for s in ST["scales"]}
    res_um={"amics":25,"ct14":14,"ct28":2.8,"nano65":0.065,"maps10":0.01,"fib":0.008589}
    poro={"ct14":1.558,"ct28":7.182,"nano65":1.925,"maps10":0.411}  # 总孔隙度；FIB-SEM 无总孔隙度(报有机质占比)，与 Amics 一样不标 φ
    n=len(order); ys=list(range(n))[::-1]   # amics 在最上(n-1)，fib 最下(0)
    xs=[res_um[k] for k in order]
    fig, ax = plt.subplots(figsize=(12, 6.2))
    ax.plot(xs, ys, color="#9BB0BF", lw=1.6, ls="--", zorder=1)
    pmax=max(poro.values())
    for k,x,y in zip(order,xs,ys):
        col = AMBER if poro.get(k)==pmax else TEAL
        ax.scatter(x, y, s=300, color=col, zorder=3, edgecolor="white", linewidth=2)
        if k in poro:
            ax.annotate(f"φ={poro[k]}%", (x,y), xytext=(0,16), textcoords="offset points",
                        ha="center", fontsize=13, color=DEEP, fontweight="bold")
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{meta[k]['name']}\n{meta[k]['res']}" for k in order], fontsize=13)
    ax.set_xscale("log"); ax.set_xlabel("分辨率 (μm，对数轴)")
    ax.set_xlim(0.005, 45); ax.set_ylim(-0.6, n-0.4)
    ax.set_title("花页7 多尺度成像阶梯：25μm → 8.589nm（跨约 3000 倍）", pad=14)
    ax.grid(axis="x", alpha=0.3, which="both")
    fig.tight_layout(); p=os.path.join(FIG,"06_ladder.png"); fig.savefig(p,bbox_inches="tight"); plt.close(fig); return p


if __name__ == "__main__":
    for fn in [fig_porosity, fig_minerals, fig_pore_radius, fig_coordination, fig_maps, fig_ladder]:
        print("  saved", os.path.relpath(fn(), ROOT))
    print(">> 花页7 图表完成")
