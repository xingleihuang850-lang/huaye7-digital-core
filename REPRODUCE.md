# 复现指南：花页7阶段二 M7-v2/M7-v3

> 约束：本草稿依据只读检查 `CLAUDE.md`、`notes/22_阶段二_M7v2_阈值标定诊断.md`、`notes/24_阶段二_M7v3_连通性迭代设计.md`、`experiments/花页7_PlanB_记录/phase2/README.md`、`src/hy7_phase2_*.py`、`.gitignore`、`requirements.txt`。未在仓库中找到的具体历史运行命令不编造，以下命令链按脚本 argparse 给出；待从远程 shell history / run log 核对后可去掉 TODO。

## 1. 主线与当前阶段

唯一主线：硕士论文《基于融合多尺度数据的页岩数字岩心-井筒建模》。四阶段为：

1. 分割
2. 2D 扩散生成
3. 多模态 3D 数字岩心
4. 数字井筒

当前复现目标是阶段二 M7-v2：先固化 DDPM 二值孔隙生成的阈值标定诊断链条，再进入 M7-v3 连通性迭代。

M7-v2 已确认结论：

- T* = 0.98732
- S2 rmse：0.07143 → 0.00242，说明 T=0 二值化导致的阈值伪影已基本修复
- Euler：T* 下 207.92 vs real 127.33，说明孔隙连通性/聚集仍是真问题
- 下一步 M7-v3：先做 50ep → 200ep 对照验证欠训练；根本方向是生成灰度介质 sus 本身，或生成 `[sus,pore]` 双通道，而不是把真实 sus 作为条件输入去分割 pore

## 2. 本机环境（macOS，轻量开发/验证）

工程根：

```bash
cd /Users/hxl/Documents/Hermes工作区/01_Claude接管剩余工作/claude
```

本机 Python 环境：

- `.venv/` 为 uv 管理的 Python 3.12 环境
- 跑脚本：`.venv/bin/python src/xxx.py`
- 装包：`uv pip install --python .venv/bin/python <包>`
- 重建：`uv venv --python 3.12 && uv pip install --python .venv/bin/python -r requirements.txt`
- 本机主要用于轻量数据处理、代码检查、图表/指标验证；阶段二 DDPM 训练/采样以远程 GPU 环境为主

`requirements.txt` 当前记录的关键本机包：

- torch 2.12.1
- torchvision 0.27.1
- numpy 2.5.0
- scipy 1.18.0
- scikit-image 0.26.0
- matplotlib 3.11.0
- pandas 3.0.3
- duckdb 1.5.4
- tifffile 2026.6.1

注意：`src/hy7_phase2_ddpm.py` 需要 `diffusers`，但本机 `requirements.txt` 尚未钉 diffusers；不要在未核实远程版本前猜测写入。

## 3. 远程 GPU 环境（训练/采样主环境）

远程别名与路径：

- `hy7-linux`：Tailscale 通道，`100.127.180.10`
- `hy7-linux-lan`：局域网通道，`192.168.1.164`；当前记录为超时，传大文件优先但需先确认可达
- user：`user`
- 花页7远程数据根：`/home/user/HXL/`
- 服务商数据本体：`/home/user/HXL/HY7_source/吉林大学数据报告归总`
- 阶段二远程实验区：`/home/user/HXL/HY7_planb/phase2/`
- M7 二值 DDPM 输出目录记录：`/home/user/HXL/HY7_planb/phase2/ddpm_ct28/`

已知远程关键版本：

- Python 3.11.15
- torch 2.8.0+cu129
- diffusers 0.38.0
- numpy 2.3.5
- scipy 1.17.1
- scikit-image 0.26.0
- SimpleITK 2.5.3
- nnunetv2 2.6.4
- GPU RTX 5090，driver 580.159.03，显存 32607 MiB

远程环境详见`docs/environment-remote.md`。

## 4. 数据路径

### 4.1 本地仓库与轻量原始统计

- 目标仓库：`/Users/hxl/Documents/Hermes工作区/01_Claude接管剩余工作/claude`
- `data/hy7_raw/`：花页7服务商统计 xlsx 的本地轻量副本，git 忽略
- `data/hy7_amics_inspect/`：Amics 局部核查原始/半原始材料，git 忽略
- `experiments/花页7_PlanB_记录/phase2/`：阶段二 DDPM 轻量证据区，保存可复核指标、图与大文件来源记录

### 4.2 外盘原始数据

花页7外盘原始数据根：

```text
/Volumes/Untitled/吉林大学数据报告归总/
```

仅 6 个尺度文件夹是服务商原件：

- `Amics矿物整体扫描25um+精细扫描1um`
- `微米CT柱塞扫描-14um`
- `微米CT精细扫描-2p8um`
- `纳米CT扫描-65nm`
- `FIB-SEM聚焦离子束扫描-8p589nm`
- `Maps整体扫描200nm+精细扫描10nm`

不要把 `_analysis/`、PPT、AI 汇总表等派生物误当原始数据。

