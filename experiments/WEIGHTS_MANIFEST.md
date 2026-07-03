# 权重与大产物 Manifest（不入权重，仅登记线索）

> 本文件只记录当前已知路径线索与待补字段；不包含权重内容。  
> 目标仓库：`/Users/hxl/Documents/Hermes工作区/01_Claude接管剩余工作/claude`。  
> 远程主线机器线索：`hy7-linux` / `hy7-linux-lan`，用户 `user`，花页7实验主目录多见于 `~/HXL/HY7_planb/`。

## 0. 记录规范（建议正式 manifest 采用）

每个权重/大样本文件至少记录：

| 字段 | 含义 |
|---|---|
| `id` | 稳定编号，如 `M7-DDPM-ct28-50ep-best` |
| `stage` | 阶段，如 `phase2` |
| `experiment` | 实验名，如 `M7 2D DDPM MVP` |
| `artifact_type` | `weight` / `sample` / `continuous_sample` / `dataset_meta` / `run_config` |
| `remote_path` | 远程路径，建议用 `hy7-linux:~/...` 形式 |
| `local_path` | 如有本地副本则填；无则 `TBD` |
| `in_git` | 是否入 git；权重/大样本通常 `no` |
| `sha256` | 文件 sha256；未知填 `TBD`，不要猜 |
| `size_bytes` | 文件大小；未知填 `TBD` |
| `mtime` | 文件修改时间；未知填 `TBD` |
| `git_commit` | 训练/采样所用代码 commit；未知填 `TBD` |
| `script` | 训练/采样/评估脚本 |
| `run_config` | epochs、seed、bs、lr、model、scheduler、阈值等；可指向 JSON/YAML/命令行 |
| `source_data` | 数据来源/切片集/体素路径线索 |
| `evidence` | 对应轻量证据 JSON/PNG/笔记 |
| `status` | `known` / `needs_hash` / `needs_remote_verify` / `deprecated` |
| `notes` | 口径说明和禁忌 |

正式 manifest 应遵守：
- 不提交 `.pt`、`.pth`、`.ckpt`、`.npy` 等大文件本体。
- 不记录任何 token、私钥、认证文件内容。
- 路径、sha256、大小必须来自实际命令输出；未知字段明确标 `TBD`。
- 同一实验的不同二值化阈值口径必须分开说明，尤其 M7 T=0、M7 eval_v2、M7-v2 T*。

## 1. 当前已知条目草稿

### 1.1 M7 50ep DDPM 权重（ct28 pore mask, phase2）

| 字段 | 内容 |
|---|---|
| `id` | `M7-DDPM-ct28-50ep-best` |
| `stage` | `phase2` |
| `experiment` | `M7 — 2D DDPM 生成 ct28 孔隙结构 MVP` |
| `artifact_type` | `weight` |
| `remote_path` | `hy7-linux:~/HXL/HY7_planb/phase2/ddpm_ct28/best.pt` |
| `local_path` | `TBD` |
| `in_git` | `no` |
| `sha256` | `ee15bb0ab5a67c1d22ad38b9bbd4f870f42ebb8ed4c41053da8989143449bb98`（2026-07-01 远程实测） |
| `size_bytes` | `252713143` |
| `mtime` | `2026-06-25 10:50:14 +0800` |
| `git_commit` | `TBD`（远程 `/home/user/HXL/HY7_planb` 非 git 工作树；需记录本地同步代码 commit） |
| `script` | `src/hy7_phase2_ddpm.py train` |
| `run_config` | 远程 `train_meta.json`：size=128、n_train=16600、epochs=50、base=64、bs=64、lr=1e-4、best_Lsimple=0.01938、params_M=63.15；seed 未写入 train_meta，当前按既有记录为 42；目录网格为 `grid_ep010...050`，sample-every=10。 |
| `source_data` | `/home/user/HXL/HY7_planb/phase2/slices_ct28_128/`，切片器 `src/hy7_phase2_make_slices.py`；meta 实测 tile=128、z_step=6、axes=z、seed=42、16600 train / 4150 test。 |
| `evidence` | `experiments/花页7_PlanB_记录/phase2/metrics.json`、`fig_eval.png`、`samples_grid.png`、`real_grid.png`；笔记 `notes/21_阶段二_M7_DDPM_MVP结果.md`。 |
| `status` | `known_remote_verified_20260701` |
| `notes` | 首基线质量未达标：T=0 口径 gen φ 23.506% vs real 6.405%，过度生成孔隙约 3.7×。 |

### 1.2 M7 50ep DDPM 采样结果：二值/默认样本

