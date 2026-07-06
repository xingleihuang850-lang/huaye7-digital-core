# HY7 B2 continuation / Stage 3 planning memo — 2026-07-06

## Workflow node

- Node: `HY7-B2-continuation-stage3-planning`
- Preceding gate: `HY7-handoff-stage3-planning-promotion-gate`
- Gate verdict inherited: `PROMOTE_WITH_CONSTRAINTS`
- Gate level inherited: `stage-3-planning-input only`
- Current action: plan the next B2/Stage3 bridge experiment; no training or 3D generation is launched by this memo.

## One-sentence decision

Continue B2 by converting the approved calibrated handoff bundle into a Stage 3 planning package: build a route/constraint matrix, define 3D connectivity/percolation semantics, and pre-register a bold but gated 2D→3D exploratory branch; do not start actual 3D generation or new training until the Stage 3 design gate passes.

## Why this is still a B2 continuation

B2 is no longer just a fallback `[sus,pore]` branch. After the B1.1 conditional closure and B2-min handoff gate, B2's immediate role is to bridge the calibrated 2D diffusion evidence into the Stage 3 multiscale 3D digital-core plan without losing:

1. the full-batch `ep015_all` planning anchor;
2. explicit `hy7-gray-calibration-qmatch-v1` calibration;
3. separation of formal vs nnUNet-qmatch routes;
4. visibility of the failed `ep015_chunk000_063` maxCC risk;
5. the no-training/no-sampling/no-scaling boundary from the gate.

This is not over-conservative: it is the minimum governance needed before a bolder 2D→3D or conditional-generation branch can be scientifically defensible.

## Active planning input

```text
handoff_bundle=experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/handoff_bundle_ep015_20260706/
constraints_matrix=experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_planning_constraints_matrix_20260706.json
promotion_gate=experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/handoff_stage_entry_gate_20260706.md
```

Key anchor:

```text
variant=ep015_all
n=512
phi=6.442654132843018
S2 rmse=0.0002854642510439182
Euler=121.26953125
maxCC=0.06397858477862998
pass_gate=True
policy=acceptance_anchor
```

Key risk:

```text
variant=ep015_chunk000_063
pass_gate=False
failure_reasons=["maxCC>0.070"]
maxCC=0.07163110510281959
policy=risk_input
```

## Literature and theory support

The next move is supported by both local archived literature and public search evidence:

1. 2D→3D reconstruction is a legitimate digital-rock task, but it must preserve morphology/connectivity rather than only match appearance.
   - Local: `Mosser2017_3D_porous_media_GAN.pdf`.
   - Local: `Kench2021_SliceGAN_2D_to_3D.pdf`.
   - Public: SliceGAN reports 3D structures can be synthesized from 2D micrographs and evaluated by microstructural metrics.

2. Digital-rock validation should include spatial/statistical/topological/flow-related metrics, not just porosity.
   - Local: `Andra2013_DRP_benchmark_PartI_imaging_segmentation.pdf` and `PartII_effective_properties.pdf`.
   - Local: `Blunt2013_pore_scale_imaging_modelling.pdf`.
   - Public searches highlight S2/two-point correlation, Minkowski functionals/Euler characteristic, connectivity/percolation, and permeability as relevant validation families.

3. Diffusion/latent diffusion for 3D porous media is now an active, plausible direction.
   - Local: `Liu2025_Controlled_Latent_Diffusion_3D_porous.pdf`.
   - Local: `Zhu2025_diffusion_3D_multiphase_poreImages.pdf`.
   - Local: `Hou2026_limited_core_multimodal_diffusion_3D.pdf`.
   - Public search result: controlled latent diffusion for 3D porous media reconstruction reports conditioning on porosity/statistics and evaluating permeability, S2, pore-size distributions.

4. Shale/multimineral 2D→3D reconstruction is not identical to sandstone; phase labels and heterogeneity must be carried explicitly.
   - Local: `Loucks2012_mudrock_pore_types.pdf` for mudrock pore-type geology.
   - Public search result: 3D multi-mineral shale reconstruction from 2D images uses two-point correlations, geometry, morphological topology, and flow characteristics; matrix/pyrite reconstruction can be weaker than pore/organic phases, so phase-specific validation is required.

## Next B2 experiment: B2-D1 constraints and connectivity semantics closure

### Status

```text
APPROVED_TO_DESIGN
NOT_APPROVED_TO_TRAIN
NOT_APPROVED_TO_GENERATE_3D
```

### Objective

