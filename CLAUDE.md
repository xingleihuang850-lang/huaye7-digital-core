# 生成式数字井筒研究 — 项目上下文

> 供编码 agent（Claude Code / Codex / Cursor 等）进入项目时自动读取，快速建立背景。
> 交接自规划对话；2026-06-15 由 agent 核对磁盘实际情况后更新。后续如有新决策，请同步更新本文件。
> 2026-06-23：笔记层改定为 **Obsidian（纯 Markdown）**，弃用思源（其 .sy/JSON 非纯 md，agent 不可直接读）；相应放宽 §3「重要约定」。

## ★ 主线任务与工作纪律（**设计每一步前必读，防偏离主线**）

> 用户指令 2026-06-25 固化。配套详表 [`notes/00_研究主线路线图与任务分解.md`](notes/00_研究主线路线图与任务分解.md)（设计下一步前连这份一起读）。

**唯一主线 = 硕士论文《基于融合多尺度数据的页岩数字岩心-井筒建模》**。贡献点 = 生成式(扩散) + 多模态融合 + 数字井筒。**分割只是阶段一地基，不能停在多尺度分割。**

开题四阶段（不可偏离）：**① 分割 → ② 2D 扩散生成 → ③ 多模态 3D 数字岩心 → ④ 数字井筒**。

**当前进度（2026-07-01）**：阶段一已收尾（E0/E2/E3 配准+3D、S3 Amics 多矿物 1μm 丰富相 0.67–0.73；官页15-1-1 T0613论文修改版基准入档见 [`notes/19_阶段一_官页15-1-1_T0613分割基准.md`](notes/19_阶段一_官页15-1-1_T0613分割基准.md)）。**阶段二 M7-v2 已完成**：见 [`notes/22_阶段二_M7v2_阈值标定诊断.md`](notes/22_阶段二_M7v2_阈值标定诊断.md)。
> **M7-v2 结论**：T*=0.98732 标定后分离出两个独立问题——① **阈值伪影（已修）**：S₂ rmse 下降约97%（0.07143→0.00242）；② **连通性真错（待迭代）**：Euler 207.92→真实127.33，孤立散点≠成簇孔隙。
> **M7-v3 / B1 当前状态**：见 [`notes/24_阶段二_M7v3_连通性迭代设计.md`](notes/24_阶段二_M7v3_连通性迭代设计.md)、[`notes/25_阶段二_M7v3_200ep评估与B1决策.md`](notes/25_阶段二_M7v3_200ep评估与B1决策.md)、[`notes/26_阶段二_B1灰度介质生成设计.md`](notes/26_阶段二_B1灰度介质生成设计.md)。`ddpm_ct28_200ep` 已完成采样/评估：200ep T=0 为 φ=4.960%、S₂ rmse=0.00372、Euler=120.88、maxCC=0.0467；T* 标定到 φ=6.4 后 S₂ rmse=0.01010、Euler=119.58。结论：单纯二值 DDPM 加 epoch 不闭合。B1 灰度 `sus` 50ep cheap run 已完成：threshold φ=6.4 口径 S₂ rmse=0.00105、Euler=111.00、maxCC=0.0880，优于二值 DDPM 主线；Fable5 后续控制确认 nnUNet 管线对真实灰度有效（real gray→nnUNet φ=5.689%、Euler=121.08、maxCC=0.0559），generated gray 的 nnUNet 过分割主要来自灰度域偏移（mean shift=-0.333，KS≈0.398；φ=6.4 阈值 real=-0.6125 vs generated=-0.9749）。下一步先做灰度域校正/阈值敏感性，再决定 B1 200ep；暂不转 B2。
> **接力提示**：新会话先读本★节 + [`notes/README.md`](notes/README.md) + [`notes/03_项目Workflow设计.md`](notes/03_项目Workflow设计.md) + [`notes/04_项目术语表与写法规范.md`](notes/04_项目术语表与写法规范.md) + 22/24 号笔记。远程长任务先开 caffeinate（见 memory [[remote-job-no-sleep]]）。

**工作纪律（每一步都遵守，不只 M6/M7）**：
1. **拆小目标、逐个完成**；**每完成一个小目标给用户一条进度说明/提示**（做了什么、结论、下一步）。
2. **设计任何新步骤前，先查文献（`literature/` + Zotero）+ 核物理原理 + 核地质意义**，把依据写进设计笔记再动手——**禁止无根据闷头做**。付费/墙外文献**不得自行绕过**：发现需要时直接告知用户（用户有学校数据库访问权限，可代为下载；获取后归档到 `literature/`，在 `_manifest.txt` 记 doi+sha256+来源"★学校访问"）。
3. **设计下一步前先读本节 + 路线图笔记**，确认仍在主线四阶段内，发现偏离立即纠正。
4. **每步留痕（防编造）**：数据分析/文献在先 → 做 → 结果即时入档 + sha256（见 memory [[provenance-no-fabrication]]、[[grounding-before-each-step]]）。

## 0. 环境与数据位置（**先读这条**）

