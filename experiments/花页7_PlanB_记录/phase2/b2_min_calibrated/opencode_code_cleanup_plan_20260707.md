# OpenCode 代码清理计划 2026-07-07

## 前提

本计划只提出后续可执行的清理任务。本次首轮审计不重构源码、不训练、不采样、不选择 checkpoint、不执行第二次 smoke、不执行 A2-small/A2-medium，不给出科学接受、qmatch formal acceptance、渗透率或生成式数字井筒结论。

## 优先级 P0：先保护科学边界

1. 给 `src/hy7_stage3_minimal_3d_smoke.py`、`src/hy7_stage3_inter_slice_audit.py`、`src/hy7_b2_min_select.py`、`src/hy7_gray_calibration.py` 增加模块级边界 docstring。
2. 把 B2-min/Stage3 的 forbidden claim 词表从代码中抽成版本化 JSON，例如 `experiments/.../claim_policy_20260707.json` 或后续 `src/hy7_claim_policy.py`。
3. 保留 `failed_chunk=ep015_chunk000_063`、`orig_raw_status=known_fail`、`formal_anchor=planning_anchor_only` 这三类负证据可见性。
4. 所有未来文档生成器必须默认写入 `diagnostic_metadata_only_not_evidence` 或同等状态，除非 Hermes/用户另给 gate。

## 优先级 P1：拆分高风险大文件

1. `src/hy7_phase2_ddpm.py` 当前混合 DDPM 训练、采样、强度校准、周期验证、2D 拓扑代理、soft regularizer 和 CLI。
2. 建议后续拆为 `hy7_phase2_ddpm_train.py`、`hy7_phase2_ddpm_sample.py`、`hy7_phase2_metrics.py`、`hy7_phase2_calibration.py`、`hy7_phase2_validation.py`。
3. 拆分前先添加 golden fixture，确保 `porosity/S2/Euler/maxCC` 在旧函数与新函数间逐项一致。
4. 不在拆分时改变任何阈值、score 权重、gate 逻辑或 checkpoint 选择语义。

## 优先级 P1：统一指标实现

当前 `S2`、Euler、连通簇、贯通/axis persistence 的逻辑分散在：

```text
src/hy7_phase2_eval.py
src/hy7_phase2_threshold_calib.py
src/hy7_phase2_ddpm.py
src/hy7_stage3_branch_a_a1_toy.py
src/hy7_stage3_minimal_3d_smoke.py
src/hy7_stage3_inter_slice_audit.py
```

后续应建立一个只含纯函数的指标模块，并用 synthetic phantoms 锁定：

1. 空体、全 1 体、单连通块、两连通块、贯通柱、断续柱。
2. 2D tile 与 3D volume 的口径差异。
3. axis 0/1/2 的含义和边界处理。
4. `Euler/Minkowski` 仍是代理指标，不能自动映射到渗透率。

## 优先级 P2：补测试

1. `src/hy7_phase2_threshold_calib.py`：补 `calibrate_threshold` 单调性、目标 φ 边界、重复值和空数组测试。
2. `src/hy7_phase2_eval.py`：补 naive baseline、S₂、Euler、maxCC 的固定答案测试。
3. `src/hy7_planb_io.py`：补路径解析、layout、`decode_phase_value`、`build_label` 的 synthetic memmap 测试。
4. `src/hy7_amics_make_nnunet.py`：补 RGB-to-label 映射测试，并记录颜色表来源。
5. `src/hy7_etl.py` 与 `src/etl_build_warehouse.py`：补最小 workbook fixture 测试。
6. 报告生成脚本：至少补 smoke test，输出到临时目录并检查文件存在。

## 优先级 P2：命名与模块边界

1. GJ5-15 报告脚本 `make_excel.py/make_figures.py/make_ppt.py/make_word.py` 建议后续改名为 `gj5_*`，避免与 HY7 主线混淆。
2. HY7 报告脚本保持 `hy7_*` 前缀。
3. PlanB 分割脚本保持阶段一地基身份，避免在阶段二/三代码中隐式导入过多训练逻辑。
4. 任何大规模重命名需用户确认，因为 notes/README 已说明重命名会影响 Obsidian 链接和历史记录。

## 优先级 P3：文档与 provenance

1. 为每个 CLI 写 `--help` 示例和“输入/输出/不可声明内容”。
2. 每个生成 package 的脚本写出 `source.git_commit`、`command`、`environment`、输入 hash、输出 hash。
3. 后续新增 evidence package 时，不写 `.npy/.npz/.pt` 到 git 管理目录，只写 manifest/hash/path。
4. `qmatch` 文件和文档必须持续使用 `hy7-gray-calibration-qmatch-v1` 这种显式版本，不允许简写成“校准后通过”。

## 不建议现在做

1. 不建议优化 DDPM 网络结构或加入新 loss，直到现有代码边界、指标口径和测试补齐。
2. 不建议把 qmatch 接成默认后处理，因为会弱化“诊断/后处理而非纯生成质量”的边界。
3. 不建议执行第二次 3D smoke 或 A2-small，当前阶段三 gate 明确要求 `REDESIGN_BEFORE_ANY_A2_SMALL_GATE`。
4. 不建议把 2D/metadata proxy 指标写成数字岩心或数字井筒有效性证据。
