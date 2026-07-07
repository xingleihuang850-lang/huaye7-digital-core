# OpenCode 代码审计与 provenance 报告 2026-07-07

## 审计结论

本次只读审计确认：当前代码库主要由五个簇组成，分别服务阶段一分割地基、阶段二 DDPM/灰度校准、B2-min calibrated handoff、阶段三下游有效性诊断，以及报告生成。代码总体是实验推进中逐步形成的“证据包脚本 + 指标代理 + CLI”体系，已有较强的 fail-closed 边界，但指标实现重复、部分高科学权重脚本缺测试、GJ5-15 与 HY7 命名边界需要后续清理。

当前阶段三边界必须保持：

```text
parent_smoke_verdict=REDESIGN_BEFORE_ANY_A2_SMALL_GATE
scientific_status=diagnostic_metadata_only_not_evidence
execution_authorized=false
second_smoke_authorized=false
A2_small_authorized=false
training_authorized=false
checkpoint_authorized=false
```

因此，`src/hy7_stage3_minimal_3d_smoke.py`、`src/hy7_stage3_inter_slice_audit.py`、`src/hy7_stage3_branch_a_a1_toy.py` 只能解释为诊断/设计/管线元数据工具，不能解释为 HY7 3D 数字岩心有效性证据。

## 主要证据来源

项目路线与状态：

```text
CLAUDE.md
notes/README.md
notes/00_研究主线路线图与任务分解.md
notes/03_项目Workflow设计.md
notes/04_项目术语表与写法规范.md
```

阶段二与 B1/B1.1/B2-min：

```text
notes/20_阶段二_2D扩散启动设计.md
notes/21_阶段二_M7_DDPM_MVP结果.md
notes/22_阶段二_M7v2_阈值标定诊断.md
notes/24_阶段二_M7v3_连通性迭代设计.md
notes/25_阶段二_M7v3_200ep评估与B1决策.md
notes/26_阶段二_B1灰度介质生成设计.md
notes/27_阶段二_B1校正敏感性与B11决策.md
notes/28_阶段二_B1理论文献支撑.md
notes/29_阶段二_B11_P0审计与花页7DLIS盘点.md
notes/30_阶段二_B11输出校准与checkpoint选择.md
```

