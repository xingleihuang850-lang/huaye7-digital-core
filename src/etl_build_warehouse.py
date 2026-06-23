#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GJ5-15 数字井筒数据 ETL —— 把分散的 txt/xlsx 原始统计汇入 DuckDB 仓库，
并导出 master_stats.json（下游出图/出文档统一读这一个文件，保证数字一致）。

数据来源（均为符号链接到外置盘的只读原始数据）：
  data/raw_stats/综合柱状图数据/*.txt        9 条连续曲线 + 储层评价 + 渗透率（GBK 编码）
  data/raw_stats/<属性>/*.xlsx               各属性逐深度段逐层明细（含体积列）
  data/raw_stats/孔隙直径/.../柱状饼状图.xlsx  孔隙等效直径分级分布
  GJ5-15data/GJ5-15_数据分析汇总_*.xlsx       数据清单 + 分段统计 + 可行性分析

产物（均为 .gitignore 忽略的派生物）：
  data/warehouse.db          DuckDB 仓库
  experiments/master_stats.json
用法：  .venv/bin/python src/etl_build_warehouse.py
"""
import os, glob, json, re
import pandas as pd
import numpy as np
import duckdb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(ROOT, "data", "raw_stats")
ZH   = os.path.join(RAW, "综合柱状图数据")
SUMMARY_XLSX = os.path.join(ROOT, "GJ5-15data", "GJ5-15_数据分析汇总_三维矿物分割评估.xlsx")
DB   = os.path.join(ROOT, "data", "warehouse.db")
OUTJSON = os.path.join(ROOT, "experiments", "master_stats.json")

# 5 个深度段（井段 3439.13–3443.52 m）
SEGMENTS = [
    (3439.13, 3439.89), (3439.89, 3440.79), (3440.79, 3441.70),
    (3441.70, 3442.64), (3442.64, 3443.52),
]
SEG_LABELS = [f"{a:.2f}-{b:.2f}" for a, b in SEGMENTS]

# 9 条连续曲线：文件名 -> (英文 key, 中文名, 单位)
CURVE_FILES = {
    "CT基质孔隙度.txt":   ("matrix_porosity", "基质孔隙度", "%"),
    "CT总孔隙度.txt":     ("total_porosity",  "总孔隙度",   "%"),
    "CT裂缝孔隙度.txt":   ("fracture_porosity","裂缝孔隙度", "%"),
    "CT总孔洞缝率.txt":   ("total_vug_frac",  "总孔洞缝率", "%"),
    "CT孔洞缝充填率.txt": ("vug_fill_rate",   "孔洞缝充填率","%"),
    "CT含油率.txt":       ("oil_content",     "含油率",     "%"),
    "CT含油饱和度.txt":   ("oil_saturation",  "含油饱和度", "%"),
    "CT泥质含量.txt":     ("shale_content",   "泥质含量",   "%"),
    "CT成岩矿物含量.txt": ("diagenetic_min",  "成岩矿物含量","%"),
}
CURVE_ORDER = ["matrix_porosity","total_porosity","fracture_porosity","total_vug_frac",
               "vug_fill_rate","oil_content","oil_saturation","shale_content","diagenetic_min"]


def read_gbk_txt(path):
    raw = open(path, "rb").read()
    for enc in ("gbk", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("gbk", errors="replace")


def seg_of(depth):
    # 与服务商汇总表口径一致：分段区间为 (top, bottom]，边界深度归“上一段”（更浅段）；
    # 全井顶点 3439.13 归第 0 段。
    for i, (a, b) in enumerate(SEGMENTS):
        if a < depth <= b:
            return i
    return 0 if depth <= SEGMENTS[0][0] else len(SEGMENTS) - 1


def load_curves():
    """9 条连续曲线合成宽表（按行序对齐，所有曲线同 17983 行）。"""
    cols = {}
    depth = None
    for fname, (key, zh, unit) in CURVE_FILES.items():
        txt = read_gbk_txt(os.path.join(ZH, fname))
        d, v = [], []
        for ln in txt.splitlines()[1:]:
            p = ln.split("\t")
            if len(p) >= 2:
                try:
                    d.append(float(p[0])); v.append(float(p[1]))
                except ValueError:
                    pass
        if depth is None:
            depth = d
        cols[key] = v
    n = min(len(v) for v in cols.values())
    df = pd.DataFrame({k: pd.Series(v[:n]) for k, v in cols.items()})
    df.insert(0, "depth_m", pd.Series(depth[:n]))
    df.insert(1, "segment", df["depth_m"].apply(seg_of))
    df.insert(2, "segment_label", df["segment"].apply(lambda i: SEG_LABELS[i]))
    return df


def load_reservoir_grade():
    txt = read_gbk_txt(os.path.join(ZH, "CT储层综合评价.txt"))
    rows = []
    for ln in txt.splitlines()[1:]:
        p = ln.split("\t")
        if len(p) >= 3:
            try:
                rows.append((float(p[0]), float(p[1]), p[2].strip()))
            except ValueError:
                pass
    return pd.DataFrame(rows, columns=["start_depth", "end_depth", "grade"])


def load_permeability():
    def parse(fname, col):
        txt = read_gbk_txt(os.path.join(ZH, fname))
        out = []
        for ln in txt.splitlines()[1:]:
            p = ln.split("\t")
            if len(p) >= 2:
                try:
                    out.append((float(p[0]), float(p[1])))
                except ValueError:
                    pass
        return out
    kh = parse("CT渗透率（Kh）.txt", "kh")
    kv = parse("CT渗透率（Kv）.txt", "kv")
    rt = parse("CT渗透率（KhKv之比）.txt", "ratio")
    # 阶梯曲线：每段值在顶/底两个深度各出现一次（边界深度还重复了相邻段的值）。
    # 正确取法 = 该段顶、底两端“都出现”的那个值（阶梯平台值），避免误取相邻段。
    def step_val(lst, a, b):
        at_a = {round(v, 6) for d, v in lst if abs(d - a) < 1e-6}
        at_b = {round(v, 6) for d, v in lst if abs(d - b) < 1e-6}
        both = at_a & at_b
        if both:
            return sorted(both)[0]
        inside = [v for d, v in lst if a < d < b]
        if inside:
            return inside[0]
        return sorted(at_a)[0] if at_a else None
    rows = []
    for i, (a, b) in enumerate(SEGMENTS):
        rows.append((SEG_LABELS[i], a, b, step_val(kh, a, b), step_val(kv, a, b), step_val(rt, a, b)))
    return pd.DataFrame(rows, columns=["segment_label","top","bottom","kh_mD","kv_mD","kh_kv_ratio"])


def load_pore_diameter():
    path = os.path.join(RAW, "孔隙直径", "柱状图饼图", "GJ5-15-3439.13-3443.52M-柱状饼状图.xlsx")
    wb = pd.read_excel(path, header=None)
    bins = ["50-100", "100-200", "200-500", "500-1000", ">1000"]
    # 列布局（见表头）：col2-6=各档孔隙“数量”，col7=数量累计，col8-12=各档“体积贡献”，col13=体积累计。
    # 占比行 = 标签行(“50-100”…)的上一行；数量占比在 col2-6，体积占比在 col8-12。
    label_row = None
    for r in range(len(wb)):
        if wb.iloc[r, 2] == "50-100":
            label_row = r; break
    frac_row = label_row - 1
    count_frac = [float(x) for x in wb.iloc[frac_row, 2:7]]
    vol_frac   = [float(x) for x in wb.iloc[frac_row, 8:13]]
    return pd.DataFrame({"diameter_um": bins,
                         "count_fraction": count_frac,
                         "volume_fraction": vol_frac})


def load_summary_sheets():
    seg = pd.read_excel(SUMMARY_XLSX, sheet_name="各深度段统计汇总", header=2)
    seg = seg.dropna(how="all").reset_index(drop=True)
    seg = seg[seg.iloc[:, 0].astype(str).str.match(r"^\d")].reset_index(drop=True)
    inv = pd.read_excel(SUMMARY_XLSX, sheet_name="数据清单总览", header=None)
    feas = pd.read_excel(SUMMARY_XLSX, sheet_name="三维矿物分割可行性分析", header=None)
    return seg, inv, feas


def main():
    print(">> 解析连续曲线 ...")
    curves = load_curves()
    grade  = load_reservoir_grade()
    perm   = load_permeability()
    pore   = load_pore_diameter()
    seg_summary, inventory, feasibility = load_summary_sheets()
    print(f"   曲线宽表 {curves.shape}, 储层评价 {len(grade)} 段, 渗透率 {len(perm)} 段, 孔径 {len(pore)} 档")

    # ---- 写 DuckDB ----
    if os.path.exists(DB):
        os.remove(DB)
    con = duckdb.connect(DB)
    con.register("curves_df", curves)
    con.execute("CREATE TABLE curves AS SELECT * FROM curves_df")
    con.register("grade_df", grade);  con.execute("CREATE TABLE reservoir_grade AS SELECT * FROM grade_df")
    con.register("perm_df", perm);    con.execute("CREATE TABLE permeability AS SELECT * FROM perm_df")
    con.register("pore_df", pore);    con.execute("CREATE TABLE pore_diameter AS SELECT * FROM pore_df")
    con.register("seg_df", seg_summary); con.execute("CREATE TABLE segment_summary_raw AS SELECT * FROM seg_df")

    # 长表（便于按属性 group by）
    long = curves.melt(id_vars=["depth_m","segment","segment_label"],
                       value_vars=CURVE_ORDER, var_name="property", value_name="value")
    con.register("long_df", long)
    con.execute("CREATE TABLE curves_long AS SELECT * FROM long_df")

    # ---- 计算 master 统计 ----
    meta = {k: {"zh": z, "unit": u} for f,(k,z,u) in CURVE_FILES.items()}
    stats = {
        "well": "GJ5-15",
        "interval_m": [3439.13, 3443.52],
        "interval_length_m": round(3443.52 - 3439.13, 2),
        "n_samples": int(len(curves)),
        "vertical_resolution_mm": round((3443.52 - 3439.13) / len(curves) * 1000, 4),
        "segments": SEG_LABELS,
        "curve_meta": meta,
        "curve_order": CURVE_ORDER,
    }
    # 全井 + 分段统计
    overall = {}
    per_segment = {s: {} for s in SEG_LABELS}
    for key in CURVE_ORDER:
        s = curves[key]
        overall[key] = {"mean": round(s.mean(),3), "std": round(s.std(),3),
                        "min": round(s.min(),3), "p25": round(s.quantile(.25),3),
                        "median": round(s.median(),3), "p75": round(s.quantile(.75),3),
                        "max": round(s.max(),3)}
        for i, lab in enumerate(SEG_LABELS):
            sub = curves.loc[curves["segment"] == i, key]
            per_segment[lab][key] = {"mean": round(sub.mean(),3),
                                     "min": round(sub.min(),3),
                                     "max": round(sub.max(),3),
                                     "std": round(sub.std(),3)}
    stats["overall"] = overall
    stats["per_segment"] = per_segment

    # 相关性矩阵
    corr = curves[CURVE_ORDER].corr().round(3)
    stats["correlation"] = {k: corr[k].to_dict() for k in CURVE_ORDER}

    # 渗透率 / 孔径 / 储层评价
    stats["permeability"] = perm.to_dict(orient="records")
    stats["pore_diameter"] = pore.round(4).to_dict(orient="records")
    grade["thickness"] = (grade["end_depth"] - grade["start_depth"]).round(3)
    gsum = grade.groupby("grade")["thickness"].sum().round(3).to_dict()
    stats["reservoir_grade_intervals"] = grade.round(3).to_dict(orient="records")
    stats["reservoir_grade_thickness"] = gsum

    # 各段切片数（来自数据清单）
    stats["slice_counts"] = {
        "3439.13-3439.89": 3399, "3439.89-3440.79": 4235, "3440.79-3441.70": 4253,
        "3441.70-3442.64": None, "3442.64-3443.52": None,
    }
    stats["ct_spec"] = {"pixel_um": 50.62, "image": "624x624", "bit_depth": "16-bit", "format": "TIFF"}

    os.makedirs(os.path.dirname(OUTJSON), exist_ok=True)
    json.dump(stats, open(OUTJSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # 仓库里也存一份分段统计宽表，方便 SQL
    rows = []
    for lab in SEG_LABELS:
        for key in CURVE_ORDER:
            d = per_segment[lab][key]
            rows.append((lab, key, meta[key]["zh"], d["mean"], d["min"], d["max"], d["std"]))
    stat_df = pd.DataFrame(rows, columns=["segment_label","property","property_zh","mean","min","max","std"])
    con.register("stat_df", stat_df)
    con.execute("CREATE TABLE segment_stats AS SELECT * FROM stat_df")

    for v in ["curves_df","grade_df","perm_df","pore_df","seg_df","long_df","stat_df"]:
        try: con.unregister(v)
        except Exception: pass
    print("\n>> DuckDB 表：")
    for t in con.execute("SHOW TABLES").fetchall():
        n = con.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
        print(f"   {t[0]:24s} {n} 行")
    con.close()
    print(f"\n>> 仓库: {DB}\n>> 统计: {OUTJSON}")
    print("\n全井均值速览：")
    for k in CURVE_ORDER:
        print(f"   {meta[k]['zh']:8s} mean={overall[k]['mean']:7.3f}{meta[k]['unit']}  "
              f"[{overall[k]['min']:.2f}, {overall[k]['max']:.2f}]")


if __name__ == "__main__":
    main()
