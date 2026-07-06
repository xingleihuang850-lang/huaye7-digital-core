# HY7 Stage 3 Branch A A2 risk register — 2026-07-06

## Workflow node

- Node: `HY7-stage3-branch-A-A2-risk-register`
- Parent card: `stage3_branch_a_a2_design_only_card_20260706.md`
- Parent checklist: `stage3_branch_a_a2_execution_gate_checklist_20260706.json`
- Phantom design: `stage3_branch_a_a2_phantom_suite_design_20260706.md`
- Metric interface schema: `stage3_branch_a_a2_metric_interface_schema_20260706.json`
- Parent gate verdict: `A1_COMPLETE_WITH_CONSTRAINTS_ALLOW_A2_DESIGN_ONLY`
- Status: `A2_DESIGN_ONLY_RISK_PRE_REGISTRATION`
- Execution boundary: design/risk registration only. This file does **not** authorize A2 execution, real 2D→3D reconstruction, training, model sampling, checkpoint creation/loading, voxel export, or HY7 scientific claims.

## Purpose

This risk register pre-registers risks for a future Branch A A2 execution request. It is deliberately conservative at the gate boundary: every risk has an owner, required evidence, fail-closed trigger, and mitigation. The goal is to let future A2 execution be reviewed mechanically before MoA/digital-rock-gate review, not to start A2 by implication.

## Severity / likelihood scale

| Code | Meaning |
|---|---|
| S1 | minor bookkeeping risk; does not affect scientific interpretation if corrected |
| S2 | moderate engineering/provenance risk; blocks execution package if unresolved |
| S3 | major scientific/metric risk; can invalidate A2 execution or downstream claims |
| S4 | critical gate risk; must fail-closed immediately |

| Code | Meaning |
|---|---|
| L1 | unlikely if checklist is followed |
| L2 | plausible |
| L3 | likely without explicit controls |
| L4 | expected unless addressed before execution |

Risk score is `severity × likelihood`; any S4 item is gate-critical regardless of numeric score.

## Gate-wide non-negotiables

A2 execution must fail closed if any of the following occur:

```text
fresh strict A2 execution gate is missing
algorithm family is unnamed
input_2d_slice_manifest is missing
formal route and nnUNet-qmatch route are merged without labels
failed chunk ep015_chunk000_063 disappears from risk discussion
S2 boundary convention is missing
asymmetric S2 phantom is missing
Euler/Minkowski is used without implementation + phantom validation
Euler/Minkowski is unimplemented but topology acceptance claims are made
deterministic-regeneration proof is missing for toy/generated artifacts
large volume or model weight is committed to git
scientific_status boundary is missing
A1/A2 design output is treated as HY7 scientific evidence
```

## Risk register

