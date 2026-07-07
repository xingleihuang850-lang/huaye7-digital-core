# HY7 Stage 3 qmatch route design card — run01 remediation planning

Date: 2026-07-07

## Status

```text
workflow_node=HY7-stage3-branch-A-route-design-card-after-remediation-plan
parent_smoke_verdict=REDESIGN_BEFORE_ANY_A2_SMALL_GATE
post_audit_verdict=KEEP_REDESIGN_AND_WRITE_ROUTE_REMEDIATION_PLAN
scientific_status=diagnostic_metadata_only_not_evidence
execution_authorized=false
second_smoke_authorized=false
A2_small_authorized=false
A2_medium_authorized=false
training_authorized=false
checkpoint_authorized=false
```

This is a design/planning card only. It does not authorize implementation, training, checkpoint operations, second smoke, A2-small, A2-medium, scientific acceptance, qmatch formal acceptance, validated permeability, B2-min final pass, or generative digital-well claims.

## Inputs and frozen evidence

```text
route_label=nnUNet ep015_qmatch
route_status=diagnostic_calibrated_route_only
calibration_version=hy7-gray-calibration-qmatch-v1
formal_anchor=ep015_all planning_anchor_only
failed_chunk=ep015_chunk000_063 visible negative evidence
source_sha256_verified=24655b96b3f50ad14f8c60548afa9e0169babb76c24b605efa870e741502b7b2
slice_range=384:448
audit_volume_shape=64x128x128
axis_0_to_slice_stacking_mapping=verified
```

Evidence package references:

```text
stage3_inter_slice_audit_package_20260707_run01/
stage3_inter_slice_audit_post_review_record_20260707.md
stage3_route_remediation_plan_20260707_run01.md
stage3_route_remediation_plan_20260707_run01.json
```

## Design problem

The run01 qmatch 2D-stack has adequate individual-slice pore presence but poor stacking-axis continuity:

```text
s2_x_over_min_yz=0.09496368732593648
adjacent_slice_jaccard_x.median=0.028101802757158005
adjacent_slice_dice_x.median=0.05466735430634347
component_persistence_pairwise_median=0.028101802757158005
per_slice_pore_count_robust_z_abs.max=4.3526328125000004
```

The design target is therefore not “find a percolating volume”. The target is to define a future route family that can be fairly reviewed for inter-slice coherence without hiding A2 execution, checkpoint selection, or permeability claims.

## Candidate route families

### Route family R1 — 2.5D/slab-context inference design

Planning concept: condition each target slice on neighboring slices while keeping the output slice-wise and qmatch semantics explicit.

Potential advantages:

```text
addresses independent-slice context gap directly
less invasive than full 3D training
can preserve 2D annotation/interface assumptions if later authorized
```

Design risks:

```text
slab width may smooth true thin/disconnected pores
qmatch calibration may need a new versioned semantics layer
future training/inference would require separate gate
```

Pre-gate design requirements:

```text
slab_width_candidates declared before execution
axis/stack provenance manifest required
failed_chunk ep015_chunk000_063 remains visible
no checkpoint selection or retraining in this card
```

### Route family R2 — inter-slice consistency regularization design

Planning concept: add a future constraint or loss that discourages abrupt adjacent-slice topology flicker while preserving geological discontinuities.

Potential advantages:

```text
directly targets low component persistence and S2 x/y,z imbalance
could be evaluated with metadata-only continuity probes if separately authorized
```

Design risks:

```text
could fabricate continuity if over-weighted
requires training/fine-tuning gate before any use
must not be described as permeability improvement
```

Pre-gate design requirements:

```text
regularizer objective labelled diagnostic-continuity-only
anti-over-smoothing controls specified
qmatch/formal acceptance separation preserved
```

### Route family R3 — calibration-route redesign

Planning concept: re-examine whether qmatch thresholding/calibration can be made slice-context-aware or replaced by a diagnostic route with explicit dimensional-lifting stability checks.

Potential advantages:

```text
targets possible slice-wise fragmentation introduced by calibration
keeps route semantics versioned and auditable
```

Design risks:

```text
calibration can become hidden acceptance if not fenced
formal anchor can be contaminated if qmatch/formal semantics are merged
```

Pre-gate design requirements:

```text
new calibration version required before any execution
formal_anchor remains planning-anchor-only
raw failure and qmatch pass/fail must both remain visible
```

### Route family R4 — metadata-only post-processing design review

Planning concept: review possible cleanup operations that reduce isolated slice flicker without creating false 3D connectivity.

Potential advantages:

```text
may expose whether route failure is post-processing-sensitive
could be evaluated as design only before any execution
```

Design risks:

```text
highest risk of connectivity fabrication
can easily be mistaken for scientific improvement
```

Pre-gate design requirements:

```text
forbidden operations list required before any execution
connectivity-fabrication guard required
raw-vs-processed evidence must remain paired
```

## Current design preference

```text
primary_design_candidate=R1_2.5D_slab_context_inference_design
secondary_design_candidate=R3_calibration_route_redesign
tertiary_design_candidate=R2_inter_slice_consistency_regularization_design
post_processing_review=R4_metadata_only_post_processing_design_review_as_last_resort
```

Reasoning: R1 addresses the leading root cause — independent 2D slice inference lacking cross-slice context — while avoiding immediate full 3D execution. R3 is paired because qmatch calibration semantics may need to be versioned for slab-context behavior. R2 is potentially useful but would require a training gate and stronger anti-fabrication controls. R4 is risky and should not be used to claim connectivity.

## Future route-feasibility review questions

A later review, still non-execution unless separately authorized, should answer:

```text
can R1 preserve qmatch calibration semantics without merging formal acceptance?
can axis/stack provenance be made unambiguous before any future run?
can failed_chunk ep015_chunk000_063 remain a visible negative control?
can a future audit target s2_x_over_min_yz >=0.25 and pairwise persistence >=0.10 without cherry-picking?
can future outputs stay diagnostic_metadata_only until a scientific gate exists?
```

## Proposed future non-execution package pieces

If the project proceeds to a route-feasibility review request, the package should include only documentation/metadata:

```text
route_design_card.md
route_design_checklist.json
axis_stack_provenance_manifest.md
qmatch_semantics_separation.md
failed_chunk_visibility_plan.md
future_metric_thresholds.json
forbidden_claims.txt
hashes.txt
```

## Forbidden claims and actions

```text
second_smoke_authorized=false
A2_small_authorized=false
A2_medium_authorized=false
training_authorized=false
checkpoint_authorized=false
qmatch_formal_acceptance_claim_authorized=false
validated_permeability_claim_authorized=false
generative_digital_well_claim_authorized=false
```

Do not create or commit `.npy`, `.npz`, `.pt`, weights, checkpoints, voxel arrays, or processed volume exports as part of this design card.