| 字段 | 内容 |
|---|---|
| `id` | `M7-DDPM-ct28-50ep-samples-T0` |
| `stage` | `phase2` |
| `experiment` | `M7 — 2D DDPM MVP sampling` |
| `artifact_type` | `sample` |
| `remote_path` | `hy7-linux:~/HXL/HY7_planb/phase2/ddpm_ct28/samples.npy` |
| `local_path` | `TBD` |
| `in_git` | `no` |
| `sha256` | `bc7cfecb572cc250341dbe077f36da802e98f3453f8ec073b0510ed39dfa7a0e` |
| `size_bytes` | `8388736` |
| `mtime` | `2026-06-26 17:14:56 +0800` |
| `git_commit` | `TBD`（远程非 git 工作树） |
| `script` | `src/hy7_phase2_ddpm.py sample`；评估 `src/hy7_phase2_eval.py` |
| `run_config` | 采样 1000 reverse steps；512 张；seed=123（M7/M7-v2 笔记指向同 seed）；二值化阈值 T=0。具体命令行待补。 |
| `source_data` | 权重 `M7-DDPM-ct28-50ep-best`；真实对照为 test set 512 tiles。 |
| `evidence` | `experiments/花页7_PlanB_记录/phase2/metrics.json`；`experiments/花页7_PlanB_记录/phase2/eval_v2/metrics.json`；`samples_grid.png`。 |
| `status` | `known_remote_verified_20260701` |
| `notes` | `eval_v2/` 仍是 T=0 原始口径，只是补了 naive baseline 与 connectivity 指标；不要和 T* 标定结果混读。 |

### 1.3 M7-v2 连续采样结果：`samples_continuous.npy`

| 字段 | 内容 |
|---|---|
| `id` | `M7-v2-DDPM-ct28-50ep-samples-continuous` |
| `stage` | `phase2` |
| `experiment` | `M7-v2 阈值标定诊断` |
| `artifact_type` | `continuous_sample` |
| `remote_path` | `hy7-linux:~/HXL/HY7_planb/phase2/ddpm_ct28/samples_continuous.npy` |
| `local_path` | `TBD` |
| `in_git` | `no` |
| `sha256` | `fdd2f264fdfb5127843b38f9e869fb9fb5c7747ac0036dbefb0b4c5b2032996d` |
| `size_bytes` | `33554560` |
| `mtime` | `2026-06-26 17:14:56 +0800` |
| `git_commit` | `TBD`（远程非 git 工作树） |
| `script` | `src/hy7_phase2_ddpm.py sample --continuous`；标定 `src/hy7_phase2_threshold_calib.py`；评估 `src/hy7_phase2_eval.py` |
| `run_config` | 512 张 128² 连续值；seed=123；使用 M7 50ep `best.pt`；T* 由真实孔隙度均值 6.40% 标定。完整命令行待补。 |
| `source_data` | 同 M7 ct28 2.8μm pore mask test set；目标 φ real mean 6.405%。 |
| `evidence` | `experiments/花页7_PlanB_记录/phase2/m7v2_calib/calib_result.json`、`fig_calib.png`；笔记 `notes/22_阶段二_M7v2_阈值标定诊断.md`。 |
| `status` | `known_remote_verified_20260701` |
| `notes` | 标定结果：`T*=0.98732`；S₂ rmse 0.07143→0.00242；Euler T* gen 207.92 vs real 127.33，说明连通性真错仍在。 |

### 1.4 phase2 切片数据集 meta（ct28, 128²）

| 字段 | 内容 |
|---|---|
| `id` | `M7-dataset-slices-ct28-128-meta` |
| `stage` | `phase2` |
| `experiment` | `M7.1 ct28 pore mask slicing` |
| `artifact_type` | `dataset_meta` |
| `remote_path` | `hy7-linux:~/HXL/HY7_planb/phase2/slices_ct28_128/meta.json` |
| `local_path` | `TBD` |
| `in_git` | `no`（meta 很小，也可考虑将内容摘要入 git；不入 train/test `.npy`） |
| `sha256` | `993b1d3220fd81c37aebfe15d4be13cad332f5c49cdf48cc5d0a0d4424ad4c9d` |
| `size_bytes` | `506` |
| `mtime` | `2026-06-25 09:45 +0800` |
| `git_commit` | `TBD`（远程非 git 工作树） |
| `script` | `src/hy7_phase2_make_slices.py` |
| `run_config` | tile=128、z_step=6、axes=z、min_valid=0.999、test_frac=0.2、seed=42；16600 train / 4150 test；test φ mean 6.443%、median 5.676%。 |
| `source_data` | E2/E3 已验证同网格 ct28 2.8μm 体；原始远程 raw 路径待补。 |
| `evidence` | `notes/21` §1；`phase2/metrics.json` 的 real 统计。 |
| `status` | `known_remote_verified_20260701` |
| `notes` | 建议正式 manifest 将 dataset meta 与模型权重分开登记，便于后续 M7-v3 200ep/B1/B2 复用。 |