| ID | Area | Risk statement | Level | Likelihood | Trigger / negative evidence | Required control | Fail-closed condition | Owner |
|---|---|---|---:|---:|---|---|---|---|
| A2-R01 | Gate authorization | A2 execution starts by implication after design completion. | S4 | L2 | any run command, generated volume, model sampling, checkpoint, or voxel export before strict gate | keep `execution_authorized=false`; require fresh strict gate record | any A2 execution artifact exists without gate | gate owner |
| A2-R02 | Scope creep | A2 design-only files are cited as scientific results. | S4 | L3 | wording such as HY7 evidence, B2-min final pass, A2 passed, final reconstruction | require `scientific_status=design_only_not_evidence` / `not_evidence` | any scientific claim from design-only output | documentation owner |
| A2-R03 | Algorithm ambiguity | Future A2 request omits algorithm family or training/sampling path. | S3 | L3 | missing SliceGAN/MPS/diffusion/etc.; unclear whether training/sampling occurs | `algorithm_config.json` must name method and execution mode | algorithm family or training/sampling mode missing | A2 proposer |
| A2-R04 | Input ambiguity | 2D input slice manifest is missing or under-specified. | S4 | L2 | no slice IDs, provenance, route labels, source hashes, voxel spacing/modality | `input_2d_slice_manifest.json` required | missing or unverifiable input manifest | data owner |
| A2-R05 | Route contamination | formal full-batch route and nnUNet-qmatch diagnostic route are merged. | S4 | L3 | metrics appear without route labels; qmatch used as acceptance silently | route labels required in every inherited metric | unlabelled merge or implicit qmatch | metric owner |
| A2-R06 | Triage misuse | selected chunk `ep015_chunk384_447` is treated as full-model acceptance. | S4 | L2 | text says selected chunk represents overall performance | selected chunk must stay `triage_only` / `not_acceptance_anchor=true` | selected chunk used as acceptance anchor | gate owner |
| A2-R07 | Negative evidence loss | failed chunk `ep015_chunk000_063` disappears from A2 risk discussion. | S4 | L3 | no failed-row reference; maxCC>0.070 omitted | `failed_risk_chunk` must remain visible | failed chunk omitted or softened | risk owner |
| A2-R08 | 2D/3D semantic overreach | 2D x/y penetrate is interpreted as 3D connectivity/permeability. | S4 | L3 | claim that 2D penetrate proves 3D connectivity/permeability | carry forbidden interpretation in schema and claims lint | any 3D permeability/connectivity claim based on 2D penetrate | science owner |
| A2-R09 | S2 boundary drift | S₂ implementation silently changes periodic/non-periodic convention. | S3 | L3 | S₂ values change without boundary label; no asymmetric phantom | report convention with every S₂ metric; include asymmetric S2 phantom | boundary convention missing or untested | metric owner |
| A2-R10 | S2 axis omission | 3D S₂ is reported without x/y/z axes. | S3 | L2 | scalar S₂ only; no axis labels | require axes `[x,y,z]` | axes missing for 3D S₂ | metric owner |
| A2-R11 | Connectivity convention ambiguity | pore/solid connectivity convention is missing or changed silently. | S4 | L2 | no 6/26 convention; alternative convention undocumented | declare pore=6, complementary solid=26, or gate-reviewed change | convention missing or unreviewed change | topology owner |
| A2-R12 | Percolation definition ambiguity | percolation flags lack face-touch component definition. | S3 | L2 | percolation reported without definition | require explicit component touches opposing faces along axis k | definition missing | topology owner |
| A2-R13 | Euler/Minkowski placeholder misuse | `NOT_IMPLEMENTED_FAIL_CLOSED` is treated as acceptable execution metric. | S4 | L3 | topology claims while Euler/Minkowski unimplemented | implement + phantom validate or explicitly de-scope fail-closed | topology metric/claim uses placeholder | topology owner |
| A2-R14 | Euler convention error | Euler/Minkowski sign or foreground/background convention is wrong. | S3 | L3 | hollow/torus phantom mismatch; sign convention undocumented | analytic phantom suite with convention-specific expected values | phantom mismatch or convention missing | topology owner |
| A2-R15 | Phantom insufficiency | phantom suite lacks axis, boundary, component, cavity, or handle tests. | S3 | L2 | missing straight_channel_y/z, asymmetric S2, hollow cube, torus | required phantom families from phantom design | required phantom family absent | test owner |
| A2-R16 | Scale hard-coding | metrics only work at 8^3 and fail at 16^3/32^3. | S2 | L3 | size-dependent failure or hard-coded shape | scale-up design at 8^3/16^3/32^3 | no scale-up validation design before execution | test owner |
| A2-R17 | Determinism gap | toy/generated artifact cannot be regenerated from seed/source hash/command. | S3 | L3 | regenerated metrics hash differs; source hash absent | deterministic-regeneration proof required | proof missing or mismatch unexplained | provenance owner |
| A2-R18 | Artifact bloat | large volumes/checkpoints/weights are committed to git. | S3 | L2 | `.npy`, `.npz`, `.pt`, checkpoints, generated volumes in git | record external artifact path/size/sha256 instead | large artifact committed without explicit policy approval | repo owner |
| A2-R19 | Hash/provenance gap | outputs lack sha256, command, environment, workdir, source hashes. | S3 | L2 | cannot reproduce or audit package | `provenance.json` + `hashes.txt` required | required provenance missing | provenance owner |
| A2-R20 | Voxel spacing/modality ambiguity | future 3D volume lacks voxel spacing/modality declaration. | S3 | L2 | output volume size present but physical/modality context absent | manifest must include voxel spacing and modality | spacing/modality missing | data owner |
| A2-R21 | Permeability overclaim | permeability/proxy is discussed before real gated 3D volume exists. | S4 | L2 | permeability proxy emitted from toy/design output | schema marks permeability not allowed before real 3D volume | permeability/proxy claim before real volume | science owner |
| A2-R22 | Porosity denominator mismatch | connected porosity/LCC denominator switches between pore-basis and volume-basis silently. | S3 | L2 | only one denominator reported; ambiguous fraction | report both pore_voxel_basis and total_volume_basis | denominator missing or unlabeled | metric owner |
| A2-R23 | Algorithm/data mismatch | selected algorithm assumes isotropic, stationary 2D texture that HY7 inputs do not support. | S3 | L2 | no stationarity/anisotropy discussion; algorithm constraints absent | algorithm config must state assumptions and input representativeness | assumptions omitted | A2 proposer |
| A2-R24 | SliceGAN-style hallucination | adversarial dimensional expansion creates plausible but topologically wrong 3D structures. | S3 | L2 | good visual texture but failing 3D connectivity/topology metrics | require 3D topology/percolation metrics; no visual-only acceptance | visual-only acceptance | science owner |
| A2-R25 | MPS/statistical overfitting | MPS/statistic-constrained reconstruction matches local stats but misses long-range connectivity. | S3 | L2 | S2/porosity match but percolation/LCC fail | require multi-metric gate, including percolation and LCC | local-stat-only acceptance | science owner |
| A2-R26 | Diffusion sampling opacity | controlled latent diffusion introduces undocumented sampling stochasticity. | S3 | L3 | seed/sampler/config missing; results not reproducible | record seed, sampler, schedule, model/hash, prompt/conditioning if any | stochastic config missing | A2 proposer |
| A2-R27 | Compute budget creep | A2 execution silently scales beyond approved toy/small/medium target. | S2 | L2 | volume size or runs exceed declared budget | output size and compute budget required in gate | undeclared scale-up | gate owner |
| A2-R28 | A2-small premature execution | 128^3 real reconstruction starts before design completion gate. | S4 | L2 | 128^3 real output exists before fresh gate | require A2 design completion gate then A2 execution gate | 128^3 real output without gate | gate owner |
| A2-R29 | A2-medium premature execution | 256^3 or larger reconstruction starts before A2-small evidence/gate. | S4 | L1 | 256^3 output/checkpoint before small-gate | require staged escalation | 256^3 output without explicit gate | gate owner |
| A2-R30 | Claim-language drift | Chinese/English wording bypasses forbidden-claim lint. | S3 | L2 | “通过/最终/代表整体/可选 qmatch”等 unsafe language | maintain bilingual forbidden claims | unsafe wording appears | documentation owner |
| A2-R31 | Missing negative-result handling | failed metrics are hidden or only successes are summarized. | S4 | L2 | metrics JSON lacks failed rows/errors | package must include negative evidence and errors | negative evidence omitted | risk owner |
| A2-R32 | Environment mismatch | local design tests pass but future execution environment differs. | S2 | L2 | package lacks env versions or runtime info | record Python/env/tool versions and commands | env absent | provenance owner |
| A2-R33 | External artifact rot | external volumes/previews are referenced but later unavailable. | S2 | L2 | path broken; hash unavailable | record path, size, sha256, storage location, representative previews | external artifact not resolvable | repo owner |
| A2-R34 | Design package incompleteness | A2 design package lacks one of card/checklist/phantom/schema/risk files. | S3 | L2 | required design file missing | design package completion gate | required file missing | documentation owner |
| A2-R35 | MoA routing risk | future gate uses wrong provider/preset or a non-strict review. | S3 | L2 | review not `digital-rock-gate`; no refs/aggregator recorded | require `provider=moa`, `preset=digital-rock-gate`, raw output saved | gate review not strict or not saved | gate owner |

