# HY7 calibrated B2-min constrained selection smoke

Status: `calibrated_constrained_selection_smoke`
Calibration: `hy7-gray-calibration-qmatch-v1`

## Selected candidate

```json
{
  "variant": "ep015_chunk384_447",
  "start": 384,
  "stop": 448,
  "n": 64,
  "phi_target": 6.4,
  "threshold": -0.625,
  "phi": 6.462860107421875,
  "s2_rmse": 0.0002106706336130071,
  "euler": 121.171875,
  "maxcc": 0.06431804952279352,
  "x_penetrate": 0.0,
  "y_penetrate": 0.0,
  "pass_gate": true,
  "selection_reason": "passed_gate_min_score",
  "selection_score": [
    0,
    0.0002106706336130071,
    1.171875,
    0.06431804952279352,
    0.06286010742187464
  ]
}
```

## Candidate table

| variant | n | phi | S2 rmse | Euler | maxCC | pass |
|---|---:|---:|---:|---:|---:|:---:|
| ep015_chunk000_063 | 64 | 6.435 | 0.00052 | 123.95 | 0.0716 | False |
| ep015_chunk064_127 | 64 | 6.405 | 0.00033 | 122.09 | 0.0629 | True |
| ep015_chunk128_191 | 64 | 6.458 | 0.00071 | 121.00 | 0.0639 | True |
| ep015_chunk192_255 | 64 | 6.755 | 0.00111 | 120.81 | 0.0647 | True |
| ep015_chunk256_319 | 64 | 6.562 | 0.00179 | 123.59 | 0.0600 | True |
| ep015_chunk320_383 | 64 | 6.598 | 0.00073 | 121.97 | 0.0626 | True |
| ep015_chunk384_447 | 64 | 6.463 | 0.00021 | 121.17 | 0.0643 | True |
| ep015_chunk448_511 | 64 | 6.642 | 0.00059 | 123.61 | 0.0611 | True |
| ep015_all | 512 | 6.443 | 0.00029 | 121.27 | 0.0640 | True |

## Forbidden

- no_retraining
- no_second_b1_1_topology_rescue
- no_gate_relaxation
- orig_raw_pass_claim
- explicit_qmatch_required
