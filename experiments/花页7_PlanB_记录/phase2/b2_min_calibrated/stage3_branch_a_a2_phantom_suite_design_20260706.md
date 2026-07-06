# HY7 Stage 3 Branch A A2 phantom-suite design — 2026-07-06

## Workflow node

- Node: `HY7-stage3-branch-A-A2-phantom-suite-design`
- Parent card: `stage3_branch_a_a2_design_only_card_20260706.md`
- Parent checklist: `stage3_branch_a_a2_execution_gate_checklist_20260706.json`
- Status: `A2_DESIGN_ONLY_PRE_EXECUTION`
- Execution boundary: design only; no A2 execution, no real 2D→3D reconstruction, no training, no model sampling, no checkpoint, no voxel export, no HY7 scientific claim.

## Purpose

This document designs the phantom suite needed before any future A2 execution gate. It does not implement the phantoms. It specifies what each phantom must prove, what metric failure it should catch, and which expected values may be asserted only after the implementation convention is fixed.

A1 already validated a small `8^3` known-answer suite:

```text
all_solid
all_pore
x_channel
isolated_voxel
```

A2 design must extend that suite to cover:

1. 3D Euler/Minkowski convention and implementation;
2. periodic vs non-periodic S₂ boundary convention;
3. scale-up beyond `8^3`;
4. deterministic-regeneration proof;
5. fail-closed topology handling before real 2D→3D reconstruction.

## Connectivity and topology conventions

Default design convention carried forward from A1:

```text
pore phase foreground connectivity: 6-neighborhood
complementary solid/background connectivity: 26-neighborhood
percolation definition: one pore-phase connected component touches both opposing faces along axis k
ndarray axis mapping: x/y/z -> axes 0/1/2
```

A2 execution must not silently change these conventions. If a future implementation chooses a different convention, the change must be explicit, justified, and gate-reviewed.

## Required phantom families

### P0 — all_solid

Purpose:
- zero-pore baseline;
- catches divide-by-zero / empty-component handling;
- verifies percolation flags stay false.

Expected design-level facts:

```text
porosity=0
percolation_x/y/z=false
largest_connected_component_fraction=0
connected_porosity_ratio=0
```

Euler/Minkowski:
- expected value must be written after implementation convention is chosen;
- if not implemented, status remains `NOT_IMPLEMENTED_FAIL_CLOSED`.

### P1 — all_pore

Purpose:
- full-pore baseline;
- verifies 3D porosity=1 and percolation in all axes;
- verifies S₂ lag-1 x/y/z=1 for both periodic and non-periodic conventions.

Expected design-level facts:

```text
porosity=1
percolation_x/y/z=true
largest_connected_component_fraction.pore_voxel_basis=1
connected_porosity_ratio.pore_voxel_basis=1
S2_lag1_x/y/z=1
```

### P2 — isolated_voxel

Purpose:
- single-component sanity;
- catches false percolation;
- catches total-volume vs pore-voxel denominator mistakes.

Expected design-level facts for size `N^3`:

```text
porosity=1/N^3
percolation_x/y/z=false
largest_connected_component_fraction.pore_voxel_basis=1
largest_connected_component_fraction.total_volume_basis=1/N^3
S2_lag1_x/y/z=0
```

Euler/Minkowski:
- should become the simplest positive object test after implementation;
- do not write a numeric Euler value until the implementation convention is fixed.

### P3 — straight_channel_x

Purpose:
- axis-specific percolation sanity;
- catches axis mapping bugs;
- catches connected-component bugs.

Construction design:

```text
volume=N^3
pore voxels at [:, mid, mid]
```

Expected design-level facts:

```text
porosity=N/N^3=1/N^2
percolation_x=true
percolation_y=false
percolation_z=false
largest_connected_component_fraction.pore_voxel_basis=1
S2_lag1_x=1/N^2 under non-periodic valid-pair lag-1 proxy
S2_lag1_y=0
S2_lag1_z=0
```

### P4 — straight_channel_y and straight_channel_z

Purpose:
- complete axis mapping coverage;
- prevents implementation that only works for axis 0.

Construction design:

```text
straight_channel_y: pore voxels at [mid, :, mid]
straight_channel_z: pore voxels at [mid, mid, :]
```