- **工程根（本地 SSD，持久，git 管理）**：`/Users/hxl/Documents/claude/`
- **原始数据（可移动外置盘，18G）**：`/Volumes/Untitled/GJ5-15data/`
  - ⚠️ 这是可移动盘，**卸载/拔盘后下面的符号链接会失效**。DuckDB 仓库里已入库的结构化数据不受影响，但重新跑导入脚本前要确认盘已挂载。
- **数据引用方式**：软链接，不拷贝（用户决策 2026-06-15）。
  - `GJ5-15data` → `/Volumes/Untitled/GJ5-15data`（整盘引用）
  - `nnunet_pipeline` → 同上的 `nnunet_pipeline/` 子目录
  - `data/raw_stats` → 同上的 `GJ5-15-统计分析库/`（DuckDB 入库的小体积 xlsx）

- **花页7（HuaYe7）多尺度数据** —— 当前主线研究。外置盘根目录 `/Volumes/Untitled/吉林大学数据报告归总/`（花页7井 4199.21m 页岩，~73 GB；"吉林大学"是来源单位，**非 GJ5-15**）。⚠️ **这个文件夹里只有 6 个尺度文件夹是服务商原件，其余全是用户用 AI 生成的派生物或既往工作**，三类务必别混：

  | 类别 | 内容 | 谁产出 |
  |---|---|---|
  | **① 服务商原件**（唯一原始数据） | 6 个尺度文件夹：`Amics矿物整体扫描25um+精细扫描1um`、`微米CT柱塞扫描-14um`、`微米CT精细扫描-2p8um`、`纳米CT扫描-65nm`、`FIB-SEM聚焦离子束扫描-8p589nm`、`Maps整体扫描200nm+精细扫描10nm`。每个含：原始体素/图像(.raw/.tif)+处理图像+服务商统计 xlsx+服务商报告(.doc/.docx) | 服务商（欧勒姆能源测试） |
  | **② AI 分析派生物** | `_analysis/`（用户早先在 **Windows(E:)** 上的分析脚本工作区：`build_excel.py`/`build_ppt.py`/`gen_charts.py`/`verify_excel.py`… 读①的统计 xlsx → 出汇总/规划/图/切片）；`花页7井_4199.21m_多尺度数据汇总.xlsx`（已删）；`花页7井_4199.21m_数据分析与AI研究规划.xlsx`（已删，由 `_analysis/build_excel.py` 产）；3 个 `花页7井_4199.21m_…pptx`（深度学习应用 / 生成式数字井筒研究方案 / 备份） | 用户用 AI 生成 |
  | **③ 既往工作（铺垫）** | `AI-Driven Automatic Segmentation and Quantitative Characterization of Shale Microstructures.pptx` | 用户之前的工作，为花页7 + 数字井筒生成铺垫 |

  - 仓库脚本只认 ① 的统计 xlsx：已把其中 7 个（~0.5 MB）拷到本地 `data/hy7_raw/`（git 忽略），`src/hy7_etl.py`/`verify_hy7.py` 路径改为本地 `B = ROOT/data/hy7_raw`，**不再依赖外盘**；改这条路径要同步 `scripts/sync_huaye7_public.sh` 的脱敏匹配串。
  - `src/hy7_*.py` 是把 ② 那套 `_analysis` 工作**清洗重写进 git** 的版本（① 统计 xlsx → `experiments/hy7_stats.json` → `deliverables/花页7/…`）。
  - ⚠️ `花页7井_4199.21m_多尺度数据汇总.xlsx` 已删：它是 **② 类 AI 派生物（可由 `_analysis` 脚本重生，非服务商原件）**。主数据流不依赖它——`hy7_etl.py` 直接从 ① 的各尺度统计 xlsx 出数；仅 `verify_hy7.py` 拿它做一次性"防编造"对账（曾 12/12 通过，结论已得）。
  - `data/hy7_amics_inspect/` 是 Amics 局部核查材料（BSE/矿物图、服务商报告/表格），按原始/半原始检查材料处理，**不入 git**；正式可复现证据与图放 `experiments/花页7_PlanB_记录/`。

- **算力机器（2026-06-23）**：
  - Linux 台式机：SSH 别名 `hy7-linux`（Tailscale `100.127.180.10`）/ `hy7-linux-lan`（同局域网 `192.168.1.164`，传大文件走这条更快），user=`user`，密钥 `~/.ssh/hy7_linux_ed25519`。花页7 实验主力机；数据在 `/home/user/HXL/`（`HY7_source/吉林大学数据报告归总` 为数据本体，与外盘 rsync 同步；`HY7_D2_*` 为训练日志/结果/图）。
  - 另有一台 5090 Linux 跑大规模计算。
  - 跨机传输按既定通道：**Tailscale / LAN + rsync**（勿用 ToDesk）。

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
| `nnunet_pipeline/` | nnU-Netv2 分割管线脚本 + 少量弱标注样本 | **判别式分割，非生成** |

**统计分析库子目录**（每个下含 5 个深度段 xlsx）：泥质含量(NZ)、成岩矿物含量(CYKW)、基质孔隙度、裂缝孔隙度、含油率、含油饱和度、孔洞缝充填率、总孔洞缝率、孔隙直径、综合柱状图数据。
- ⚠️ 库根目录有一批带 `(1)` 后缀的**重复文件**（如 `…基质孔隙度(1).xlsx`），入库前去重。

