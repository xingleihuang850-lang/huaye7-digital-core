# experiments/INDEX.md — 实验证据索引

> 快照依据：`experiments/` 目录枚举、`.gitignore`、`git ls-files experiments`、`git status -- experiments`、`experiments/花页7_PlanB_记录/README.md`、`experiments/花页7_PlanB_记录/phase2/README.md`、`notes/README.md`、`notes/21_*`、`notes/22_*`、`notes/24_*`。

## 0. 总原则

- `experiments/` 存放实验轻量证据、可复核图表、指标 JSON、阶段性分析产物索引。
- 大体积训练产物、权重、原始体素、中间 patch/tile 数据不直接入 git；应在权重/ckpt manifest 中记录路径、大小、sha256、commit、run_config、生成命令和日期。
- 正式论文/汇报证据优先使用 `experiments/花页7_PlanB_记录/` 及其 `phase2/` 子目录；`experiments/figures/`、`experiments/hy7_figures/`、`experiments/hy7_planb/`、`experiments/master_stats.json`、`experiments/hy7_stats.json` 是 `.gitignore` 中声明的可重建产物或中间产物。
- `figs_ppt/` 当前为未跟踪展示图目录，建议暂缓纳入正式证据；如需入库，应先核对来源脚本/生成命令/sha256，并在本索引中升级说明。

## 1. 目录/文件清单

