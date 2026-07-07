# HY7 Stage 3 smoke RCA / redesign plan — run01

Date: 2026-07-07

## Status

```text
post_run_review_verdict=REDESIGN_BEFORE_ANY_A2_SMALL_GATE
scientific_status=diagnostic_smoke_not_evidence
execution_authorized=false
ready_for_a2_small_gate=false
```

This is a metadata-only redesign artifact. It does not authorize a second smoke, A2-small, A2-medium, training, checkpoint work, full 2D→3D reconstruction, scientific acceptance, or a digital-well claim.

## Parent smoke

```text
package=experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_minimal_3d_smoke_package_20260707_run01_qmatch_candidate/
route=nnUNet ep015_qmatch
calibration=hy7-gray-calibration-qmatch-v1
formal_anchor=ep015_all planning_anchor_only
failed_chunk=ep015_chunk000_063 visible negative evidence
candidate=external qmatch pore nnUNet2d npy, slice 384:448, shape 64x128x128
source_sha256=24655b96b3f50ad14f8c60548afa9e0169babb76c24b605efa870e741502b7b2
```

## Negative evidence summary

```text
percolation_flags_3d={x:false,y:false,z:false}
connected_porosity_pore_basis=0.005316792202038104
connected_porosity_total_basis=0.000308990478515625
physical_proxy_flow={x:0,y:0,z:0}
Euler/Minkowski=explicitly_de_scoped_fail_closed
S2 lag1 no-wrap={x:0.0033976236979166665,y:0.0357781357652559,z:0.037223755843996065}
```

The result is a clean negative diagnostic. It does not show positive 3D connectivity or physical response. It also does not prove that the route is scientifically dead, because likely route/assembly/REV confounders remain.

## Ranked hypotheses

1. **Inter-slice 2D inference inconsistency / 2D→3D assembly artifact**
   - Support: x-axis lag-1 S2 is about an order of magnitude below y/z; current axis convention maps x to slice-stacking axis.
   - Discriminating next artifact: inter-slice consistency audit protocol before any second smoke.

2. **Sub-REV or unrepresentative selected chunk**
   - Support: one 64x128x128 subvolume only; no axis percolates; connected porosity is extremely low.
   - Discriminating next artifact: minimum-REV / subvolume-selection plan, with pre-registered criteria that do not cherry-pick percolation.

3. **qmatch threshold / binary diagnostic-route fragmentation**
   - Support: candidate is qmatch-conditioned 2D nnUNet pore output; qmatch remains diagnostic and cannot be merged with formal threshold anchor.
   - Discriminating next artifact: route-labelled comparison plan; no qmatch formal acceptance.

4. **Genuinely tight/disconnected rock at this scale**
   - Support: all-axis non-percolation and zero flow proxy are compatible with tight disconnected pore space.
   - Limitation: cannot separate physical rock signal from route/REV artifacts from one diagnostic smoke.

## Future second-smoke prerequisites before any request

A future second-smoke request, if any, must first provide:

```text
metadata-only inter-slice consistency audit plan
minimum-REV/subvolume-selection plan
explicit treatment of x-axis low S2 as route artifact vs expected anisotropy hypothesis
preserved failed chunk ep015_chunk000_063 negative evidence
no cherry-picked rerun to find percolation
new strict gate before second smoke
```

A2-small is not discussable until a later strict gate sees a redesigned diagnostic package that addresses the above confounders.

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
