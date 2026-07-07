# HY7 Stage 3 route-remediation plan after inter-slice audit — run01

Date: 2026-07-07

## Status

```text
workflow_node=HY7-stage3-branch-A-route-remediation-plan-after-inter-slice-audit
parent_smoke_verdict=REDESIGN_BEFORE_ANY_A2_SMALL_GATE
post_audit_verdict=KEEP_REDESIGN_AND_WRITE_ROUTE_REMEDIATION_PLAN
scientific_status=diagnostic_metadata_only_not_evidence
second_smoke_authorized=false
A2_small_authorized=false
A2_medium_authorized=false
training_authorized=false
checkpoint_authorized=false
```

This is a documentation/planning artifact only. It does not run or authorize second smoke, A2-small, A2-medium, full 2D→3D reconstruction, training, fine-tuning, checkpoint creation/selection, scientific acceptance, qmatch formal acceptance, validated permeability, B2-min final pass, or generative digital-well claims.

## Evidence base

Inter-slice audit package:

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_inter_slice_audit_package_20260707_run01/
```

Post-audit review:

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_inter_slice_audit_post_review_record_20260707.md
verdict=KEEP_REDESIGN_AND_WRITE_ROUTE_REMEDIATION_PLAN
```

Frozen route/provenance:

```text
route_label=nnUNet ep015_qmatch
route_status=diagnostic_calibrated_route_only
calibration_version=hy7-gray-calibration-qmatch-v1
formal_anchor=ep015_all planning_anchor_only
failed_chunk=ep015_chunk000_063 visible negative evidence
source_sha256_verified=24655b96b3f50ad14f8c60548afa9e0169babb76c24b605efa870e741502b7b2
slice_range=384:448
full_array_shape=512x128x128
audit_volume_shape=64x128x128
axis_0_to_slice_stacking_mapping=verified
```

## Diagnostic drivers

The route-remediation need is driven by four diagnostic observations:

1. **S2 stacking-axis collapse**

```text
s2_lag1.x=0.0033976236979166665
s2_lag1.y=0.0357781357652559
s2_lag1.z=0.037223755843996065
s2_x_over_y=0.09496368732593648
s2_x_over_z=0.09127568191012299
s2_x_over_min_yz_lt_0.25=true
```

2. **Low adjacent-slice pairwise persistence**

```text
adjacent_slice_jaccard_x.median=0.028101802757158005
adjacent_slice_dice_x.median=0.05466735430634347
component_persistence_pairwise_median_lt_0.10=true
```

3. **Per-slice pore-count outliers**

```text
per_slice_pore_count_robust_z_abs.max=4.3526328125000004
per_slice_pore_count_robust_z_abs_gt_3.5=true
```

4. **Non-degenerate but incoherent volume**

```text
zero_or_near_zero_pore_slice_runs.longest_run=0
zero_or_near_zero_pore_slice_run_ge_3=false
jaccard_x_median_over_yz_median_lt_0.25=false
```

This pattern suggests pores exist in individual slices, but the qmatch 2D-stack does not preserve adequate inter-slice continuity.

## Ranked route-level hypotheses

1. **Independent 2D-slice inference lacks cross-slice context**

The route may produce plausible per-slice masks while ignoring continuity across axis 0. This is the leading hypothesis because axis 0 is verified as the slice-stacking axis and x-axis S2 is less than 10% of y/z.

2. **No explicit 3D consistency regularization / post-processing**

The current diagnostic route appears to lack constraints that penalize slice-to-slice topology flicker. Low adjacent-slice Jaccard/Dice is consistent with topology flicker.

3. **qmatch calibration may fragment continuity across slices**

qmatch improves the 2D diagnostic route under its calibration objective, but may sharpen or threshold structures inconsistently slice by slice. qmatch remains diagnostic and not formal acceptance.

4. **Checkpoint/ensemble route may be 2D-good but 3D-incoherent**

