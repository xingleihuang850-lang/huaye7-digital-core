# HY7 Stage 3 minimal 3D smoke gate record — 2026-07-06

## Gate question

May HY7 Stage 3 Branch A run one minimal qmatch-conditioned 3D smoke to test whether dimensional lifting preserves 3D connectivity and diagnostic physical-response consistency?

Not a request for: A2-small, A2-medium, scientific acceptance, full 2D->3D campaign, training, checkpoint operations, or a generative digital-well claim.

## Verdict

```text
ALLOW_MINIMAL_3D_SMOKE_ONLY
```

## Prerequisite verification

Prior gate returned `READY_TO_REQUEST_MINIMAL_3D_SMOKE_GATE_WITH_CONSTRAINTS`. Both cited files were read in full (not trusted on quote):

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_a2_smoke_completion_gate_moa_output_20260706.md
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_a2_smoke_completion_gate_record_20260706.md
```

All four carry-forward constraints from the prior gate are satisfied in this payload:

1. Per-channel condition declaration concretely populated (5 channels, status + rationale, blank->fail-closed).
2. Metric set enumerated verbatim with fail-closed slots (12 rows + frozen connectivity semantics).
3. Negative-evidence protocol specifies how (9 sections, manifest-mirrored, only-successes fails closed).
4. Request-level stamps present (not_a_generative_digital_well=true; ep015_chunk000_063 visible).

## Interpretation

This verdict authorizes ONE diagnostic smoke execution (smoke_execution_only=true), not A2 execution. Real HY7-derived / qmatch-conditioned candidate paths are permitted at smoke scale, restricted to the frozen diagnostic route.

Preserved:

```text
execution_authorized_by_this_gate=smoke_only
ready_for_a2_execution=false
scientific_status=diagnostic_smoke_not_evidence
route=nnUNet ep015_qmatch (diagnostic_calibrated_route_only)
calibration=hy7-gray-calibration-qmatch-v1
formal_anchor=ep015_all planning_anchor_only
not_a_generative_digital_well=true
```

## Scope granted

```text
one run; candidate_count_max=3
volume_target_preferred <=64^3; volume_target_max_without_extra_gate <=128^3
reruns for reproducibility verification only, must be labelled
launcher must NOT auto-proceed to A2-small or scaling
```

## Required package (12 files)

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

Git: no volumes/weights/checkpoints/.npy/.npz/.pt committed; metadata + sha256 + preview-hash only.

## Stop conditions after smoke

```text
no_axis_percolates_but_physical_response_proxy_is_positive
qmatch_route_label_missing_or_merged
3D_connectivity_metrics_absent_or_uninterpretable
S2_boundary_convention_missing
Euler_Minkowski_used_without_implementation_and_phantom_validation
negative_evidence_missing
volume_or_proxy_cannot_be_reproduced
```

## Still forbidden

```text
A2-small / A2-medium execution
full 2D->3D campaign
training / fine-tuning
checkpoint creation or selection
large volume export as scientific output
HY7 scientific acceptance claim
generative digital-well claim
B2-min final pass claim
qmatch as formal acceptance route
2D x/y penetration -> 3D permeability/connectivity
validated permeability claim from diagnostic proxy fields
condition-response / representativeness claim without future condition gate
```

## MoA evidence

- provider: `moa`
- preset/model: `digital-rock-gate`
- aggregator/acting model: `custom:dk-claude` claude-opus
- reference models actually consulted this turn: `openai-codex` gpt-5.5, `deepseek` v4-pro, `openrouter` z-ai/glm-5.2, `custom:dk-claude` claude-fable-5
- panel result: unanimous ALLOW_MINIMAL_3D_SMOKE_ONLY (aggregation of the four reference responses + aggregator)
- provenance note: this parent session invoked the real Hermes CLI command `hermes --provider moa -m digital-rock-gate` and saved stdout to the raw output file below. Inside that MoA run, the aggregator reported the listed reference models and flagged that the record must not overstate independence beyond the MoA aggregation.
- raw output: `experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_minimal_3d_smoke_gate_moa_output_20260706.md`

## Next allowed step

Write the minimal 3D smoke implementation/launcher + package contract. It may touch real HY7-derived/qmatch-conditioned candidate paths under the frozen route, produce ONE tiny diagnostic package, and must fail closed on any missing calibration artifact, failed-chunk record, metric slot, or negative-evidence section. It must not scale, train, checkpoint, or make any acceptance/digital-well claim.
