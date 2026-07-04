# B1.1 output calibration probe

Purpose: run the B1.1 sampling/output calibration supplement requested after P0. This is not a new 50ep training run; it tests whether train-split moment calibration and best-vs-final checkpoint choice explain the generated-gray domain shift and nnUNet behavior.

Remote source:

```text
hy7-linux:/home/user/HXL/HY7_planb/phase2/b1_gray_sus_b11_output_calib_20260703/
```

Code sync:

```text
local commit: ff6c1bc
src/hy7_phase2_ddpm.py sha256: bfb1bd3d28303be06e6f38c6dc6fe1709321254ac380d6d5a3801f2d06a7d51b
```

## Variants

| variant | checkpoint | output calibration |
|---|---|---|
| `best_none` | `best.pt` | none |
| `best_train_moments` | `best.pt` | affine match generated mean/std to train.npy mean/std |
| `final_none` | `final.pt` | none |
| `final_train_moments` | `final.pt` | affine match generated mean/std to train.npy mean/std |

The calibration uses only `train.npy` moments, not test gray distribution. It is an explicit post-sampling calibration and must not be reported as pure generation quality.

## Gray sample statistics

| variant | mean | std | p6.4 | mean shift vs train | mean shift vs test512 |
|---|---:|---:|---:|---:|---:|
| best_none | -0.4319 | 0.3733 | -0.9749 | -0.3393 | -0.3330 |
| best_train_moments | -0.0947 | 0.3670 | -0.6365 | -0.0021 | 0.0042 |
| final_none | -0.1344 | 0.4738 | -0.8511 | -0.0418 | -0.0355 |
| final_train_moments | -0.0926 | 0.3739 | -0.6582 | ~0.0000 | 0.0063 |

Key finding: the final checkpoint naturally has much smaller mean shift than the best-loss checkpoint, but its distribution is higher-contrast/wider. Train-moments calibration fixes one-dimensional moments but does not guarantee nnUNet/topology improvement.

## nnUNetv2-2d downstream

| variant | φ gen | S₂ rmse | Euler gen | maxCC gen |
|---|---:|---:|---:|---:|
| best_none | 20.649% | 0.05097 | 150.65 | 0.0804 |
| best_train_moments | 3.777% | 0.00584 | 115.14 | 0.1003 |
| final_none | 10.989% | 0.01808 | 124.52 | 0.0680 |
| final_train_moments | 5.601% | 0.00220 | 91.21 | 0.0823 |

Reference real values from the same protocol: φ=6.405%, Euler=127.33, maxCC=0.0597.

## Interpretation

1. `best.pt` is bad for raw nnUNet because of strong dark shift. Train-moments calibration fixes mean/std but over-corrects segmentation behavior: φ becomes too low and maxCC worsens.
2. `final.pt` without calibration has much better topology (`Euler=124.52`, `maxCC=0.0680`) than best-loss raw, but porosity and S₂ are poor (`φ=10.989%`, `S₂=0.01808`). This suggests L_simple-best is not aligned with downstream digital-rock metrics.
3. `final_train_moments` gets φ close to real and S₂ near the acceptance edge (`0.00220`) but collapses Euler (`91.21`) and leaves maxCC high (`0.0823`). Moment calibration alone is insufficient and can damage topology.

## Decision implication

Do not use train-moments calibration as the B1.1 solution. The important finding is model-selection related: final checkpoint carries better connectivity/maxCC than best-loss checkpoint, while best-loss checkpoint carries better threshold S₂ after qmatch/φ matching. B1.1 should therefore add metric-aware checkpoint selection and/or validation sampling during training, not just post-hoc intensity calibration.

Recommended next B1.1 change:

- During cheap training, save periodic checkpoints (not only best/final) and evaluate a small validation sample every 10 epochs with gray stats + threshold S₂/Euler/maxCC + optional nnUNet proxy.
- Select checkpoint by a multi-objective score, not `L_simple` alone.
- If training objective is changed, keep this metric-aware checkpoint selection as the evaluation gate.