### 4.3 远程数据与 M7-v2 大文件

远程记录：

```text
hy7-linux:~/HXL/HY7_planb/phase2/ddpm_ct28/samples_continuous.npy
```

`phase2/README.md` 明确：`samples.npy`、`samples_continuous.npy`、`ckpt/*.pt` 等训练/采样大文件不直接入 git；只记录路径、sha256、生成命令与日期。

## 5. 阶段二 M7-v2 命令链

以下命令按当前脚本接口整理。`<...>` 为需要按实际机器替换或从历史记录核对的路径。

### 5.1 生成 train/test 二值孔隙切片

脚本：`src/hy7_phase2_make_slices.py`

输入：同网格 ct28 体，依赖 `hy7_planb_io.ScaleVolumes`。输出为：

- `train.npy`
- `test.npy`
- `meta.json`

命令模板：

```bash
python src/hy7_phase2_make_slices.py \
  --scale ct28 \
  --root /home/user/HXL/HY7_source/吉林大学数据报告归总 \
  --layout source \
  --tile 128 \
  --z-step <TODO: M7 实际 z-step> \
  --axes <TODO: M7 实际 axes，例如 z 或 zyx> \
  --min-valid 0.999 \
  --test-frac 0.2 \
  --out /home/user/HXL/HY7_planb/phase2/ct28_tiles \
  --seed 42
```

TODO：从远程实际 `meta.json` 或历史日志补齐 M7 当时的 `--z-step`、`--axes`、`--out` 精确值。本草稿不猜。

### 5.2 训练 M7 二值孔隙 DDPM

脚本：`src/hy7_phase2_ddpm.py train`

模型与算法：

- diffusers `UNet2DModel`
- 单通道输入/输出
- `DDPMScheduler(num_train_timesteps=1000, beta_schedule="linear", beta_start=1e-4, beta_end=0.02)`
- ε-预测 L_simple
- 二值孔隙标签缩放到 `[-1, 1]`
- M7-v2 记录的基线为 50 ep，最佳检查点 `ddpm_ct28/best.pt`

命令模板：

```bash
python src/hy7_phase2_ddpm.py train \
  --data /home/user/HXL/HY7_planb/phase2/ct28_tiles \
  --out /home/user/HXL/HY7_planb/phase2/ddpm_ct28 \
  --epochs 50 \
  --bs <TODO: M7 实际 batch size> \
  --base 64 \
  --lr 1e-4 \
  --amp \
  --seed <TODO: M7 训练 seed> \
  --sample-every <TODO: M7 实际 sample interval>
```

TODO：从远程 `train_meta.json`、日志或 shell history 补齐 `--bs`、训练 seed、`--sample-every`。

### 5.3 采样 512 张并保存连续输出

脚本：`src/hy7_phase2_ddpm.py sample`

M7-v2 关键点：必须加 `--continuous`，保存 `samples_continuous.npy`，否则无法做阈值标定。

命令模板：

```bash
python src/hy7_phase2_ddpm.py sample \
  --ckpt /home/user/HXL/HY7_planb/phase2/ddpm_ct28/best.pt \
  --out /home/user/HXL/HY7_planb/phase2/ddpm_ct28 \
  --n 512 \
  --size 128 \
  --base 64 \
  --bs <TODO: M7 实际 sampling batch size> \
  --seed 123 \
  --continuous
```

输出：

- `/home/user/HXL/HY7_planb/phase2/ddpm_ct28/samples.npy`
- `/home/user/HXL/HY7_planb/phase2/ddpm_ct28/samples_continuous.npy`
- `/home/user/HXL/HY7_planb/phase2/ddpm_ct28/samples_grid.png`

### 5.4 原始 T=0 口径评估 + naive baseline

脚本：`src/hy7_phase2_eval.py`

命令模板：

```bash
python src/hy7_phase2_eval.py \
  --real /home/user/HXL/HY7_planb/phase2/ct28_tiles/test.npy \
  --gen /home/user/HXL/HY7_planb/phase2/ddpm_ct28/samples.npy \
  --out experiments/花页7_PlanB_记录/phase2/eval_v2 \
  --n 512 \
  --rmax 48 \
  --seed 0
```

已入档轻量结果：`experiments/花页7_PlanB_记录/phase2/eval_v2/metrics.json`

关键指标：

- real φ mean = 6.405%
- gen φ mean = 23.506%
- naive φ mean = 6.408%
- S2 rmse gen = 0.07143
- S2 rmse naive = 0.00493
- Euler real = 127.33
- Euler gen = 146.24
- Euler naive = 890.16
- max connected component fraction：real 0.0597，gen 0.1588，naive 0.0048

### 5.5 M7-v2 阈值标定诊断

脚本：`src/hy7_phase2_threshold_calib.py`

命令模板：