### 1.5 阶段一 ct14 baseline 分割权重（已知但非本次 phase2 主项）

| 字段 | 内容 |
|---|---|
| `id` | `P1-PlanB-ct14-baseline-best` |
| `stage` | `phase1` |
| `experiment` | `Plan B ct14 三相 baseline` |
| `artifact_type` | `weight` |
| `remote_path` | `hy7-linux:~/HXL/HY7_planb/experiments/hy7_planb/train_ct14/best.pt`；另见整理后路径线索 `hy7-linux:~/HXL/HY7_planb/runs/train_ct14_baseline/best.pt` |
| `local_path` | `TBD` |
| `in_git` | `no` |
| `sha256` | `ed6fc55e24ce69cdca1632132bb897f7cd5b760a180e35ccad4735362e56fc1f` |
| `size_bytes` | `22401037`（来自 `evidence_training_meta.txt`） |
| `mtime` | `Jun 23 21:14`（来自 `evidence_training_meta.txt`，年份/时区待补） |
| `git_commit` | `TBD` |
| `script` | `src/hy7_planb_train.py` |
| `run_config` | 100 epoch baseline；final mean dice 0.831（见 `experiments/花页7_PlanB_记录/README.md`）；完整命令待补。 |
| `source_data` | ct14 同网格 SUS/pore/FENG raw；`evidence_training_meta.txt` 记录部分 raw 路径和大小。 |
| `evidence` | `experiments/花页7_PlanB_记录/evidence_trainlog_ct14.json`、`evidence_training_meta.txt`、`README.md`；`notes/13_阶段一_PlanB实验记录_E0.md`。 |
| `status` | `known_needs_commit_run_config` |
| `notes` | 本条用于 P0/P1 复现骨架完整性；不是阶段二 DDPM 权重。正式 manifest 可放在“阶段一分割权重”小节。 |

### 1.6 阶段一 ct14 E1 / ct28 E2 权重 sha 线索（待补路径）

| id | stage | artifact_type | remote_path | sha256 | size_bytes | evidence | status |
|---|---|---|---|---|---|---|---|
| `P1-PlanB-ct14-e1-best` | `phase1` | `weight` | `hy7-linux:~/HXL/HY7_planb/runs/train_ct14_e1/best.pt` | `84142b600685595bff4fef61e7f517c201ee2b833113673eb621aa48901a5577` | `TBD` | `evidence_training_meta.txt`、`evidence_trainlog_ct14_e1.json`、`notes/14` | `needs_remote_verify` |
| `P1-PlanB-ct28-e2-best` | `phase1` | `weight` | `hy7-linux:~/HXL/HY7_planb/runs/train_ct28_e2/best.pt` | `f5685b4a244c97cf327ab34af24383c416f7f7a2da20032dc72a551c6fa6ea1f` | `TBD` | `evidence_training_meta.txt`、`evidence_trainlog_ct28_e2.json`、`notes/15` | `needs_remote_verify` |

## 2. M7-v3 / 后续 B1-B2 条目

### 2.1 M7-v3 200ep cheap control（已采样评估）

| id | artifact_type | remote_path | sha256 | size_bytes | mtime | evidence | status |
|---|---|---|---|---:|---|---|---|
| `M7-v3-DDPM-ct28-200ep-best` | `weight` | `hy7-linux:~/HXL/HY7_planb/phase2/ddpm_ct28_200ep/best.pt` | `f009973ce37228644e6158ed46d9e08b1dfdb8c892754b6e327933b970646a6d` | `252713143` | `2026-06-27 20:46:19 +0800` | `remote_provenance_20260701/`；`notes/24` | `trained_remote_verified` |
| `M7-v3-DDPM-ct28-200ep-final` | `weight` | `hy7-linux:~/HXL/HY7_planb/phase2/ddpm_ct28_200ep/final.pt` | `4975ed241dc4af15178199ee32370ad39a45763e745fbdda285fc2484634ae78` | `252713531` | `2026-06-27 21:51:10 +0800` | `remote_provenance_20260701/` | `trained_remote_verified` |
| `M7-v3-DDPM-ct28-200ep-samples-T0` | `sample` | `hy7-linux:~/HXL/HY7_planb/phase2/ddpm_ct28_200ep/samples.npy` | `42101fdd97f531608d33f6c7a7b2be649b777210d36d48ef63aa7a2a47331288` | `8388736` | `2026-07-03 15:20:26 +0800` | `phase2/m7v3_200ep/eval/metrics.json`；`notes/25` | `sampled_evaluated` |
| `M7-v3-DDPM-ct28-200ep-samples-continuous` | `continuous_sample` | `hy7-linux:~/HXL/HY7_planb/phase2/ddpm_ct28_200ep/samples_continuous.npy` | `7184d08955c36137da82632b2a2d0028abc1d8e9de8e8e4490806b563ba9de61` | `33554560` | `2026-07-03 15:20:26 +0800` | `phase2/m7v3_200ep/calib/calib_result.json`；`notes/25` | `sampled_calibrated` |

