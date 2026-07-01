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
| `sha256` | `ee15bb0ab5a67c1d22ad38b9bbd4f870f42ebb8ed4c41053da8989143449bb98`（来自 `notes/21_阶段二_M7_DDPM_MVP结果.md`；建议远程复核一次） |
| `size_bytes` | `TBD` |
| `mtime` | `TBD` |
| `git_commit` | `TBD` |
| `script` | `src/hy7_phase2_ddpm.py train` |
| `run_config` | `TBD`；笔记已知：diffusers `UNet2DModel` 约 63.1M，base64，attn@16²；`DDPMScheduler` T=1000、linear beta 1e-4→0.02、epsilon prediction；50 epoch、bs64、lr1e-4、AMP；5090；L_simple≈0.019；seed 待补。 |
| `source_data` | `phase2/slices_ct28_128/`，切片器 `src/hy7_phase2_make_slices.py`；128²，16600 train / 4150 test，沿 z 顶部 20% 防泄漏留出。远程实际路径待补。 |
| `evidence` | `experiments/花页7_PlanB_记录/phase2/metrics.json`、`fig_eval.png`、`samples_grid.png`、`real_grid.png`；笔记 `notes/21_阶段二_M7_DDPM_MVP结果.md`。 |
| `status` | `needs_remote_verify` |
| `notes` | 首基线质量未达标：T=0 口径 gen φ 23.506% vs real 6.405%，过度生成孔隙约 3.7×。 |

### 1.2 M7 50ep DDPM 采样结果：二值/默认样本

| 字段 | 内容 |
|---|---|
| `id` | `M7-DDPM-ct28-50ep-samples-T0` |
| `stage` | `phase2` |
| `experiment` | `M7 — 2D DDPM MVP sampling` |
| `artifact_type` | `sample` |
| `remote_path` | `hy7-linux:~/HXL/HY7_planb/phase2/ddpm_ct28/samples.npy`（路径线索；需远程确认文件名/是否存在） |
| `local_path` | `TBD` |
| `in_git` | `no` |
| `sha256` | `TBD` |
| `size_bytes` | `TBD` |
| `mtime` | `TBD` |
| `git_commit` | `TBD` |
| `script` | `src/hy7_phase2_ddpm.py sample`；评估 `src/hy7_phase2_eval.py` |
| `run_config` | 采样 1000 reverse steps；512 张；seed=123（M7/M7-v2 笔记指向同 seed）；二值化阈值 T=0。具体命令行待补。 |
| `source_data` | 权重 `M7-DDPM-ct28-50ep-best`；真实对照为 test set 512 tiles。 |
| `evidence` | `experiments/花页7_PlanB_记录/phase2/metrics.json`；`experiments/花页7_PlanB_记录/phase2/eval_v2/metrics.json`；`samples_grid.png`。 |
| `status` | `needs_remote_verify` |
| `notes` | `eval_v2/` 仍是 T=0 原始口径，只是补了 naive baseline 与 connectivity 指标；不要和 T* 标定结果混读。 |

### 1.3 M7-v2 连续采样结果：`samples_continuous.npy`

| 字段 | 内容 |
|---|---|
| `id` | `M7v2-DDPM-ct28-50ep-samples-continuous` |
| `stage` | `phase2` |
| `experiment` | `M7-v2 阈值标定诊断` |
| `artifact_type` | `continuous_sample` |
| `remote_path` | `hy7-linux:~/HXL/HY7_planb/phase2/ddpm_ct28/samples_continuous.npy` |
| `local_path` | `TBD` |
| `in_git` | `no` |
| `sha256` | `TBD` |
| `size_bytes` | `TBD` |
| `mtime` | `TBD` |
| `git_commit` | `TBD` |
| `script` | `src/hy7_phase2_ddpm.py sample --continuous`；标定 `src/hy7_phase2_threshold_calib.py`；评估 `src/hy7_phase2_eval.py` |
| `run_config` | 512 张 128² 连续值；seed=123；使用 M7 50ep `best.pt`；T* 由真实孔隙度均值 6.40% 标定。完整命令行待补。 |
| `source_data` | 同 M7 ct28 2.8μm pore mask test set；目标 φ real mean 6.405%。 |
| `evidence` | `experiments/花页7_PlanB_记录/phase2/m7v2_calib/calib_result.json`、`fig_calib.png`；笔记 `notes/22_阶段二_M7v2_阈值标定诊断.md`。 |
| `status` | `needs_hash` |
| `notes` | 标定结果：`T*=0.98732`；S2 rmse 0.07143→0.00242；Euler T* gen 207.92 vs real 127.33，说明连通性真错仍在。 |