Turn the Stage 3 planning gate's required strengthening into a concrete, auditable Stage 3 design input.

### Deliverables

1. `stage3_planning_constraints_matrix_20260706.json` — created in this step.
2. Stage 3 design card to be written next, with sections for:
   - 2D planning anchor;
   - route separation;
   - connectivity/percolation semantics;
   - literature-backed exploratory branches;
   - stage-entry tests/gates.

### Connectivity semantics inherited from current code

`src/hy7_phase2_eval.py` defines:

```text
x_penetrate: 最大连通簇同时接触左/右边界的 tile 比例（x 方向贯通）。
y_penetrate: 最大连通簇同时接触上/下边界的 tile 比例（y 方向贯通）。
```

Therefore:

```text
current x_penetrate=0.0 / y_penetrate=0.0
= no detected 2D tile-level largest-connected-component spanning in x/y under the current threshold route.
```

It does **not** mean:

```text
3D permeability passed
3D z-direction percolation passed
3D connectivity validated
```

Stage 3 must add 3D-specific checks:

- 3D connected porosity ratio;
- x/y/z percolation flags;
- 3D largest connected component fraction;
- 3D Euler / Minkowski functional;
- permeability or permeability proxy only after a 3D volume exists.

## Bold exploratory branches, with gates

The user preference is to avoid excessive conservatism when data, theory, and public authoritative literature support exploration. Under that policy, the following branches are scientifically plausible, but only Branch A is ready for immediate design.

### Branch A — 2D-to-3D statistical reconstruction planning from calibrated B2 handoff

Decision: `PRIMARY_NEXT_DESIGN`

Idea:
Use the calibrated `ep015_all` 2D anchor and route-separated metrics to design a Stage 3 2D→3D reconstruction experiment, initially as a planning/design card only.

Why bold but justified:
- Uses existing HY7 calibrated evidence.
- Directly advances the thesis path from 2D diffusion to 3D digital core.
- Supported by Mosser2017, SliceGAN/Kench2021, MPS/Okabe-Blunt style 2D→3D reconstruction literature, and recent diffusion-based 3D porous media work.

First design gates:
- no new training until Stage 3 design card is accepted;
- define target volume size and voxel spacing separately for micro-CT / nano-CT / FIB-SEM contexts;
- pre-register S2, Euler, connected porosity, x/y/z percolation, LCC fraction;
- explicitly mark `ep015_all` as planning anchor and `ep015_chunk384_447` as triage-only.

### Branch B — conditional `[gray,pore]` or `[sus,pore]` joint/paired generation

Decision: `SECONDARY_EXPLORATION_AFTER_BRANCH_A_DESIGN`

Idea:
Use gray/calibrated `sus` and pore masks as condition/target pairs for a conditional model that learns pore structure under gray/mineral constraints.

Why plausible:
- It matches the thesis direction: conditional diffusion + multimodal fusion.
- Public and local literature supports paired/multimodal diffusion and image-to-image reconstruction.

Why not immediate:
- It would require new training.
- B2-min gate explicitly did not authorize new training or new checkpoint.
- It needs a separate training gate with budget, data split, validation cadence, and fail-closed metrics.

### Branch C — topology/percolation-controlled generative sampling

Decision: `RESEARCH_SPIKE_AFTER_CONNECTIVITY_DEFINITION`

Idea:
Condition or select generated samples by porosity + topology/connectivity statistics, inspired by controlled latent diffusion and digital-rock physical validation.

Why plausible:
- Current B1.1 bottleneck was topology/connectivity, not S2 alone.
- Recent literature uses porosity/statistics conditioning and evaluates permeability/S2/pore-size distributions.

Why not immediate:
- Current 3D connectivity semantics are not yet defined for HY7.
- Current evidence is 2D slice-level.

## Forbidden carry-forward claims

Do not write or imply:

- B2-min final pass.
- B1.1 unconditional pass.
- ORIG raw pass.
- qmatch optional.
- selected chunk represents full model performance.
- formal route and nnUNet-qmatch route are one metric.
- x/y 2D penetrate=0.0 proves 3D impermeability or 3D connectivity.
- Stage 3 planning promotion authorizes actual 3D generation.

## Immediate next action after this memo

Write the Stage 3 design card for Branch A:

```text
stage3_branch_a_2d_to_3d_reconstruction_design_20260706.md
```

The design card should be a pre-registration document: inputs, outputs, target volume candidates, metrics, forbidden claims, validation gates, and compute/data budget. It can be bold in experimental direction, but must remain evidence/provenance constrained.
