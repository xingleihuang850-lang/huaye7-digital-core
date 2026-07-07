## Verdict

**ALLOW_METADATA_ONLY_INTER_SLICE_AUDIT_WITH_CONSTRAINTS**

## Rationale

The single blocking defect from the prior `REQUIRE_FIXES_BEFORE_AUDIT_GATE` — downstream second-smoke implication language in the plan heading (`"Candidate for second-smoke request only after new gate"`) and the checklist key (`decision_criteria.second_smoke_request_candidate_only_if`) — has been fixed at the source, not papered over. The correction is verifiable in the diff:

- **Removed**: the offending heading and decision-criteria key.
- **Counter-asserted**: `no_second_smoke_implication=true`, `no_a2_small_implication=true`, `post_audit_downstream_status=out_of_scope`, plus the two `audit_result_does_not_authorize_or_imply_*` flags.

That was the specific defect; it is neutralized. Nothing else in the corrected artifacts contradicts the forbidden-claims list, and no new defect was introduced.

The package design is otherwise sound and remains within the parent gate:
- Scope is strictly metadata (JSON/MD/TXT), no arrays committed, `torch`/`tensorflow`/`nnunet` forbidden — consistent with `no-heavy-inference` and array-leakage controls.
- `first_check_fail_closed=axis_0_to_slice_stacking_mapping...` correctly gates all metric computation behind axis-convention verification — right order of operations for a 2D-stack-as-3D proxy.
- Thresholds are labeled negative-evidence-only, not acceptance — consistent with `qmatch formal acceptance claim` remaining forbidden.
- `component_persistence...proxy_not_3d_percolation` and `run_length...proxy_not_3d_percolation` are self-labeled to prevent misreading as percolation evidence.
- Failed chunk `ep015_chunk000_063` is a named visibility control, not hidden.
- Parent state (`REDESIGN_BEFORE_ANY_A2_SMALL_GATE`, `current_execution_authorized=false`, `ready_for_second_smoke=false`, `ready_for_a2_small_gate=false`) is left untouched and unaffected.

All five reference reviewers converge on the same verdict independently.

## Remaining blocking fixes

**None.** Two non-blocking hardening items to fold in during package authoring (not gate conditions):

1. Store distribution metrics (`adjacent_slice_jaccard_distribution_along_x`, `dice_distribution`, `s2_lag1_*`) as **summary statistics only** — median/percentiles/histogram bins — never full per-slice-pair or per-pixel arrays. Keeps them unambiguously "metadata" under the array-leakage control.
2. Add one explicit line to `negative_evidence.md` and/or `forbidden_claims.txt`: *"Audit outcome, pass or fail, has no bearing on `parent_smoke_verdict=REDESIGN_BEFORE_ANY_A2_SMALL_GATE` and does not reopen or modify that gate."* Closes residual ambiguity already implied by the flags.

## Exact next allowed action

Author and execute the metadata-only 9-file audit package, in this strict fail-closed order:

1. **Re-verify `source_sha256`** = `24655b96b3f50ad14f8c60548afa9e0169babb76c24b605efa870e741502b7b2` against `hy7-linux:/home/user/HXL/HY7_planb/phase2/b1_gray_sus_b11_rescue20_nnunet_review_20260706/ep015_qmatch_pore_nnunet2d.npy` **before loading anything**. Mismatch → halt.
2. **Run the axis-0-to-slice-stacking mapping check** for the `384:448` range (`first_check_fail_closed`). If it cannot be confirmed → halt, compute no metric, record the failure in `axis_boundary_semantics.md`.
3. **Compute only the pre-registered metrics** as summary-statistic metadata, using numpy/scipy/scikit-image only. No `torch`/`tensorflow`/`nnunet`. Write directly into the 9 named files; any scratch stays in an ephemeral non-repo location and is deleted immediately.
4. **Log failed chunk `ep015_chunk000_063`** as visible negative evidence in `negative_evidence.md` — do not omit or soften.
5. **Populate `forbidden_claims.txt`** with the full "still forbidden regardless" list verbatim, plus the two hardening lines.
6. **Compute `hashes.txt`** over the 9 output files (package integrity), not over the source array.
7. **Stop.** Thresholds flag negative evidence only — no acceptance. The audit authorizes nothing downstream.

## Explicitly NOT authorized by this verdict

Second smoke, A2-small, A2-medium, full 2D-to-3D reconstruction, training/fine-tuning, checkpoint creation/selection, large-volume export, HY7 scientific acceptance, B2-min final pass, qmatch formal acceptance, validated permeability, or generative digital-well claims — all remain blocked. Any future second-smoke or A2-small request requires a separate, later, stricter gate not addressed here.

Want me to author and run the 9-file package now under these constraints?
