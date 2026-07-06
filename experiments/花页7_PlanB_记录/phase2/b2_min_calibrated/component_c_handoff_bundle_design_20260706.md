# HY7 B2-min Component C design card — calibrated handoff bundle

## Workflow node

- Node: `HY7-B2-min-component-C-handoff-design`
- Parent memo: `design_memo_20260706.md`
- Status: `DESIGN_ONLY`
- Execution boundary: no retraining, no new sampling, no scaling, no new checkpoint.

## Component name

```text
calibrated pore-mask / gray-pore handoff bundle for downstream multiscale 3D fusion
```

## Purpose

Create a design for a future no-retraining handoff bundle that can carry the frozen B1.1 conditional-pass 2D candidate into the next multiscale 3D digital-core planning step without weakening the B2-min design-entry gate.

This card does **not** authorize a dry-run package yet. It defines what that package must contain if/when the user approves the dry-run.

## Scientific rationale

The next stage should not immediately introduce `[sus,pore]` joint generation, conditioned B2 training, or 100/200ep scaling. The current bottleneck is governance and calibrated handoff:

1. B1.1 is conditionally closed only under explicit qmatch / gray calibration.
2. ORIG raw remains known-fail.
3. The selected 64-slice chunk is useful for triage but cannot replace full-batch gates.
4. Stage-three multiscale 3D fusion will need a clear, versioned 2D-to-3D handoff object: calibrated gray samples, pore masks, formal metrics, qmatch manifest, and forbidden-claim constraints.

## Frozen inputs

### Required baseline evidence

```text
baseline_package=00_ORDERED_VIEW/05_b2_min_calibrated/00_baseline_package_ep015
selection_smoke=00_ORDERED_VIEW/05_b2_min_calibrated/01_constrained_selection_smoke_ep015
main_checkpoint=ep015
calibration_version=hy7-gray-calibration-qmatch-v1
orig_raw_status=known_fail
```

### Full-batch anchor

```text
variant=ep015_all
n=512
phi=6.442654132843018
S2 rmse=0.0002854642510439182
Euler=121.26953125
maxCC=0.06397858477862998
pass_gate=True
```

### nnUNet-qmatch reference

```text
variant=ep015_qmatch
phi=5.794930458068848
S2 rmse=0.0017214588891168259
Euler=116.154296875
maxCC=0.06510709034871634
reverse_fail=False
```

## Proposed dry-run output directory, if later approved

Remote output directory:

```text
/home/user/HXL/HY7_planb/phase2/b2_min_calibrated_handoff_bundle_ep015_20260706
```

Local evidence mirror, if lightweight files are pulled back:

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/handoff_bundle_ep015_20260706/
```

## Required dry-run package contents

If the dry-run is later approved, the bundle must contain at least:

```text
handoff_manifest.json
handoff_readme.md
formal_vs_qmatch_metrics.json
candidate_rows.json
forbidden_claims.txt
hashes.txt
```

Optional lightweight additions:

```text
audit_report.json
ordered_view_links.txt
```

Large arrays or model weights must not be committed to git. If referenced, they must be recorded by path + sha256 + size only.

## Required manifest fields

`handoff_manifest.json` must include:

```json
{
  "status": "calibrated_b2_min_handoff_design_dry_run",
  "main_checkpoint": "ep015",
  "calibration_version": "hy7-gray-calibration-qmatch-v1",
  "orig_raw_status": "known_fail",
  "execution_boundary": "no_retraining_no_new_sampling_no_scaling_no_new_checkpoint",
  "acceptance_anchor": "ep015_all",
  "selected_chunk_policy": "triage_only",
  "formal_route": "threshold_formal_full_batch",
  "nnunet_route": "qmatch_nnunet_diagnostic",
  "downstream_target": "multiscale_3d_digital_core_planning"
}
```

## Required metrics file

`formal_vs_qmatch_metrics.json` must keep the two routes separate:

```json
{
  "formal_full_batch_ep015_all": {
    "variant": "ep015_all",
    "n": 512,
    "phi": 6.442654132843018,
    "s2_rmse": 0.0002854642510439182,
    "euler": 121.26953125,
    "maxcc": 0.06397858477862998,
    "pass_gate": true
  },
  "formal512_ep015_phi64": {
    "phi_target": 6.4,
    "s2_rmse": 0.00034034164909631633,
    "euler": 120.810546875,
    "maxcc": 0.06408827658203413,
    "passed_gate": true
  },
  "nnunet_ep015_qmatch": {
    "phi": 5.794930458068848,
    "s2_rmse": 0.0017214588891168259,
    "euler": 116.154296875,
    "maxcc": 0.06510709034871634,
    "reverse_fail": false
  },
  "interpretation": "formal threshold and nnUNet-qmatch routes are both supportive but numerically distinct; do not merge them into one unlabeled metric."
}
```

## Candidate rows policy

`candidate_rows.json` must include all constrained-selection rows, including the failed row:

```text
failed row required:
variant=ep015_chunk000_063
failed=maxCC>0.070
phi=6.435489654541016
S2 rmse=0.0005247734726096197
Euler=123.953125
maxCC=0.07163110510281959
```

Selected row policy:

```text
variant=ep015_chunk384_447
policy=triage_only
not_acceptance_anchor=true
```

Full-batch policy:

```text
variant=ep015_all
policy=acceptance_anchor
required_for_promotion=true
```

## Forbidden claims file

`forbidden_claims.txt` must contain at least:

```text
B1.1 unconditional pass
ORIG raw passed
qmatch optional
selected chunk represents full model performance
B2-min passed
100/200ep scaling approved
new training approved
```

The handoff README should phrase these as prohibited claims, not as claims being made.

## Audit checklist

Before any dry-run bundle is considered complete, run the B2-min audit checklist:

```bash
python3 src/hy7_b2_min_audit.py \
  --manifest <handoff-or-baseline-manifest.json> \
  --selection-summary <selection_summary.json> \
  --design-text <handoff_readme_or_design_text.md>
```

Minimum expected result:

```json
{
  "passed": true,
  "errors": []
}
```

The audit must check:

- `main_checkpoint=ep015`.
- `calibration_version=hy7-gray-calibration-qmatch-v1`.
- `orig_raw_status=known_fail`.
- full-batch `ep015_all` present.
- failed/rejected row visible.
- selected chunk labeled `triage_only`.
- forbidden unsafe claims absent from positive wording.

## Promotion gate

This design card does not grant promotion. A future handoff dry-run can be promoted only after:

1. The dry-run bundle exists and passes the audit checklist.
2. Hashes are internally verified with `sha256sum -c hashes.txt` or equivalent.
3. The full-batch `ep015_all` remains the acceptance anchor.
4. Formal-vs-qmatch differences are stated in the README.
5. A follow-up gate confirms whether the bundle is sufficient for stage-three multiscale 3D digital-core planning.

## Explicit non-goals

Do not do any of the following under this Component C design card:

- run new DDPM training;
- run 100/200ep scaling;
- introduce a new checkpoint;
- run a second B1.1 topology rescue;
- start `[sus,pore]` joint generation;
- claim B2-min has passed as a result stage;
- claim ORIG raw passed;
- use selected chunk metrics as the acceptance threshold.

## Next decision

After this design card is reviewed, the next user decision is:

```text
Approve or defer the no-retraining handoff bundle dry-run package.
```

If approved, implement only a lightweight packaging dry-run around existing artifacts and run the audit checklist before any commit.
