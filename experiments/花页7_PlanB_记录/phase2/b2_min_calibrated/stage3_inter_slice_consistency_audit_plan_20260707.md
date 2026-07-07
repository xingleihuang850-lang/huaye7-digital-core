# HY7 Stage 3 inter-slice consistency audit plan — 2026-07-07

## Status

```text
workflow_node=HY7-stage3-branch-A-inter-slice-consistency-audit-plan
parent_verdict=REDESIGN_BEFORE_ANY_A2_SMALL_GATE
scientific_status=planning_only_not_evidence
execution_authorized=false
ready_for_second_smoke=false
ready_for_a2_small_gate=false
```

This is a metadata-only audit plan. It does not authorize a second smoke, A2-small, A2-medium, training, checkpoint operations, full 2D→3D reconstruction, scientific acceptance, qmatch formal acceptance, validated permeability, or a generative digital-well claim.

## Parent evidence

Parent smoke package:

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_minimal_3d_smoke_package_20260707_run01_qmatch_candidate/
```

Parent post-run review:

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_minimal_3d_smoke_post_run_review_record_20260707.md
verdict=REDESIGN_BEFORE_ANY_A2_SMALL_GATE
```

Frozen route/provenance to preserve:

```text
route_label=nnUNet ep015_qmatch
route_status=diagnostic_calibrated_route_only
calibration_version=hy7-gray-calibration-qmatch-v1
formal_anchor=ep015_all planning_anchor_only
failed_chunk=ep015_chunk000_063 visible negative evidence
candidate_source=hy7-linux:/home/user/HXL/HY7_planb/phase2/b1_gray_sus_b11_rescue20_nnunet_review_20260706/ep015_qmatch_pore_nnunet2d.npy
candidate_source_sha256=24655b96b3f50ad14f8c60548afa9e0169babb76c24b605efa870e741502b7b2
parent_slice_range=384:448
parent_candidate_shape=64x128x128
```

Parent negative evidence to keep visible:

```text
percolation_flags_3d={x:false,y:false,z:false}
connected_porosity_pore_basis=0.005316792202038104
connected_porosity_total_basis=0.000308990478515625
S2_lag1_valid_no_wrap={x:0.0033976236979166665,y:0.0357781357652559,z:0.037223755843996065}
physical_proxy_flow={x:0,y:0,z:0}
euler_minkowski_status=explicitly_de_scoped_fail_closed
```

## Audit question

Can the parent smoke’s all-axis non-percolation and x-axis S2 collapse be explained or bounded by inter-slice 2D-inference / 2D→3D assembly inconsistency before any future second smoke is requested?

Not the question:

```text
Can A2-small start?
Can qmatch be accepted as formal route?
Can the diagnostic proxy be treated as permeability?
Can a new candidate be generated or cherry-picked?
```

## Required audit inputs for a future execution gate

A future metadata-only audit execution, if separately authorized, may read existing external arrays but must not write arrays to git. Required inputs:

```text
qmatch candidate array path and sha256
slice range(s) to inspect, pre-registered
axis mapping declaration: x/y/z -> ndarray axes 0/1/2
route label and calibration version
failed chunk ep015_chunk000_063 record
parent smoke package hashes
```

Optional comparison inputs, still metadata-only:

```text
formal threshold anchor metadata for ep015_all
failed chunk ep015_chunk000_063 metrics
neighbor chunk metadata around 384:448
qmatch generalization summaries if formally copied into evidence package
```

## Planned metrics: inter-slice consistency

For a future audit run, compute only lightweight metadata/statistics, not new scientific volumes. Axis mapping must be verified first; no other metric may be interpreted if axis 0 cannot be tied to the 384:448 slice-stacking range.

