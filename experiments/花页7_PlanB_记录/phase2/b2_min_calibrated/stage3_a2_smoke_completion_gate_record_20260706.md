# HY7 Stage 3 A2/smoke completion gate record — 2026-07-06

## Gate question

Is the current A2/smoke design package complete enough to request a separate fresh-gated minimal 3D smoke?

This gate does **not** authorize:

```text
3D smoke execution
A2 execution
A2-small / A2-medium
full 2D→3D campaign
training / fine-tuning
checkpoint operations
voxel volume export as scientific output
HY7 scientific acceptance claim
generative digital-well claim
```

## Verdict

```text
READY_TO_REQUEST_MINIMAL_3D_SMOKE_GATE_WITH_CONSTRAINTS
```

## Interpretation

The package is complete enough to submit a future **minimal 3D smoke gate request**. It is not complete enough to run the smoke without that future gate, and it is not an A2 execution authorization.

The strict MoA review accepted the package as request-stage complete because it now contains:

```text
A2 design card / checklist / metric schema / risk register
qmatch-conditioned minimal 3D smoke design
minimal 3D smoke gate checklist
condition-interface design
```

and preserves:

```text
execution_authorized=false
ready_for_a2_execution=false
smoke_gate_required_before_execution=true
scientific_status=diagnostic_smoke_not_evidence
```

## Required constraints to carry into the future smoke gate request

The MoA review said these are not blocking design fixes, but they must be carried into the actual smoke-gate request payload:

1. Per-channel condition declaration must be concretely populated:
   - depth/mineral/log/electrical-imaging = used / held / de-scoped / not available;
   - each channel needs a one-line rationale;
   - blank channel => gate fails closed.
2. Smoke metric set must be enumerated verbatim with pass/fail/negative-evidence slots:
   - 3D porosity;
   - connected porosity;
   - x/y/z percolation;
   - LCC fractions;
   - boundary-labelled S2 x/y/z;
   - Euler/Minkowski status.
3. Negative-evidence protocol must state how evidence is recorded and surfaced, not only that negative evidence is required.
4. The request itself must stamp:

```text
not_a_generative_digital_well=true
failed_chunk=ep015_chunk000_063 visible negative evidence
```

## Condition-interface judgment

The condition-interface / representativeness / conditional-response layer is adequately registered for this stage.

It is sufficient for requesting a minimal local 3D smoke because it forces the package to declare which condition channels are used, held constant, unavailable, or de-scoped. It also prevents the minimal smoke from being called a digital well.

However, digital-well claims remain impossible until future artifacts exist:

```text
condition_manifest.json
representativeness_audit.json
conditional_response_plan.json
conditional_response_gate / conditional_response_metrics.json
```

## Still forbidden

```text
3D smoke execution without a future smoke-gate verdict
A2 execution
A2-small / A2-medium
full 2D→3D campaign
training
checkpoint operations
volume export as scientific output
HY7 scientific acceptance
generative digital-well claim
qmatch as formal acceptance route
B2-min final pass
2D penetration => 3D permeability/connectivity
validated permeability claim from diagnostic proxy fields
positive flow proxy on a non-percolating axis
ep015_all treated as more than planning_anchor_only
```

## MoA evidence

- provider: `moa`
- preset/model: `digital-rock-gate`
- smoke test: `OK-ROCK`
- raw output:

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_a2_smoke_completion_gate_moa_output_20260706.md
```

## Next allowed step

Write the future minimal 3D smoke gate request payload. That payload may ask for `ALLOW_MINIMAL_3D_SMOKE_ONLY`, but it still must not execute the smoke unless that next gate approves it.