# HY7 B2-min rock gate / multi-expert review — 2026-07-06

## Workflow node

- Node: `HY7-B2-min-rock-gate-review`
- Provider: `moa`
- Preset/model: `digital-rock-gate`
- Command form:

```bash
hermes -z "$(cat '/Users/hxl/Documents/Hermes工作区/99_临时文件与一次性输出/rock_b2_min_gate_review_20260706.md')" --provider moa -m digital-rock-gate
```

## MoA preset evidence

`hermes moa list` immediately before the run reported:

```text
digital-rock-gate
Reference models:
  1. openai-codex:gpt-5.5
  2. deepseek:deepseek-v4-pro
  3. openrouter:z-ai/glm-5.2
  4. custom:dk-claude:claude-fable-5
Aggregator: custom:dk-claude:claude-opus-4-8
```

Smoke test immediately before the run:

```bash
hermes -z '请只输出 OK-ROCK，不要解释。' --provider moa -m digital-rock-gate
```

Output:

```text
OK-ROCK
```

## Review input

Prompt file:

```text
/Users/hxl/Documents/Hermes工作区/99_临时文件与一次性输出/rock_b2_min_gate_review_20260706.md
```

The prompt asked the MoA gate to decide whether the already-reviewed `B2-min baseline package + constrained selection smoke` is sufficient to enter next-stage B2-min design. It included:

- remote ordered view integrity: `LINK_COUNT=42`, `BROKEN_COUNT=0`;
- baseline package hashes and manifest fields;
- formal512 / nnUNet qmatch / qmatch split evidence for ep015;
- constrained selection summary, selected row, full-batch control row;
- explicit forbidden constraints.

## Aggregated verdict

```text
CONDITIONAL_PASS
```

Important wording: this is a `design-entry` gate, not a B2-min result/pass gate.

## Aggregated decision summary

The rock gate judged that the evidence is sufficient to open B2-min design, with hard constraints:

1. The scope is design / method planning / gate definition / experiment-card drafting only.
2. No training, no hyperparameter search, no resampling, no scaling, and no new checkpoint are authorized by this gate.
3. `ep015` is the only frozen checkpoint for this design-entry step.
4. `hy7-gray-calibration-qmatch-v1` must be explicitly declared in every pipeline path.
5. B2-min acceptance thresholds must be anchored on full-batch evidence, especially `ep015_all`, not on the selected 64-slice chunk.
6. ORIG raw remains known-fail and can only be used as a negative control / risk note.

## Claims supported by this gate

Supported:

- `ep015 + qmatch-v1` calibrated pipeline passes formal512 and nnUNet qmatch review and generalizes across even/odd qmatch reference splits.
- The B2-min baseline package is reproducible enough for design-entry because it has manifest/readme/hash records and ordered-view reachability.
- Constrained selection is deterministic and internally consistent and can be used for candidate triage.

Not supported:

- B1.1 unconditional full pass.
- ORIG raw pass.
- Treating selected chunk metrics as model-wide metrics.
- Treating the smoke as final B2-min validation.
- Any 100/200ep scaling or new training authorization.
- Treating qmatch as fully validated across all downstream contexts.

## Allowed actions

The gate permits:

1. Write a B2-min design memo with goals, components, full-batch anchored gates, failure paths, and forbidden claims.
2. Extend/freeze no-retraining calibrated selection / packaging around existing artifacts only.
3. Draft the next B2 component's minimal design and dry-run plan, without training.
4. Treat the baseline package as a frozen reference and optionally pin package/script commit hashes in a follow-up manifest.
5. Update ordered view and notes/30 with this verdict and constraints.
6. Add audit tests: manifest schema, ordered-view integrity, hash reproducibility, explicit qmatch, and forbidden-claim lint.

## Forbidden actions

The gate explicitly forbids:

1. ORIG raw pass claims or use beyond negative control/baseline risk documentation.
2. Implicit qmatch.
3. A second B1.1 topology rescue.
4. Gate relaxation.
5. Replacing full-batch formal/nnUNet gate with the selected 64-slice chunk.
6. Direct 100/200ep scaling, new training, or new checkpoint introduction.
7. Modifying hash-locked baseline package content in place.
8. Claiming constrained selection smoke is formal selection validation.
9. Using unconditional B1.1 pass wording.

## Recommended non-blocking補强

The MoA gate said no blocking evidence is needed before design, but recommended three parallel補强 items:

1. Run `sha256sum -c hashes.txt` for baseline package internal consistency.
2. Record the one failed selection row and its failure reason.
3. In the B2-min design memo, explicitly note formal-vs-qmatch metric differences, especially formal512 `phi=6.4/Euler=120.81` vs nnUNet qmatch `phi≈5.79/Euler≈116.15`.