```text
per_slice_porosity_mean_std_min_max
adjacent_slice_jaccard_distribution along x
adjacent_slice_dice_distribution along x
adjacent_slice_overlap_drop_flags
component_persistence_across_adjacent_slices 2D-pairwise proxy, not 3D percolation
run_length_of_connected_foreground_across_x 2D-pairwise proxy, not 3D percolation
S2 lag-1 x/y/z recomputed with boundary label
S2 anisotropy ratios: x/y and x/z
per-slice pore-count outlier flags
```

Pre-registered diagnostic thresholds for flagging negative evidence only:

```text
jaccard_x_median_over_yz_median_lt_0.25
s2_x_over_min_yz_lt_0.25
component_persistence_pairwise_median_lt_0.10
per_slice_pore_count_robust_z_abs_gt_3.5
zero_or_near_zero_pore_slice_run_ge_3
```

These thresholds are not pass/fail scientific acceptance criteria and do not authorize downstream execution.

All metrics must be labelled:

```text
status=diagnostic_metadata_only
not_permeability=true
not_scientific_acceptance=true
not_formal_qmatch_acceptance=true
no_second_smoke_implication=true
no_a2_small_implication=true
low_n_caveat=64 slices / 63 adjacent pairs; descriptive, not confirmatory
```

## Planned controls

Minimum controls before interpreting any future audit:

1. **Axis convention control** — first prove axis 0 in the package is the slice-stacking axis for the pre-registered 384:448 range before calling x-S2 an inter-slice signal; fail closed on ambiguity.
2. **Boundary convention control** — keep `lag_1_valid_pairs_no_wrap_no_periodic_boundary`; no periodic wrapping.
3. **Failed chunk visibility control** — include ep015_chunk000_063 in the audit record, even if not re-read.
4. **No cherry-pick control** — any additional slice windows must be pre-registered before reading results.
5. **No formal-route merge control** — formal threshold anchor and qmatch diagnostic route must remain separate.
6. **No artifact leakage control** — no `.npy`, `.npz`, `.pt`, weights, checkpoints, or voxel exports in git.
7. **No heavy inference import control** — future implementation must not import torch, tensorflow, nnunet, or training/checkpoint libraries.

## Diagnostic interpretation limits after a future audit

The audit result may only refine root-cause interpretation and implementation risk. It must not authorize or imply downstream execution:

```text
post_audit_downstream_status=out_of_scope
audit_result_does_not_authorize_or_imply_second_smoke=true
audit_result_does_not_authorize_or_imply_A2_small=true
any_future_execution_gate_is_separate_and_not_discussed_here=true
```

Keep `REDESIGN_BEFORE_ANY_A2_SMALL_GATE` if any pre-registered diagnostic threshold flags route/assembly risk:

```text
jaccard_x_median_over_yz_median_lt_0.25
s2_x_over_min_yz_lt_0.25
component_persistence_pairwise_median_lt_0.10
per_slice_pore_count_robust_z_abs_gt_3.5
zero_or_near_zero_pore_slice_run_ge_3
```

### Stop / route redesign

Recommend stop or route redesign if:

```text
inter-slice consistency failure is severe and systematic across pre-registered windows
qmatch diagnostic route cannot preserve 3D continuity without new model design
route remediation would require training, checkpoint selection, or non-authorized inference
```

## Required future audit package files

If a future gate authorizes execution of this metadata-only audit, write a package with:

```text
inter_slice_audit_manifest.json
inter_slice_audit_readme.md
input_route_manifest.json
candidate_source_manifest.json
inter_slice_metrics.json
axis_boundary_semantics.md
negative_evidence.md
forbidden_claims.txt
hashes.txt
```

## Still forbidden

```text
second smoke execution without new strict gate
A2-small execution
A2-medium execution
full 2D-to-3D reconstruction campaign
training or fine-tuning
checkpoint creation or selection
large volume export as scientific output
HY7 scientific acceptance claim
B2-min final pass claim
qmatch formal acceptance claim
validated permeability claim
generative digital-well claim
cherry-picked rerun to find percolation
hiding failed chunk ep015_chunk000_063
committing .npy/.npz/.pt/weights/checkpoints/voxel arrays
```