| 路径 | 用途 | 是否正式证据 | 当前入 git 状态 | 对应脚本/笔记 | 可重建性/注意事项 |
|---|---|---:|---|---|---|
| `experiments/.gitkeep` | 保持空目录/目录存在 | 否 | 已跟踪 | 无 | 无实质实验含义。 |
| `experiments/master_stats.json` | GJ5-15/早期统计分析产物 | 否，偏派生汇总 | 被 `.gitignore` 忽略，未跟踪 | 早期 ETL/统计脚本；详见 `CLAUDE.md` 数据流 | 可由原始统计表/脚本重建；不应作为不可替代证据。 |
| `experiments/figures/` | GJ5-15/早期统计图，如 well tracks、segment bars、correlation、permeability 等 | 否，展示/派生图 | 被 `.gitignore` 忽略，未跟踪 | 早期统计作图脚本 | 可重建；若用于汇报，需回链到生成脚本和输入数据。 |
| `experiments/hy7_stats.json` | 花页7服务商统计 xlsx 清洗后的结构化汇总 | 否，派生汇总；可作数据核查中间产物 | 被 `.gitignore` 忽略，未跟踪 | `src/hy7_etl.py`（见 `CLAUDE.md` 花页7数据流） | 可从 `data/hy7_raw/` 的服务商统计表重建。 |
| `experiments/hy7_figures/` | 花页7统计图：porosity、minerals、pore radius、coordination、maps、ladder | 否，展示/派生图 | 被 `.gitignore` 忽略，未跟踪 | `src/hy7_*.py` 系列统计/作图脚本 | 可重建；适合汇报预览，不等同阶段一/二模型证据。 |
| `experiments/hy7_planb/` | Plan B 本地/中间检查产物；现见 `align_check/` | 否，属于可重建中间产物 | 被 `.gitignore` 忽略，未跟踪 | `src/hy7_planb_check_alignment.py --scale ct14` | 可重建；正式对齐证据已拷贝/沉淀到 `花页7_PlanB_记录/`。 |
| `experiments/hy7_planb/align_check/summary_ct14.json` | ct14 三体同网格/孔隙裂缝重叠核查摘要 | 中间证据；正式引用用 `花页7_PlanB_记录/evidence_align_summary_ct14.json` | 被 `.gitignore` 忽略，未跟踪 | `src/hy7_planb_check_alignment.py --scale ct14`；笔记 `notes/13_阶段一_PlanB实验记录_E0.md` | 可重建；避免同时引用中间目录和正式目录造成口径混淆。 |
| `experiments/hy7_planb/align_check/ct14_z*.png` | ct14 灰度+标签叠加切片核查图 | 中间证据；正式引用用 `花页7_PlanB_记录/ct14_z*.png` | 被 `.gitignore` 忽略，未跟踪 | 同上 | 可重建；正式证据区已有对应副本。 |
| `experiments/花页7_PlanB_记录/` | 花页7阶段一 Plan B 对齐+分割正式证据包；也承载阶段二轻量证据 | 是 | 已跟踪（例外：`figs_ppt/` 未跟踪且已 `.gitignore` 屏蔽） | README 指向 `notes/13` 等阶段一笔记；阶段二见 `phase2/README.md`、`notes/21_*`、`notes/22_*`、`notes/24_*` | 作为论文/汇报数字与图的主要可追溯证据区；大权重不入 git，仅记录路径/sha。 |
| `experiments/花页7_PlanB_记录/README.md` | 阶段一证据包说明：inspect、alignment、trainlog、meta、脚本 sha 等 | 是 | 已跟踪 | `src/hy7_planb_io.py inspect`、`src/hy7_planb_check_alignment.py`、训练命令见阶段一实验记录 | 入口说明文件；记录 ct14 `best.pt` 远程路径与 sha256。 |
| `experiments/花页7_PlanB_记录/remote_data_manifest/` | hy7-linux 花页7远程数据 manifest 与全量 inventory TSV | 是 | 待跟踪 | `MANIFEST_huaye7_remote_20260703.txt`、`MANIFEST_huaye7_remote_20260703_inventory.tsv` | 证明远程 Linux 主工作副本中 6 个服务商原始尺度目录均可访问；`_analysis` 明确标为派生目录；大 raw/image 记录 path/size/mtime，小型服务商文档/统计表按策略 sha256。 |
| `experiments/花页7_PlanB_记录/evidence_inspect_volumes.json` | 7 体素取值分布 + 相值反推 | 是 | 已跟踪 | `python src/hy7_planb_io.py inspect` | 可由原始体素与脚本重建；证明 sus=灰度、相值=0 等基础事实。 |
| `experiments/花页7_PlanB_记录/evidence_align_summary_ct14.json` + `ct14_z*.png` | ct14 同网格对齐核查与叠加图 | 是 | 已跟踪 | `python src/hy7_planb_check_alignment.py --scale ct14`；`notes/13` | 可重建；用于钉住同 shape、孔隙∩裂缝重叠等事实。 |
| `experiments/花页7_PlanB_记录/evidence_trainlog_ct14*.json`、`evidence_trainlog_ct28_e2.json` | 阶段一训练曲线/指标记录 | 是 | 已跟踪 | `src/hy7_planb_train.py`；`notes/13/14/15` | 轻量训练日志可入 git；权重另记 manifest。 |
| `experiments/花页7_PlanB_记录/evidence_training_meta.txt` | 远程训练机器/env/权重大小和 sha、脚本 sha、数据源快照 | 是 | 已跟踪 | Linux 快照；`notes/13` | 关键 provenance 文件；ct14 baseline best.pt sha 已有，部分权重路径/大小可继续补齐到 WEIGHTS_MANIFEST。 |
| `experiments/花页7_PlanB_记录/evidence_src_sha256_mac.txt` | 本机脚本 sha256，和 Linux 运行脚本比对 | 是 | 已跟踪 | `shasum -a 256 src/hy7_planb_*.py` | 用于证明“跑的就是这份码”。 |
| `experiments/花页7_PlanB_记录/evidence_nonleak_check.txt` | 防泄漏/切分核查 | 是 | 已跟踪 | `src/hy7_planb_verify_nonleak.py`；阶段一笔记 | 可重建；用于支撑训练/验证切分可信。 |
| `experiments/花页7_PlanB_记录/evidence_e3_nnunet_3d5ep_summary.json` | E3 nnU-Netv2 同网格 3d_fullres 5ep 核验摘要 | 是 | 已跟踪 | `notes/16_阶段一_E3_nnUNet同网格核验.md` | 轻量摘要；大模型/nnUNet产物不入 git。 |
| `experiments/花页7_PlanB_记录/evidence_e3_nnunet_2d50ep_summary.json` | E3 nnU-Netv2 同网格 2d 50ep 核验摘要 | 是 | 已跟踪 | `notes/16_阶段一_E3_nnUNet同网格核验.md` | foreground Dice 0.9659805457 / IoU 0.9342477872，4例验证；sha256 `ab7b6151cde35a573b77184e28387179098374fad47c4ed2ce169d309f43a51e`。 |
| `experiments/花页7_PlanB_记录/evidence_s3_*`、`evidence_amics_color_mapping.json`、`fig_S3_25um_vs_1um.png` | S3 Amics 多矿物分割/尺度对照证据 | 是 | 已跟踪 | `notes/17_阶段一_S3_Amics多矿物分割.md` | 正式阶段一收尾证据之一。 |
| `experiments/花页7_PlanB_记录/fig_E2_vs_codex_ct28.png` | E2 ct28 配准对照图 | 是 | 已跟踪 | `notes/15_阶段一_E2_ct28配准对照.md` | 正式图；用于说明配准修复效果。 |
| `experiments/花页7_PlanB_记录/phase2/` | 阶段二 DDPM 生成轻量证据区 | 是 | 已跟踪 | `src/hy7_phase2_make_slices.py`、`src/hy7_phase2_ddpm.py`、`src/hy7_phase2_eval.py`、`notes/21_*`、`notes/22_*`、`notes/24_*` | 大文件如 `samples.npy`、`samples_continuous.npy`、`ckpt/*.pt` 不入 git；仅存指标/图/README。 |
| `experiments/花页7_PlanB_记录/phase2/README.md` | 阶段二证据说明，防止阈值口径混读 | 是 | 已跟踪 | `notes/21_*`、`notes/22_*`、`notes/24_*` | 必读入口；明确 `eval_v2` 是 T=0，`m7v2_calib` 是 T* 标定。 |
| `experiments/花页7_PlanB_记录/phase2/m7v3_200ep/` | M7-v3 200ep cheap control 轻量证据 | 是 | 已跟踪 | `notes/25_阶段二_M7v3_200ep评估与B1决策.md` | 入 git轻量文件：eval/calib JSON+PNG、samples_grid.png、remote_run 日志/hash；大文件 samples.npy/samples_continuous.npy 只记远程 sha。 |
| `experiments/花页7_PlanB_记录/phase2/b1_gray_sus/probe_20260703/` | B1 灰度介质生成前的 ct28 `sus` 只读分布探针 | 是 | 已跟踪 | `notes/26_阶段二_B1灰度介质生成设计.md` | 无训练；记录 valid mask、histogram、percentiles、min/max、M7 tile-compatible 20,750 tiles 分布；建议首版归一化 p1–p99 `[45,205]`。 |
| `experiments/花页7_PlanB_记录/phase2/b1_gray_sus/slices_ct28_gray_128/` | B1 灰度 `sus` DDPM 数据集轻量证据 | 是 | 已跟踪 | `src/hy7_phase2_make_gray_slices.py`、`notes/26_阶段二_B1灰度介质生成设计.md` | 远程大数组不入 git：`train.npy`/`test.npy`/`test_pore.npy`；本地仅保存 `meta.json`、`verify_summary.json`、`sha256.txt`、README。 |
| `experiments/花页7_PlanB_记录/phase2/b1_gray_sus/cheap50/` | B1 灰度 `sus` 50ep cheap run + 512 灰度采样 + threshold/nnUNet 下游评估 | 是 | 已跟踪 | `src/hy7_phase2_ddpm.py`、`src/hy7_phase2_eval.py`、`notes/26_阶段二_B1灰度介质生成设计.md` | 大权重/样本不入 git；本地保存 train_meta、grid、eval metrics/fig、remote logs/hash。threshold 口径：S₂ rmse=0.00105、Euler=111.00、maxCC=0.0880；nnUNet2d 口径过分割 φ=20.649%。 |
| `experiments/花页7_PlanB_记录/phase2/b1_gray_sus/controls_20260703/` | Fable5 后续归因控制：reference-real nnUNet、real-gray-threshold、generated vs real gray 分布诊断 | 是 | 待跟踪 | `src/hy7_phase2_eval.py`、nnUNetv2 predict、`notes/26_阶段二_B1灰度介质生成设计.md` | 证明 nnUNet 管线对真实灰度有效（φ=5.689%、Euler=121.08、maxCC=0.0559），真实灰度阈值方法上限强（S₂ rmse=0.00071、Euler=130.28），generated gray 存在明显域偏移（mean shift=-0.333，KS≈0.398）。 |
| `experiments/花页7_PlanB_记录/phase2/metrics.json` | M7 首基线评估：DDPM 50ep，T=0 二值化 | 是 | 已跟踪 | `src/hy7_phase2_eval.py`；`notes/21` | 真实 512 vs 生成 512；φ gen 23.506% vs real 6.405%，S₂ rmse 0.07143，Euler gen 146.24 vs real 127.33。 |
| `experiments/花页7_PlanB_记录/phase2/{samples_grid,real_grid,fig_eval}.png` | M7 首基线可视化/评估图 | 是 | 已跟踪 | `src/hy7_phase2_ddpm.py sample`、`src/hy7_phase2_eval.py`；`notes/21` | 图为轻量证据；原始 samples 大文件另记 manifest。 |
| `experiments/花页7_PlanB_记录/phase2/eval_v2/` | M7 原始 T=0 评估补充版：增加 naive baseline 与连通指标 | 是 | 已跟踪 | `src/hy7_phase2_eval.py` 扩展版；`notes/22` §5 | 重要：仍是 T=0 口径，不是 T* 标定后结果；不能用来声称阈值已修。 |
| `experiments/花页7_PlanB_记录/phase2/eval_v2/metrics.json` | M7 T=0 + naive baseline + connectivity 指标 | 是 | 已跟踪 | `src/hy7_phase2_eval.py`；`notes/22` | 关键数字：φ real 6.405 / gen 23.506 / naive 6.408；Euler real 127.33 / gen 146.24 / naive 890.16；max_cc_frac real 0.0597 / gen 0.1588 / naive 0.0048。说明 DDPM 已学到部分聚集，但程度不够。 |
| `experiments/花页7_PlanB_记录/phase2/eval_v2/fig_eval.png` | eval_v2 评估图 | 是 | 已跟踪 | 同上 | 英文标签，适合跨 Linux/macOS 复现。 |
| `experiments/花页7_PlanB_记录/phase2/m7v2_calib/` | M7-v2 阈值标定诊断 | 是 | 已跟踪 | `src/hy7_phase2_threshold_calib.py`；`notes/22` | 重要：这是 T*=0.98732 标定口径，用于分离“阈值伪影”与“连通性真错”。 |
| `experiments/花页7_PlanB_记录/phase2/m7v2_calib/calib_result.json` | T* 标定指标 | 是 | 已跟踪 | `src/hy7_phase2_threshold_calib.py`；`notes/22` | 关键数字：T*=0.98732；S₂ rmse 0.07143→0.00242；φ 对齐到 6.4%；Euler real 127.33→T* gen 207.92，说明连通性/聚集仍是真问题。 |
| `experiments/花页7_PlanB_记录/phase2/m7v2_calib/fig_calib.png` | T* 标定诊断图 | 是 | 已跟踪 | 同上 | 与 `calib_result.json` 配套引用。 |
| `experiments/花页7_PlanB_记录/phase2/remote_provenance_20260701/` | 2026-07-01 远程只读核验原始留痕：`ddpm_ct28_200ep` 训练日志摘录、train_meta、sha256 清单、环境/JSON 快照、SUMMARY/README | 是 | 已跟踪（2026-07-03 纳入） | `docs/environment-remote.md`、`WEIGHTS_MANIFEST.md`、`phase2/README.md`、`notes/24_*` | 「200ep 已训完、未采样评估」主张与本批 sha256 回填的唯一原始证据；7 个纯文本文件，必须随引用它的文档一同入 git。 |
| `experiments/花页7_PlanB_记录/figs_ppt/` | PPT/汇报展示图与公式图临时集合 | 暂缓；展示图，不作为正式证据 | 未跟踪，且已在 `.gitignore` 屏蔽以防误提交（2026-07-03） | 生成脚本/来源需补；可能来自阶段一/二汇报制图流程 | 建议暂缓入库。若要正式化，需逐图补来源脚本、输入证据、sha256、是否可重建、是否对应论文图号，并移除 `.gitignore` 对应条目后单独提交。当前不要和正式证据混用。 |
| `experiments/花页7_PlanB_记录/figs_ppt/formulas/` | PPT 公式/原理图：Archie、DDPM、Dice/IoU/S₂/Euler、CT physics 等 | 暂缓；展示/教学图 | 未跟踪（随上条被 `.gitignore` 屏蔽） | 来源脚本/生成方式待补 | 展示图优先；正式论文中应使用可追溯公式或重绘矢量图。 |

