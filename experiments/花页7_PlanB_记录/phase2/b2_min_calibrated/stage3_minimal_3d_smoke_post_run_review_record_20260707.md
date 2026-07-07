# HY7 Stage 3 minimal 3D smoke post-run review record — 2026-07-07

## Gate question

Given the one authorized minimal qmatch-conditioned 3D diagnostic smoke result, should HY7 Stage 3 Branch A stop, redesign, or consider a later A2-small gate?

This review is not an A2 execution request and does not authorize A2-small, A2-medium, full 2D→3D campaign, training, checkpoint operations, scientific acceptance, qmatch formal acceptance, B2-min final pass, or generative digital-well claims.

## Verdict

```text
REDESIGN_BEFORE_ANY_A2_SMALL_GATE
```

## Evidence under review

Package:

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_minimal_3d_smoke_package_20260707_run01_qmatch_candidate/
```

Frozen diagnostic route:

```text
route_label=nnUNet ep015_qmatch
calibration_version=hy7-gray-calibration-qmatch-v1
formal_anchor=ep015_all planning_anchor_only
failed_chunk=ep015_chunk000_063 visible negative evidence
scientific_status=diagnostic_smoke_not_evidence
not_a_generative_digital_well=true
```

Candidate provenance:

```text
source_path=hy7-linux:/home/user/HXL/HY7_planb/phase2/b1_gray_sus_b11_rescue20_nnunet_review_20260706/ep015_qmatch_pore_nnunet2d.npy
source_sha256=24655b96b3f50ad14f8c60548afa9e0169babb76c24b605efa870e741502b7b2
slice_range=384:448
candidate_shape=64x128x128
candidate_arrays_written=false
forbidden_extensions_written=[]
```

Smoke metrics:

```text
porosity_phi_3d=0.05811595916748047
connected_porosity_ratio_3d.pore_voxel_basis=0.005316792202038104
connected_porosity_ratio_3d.total_volume_basis=0.000308990478515625
percolation_flags_3d={x:false,y:false,z:false}
S2_lag1_valid_no_wrap={x:0.0033976236979166665,y:0.0357781357652559,z:0.037223755843996065}
euler_minkowski_status=explicitly_de_scoped_fail_closed
physical_proxy={x:0.0,y:0.0,z:0.0}; qualitative only, not permeability
```

## Interpretation

The smoke is a clean negative diagnostic, not a success:

1. All three axes are non-percolating.
2. Connected porosity is extremely low: about 0.53% of pore voxels and 0.031% of total volume.
3. Physical proxy is consistent only because it reports zero flow on every non-percolating axis; this is not positive physical-response evidence.
4. S2 is strongly anisotropic: x-axis lag-1 is about one order of magnitude below y/z. The review flags this as a likely inter-slice 2D-inference / 2D-to-3D assembly consistency problem rather than proof of scientific failure or success.
5. Euler/Minkowski remains explicitly de-scoped fail-closed, so topology is incomplete by design.
6. qmatch remains a diagnostic route and must not be promoted to formal acceptance.

## Still forbidden

```text
A2-small execution
A2-medium execution
full 2D-to-3D reconstruction campaign
training or fine-tuning
checkpoint creation or selection
HY7 scientific acceptance claim
B2-min final pass claim
qmatch formal acceptance claim
validated permeability claim
generative digital-well claim
cherry-picked rerun to find percolation
hiding failed chunk ep015_chunk000_063
```

## Next allowed artifact/action

Only a metadata-only root-cause / redesign package is allowed next. It must not run new model inference, train, fine-tune, checkpoint, export new scientific volumes, or claim acceptance.

Required contents:

```text
ranked hypotheses for all-axis non-percolation and x-axis S2 decorrelation
inter-slice consistency check protocol
sub-REV / minimum-REV estimation plan
alternative subvolume-selection criteria
criteria for any future second smoke before A2-small can even be discussed
preserved route/provenance/negative-evidence boundaries
```

## MoA evidence

- provider: `moa`
- preset/model: `digital-rock-gate`
- parent session command: `hermes -z "$(cat stage3_minimal_3d_smoke_post_run_review_request_concise_20260707.md)" --provider moa -m digital-rock-gate`
- raw output: `experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_minimal_3d_smoke_post_run_review_moa_output_20260707.md`
- note: the first full prompt attempt timed out and produced no usable evidence; the concise self-contained prompt above produced the recorded verdict.