B2-min 与阶段三证据包：

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/baseline_package_ep015/b2_min_manifest.json
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/constrained_selection_smoke_ep015/selection_summary.json
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_minimal_3d_smoke_package_20260707_run01_qmatch_candidate/
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_inter_slice_audit_package_20260707_run01/
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_route_design_card_20260707_run01.md
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_route_design_completion_gate_record_20260707.md
```

文献与数据 provenance：

```text
literature/_manifest.txt
REPRODUCE.md
```

## 代码簇审计

### 1. Stage 3 downstream-validity cluster

文件：

```text
src/hy7_stage3_minimal_3d_smoke.py
tests/test_hy7_stage3_minimal_3d_smoke.py
src/hy7_stage3_inter_slice_audit.py
tests/test_hy7_stage3_inter_slice_audit.py
src/hy7_stage3_branch_a_a1_toy.py
tests/test_hy7_stage3_branch_a_a1_toy.py
```

它解决的问题：在 B2-min calibrated 结果尝试进入阶段三前，先用最小 3D/跨切片元数据诊断检查“把 2D qmatch/nnUNet 结果堆成 3D”是否存在明显下游有效性问题。

演化线索：

```text
bf0dd77 feat: add branch A A1 toy metric plumbing
1c7f2f9 feat: add minimal 3D smoke launcher contract
4aa46e9 feat: run minimal 3D smoke diagnostic
81e0f33 feat: add inter-slice metadata audit
```

核心输入/输出：

| 文件 | 输入 | 输出 | 覆盖测试 |
|---|---|---|---|
| `hy7_stage3_branch_a_a1_toy.py` | synthetic known-answer phantoms | A1 toy package、metrics、connectivity semantics | `test_hy7_stage3_branch_a_a1_toy.py` |
| `hy7_stage3_minimal_3d_smoke.py` | calibration artifact、failed chunk record、外部 candidate `.npy` 路径/hash/origin | 12-file smoke metadata package，不提交体素数组 | `test_hy7_stage3_minimal_3d_smoke.py` |
| `hy7_stage3_inter_slice_audit.py` | candidate source、route label、axis mapping、hash | 9-file metadata-only inter-slice audit package | `test_hy7_stage3_inter_slice_audit.py` |

关键 provenance：`branch_a_3d_smoke_manifest.json` 记录 `route_label=nnUNet ep015_qmatch`、`calibration_version=hy7-gray-calibration-qmatch-v1`、`formal_anchor=ep015_all planning_anchor_only`、`failed_chunk_required=ep015_chunk000_063`、candidate origin 为远程 `hy7-linux:/home/user/HXL/HY7_planb/.../ep015_qmatch_pore_nnunet2d.npy`，并明确 `scientific_status=diagnostic_smoke_not_evidence`。

理论依据：孔隙连通/贯通、两点相关、Euler/Minkowski 拓扑代理。依据来自 `notes/28` 对 S₂ 不充分、Euler/maxCC 对孔隙网络重要性的总结，以及 Andrä2013、Blunt2013、Jiao/Gommes/Amiri 类文献框架。

科学边界：这些脚本不得用于声明渗透率、qmatch formal acceptance、B2-min final pass、HY7 3D 数字岩心有效、或生成式数字井筒有效。`stage3_route_design_card_20260707_run01.md` 已说明 run01 qmatch 2D-stack 的 stacking-axis continuity 很差，设计目标是后续路线评审，而不是寻找贯通体。

清理建议：把 3D component/S₂/axis helper 抽成共享纯函数模块；给每个 metric 写 known-answer fixture；把 axis boundary semantics 写入函数 docstring。

### 2. B2-min calibrated handoff cluster

文件：

```text
src/hy7_b2_min_audit.py
src/hy7_b2_min_handoff.py
src/hy7_b2_min_package.py
src/hy7_b2_min_select.py
tests/test_hy7_b2_min_audit.py
tests/test_hy7_b2_min_handoff.py
tests/test_hy7_b2_min_package.py
tests/test_hy7_b2_min_select.py
```

它解决的问题：把 B1.1 的 `ep015 + qmatch` calibrated candidate 整理成可审计的 B2-min design-entry/handoff bundle，同时阻止“orig raw pass”“qmatch formal acceptance”“final pass”等越界表述。

演化线索：

```text
6ad21ef feat(phase2): close B1.1 and prepare calibrated B2-min
a8ce11d feat(phase2): add calibrated B2-min selection smoke
4715e7a feat: add B2-min design audit checklist
ea2b534 docs: reconcile B2-min audit evidence
84238f4 feat: add B2-min handoff dry-run bundle
```

核心输入/输出：

| 文件 | 角色 | 输入 | 输出 | 测试 |
|---|---|---|---|---|
| `hy7_b2_min_package.py` | baseline evidence package | formal512、nnUNet disagreement、qmatch generalization、checkpoint hash | `baseline_package_ep015/b2_min_manifest.json` | package tests |
| `hy7_b2_min_select.py` | constrained no-training selection smoke | fixed calibrated chunks、qmatch manifest、formal metric helpers | `constrained_selection_smoke_ep015/selection_summary.json/md` | select tests |
| `hy7_b2_min_audit.py` | manifest/selection/design claim lint | manifests and design text | audit JSON/status | audit tests |
| `hy7_b2_min_handoff.py` | dry-run handoff bundle | baseline manifest、selection summary、audit module | `handoff_bundle_ep015_20260706/*` | handoff tests |

关键数值 provenance：`baseline_package_ep015/b2_min_manifest.json` 记录 checkpoint `ckpt_ep015.pt` sha256 `83995e66...`；formal512 `formal512_ep015.json` sha256 `45c565aa...`；nnUNet disagreement summary sha256 `5b425132...`；qmatch generalization summary sha256 `4044881e...`。其中 formal512 `s2_rmse=0.0003403`、`euler=120.81`、`maxcc=0.06409`，nnUNet ep015_qmatch `phi=5.7949`、`s2_rmse=0.001721`、`euler=116.154`、`maxcc=0.065107`。

理论依据：灰度强度校正/domain shift、S₂、Euler/maxCC、数字岩心评估代理。`notes/28` 明确 qmatch 是诊断/后处理，不能当成纯生成质量。

科学边界：`selection_summary.json` 是 constrained selection smoke，不是重新训练、不修改 checkpoint、不证明 B2-min final pass；`ep015_all` 只能是 planning anchor，不是 formal acceptance。

清理建议：把 manifest schema、forbidden claim policy、sha256/json helpers 合并；把 scoring gate 权重和阈值抽成显式版本化配置。

### 3. Phase 2 DDPM / calibration cluster

文件：

```text
src/hy7_phase2_ddpm.py
src/hy7_phase2_eval.py
src/hy7_phase2_make_gray_slices.py
src/hy7_phase2_make_slices.py
src/hy7_phase2_threshold_calib.py
src/hy7_gray_calibration.py
tests/test_hy7_phase2_ddpm_*.py
tests/test_hy7_phase2_make_gray_slices.py
tests/test_hy7_gray_calibration.py
```

它解决的问题：阶段二从二值孔隙 DDPM 过渡到灰度 `sus` 生成、输出校准、metric-aware checkpoint selection 和 qmatch 诊断。

关键演化线索：

```text
31119d8 feat(hy7-阶段二): M7 2D DDPM MVP
5348321 feat(phase2): add threshold calibration for M7 DDPM outputs
99a7b96 feat(phase2): add connectivity metrics and naive baseline evaluation
4e71741 feat(phase2): build B1 gray sus slice dataset
a9b7196 feat(phase2): support B1 gray DDPM training
ff6c1bc feat(phase2): add B1 gray train-moments calibration
f0f66bc feat(phase2): add B1.1 metric-aware checkpoint scoring
c4b60c1 feat(phase2): add B1.1 periodic validation sampling
6ad21ef feat(phase2): close B1.1 and prepare calibrated B2-min
```

算法依据与边界：

| 算法/指标 | 代码路径 | 依据 | 边界 |
|---|---|---|---|
| DDPM ε-prediction | `hy7_phase2_ddpm.py` | Ho2020；`notes/20` | 训练/采样不是本审计允许动作 |
| 二值孔隙切片 | `hy7_phase2_make_slices.py` | PlanB 同网格标签；`REPRODUCE.md` | 派生训练集，不是原始数据 |
| M7-v2 T* 阈值标定 | `hy7_phase2_threshold_calib.py` | `notes/22` | T* 修阈值伪影，不修拓扑真错 |
| S₂/Euler/maxCC | `hy7_phase2_eval.py`、`hy7_phase2_ddpm.py` | `notes/22`、`notes/28` | 2D tile proxy，不是渗透率 |
| gray `sus` dataset | `hy7_phase2_make_gray_slices.py` | `notes/26`、`notes/29` | gray preprocessing 不等于生成质量 |
| train-moments/qmatch | `hy7_phase2_ddpm.py`、`hy7_gray_calibration.py` | `notes/27-30`、domain shift/histogram matching | qmatch 是后处理/诊断，不是 formal acceptance |

数据 provenance：`REPRODUCE.md` 记录 `slices_ct28_128/meta.json` sha256 `993b1d3220fd81c37aebfe15d4be13cad332f5c49cdf48cc5d0a0d4424ad4c9d`，主链数据集 `tile=128`、`z_step=6`、`axes=z`、`n_train=16600`、`n_test=4150`。M7-v2 远程 `train_meta.json` sha256 `1d04c071...`，`samples_continuous.npy` 和 checkpoint 大文件只记录路径/hash，不入 git。

测试覆盖：DDPM 数据加载、灰度校准、metric-aware selection、periodic validation、soft proxy loss、CLI 均有测试；`hy7_phase2_eval.py` 和 `hy7_phase2_threshold_calib.py` 暂无直接测试，是科学权重较高的缺口。

清理建议：`hy7_phase2_ddpm.py` 是当前最大风险文件，应拆分；指标实现需要统一 golden fixture；`threshold_calib` 和 `eval` 要补测试后再重构。

### 4. PlanB data/segmentation cluster

文件：

```text
src/hy7_planb_*.py
src/hy7_ct14_make_nnunet_3phase.py
src/hy7_amics_make_nnunet.py
src/hy7_etl.py
src/etl_build_warehouse.py
```

它解决的问题：阶段一分割地基和统计 ETL，为阶段二/三提供同网格相场、孔隙标签、灰度体和尺度统计。阶段一已是地基，不是论文终点。

关键演化线索：

```text
0bca022 feat(hy7-planb): 多尺度对齐+三相分割管线（Plan B）脚本/记录/证据
1bb036c docs(hy7-planb): E3 nnU-Net同网格交叉核验
128f54f feat(hy7-planb): 补提交 E1 裂缝过采样+可复现seed 实现代码
1e27ad2 feat(hy7-planb): S3 Amics多矿物分割
fe3030f feat(hy7): 花页7 多尺度 ETL/核校/出图/成品
9f835ad feat(gj5-15): GJ5-15 数字井筒 ETL/出图/成品
```

每个重要文件：

| 文件 | 角色 | 输入/输出 | 依据 | 测试 |
|---|---|---|---|---|
| `hy7_planb_io.py` | volume path/layout/memmap/label 工具 | HY7 服务商体数据到 decoded labels | notes/12-16 | 无 |
| `hy7_planb_dataset.py` | PlanB dataset inspection/build | 同网格组件到 dataset summaries | notes/12-13 | 无 |
| `hy7_planb_check_alignment.py` | 多尺度/相值对齐诊断 | memmap/porosity 到 alignment diagnostics | notes/12/15/16 | 无 |
| `hy7_planb_make_nnunet.py` | PlanB 到 nnU-Netv2 数据集 | nnUNet_raw | notes/16 | 无 |
| `hy7_ct14_make_nnunet_3phase.py` | ct14 三相 dataset writer | nnUNet_raw 三相 | notes/13 | 无 |
| `hy7_amics_make_nnunet.py` | Amics RGB 矿物图转 labels | mineral labels | notes/17 | 无 |
| `hy7_planb_train.py` | 轻量 U-Net baseline | checkpoints/logs | notes/13-14 | 无 |
| `hy7_planb_verify_nonleak.py` | 防泄漏 QA | stdout diagnostics | notes/18 | 无 |
| `hy7_etl.py` | HY7 服务商统计 xlsx ETL | `experiments/hy7_stats.json` | CLAUDE.md HY7 数据规则 | 无 |
| `etl_build_warehouse.py` | GJ5-15 DuckDB ETL | `data/warehouse.db` | GJ5-15 外部补充 | 无 |

数据 provenance：HY7 原始数据只有外盘/远程的 6 个服务商尺度文件夹；本地 `data/hy7_raw/` 是统计 xlsx 轻量副本。GJ5-15 现在是外部补充/迁移验证对象，不再是花页7阶段四前置依赖。

科学边界：这些代码可以支撑“阶段一分割地基”和“阶段二输入数据”，不能单独构成生成式贡献或数字井筒有效性结论。

清理建议：优先给 `hy7_planb_io.py`、Amics RGB 映射、ETL workbook parsing 加测试；将 GJ5-15 脚本后续命名为 `gj5_*`，避免和 HY7 主线混淆。

### 5. Reporting/productivity cluster

文件：

```text
src/hy7_make_excel.py
src/hy7_make_ppt.py
src/hy7_make_word.py
src/make_excel.py
src/make_figures.py
src/make_ppt.py
src/make_word.py
src/hy7_figures.py
src/hy7_mpl_cjk.py
src/verify_hy7.py
src/verify_integrity.py
```

它解决的问题：把 HY7/GJ5-15 统计、图表和阶段性结果转成 Excel/PPT/Word 交付物，并做一次性完整性核查。

演化线索：HY7 报告脚本来自 `fe3030f`；GJ5-15 报告脚本来自 `9f835ad`；CJK 字体集中配置来自 `ef5fb6a`。

边界：报告脚本是展示层，不应引入或强化科学声明。Linux 远程绘图优先英文标签，遵守 `CLAUDE.md` 字体规则。

清理建议：为报告生成器加 smoke test；将内容文本和格式代码分离；GJ5-15 报告脚本后续加 `gj5_` 前缀。

## 不能用于哪些结论

以下代码路径不得用于声称渗透率、qmatch formal acceptance、B2-min final pass 或生成式数字井筒有效：

```text
src/hy7_gray_calibration.py
src/hy7_b2_min_select.py
src/hy7_b2_min_package.py
src/hy7_b2_min_handoff.py
src/hy7_stage3_minimal_3d_smoke.py
src/hy7_stage3_inter_slice_audit.py
src/hy7_stage3_branch_a_a1_toy.py
src/hy7_phase2_ddpm.py 的 periodic/proxy/qmatch 相关路径
```

理由：这些路径要么是后处理/校准，要么是 constrained smoke，要么是 metadata-only diagnostic，要么是 2D/小样本代理。它们可以说明“为什么需要重设计/为什么不能直接推进”，不能说明“数字岩心/数字井筒已经有效”。

## 测试覆盖缺口

已覆盖较好的部分：Stage3 fail-closed package、B2-min audit/package/select/handoff、qmatch calibration、DDPM data loading/intensity calibration/metric-aware/periodic validation。

主要缺口：

1. `src/hy7_phase2_eval.py` 无直接测试。
2. `src/hy7_phase2_threshold_calib.py` 无直接测试。
3. `src/hy7_planb_io.py` 无路径/label decoding 测试。
4. `src/hy7_amics_make_nnunet.py` 无 RGB-to-label 映射测试。
5. `src/hy7_etl.py`、`src/etl_build_warehouse.py` 无 workbook fixture 测试。
6. 报告生成脚本无 smoke test。

## 总体建议

下一步不要先改科学行为。应先完成：统一指标模块、补高权重指标测试、抽 claim policy、拆分 `hy7_phase2_ddpm.py`、命名隔离 GJ5-15 报告代码。所有改动必须保持现有证据包 hash/provenance 可追溯，且不得把 qmatch 或 metadata proxy 包装成科学接受证据。
