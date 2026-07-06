# HY7 Stage 3 minimal 3D smoke gate request — 2026-07-06

You are the strict `digital-rock-gate` MoA review panel. This is a fresh smoke gate request. It may authorize only a minimal diagnostic 3D smoke, not A2 execution.

## Gate question

May HY7 Stage 3 Branch A run one minimal qmatch-conditioned 3D smoke, under the constraints below, to test whether dimensional lifting preserves 3D connectivity and diagnostic physical-response consistency?

This is NOT a request for A2-small, A2-medium, scientific acceptance, a full 2D→3D campaign, training, checkpoint operations, or a generative digital-well claim.

## Candidate verdicts

Return exactly one of:

```text
ALLOW_MINIMAL_3D_SMOKE_ONLY
ALLOW_TOY_OR_SYNTHETIC_3D_SMOKE_ONLY
DO_NOT_START_3D_SMOKE
```

## Existing prerequisite gate

The prior completion gate returned:

```text
READY_TO_REQUEST_MINIMAL_3D_SMOKE_GATE_WITH_CONSTRAINTS
```

Raw evidence:

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_a2_smoke_completion_gate_moa_output_20260706.md
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_a2_smoke_completion_gate_record_20260706.md
```

## Requested allowed action if gate passes

If the verdict is `ALLOW_MINIMAL_3D_SMOKE_ONLY`, the next action would be to write a minimal smoke implementation/launcher and package contract. The launcher may produce only a tiny diagnostic smoke package under the constraints below.

If the verdict is `ALLOW_TOY_OR_SYNTHETIC_3D_SMOKE_ONLY`, the launcher must use toy/synthetic or dry-run paths only; no real HY7-derived 3D candidate.

If the verdict is `DO_NOT_START_3D_SMOKE`, no launcher or smoke run should be written.

## Proposed smoke scope

```text
execution_authorized_by_this_request=false until gate verdict is returned
if allowed: smoke_execution_only=true
ready_for_a2_execution=false
scientific_status=diagnostic_smoke_not_evidence
volume_target_preferred <=64^3
volume_target_max_without_extra_gate <=128^3
candidate_count_max=3
route_label_required=nnUNet ep015_qmatch
route_status=diagnostic_calibrated_route_only
calibration_version_required=hy7-gray-calibration-qmatch-v1
formal_anchor=ep015_all planning_anchor_only
selected_chunk_policy=triage_only_not_full_model_proof
failed_chunk_required=ep015_chunk000_063 visible negative evidence
not_a_generative_digital_well=true
condition_interface_status=not_yet_condition_response_test
```

## Condition channel declaration for this smoke request

| Channel | Status for this smoke request | Rationale |
|---|---|---|
| qmatch_calibration_version | used | The smoke must explicitly use/declare `hy7-gray-calibration-qmatch-v1` and route label `nnUNet ep015_qmatch`. |
| depth_or_interval_id | explicitly_de_scoped_until_future_gate | This smoke is local uncertainty reduction only; no depth-indexed wellbore sequence is claimed. |
| mineral_phase_or_lithofacies_label | explicitly_de_scoped_until_future_gate | Mineral/lithofacies response is a future conditional-response gate item; this smoke checks local 3D connectivity/response only. |
| log_constraints | explicitly_de_scoped_until_future_gate | GR/DEN/CNL/AC/RT/RXO conditioning is not used in this smoke; no log-conditioned generation claim is allowed. |
| electrical_imaging_constraints | explicitly_de_scoped_until_future_gate | Electrical imaging constraints are not used in this smoke; no imaging-constrained digital well claim is allowed. |

Blank or silently imputed condition channels must fail closed. This smoke is explicitly not a generative digital well.

## Minimal smoke package contract if allowed

A future package must include:

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

Large volumes, model weights, checkpoints, and `.npy/.npz/.pt` artifacts must not be committed to git. If a candidate volume exists, commit only path/size/sha256/command/environment/preview-hash metadata.

## Required 3D connectivity metrics with pass/fail/negative evidence slots

The package must report every item below, either with a value or explicit fail-closed status:

| Metric | Required label / denominator | Fail-closed / negative-evidence slot |
|---|---|---|
| `porosity_phi_3d` | scalar, volume basis | missing or non-finite value |
| `connected_porosity_ratio_3d.pore_voxel_basis` | pore-voxel denominator | missing denominator or non-finite value |
| `connected_porosity_ratio_3d.total_volume_basis` | total-volume denominator | missing denominator or non-finite value |
| `percolation_flags_3d.x` | pore 6-neighborhood | absent flag |
| `percolation_flags_3d.y` | pore 6-neighborhood | absent flag |
| `percolation_flags_3d.z` | pore 6-neighborhood | absent flag |
| `largest_connected_component_fraction_3d.pore_voxel_basis` | pore-voxel denominator | denominator ambiguity |
| `largest_connected_component_fraction_3d.total_volume_basis` | total-volume denominator | denominator ambiguity |
| `s2_two_point_correlation_3d.x` | boundary-labelled | missing S2 boundary convention |
| `s2_two_point_correlation_3d.y` | boundary-labelled | missing S2 boundary convention |
| `s2_two_point_correlation_3d.z` | boundary-labelled | missing S2 boundary convention |
| `euler_minkowski_status` | implemented+phantom_validated OR explicitly_de_scoped_fail_closed | topology claim while unimplemented |

Connectivity semantics are fixed unless a future gate changes them:

```text
pore_phase_connectivity=6-neighborhood
complementary_solid_connectivity=26-neighborhood
percolation=one pore-phase connected component touches both opposing faces along axis k
axis_mapping=x/y/z -> ndarray axes 0/1/2
```

## Required diagnostic physical-response proxy

`physical_response_proxy.json` must be diagnostic-only and must report:

```text
method_name
assumptions
units_or_unitless_status
qualitative_only_flag=true
axis_labels
consistency_with_percolation
percolation_supported_flow_proxy
connected_porosity_proxy
axis_anisotropy_proxy
resistivity_or_conductivity_proxy_if_available
formation_factor_proxy_if_available
```

Fail closed if:

```text
positive_flow_proxy_on_non_percolating_axis
validated_permeability_claim_without_gate
method_or_assumptions_missing
axis_labels_missing
```

## Required negative evidence protocol

Negative evidence must be surfaced in `negative_evidence.md` and mirrored in the manifest, not hidden in logs. It must include sections for:

```text
non_percolating_axes
low_connected_porosity
largest_connected_component_mismatch
S2_axis_or_boundary_disagreement
Euler_Minkowski_missing_or_mismatch
physical_response_proxy_contradictions
formal_vs_qmatch_route_disagreement
failed_chunk_ep015_chunk000_063_relation
unreproducible_volume_or_metrics
```

The smoke is useful if it fails, provided the failure is explicit. A smoke that reports only successes must fail closed.

## Stop conditions after smoke

Even if this gate permits the smoke, the post-smoke interpretation must stop rather than scale if:

```text
no_axis_percolates_but_physical_response_proxy_is_positive
qmatch_route_label_missing_or_merged
3D_connectivity_metrics_absent_or_uninterpretable
S2_boundary_convention_missing
Euler_Minkowski_used_without_implementation_and_phantom_validation
negative_evidence_missing
volume_or_proxy_cannot_be_reproduced
```

## Conditions to consider later A2-small gate

Only a later, separate gate may consider A2-small, and only if the smoke package shows:

```text
qmatch_route_labels_clean
3D_connectivity_metrics_complete
physical_response_proxy_qualitatively_consistent_with_percolation_and_connected_porosity
negative_evidence_visible
provenance_and_hashes_close
digital_rock_gate_accepts_smoke_as_uncertainty_reducing_not_scientific_acceptance
```

## Still forbidden even if smoke is allowed

```text
A2-small scientific execution
A2-medium execution
full 2D-to-3D reconstruction campaign
training or fine-tuning
checkpoint creation or selection
large volume export as scientific output
HY7 scientific acceptance claim
generative digital-well claim
B2-min final pass claim
qmatch as formal acceptance route
2D x/y penetrate interpreted as 3D permeability/connectivity
validated permeability claim from diagnostic proxy fields
condition-response or representativeness claim without future condition gate
```

## Review request

Please answer:

1. Verdict from the three candidate verdicts.
2. Whether a minimal 3D smoke implementation/launcher may be written next.
3. If allowed, whether it may touch real HY7-derived/qmatch-conditioned candidate paths or must remain toy/synthetic/dry-run only.
4. Required launcher/package constraints.
5. Still-forbidden actions and claims.

Be strict. If condition-channel declarations, metric slots, physical proxy constraints, or negative-evidence protocol are insufficient, return `DO_NOT_START_3D_SMOKE` or `ALLOW_TOY_OR_SYNTHETIC_3D_SMOKE_ONLY`, not encouragement.