Expected design-level facts:
- same as P3 with axis rotated.

### P5 — two_disconnected_blobs

Purpose:
- component count sanity;
- catches largest-component and connected-porosity denominator errors.

Construction design:

```text
two non-touching cubic pore blocks
blocks separated by at least one solid voxel under 6-neighborhood
```

Expected design-level facts:

```text
component_count=2
percolation_x/y/z=false unless a block intentionally spans an axis
largest_connected_component_fraction.pore_voxel_basis=max(block_sizes)/sum(block_sizes)
```

Euler/Minkowski:
- exact expected value depends on implementation convention and block geometry;
- write analytic value only after implementation is chosen.

### P6 — hollow_cube_shell_or_cavity

Purpose:
- tests cavity / complement ambiguity;
- forces explicit foreground/background connectivity convention;
- catches Euler sign and background-connectivity mistakes.

Construction design:

```text
solid or pore shell with enclosed cavity, depending on foreground choice
must state whether the pore phase is shell or cavity
must state foreground/background convention before expected Euler is asserted
```

Expected design-level facts:
- do not write numeric Euler/Minkowski value before convention is fixed;
- this phantom is mandatory before topology-based A2 execution claims.

### P7 — torus_like_ring

Purpose:
- handle/genus sensitivity;
- tests Euler/Minkowski implementation beyond components/cavities.

Construction design:

```text
voxelized ring-like pore object with one handle
size must be large enough to avoid aliasing, likely >=32^3
```

Expected design-level facts:
- exact analytic value is convention- and voxelization-dependent;
- must be separately documented in the implementation PR/design before A2 execution.

### P8 — asymmetric_s2_boundary

Purpose:
- distinguishes periodic vs non-periodic S₂;
- catches silent boundary convention changes.

Construction design:

```text
volume=N^3
pore cluster near one x-boundary
no matching pore cluster near the opposite x-boundary
```

Expected design-level facts:

```text
non_periodic_valid_pairs_lag1 != periodic_wrap_lag1 for at least one axis
implementation must report convention label with every S2 metric
```

This phantom is required because `straight_channel_x` alone does not discriminate boundary handling strongly enough.

### P9 — sparse_random_seeded_toy

Purpose:
- deterministic-regeneration proof;
- catches seed/source-hash reproducibility bugs.

Construction design:

```text
seed recorded
generator recorded
source hash recorded
volume not committed
metrics hash or reproducible subset recorded
```

Expected design-level facts:
- same seed + same source hash + same command must regenerate the same declared metrics subset;
- if a future code change intentionally alters metrics, the source hash and expected metrics must change.

## Scale-up matrix

A2 design should require the following non-scientific toy scale-up matrix before execution:

| Size | Required phantoms | Purpose | Scientific status |
|---:|---|---|---|
| 8^3 | P0–P5, P8 | continuity with A1 and boundary tests | not_evidence |
| 16^3 | P0–P5, P8 | catches hard-coded 8^3 assumptions | not_evidence |
| 32^3 | P0–P8 where feasible | minimum for torus/ring topology design | not_evidence |

No scale-up toy output is HY7 scientific evidence. Every scale-up toy report must carry:

```text
scientific_status=not_evidence
```

## Phantom-suite fail-closed rules

A2 execution gate must fail closed if:

- connectivity convention is missing;
- S₂ boundary convention is missing;
- asymmetric S₂ phantom is missing;
- straight channels do not test x/y/z separately;
- Euler/Minkowski is used but not phantom-validated;
- Euler/Minkowski is unimplemented but topology claims are still made;
- deterministic-regeneration proof is missing;
- any toy volume is committed to git without explicit artifact-policy approval;
- any phantom output is labelled as HY7 evidence.

## Immediate implementation-design implications

Before A2 execution can be requested, a future implementation plan must decide:

1. whether Euler/Minkowski is implemented before execution or explicitly de-scoped;
2. whether S₂ reports non-periodic only or both non-periodic and periodic diagnostics;
3. how deterministic-regeneration proof is encoded in manifests;
4. whether phantom generation remains pure-code deterministic or writes external toy arrays;
5. how the phantom suite is tested in CI/focused pytest without committing volume artifacts.