### 1.4 phase2 切片数据集 meta（ct28, 128²）

| 字段 | 内容 |
|---|---|
| `id` | `M7-dataset-slices-ct28-128-meta` |
| `stage` | `phase2` |
| `experiment` | `M7.1 ct28 pore mask slicing` |
| `artifact_type` | `dataset_meta` |
| `remote_path` | `hy7-linux:~/HXL/HY7_planb/phase2/slices_ct28_128/meta.json`（由 `notes/21` 的 `phase2/slices_ct28_128/meta.json` 推断为远程相对路径；需确认） |
| `local_path` | `TBD` |
| `in_git` | `no`（如很小也可考虑只入 meta，不入 tiles；需项目决定） |
| `sha256` | `TBD` |
| `size_bytes` | `TBD` |
| `mtime` | `TBD` |
| `git_commit` | `TBD` |
| `script` | `src/hy7_phase2_make_slices.py` |
| `run_config` | 128²；16600 train / 4150 test；沿 z 顶部 20% 防泄漏留出；孔隙度 train 7.29%，test median 5.67%、mean 6.40%。 |
| `source_data` | E2/E3 已验证同网格 ct28 2.8μm 体；原始远程 raw 路径待补。 |
| `evidence` | `notes/21` §1；`phase2/metrics.json` 的 real 统计。 |
| `status` | `needs_remote_verify` |
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

## 2. M7-v3 预留条目（尚未补证据）

以下仅作 manifest 骨架，不表示实验已经完成：

| id | 预期路径 | 目的 | 当前状态 |
|---|---|---|---|
| `M7v3-DDPM-ct28-200ep-best` | `hy7-linux:~/HXL/HY7_planb/phase2/ddpm_ct28_200ep/best.pt` | 50→200ep 欠训练对照，复用 eval_v2 判据 | `planned_or_running_TBD`；需实际远程核查 |
| `M7v3-DDPM-ct28-200ep-samples` | `hy7-linux:~/HXL/HY7_planb/phase2/ddpm_ct28_200ep/samples.npy` | 200ep T=0/或统一口径采样 | `TBD` |
| `M7v3-DDPM-ct28-gray-best` | `hy7-linux:~/HXL/HY7_planb/phase2/ddpm_ct28_gray/best.pt` 或后续实际目录 | B1 灰度 sus 介质生成 | `design_only`，见 `notes/24` |
| `M7v3-DDPM-ct28-sus-pore-2ch-best` | `hy7-linux:~/HXL/HY7_planb/phase2/ddpm_ct28_sus_pore_2ch/best.pt` 或后续实际目录 | B2 `[sus,pore]` 双通道联合生成 | `design_only`，见 `notes/24` |

## 3. 待补命令清单（只读/校验，不提交大文件）

后续在远程上可用类似命令补字段，注意不要打印敏感文件内容：

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
1. `M7-DDPM-ct28-50ep-best` 的 size、mtime、commit、完整训练命令/run_config。
2. `samples.npy` 与 `samples_continuous.npy` 的 sha256/size/mtime。
3. `phase2/slices_ct28_128/meta.json` 的真实远程路径、sha256、内容摘要。
4. M7-v3 200ep 若已启动/完成，新增独立条目，不覆盖 M7 50ep 条目。

## 4. 口径警告

- M7 `metrics.json` 与 `eval_v2/metrics.json` 都是 T=0 二值化口径；`eval_v2` 只是补 naive baseline 和连通指标。
- M7-v2 `m7v2_calib/calib_result.json` 是 T*=0.98732 标定口径；它修复了 S2/孔隙度伪影，但暴露 Euler/连通性真错。
- `samples_continuous.npy` 是 M7-v2 标定所需关键大文件，必须补 sha256 与大小，否则复现链不闭合。
- 后续 M7-v3 的“sus 条件输入→pore 输出”若使用真实 sus，语义上是分割，不是生成；正式生成方向应是灰度 sus 介质生成或 `[sus,pore]` 联合生成（见 `notes/24`）。
