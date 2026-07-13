---
title: E3 nnU-Netv2 同网格交叉核验 —— 同工具受限对照
created: 2026-06-24
tags: [花页7, 实验, E3, nnU-Netv2, 配准, 交叉核验, 中期汇报]
---

# E3：nnU-Netv2 同网格交叉核验

> 目的：E2 用自写 UNet 得高 dice，但 codex 用 nnU-Netv2、模型不同是混淆因素。
> E3 复刻 codex 的 nnU-Netv2 协议并改用同网格 sus，检验同网格输入是否与更高内部 Dice 一致；其余构建与切分因素未完全受控。
> 用独立 nnUNet 工程目录 `~/HXL/HY7_planb/nnunet/`，**不碰 codex 的 `nnUNet_data`**。
>
> **P4 边界补记（2026-07-12）**：Dataset722 的 20 个 192³ block 都从同一 ct28 体随机采样，未保存坐标、buffer、`splits_final.json` 或 case-to-coordinate manifest；fold_0 的 4 例验证可能与训练 block 空间重叠。因此 0.9189/0.9660 是同体 sampled-block internal validation，不是空间独立或跨井泛化。

## 受限同工具对照表（nnU-Netv2）

| 工具 | 配置 | 图像源 | 配准 | 孔隙 Dice |
|---|---|---|---|---|
| nnU-Netv2（codex, Dataset712） | 3d_fullres 5ep | 2024³ 裁剪 | 错位 | **0.0** |
| **nnU-Netv2（E3, 我, Dataset722）** | 3d_fullres 5ep | **同网格 sus** | 共配准 | **0.9189**（IoU 0.85） |
| nnU-Netv2（codex, Dataset712） | 2d 50ep | 2024³ 裁剪 | 错位 | **0.000228** |
| **nnU-Netv2（E3, 我, Dataset722）** | 2d 50ep | **同网格 sus** | 共配准 | **0.9660**（IoU 0.9342） |
| （参考）自写 UNet（E2） | 100ep | 同网格 sus | 共配准 | 0.939 |

## 结论（同体 internal-validation 口径）

- **同一个工具(nnU-Netv2)、相近配置下，改为同网格 sus 后，内部 fold_0 Dice 从早期裁剪路线近零提升到 0.919。**
- 这显著降低了“仅因自写 UNet 才好”的解释空间：nnU-Netv2 在同网格 sampled blocks 上也得到高内部 Dice。
- → 结果为配准错位是早期失败的重要解释提供强线索；因 block 构建、空间 split 和训练设置未完全受控，不能把该结果写成唯一因果变量、空间泛化或外部泛化证明。
- 与 E2（自写 UNet 0.939）相互印证：两种模型在同网格上都得高 dice，量级一致。

## 协作意义（非竞赛）
- 这不是"我赢 codex"，而是**实证 codex 自己 6/22 的纠正方向**（弃 2024³裁剪、改 sus+pore==0）是对的；
  并给团队一个**同体内部 nnU-Netv2 baseline**，可带边界说明进入中期汇报。
- 建议 codex：把早期 Dataset712/713（2024³裁剪, dice≈0）标 superseded，正式 baseline 用同网格 Dataset722 思路。

## 产物 / 防编造
- 数据集：`hy7-linux:~/HXL/HY7_planb/nnunet/nnUNet_raw/Dataset722_HY7_CT2p8um_2phase_samegrid`（20×192³，孔隙 4–11%）
- 构建脚本：`src/hy7_planb_make_nnunet.py`（同网格 sus+pore==0，独立目录）
- 3d 结果：`experiments/花页7_PlanB_记录/evidence_e3_nnunet_3d5ep_summary.json`（foreground Dice 0.9189）
- 2d 结果 `[测]`（2026-06-24 16:10 跑完）：`nnUNetTrainer_50epochs__nnUNetPlans__2d/fold_0/validation/summary.json`，
  孔隙 class1 **Dice 0.9660 / IoU 0.9342**（4 例验证 HY7_003/008/013/016，192³）；"Training done." + Mean Validation Dice 0.9660。
  本地证据副本：`experiments/花页7_PlanB_记录/evidence_e3_nnunet_2d50ep_summary.json`，sha256 `ab7b6151cde35a573b77184e28387179098374fad47c4ed2ce169d309f43a51e`。
- 配置：`nnUNetv2_train 722 3d_fullres 0 -tr nnUNetTrainer_5epochs`（复刻 codex），CTNormalization。

## 阶段一收尾 → 转阶段二
E3 完成即阶段一（分割）的同体内部基线与受限配准对照收尾；不代表空间独立或外部验证完成。
按已确认决策 **D1：下一步转阶段二（2D 扩散生成 DDPM）**，进入论文真正的贡献点。
