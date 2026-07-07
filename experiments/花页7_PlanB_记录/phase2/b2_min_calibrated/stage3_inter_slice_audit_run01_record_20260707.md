# HY7 Stage 3 inter-slice consistency audit run01 record — 2026-07-07

## Status

```text
package_status=METADATA_ONLY_INTER_SLICE_AUDIT
verdict_authorizing_execution=ALLOW_METADATA_ONLY_INTER_SLICE_AUDIT_WITH_CONSTRAINTS
scientific_status=diagnostic_metadata_only_not_evidence
parent_smoke_verdict=REDESIGN_BEFORE_ANY_A2_SMALL_GATE
second_smoke_authorized=false
A2_small_authorized=false
```

## Package

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_inter_slice_audit_package_20260707_run01/
```

Files:

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

## Source verification

Remote source:

```text
hy7-linux:/home/user/HXL/HY7_planb/phase2/b1_gray_sus_b11_rescue20_nnunet_review_20260706/ep015_qmatch_pore_nnunet2d.npy
```

Verified SHA256 before metrics:

```text
24655b96b3f50ad14f8c60548afa9e0169babb76c24b605efa870e741502b7b2
```

Slice/range:

```text
slice_range=384:448
full_array_shape=512x128x128
audit_volume_shape=64x128x128
axis_0_to_slice_stacking_mapping=verified
boundary_semantics=lag_1_valid_pairs_no_wrap_no_periodic_boundary
```

## Metadata-only controls

```text
candidate_arrays_written=false
raw_pair_values_written=false
raw_per_slice_values_written=false
no .npy/.npz/.pt files in package
hashes.txt verified OK
```

## Summary metrics

```text
per_slice_porosity.median=0.056884765625
per_slice_porosity.mean=0.05811595916748047
adjacent_slice_jaccard_x.median=0.028101802757158005
adjacent_slice_dice_x.median=0.05466735430634347
s2_lag1={x:0.0033976236979166665,y:0.0357781357652559,z:0.037223755843996065}
s2_x_over_y=0.09496368732593648
s2_x_over_z=0.09127568191012299
per_slice_pore_count_robust_z_abs.max=4.3526328125000004
zero_or_near_zero_pore_slice_runs.longest_run=0
```

## Pre-registered negative-evidence flags

```text
jaccard_x_median_over_yz_median_lt_0.25=false
s2_x_over_min_yz_lt_0.25=true
component_persistence_pairwise_median_lt_0.10=true
per_slice_pore_count_robust_z_abs_gt_3.5=true
zero_or_near_zero_pore_slice_run_ge_3=false
```

## Interpretation boundary

This audit strengthens the metadata-only diagnosis that the run01 qmatch 2D-stack has severe slice-stacking inconsistency / decorrelation signals, especially low x-axis S2 relative to y/z and low adjacent-slice pairwise persistence. It does not prove permeability, scientific acceptance, qmatch formal acceptance, B2-min final pass, or generative digital-well validity.

The audit outcome, pass or fail, has no bearing on `parent_smoke_verdict=REDESIGN_BEFORE_ANY_A2_SMALL_GATE` and does not reopen or modify that gate.

## Still forbidden

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
committing .npy/.npz/.pt/weights/checkpoints/voxel arrays
```
