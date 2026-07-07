# OpenCode handoff — HY7 digital-rock code ownership lane

Date: 2026-07-07

## Purpose

The coding lane for this repository is now handed to OpenCode. Hermes will continue the research/gate/interpretation lane, while OpenCode owns code inspection, cleanup, normalization, code documentation, and code-provenance explanation.

This handoff is intentionally strict: OpenCode should first make the existing code understandable before changing scientific behavior.

## Repository

```text
/Users/hxl/Documents/Hermes工作区/01_Claude接管剩余工作/claude
branch=main
latest known commit before handoff=3dd8f49 docs: record route design completion gate
remote=https://github.com/xingleihuang850-lang/huaye7-digital-core.git
```

Current untracked directory to leave untouched unless user explicitly says otherwise:

```text
experiments/花页7_PlanB_记录/phase2/local_pulled_20260706_b11_readable/
```

## Division of labor

### Hermes continues

```text
research interpretation
scientific gate design and MoA review
literature/context synthesis
HY7 route decisions
claims boundary enforcement
```

### OpenCode owns

```text
codebase audit
source/test cleanup
style and naming normalization
module dependency map
test coverage gap map
code provenance documentation
per-file explanation of how code was written and why
future refactor implementation after audit report
```

## First OpenCode task: read-only code audit and provenance report

Do not refactor source code in the first pass. Create documentation artifacts only.

Deliverables:

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/opencode_code_audit_report_20260707.md
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/opencode_code_audit_inventory_20260707.json
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/opencode_code_cleanup_plan_20260707.md
```

For each meaningful file under `src/` and matching tests under `tests/`, report:

```text
file path
role in workflow
main functions/classes/CLI entry points
data inputs and outputs
which experiment/package/notes use it
which tests cover it
how it appears to have been written or evolved
references to notes/literature/evidence that justify the algorithm
associated data provenance
geological / petrophysical / logging / digital-rock theory assumptions
known limitations or scientific-claim boundaries
cleanup/refactor recommendations
```

## Must explicitly map these current code clusters

### Stage 3 downstream-validity cluster

```text
src/hy7_stage3_minimal_3d_smoke.py
tests/test_hy7_stage3_minimal_3d_smoke.py
src/hy7_stage3_inter_slice_audit.py
tests/test_hy7_stage3_inter_slice_audit.py
src/hy7_stage3_branch_a_a1_toy.py
tests/test_hy7_stage3_branch_a_a1_toy.py
```

Context files:

```text
notes/30_阶段二_B11输出校准与checkpoint选择.md
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_minimal_3d_smoke_package_20260707_run01_qmatch_candidate/
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_inter_slice_audit_package_20260707_run01/
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_route_design_card_20260707_run01.md
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_route_design_completion_gate_record_20260707.md
```

Current scientific boundary:

```text
parent_smoke_verdict=REDESIGN_BEFORE_ANY_A2_SMALL_GATE
scientific_status=diagnostic_metadata_only_not_evidence
execution_authorized=false
second_smoke_authorized=false
A2_small_authorized=false
training_authorized=false
checkpoint_authorized=false
```

### B2-min calibrated handoff cluster

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

Context files:

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/
notes/30_阶段二_B11输出校准与checkpoint选择.md
```

### Phase 2 DDPM / calibration cluster

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

Context files:

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

### PlanB data/segmentation cluster

```text
src/hy7_planb_*.py
src/hy7_ct14_make_nnunet_3phase.py
src/hy7_amics_make_nnunet.py
src/hy7_etl.py
src/etl_build_warehouse.py
```

Context files:

```text
notes/10_阶段一_分割研究设计.md
notes/11_阶段一_早期研究设计与路线.md
notes/12_阶段一_PlanB对齐分割管线.md
notes/13_阶段一_PlanB实验记录_E0.md
notes/14_阶段一_E1裂缝收敛实验.md
notes/15_阶段一_E2_ct28配准对照.md
notes/16_阶段一_E3_nnUNet同网格核验.md
notes/17_阶段一_S3_Amics多矿物分割.md
notes/18_阶段一_codex实验核查与边界.md
notes/19_阶段一_官页15-1-1_T0613分割基准.md
```

### Reporting/productivity cluster

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

## Research/provenance questions OpenCode must answer

For each code cluster and each important algorithm, answer:

1. What problem is this code solving in the HY7 workflow?
2. Which notes or experiment records show why it was needed?
3. What data does it use?
4. What are the source paths / hashes / manifests for that data, if present?
5. Which public theory/literature category does the code rely on?
   - digital rock physics
   - pore connectivity/percolation
   - two-point correlation / spatial statistics
   - Euler/Minkowski/topology
   - DDPM/diffusion generation
   - nnUNet/segmentation
   - intensity/gray calibration
   - logging/electrical-imaging constraints
   - shale/mineralogy/petrophysical assumptions
6. Which statements are only diagnostic proxies and not scientific acceptance?
7. Which code paths must not be used to claim permeability, qmatch formal acceptance, B2-min final pass, or digital-well validity?
8. Which parts need clearer docstrings/comments/tests before future coding?

## Mandatory boundaries for OpenCode

Do not do any of the following in the first pass:

```text
no source-code refactor yet
no training or fine-tuning
no checkpoint creation or selection
no model inference execution
no second smoke
no A2-small/A2-medium
no route-feasibility review execution
no post-processing execution
no scientific acceptance claim
no qmatch formal acceptance claim
no validated permeability claim
no generative digital-well claim
no committing .npy/.npz/.pt/weights/checkpoints/voxel arrays
```

Allowed in first pass:

```text
read files
run existing tests if needed
inspect git history
write the three OpenCode audit/planning docs listed above
suggest refactor tasks for a later pass
```

## Verification expectations

Before saying the audit is done, OpenCode should run at least:

```bash
python3 -m pytest tests/test_hy7_stage3_inter_slice_audit.py -q
python3 -m pytest tests/test_hy7_stage3_minimal_3d_smoke.py -q
python3 -m pytest tests -q
```

If full tests fail due to environment, report the concrete blocker and do not claim suite green.

Also verify that the new audit docs do not introduce forbidden binary artifacts:

```bash
python3 - <<'PY'
from pathlib import Path
bad=[str(p) for p in Path('experiments/花页7_PlanB_记录/phase2/b2_min_calibrated').rglob('*') if p.suffix in {'.npy','.npz','.pt'}]
print('FORBIDDEN_UNDER_B2_MIN', bad)
assert not bad
PY
```

## Output standard

The report must be understandable to a researcher who wants to know where the code came from, what evidence it used, what theory it encodes, and where it is only a proxy.

Write in Chinese unless code identifiers or cited file paths require English.