```bash
python src/hy7_phase2_threshold_calib.py \
  --real /home/user/HXL/HY7_planb/phase2/ct28_tiles/test.npy \
  --cont /home/user/HXL/HY7_planb/phase2/ddpm_ct28/samples_continuous.npy \
  --out experiments/花页7_PlanB_记录/phase2/m7v2_calib \
  --target_phi 6.4 \
  --n 512 \
  --rmax 48 \
  --seed 0
```

已入档轻量结果：`experiments/花页7_PlanB_记录/phase2/m7v2_calib/calib_result.json`

关键指标：

- T_star = 0.98732
- target_phi_pct = 6.4
- T=0：φ mean 23.506%，Euler 146.24，S2 rmse 0.07143
- T*：φ mean 6.4%，Euler 207.92，S2 rmse 0.00242
- verdict：阈值伪影已修但连通性真错仍在；下一步修聚集/连通性

## 6. M7-v3 入口

M7-v3 设计见 `notes/24_阶段二_M7v3_连通性迭代设计.md`。

### 6.1 步 A：50ep → 200ep cheap control

目的：只改变训练 epoch，隔离欠训练变量。若 Euler 向 real 127.33 收敛，说明训练不足是部分原因；若不改善，说明二值目标信息不足，需要 B1/B2。

命令模板：

```bash
python src/hy7_phase2_ddpm.py train \
  --data /home/user/HXL/HY7_planb/phase2/ct28_tiles \
  --out /home/user/HXL/HY7_planb/phase2/ddpm_ct28_200ep \
  --epochs 200 \
  --bs <同 M7> \
  --base 64 \
  --lr 1e-4 \
  --amp \
  --seed <同 M7> \
  --sample-every <TODO>
```

之后复用采样、`hy7_phase2_eval.py`、`hy7_phase2_threshold_calib.py`，新轻量证据建议放：

```text
experiments/花页7_PlanB_记录/phase2/m7v3_200ep/
```

### 6.2 步 B：灰度介质生成或双通道联合生成

方向：

- B1 灰度生成：DDPM 从噪声生成连续灰度 ct28 sus 切片；下游再阈值/分割得到 pore，并用 φ/S2/Euler/连通簇评估
- B2 双通道联合生成：DDPM 从噪声联合生成 `[sus,pore]`，让孔隙与灰度语境绑定

注意：真实 sus 输入 → pore 输出是分割，不是生成；不应作为阶段二生成式贡献的主路线。

## 7. 哪些产物入 git，哪些不入 git

### 7.1 应入 git / 可考虑入 git

- 源码：`src/hy7_phase2_*.py`、相关工具脚本
- 设计与复现实验笔记：`notes/*.md`
- 轻量证据说明：`experiments/花页7_PlanB_记录/phase2/README.md`
- 轻量指标 JSON：如 `experiments/花页7_PlanB_记录/phase2/eval_v2/metrics.json`、`m7v2_calib/calib_result.json`
- 轻量图表 PNG：如 `fig_eval.png`、`fig_calib.png`（若大小适中且用于证据留痕）
- 大文件清单/sha256/命令记录：建议用 md/txt 记录，不提交 `.npy`/`.pt` 本体

### 7.2 不入 git

`.gitignore` 与 phase2 README 已明确下列不入 git：

- 外盘/软链接数据：`/GJ5-15data`、`/nnunet_pipeline`、`/data/raw_stats`
- 花页7本地轻量原始 xlsx 副本：`/data/hy7_raw/`
- Amics 核查原始/半原始材料：`/data/hy7_amics_inspect/`
- DuckDB 与向量库：`/data/warehouse.db`、`/data/*.duckdb`、`/vectorstore/`
- 可重建分析产物：`/experiments/figures/`、`/experiments/master_stats.json`、`/experiments/hy7_figures/`、`/experiments/hy7_stats.json`、`/deliverables/`
- 大体积体素/训练中间产物：`/data/hy7_volumes/`、`/data/hy7_planb/`、`/experiments/hy7_planb/`
- 大文件：`*.tif`、`*.tiff`、`*.nii`、`*.nii.gz`
- Python 环境与缓存：`.venv/`、`__pycache__/`、`*.pyc`
- Obsidian 本地 UI 状态：`/notes/.obsidian/`
- 文献 PDF：`/literature/*.pdf`
- 阶段二训练/采样大文件：`samples.npy`、`samples_continuous.npy`、`ckpt/*.pt`、`best.pt`、`final.pt` 等

## 8. 待补齐 TODO

1. 从远程实际 `meta.json` / `train_meta.json` / 日志补齐 M7 精确命令参数：`--z-step`、`--axes`、`--bs`、训练 seed、`--sample-every`。
2. 给 `samples.npy`、`samples_continuous.npy`、`best.pt`、`final.pt` 等远程大文件补 sha256、文件大小、生成日期。
3. 如需本地完整复现 DDPM，先确认远程 `diffusers==0.38.0` 与本机 Python 3.12/torch 2.12.1 兼容，再更新依赖策略。
4. 若 `hy7-linux-lan` 恢复，记录 LAN 传输路径；否则继续使用 `hy7-linux` Tailscale 通道。