The selected route may pass 2D-oriented proxies while failing dimensional-lifting stability. This is a route-design issue, not a reason to select or create checkpoints now.

5. **Stacking/preprocessing convention risk remains worth independent review**

Axis 0 mapping is verified in the audit package, but remediation should still require a source-to-stack provenance review before any future implementation change.

## Non-execution remediation directions

These are planning directions only; none authorizes implementation, training, checkpoint selection, or new inference.

### Option A — 2.5D / slab-context inference design

Design a future route that conditions each slice on neighboring slices, e.g. input slabs around the target slice. Goal: reduce slice-to-slice topology flicker without immediately requiring full 3D training.

Planning questions:

```text
what slab width is geologically/plausibly local?
how to preserve qmatch calibration semantics?
how to evaluate held-out inter-slice continuity without cherry-picking?
```

### Option B — explicit inter-slice consistency regularization

Design a future loss/constraint that penalizes abrupt adjacent-slice mask changes while preserving pore geometry. This would require a separate training gate if ever implemented.

Planning questions:

```text
what continuity proxy is safe and not a permeability proxy?
how to avoid over-smoothing genuine thin disconnected pores?
how to keep failed chunk evidence visible?
```

### Option C — metadata-only post-processing design review

Evaluate whether future post-processing could reduce isolated slice flicker without fabricating 3D connectivity. This is only a design review; no current post-processing should be applied to claim scientific evidence.

Planning questions:

```text
what operations would be forbidden as connectivity fabrication?
what operations would be label-preserving cleanup only?
how to pre-register before any execution?
```

### Option D — calibration-route redesign

Review whether qmatch calibration should be made slice-context-aware, held-out-interval-aware, or replaced by a route with explicit 3D diagnostic stability checks.

Planning questions:

```text
can qmatch remain a diagnostic route only?
which formal anchor stays separate?
how to prevent qmatch from becoming hidden acceptance?
```

### Option E — route feasibility decision framework

If future planning shows that 2D-only qmatch cannot meet inter-slice stability thresholds without unauthorized training/checkpoint changes, prepare a later gate to stop or redesign Branch A route. This plan does not make that decision.

## Future threshold targets before any later gate discussion

These are proposed planning targets for a future gate package, not current acceptance criteria:

```text
s2_x_over_min_yz_target_ge=0.25
component_persistence_pairwise_median_target_ge=0.10
per_slice_pore_count_robust_z_abs_target_le=3.5
adjacent_slice_jaccard_x_median_target_ge=0.05
adjacent_slice_dice_x_median_target_ge=0.10
zero_or_near_zero_pore_slice_run_target_lt=3
```

Any future threshold must be re-registered in the relevant gate request before data is read or computed.

## Future gate prerequisites, if any route-remediation execution is later proposed

```text
separate strict gate required
route design card with no hidden A2 execution
axis/stacking provenance manifest
failed chunk ep015_chunk000_063 preserved as negative evidence
qmatch/formal anchor semantics separated
no checkpoint creation/selection without explicit gate
no training/fine-tuning without explicit gate
no volume arrays committed
all outputs labelled diagnostic_metadata_only until a future scientific gate says otherwise
```

## Explicit authorization statement

```text
second_smoke_authorized=false
A2_small_authorized=false
A2_medium_authorized=false
full_2d_to_3d_campaign_authorized=false
training_authorized=false
checkpoint_authorized=false
scientific_acceptance_claim_authorized=false
qmatch_formal_acceptance_claim_authorized=false
validated_permeability_claim_authorized=false
generative_digital_well_claim_authorized=false
```

This plan does not alter `REDESIGN_BEFORE_ANY_A2_SMALL_GATE`. It does not reopen or modify the parent smoke gate. It only records planning-level route-remediation hypotheses and future non-execution criteria.

## Hash manifest

See:

```text
stage3_route_remediation_plan_20260707_run01.hashes.txt
```
