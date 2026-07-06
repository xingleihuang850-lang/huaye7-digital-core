# HY7 Stage 3 Branch A qmatch-conditioned minimal 3D smoke design — 2026-07-06

## Workflow node

- Node: `HY7-stage3-branch-A-qmatch-conditioned-minimal-3d-smoke-design`
- Parent design card: `stage3_branch_a_a2_design_only_card_20260706.md`
- Parent metric schema: `stage3_branch_a_a2_metric_interface_schema_20260706.json`
- Parent risk register: `stage3_branch_a_a2_risk_register_20260706.md`
- Status: `SMOKE_DESIGN_ONLY_EXECUTION_NOT_AUTHORIZED`
- Execution boundary: design only. This file does not authorize 3D smoke execution, real 2D→3D reconstruction, training, model sampling, checkpoint creation/loading, voxel export, or HY7 scientific claims.

## Reframed research risk

The 2D battlefield is mostly cleaned up. The remaining core uncertainty is not whether the existing 2D gate can be packaged more neatly; it is whether the qmatch-conditioned path still produces meaningful 3D connectivity and physical-response behavior after dimensional lifting.

Therefore the next research logic should not keep polishing 2D evidence. It should convert the largest uncertainty into a small, controlled, fresh-gated 3D smoke result:

```text
maximum uncertainty = qmatch-conditioned 3D connectivity + physical response validity
minimum next experiment = fresh-gated 3D smoke, not full A2 execution
```

This smoke is not a scientific acceptance run. It is an uncertainty-reduction experiment designed to answer whether the 3D path is even worth scaling.

## Smoke gate boundary

Before any smoke run, a fresh strict gate must explicitly authorize only the smoke. The allowed future verdicts should be:

```text
ALLOW_MINIMAL_3D_SMOKE_ONLY
ALLOW_TOY_OR_SYNTHETIC_3D_SMOKE_ONLY
DO_NOT_START_3D_SMOKE
```

The smoke gate must not authorize:

```text
A2-small scientific execution
A2-medium execution
full 2D→3D reconstruction campaign
training or fine-tuning
new checkpoint selection
large volume export as scientific output
HY7 scientific acceptance claim
```

## Smoke objective

The minimal 3D smoke should answer only four questions:

1. Can a qmatch-conditioned 3D candidate be produced or selected under a tightly bounded design without route-label contamination?
2. Do the 3D connectivity metrics return finite, interpretable values on the candidate?
3. Do simple physical-response proxies agree with the connectivity story at least qualitatively?
4. Does negative evidence appear early enough to stop before scaling?

If any answer is missing, the smoke fails closed.

## Candidate smoke scope

The smoke should be deliberately small:

```text
volume_target: <=64^3 preferred, <=128^3 only if explicitly gate-approved
candidate_count: 1-3 candidates maximum
route: qmatch-conditioned diagnostic route explicitly labelled
formal_anchor: ep015_all kept as planning anchor only, not acceptance
selected_chunk: triage-only, not full-model proof
failed_chunk: ep015_chunk000_063 retained as risk row
scientific_status: diagnostic_smoke_not_evidence
```

The smoke may use synthetic / proxy / dry-run volume paths only if the gate restricts it that way. If it touches real HY7-derived data, the gate must explicitly say so.

## Required 3D connectivity metrics

The smoke must emit a `metrics_3d_smoke.json` with, at minimum:

```text
porosity_phi_3d
connected_porosity_ratio_3d.pore_voxel_basis
connected_porosity_ratio_3d.total_volume_basis
percolation_flags_3d.x/y/z
largest_connected_component_fraction_3d.pore_voxel_basis
largest_connected_component_fraction_3d.total_volume_basis
s2_two_point_correlation_3d.x/y/z with boundary convention label
Euler/Minkowski status: implemented+phantom_validated OR explicitly_de_scoped_fail_closed
```

Connectivity semantics must remain:

```text
pore phase connectivity = 6-neighborhood
complementary solid/background connectivity = 26-neighborhood
percolation = one pore-phase connected component touches both opposing faces along axis k
axis mapping = x/y/z -> ndarray axes 0/1/2
```

## Required physical-response proxies

The smoke should not claim true permeability unless the method is implemented, validated, and gate-approved. Instead it should use clearly labelled physical-response proxies:

```text
percolation_supported_flow_proxy
connected_porosity_proxy
axis_anisotropy_proxy
resistivity_or_conductivity_proxy_if_available
formation_factor_proxy_if_available
```

Rules:

- If no connected pore path exists along an axis, any flow/proxy for that axis must be zero, absent, or fail-closed; it must not report a positive permeability-like response.
- If a proxy is computed, it must report method name, assumptions, units or unitless status, and whether it is qualitative only.
- Physical-response proxies are diagnostic only until a separate scientific validation gate.

## qmatch-specific risk controls

Because qmatch is a calibrated diagnostic route rather than the formal acceptance route, the smoke must keep qmatch visible instead of hiding it:

```text
route_label=nnUNet ep015_qmatch
route_status=diagnostic_calibrated_route_only
not_formal_acceptance_anchor=true
calibration_version=hy7-gray-calibration-qmatch-v1
formal_anchor=ep015_all planning_anchor_only
```

Fail closed if:

- qmatch route label is missing;
- qmatch metrics are merged with formal metrics;
- qmatch output is treated as unconditional acceptance;
- qmatch-conditioned 3D smoke is described as B2-min final pass;
- qmatch-conditioned physical response is described as validated permeability.

## Negative evidence required

The smoke is useful even if it fails. It must explicitly record:

```text
non-percolating axes
low connected porosity
high largest connected component mismatch
S2 axis/boundary disagreements
Euler/Minkowski missing or mismatch
physical-response proxy contradictions
route disagreement between formal anchor and qmatch diagnostic path
failed chunk ep015_chunk000_063 risk relation
```

A smoke that hides negative evidence is worse than no smoke.

## Minimal smoke package contract

A future smoke package should contain:

```text
branch_a_3d_smoke_manifest.json
branch_a_3d_smoke_readme.md
input_route_manifest.json
candidate_volume_manifest.json
metrics_3d_smoke.json
physical_response_proxy.json
connectivity_semantics.md
s2_boundary_semantics.md
euler_minkowski_status.md
negative_evidence.md
forbidden_claims.txt
hashes.txt
```

Large volumes must not be committed to git. If a candidate volume exists after a future gate, record only:

```text
path
size
sha256
generation_or_selection_command
environment
preview/downsample hash if available
```

## Stop / continue decision after smoke

The smoke should drive a hard decision tree:

### STOP

Stop and do not scale if:

- no axis percolates but physical response proxy is positive;
- qmatch route label is missing or merged;
- 3D connectivity metrics are absent or uninterpretable;
- S2 boundary convention is missing;
- Euler/Minkowski is used but not implemented + phantom-validated;
- negative evidence is missing;
- volume/proxy cannot be reproduced.

### REDESIGN

Redesign before scaling if:

- metrics are technically valid but connectivity and physical proxy disagree;
- only one axis is plausible and anisotropy interpretation is unclear;
- qmatch-conditioned route differs strongly from formal-anchor expectations;
- physical proxy is too crude to support even qualitative interpretation.

### CONSIDER A2-small gate

Only consider a later A2-small execution gate if:

- qmatch route labels are clean;
- 3D connectivity metrics are complete;
- physical-response proxy is qualitatively consistent with percolation/connected porosity;
- negative evidence is visible;
- provenance and hashes close;
- MoA/digital-rock-gate accepts the smoke as uncertainty-reducing evidence, not scientific acceptance.

## Design updates required elsewhere

This smoke design changes the emphasis of the A2 design package:

1. The next gate should be a **minimal 3D smoke gate**, not a full A2 execution gate.
2. A2 risk register must explicitly rank qmatch-conditioned 3D connectivity / physical response as the highest uncertainty.
3. Metric interface must include physical-response proxy fields as diagnostic smoke outputs.
4. Completion gate should ask whether the design package is complete enough to request a smoke gate, not whether A2 execution can start.

## Current status

```text
minimal_3d_smoke_execution_authorized=false
ready_for_smoke_gate_review=true_after_design_audit
ready_for_A2_execution=false
```

The immediate next permissible step is a strict completion/gate review of this smoke design package. It must not run the smoke unless that later gate explicitly allows `ALLOW_MINIMAL_3D_SMOKE_ONLY`.