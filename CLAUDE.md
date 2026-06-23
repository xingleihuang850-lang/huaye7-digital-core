# 生成式数字井筒研究 — 项目上下文

> 供编码 agent（Claude Code / Codex / Cursor 等）进入项目时自动读取，快速建立背景。
> 交接自规划对话；2026-06-15 由 agent 核对磁盘实际情况后更新。后续如有新决策，请同步更新本文件。
> 2026-06-23：笔记层改定为 **Obsidian（纯 Markdown）**，弃用思源（其 .sy/JSON 非纯 md，agent 不可直接读）；相应放宽 §3「重要约定」。

## 0. 环境与数据位置（**先读这条**）

- **工程根（本地 SSD，持久，git 管理）**：`/Users/hxl/Documents/claude/`
- **原始数据（可移动外置盘，18G）**：`/Volumes/Untitled/GJ5-15data/`
  - ⚠️ 这是可移动盘，**卸载/拔盘后下面的符号链接会失效**。DuckDB 仓库里已入库的结构化数据不受影响，但重新跑导入脚本前要确认盘已挂载。
- **数据引用方式**：软链接，不拷贝（用户决策 2026-06-15）。
  - `GJ5-15data` → `/Volumes/Untitled/GJ5-15data`（整盘引用）
  - `nnunet_pipeline` → 同上的 `nnunet_pipeline/` 子目录
  - `data/raw_stats` → 同上的 `GJ5-15-统计分析库/`（DuckDB 入库的小体积 xlsx）

## 1. 项目目标

- **主线**：完成"生成式数字井筒"研究。
- **数字井筒**：基于多尺度数字岩心，结合电成像、常规测井构建的三维井筒表征，可提供虚拟测井数据，是三维测井数据处理与解释的辅助手段。
- **"生成式"贡献点**：在数字岩心 / 测井基础上，用生成模型（VAE / GAN / 扩散 / Transformer / 大模型）做：
  - 三维体素超分辨；
  - 缺失数据 / 坏井段补全；
  - 从少量 CT 岩心样本，生成沿井深连续的虚拟岩心 / 虚拟测井；
  - 不确定性量化（多样本生成，给分布而非单点）。
- **核心认识**：现状停在判别式"分割"；本研究的下一跳是"生成"。从"几块扫描过的岩心"到"一整条数字井筒"，那一步生成式建模就是贡献所在。

## 2. 已有数据（核对自磁盘，GJ5-15 为井号/样品号）

岩心井段整体 **3439.13–3443.52 m**（约 4.4 m），统计按 5 个深度段切分：
`3439.13–3439.89` / `3439.89–3440.79` / `3440.79–3441.70` / `3441.70–3442.64` / `3442.64–3443.52` m。

| 路径 | 内容 | 备注 |
|---|---|---|
| `GJ5-15data/GJ5-15_数据分析汇总_三维矿物分割评估.xlsx` | 分割后定量统计与评价（矿物体积分数、孔隙等） | 汇总表 |
| `GJ5-15data/GJ5-15_三维矿物分割可行性分析.pptx` | 可视化 / 汇报 | — |
| `data/raw_stats/`（=统计分析库） | 按属性分目录的逐深度段 xlsx | **DuckDB 入库金矿** |
| `GJ5-15data/GJ5-15-图片库/` | CT 2D切片、3D岩心/孔隙/矿物/裂缝渲染图、岩心剖面展开图 | 大，LanceDB 多模态索引对象 |
| `GJ5-15data/GJ5-15-动画库/` | 含油/孔隙/成岩矿物/纹夹层/裂缝 3D 动画 | 大，已 .claudeignore |
| `nnunet_pipeline/` | nnU-Net v2 分割管线脚本 + 少量弱标注样本 | **判别式分割，非生成** |

**统计分析库子目录**（每个下含 5 个深度段 xlsx）：泥质含量(NZ)、成岩矿物含量(CYKW)、基质孔隙度、裂缝孔隙度、含油率、含油饱和度、孔洞缝充填率、总孔洞缝率、孔隙直径、综合柱状图数据。
- ⚠️ 库根目录有一批带 `(1)` 后缀的**重复文件**（如 `…基质孔隙度(1).xlsx`），入库前去重。

