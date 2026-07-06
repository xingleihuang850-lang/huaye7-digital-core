VERDICT: ALLOW_MINIMAL_3D_SMOKE_ONLY

Provenance: produced via Hermes MoA preset `digital-rock-gate` in this session.
Aggregator/acting model: custom:dk-claude claude-opus. Reference models actually
consulted this turn: openai-codex gpt-5.5, deepseek v4-pro, openrouter GLM-5.2,
custom:dk-claude claude-fable-5. All four references and the aggregator converged on
ALLOW_MINIMAL_3D_SMOKE_ONLY (unanimous). No separate external gate CLI was run; the
verdict is the aggregation of the reference responses listed above, authored here.
Reference 4 (fable-5) additionally flagged that an earlier draft of this record
overstated its provenance as an external tooling run; this block is the corrected,
truthful version.

## 1. Verdict

ALLOW_MINIMAL_3D_SMOKE_ONLY

Not the toy/synthetic downgrade. The gate question is whether dimensional lifting of the REAL HY7 qmatch-conditioned route preserves 3D connectivity and diagnostic physical-response consistency. A synthetic phantom cannot answer that question, and the payload contains no deficiency that would justify the downgrade. Synthetic phantoms remain RECOMMENDED as a validation harness for the connectivity / S2 / Euler code itself, before it touches the real candidate.

## 2. Prerequisite verification

Both prior-gate files were read in full (not trusted on quote):
- stage3_a2_smoke_completion_gate_moa_output_20260706.md
- stage3_a2_smoke_completion_gate_record_20260706.md
Both confirm the prior verdict `READY_TO_REQUEST_MINIMAL_3D_SMOKE_GATE_WITH_CONSTRAINTS` and enumerate four carry-forward constraints.

## 3. Constraint-by-constraint check (payload vs prior gate's four required carries)

1. Per-channel condition declaration concretely populated — SATISFIED. All five channels declared with explicit status + one-line rationale; only qmatch_calibration_version=used, the rest explicitly_de_scoped_until_future_gate. Blank/silently-imputed channels fail closed.
2. Metric set enumerated verbatim with pass/fail/negative-evidence slots — SATISFIED. 12 rows: 3D porosity; connected porosity on both denominators; percolation x/y/z (6-neighborhood pore); LCC on both denominators; boundary-labelled S2 x/y/z; Euler/Minkowski with "implemented+phantom_validated OR explicitly_de_scoped_fail_closed" slot. Connectivity semantics frozen (6/26 duality, face-to-face percolation, x/y/z->axes 0/1/2).
3. Negative-evidence protocol specifies HOW — SATISFIED. negative_evidence.md with nine enumerated sections, mirrored in manifest, plus anti-gaming rule: a smoke reporting only successes must fail closed.
4. Request-level stamps — SATISFIED. not_a_generative_digital_well=true and failed_chunk=ep015_chunk000_063 visible negative evidence appear in the request scope itself, not only design docs.

No authority escalation: ready_for_a2_execution=false, scientific_status=diagnostic_smoke_not_evidence, qmatch=diagnostic_calibrated_route_only, ep015_all=planning_anchor_only.

## 4. Answers to the five review questions

1. Verdict: ALLOW_MINIMAL_3D_SMOKE_ONLY.
2. Minimal 3D smoke implementation/launcher + package contract MAY be written next.
3. It MAY touch real HY7-derived / qmatch-conditioned candidate paths, restricted to route label `nnUNet ep015_qmatch`, calibration `hy7-gray-calibration-qmatch-v1` (mandatory; fail closed if the calibration manifest cannot be resolved at runtime), ep015_all as planning_anchor_only, ep015_chunk000_063 kept visible as negative evidence. NOT limited to toy/synthetic/dry-run, but diagnostic-only.
4. Launcher/package constraints — bind verbatim (see section 5).
5. Still-forbidden — restated unchanged (see section 6).

## 5. Required launcher / package constraints (binding)

Authority transition — this verdict DOES authorize one execution: smoke_execution_only=true. One run. candidate_count_max=3. Volume <=64^3 preferred, <=128^3 hard cap without a further gate. Reruns permitted ONLY for reproducibility verification and must be labelled as such — no retry-as-sweep, no candidate cherry-picking without logging all candidates.

Package contract (12 files, all required):
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

Git hygiene: no large volumes, model weights, checkpoints, or .npy/.npz/.pt in git. If a candidate volume exists, commit ONLY path/size/sha256/command/environment/preview-hash metadata (candidate_volume_manifest.json).

Metrics: every row filled with a value OR an explicit fail-closed status. Denominator ambiguity fails closed. Missing/non-finite -> negative evidence, never silent. Connectivity in code (not just docs): 6-neighborhood pore, 26-neighborhood solid, percolation = one pore component touching both opposing faces along axis k, x/y/z->axes 0/1/2. S2 boundary-labelled; missing boundary convention fails closed. Euler/Minkowski defaults to explicitly_de_scoped_fail_closed unless phantom validation is actually built — most likely accidental topology-claim vector.

Physical-response proxy: qualitative_only_flag=true; method_name + assumptions + units/unitless + axis_labels required. Fail closed on: positive_flow_proxy_on_non_percolating_axis; validated_permeability_claim_without_gate; method_or_assumptions_missing; axis_labels_missing. Percolation flags must be checked before any proxy field is written.

Negative evidence: all nine sections present and meaningful, incl. failed_chunk_ep015_chunk000_063_relation. All three S2/percolation axes reported even when disagreeing; axis disagreement -> negative evidence, not silence.

Runtime fail-closed: verify existence/hash of qmatch calibration artifact and the ep015_chunk000_063 failure record before producing any candidate; on failure emit a fail-closed package (negative evidence populated, metrics marked absent) rather than a partial success. Deterministic seeds + environment capture required. Launcher must NOT auto-proceed to A2-small or scaling logic after smoke completion.

Stop conditions after smoke (interpretation must stop, not scale):
no_axis_percolates_but_physical_response_proxy_is_positive
qmatch_route_label_missing_or_merged
3D_connectivity_metrics_absent_or_uninterpretable
S2_boundary_convention_missing
Euler_Minkowski_used_without_implementation_and_phantom_validation
negative_evidence_missing
volume_or_proxy_cannot_be_reproduced

A later, SEPARATE gate may consider A2-small only if the smoke shows: clean qmatch route labels; complete 3D connectivity metrics; proxy qualitatively consistent with percolation and connected porosity; visible negative evidence; provenance/hashes close; gate accepts smoke as uncertainty-reducing, not scientific acceptance.

## 6. Still forbidden even if smoke is allowed

A2-small scientific execution; A2-medium execution; full 2D-to-3D reconstruction campaign; training or fine-tuning; checkpoint creation or selection; large volume export as scientific output; HY7 scientific acceptance claim; generative digital-well claim; B2-min final pass claim; qmatch as formal acceptance route; 2D x/y penetration interpreted as 3D permeability/connectivity; validated permeability claim from diagnostic proxy fields; condition-response or representativeness claim without future condition gate.

No scaling authorized. One diagnostic smoke only.
