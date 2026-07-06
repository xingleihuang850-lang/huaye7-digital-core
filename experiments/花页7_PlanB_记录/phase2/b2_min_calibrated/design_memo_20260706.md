# HY7 B2-min design memo — 2026-07-06

## Workflow node

- Node: `HY7-B2-min-design`
- Preceding gate: `HY7-B2-min-rock-gate-review`
- Gate verdict: `CONDITIONAL_PASS` for design-entry only
- Git evidence commit at gate: `04f652d docs: record B2-min rock gate review`
- Design status: `READY_FOR_DRY_RUN_DESIGN`, not execution/training

## Purpose

This memo defines the next B2-min design boundary after the rock gate judged that the calibrated B2-min baseline package and constrained selection smoke are sufficient to start design.

This is a **design-entry document**, not a training plan and not a B2-min result claim.

B2-min should answer only:

1. Can the frozen B1.1 conditional-pass candidate `ep015` be used as a calibrated, reproducible starting point for the next phase?
2. Can no-retraining candidate triage / packaging be made auditable without weakening full-batch gates?
3. What exact gates must be satisfied before any future B2 component can be promoted beyond dry-run/design?

## Frozen inputs

### Checkpoint and preprocessing

```text
main_checkpoint=ep015
required_calibration=hy7-gray-calibration-qmatch-v1
orig_raw_status=known_fail
execution_boundary=no new training / no retraining / no scaling / no new checkpoint
```

Only the explicit calibrated path is allowed for design-entry claims. Any downstream path must declare `hy7-gray-calibration-qmatch-v1` in its manifest, README, and report text.

### Remote ordered-view entry points

```text
hy7-linux:/home/user/HXL/HY7_planb/phase2/00_ORDERED_VIEW/05_b2_min_calibrated/00_baseline_package_ep015
hy7-linux:/home/user/HXL/HY7_planb/phase2/00_ORDERED_VIEW/05_b2_min_calibrated/01_constrained_selection_smoke_ep015
```

### Baseline package hash check

Already checked after rock gate:

```text
BASE_HASH_CHECK
b2_min_manifest.json: 成功
b2_min_readme.md: 成功
```

Tracked package hashes:

```text
27c2cf40476f78e69480ba364011bb86a394a01d99750c8cc3037ec4d04439df  b2_min_manifest.json
6458295a689dbcfc193a3f1774d690ccc6aba0840bee3a232527beb785bff7ae  b2_min_readme.md
658f3ff9f392c609b04b88f53479524a31709d79d14c5591961f624b9921634c  hashes.txt
```

## Full-batch anchor: the only acceptance anchor for B2-min design

B2-min thresholds and acceptance language must be anchored on **full-batch evidence**, not on the selected 64-slice chunk.

Full-batch constrained-selection control:

```text
variant=ep015_all
n=512
phi=6.442654132843018
S2 rmse=0.0002854642510439182
Euler=121.26953125
maxCC=0.06397858477862998
pass_gate=True
```

Formal512 B1.1 reference:

```text
formal512 ep015@phi6.4
S2 rmse=0.00034034164909631633
Euler=120.810546875
maxCC=0.06408827658203413
passed_gate=True
```

nnUNet qmatch reference:

```text
nnUNet ep015_qmatch
phi=5.794930458068848
S2 rmse=0.0017214588891168259
Euler=116.154296875
maxCC=0.06510709034871634
reverse_fail=False
```

Held-out qmatch split reference:

```text
ep015_qmatch_even: pass=True, Euler=116.13671875
ep015_qmatch_odd:  pass=True, Euler=116.16796875
```

## Formal-vs-qmatch metric difference to carry forward

The rock gate explicitly required this to be visible in the design memo.

There is a systematic metric difference between the direct formal threshold route and the nnUNet qmatch route:

```text
formal512 ep015@phi6.4: phi=6.4, Euler=120.81, maxCC=0.0641
nnUNet ep015_qmatch:    phi≈5.79, Euler≈116.15, maxCC=0.0651
```

Interpretation:

- `reverse_fail=False` and qmatch even/odd stability support the calibrated path.
- The difference does **not** invalidate B2-min design-entry.
- The difference must be treated as a downstream sensitivity/risk item. If a future B2 component is sensitive to absolute φ/Euler, the component must pre-register its tolerance range and decide whether it uses threshold-formal or nnUNet-qmatch as the operational route.
- No future report may collapse these two routes into one unlabeled metric.

## Constrained selection smoke: triage only

Selected row:

```text
variant=ep015_chunk384_447
n=64
phi=6.462860107421875
S2 rmse=0.0002106706336130071
Euler=121.171875
maxCC=0.06431804952279352
pass_gate=True
selection_reason=passed_gate_min_score
```

This row is useful for triage / candidate inspection only. It must not be used as the model-wide acceptance anchor.

Known failed row from the same smoke:

```text
variant=ep015_chunk000_063
n=64
phi=6.435489654541016
S2 rmse=0.0005247734726096197
Euler=123.953125
maxCC=0.07163110510281959
failed=maxCC>0.070
```