Follow-up check already run after the MoA output:

```text
BASE_HASH_CHECK
b2_min_manifest.json: 成功
b2_min_readme.md: 成功
SELECTION_FAIL_ROWS
{"euler": 123.953125, "failed": ["maxCC>0.070"], "maxcc": 0.07163110510281959, "n": 64, "phi": 6.435489654541016, "s2_rmse": 0.0005247734726096197, "variant": "ep015_chunk000_063"}
```

## One-line conclusion for notes/30

> B2-min design-entry gate 判定 **CONDITIONAL_PASS**：ep015 + hy7-gray-calibration-qmatch-v1 的 full-batch pass、baseline package 与含 full-batch control 的 constrained selection smoke 足以开启 B2-min 设计；边界为 calibrated / no-retraining / explicit qmatch / full-batch 为唯一验收口径，ORIG raw remains known_fail，selected chunk 仅限 triage 不得替代 full-batch gate，100/200ep scaling 与新训练未获授权。

## Full MoA output

```text
# HY7 B2-min Design-Entry Gate — digital-rock-gate 多专家正式复核

四位 reference 专家（reproducibility/packaging、statistics、topology/物性、process governance）独立评审后收敛一致。以下为聚合裁定。

═══════════════════════════════════════════
1. GATE VERDICT
═══════════════════════════════════════════

CONDITIONAL_PASS（design-entry 级别，非结果验收级别）

四专家一致，无分歧。判定不是 PASS（因 ORIG raw known_fail、qmatch 强制显式等前置约束仍生效），也不是 NEED_MORE_EVIDENCE（缺项均为低成本、可并行、非阻塞，不构成设计阻塞）。

核心支撑：
- Baseline package 完整：manifest / readme / hashes 三件齐全，sha256 已锁；manifest 显式编码 main_checkpoint=ep015、calibration_version=hy7-gray-calibration-qmatch-v1、orig_raw_status=known_fail，forbidden constraints 六项与 B1.1 conditional pass 逐条对齐。
- Full-batch 证据独立成立：formal512 ep015@phi6.4 passed_gate=True（S2 rmse≈3.4e-4，Euler≈120.81）；nnUNet ep015_qmatch reverse_fail=False；qmatch even/odd split 双通过（116.14 / 116.17），证明 calibration 非单一 split 过拟合。
- Selection smoke 设计正确：确定性 lexicographic tie-break（pass_gate → min S2 → |Euler−120| → maxCC → |phi−6.4|），且保留 full-batch control row（ep015_all, n=512, pass_gate=True）——这是关键，证明 selection 未替代或污染 full-batch 证据。
- Ordered view 结构完整：42 links / 0 broken；package 与 select 脚本已纳入 ordered view，可追溯；本地 31 passed。

Conditional 的理由：所有结论有效域被限定在 calibrated（qmatch 显式）+ ep015 + no-retraining 边界内，越界即失效。

═══════════════════════════════════════════
2. 是否足以开启下一阶段 B2-min 设计？设计边界
═══════════════════════════════════════════

足以开启。但"设计"= 方法学规划 / 组件分解 / 验收 gate 定义 / 实验卡拟定，不含任何训练、超参搜索、重采样、rescaling、新 checkpoint。

硬边界（写死进 design memo）：
1. 唯一 checkpoint：ep015；不引入新 checkpoint、不做新训练。
2. 每条 pipeline 必须显式声明 hy7-gray-calibration-qmatch-v1（禁止隐式/默认）。
3. B2-min 验收阈值必须锚定 full-batch 数值（ep015_all: S2 rmse≈2.85e-4, Euler≈121.27, maxCC≈0.0640, phi≈6.44），不得锚定 selected chunk（chunk384_447）数值——后者 S2 rmse=2.1e-4 优于 full-batch 属 selection bias / winner's curse，是"选出来的"而非能力提升。
4. Selection 仅用于 smoke / candidate triage / 排序；正式 gate 一律 full-batch。
5. ORIG raw 只能作为 negative control 出现在设计文档中，且必须标注 known_fail。

═══════════════════════════════════════════
3. 证据能 / 不能支持的 claim
═══════════════════════════════════════════

可支持：
- "ep015 + qmatch-v1 calibrated pipeline 在 formal512 与 nnUNet 双视角下均通过 full-batch gate，且 qmatch 具备 even/odd split generalization。"
- "B2-min baseline package 具备 reproducibility（manifest + hashes + ordered view），可作为 design-entry 参照。"
- "Constrained selection 机制内部一致、确定性、不破坏 full-batch 证据，可用于 B2-min 候选 triage。"

不可支持：
- 任何 "ORIG raw passed" 或 "B1.1 unconditional full pass"。
- "selected chunk (n=64) 指标代表模型整体水平" 或用其替代 full-batch gate / 设定阈值。
- "B2-min 本身已通过验收"——当前只是允许开始设计，B2-min 尚无结果。
- 任何 100/200ep scaling 或新训练的合理性（本 gate 未授权）。
- "qmatch calibration 已充分覆盖全域 downstream"——even/odd 是最小正证据，非完整泛化证明。

═══════════════════════════════════════════
4. 允许行动清单（本 gate 直接授权，无需补证据）
═══════════════════════════════════════════

1. 撰写 B2-min design memo：目标、组件分解、验收 gate 定义（阈值锚定 full-batch）、失败回退路径、forbidden claims。
2. No-retraining calibrated selection / packaging 的扩展与固化（扩大 selection 网格、tie-break 敏感性分析，均限现有 artifacts）。
3. 下一 B2 component 的最小实验设计（design doc + dry-run + 基于现有 artifacts 的 smoke，不触发训练）。
4. 把 baseline package 作为 frozen reference（tag commit 2cd18b8 或后继 tag）；在 manifest 中 pin 住脚本 commit hash（若尚未 pin）。
5. 更新 ordered view 与 notes/30，记录 verdict / allowed / forbidden / evidence hash / commit id。
6. 增补审计测试：manifest schema test、ordered view link integrity test、hash reproducibility test、qmatch explicitness check、forbidden-claim lint。

═══════════════════════════════════════════
5. 禁止行动清单（触犯即 CONDITIONAL_PASS 自动失效，须重审）
═══════════════════════════════════════════

1. 禁止声称 ORIG raw passed，或将其用于 negative control / baseline 以外用途。
2. 禁止 implicit qmatch——任何未显式声明 calibration_version 的下游使用。
3. 禁止第二次 B1.1 topology rescue。
4. 禁止 gate relaxation（含"因 smoke 通过所以放宽 full-batch 阈值"这类变体）。
5. 禁止用 selected chunk（n=64）替代 full-batch formal / nnUNet gate，或用其指标设定 B2-min 阈值。
6. 禁止直接 100/200ep scaling、新训练、新 checkpoint 引入（除非后续 gate 明确授权）。
7. 禁止回溯修改已打 hash 的 baseline package 内容（如需变更，走新版本 package）。
8. 禁止将 constrained selection smoke 宣称为正式 selection validation（它是 smoke，不是 full validation）。
9. 禁止在任何文档中使用 unconditional B1.1 pass 措辞。

═══════════════════════════════════════════
6. 是否需要先补证据再设计？
═══════════════════════════════════════════

不需要阻塞性补证据。Full-batch pass（formal512 + nnUNet qmatch）+ even/odd split generalization + 带 full-batch control 的 selection smoke，已构成 design-entry 的最小充分集。ordered view 结构校验通过、本地 31 passed，reproducibility 链闭合。

但有 3 项非阻塞、建议与设计并行的补强（recommended，非 required）——statistics 与 packaging 专家特别标注，是"严格 gate 而非橡皮图章"的关键：

1. hashes.txt 内部一致性：当前只报告了三个文件各自的 sha256，未确认 hashes.txt 内部条目与实际文件逐一自洽——补一次 sha256sum -c 校验。
2. 9 rows 中那 1 条 fail row：记录其失败原因与数值，防止 silent drop，保证 selection 负样本可追溯（写入 design memo 作为 known limitation）。
3. phi / Euler 的 formal-vs-qmatch 系统性差异：formal512 phi=6.4 / Euler=120.81 vs nnUNet qmatch phi=5.79 / Euler=116.15（差≈4.7）。reverse_fail=False 不受影响，但若 B2-min 下游对 phi/Euler 敏感，需在 design memo 中显式声明容忍区间与适用范围。

若未来目标从"设计"升级为 B2 component promotion / production package / scaling / 新训练，则须走独立 scaling/promotion gate，不得从本次 gate 自动继承授权。

═══════════════════════════════════════════
7. 写入 notes/30 的一句话结论
═══════════════════════════════════════════

> B2-min design-entry gate 判定 CONDITIONAL_PASS：ep015 + hy7-gray-calibration-qmatch-v1 的 full-batch pass、baseline package 与含 full-batch control 的 constrained selection smoke 足以开启 B2-min 设计；边界为 calibrated / no-retraining / explicit qmatch / full-batch 为唯一验收口径，ORIG raw remains known_fail，selected chunk 仅限 triage 不得替代 full-batch gate，100/200ep scaling 与新训练未获授权。
```