Run config：200ep train_meta 记录 size=128、n_train=16600、epochs=200、base=64、bs=64、lr=1e-4、best_Lsimple=0.01881；采样命令为 `src/hy7_phase2_ddpm.py sample --ckpt .../ddpm_ct28_200ep/best.pt --out .../ddpm_ct28_200ep --n 512 --size 128 --base 64 --bs 64 --seed 123 --continuous`。评估为 `--n 512 --rmax 48 --seed 0`，标定 `target_phi=6.4`。

结论：200ep T=0 φ=4.960%、S₂ rmse=0.00372、Euler=120.88、maxCC=0.0467；T* φ=6.4 后 S₂ rmse=0.01010、Euler=119.58。单纯加 epoch 不闭合，转 B1 灰度介质生成。

### 2.2 后续 B1/B2 预留条目（尚未训练）

| id | 预期路径 | 目的 | 当前状态 |
|---|---|---|---|
| `M7-v4-DDPM-ct28-gray-best` | `hy7-linux:~/HXL/HY7_planb/phase2/ddpm_ct28_gray/best.pt` 或后续实际目录 | B1 灰度 sus 介质生成 | `design_next`，见 `notes/25` |
| `M7-v4-DDPM-ct28-sus-pore-2ch-best` | `hy7-linux:~/HXL/HY7_planb/phase2/ddpm_ct28_sus_pore_2ch/best.pt` 或后续实际目录 | B2 `[sus,pore]` 双通道联合生成 | `backup_design`，见 `notes/25` |

## 3. 后续补证命令清单（只读/校验，不提交大文件）

2026-07-01 已补齐 M7 50ep `best.pt`、`samples.npy`、`samples_continuous.npy` 与 `slices_ct28_128/meta.json` 的远程路径、大小、mtime、sha256。后续如需继续补字段，优先补仍缺的原始命令、训练 seed、代码版本/同步时间，并在远程上只运行类似只读命令，注意不要打印敏感文件内容：

```bash
# 示例：仅对已知实验产物目录列大小与哈希
cd ~/HXL/HY7_planb/phase2/ddpm_ct28
ls -lh best.pt samples.npy samples_continuous.npy meta.json 2>/dev/null || true
sha256sum best.pt samples.npy samples_continuous.npy 2>/dev/null || true

# 记录代码版本（在对应 git 工作树内执行；若远程不是 git 工作树则记录本地 commit + rsync 时间）
git rev-parse HEAD 2>/dev/null || true
git status --short 2>/dev/null || true
```

补字段时优先补：
1. M7 50ep 原始 shell 命令或 shell history，用于二次确认 `--seed 42` 与完整 `--sample-every 10`。
2. 本地代码同步到远程时的 commit/rsync 时间；远程 `/home/user/HXL/HY7_planb` 当前不是 git 工作树。
3. B1/B2 后续训练开始后，新增对应权重、采样、eval/calib 条目；不要覆盖 M7 50ep 与 M7-v3 200ep 条目。

## 4. 口径警告

- M7 `metrics.json` 与 `eval_v2/metrics.json` 都是 T=0 二值化口径；`eval_v2` 只是补 naive baseline 和连通指标。
- M7-v2 `m7v2_calib/calib_result.json` 是 T*=0.98732 标定口径；它修复了 S₂/孔隙度伪影，但暴露 Euler/连通性真错。
- `samples_continuous.npy` 是 M7-v2 标定所需关键大文件；其 sha256/大小已于 2026-07-01 补齐，后续不要用远程旧 verdict 覆盖本地修正版。
- 后续 M7-v3 的“sus 条件输入→pore 输出”若使用真实 sus，语义上是分割，不是生成；正式生成方向应是灰度 sus 介质生成或 `[sus,pore]` 联合生成（见 `notes/24`）。
