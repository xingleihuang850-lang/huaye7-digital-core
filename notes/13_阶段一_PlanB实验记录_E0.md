---
title: 花页7 Plan B 实验记录（逐步骤·可追溯·防编造）
well: 花页7
created: 2026-06-23
tags: [花页7, 实验记录, 防编造, PlanB]
---

# 花页7 Plan B 实验记录

> **原则**：每个数字/图都标来源；区分 `[测]`实测 / `[核]`核验 / `[假]`假设；
> 命令可复现；产物有路径+checksum。**不编造**——本页所有数字均来自下列证据文件或可复现命令。
> 关联方法说明见 [[12_阶段一_PlanB对齐分割管线]]；Linux 环境见 memory `hy7-planb-linux-training`。

## 证据清单 `experiments/花页7_PlanB_记录/`（入 git）

| 文件 | 内容 | 由谁/如何产生 |
|---|---|---|
| `evidence_inspect_volumes.json` | 7 个体素的取值分布、相值反推 | `src/hy7_planb_io.py inspect` |
| `evidence_align_summary_ct14.json` | 三体同 shape、孔隙∩裂缝重叠=0% | `hy7_planb_check_alignment.py --scale ct14` |
| `ct14_z0240/0613/0986/1360.png` | 灰度+标签叠加图（4 张深度切片） | 同上 |
| `evidence_trainlog_ct14.json` | 100 epoch 全曲线（原始记录） | `hy7_planb_train.py`（Linux 5090） |
| `evidence_training_meta.txt` | 机器/env/best.pt sha256/脚本 sha256/数据源 | Linux 快照 |
| `evidence_src_sha256_mac.txt` | 本机脚本 sha256（与 Linux 比对） | `shasum` |

## 时间线（2026-06-23）

### 0. 数据落位
- **做**：从外盘 `/Volumes/Untitled/吉林大学数据报告归总/` `cp` 7 个 CT `.raw` → 本机 `data/hy7_volumes/`（35G）。
- **来源**：服务商欧勒姆能源测试原件（与 Linux `HY7_source` 为同一份，rsync）。
- **坑**：首拷用 `rsync --info=progress2` 失败（macOS openrsync 不支持），改 `cp` 重拷。`[测]`
- **用途澄清**：此 35G 仅为「腾外盘 + Mac 自检」，**与训练无关**（训练直读 Linux）。

### 1. 维度确认 `[测][核]`
- ct14 = 1600×1620×1620（字节 4,199,040,000 = 乘积 ✓）；ct28 = 1500³（3,375,000,000 ✓）。
- **依据**：文件名「AxBxC」+ `stat` 字节数交叉验证（脚本 `open_memmap` 内置该校验）。
- **轴序**：`reshape(nz,ny,nx)` 是 `[假]`——字节总数只能证明体积，不能证明轴排列；由步骤 3 叠加图**视觉确认**（图像连贯、非错乱），非形式证明。

### 2. 编码解码（防编造关键）`[测][核]`
- **命令**：`python src/hy7_planb_io.py inspect`（产物 `evidence_inspect_volumes.json`）。
- **结论**：`sus`=真灰度（256 级；取值 0 占 ~22.4% = 圆柱塞外方角，π/4≈78.5% 为圆、角占 21.5%，几何吻合）；`pore/feng`=二值 `{0,255}`，**相标记值=0**。
- **相值=0 的依据**：用**已核校总孔隙度**（ct14 1.558%，源自 `src/verify_hy7.py` 逐切片复现）反推——全体反推 pore 0.73% + feng 0.46% ≈ 1.2%（`evidence_inspect_volumes.json` 全体 val=0 占比），与 1.558% 同量级。**不是猜，是与独立核校值对齐。** 印证 forensics「pore==0 是真孔隙」。

### 3. 对齐自检 `[测]`
- **命令**：`python src/hy7_planb_check_alignment.py --scale ct14`。
- **结论**：三组件体同 shape (1600,1620,1620)；孔隙∩裂缝**逐切片重叠 = 0%**（互斥，可合 3 相）；叠加图肉眼见页岩纹层、轴序正确。
- **产物**：`evidence_align_summary_ct14.json` + 4 张 PNG。

