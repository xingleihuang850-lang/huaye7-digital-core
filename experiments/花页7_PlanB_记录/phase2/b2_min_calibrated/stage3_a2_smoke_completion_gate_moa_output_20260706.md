VERDICT: READY_TO_REQUEST_MINIMAL_3D_SMOKE_GATE_WITH_CONSTRAINTS

1. Verdict
READY_TO_REQUEST_MINIMAL_3D_SMOKE_GATE_WITH_CONSTRAINTS.

2. Complete enough to request a fresh-gated minimal 3D smoke?
Yes — request-stage complete, execution-stage not. All four design layers are present (A2 card/checklist/schema/risk register; qmatch-conditioned minimal smoke design; smoke gate checklist; condition interface). Every constraint the future gate must enforce is already declared: three-verdict-only smoke outcome space, frozen qmatch route (nnUNet ep015_qmatch, diagnostic_calibrated_route_only, hy7-gray-calibration-qmatch-v1), ep015_all planning_anchor_only, failed ep015_chunk000_063 visible, full metric set, fail-closed proxies, negative-evidence requirement, no permeability claim. Nothing escalates authority (execution_authorized=false, ready_for_a2_execution=false preserved). This verdict authorizes ONLY submitting the gate request; the fresh gate independently re-verifies and may still return DO_NOT_START_3D_SMOKE.

3. Required fixes before request
None blocking. Carry these AS CONSTRAINTS into the request payload (this is why WITH_CONSTRAINTS, not CONDITIONALLY_READY):
- Per-channel condition declaration must be concretely POPULATED (depth/mineral/log/electrical-imaging = used/held/de-scoped, one-line rationale each), not left as interface-only; any blank channel → gate fails closed.
- Enumerate the smoke metric set verbatim with pre-defined pass/fail/negative-evidence slots (3D porosity, connected porosity, percolation x/y/z, LCC fractions, boundary-labelled S2 x/y/z, Euler/Minkowski status).
- Negative-evidence protocol: specify HOW it is recorded/surfaced, not just that it is required.
- Stamp not_a_generative_digital_well=true and reference failed chunk ep015_chunk000_063 as visible negative evidence on the request itself, not only the design doc.

4. Condition-interface / representativeness / conditional-response layer
Adequately registered for THIS stage. Per-channel used/held/de-scoped semantics plus not_a_generative_digital_well=true correctly bound the minimal-smoke scope and prevent silent creep into digital-well claims. condition_manifest, representativeness_audit, and conditional_response_plan/gate are correctly positioned as deferred-but-mandatory future obligations gating any digital-well claim — not prerequisites for this smoke request. Fidelity is right: present enough to lock scope, deferred enough not to over-burden a diagnostic smoke.

5. Still-forbidden actions
- 3D smoke execution without a future smoke-gate verdict
- A2 execution; A2-small / A2-medium
- Full 2D→3D campaign
- Training; checkpoint operations
- Volume export as scientific output
- HY7 scientific acceptance
- Generative digital-well claim
- qmatch as formal acceptance route
- B2-min final pass
- 2D penetration ⇒ 3D permeability/connectivity inference
- Any validated permeability claim from diagnostic proxy fields; positive flow proxy on a non-percolating axis must fail closed
- Treating ep015_all as anything beyond planning_anchor_only

No execution authorized. Request submission only.
