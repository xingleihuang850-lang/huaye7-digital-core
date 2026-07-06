# HY7 Stage 3 Branch A design card — 2D→3D reconstruction planning from calibrated B2 handoff

## Workflow node

- Node: `HY7-stage3-branch-A-2d-to-3d-reconstruction-design`
- Parent node: `HY7-B2-continuation-stage3-planning`
- Source gate: `HY7-handoff-stage3-planning-promotion-gate`
- Source gate verdict: `PROMOTE_WITH_CONSTRAINTS`
- Gate level inherited: `stage-3-planning-input only`
- Status: `DESIGN_CARD_PRE_REGISTRATION`
- Execution boundary: design only; no training, no new sampling, no actual 3D generation, no voxel export, no new checkpoint.

## One-sentence design decision

Branch A is the primary next design: use the calibrated B2 handoff bundle as a constrained planning input for a 2D→3D digital-rock reconstruction experiment, pre-registering volume targets, route labels, morphology/topology/percolation metrics, and fail-closed gates before any generation or training is launched.

## Why Branch A is the right next B2 continuation

The B2-min handoff is not a final result; it is a controlled bridge from Stage 2 2D diffusion evidence toward Stage 3 multiscale 3D digital-core design. Branch A is the least speculative route that still moves boldly toward the thesis mainline:

1. It directly addresses the thesis transition from 2D generation to 3D digital core.
2. It uses the approved handoff bundle and does not discard B1.1/B2-min governance.
3. It is literature-supported: 2D→3D porous-media reconstruction, SliceGAN/dimensionality expansion, MPS/Okabe-Blunt style reconstruction, and recent diffusion/latent-diffusion porous-media reconstruction all treat 2D/limited images as legitimate inputs when validation includes morphology and connectivity.
4. It targets the current weakness explicitly: 2D `x/y_penetrate=0.0/0.0` is not 3D connectivity evidence, so Branch A makes 3D connectivity/percolation a first-class gate.

## Inputs

### Required handoff bundle

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/handoff_bundle_ep015_20260706/
```

Required files:

```text
handoff_manifest.json
handoff_readme.md
formal_vs_qmatch_metrics.json
candidate_rows.json
forbidden_claims.txt
audit_report.json
ordered_view_links.txt
hashes.txt
```

### Required constraints matrix

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_planning_constraints_matrix_20260706.json
```

### Formal planning anchor

```text
variant=ep015_all
route=threshold_formal_full_batch
n=512
phi=6.442654132843018
S2 rmse=0.0002854642510439182
Euler=121.26953125
maxCC=0.06397858477862998
pass_gate=True
allowed_use=planning_anchor_only
```

### Diagnostic calibrated route

```text
variant=nnUNet ep015_qmatch
route=qmatch_nnunet_diagnostic
phi=5.794930458068848
S2 rmse=0.0017214588891168259
Euler=116.154296875
maxCC=0.06510709034871634
reverse_fail=False
allowed_use=diagnostic_calibrated_route_only
```

### Triage and risk rows

```text
selected_triage=ep015_chunk384_447
selected_policy=triage_only
selected_maxCC=0.06431804952279352

failed_risk=ep015_chunk000_063
failed_policy=risk_input
failed_reason=maxCC>0.070
failed_maxCC=0.07163110510281959
```

## Literature basis

This design card uses the following local literature anchors and public-search evidence already recorded in the B2 continuation memo:

- `Mosser2017_3D_porous_media_GAN.pdf`: 3D porous media can be reconstructed with generative models, but physical/statistical evaluation is required.
- `Kench2021_SliceGAN_2D_to_3D.pdf`: 2D micrographs can support dimensionality expansion to 3D when generated volumes are assessed with microstructural metrics and the 2D image is representative.
- `Andra2013_DRP_benchmark_PartI_imaging_segmentation.pdf` and `Andra2013_DRP_benchmark_PartII_effective_properties.pdf`: digital-rock validation must connect imaging/segmentation choices to effective properties.
- `Blunt2013_pore_scale_imaging_modelling.pdf`: pore-scale imaging/modeling connects structure to flow and transport interpretation.
- `Liu2025_Controlled_Latent_Diffusion_3D_porous.pdf`: controlled latent diffusion for 3D porous media motivates statistic-conditioned 3D exploration, but not without validation gates.
- `Zhu2025_diffusion_3D_multiphase_poreImages.pdf`: diffusion-based 3D multiphase pore-scale image generation motivates topology/Minkowski/flow-related validation.
- `Hou2026_limited_core_multimodal_diffusion_3D.pdf`: limited-core / multimodal diffusion is relevant to later Branch B/C planning.
- `Loucks2012_mudrock_pore_types.pdf`: shale/mudrock pore types require geological phase awareness; sandstone assumptions cannot be copied blindly.

## Proposed experiment family

Branch A should be split into three increasingly risky design levels.

### A0 — no-generation planning package

Status: `CURRENTLY_ALLOWED`

Purpose:
Write a complete Stage 3 design package without generating voxels.

Outputs:

```text
stage3_branch_a_2d_to_3d_reconstruction_design_20260706.md
stage3_branch_a_gate_metrics_20260706.json
stage3_branch_a_literature_support_20260706.md
```

Allowed actions:

- define target volumes;
- define metrics;
- define candidate algorithms;
- define gate levels;
- define compute/data budget;
- define fail-closed criteria.

Forbidden actions:

