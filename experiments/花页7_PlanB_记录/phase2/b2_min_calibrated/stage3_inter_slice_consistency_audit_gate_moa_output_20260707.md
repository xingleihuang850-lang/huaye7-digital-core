I've verified both planning artifacts against the gate request. My verdict resolves a genuine split in the reference panel: two references (Codex, and implicitly the fail-closed logic) flag a blocking issue that the ALLOW-leaning references overlooked.

**The blocking flaw is real and confirmed by direct read.** The gate request itself lists as a fail-closed condition: *"any second-smoke/A2-small implication is made."* Yet the actual artifacts contain exactly that:

- Plan lines 140–153: a section titled **"Candidate for second-smoke request only after new gate"** listing conditions under which *"A future second-smoke request may be considered."*
- Checklist lines 88–95: key **`second_smoke_request_candidate_only_if`** with six unlock criteria.

Codex correctly caught this; the ALLOW-leaning references (DeepSeek, GLM, Sonnet) either treated this language as acceptably conservative or missed that it directly trips the request's own fail-closed trigger. But the boundary the user set is explicit — this audit runs *"before any future second-smoke or A2-small discussion"* — and the artifacts discuss precisely that. I cannot issue a clean ALLOW while the approved-scope documents violate a stated fail-closed condition.

The verdict is therefore not ALLOW-yet, but it is also not a scope rejection — the metadata-only concept is sound and well-motivated by the x-axis S2 collapse (~10× below y/z) plus all-axis non-percolation.

---

## VERDICT

```text
REQUIRE_FIXES_BEFORE_AUDIT_GATE
```

The metadata-only inter-slice consistency audit is **conceptually within the allowed diagnostic boundary**, but the current plan and checklist are **not gate-clean** because they contain downstream second-smoke implication language that trips the request's own fail-closed condition ("any second-smoke/A2-small implication is made"). No audit launcher/package implementation may proceed yet, except to correct the planning artifacts.

---

## BLOCKING FIXES (must land before any audit gate re-request)

1. **Remove second-smoke unlock language from the plan.** Delete/neutralize plan lines 140–153 ("Candidate for second-smoke request only after new gate" + its six criteria). Replace with an out-of-scope block:
```text
post_audit_downstream_status=out_of_scope
audit_result_does_not_authorize_or_imply_second_smoke=true
audit_result_does_not_authorize_or_imply_A2_small=true
any future execution gate is separate and not discussed here
```

2. **Remove/rename the checklist key.** Delete `second_smoke_request_candidate_only_if` (lines 88–95) or rename to a non-downstream neutral block (e.g. `post_audit_allowed_interpretation_limits`) containing only diagnostic interpretation boundaries — never future execution criteria. Keep `still_redesign_if` and `stop_or_route_redesign_if`; those are terminal/conservative and fine.

3. **Add explicit no-implication labels** to the metric-label block, so the audit output cannot be read as escalation:
```text
no_second_smoke_implication=true
no_a2_small_implication=true
```

---

## REQUIRED DESIGN FIXES (fold in during the same edit; enforced in implementation)

These come from the panel's strongest technical catches (Sonnet #1–#3, GLM axis control, DeepSeek/Sonnet hash re-verification):

4. **Pre-register numeric thresholds, not qualitative language.** The decision criteria currently say "much lower than," "severe decorrelation," "strong outlier bands" — post-hoc judgment calls that conflict with `no_cherry_pick_control`. Lock concrete cutoffs in the manifest *before* computing: specific Jaccard/Dice x-vs-y/z ratio cutoff, a specific S2 anisotropy ratio threshold, a specific MAD/z-score outlier threshold.

5. **Axis→physical-stacking mapping verified FIRST, not last.** `64×128×128` with slice range `384:448` (64 slices) implies axis 0 = the 2D-inference stacking axis = "x". This is the single most decisive fact (x-axis S2 collapse is exactly what a stacking artifact looks like). Verify against the actual array and write to `axis_boundary_semantics.md` before any other metric; fail closed on ambiguity as the first check.

6. **Label component-persistence / run-length as 2D-pairwise proxies**, computed from adjacent-slice 2D overlap only — explicitly *not* a 3D percolation solver — so the audit cannot be read as a disguised second connectivity smoke.

7. **In-implementation SHA256 re-verification.** The launcher must compute sha256 of the bytes it actually reads and compare to `24655b96b3f50ad14f8c60548afa9e0169babb76c24b605efa870e741502b7b2`, failing closed on mismatch before any metric. The `candidate_source=hy7-linux:...` path means the source is remote — run on hy7-linux or hash-verify a local copy; no unverified local copy is acceptable.

8. **No intermediate array persistence anywhere** (not just under git) — in-memory only, or scratch outside any repo path, deleted after run — so `candidate_arrays_written=false` stays true.

9. **Low-n caveat.** 64 slices = 63 adjacent pairs; report per-slice outlier/distribution stats as descriptive, not confirmatory tests, in `negative_evidence.md`/readme.

10. **Import guard.** `forbidden_claims.txt` must state that any import of torch/tensorflow/nnunet is a violation; the audit uses only numpy/scipy/json/hashlib.

---

## WHAT MAY PROCEED NEXT

Only the plan/checklist correction (fixes 1–3, folding in 4–6 as documentation) — a cheap documentation edit, not a scope change. **The audit launcher/package may NOT be implemented until the corrected artifacts are re-submitted through a gate.** Fixes 7–10 are then enforced in the implementation.

I did **not** authorize, and this verdict does not imply: second smoke, A2-small, A2-medium, full 2D→3D reconstruction, training/fine-tuning, checkpoint creation/selection, large-volume export, HY7 scientific acceptance, B2-min final pass, qmatch formal acceptance, validated permeability, or a generative digital-well claim. The failed chunk `ep015_chunk000_063` must remain visible throughout.

---

Want me to apply blocking fixes 1–3 (and fold in 4–6) to the plan and checklist now, so a corrected pair is ready for re-submission? I'll only touch those two files and won't implement any audit launcher.