**nnunet_pipeline 要点**（详见其 `README_PIPELINE.txt`）：
- 分割 3 类：`0=基质 / 1=孔隙 / 2=裂缝`。
- 设计为整包 scp 到 Linux GPU 机训练（step0 诊断 → step1 转 nnU-Net 格式 → step2 训练 → step3 推理）。
- 此目录只有脚本 + `refine_set/`（弱标注 tif 样本）+ `reference_porosity_curve.csv`。
- ⚠️ **真正的大体积 CT 训练数据不在这 18G 内**——需确认它在哪台机器/盘上。

## 3. 本地知识 / 数据系统架构

| 层 | 工具 | 内容 |
|---|---|---|
| 结构化数据 | DuckDB | 测井曲线、统计指标、模型评价（LAS / CSV / Parquet）→ `data/warehouse.db` |
| 向量 / 多模态 | LanceDB | CT 切片、渲染图、曲线 embedding（agent 语义记忆）→ `vectorstore/` |
| 文献 | Zotero | 论文、教材、标准、引用 |
| 笔记 | Obsidian（纯 md vault） | 学习笔记、概念卡、公式、源码笔记；纯 Markdown，agent 可直接读 |
| 代码 / 实验 | Git | 代码、模型、实验配置、笔记导出 |

**数据流**：结构化路径 井数据→DuckDB；语义路径 论文（Zotero 导出）+ 笔记（Obsidian 纯 md，无需导出）→分块→embedding→LanceDB。两路在 **agent** 处汇合：对 DuckDB 走 SQL，对 LanceDB 走向量检索 → 解释 / 生成 / 评价。

**重要约定**：agent 有两条读取面——① **直接读 Obsidian vault（纯 md）** 做精确查找/grep；② **LanceDB（向量）+ DuckDB（SQL）** 做语义/结构化检索。笔记同时进 LanceDB 做语义查。（喂 embedding 前可轻量清理 Obsidian 自家语法：`[[双链]]`、`%%注释%%`、callout、YAML frontmatter。）

## 4. 目录与工程约定

```
/Users/hxl/Documents/claude/        # 工程根（本地，git）
├── CLAUDE.md                       # 本文件
├── .claudeignore  .gitignore
├── data/
│   ├── raw_stats -> 外盘/统计分析库  # 符号链接
│   ├── raw_las/  parquet/           # 待建
│   └── warehouse.db                 # DuckDB（产物，不入 git）
├── src/                            # 解释函数、模型、agent 代码
├── experiments/                    # 实验记录与产出
├── notes/                          # Obsidian vault（纯 md，入 git；attachments/ 放附件）
├── vectorstore/                    # LanceDB 索引（产物，不入 git）
├── GJ5-15data -> 外盘              # 符号链接（整盘）
└── nnunet_pipeline -> 外盘/…       # 符号链接（已有分割管线）
```

- Python 工具：`lasio` / `welly`（读测井）、`duckdb`、`lancedb`、`pytorch`、`openpyxl`（读 xlsx）。
- 关键术语中英对照：含水饱和度/Sw、含油饱和度/So、孔隙度/porosity、泥质含量/Vsh(NZ)、成岩矿物/CYKW、基质/matrix、孔隙/pore、裂缝/fracture。

## 5. 建议 agent 优先做的事

1. ✅ 搭骨架 + 软链接 + git（2026-06-15 完成）。
2. 读 `GJ5-15data/GJ5-15_数据分析汇总_三维矿物分割评估.xlsx`，理解结构，设计 DuckDB 表 + 导入脚本（`src/`）。
3. 把 `data/raw_stats/` 各属性逐深度段 xlsx 汇入 DuckDB（注意去重 `(1)` 文件、从文件名解析深度段）。
4. 给 `GJ5-15data/GJ5-15-图片库/` 建 LanceDB 多模态索引最小原型。
5. 梳理 `nnunet_pipeline/` 的 `dataset.json`/自定义脚本，记录数据规格与产出；确认大体积 CT 训练数据所在。
6. 调研并起草"分割 → 生成"那一跳的技术方案（超分辨 / 补全 / 虚拟岩心生成）。