- no 3D voxel generation;
- no training;
- no new sampling;
- no checkpoint creation;
- no B2-min final-pass claim.

### A1 — tiny synthetic dry-run, future gate required

Status: `NOT_YET_APPROVED`

Purpose:
If separately approved, run a tiny non-scientific plumbing dry-run that creates a toy volume or mock volume solely to verify metric code paths.

Example target:

```text
volume_size=64^3 or smaller
purpose=metric plumbing only
scientific_status=not evidence
```

Gate required before A1:

- confirm source arrays / representative 2D slices;
- write exact command;
- guarantee no large artifacts committed;
- verify 3D metrics on toy output;
- record all outputs under a dry-run path.

### A2 — real Branch A reconstruction experiment, future gate required

Status: `NOT_YET_APPROVED`

Purpose:
Run actual 2D→3D reconstruction or diffusion/SliceGAN-style experiment.

Gate required before A2:

- choose algorithm family;
- define training or non-training path;
- define data split and representative slices;
- define compute budget;
- define output volume size;
- define exact metrics and pass/fail thresholds;
- run a MoA/digital-rock gate if training or major compute is requested.

## Candidate algorithm families

### Family 1 — SliceGAN-style dimensionality expansion

Use when:

- representative 2D slices are available;
- the goal is 2D-to-3D statistical reconstruction;
- validation focuses on matching 2D/3D morphology, not direct physical claims.

Pros:

- Strong literature precedent for 2D→3D microstructure generation.
- Directly aligns with Branch A.

Risks:

- Shale anisotropy and multimineral heterogeneity may violate simple representativeness assumptions.
- Requires training if implemented, so not currently authorized.

### Family 2 — MPS / statistic-constrained reconstruction planning

Use when:

- the immediate goal is a non-training design baseline;
- the project needs explicit two-point/multi-point statistics and percolation gates.

Pros:

- Strong conceptual connection to Okabe-Blunt and multipoint-statistics literature.
- Good for defining validation metrics before deep generation.

Risks:

- May underrepresent complex shale phase relationships unless phase labels are explicit.

### Family 3 — controlled latent diffusion / statistic-conditioned 3D diffusion

Use when:

- a future gate authorizes training or reuse of a pretrained framework;
- conditioning variables include porosity/S2/topology/percolation.

Pros:

- Bold, modern, thesis-aligned.
- Naturally extends current DDPM work.

Risks:

- Requires training/compute and new checkpoints.
- Must not be started under current gate.

## Target volume candidates

These are design targets, not authorized outputs.

| Candidate | Size | Purpose | Status |
|---|---:|---|---|
| A0-table | none | paper design / metric matrix only | allowed now |
| A1-toy | 32^3–64^3 | metric plumbing / code dry-run only | future gate required |
| A2-small | 128^3 | first real 3D reconstruction candidate | future gate required |
| A2-medium | 256^3 | higher-FOV planning target | future gate required |

Voxel spacing must be chosen per data modality. Do not mix micro-CT/nano-CT/FIB-SEM spacing without explicit resampling and provenance.

## Required metrics and gates

### 2D inherited metrics

- porosity / phi;
- S2 / two-point correlation;
- Euler characteristic;
- maxCC;
- x/y 2D penetrate, explicitly labelled as 2D tile-level.

### 3D metrics to add before any actual 3D result claim

- 3D porosity;
- 3D S2 along x/y/z directions;
- 3D connected porosity ratio;
- x/y/z percolation flags;
- 3D largest connected component fraction;
- 3D Euler characteristic / Minkowski functional;
- pore-size distribution or granulometry proxy;
- optional permeability/proxy only after a real 3D volume exists.

### Fail-closed rules

A generated or reconstructed 3D volume must be rejected or downgraded to diagnostic-only if any of the following occurs:

- no route label for formal vs qmatch;
- no full-batch `ep015_all` anchor in the report;
- selected chunk is treated as model-wide acceptance;
- failed chunk `ep015_chunk000_063` disappears from risk discussion;
- 2D penetrate is interpreted as 3D percolation;
- 3D connectivity/percolation metrics are absent;
- artifact hashes are missing;
- volume size / voxel spacing / modality are not recorded.

## Planned output schema for future A1/A2 packages

Future packages should contain at least:

```text
branch_a_manifest.json
branch_a_readme.md
input_slice_manifest.json
route_constraints.json
metrics_2d_inherited.json
metrics_3d_required_schema.json
connectivity_semantics.md
forbidden_claims.txt
hashes.txt
```

If real outputs are generated later, large volumes must not be committed to git. Record path, size, sha256, command, environment, and representative previews only.

## Forbidden claims and actions

Still forbidden under this design card:

- B2-min final pass claim;
- B1.1 unconditional pass claim;
- ORIG raw pass claim;
- qmatch optional claim;
- selected chunk represents full model performance;
- formal route and nnUNet-qmatch route merged without labels;
- x/y 2D penetrate proves 3D permeability or 3D connectivity;
- Stage 3 planning promotion authorizes actual 3D generation;
- training, new sampling, scaling, new checkpoint, or voxel export without a new gate.

## Immediate next work item

Create the Branch A gate metrics schema:

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_branch_a_gate_metrics_20260706.json
```

This schema should be machine-readable and should encode required 2D inherited metrics, required 3D metrics, fail-closed conditions, and artifact/provenance requirements. After that, run a document/schema verification and, if clean, submit a new gate for whether A1 toy metric-plumbing dry-run may be started.
