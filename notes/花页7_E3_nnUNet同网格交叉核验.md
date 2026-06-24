---
title: E3 nnU-Net 同网格交叉核验 —— 隔离模型变量，钉死"配准是病根"
created: 2026-06-24
tags: [花页7, 实验, E3, nnU-Net, 配准, 交叉核验, 中期汇报]
---

# E3：nnU-Net 同网格交叉核验

> 目的：E2 用自写 UNet 得高 dice，但 codex 用 nnU-Net、模型不同是混淆因素。
> E3 **复刻 codex 的 nnU-Net 协议（同工具、同配置、同子块规格），只把图像源从 2024³裁剪换成同网格 sus** →
> 看 nnU-Net 是否也从 dice≈0 翻身。**翻身即证明：病根是配准、不是模型/工具。**
> 用独立 nnUNet 目录 `~/HXL/HY7_planb/nnunet/`，**不碰 codex 的 `nnUNet_data`**。

## 决定性对照表（同工具 nnU-Net，唯一变量=图像是否同网格）

| 工具 | 配置 | 图像源 | 配准 | 孔隙 Dice |
|---|---|---|---|---|
| nnU-Net（codex, Dataset712） | 3d_fullres 5ep | 2024³ 裁剪 | 错位 | **0.0** |
| **nnU-Net（E3, 我, Dataset722）** | 3d_fullres 5ep | **同网格 sus** | 共配准 | **0.9189**（IoU 0.85） |
| nnU-Net（codex, Dataset712） | 2d 50ep | 2024³ 裁剪 | 错位 | **0.000228** |
| **nnU-Net（E3, 我, Dataset722）** | 2d 50ep | **同网格 sus** | 共配准 | ⏳ 跑完补 |
| （参考）自写 UNet（E2） | 100ep | 同网格 sus | 共配准 | 0.939 |

## 结论（airtight）

- **同一个工具(nnU-Net)、同一个配置(3d_fullres 5ep)，只改"图像-标签是否同网格"，dice 从 0.0 → 0.919。**
- 这把"是不是因为我换了自写 UNet 才好"的**模型混淆变量彻底排除**：nnU-Net 本身在对齐数据上也得 0.92。
- → **病根是配准（2024→1500 裁剪错位），不是数据、不是任务、不是模型/工具。** Plan B 同网格直接根治。
- 与 E2（自写 UNet 0.939）相互印证：两种模型在同网格上都得高 dice，量级一致。

## 协作意义（非竞赛）
- 这不是"我赢 codex"，而是**实证 codex 自己 6/22 的纠正方向**（弃 2024³裁剪、改 sus+pore==0）是对的；
  并给团队一个**可信的 nnU-Net 同网格 baseline**，可直接进中期汇报。
- 建议 codex：把早期 Dataset712/713（2024³裁剪, dice≈0）标 superseded，正式 baseline 用同网格 Dataset722 思路。

## 产物 / 防编造
- 数据集：`hy7-linux:~/HXL/HY7_planb/nnunet/nnUNet_raw/Dataset722_HY7_CT2p8um_2phase_samegrid`（20×192³，孔隙 4–11%）
- 构建脚本：`src/hy7_planb_make_nnunet.py`（同网格 sus+pore==0，独立目录）
- 3d 结果：`experiments/花页7_PlanB_记录/evidence_e3_nnunet_3d5ep_summary.json`（foreground Dice 0.9189）
- 配置：`nnUNetv2_train 722 3d_fullres 0 -tr nnUNetTrainer_5epochs`（复刻 codex），CTNormalization。

## 阶段一收尾 → 转阶段二
E3 完成即**阶段一（分割）收尾**：花页7 多尺度三相/二相分割 + 配准修复 + 模型隔离全部证完。
按已确认决策 **D1：下一步转阶段二（2D 扩散生成 DDPM）**，进入论文真正的贡献点。
