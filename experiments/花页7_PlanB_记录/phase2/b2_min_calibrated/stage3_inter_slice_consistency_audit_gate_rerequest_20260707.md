# HY7 Stage 3 corrected inter-slice consistency audit gate re-request — 2026-07-07

## Gate question

After correcting the prior planning artifacts, may HY7 Stage 3 Branch A implement/run one metadata-only inter-slice consistency audit package, using the already-touched external qmatch diagnostic candidate only to compute pre-registered slice-continuity metadata?

This remains before and separate from any future second-smoke or A2-small discussion.

## Candidate verdicts

Choose exactly one:

```text
ALLOW_METADATA_ONLY_INTER_SLICE_AUDIT_WITH_CONSTRAINTS
REQUIRE_FIXES_BEFORE_AUDIT_GATE
DO_NOT_RUN_AUDIT
```

## Corrected artifacts

```text
stage3_inter_slice_consistency_audit_plan_20260707.md
stage3_inter_slice_consistency_audit_checklist_20260707.json
```

Prior blocking issue from `REQUIRE_FIXES_BEFORE_AUDIT_GATE` was downstream second-smoke implication language. It has been removed/neutralized:

```text
removed: plan heading "Candidate for second-smoke request only after new gate"
removed: checklist key decision_criteria.second_smoke_request_candidate_only_if
added: no_second_smoke_implication=true
added: no_a2_small_implication=true
added: post_audit_downstream_status=out_of_scope
added: audit_result_does_not_authorize_or_imply_second_smoke=true
added: audit_result_does_not_authorize_or_imply_A2_small=true
```

## Current authorization state

```text
parent_smoke_verdict=REDESIGN_BEFORE_ANY_A2_SMALL_GATE
scientific_status=planning_only_not_evidence
current_execution_authorized=false
ready_for_second_smoke=false
ready_for_a2_small_gate=false
```

## Frozen route/provenance

```text
route_label=nnUNet ep015_qmatch
route_status=diagnostic_calibrated_route_only
calibration_version=hy7-gray-calibration-qmatch-v1
formal_anchor=ep015_all planning_anchor_only
failed_chunk=ep015_chunk000_063 visible negative evidence
not_a_generative_digital_well=true
source_path=hy7-linux:/home/user/HXL/HY7_planb/phase2/b1_gray_sus_b11_rescue20_nnunet_review_20260706/ep015_qmatch_pore_nnunet2d.npy
source_sha256=24655b96b3f50ad14f8c60548afa9e0169babb76c24b605efa870e741502b7b2
slice_range=384:448
shape=64x128x128
```

## Pre-registered metrics and thresholds

```text
per_slice_porosity_mean_std_min_max
adjacent_slice_jaccard_distribution_along_x
adjacent_slice_dice_distribution_along_x
adjacent_slice_overlap_drop_flags
component_persistence_across_adjacent_slices_2d_pairwise_proxy_not_3d_percolation
run_length_of_connected_foreground_across_x_2d_pairwise_proxy_not_3d_percolation
s2_lag1_x_y_z_with_boundary_label
s2_anisotropy_ratios_x_over_y_and_x_over_z
per_slice_pore_count_outlier_flags
```

Thresholds for negative-evidence flagging only, not acceptance:

```text
jaccard_x_median_over_yz_median_lt=0.25
s2_x_over_min_yz_lt=0.25
component_persistence_pairwise_median_lt=0.10
per_slice_pore_count_robust_z_abs_gt=3.5
zero_or_near_zero_pore_slice_run_ge=3
```

## Required controls

```text
first_check_fail_closed=axis_0_to_slice_stacking_mapping_for_384_448_range_must_be_verified_before_any_metric
axis_convention_control
boundary_convention_control
failed_chunk_visibility_control
no_cherry_pick_control
no_formal_route_merge_control
no_artifact_leakage_control
no_heavy_inference_import_control
source sha256 re-verified before metrics
no intermediate array persistence except deleted scratch outside repo
forbidden imports: torch, tensorflow, nnunet
```

## Proposed 9-file package if allowed

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

## Still forbidden regardless of verdict

```text
second smoke execution without a later strict gate
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

Requested output: verdict, remaining blocking fixes if any, and exact next allowed action. Do not authorize second smoke or A2-small.
