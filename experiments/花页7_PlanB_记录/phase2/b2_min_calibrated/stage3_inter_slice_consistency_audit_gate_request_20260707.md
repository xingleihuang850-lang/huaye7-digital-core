# HY7 Stage 3 inter-slice consistency audit gate request — 2026-07-07

## Gate question

May HY7 Stage 3 Branch A run one metadata-only inter-slice consistency audit, using the already-touched external qmatch diagnostic candidate only to compute pre-registered slice-continuity metadata, before any future second-smoke or A2-small discussion?

This is not a request for a second smoke, A2-small, A2-medium, full 2D→3D reconstruction, training, fine-tuning, checkpoint operation, scientific acceptance, qmatch formal acceptance, validated permeability, or generative digital-well claim.

## Candidate verdicts

Choose exactly one:

```text
ALLOW_METADATA_ONLY_INTER_SLICE_AUDIT_WITH_CONSTRAINTS
REQUIRE_FIXES_BEFORE_AUDIT_GATE
DO_NOT_RUN_AUDIT
```

## Current state

```text
parent_smoke_verdict=REDESIGN_BEFORE_ANY_A2_SMALL_GATE
scientific_status=diagnostic_smoke_not_evidence
current_artifact_status=planning_only_not_evidence
execution_authorized=false
ready_for_second_smoke=false
ready_for_a2_small_gate=false
```

Parent smoke package:

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_minimal_3d_smoke_package_20260707_run01_qmatch_candidate/
```

Planning artifacts under review:

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_inter_slice_consistency_audit_plan_20260707.md
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_inter_slice_consistency_audit_checklist_20260707.json
```

## Frozen route/provenance

```text
route_label=nnUNet ep015_qmatch
route_status=diagnostic_calibrated_route_only
calibration_version=hy7-gray-calibration-qmatch-v1
formal_anchor=ep015_all planning_anchor_only
failed_chunk=ep015_chunk000_063 visible negative evidence
not_a_generative_digital_well=true
```

Parent candidate provenance:

```text
source_path=hy7-linux:/home/user/HXL/HY7_planb/phase2/b1_gray_sus_b11_rescue20_nnunet_review_20260706/ep015_qmatch_pore_nnunet2d.npy
source_sha256=24655b96b3f50ad14f8c60548afa9e0169babb76c24b605efa870e741502b7b2
parent_slice_range=384:448
parent_candidate_shape=64x128x128
candidate_arrays_written=false
```

## Parent negative evidence motivating audit

```text
percolation_flags_3d={x:false,y:false,z:false}
connected_porosity_pore_basis=0.005316792202038104
connected_porosity_total_basis=0.000308990478515625
S2_lag1_valid_no_wrap={x:0.0033976236979166665,y:0.0357781357652559,z:0.037223755843996065}
physical_proxy_flow={x:0,y:0,z:0}
euler_minkowski_status=explicitly_de_scoped_fail_closed
```

Interpretation boundary: the smoke is clean negative diagnostic evidence, not a success. The audit question is whether x-axis S2 collapse and all-axis non-percolation are consistent with inter-slice 2D inference / 2D→3D assembly inconsistency, sub-REV, route fragmentation, or genuinely disconnected rock at this scale.

## Proposed audit scope if allowed

One metadata-only audit package may compute only pre-registered statistics from the existing external qmatch candidate. It must not train, fine-tune, checkpoint, infer new model outputs, generate new candidate volumes, cherry-pick windows, or write voxel arrays to git.

Required metrics:

```text
per_slice_porosity_mean_std_min_max
adjacent_slice_jaccard_distribution_along_x
adjacent_slice_dice_distribution_along_x
adjacent_slice_overlap_drop_flags
component_persistence_across_adjacent_slices_proxy
run_length_of_connected_foreground_across_x_proxy
S2_lag1_x_y_z_with_boundary_label
S2_anisotropy_ratios_x_over_y_and_x_over_z
per_slice_pore_count_outlier_flags
```

Required labels:

```text
status=diagnostic_metadata_only
not_permeability=true
not_scientific_acceptance=true
not_formal_qmatch_acceptance=true
```

Required controls:

```text
axis_convention_control
boundary_convention_control
failed_chunk_visibility_control
no_cherry_pick_control
no_formal_route_merge_control
no_artifact_leakage_control
```

## Proposed package contract if allowed

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

## Fail-closed conditions

The audit implementation must fail closed if any of the following occurs:

```text
candidate source path/hash cannot be verified
route label/calibration version mismatch
axis mapping missing or ambiguous
slice range not pre-registered
failed chunk ep015_chunk000_063 not visible
any attempt to write .npy/.npz/.pt/weights/checkpoints/voxel arrays under git
any metric is described as permeability or scientific acceptance
any second-smoke/A2-small implication is made
```

## Still forbidden regardless of audit verdict

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

## Requested output

Return the single verdict, required constraints, any missing design fixes, and whether a metadata-only audit launcher/package may be implemented next. Do not authorize second smoke or A2-small.
