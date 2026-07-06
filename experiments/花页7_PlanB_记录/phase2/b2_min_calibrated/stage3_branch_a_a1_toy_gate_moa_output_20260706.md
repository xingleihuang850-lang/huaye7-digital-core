# HY7 Stage 3 Branch A — A1 toy metric-plumbing gate record — 2026-07-06

- Gate node: `HY7-stage3-branch-A-A1-toy-metric-plumbing-gate`
- Parent gate: `HY7-handoff-stage3-planning-promotion-gate`
- Parent verdict: `PROMOTE_WITH_CONSTRAINTS`
- Parent level: `stage-3-planning-input only`
- Reviewer: `digital-rock-gate` MoA panel (aggregator custom:dk-claude:claude-opus-4-8; refs openai-codex:gpt-5.5, deepseek:deepseek-v4-pro, openrouter:z-ai/glm-5.2, custom:dk-claude:claude-fable-5)
- Mandate: strict scientific gate, not an encouraging summary.

## VERDICT

`ALLOW_A1_WITH_CONSTRAINTS`

Rationale for `WITH_CONSTRAINTS` over bare `ALLOW_A1_TOY_METRIC_PLUMBING_ONLY`:
the A0 schema justifies promotion and the proposed A1 scope is sound and
non-destructive, but the request has real gaps (no known-answer phantom, no
declared connectivity/percolation convention, no fail-closed Euler encoding, no
toy-route label hygiene). These must be BINDING conditions, not advisory notes,
or the "plumbing test" could run clean while silently computing wrong numbers.

## Evidence integrity (verified this gate)

- Design card sha256 = `166c7b57d9a645a9913126413f01cd81504180c7c0e18676a30b1d49919a51e2` — MATCH.
- Gate-metrics schema sha256 = `ecc77daf94fbfb0e7a20c3f7a3c65777a23d3a8078f6bf558d44cef838a2ba64` — MATCH.
- Constraints matrix sha256 = `590496c0d3a52cb6219a096c09014f5d8092b0350607daccf6bc8ee3b9d1e3b4` — MATCH.
- Handoff bundle `hashes.txt` re-check — all 7 files OK.
- JSON syntax — both schema and constraints matrix OK.
- Cross-consistency — design card pre-registers THIS exact gate as its next step;
  schema `next_gate_question` / `next_gate_expected_verdicts` match the request
  verbatim; frozen anchors (ep015_all formal, nnUNet qmatch diagnostic, triage
  chunk384_447, failed risk chunk000_063) identical across all three files. No anchor drift.
- Governance note: target record file pre-existed but was EMPTY (0 bytes) — a
  placeholder awaiting this verdict, not a conflicting prior ruling. This write
  is not an overwrite of substantive content.

## Answers to the seven review tasks

### 1. Verdict
`ALLOW_A1_WITH_CONSTRAINTS`.

### 2. Is A1 justified after A0?
Yes. A0 schema is complete, hash-verified, internally consistent, and
pre-registers this exact gate. A1 is the minimal next step that de-risks 3D
metric code paths and artifact package shape BEFORE any real reconstruction
gate. It is the least-speculative move that still advances the thesis 2D→3D
transition, and it introduces no scientific claim.

### 3. Exact constraints and required outputs if allowed

Authorized A1 scope (all binding):
- `volume_size <= 64^3`;
- `input_type = synthetic toy/mock volume only`;
- `scientific_status = not_evidence`;
- `purpose = verify 3D metric code paths and artifact package shape only`;
- no HY7 scientific claim; no B2-min final-pass claim;
- no training; no new sampling from any model; no checkpoint;
- no actual 2D→3D reconstruction claim;
- no large artifacts committed to git;
- outputs under a dry-run path only;
- A1 "may be started" — executing A1 and reporting A1 results is a separate
  action. This record authorizes A1; it does not contain A1 results.

Additional BINDING conditions (the substance of WITH_CONSTRAINTS):
- **C1 Known-answer phantom suite (non-negotiable).** A1 must validate metric
  code against >=2-3 analytically-known phantoms, e.g. solid/all-solid cube
  (phi known, trivial percolation), all-pore volume (phi=1), single straight
  through-channel (percolation must fire in exactly one axis), isolated single
  voxel/block. Computed values must match closed-form expectations or A1 FAILS
  CLOSED. A run that merely does not crash is not a pass.
