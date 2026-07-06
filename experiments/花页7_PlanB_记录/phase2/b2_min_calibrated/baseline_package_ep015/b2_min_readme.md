# HY7 Calibrated B2-min Baseline Package

Status: `calibrated_b2_min_candidate`

Main checkpoint: `ep015`

Required calibration: `hy7-gray-calibration-qmatch-v1`

ORIG raw status: `known_fail`

## Evidence summary

Formal512 ep015@φ6.4:

```json
{
  "s2_rmse": 0.00034034164909631633,
  "euler": 120.810546875,
  "maxcc": 0.06408827658203413,
  "passed_gate": true
}
```

nnUNet ep015_qmatch:

```json
{
  "phi": 5.794930458068848,
  "s2_rmse": 0.0017214588891168259,
  "euler": 116.154296875,
  "maxcc": 0.06510709034871634,
  "reverse_fail": false
}
```

qmatch generalization ep015:

```json
{
  "even_pass": true,
  "odd_pass": true,
  "even_euler": 116.13671875,
  "odd_euler": 116.16796875
}
```

## Forbidden

- unconditional_b1_1_pass_claim
- orig_raw_pass_claim
- second_b1_1_topology_rescue
- gate_relaxation
- implicit_qmatch