### 4. 在线采样验证 `[测]`
- **命令**：`python src/hy7_planb_io.py sample --scale ct14`。
- **结论**：3 相标签正确、含 ignore、`norm=(131.5,29.0)`；**Mac 与 Linux 同数据同种子逐字节一致**。

### 5. Linux 环境/数据核实 `[测][核]`
- 数据在 `~/HXL/HY7_source/吉林大学数据报告归总/`：ct14 三 raw(各4G)、ct28 两 raw(各3.2G) 齐全。
- env `nnunet_t28`：torch 2.8.0+cu129 / numpy 2.3.5 / RTX 5090 / driver 580.159.03。
- **完整性**：Linux 上 4 脚本 sha256 **与本机 `src/` 逐字节一致**（`evidence_training_meta.txt` 11–15 行 == `evidence_src_sha256_mac.txt`）→「训练用的就是仓库这份代码」。

### 6. 冒烟/探针 `[测]`
- 冒烟：1ep/8步/patch64/base8/AMP → 1.7s 出 ckpt。
- 显存探针：patch128/base16/bs2 → 峰值 **3410 MiB / 32607**（监测命令循环采 `nvidia-smi`）。

### 7. 正式训练 `[测]`（原始记录 = `evidence_trainlog_ct14.json`）
- **确切命令**：
  ```
  python hy7_planb_train.py --scale ct14 --root ~/HXL/HY7_source/吉林大学数据报告归总 \
      --layout source --epochs 100 --steps 400 --bs 4 --patch 128 --base 32 \
      --workers 8 --val-n 60 --amp
  ```
- **环境**：nnunet_t28 / RTX 5090 / torch 2.8+cu129。
- **结果**（dice，验证集 60 patch 固定 seed=12345）：

  | epoch | 基质 | 孔隙 | 裂缝 | 均值 |
  |---|---|---|---|---|
  | 1 | 0.913 | 0.195 | 0.014 | 0.374 |
  | 10 | 0.995 | 0.771 | 0.418 | 0.728 |
  | 50 | 0.996 | 0.817 | 0.536 | 0.783 |
  | **100(best)** | **0.998** | **0.924** | **0.571** | **0.831** |
- **产物**：`best.pt`（Linux，22,401,037 B，sha256 `ed6fc55e24ce69cdca1632132bb897f7cd5b760a180e35ccad4735362e56fc1f`）。
- **耗时**：~19.8s/epoch ×100 ≈ 33 min；显存 12.1G/32.6G、GPU 100%。

## 局限与诚实声明（不掩盖）

1. **训练非逐位复现**：`train.py` 在线采样用 `np.random.default_rng()` **未固定种子**，重训 dice 会有小幅差异（趋势/量级稳定）。验证集固定 seed=12345 可复现。如需逐位复现需固定训练种子——**当前未做**。
2. **轴序为视觉验证**，非形式证明（见步骤 1）。
3. **裂缝 dice 0.571 未收敛到顶**，曲线末端仍升——是基线，非终值。
4. **best.pt 未入 git**（22MB），仅记 sha256 + 复现命令；模型本体在 `hy7-linux:~/HXL/HY7_planb/...`。
5. 本次所有代码/记录**截至本页写时尚未 git commit**（待用户确认后提交）。
6. **空间边界**：E0 的训练和固定验证 patch 都来自同一 ct14 体，历史未保存坐标或 buffer；Dice 仅为同体内部 patch 验证，不是空间独立、无训练-验证重叠或跨体/跨井泛化结论。

## 数字溯源速查
- 多尺度孔隙度 1.558/7.182% → `src/verify_hy7.py` + `experiments/hy7_stats.json`（既往，12 项核校）。
- 相值=0 → 步骤 2，与上面孔隙度对齐。
- dice 0.831 → 步骤 7，`evidence_trainlog_ct14.json` 原始记录。