## 2. phase2 口径特别说明

### 2.1 `phase2/eval_v2/`：M7 原始 T=0 补充评估

- 语义：在 M7 首基线 `T=0` 二值化口径上，补充 naive baseline 与连通性指标。
- 不是 T* 阈值标定后的评估。
- 关键结论：
  - M7 T=0 仍过度生成孔隙：φ gen 23.506% vs real 6.405%。
  - naive baseline 按真实 tile φ 撒点，Euler 890.16 极高；DDPM Euler 146.24，明显低于 naive，说明 DDPM 已学到一定空间聚集。
  - 但 DDPM 最大连通簇占比、Euler 等仍与真实有差距，M7 首基线质量未达标。

### 2.2 `phase2/m7v2_calib/`：M7-v2 T* 阈值标定诊断

- 语义：对 M7 连续输出标定阈值 `T*=0.98732`，使生成孔隙度均值对齐真实均值 6.4%，用于诊断 T=0 伪影与结构真错。
- 关键结论：
  - 阈值伪影已基本修复：S₂ rmse 0.07143 → 0.00242（约下降 97%）。
  - 连通性真错仍在：Euler T* gen 207.92 vs real 127.33，且比 T=0 的 146.24 更差，说明保留下来的高置信孔隙更偏孤立散点。
  - 后续 M7-v3 应优先做 50→200ep 欠训练对照，并推进灰度 sus 介质生成（B1）或 `[sus,pore]` 双通道联合生成（B2），而不是把真实 sus 当 condition 做分割。