- **C2 Connectivity convention declared.** `connectivity_semantics.md` must
  state the neighborhood convention (6/18/26) used for pore-phase connected
  components AND the complementary convention for solid phase, for CC,
  percolation flags, and Euler. This is the classic silent-inconsistency bug and
  ties directly to the project's "2D penetrate != 3D percolation" concern.
- **C3 Percolation definition explicit.** e.g. "a single pore-phase connected
  component touches both opposing faces along axis k." Written before computing.
- **C4 Fail-closed Euler encoding.** If Euler not implemented,
  `metrics_3d_toy.json` must carry `"euler_3d": {"status":
  "NOT_IMPLEMENTED_FAIL_CLOSED"}` — not null, not omission.
- **C5 Toy-route label hygiene.** Every A1 metrics JSON must carry
  `input_type: synthetic_toy`, `scientific_status: not_evidence`, and a distinct
  toy label (e.g. `route=synthetic_toy_plumbing`). Toy numbers must NOT carry the
  formal `threshold_formal_full_batch` or `nnUNet ep015_qmatch` route labels, so
  they can never be silently merged with the inherited 2D anchors.
- **C6 Determinism.** Any random toy volume must record seed + generator and be
  reproducible.

Required A1 outputs (committed):
```
branch_a_a1_manifest.json
branch_a_a1_readme.md
metrics_3d_toy.json
connectivity_semantics.md
forbidden_claims.txt
hashes.txt
```
Optional:
```
toy_volume_path.txt   # path/hash/size only, no volume committed
```

Required A1 metrics (`metrics_3d_toy.json`, each with an implementation-status
field `implemented` / `proxy` / `fail_closed_placeholder`):
- 3D porosity;
- 3D S2 along x/y/z, or a clearly named small-lag proxy if full S2 not yet
  implemented (name, lag set, axes, normalization must be stated);
- 3D connected porosity ratio;
- x/y/z percolation flags;
- 3D largest connected component fraction;
- 3D Euler characteristic, or explicit `NOT_IMPLEMENTED_FAIL_CLOSED` placeholder.

Required provenance fields:
- command; working directory; code version / git commit or source hash;
- environment / package versions sufficient to reproduce;
- timestamp; volume size; voxel spacing OR `synthetic_no_physical_spacing`;
- input type; random seed if used; toy generator params if used;
- route labels; artifact hashes; and, if any toy array exists outside git,
  its path/hash/size only.

### 4. May toy arrays be created, and committed to git?
Toy arrays MAY be created, only if explicitly labelled synthetic
metric-plumbing output and never used as HY7 evidence. They MUST NOT be
committed to git. If a binary toy array is materialized, keep it untracked or
outside git and record only path/hash/size in `toy_volume_path.txt`.
Standard caveat: `hashes.txt` cannot contain its own hash.

### 5. Missing metric/provenance requirements before A1
Before A1 may proceed, the following (absent from the base request) become
required: known-answer phantom suite (C1), declared connectivity convention
(C2), explicit percolation definition (C3), fail-closed Euler encoding (C4),
toy-route labeling (C5), seed/determinism recording (C6), and per-metric
implementation-status fields.

### 6. Forbidden actions still in force (restated verbatim + matrix additions)
- real 3D reconstruction;
- training;
- new sampling from DDPM or any generative model;
- new checkpoint;
- voxel export as scientific output;
- committing large volumes or weights to git;
- B2-min final-pass claim;
- B1.1 unconditional pass claim;
- ORIG raw pass claim;
- qmatch optional claim / implicit qmatch;
- treating selected 64-slice chunk as full model performance;
- merging formal route and nnUNet-qmatch route without labels;
- interpreting 2D x/y penetrate as 3D permeability or 3D connectivity;
- (from constraints matrix) second B1.1 topology rescue; gate relaxation;
  100/200ep or any scaling without a new explicit gate;
- starting A2 or any real reconstruction without a new explicit gate.

### 7. May A1 output be used as HY7 scientific evidence?
NO. A1 output cannot be used as HY7 scientific evidence under any circumstance.
It is toy metric-plumbing only. `scientific_status = not_evidence` must appear
in every A1 artifact and in `forbidden_claims.txt`.

## Next gate
A1 -> A2, any real 2D→3D reconstruction, any training, sampling, scaling,
checkpoint, or voxel export each require a NEW explicit gate. This record does
not authorize them.
