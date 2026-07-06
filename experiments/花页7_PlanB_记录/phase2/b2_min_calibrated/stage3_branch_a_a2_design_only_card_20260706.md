# HY7 Stage 3 Branch A A2 design-only card — 2026-07-06

## Workflow node

- Node: `HY7-stage3-branch-A-A2-design-only`
- Parent node: `HY7-stage3-branch-A-A1-toy-metric-plumbing`
- Parent completion gate: `HY7-stage3-branch-A-A1-completion-review-gate`
- Parent gate verdict: `A1_COMPLETE_WITH_CONSTRAINTS_ALLOW_A2_DESIGN_ONLY`
- Status: `A2_DESIGN_ONLY_PRE_EXECUTION`
- Execution boundary: design documents/specs only; no A2 execution, no real 2D→3D reconstruction, no training, no model sampling, no checkpoint, no voxel export, no HY7 scientific claim.

## One-sentence design decision

A2 is allowed to be designed, not executed: convert the A1 toy metric-plumbing package into an execution-ready design specification for future 2D→3D reconstruction, while closing the known blockers around 3D Euler/Minkowski, S₂ boundary conventions, deterministic toy regeneration, scale-up validation, and a future strict execution gate.

## Gate inheritance

The A1 completion gate explicitly authorizes only A2 design. It does not authorize:

```text
A2 execution
real 2D→3D reconstruction
training/fine-tuning
new sampling from any model
checkpoint creation/loading
voxel volume export or git commit
HY7 scientific claim from A1 or A2 design outputs
```

A2 design may include:

```text
design docs / interface / schema specs
3D Euler/Minkowski algorithm design
phantom-suite extension design
asymmetric S₂ boundary-condition phantom design
metric acceptance criteria
real 2D→3D reconstruction pipeline architecture (design only)
provenance/hash/manifest conventions
test plan
risk register
A2 execution gate criteria
```

## Inputs

A1 package:

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_branch_a_a1_toy_metric_plumbing_20260706/
```

A1 completion gate record:

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_branch_a_a1_completion_gate_moa_output_20260706.md
```

Branch A design card:

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_branch_a_2d_to_3d_reconstruction_design_20260706.md
```

Gate metrics schema:

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_branch_a_gate_metrics_20260706.json
```

## A2 design objectives

1. Define how a future A2 execution package would extend from synthetic A1 metric plumbing to real 2D→3D reconstruction without losing labels, provenance, or fail-closed gates.
2. Specify the missing topology and S₂ boundary-condition work before execution.
3. Define exact design-level package artifacts and acceptance rules.
4. Pre-register the future A2 execution gate question so that A2 cannot start by implication.

## A2 design package target

Future A2 design package should contain at least:

```text
stage3_branch_a_a2_design_only_card_20260706.md
stage3_branch_a_a2_execution_gate_checklist_20260706.json
stage3_branch_a_a2_phantom_suite_design_20260706.md
stage3_branch_a_a2_metric_interface_schema_20260706.json
stage3_branch_a_a2_risk_register_20260706.md
```

This step writes the design card and execution gate checklist. It does not write implementation code for A2 execution.

## 3D Euler/Minkowski design

### Current state inherited from A1

A1 records:

```text
euler_characteristic_or_minkowski_3d.status=NOT_IMPLEMENTED_FAIL_CLOSED
```

This is acceptable during A2 design only.

### Design requirement before A2 execution

Before any A2 execution whose metric, acceptance criterion, or claim depends on topology, one of the following must happen:

1. **Implement and phantom-validate 3D Euler/Minkowski**:
   - declare foreground/background connectivity pair;
   - keep pore-phase connectivity at 6-neighborhood unless a future gate changes it;
   - keep complementary solid connectivity at 26-neighborhood for dual-consistency;
   - test on analytically known phantoms;
   - report implementation status and errors in manifest.
2. **Explicitly de-scope topology from A2 execution claims**:
   - state why Euler/Minkowski is not used;
   - preserve `NOT_IMPLEMENTED_FAIL_CLOSED` in all manifests;
   - forbid topology-based acceptance claims.

No silent placeholder is allowed during A2 execution.

### Phantom candidates for Euler/Minkowski design

These are design targets, not execution outputs:

| Phantom | Purpose | Expected topology note |
|---|---|---|
| all_solid | zero pore baseline | no pore components |
| all_pore | full pore baseline | one pore component spanning x/y/z |
| isolated_voxel | single component sanity | one isolated pore object |
| straight_channel_x | axis percolation sanity | one x-spanning pore object |
| hollow_cube_shell / cavity | cavity / complement ambiguity | must clarify foreground/background convention |
| torus-like ring | handle / genus sensitivity | used to test Euler sign/convention after implementation |
| two_disconnected_blobs | component count sanity | two pore components |