## 3. 推荐后续补齐项

- 新增正式实验条目时，同步新增/引用 `WEIGHTS_MANIFEST.md`，但不要把权重本体入 git。
- 对 `phase2/ddpm_ct28/` 远程大文件补：`best.pt` 大小、mtime、sha256、训练 commit、run_config、采样命令、`samples.npy`/`samples_continuous.npy` 大小与 sha256。
- 对 `figs_ppt/` 做一次来源核查；核查前保持“暂缓/展示图”状态。
- M7-v3 新实验目录建议按意图区分：`m7v3_200ep/`、`m7v3_sus_gray/`、`m7v3_sus_pore_2ch/`，避免与 `eval_v2`/`m7v2_calib` 口径混淆。

## 4. 暂缓项边界

| 项 | 当前状态 | 边界 | 升级为正式证据的条件 |
|---|---|---|---|
| `experiments/花页7_PlanB_记录/figs_ppt/` | 未跟踪（已加 `.gitignore` 防误提交） | PPT/汇报展示图，暂不作为正式证据 | 逐图补来源脚本/输入证据/sha256/用途后，移除 `.gitignore` 条目并单独提交 |
| `src/hy7_ct14_make_nnunet_3phase.py` | 暂缓且已 `.gitignore` 精确屏蔽 | 阶段一 CT14 三相 nnU-Netv2 helper，当前不属于阶段二 B1 灰度生成主线，也不作为阶段一正式收尾证据 | 补 SimpleITK/nnUNet 依赖说明、实际运行日志、输出目录、meta/hash 后，移除 `.gitignore` 精确屏蔽并作为单独阶段一补档提交 |