## Stage-specific risk controls

### A1 toy metric-plumbing inheritance

A1 is complete only as toy plumbing. Its risks carry forward as controls, not as evidence:

- A1 phantoms validate code paths, not HY7 geology.
- A1 `8^3` does not validate scale.
- A1 Euler/Minkowski is fail-closed, not implemented.
- A1 no-volume policy must continue unless an explicit artifact policy changes.

### A2-small risk profile

A2-small means a future, gate-authorized small real reconstruction target, likely around `128^3`. It has the highest semantic risk because it is the first possible transition from toy/design outputs to real 2D→3D reconstruction. Required controls:

```text
fresh A2 execution gate
algorithm_config.json
input_2d_slice_manifest.json
route_constraints.json
metrics_3d_reconstruction.json
S2 boundary semantics
connectivity semantics
Euler/Minkowski implemented+validated or explicitly de-scoped
provenance.json
hashes.txt
negative evidence retained
```

A2-small must not be called scientifically accepted unless a separate future scientific acceptance gate says so.

### A2-medium risk profile

A2-medium means a future larger reconstruction target, likely around `256^3`. It must not be used to bypass A2-small evidence. Required additional controls:

```text
A2-small package review
scale/performance budget
memory/runtime budget
external artifact storage policy
preview/downsample hash policy
failure-mode comparison to A2-small
new strict gate
```

