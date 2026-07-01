# 远程环境记录 — hy7-linux / 阶段二 DDPM

> 状态说明：本草稿使用已知环境版本与仓库上下文整理；未再次读取远程私钥、token、auth 或 `.env` 内容。

## 1. 远程主机与访问状态

远程主机：

- SSH 别名：`hy7-linux`
- Tailscale IP：`100.127.180.10`
- 用户：`user`
- 主要用途：花页7阶段二 DDPM 训练/采样与后续 M7-v3 实验

局域网通道：

- SSH 别名：`hy7-linux-lan`
- LAN IP：`192.168.1.164`
- 当前记录：`hy7-linux-lan` 超时；`hy7-linux` / Tailscale 可访问
- 建议：大文件 rsync 优先尝试 LAN，但每次传输前先做连通性检查；LAN 不通时使用 Tailscale

SSH 密钥记录：仓库上下文提到密钥为 `~/.ssh/hy7_linux_ed25519`，本草稿不读取密钥内容。

## 2. 远程数据与实验路径

远程数据根：

```text
/home/user/HXL/
```

花页7服务商数据本体：

```text
/home/user/HXL/HY7_source/吉林大学数据报告归总
```

阶段二实验区：

```text
/home/user/HXL/HY7_planb/phase2/
```

M7-v2 已知二值 DDPM 输出目录：

```text
/home/user/HXL/HY7_planb/phase2/ddpm_ct28/
```

已知关键大文件：

```text
/home/user/HXL/HY7_planb/phase2/ddpm_ct28/samples.npy
/home/user/HXL/HY7_planb/phase2/ddpm_ct28/samples_continuous.npy
/home/user/HXL/HY7_planb/phase2/ddpm_ct28/best.pt
/home/user/HXL/HY7_planb/phase2/ddpm_ct28/final.pt
```

注意：上述 `.npy` / `.pt` 属训练与采样大文件，不入 git；应在仓库中只记录远程路径、sha256、文件大小、生成命令与日期。

## 3. 远程软件版本快照

以下为 2026-07-01 通过 `hy7-linux` / conda env `nnunet_t28` 采集或核实的当前记录；后续正式实验仍应把完整命令输出保存到实验 evidence：

| 组件 | 版本 |
|---|---|
| Python | 3.11.15 |
| torch | 2.8.0+cu129 |
| diffusers | 0.38.0 |
| numpy | 2.3.5 |
| scipy | 1.17.1 |
| scikit-image | 0.26.0 |
| SimpleITK | 2.5.3 |
| nnunetv2 | 2.6.4 |

GPU/驱动：

| 项 | 记录 |
|---|---|
| GPU | RTX 5090 |
| Driver | 580.159.03 |
| 显存 | 32607 MiB |

TODO：从远程补一份机器生成的完整环境快照，例如：

```bash
python --version
python - <<'PY'
import torch, diffusers, numpy, scipy, skimage, SimpleITK
print('torch', torch.__version__)
print('cuda available', torch.cuda.is_available())
print('cuda', torch.version.cuda)
print('diffusers', diffusers.__version__)
print('numpy', numpy.__version__)
print('scipy', scipy.__version__)
print('skimage', skimage.__version__)
print('SimpleITK', SimpleITK.Version())
PY
python -m nnunetv2 --version 2>/dev/null || nnUNetv2_plan_and_preprocess --version 2>/dev/null || true
nvidia-smi
```

## 4. 与本机环境的差异

本机 macOS 环境：

- `.venv/` 为 uv 管理的 Python 3.12
- `requirements.txt` 当前记录 torch 2.12.1、numpy 2.5.0、scipy 1.18.0、scikit-image 0.26.0
- 本机未在 requirements 中钉 diffusers
- 本机用于轻量开发/验证；大规模训练与采样在远程 GPU 上完成

远程环境：

- Python 3.11.15
- torch 2.8.0+cu129 + RTX 5090 CUDA 环境
- diffusers 0.38.0，当前阶段二 DDPM 脚本实际依赖该包

复现原则：

1. 训练/采样优先使用远程环境。
2. 本机如需跑 `src/hy7_phase2_ddpm.py`，先按远程版本策略安装并记录 diffusers，避免猜测依赖。
3. 指标评估脚本 `src/hy7_phase2_eval.py`、`src/hy7_phase2_threshold_calib.py` 主要依赖 numpy/scipy/scikit-image/matplotlib，可在本机或远程跑，但要固定输入 `.npy` 与 seed。

## 5. M7-v2 远程复现关联文件

代码：

- `src/hy7_phase2_make_slices.py`
- `src/hy7_phase2_ddpm.py`
- `src/hy7_phase2_eval.py`
- `src/hy7_phase2_threshold_calib.py`

轻量证据：

- `experiments/花页7_PlanB_记录/phase2/README.md`
- `experiments/花页7_PlanB_记录/phase2/eval_v2/metrics.json`
- `experiments/花页7_PlanB_记录/phase2/m7v2_calib/calib_result.json`

结果口径：

- 原始 `T=0`：φ gen 23.506% vs real 6.405%，S2 rmse 0.07143，Euler gen 146.24 vs real 127.33
- 标定 `T*=0.98732`：φ 对齐到 6.4%，S2 rmse 0.00242，但 Euler 207.92 vs real 127.33
- 解释：阈值伪影已修；连通性/聚集是真问题，进入 M7-v3

## 6. 建议补充的远程 provenance

后续建议在不提交大文件的前提下补齐：

```bash
sha256sum /home/user/HXL/HY7_planb/phase2/ddpm_ct28/samples.npy
sha256sum /home/user/HXL/HY7_planb/phase2/ddpm_ct28/samples_continuous.npy
sha256sum /home/user/HXL/HY7_planb/phase2/ddpm_ct28/best.pt
sha256sum /home/user/HXL/HY7_planb/phase2/ddpm_ct28/final.pt
ls -lh /home/user/HXL/HY7_planb/phase2/ddpm_ct28/
```

并记录：

- 生成命令
- 生成日期
- 训练日志路径
- `train_meta.json` 内容
- 切片数据 `meta.json` 内容
- 远程环境快照命令输出

## 7. M7-v3 远程运行提醒

M7-v3 第一步为 cheap control：二值 DDPM 从 50ep 加到 200ep，仅改变 epoch，其余 data/seed/base/bs/lr/amp 尽量保持不变。

建议输出目录：

```text
/home/user/HXL/HY7_planb/phase2/ddpm_ct28_200ep/
```

建议仓库轻量证据目录：

```text
experiments/花页7_PlanB_记录/phase2/m7v3_200ep/
```

远程长任务注意：先使用防睡眠/断连策略（例如 caffeinate/setsid 或远程等价方案），并把 stdout/stderr 保存到日志文件；不要只依赖终端滚动输出。

## 7. requirements-remote.txt 说明

`requirements-remote.txt` 是远程 `nnunet_t28` 环境的完整 `pip freeze` 快照，不等同于最小可移植安装文件。`torch==2.8.0+cu129`、`torchvision==0.23.0+cu129`、`torchaudio==2.8.0+cu129` 复建时可能需要指定 PyTorch CUDA wheel 源或复用 conda 环境；后续可另建最小 `requirements-m7-minimal.txt`。
