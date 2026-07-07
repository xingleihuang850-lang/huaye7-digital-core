# HY7 Stage 3 Branch A minimal 3D smoke post-run review request — 2026-07-07

## Gate question

Given the one authorized minimal qmatch-conditioned 3D diagnostic smoke result, should HY7 Stage 3 Branch A:

1. STOP / do not scale,
2. REDESIGN before any next execution,
3. only request a later A2-small gate if additional constraints are satisfied?

This is not a request for A2-small execution, A2-medium execution, training, checkpoint operations, full 2D→3D campaign, HY7 scientific acceptance, qmatch formal acceptance, B2-min final pass, or a generative digital-well claim.

## Prior verdicts and boundaries

```text
A1 completion gate: A1_COMPLETE_WITH_CONSTRAINTS_ALLOW_A2_DESIGN_ONLY
A2/smoke design completion gate: READY_TO_REQUEST_MINIMAL_3D_SMOKE_GATE_WITH_CONSTRAINTS
Minimal 3D smoke gate: ALLOW_MINIMAL_3D_SMOKE_ONLY
```

Frozen diagnostic route:

```text
route_label=nnUNet ep015_qmatch
route_status=diagnostic_calibrated_route_only
calibration_version=hy7-gray-calibration-qmatch-v1
formal_anchor=ep015_all planning_anchor_only
failed_chunk=ep015_chunk000_063 visible negative evidence
scientific_status=diagnostic_smoke_not_evidence
not_a_generative_digital_well=true
```

## Package under review

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_minimal_3d_smoke_package_20260707_run01_qmatch_candidate/
```

Package status:

```text
package_status=DIAGNOSTIC_SMOKE_METADATA_ONLY
smoke_executed=true
candidate_count=1
candidate_arrays_written=false
volume_files_written=[]
forbidden_extensions_written=[]
```

Candidate provenance:

```text
source_path=hy7-linux:/home/user/HXL/HY7_planb/phase2/b1_gray_sus_b11_rescue20_nnunet_review_20260706/ep015_qmatch_pore_nnunet2d.npy
local_materialized_path=/var/folders/l6/qjrw5dps6s96b9ddgnmlbh8m0000gn/T/hy7-smoke-candidate-hBB4Y0/ep015_qmatch_pore_nnunet2d.npy
source_sha256=24655b96b3f50ad14f8c60548afa9e0169babb76c24b605efa870e741502b7b2
source_shape=[512,128,128]
source_dtype=uint8
slice_range=384:448
candidate_shape=[64,128,128]
preview_downsample_sha256=8b3a997d08def6fac409dc78235fa74deca4ffbfd683bc044f65f2d6ee2a5ab4
```

No .npy/.npz/.pt/volume/weight/checkpoint files are in the package or staged for git; the candidate array remains external and uncommitted.

## Smoke metrics

```text
porosity_phi_3d=0.05811595916748047
connected_porosity_ratio_3d.pore_voxel_basis=0.005316792202038104
connected_porosity_ratio_3d.total_volume_basis=0.000308990478515625
percolation_flags_3d={x:false, y:false, z:false}
largest_connected_component_fraction_3d.pore_voxel_basis=0.005316792202038104
largest_connected_component_fraction_3d.total_volume_basis=0.000308990478515625
S2 lag_1_valid_pairs_no_wrap_no_periodic_boundary={x:0.0033976236979166665, y:0.0357781357652559, z:0.037223755843996065}
Euler/Minkowski=explicitly_de_scoped_fail_closed; no topology claim from Euler/Minkowski
```

Physical-response proxy:

```text
method=percolation_supported_flow_proxy
qualitative_only_flag=true
units_or_unitless_status=unitless diagnostic proxy only; not permeability
per_axis_flow_proxy={x:0.0, y:0.0, z:0.0}
consistency_with_percolation=consistent_by_construction
fail_closed_reasons=[]
forbidden_claims=[validated permeability, scientific physical response]
```

## Negative evidence that must remain visible

```text
non_percolating_axes=[x,y,z]
low_connected_porosity=true (pore basis about 0.0053; total-volume basis about 0.000309)
Euler/Minkowski explicitly de-scoped fail-closed
formal-vs-qmatch route remains not merged
failed chunk ep015_chunk000_063 remains visible negative evidence
physical proxy reports zero flow on all non-percolating axes, so no contradiction, but also no positive flow evidence
```

## Verification evidence

```text
python3 -m pytest tests/test_hy7_stage3_minimal_3d_smoke.py -q -> 8 passed
python3 -m pytest tests -q -> 50 passed
shasum -a 256 -c hashes.txt -> 11 package files OK
package FILE_COUNT=12
package FORBIDDEN=[]
```

## Candidate verdicts requested

Please choose one of:

```text
STOP_DO_NOT_SCALE
REDESIGN_BEFORE_ANY_A2_SMALL_GATE
CONSIDER_A2_SMALL_GATE_ONLY_AFTER_ADDITIONAL_CONSTRAINTS
```

Review requirements:

- Treat this as diagnostic smoke, not scientific acceptance.
- Do not promote qmatch to formal acceptance.
- Do not interpret 2D x/y penetration or this diagnostic proxy as validated 3D permeability.
- Keep the all-axis non-percolation and very low connected porosity visible.
- State whether the next action should be stop/redesign/future-gate-only, and list still-forbidden actions.
