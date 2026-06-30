---
title: 花页7 Linux ~/HXL 目录整理与分类记录
created: 2026-06-24
tags: [花页7, Linux, 整理, 边界, codex]
---

# Linux `~/HXL` 目录整理与分类记录

> 原则（用户指令）：**codex 的一律不动**；只整理我(Claude)自己的 + 真正的以前残留。
> 判定归属用证据：① 创建者/日期 ② codex 工程（`~/Documents/生成式数字井筒研究`）是否用绝对路径引用。
> grep codex 工程发现它引用了 `GJ5-15_CT / cigrocksem_experiment / U-Net / Shale_0.3_vis / HY7_D2_* / HY7_source …`
> —— 故这些都判为 codex，**不动**（移动会断其引用）。

## 分类总表（顶层）

| 项 | 大小 | 日期 | 归属 | 依据 | 处理 |
|---|---|---|---|---|---|
| **HY7_planb** | 22M | 06-24 | **我** | 我创建 | ✅ **已整理**（见下） |
| HY7_source | 73G | 06-22 | 共享数据 | codex+我都引用 | 不动（只读） |
| nnUNet_data | 40G | 06-21 | codex | Dataset70x/71x | 不动 |
| HY7_D2_balanced_logs / blocks_logs / blocks_results_figures | <1M | 06-20 | codex | 工程引用 | 不动 |
| HY7_miniQC_logs | 12K | 06-20 | codex | 工程引用 | 不动 |
| run_dataset712_*.sh ×3 | 12K | 06-20 | codex | nnU-Net 训练脚本 | 不动 |
| GJ5-15_CT | 3.9G | 06-08 | codex | **grep 命中引用** | 不动 |
| cigrocksem_experiment | 6.3G | 04-15 | codex | grep 命中引用 | 不动 |
| cigrocksem_nnunet_shale | 22M | 04-15 | codex | 同系列 | 不动 |
| model_comparison | 4.4G | 04-14 | codex | 同系列 | 不动 |
| public_shale_validation | 650M | 04-15 | codex | 工程引用 | 不动 |
| reed2025_repro | 3.7G | 04-09 | codex | 工程引用 | 不动 |
| shale_experiments | 345M | 04-17 | codex | 同系列 | 不动 |
| nnunet_pipeline | 18M | 06-09 | 共享/前期汪清流程 | CLAUDE.md 提及 | 不动（待确认） |
| **guanye15-1-1_400** | 371M | 2025-11 | **用户重要数据** | 开题 PPT「已开展研究」的**官页15-1-1井 3260.9m**（孔隙18.8%/石英32.2%/长石35.6%），X/Y/Z 体数据 | **保留勿动**（非残留） |
| 散落文件（见下） | — | 老 | 用户参考/杂项 | — | **不动，建议归档（待确认）** |

散落于 `~/HXL` 根的文件：`U-Net…QEMSCAN.pdf`(参考论文,codex引用)、`nnUNetv2学习教程(Linux/Windows).docx`、某凭据命名文档、`repomix-output-tree-master.xml`、`set_env.txt`、`eval_when_done.log`、`run_unet3plus_eval_when_done.sh`。

## 我做了什么（仅 HY7_planb）

整理前（全堆在一层）→ 整理后（清晰三分）：
```
HY7_planb/
├── README_OWNERSHIP.md          # 归属与边界
├── src/                         # 5 个脚本（rsync 目标）
│   └── hy7_planb_{io,check_alignment,dataset,train,verify_nonleak}.py
├── runs/
│   └── train_ct14_baseline/     # dice 0.831 基线（best.pt + trainlog.json）
└── logs/
    └── train_ct14_baseline.log
```
- 删了 `__pycache__`；把根层脚本归入 `src/`；训练产物归入 `runs/<run名>/`；日志归入 `logs/`。
- 对应改了 `train.py` 默认输出到 `runs/train_<scale>`；rsync 目标改为 `~/HXL/HY7_planb/src/`。

## 我没动什么 + 为什么

- **codex 的一律没动**（用户硬约束）；且 codex 工程用绝对路径引用了大量目录，移动会断引用。
- **歧义项没动**：`guanye15-1-1_400`、根目录散落文件——无法 100% 排除 codex/你在用，**擅自移动违反"codex 不动"且不可逆**。

## 建议你拍板的（确认后我再动）
1. `guanye15-1-1_400`(371M)：是哪口井的早期数据？若确无用/归别处，我可移到 `~/HXL/_archive_legacy/`。
2. 根目录散落参考文件（教程 docx、odt、xml、log）：是否归到 `~/HXL/_refs/` 让根目录清爽？（这些大概率不被脚本引用，但我不擅自动。）
3. `nnunet_pipeline`(前期汪清流程)：保留原位还是归档？

> 在你确认前，除 `HY7_planb` 外**一切原位不动**。

## 已执行（2026-06-27，用户拍板「只归档零散文件」）
- 新建 `~/HXL/_refs/`，`mv`（可逆）进 5 个**经 grep 确认无脚本引用**的零散文件：
  `nnUNetv2学习教程(Linux/Windows).docx` · 某凭据命名文档 · `repomix-output-tree-master.xml` · `eval_when_done.log`。
- **大目录全部原位不动**——确认了硬约束：除 `HY7_planb`（我的，且是 rsync 目标）外几乎全是 codex 绝对路径引用或共享只读数据，物理移动会断 codex 工程/我的 rsync，不可逆。故"大目录分组重排"与"codex 不动"本质冲突，只能靠 `00_README_INDEX.md` 索引归类。
- 仍留根目录（codex 引用，勿动）：`run_dataset712_*.sh`×3、`run_unet3plus_eval_when_done.sh`、`set_env.txt`（nnUNet env 变量）、`U-Net…QEMSCAN.pdf`。
- 待办项 1（guanye15-1-1_400）、3（nnunet_pipeline）：用户选择暂不动（非 codex 但归属待定，无脚本引用风险时再议）。
