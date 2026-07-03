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

2026-07-01 已保存一份机器生成的完整环境快照到 `experiments/花页7_PlanB_记录/phase2/remote_provenance_20260701/04_environment_snapshot.txt`。后续每次正式训练/采样仍建议随 run 再保存一次同类 stdout。

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

- 原始 `T=0`：φ gen 23.506% vs real 6.405%，S₂ rmse 0.07143，Euler gen 146.24 vs real 127.33
- 标定 `T*=0.98732`：φ 对齐到 6.4%，S₂ rmse 0.00242，但 Euler 207.92 vs real 127.33
- 解释：阈值伪影已修；连通性/聚集是真问题，进入 M7-v3

## 6. 2026-07-01 远程 provenance 核验结果

原始 stdout 已保存到：`experiments/花页7_PlanB_记录/phase2/remote_provenance_20260701/`。

### 6.1 M7 128² 切片数据集

主链数据集为：

```text
/home/user/HXL/HY7_planb/phase2/slices_ct28_128/
```

`meta.json`：

- sha256：`993b1d3220fd81c37aebfe15d4be13cad332f5c49cdf48cc5d0a0d4424ad4c9d`
- size：506 B
- mtime：2026-06-25 09:45 +0800
- 关键内容：`tile=128`、`z_step=6`、`axes=z`、`min_valid=0.999`、`test_frac=0.2`、`seed=42`、`n_train=16600`、`n_test=4150`、test φ mean `6.443%`、test φ median `5.676%`

注意：远程另有 `/home/user/HXL/HY7_planb/phase2/slices_ct28/`，但它是 `tile=256`、`z_step=4`、`n_train=4800`、`n_test=1200` 的旧/备用数据集，不应与 M7 128² DDPM 主链混用。

### 6.2 M7 50ep DDPM 大文件

| 文件 | size_bytes | mtime (+0800) | sha256 |
|---|---:|---|---|
| `/home/user/HXL/HY7_planb/phase2/ddpm_ct28/best.pt` | 252713143 | 2026-06-25 10:50:14 | `ee15bb0ab5a67c1d22ad38b9bbd4f870f42ebb8ed4c41053da8989143449bb98` |
| `/home/user/HXL/HY7_planb/phase2/ddpm_ct28/final.pt` | 252713531 | 2026-06-25 10:55:46 | `12665a44821b59e858640332986fb226d8aa07559e678ddbe58ac42a4b852ba9` |
| `/home/user/HXL/HY7_planb/phase2/ddpm_ct28/samples.npy` | 8388736 | 2026-06-26 17:14:56 | `bc7cfecb572cc250341dbe077f36da802e98f3453f8ec073b0510ed39dfa7a0e` |
| `/home/user/HXL/HY7_planb/phase2/ddpm_ct28/samples_continuous.npy` | 33554560 | 2026-06-26 17:14:56 | `fdd2f264fdfb5127843b38f9e869fb9fb5c7747ac0036dbefb0b4c5b2032996d` |

`ddpm_ct28/train_meta.json` sha256：`1d04c071f3efe1edb4b356fb609966d254d74e3e26c938ed097da5f5b17c4325`，记录 `epochs=50`、`bs=64`、`base=64`、`lr=1e-4`、`best_Lsimple=0.01938`、`params_M=63.15`。该 meta 未记录 seed。

### 6.3 M7-v3 200ep 训练状态

远程已存在并完成训练：

```text
/home/user/HXL/HY7_planb/phase2/ddpm_ct28_200ep/
```

| 文件 | size_bytes | mtime (+0800) | sha256 |
|---|---:|---|---|
| `/home/user/HXL/HY7_planb/phase2/ddpm_ct28_200ep/best.pt` | 252713143 | 2026-06-27 20:46:19 | `f009973ce37228644e6158ed46d9e08b1dfdb8c892754b6e327933b970646a6d` |
| `/home/user/HXL/HY7_planb/phase2/ddpm_ct28_200ep/final.pt` | 252713531 | 2026-06-27 21:51:10 | `4975ed241dc4af15178199ee32370ad39a45763e745fbdda285fc2484634ae78` |

`ddpm_ct28_200ep/train_meta.json` sha256：`6670df671d08be425fc957e7358d21a4c445c0b2685fbb9cba9470b8aced335f`，记录 `epochs=200`、`bs=64`、`base=64`、`lr=1e-4`、`best_Lsimple=0.01881`、`params_M=63.15`。

日志 `/home/user/HXL/HY7_planb/phase2/ddpm_ct28_200ep.log` sha256：`01a6dc7eb837b4df8397bb379bbc7c2e16d0249258ed7f5ac659d22d5d79a2f5`；末行为 `[done] best L_simple=0.0188 -> ddpm_ct28_200ep`。

尚未发现：

```text
/home/user/HXL/HY7_planb/phase2/ddpm_ct28_200ep/samples.npy
/home/user/HXL/HY7_planb/phase2/ddpm_ct28_200ep/samples_continuous.npy
```

因此 200ep 目前只能说明训练已完成，不能说明 S₂/Euler/连通性是否改善。下一步应采样和评估，而不是重跑训练。

### 6.4 远程 JSON verdict 警告

远程 `/home/user/HXL/HY7_planb/phase2/m7v2_calib/calib_result.json` 与 `ddpm_ct28/m7v2_calib/calib_result.json` 的 verdict 仍是旧错判：写作“标定后 S₂/Euler 明显改善”。本地入库版本已修正为“S₂ 明显改善，Euler 变差”。后续同步远程文件时不能用远程旧 verdict 覆盖本地修正版。

## 7. M7-v3 远程运行提醒

M7-v3 第一步 cheap control（50ep→200ep）已完成训练；当前缺口是对 `ddpm_ct28_200ep/best.pt` 采样并复用 eval/calib 口径验证 S₂/Euler/连通性。若继续执行，应优先采样评估，不要重复启动 200ep 训练。

已核实输出目录：

```text
/home/user/HXL/HY7_planb/phase2/ddpm_ct28_200ep/
```

建议仓库轻量证据目录：

```text
experiments/花页7_PlanB_记录/phase2/m7v3_200ep/
```

远程长任务注意：先使用防睡眠/断连策略（例如 caffeinate/setsid 或远程等价方案），并把 stdout/stderr 保存到日志文件；不要只依赖终端滚动输出。

## 8. requirements-remote.txt 说明

`requirements-remote.txt` 是远程 `nnunet_t28` 环境的完整 `pip freeze` 快照，不等同于最小可移植安装文件。`torch==2.8.0+cu129`、`torchvision==0.23.0+cu129`、`torchaudio==2.8.0+cu129` 复建时可能需要指定 PyTorch CUDA wheel 源或复用 conda 环境；后续可另建最小 `requirements-m7-minimal.txt`。