A2-medium fails closed if it starts before A2-small risks are reviewed.

## Negative evidence policy

Negative evidence is not optional. Future A2 packages must record:

- failed phantom cases;
- metric exceptions;
- route disagreements;
- mismatch between formal and diagnostic routes;
- S2 boundary disagreement;
- Euler/Minkowski not implemented or mismatch;
- failed chunks, especially `ep015_chunk000_063`;
- large-artifact omissions or external-path failures.

If negative evidence is missing, the package is incomplete and must fail closed.

## Claim boundary policy

Allowed wording for A2 design:

```text
A2 design-only
not evidence
execution not authorized
future gate required
planning anchor only
triage only
fail-closed placeholder
```

Forbidden wording:

```text
A2 executed
real 2D→3D reconstruction completed
HY7 scientific evidence from A1/A2 design
B2-min final pass
B1.1 unconditional pass
ORIG raw pass
qmatch optional
selected chunk represents full model performance
2D x/y penetrate proves 3D permeability/connectivity
```

## Minimum evidence before A2 design completion gate

Before asking whether the A2 design package is complete enough for an A2 execution-gate review, the package must include:

```text
stage3_branch_a_a2_design_only_card_20260706.md
stage3_branch_a_a2_execution_gate_checklist_20260706.json
stage3_branch_a_a2_phantom_suite_design_20260706.md
stage3_branch_a_a2_metric_interface_schema_20260706.json
stage3_branch_a_a2_risk_register_20260706.md
```

and must pass a mechanical audit for:

```text
execution_authorized=false
scientific_status boundary present
route constraints present
failed chunk visible
S2 boundary semantics present
Euler/Minkowski fail-closed / validation policy present
deterministic regeneration policy present
large artifact policy present
fresh strict gate required before execution
```

## Current risk posture

Current status after writing this register:

```text
A2_DESIGN_ONLY_RISK_PRE_REGISTRATION
execution_authorized=false
ready_for_A2_execution=false
eligible_next_step=A2 design package completion gate review
```

The next permissible step is a completion review/gate of the A2 design package. That review may decide whether the design package is complete enough to support a future A2 execution-gate request. It must not execute A2.