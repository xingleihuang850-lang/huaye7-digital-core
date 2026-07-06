# HY7 Stage 3 conditional digital-well interface design — 2026-07-06

## Workflow node

- Node: `HY7-stage3-conditional-digital-well-interface-design`
- Related Branch A node: `HY7-stage3-branch-A-qmatch-conditioned-minimal-3d-smoke-design`
- Status: `CONDITION_INTERFACE_DESIGN_ONLY_EXECUTION_NOT_AUTHORIZED`
- Execution boundary: design only. This file does not authorize 3D smoke execution, A2 execution, training, model sampling, checkpoint creation/loading, voxel export, or HY7 digital-well scientific claims.

## Why this exists

The previous largest uncertainty was whether 2D evidence can be lifted to 3D. The qmatch-conditioned minimal 3D smoke addresses that. The next missing layer is different:

```text
even a valid 3D local digital core may still be an unconditional local digital rock,
not a generative digital well constrained by wellbore information.
```

A digital well must change in a verifiable way with conditioning variables such as depth, lithofacies/mineral phase, logs, and electrical imaging constraints. If those variables do not enter the generation path and if outputs do not respond to them, the result is not yet a generative digital well, even if local 3D metrics look plausible.

## Design objective

Add a condition-interface layer to Stage 3 planning so future gates distinguish:

| Object | Meaning | Current status |
|---|---|---|
| local digital core | one local 3D porous medium candidate | design/smoke only |
| qmatch-conditioned 3D smoke | diagnostic 3D candidate under calibrated qmatch route | future fresh gate required |
| condition-aware digital core | 3D candidate with declared conditioning vector and response checks | design only |
| generative digital well | depth-indexed / log-constrained sequence of condition-responsive 3D candidates | not authorized |

The immediate minimal 3D smoke may remain small, but it must no longer be interpreted as digital-well progress unless it records condition status explicitly.

## Conditioning variables to design for

Future condition interface should support these categories, even if the first smoke de-scopes some fields:

```text
depth_or_interval_id
stratigraphic_unit_or_layer_label
mineral_phase_or_lithofacies_label
porosity_or_pore_fraction_target
log_constraints: GR, DEN, CNL, AC, RT/RXO where available
electrical_imaging_constraints: fracture/lamination/bedding orientation proxies where available
core_or_thin_section_slice_id
qmatch_calibration_version
route_label and source model/checkpoint label
```

Every condition field must have one of:

```text
provided
not_available
held_constant_for_smoke
explicitly_de_scoped_until_future_gate
```

Missing fields must not be silently imputed.

## Minimum condition interface schema

Future condition-aware packages should emit:

```text
condition_manifest.json
representativeness_audit.json
conditional_response_plan.json
conditional_response_metrics.json  # only after a future gate/run
condition_semantics.md
```

### `condition_manifest.json` required fields

```text
condition_schema_version
depth_or_interval_id
sample_or_slice_ids
route_label
qmatch_calibration_version
available_condition_channels
unavailable_condition_channels
held_constant_channels
explicitly_de_scoped_channels
normalization_or_binning_policy
source_hashes
provenance
scientific_status
```

### `representativeness_audit.json` required checks

```text
sample coverage over depth/intervals
mineral/lithofacies coverage if labels exist
log-range coverage if logs exist
imaging-feature coverage if electrical imaging exists
whether selected slices/candidates are local-only or interval-representative
negative evidence: missing intervals, missing phases, out-of-range logs
```

### `conditional_response_plan.json` required checks

```text
which condition variable is perturbed
what output metric should respond
expected response direction if physically justified
what should remain invariant
what counts as non-response
what counts as physically inconsistent response
```

## Conditional response gate

A future conditional-response gate should ask:

```text
Do generated 3D candidates change in the expected, physically interpretable way when depth/mineral/log/electrical-imaging conditions change, without losing route labels, provenance, or 3D connectivity/physical-response sanity?
```

Allowed future verdicts:

```text
ALLOW_CONDITIONAL_RESPONSE_SMOKE_ONLY
ALLOW_CONDITION_INTERFACE_DESIGN_ONLY
DO_NOT_START_CONDITIONAL_RESPONSE_TEST
```

This gate is distinct from the minimal 3D smoke gate. The minimal 3D smoke tests whether qmatch-conditioned 3D connectivity and simple physical proxies are coherent. The conditional-response gate tests whether the generator is condition-aware rather than unconditional.

## Interaction with minimal 3D smoke

Before a minimal 3D smoke is run, the smoke package should at least declare:

```text
condition_interface_status=not_yet_condition_response_test
condition_channels_used=[qmatch route/calibration at minimum]
condition_channels_held_constant_or_de_scoped=[depth, mineral, logs, electrical imaging as applicable]
not_a_generative_digital_well=true
```

If the smoke uses only qmatch calibration and no depth/mineral/log/imaging variables, it may still be useful as a local 3D uncertainty-reduction smoke. It must not be called a digital well.

## Fail-closed conditions

Fail closed if:

- a result is called a digital well without condition manifest;
- depth/mineral/log/electrical-imaging constraints are claimed but not present in `condition_manifest.json`;
- generated outputs do not change when condition variables change, yet are described as conditional;
- outputs change with condition variables but the change is physically uninterpretable or contradicts logs/imaging;
- representativeness audit is missing;
- unavailable condition channels are silently imputed;
- qmatch calibration version or route label is missing;
- local 3D smoke is used as evidence of wellbore-scale representativeness.

## Required update to research narrative

Current defensible statement:

```text
HY7 now has a strictly controlled local 2D generation evidence chain and a calibrated handoff into Stage 3 planning.
```

Not yet defensible:

```text
HY7 has a generative digital well.
```

Missing bridge:

```text
condition variables must enter the generation model, and generated 3D outputs must show verifiable, physically interpretable response across depth, mineral phase, logs, and electrical imaging constraints.
```

## Current status

```text
condition_interface_design_present=true
condition_response_test_authorized=false
minimal_3d_smoke_may_request_gate_after_completion_review=true
A2_execution_authorized=false
generative_digital_well_claim_authorized=false
```