**nnunet_pipeline 要点**（详见其 `README_PIPELINE.txt`）：
- 分割 3 类：`0=基质 / 1=孔隙 / 2=裂缝`。
- 设计为整包 scp 到 Linux GPU 机训练（step0 诊断 → step1 转 nnU-Netv2 格式 → step2 训练 → step3 推理）。
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
├── notes/                          # Obsidian vault（纯 md，入 git；NN_前缀编号排序，见下；attachments/ 放附件）
├── vectorstore/                    # LanceDB 索引（产物，不入 git）
├── GJ5-15data -> 外盘              # 符号链接（整盘）
└── nnunet_pipeline -> 外盘/…       # 符号链接（已有分割管线）
```

- **notes/ 笔记命名与阅读顺序约定（2026-06-25 固化，每次新建笔记都遵守）**：用 `NN_[阶段_]主题.md` 编号前缀，使 Finder/Obsidian/grep 里自动成阅读顺序。号段：`00` 总览路线图 · `01–02` 综述/工作梳理 · `1x` 阶段一(分割) · `2x` 阶段二(生成) · `3x` 阶段三(多模态3D) · `4x` 阶段四(数字井筒) · `9x` 工程/杂项。**新笔记取所属阶段下一个空号；建完在 [`notes/README.md`](notes/README.md)（阅读索引 MOC）补一行。重命名笔记须同步改所有 `[[双链]]`/链接（notes+CLAUDE.md+memory）。** 入口永远是 `notes/README.md`。
- Python 工具：`lasio` / `welly`（读测井）、`duckdb`、`lancedb`、`pytorch`、`openpyxl`（读 xlsx）。
- **⚠️ Matplotlib 中文字体规范（必须遵守，违者图中汉字变方框）**：
  - **hy7-linux（远程 Linux）**：系统默认无中文字体，生成图的所有 `title/xlabel/ylabel/label/suptitle` **一律用英文**；若必须中文，需先 `ssh hy7-linux-lan "fc-list | grep -i noto"` 确认字体存在，并在脚本开头加 `matplotlib.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'DejaVu Sans']`。
  - **本机 macOS**：可用 `matplotlib.rcParams['font.sans-serif'] = ['PingFang SC', 'Heiti SC', 'Arial Unicode MS', 'DejaVu Sans']`；同时加 `matplotlib.rcParams['axes.unicode_minus'] = False`。
  - **最安全做法**：凡脚本可能在 Linux 上跑，图表标签一律英文——这是科学图表惯例，不影响论文质量。
- **本机 Python 环境（2026-06-24 升级）**：`.venv/` 是 **uv 管理的 Python 3.12**（取代旧系统 3.9.6），依赖钉死在 `requirements.txt`。
  - 跑脚本：`.venv/bin/python src/xxx.py`。
  - 装包：用 **`uv pip install --python .venv/bin/python <包>`**（uv 在 `~/Library/Python/3.9/bin/uv`）；⚠️ `.venv` 内没有 pip，别用 `.venv/bin/python -m pip`。
  - 重建：`uv venv --python 3.12 && uv pip install --python .venv/bin/python -r requirements.txt`。
  - 已装：分析栈（numpy/pandas/scipy/matplotlib/openpyxl/python-docx/python-pptx/duckdb/tifffile/scikit-image）+ **torch 2.12（Apple Silicon MPS 可用）**。本机只做轻量 dev/验证，大规模训练在 5090 Linux。
  - **阶段二 DDPM 训练/采样脚本当前按远程 GPU 环境运行**：`src/hy7_phase2_ddpm.py` 需要 `diffusers`；2026-07-01 已核实远程 `nnunet_t28` 环境为 `diffusers==0.38.0`。本机 `.venv` 暂未钉该包；若要本机复现 DDPM train/sample，先按远程版本策略补依赖并记录。
- 关键术语中英对照：含水饱和度/Sw、含油饱和度/So、孔隙度/porosity、泥质含量/Vsh(NZ)、成岩矿物/CYKW、基质/matrix、孔隙/pore、裂缝/fracture。

## 5. 建议 agent 优先做的事

1. ✅ 搭骨架 + 软链接 + git（2026-06-15 完成）。
2. 读 `GJ5-15data/GJ5-15_数据分析汇总_三维矿物分割评估.xlsx`，理解结构，设计 DuckDB 表 + 导入脚本（`src/`）。
3. 把 `data/raw_stats/` 各属性逐深度段 xlsx 汇入 DuckDB（注意去重 `(1)` 文件、从文件名解析深度段）。
4. 给 `GJ5-15data/GJ5-15-图片库/` 建 LanceDB 多模态索引最小原型。
5. 梳理 `nnunet_pipeline/` 的 `dataset.json`/自定义脚本，记录数据规格与产出；确认大体积 CT 训练数据所在。
6. 调研并起草"分割 → 生成"那一跳的技术方案（超分辨 / 补全 / 虚拟岩心生成）。
