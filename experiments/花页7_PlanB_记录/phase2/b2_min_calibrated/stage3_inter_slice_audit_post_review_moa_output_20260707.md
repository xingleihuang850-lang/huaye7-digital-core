VERDICT

KEEP_REDESIGN_AND_WRITE_ROUTE_REMEDIATION_PLAN

RATIONALE

The gate question is whether the run01 metadata-only inter-slice audit gives grounds to relax the parent redesign requirement (→ request second smoke), escalate to termination (→ stop Branch A), or confirm-and-act on it as written (→ remediation plan). The metrics point unambiguously to the third.

Three of five pre-registered negative-evidence flags fired — a majority, not a borderline result:
- s2_x_over_min_yz_lt_0.25=true — x-axis S2 lag1 (0.00340) is under 10% of y (0.0358) and z (0.0372). The stacking axis carries almost none of the in-plane spatial structure.
- component_persistence_pairwise_median_lt_0.10=true — connected pore components do not persist across adjacent slices.
- per_slice_pore_count_robust_z_abs_gt_3.5=true (max 4.35) — outlier slices with abnormal pore counts.

Corroborating (not flag-gated) evidence: adjacent-slice Jaccard median ~0.028 and Dice ~0.055 are very low in absolute terms. This is the classic signature of a per-2D-slice nnUNet inference that is individually plausible per slice but incoherent along the stacking axis — exactly the slice-stacking decorrelation failure mode the parent redesign gate exists to catch.

Two flags did NOT fire (jaccard_x_median_over_yz_median_lt_0.25=false; zero_or_near_zero_pore_slice_run_ge_3=false), so the volume is not degenerate/empty — pores exist and are non-trivially distributed within slices. The problem is specifically inter-slice continuity, which is a route/reconstruction design defect, not noise.

Why not the other two verdicts:
- REQUEST_SECOND_SMOKE — unjustified. The audit did not mitigate the inconsistency concern; it substantiated it. The problems are structural, not noise-level, so a second smoke would test nothing new. The instructions explicitly forbid authorizing second smoke here and direct conservative remediation planning when the audit strengthens the risk. second_smoke_authorized remains false.
- STOP_BRANCH_A — over-escalation. scientific_status=diagnostic_metadata_only_not_evidence. The interpretation boundary states this audit does not prove scientific invalidity and does not reopen/modify the redesign gate. A metadata-only diagnostic is insufficient grounds for full route termination; a stop should be reserved for when remediation is judged structurally infeasible after actual planning — that determination has not been made.

The parent state (parent_smoke_verdict=REDESIGN_BEFORE_ANY_A2_SMALL_GATE, second_smoke_authorized=false, A2_small_authorized=false) remains controlling and unchanged. The only self-consistent action is to keep the redesign requirement in force and produce the planning artifact it implies.

EXACT NEXT ALLOWED ARTIFACT/ACTION

A text/metadata-only route-remediation plan (Markdown/JSON/TXT only — no arrays, checkpoints, or forbidden artifacts). Suggested path:

experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_route_remediation_plan_20260707_run01.md

Required contents:
1. Cite the run01 audit package by verified path and source_sha256 (24655b96…02b7b2), and record route_label=nnUNet ep015_qmatch, calibration_version=hy7-gray-calibration-qmatch-v1. State scientific_status=diagnostic_metadata_only_not_evidence.
2. Enumerate the four diagnostic drivers: the three fired flags plus the sub-threshold Jaccard/Dice medians, with their numeric values, as the motivation for route changes.
3. Root-cause hypotheses for x-axis decorrelation — e.g., independent per-2D-slice inference with no cross-slice conditioning/context; no 3D-consistency regularization or post-hoc smoothing; per-slice interaction of the qmatch calibration; downstream handling of the stacking mapping (even though axis_0_to_slice_stacking_mapping=verified, worth re-examining).
4. Non-execution remediation directions (proposals only): 2.5D/slab-context inference vs pure per-slice 2D; explicit inter-slice consistency loss or post-processing; planning-level review of checkpoint/ensemble strategy; alternative calibration schemes; whether qmatch is achievable with a 2D-only pipeline at all.
5. Tightened pre-registered numeric thresholds that a FUTURE audit would need to clear before a second-smoke gate could even be requested (explicit targets for s2_x_over_min_yz, component_persistence_pairwise_median, per_slice_pore_count_robust_z_abs, adjacent-slice Jaccard/Dice).
6. Explicit authorization statement: second_smoke_authorized=false and A2_small_authorized=false remain unchanged; this document does not alter REDESIGN_BEFORE_ANY_A2_SMALL_GATE; no scientific, qmatch, permeability, B2-min pass, or digital-well claims are made or implied.
7. A hashes.txt-style manifest consistent with the metadata-only package discipline.

GUARDRAILS FOR THE ACTING AGENT
- The deliverable is a documentation/planning file only. Do not run, schedule, or imply any smoke, A2-small/medium, reconstruction, training, checkpoint, or fine-tuning work.
- Do not flip second_smoke_authorized or A2_small_authorized to true, including implicitly via phrasing.
- Do not characterize the audit as resolving or disproving the redesign concern — it corroborates it.
- Keep scientific_status=diagnostic_metadata_only_not_evidence in any new metadata.
- Do not create or commit any .npy/.npz/.pt/weights/checkpoints/voxel arrays as part of this artifact.

Want me to draft the route-remediation plan .md at the suggested path now (documentation only, no execution)?
