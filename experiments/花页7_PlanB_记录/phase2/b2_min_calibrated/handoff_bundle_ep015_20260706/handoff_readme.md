# HY7 B2-min calibrated handoff dry-run bundle

Status: `calibrated_b2_min_handoff_design_dry_run`

B2-min design-entry gate = CONDITIONAL_PASS.

Main checkpoint: `ep015`

Required calibration: `hy7-gray-calibration-qmatch-v1`

ORIG raw status: `known_fail` / known_fail.

Execution boundary: `no_retraining_no_new_sampling_no_scaling_no_new_checkpoint` / no new training.

Acceptance anchor: `ep015_all`.

Selected chunk policy: `triage_only`.

## Formal route

formal512 ep015@phi6.4 and full-batch `ep015_all` are the threshold-formal route.

Full-batch `ep015_all`:

```json
{
  "variant": "ep015_all",
  "start": 0,
  "stop": 512,
  "n": 512,
  "phi_target": 6.4,
  "threshold": -0.625,
  "phi": 6.442654132843018,
  "s2_rmse": 0.0002854642510439182,
  "euler": 121.26953125,
  "maxcc": 0.06397858477862998,
  "x_penetrate": 0.0,
  "y_penetrate": 0.0,
  "pass_gate": true
}
```

## nnUNet-qmatch route

nnUNet ep015_qmatch is a calibrated diagnostic route and remains numerically distinct from the formal route.

```json
{
  "phi": 5.794930458068848,
  "s2_rmse": 0.0017214588891168259,
  "euler": 116.154296875,
  "maxcc": 0.06510709034871634,
  "reverse_fail": false
}
```

## Candidate rows

Selected chunk `ep015_chunk384_447` is triage_only. It is not the acceptance anchor.

Failed/rejected rows remain visible in `candidate_rows.json`; notably `ep015_chunk000_063` failed because maxCC>0.070.

## Forbidden claims / do not write

- B1.1 unconditional pass
- ORIG raw passed
- qmatch optional
- selected chunk represents full model performance
- B2-min passed
- 100/200ep scaling approved
- new training approved