Interpretation:

- The one failed row proves the selection step is not silently dropping negative evidence.
- Failure is narrow and caused by `maxCC>0.070` despite acceptable S₂/Euler/φ.
- For B2-min design, all selected/rejected candidates must remain visible.

## Design-entry gates

A future B2-min dry-run / component design can proceed only if all of the following remain true:

1. `main_checkpoint=ep015`.
2. `calibration_version=hy7-gray-calibration-qmatch-v1` is explicit in every manifest/report.
3. No new training, no 100/200ep scaling, no new checkpoint.
4. Full-batch `ep015_all` remains the acceptance anchor.
5. Selected chunks are labeled `triage_only`.
6. ORIG raw remains `known_fail` and appears only as negative control / risk documentation.
7. Gates are not relaxed after seeing outputs.
8. Formal route and nnUNet-qmatch route are labeled separately.

## Proposed B2-min design components

### Component A — Frozen calibrated baseline reference

Objective: make `ep015 + qmatch-v1` a frozen reference bundle for all subsequent B2 work.

Allowed work:

- Add a schema/checklist for the existing package.
- Verify package hashes and ordered-view links.
- Record commit id and script hashes in a follow-up manifest version if needed.

Not allowed:

- Editing the existing hash-locked package in place.
- Replacing `ep015`.
- Recomputing metrics with changed gates.

Exit criteria:

```text
manifest schema valid
hashes verify
ordered-view links resolve
qmatch explicit
ORIG raw known_fail visible
```

### Component B — No-retraining calibrated candidate triage

Objective: use the existing selection script as candidate triage without turning it into a result gate.

Allowed work:

- Re-render selection reports from existing artifacts.
- Add deterministic tie-break documentation.
- Add a rejected-row table.
- Add full-batch row as mandatory control.

Not allowed:

- Treating selected 64-slice chunks as acceptance evidence.
- Using selected chunk metrics to set thresholds.
- Resampling until a better chunk appears.

Exit criteria:

```text
all rows visible
failed rows have failure reasons
selected row labeled triage_only
full-batch row labeled acceptance_anchor
```

### Component C — Next B2 component experiment card, dry-run only

Objective: draft the first actual B2 component as an experiment card without launching it.

Allowed content:

- Component hypothesis.
- Inputs from frozen baseline package.
- Calibration route.
- Formal and nnUNet-qmatch gates.
- Failure conditions.
- Promotion gate requirements.

Recommended first B2 component direction:

```text
calibrated pore-mask / gray-pore handoff bundle for downstream multiscale 3D fusion
```

Reason:

- It is still no-retraining and artifact/manifest based.
- It prepares the transition toward multiscale 3D digital core without introducing a new generative model.
- It keeps the current risk focus on calibrated inference, not new model capacity.

Explicitly not authorized yet:

```text
[sus,pore] joint generation training
conditioned B2 model training
100/200ep scaling
new topology rescue
```

## Acceptance thresholds for future dry-run reports

Future dry-run reports must separate two levels.

### Design-entry consistency threshold

This is for checking that future no-retraining reports did not break the frozen baseline:

```text
full_batch_required=True
S2 rmse <= 0.003
Euler >= 115
maxCC <= 0.070
phi in [5.8, 6.8] for threshold route
reverse_fail=False for nnUNet-qmatch route
```

### Promotion threshold

Promotion beyond dry-run/design requires a new gate. Minimum requirements:

```text
full-batch formal route passes
nnUNet-qmatch route passes
all rejected/failed candidates reported
formal-vs-qmatch metric differences explained
rock gate or equivalent multi-expert review repeated
no hidden retraining/no hidden qmatch
```

This memo does not grant promotion.

## Forbidden claims

Do not write:

- “B1.1 unconditionally passed.”
- “ORIG raw passed.”
- “B2-min passed.”
- “Selected chunk represents full model performance.”
- “qmatch is optional.”
- “Scaling/new training is now approved.”

Allowed wording:

- “B1.1 is a conditional pass under explicit qmatch/gray calibration.”
- “B2-min design-entry is `CONDITIONAL_PASS`.”
- “The frozen `ep015 + qmatch-v1` baseline is sufficient for no-retraining B2-min design.”
- “Selected chunks are triage-only; full-batch `ep015_all` anchors acceptance.”

## Immediate next steps

1. Add or update a lightweight design-audit checklist covering:
   - manifest schema,
   - qmatch explicitness,
   - forbidden claims,
   - full-batch anchor presence,
   - selected chunk triage-only wording,
   - rejected-row visibility.
2. Draft Component C experiment card for `calibrated pore-mask / gray-pore handoff bundle`.
3. Do not launch remote training or new sampling before that design card is reviewed.

## Done criteria for this design memo

This memo is complete when:

- It records the rock gate `CONDITIONAL_PASS` boundary.
- It names `ep015` and `hy7-gray-calibration-qmatch-v1` as hard dependencies.
- It anchors thresholds on full-batch `ep015_all`.
- It records the failed selection row.
- It records formal-vs-qmatch metric differences.
- It forbids new training/scaling/rescue.
