# HY7 handoff bundle → Stage 3 planning promotion gate — 2026-07-06

## Workflow node

- Node: `HY7-handoff-stage3-planning-promotion-gate`
- Gate target: `Component C no-retraining calibrated handoff bundle dry-run`
- Gate question: whether the handoff bundle can be used as input for Stage 3 `multiscale 3D digital core planning`.
- MoA provider: `moa`
- MoA preset/model: `digital-rock-gate`
- Command form:

```bash
hermes -z "$(python3 - <<'PY'
from pathlib import Path
print(Path('/Users/hxl/Documents/Hermes工作区/99_临时文件与一次性输出/rock_handoff_stage_entry_gate_20260706.md').read_text())
PY
)" --provider moa -m digital-rock-gate
```

## MoA evidence

`hermes moa list` immediately before the review showed:

```text
digital-rock-gate
Reference models:
  1. openai-codex:gpt-5.5
  2. deepseek:deepseek-v4-pro
  3. openrouter:z-ai/glm-5.2
  4. custom:dk-claude:claude-fable-5
Aggregator: custom:dk-claude:claude-opus-4-8
```

Smoke test:

```bash
hermes -z '请只输出 OK-ROCK，不要解释。' --provider moa -m digital-rock-gate
```

Output:

```text
OK-ROCK
```

Full MoA output was captured at:

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/handoff_stage_entry_gate_moa_output_20260706.md
```

## Reviewed bundle

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/handoff_bundle_ep015_20260706/
```

Required files present and internally hash-verified:

```text
handoff_manifest.json: OK
handoff_readme.md: OK
formal_vs_qmatch_metrics.json: OK
candidate_rows.json: OK
forbidden_claims.txt: OK
audit_report.json: OK
ordered_view_links.txt: OK
```

Key manifest fields:

```text
status=calibrated_b2_min_handoff_design_dry_run
main_checkpoint=ep015
calibration_version=hy7-gray-calibration-qmatch-v1
orig_raw_status=known_fail
execution_boundary=no_retraining_no_new_sampling_no_scaling_no_new_checkpoint
acceptance_anchor=ep015_all
selected_chunk_policy=triage_only
formal_route=threshold_formal_full_batch
nnunet_route=qmatch_nnunet_diagnostic
downstream_target=multiscale_3d_digital_core_planning
```

Audit report:

```text
passed=true
errors=[]
checks=18
```

## Verdict

```text
PROMOTE_WITH_CONSTRAINTS
```

Gate level:

```text
stage-3-planning-input only
```

Meaning:

- The handoff bundle is promoted as a Stage 3 multiscale 3D digital core **planning input**.
- This does **not** authorize B2-min final result acceptance.
- This does **not** authorize 3D generation, voxel export, training, new sampling, 100/200ep scaling, new checkpoint, or production/scientific acceptance claims.

## Reasons accepted by the gate

1. Integrity: bundle hashes verify for all committed handoff files.
2. Provenance: manifest `source_sha256` values match the local mirrored upstream baseline manifest, selection summary, and qmatch manifest.
3. Audit: `audit_report.json` passed with 18 checks and 0 errors.
4. Formal anchor: full-batch `ep015_all` is the acceptance/planning anchor:

```text
n=512
phi=6.442654132843018
S2 rmse=0.0002854642510439182
Euler=121.26953125
maxCC=0.06397858477862998
pass_gate=True
policy=acceptance_anchor
```

5. formal vs qmatch separation is explicit:

```text
formal512 ep015@phi6.4:
  S2 rmse=0.00034034164909631633
  Euler=120.810546875
  maxCC=0.06408827658203413
  passed_gate=True

nnUNet ep015_qmatch:
  phi=5.794930458068848
  S2 rmse=0.0017214588891168259
  Euler=116.154296875
  maxCC=0.06510709034871634
  reverse_fail=False
```

6. Negative evidence remains visible:

```text
ep015_chunk000_063:
  pass_gate=False
  failure_reasons=["maxCC>0.070"]
  maxCC=0.07163110510281959
```

7. The selected 64-slice row remains `triage_only` and is not used as full-model performance.

## Allowed next actions

- Register this bundle as Stage 3 multiscale 3D digital core planning input.
- Draft Stage 3 planning memo / requirements / design card.
- Build a constraints matrix carrying forward:
  - formal route,
  - qmatch route,
  - triage chunks,
  - failed row,
  - forbidden claims.
- Define Stage 3 gate drafts and metric routes.
- Use `ep015_all` as planning anchor only.
- Use qmatch diagnostics only with explicit route labels.
- Clarify/upgrade connectivity/percolation semantics before any final Stage 3 design or 3D execution.

## Still forbidden

- B2-min final pass claim.
- B1.1 unconditional pass claim.
- ORIG raw pass claim.
- implicit qmatch.
- second B1.1 topology rescue.
- gate relaxation.
- new training.
- new sampling.
- scaling or 100/200ep expansion.
- new checkpoint.
- actual 3D generation / voxel export / production acceptance.
- treating the selected 64-slice chunk as full-model performance.
- merging formal route with nnUNet-qmatch route.
- treating planning-input promotion as final scientific validation.

## Required strengthening before Stage 3 design finalization

### Blocking for final Stage 3 design

- Clarify connectivity / percolation semantics.

The MoA review flagged `x_penetrate=0.0 / y_penetrate=0.0` as a planning risk. The repo code defines these in `src/hy7_phase2_eval.py` as:

```text
x_penetrate: 最大连通簇同时接触左/右边界的 tile 比例（x 方向贯通）。
y_penetrate: 最大连通簇同时接触上/下边界的 tile 比例（y 方向贯通）。
```

Therefore, for Stage 3 planning, `x_penetrate=0.0 / y_penetrate=0.0` must be interpreted as **no detected 2D tile-level largest-connected-component spanning in x/y under the current threshold route**, not as evidence of 3D permeability or 3D connectivity. Stage 3 must define separate 3D/z-direction connectivity or percolation checks before any generation/execution claim.

### Non-blocking but mandatory in the Stage 3 planning memo

- Record chunk threshold drift: per-chunk thresholds vary among `-0.6125`, `-0.625`, `-0.6375`; chunk rows are triage, not one fixed-threshold stratified validation.
- Record formal vs qmatch porosity difference: formal `phi≈6.44`, nnUNet-qmatch `phi≈5.79`; no unlabelled merge.
- Record candidate_rows structure: 8 chunks + 1 full-batch row; do not double-count `sum_n=1024` as independent sample count.
- Carry failed chunk `ep015_chunk000_063` as a spatial heterogeneity / maxCC risk input.
- Record that selection provenance hash in manifest refers to `selection_summary.json`, not `selection_summary.md`.
- Add a short human-readable explanation of `hy7-gray-calibration-qmatch-v1` and threshold route.

## One-sentence decision for notes/30

HY7 B2-min 校准无重训交接束哈希与上游溯源全验通过、审计 18/18、双路线分离且负证据可见，经 digital-rock-gate 判定 `PROMOTE_WITH_CONSTRAINTS`，批准升级为 Stage 3 多尺度 3D 数字岩心**规划输入**（仅规划级，带全部禁令与 2D/3D connectivity 语义补强约束），不授权 3D 生成、训练/扩量或最终科学验收。