The exact analytic Euler values must be written next to the implementation chosen. Do not claim values here without implementation-specific convention.

## S₂ boundary-condition design

A1 uses:

```text
S2 proxy=lag_1_valid_pairs_no_wrap
```

This must remain explicitly labelled. A2 design must pin whether future S₂ uses:

1. non-periodic valid-pair convention;
2. periodic wrap convention;
3. both, with labels.

Gate recommendation: keep non-periodic valid-pair as the default for finite toy phantoms, and add periodic/non-periodic comparison only as a diagnostic.

### Required asymmetric phantom

A2 design must add an asymmetric phantom that distinguishes periodic from non-periodic S₂. Example design:

```text
volume_size >= 8^3
pore voxels placed near one boundary only
expected: non-periodic lag statistics differ from periodic wrap statistics
purpose: fail if S2 implementation silently changes boundary convention
```

The current `x_channel` does not discriminate boundary convention strongly enough by itself.

## Deterministic-regeneration proof

Because A1 did not commit toy volume arrays, A2 design must specify a deterministic regeneration proof instead of committing toy data:

```text
input_type=synthetic_toy
seed=20260706 or recorded value
source_hash=sha256(src/hy7_stage3_branch_a_a1_toy.py)
command=exact CLI command
regenerated_metrics_sha256 must match recorded metrics_3d_toy.json or a declared reproducible subset
```

A2 design should prefer deterministic regeneration over committing toy volumes. Committing volumes remains disfavored and would need a new artifact-policy note.

## Scale-up validation design

A1 used `8^3`, which is sufficient for plumbing but not for execution confidence. A2 design must include scale-up validation before execution:

```text
sizes=[8^3, 16^3, 32^3]
phantoms=all_solid, all_pore, straight_channel_x, isolated_voxel, asymmetric_s2_boundary
purpose=verify metrics remain stable and performant beyond A1
status=design_only_until_execution_gate
```

Do not treat scale-up toy validation as HY7 scientific evidence.

## A2 metric interface design

A future A2 execution package should emit, at minimum:

```text
branch_a_a2_manifest.json
branch_a_a2_readme.md
input_2d_slice_manifest.json
algorithm_config.json
route_constraints.json
metrics_2d_inherited.json
metrics_3d_reconstruction.json
connectivity_semantics.md
s2_boundary_semantics.md
euler_minkowski_semantics.md
provenance.json
forbidden_claims.txt
hashes.txt
```

Large generated volumes, model weights, or checkpoints must not be committed to git. If produced after a future gate, record path, size, sha256, command, environment, and representative previews only.

## A2 design acceptance criteria

A2 design can be considered ready for execution-gate review only when the design package answers:

1. What exact algorithm family is proposed: SliceGAN-style, MPS/statistic-constrained, controlled latent diffusion, or another method?
2. Does it require training or model sampling?
3. What 2D inputs are used, and are they representative?
4. What is the target output volume size and voxel spacing?
5. What route labels will be carried forward?
6. How are formal route and nnUNet-qmatch route kept separate?
7. How is `ep015_all` used as planning anchor without turning it into final acceptance?
8. How is failed chunk `ep015_chunk000_063` retained in risk discussion?
9. Are 3D Euler/Minkowski implemented and phantom-validated, or explicitly de-scoped fail-closed?
10. Is S₂ boundary convention pinned and tested with asymmetric phantom?
11. Is deterministic regeneration proof defined?
12. Are hashes, commands, environment, seeds, and artifact policies defined?
13. Does the design preserve `scientific_status` boundaries?

## A2 execution gate question, pre-registered

Future gate question:

```text
May Branch A A2 execution begin under the specified algorithm, data, compute, artifact, and metric constraints?
```

Allowed future verdicts should be restricted to:

```text
ALLOW_A2_EXECUTION_WITH_CONSTRAINTS
ALLOW_A2_TOY_SCALEUP_ONLY
DO_NOT_START_A2_EXECUTION
```

This design card does not answer that future gate.

## Still-forbidden claims/actions

Do not write or imply:

- A2 execution is authorized.
- Real 2D→3D reconstruction has been run.
- Training/fine-tuning has been authorized.
- New model sampling has been authorized.
- New checkpoint has been created or selected.
- Voxel volume export is a scientific output.
- A1 toy or A2 design outputs are HY7 scientific evidence.
- B2-min final pass.
- B1.1 unconditional pass.
- ORIG raw pass.
- qmatch optional / implicit qmatch.
- selected chunk represents full model performance.
- formal route and nnUNet-qmatch route are merged without labels.
- 2D x/y penetrate proves 3D permeability/connectivity.

## Immediate next work item

Write the machine-readable A2 execution gate checklist:

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_branch_a_a2_execution_gate_checklist_20260706.json
```

The checklist should encode the blocking requirements above so a future A2 execution request can be audited mechanically before MoA review.
