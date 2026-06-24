---
title: 花页7 Plan B —— 多尺度对齐 + 矿物/三相分割 管线
well: 花页7
depth_m: 4199.21
created: 2026-06-23
tags: [花页7, 数字井筒, 分割, PlanB, 对齐]
---

# 花页7 Plan B —— 对齐 + 分割 管线

> 对应 CLAUDE.md「03 数据掌握·多尺度对齐·矿物分割」的前沿部分。
> 数据掌握已完成（3 件 iWork 成品 + `hy7_stats.json` 12 项核校）；本页是**对齐+分割**的可执行管线。

## 1. 立论（Plan B）

跨尺度**原图配准**是真瓶颈。绕过它：服务商「处理图像」里的 `sus / pore / feng`
是**同一处理网格**的产物，天生共配准。直接拿 `sus`(灰度) + `pore/feng`(相掩膜)
做「灰度 → 3 相」分割，不碰原图配准。

## 2. 数据落位（本机，已从外盘拷入，35G，git 忽略）

`data/hy7_volumes/`，uint8，reshape 顺序 `(nz, ny, nx)`：

| key | 文件 | 维度 (z,y,x) | 角色 |
|---|---|---|---|
| `ct14_sus` | ct14_14um/…_14um_SUS.raw | 1600×1620×1620 | **灰度体**（输入） |
| `ct14_pore` | …_14um_pore.raw | 同上 | 孔隙掩膜 |
| `ct14_feng` | …_14um_FENG.raw | 同上 | 裂缝掩膜 |
| `ct14_orig` | …_2024x2024x2024_14.raw | 2024³ | 原始灰度（**异网格**，Plan B 不用） |
| `ct28_sus` | ct28_2p8um/…_2p8um_sus.raw | 1500³ | 灰度体（输入） |
| `ct28_pore` | …_2p8um_pore.raw | 1500³ | 孔隙掩膜（**此尺度无 feng**） |
| `ct28_orig` | …_2024x2024x2024_2p8.raw | 2024³ | 原始灰度（异网格） |

> nano65 tif 序列也已拷入 `nano65/nano_images/`（1019 张）。
> **Maps(12.7G)/FIB tif 栈未拷**——非 CT 体素 Plan B，需要再从外盘/hy7-linux 取。

## 3. 已验证结论（`hy7_planb_io.py inspect` + `check_alignment`）

- `sus` 是**真灰度**（256 级，峰在 ~110–130）；取值 0 的 ~22% = 圆柱塞外方角
  （内切圆占 π/4≈78.5%，角占 21.5%，对得上）。
- `pore/feng` 二值 `{0,255}`，**相标记值 = 0**（与已核校孔隙度同量级；印证
  forensics「pore==0 是真孔隙」）。脚本用已知孔隙度**自动反推**该值，不写死。
- `pore` 与 `feng` 逐切片**重叠 = 0%** → 互斥，可安全合成 3 相标签。
- 标签方案：`0=基质 / 1=孔隙 / 2=裂缝 / 255=ignore`（圆柱外，不计 loss；
  但真孔隙/裂缝即便落在暗区也覆盖 ignore）。
- 灰度切片肉眼可见**页岩纹层**，轴序正确（见 `experiments/hy7_planb/align_check/*.png`）。

## 4. 脚本（`src/`，numpy 部分本机可跑，训练去 Linux）

| 脚本 | 作用 | 依赖 |
|---|---|---|
| `hy7_planb_io.py` | 体素注册表 + memmap 读 + 相值反推 + `inspect` + **在线 patch 采样(`ScaleVolumes`)** | numpy |
| `hy7_planb_check_alignment.py` | 同网格校验 + 互斥性 + 灰度/标签叠加出图 | numpy, matplotlib |
| `hy7_planb_train.py` | 3D U-Net 三相分割，**在线采样直读完整体素**（CE+Dice, ignore=255, AMP） | **torch（hy7-linux）** |
| `hy7_planb_dataset.py` | （**可选**）预烤 `.npz` shards——固化可复现小集合；训练默认不用它 | numpy |

> **35G 本机拷贝的用途 = 腾外盘 + Mac 上 numpy 自检；与训练无关。**
> 训练在 hy7-linux 上**直读** rsync 来的 `HY7_source` 完整体素（`--layout source`），
> 每 epoch 现采 patch，无需预烤数据集、无需本机拷贝。
> `io.py` 用两套路径布局适配 Mac(扁平 local) / Linux(原始嵌套 source)，同一套代码两边跑。

## 5. 执行流程

```bash
# —— 本机(Mac, .venv)：只做验证，已做 ——
.venv/bin/python src/hy7_planb_io.py inspect                      # 解码编码
.venv/bin/python src/hy7_planb_check_alignment.py --scale ct14    # 对齐出图
.venv/bin/python src/hy7_planb_io.py sample --scale ct14 --n 4    # 在线采样自检

# —— 只把小脚本推到 hy7-linux 的 src/（数据本来就在那，已 rsync）——
rsync -avP src/hy7_planb_*.py hy7-linux:/home/user/HXL/HY7_planb/src/

# —— hy7-linux(GPU, RTX 5090, env=nnunet_t28)：直读完整体素在线训练 ——
# 目录结构：HY7_planb/{src,runs,logs}（见 花页7_Linux目录整理记录）
PY=~/miniconda3/envs/nnunet_t28/bin/python        # torch 2.8+cu129, numpy 2.3.5
SRC=~/HXL/HY7_source/吉林大学数据报告归总          # 处理 .raw 已确认齐全
cd ~/HXL/HY7_planb
$PY src/hy7_planb_io.py inspect --root "$SRC" --layout source --key ct14_sus   # 数据可达自检
$PY src/hy7_planb_train.py --scale ct14 --root "$SRC" --layout source \
    --epochs 80 --steps 400 --bs 2 --patch 128 --base 16 --workers 6 --amp
# 若显存吃紧：--bs 1 或 --patch 96。产物：runs/train_ct14/best.pt + trainlog.json
```

> **已在 5090 上冒烟通过（2026-06-23）**：1ep/8步/patch64/base8/AMP，1.7s 出 ckpt；
> 数据可达→解码→在线采样→3D UNet→Dice+CE(ignore)→AMP→存档 全链路打通。
> 见 memory `hy7-planb-linux-training`。
> 若以后真想要冻结的可复现集合，再用 `hy7_planb_dataset.py` 预烤；否则在线采样即可。

## 6. 风险 / 待办

- `ct28` 无 `feng` → 只能 2 相（基质/孔隙）；`ct14` 才有完整 3 相。
- patch 采样是随机+前景筛；若类极不平衡可调 `--min-fg / --bg-keep`，或后续加难例重采。
- **这只是"对齐+分割"那一跳**。下一跳按项目目标：多尺度**融合** → 生成式
  （超分 / 缺失补全 / 沿井深虚拟岩心）。见 [[花页7_多尺度融合_生成式_构想]]（待写）。
- 矿物分割（Amics 长英质/碳酸盐/黏土）是另一条线：标签来自 Amics 矿物图，
  注意粗/精扫基准；与本页的 CT 三相分割不是同一套标签。
