# B1 gray correction and threshold sensitivity

Purpose: follow the Fable5 review recommendation after B1 cheap50. This gate tests whether simple gray-domain correction fixes nnUNet over-segmentation and whether threshold-derived structure is stable across target φ.

Remote source directory:

```text
hy7-linux:/home/user/HXL/HY7_planb/phase2/b1_gray_sus_correction_sensitivity_20260703/
```

Large remote-only arrays:

```text
phase2/ddpm_ct28_gray/samples_gray_orig.npy
phase2/ddpm_ct28_gray/samples_gray_affine.npy
phase2/ddpm_ct28_gray/samples_gray_qmatch.npy
phase2/ddpm_ct28_gray/samples_pore_nnunet2d_{orig,affine,qmatch}.npy
```

Local evidence only includes JSON/CSV/PNG/log/hash files; `.npy` arrays remain remote-only.

## Gray-domain correction variants

| variant | operation |
|---|---|
| `orig` | original B1 cheap50 generated gray |
| `affine` | match generated global mean/std to real test gray, then clip to [-1,1] |
| `qmatch` | quantile/histogram match generated gray to real test gray, then clip to [-1,1] |

Gray distribution vs real:

| variant | mean | KS vs real | Wasserstein | p6.4 |
|---|---:|---:|---:|---:|
| orig | -0.4319 | 0.3979 | 0.3330 | -0.9749 |
| affine | -0.1003 | 0.0597 | 0.0278 | -0.6134 |
| qmatch | -0.1010 | 0.0170 | 0.0025 | -0.6125 |

Interpretation: qmatch essentially fixes the one-dimensional gray histogram mismatch; affine fixes mean/std but leaves more distributional mismatch.

## nnUNetv2-2d downstream after correction

| variant | φ gen | S₂ rmse | Euler gen | maxCC gen |
|---|---:|---:|---:|---:|
| orig | 20.649% | 0.05097 | 150.64 | 0.0804 |
| affine | 2.597% | 0.00802 | 95.67 | 0.0993 |
| qmatch | 5.711% | 0.00137 | 108.79 | 0.0824 |

Reference real values from the same eval protocol: φ=6.405%, Euler=127.33, maxCC=0.0597.

Interpretation: histogram/quantile matching strongly improves nnUNet downstream extraction (φ from 20.65% to 5.71%, S₂ rmse from 0.05097 to 0.00137). However Euler remains low and maxCC remains high; qmatch fixes intensity-domain mismatch, not the residual topology/cluster-size bias.

## Threshold sensitivity φ=5–8%

Summary for original generated gray:

| target φ | actual φ | S₂ rmse | Euler gen | maxCC gen |
|---:|---:|---:|---:|---:|
| 5.0 | 5.000 | 0.00287 | 114.37 | 0.0824 |
| 5.5 | 5.500 | 0.00175 | 113.26 | 0.0832 |
| 6.0 | 6.000 | 0.00083 | 111.86 | 0.0857 |
| 6.4 | 6.400 | 0.00105 | 111.00 | 0.0880 |
| 7.0 | 7.000 | 0.00249 | 110.38 | 0.0902 |
| 7.5 | 7.500 | 0.00390 | 110.73 | 0.0897 |
| 8.0 | 8.000 | 0.00542 | 111.43 | 0.0896 |

Because affine and quantile matching are monotonic transformations, threshold segmentation is mostly unchanged under matched target φ. The best S₂ point is near φ≈6.0, but Euler remains ~111–114 and maxCC stays ~0.082–0.090 across the full φ sweep.

## Decision read

1. Gray-domain mismatch is real and correctable: qmatch brings generated gray close to real histogram and makes nnUNet downstream nearly usable.
2. The residual B1 problem is structural/topological: maxCC stays too high and Euler stays too low across threshold sensitivity and after qmatch-nnUNet.
3. Do not switch to B2 yet, but do not run B1 200ep blindly either. The next B1 run should change the training objective/normalization pressure, not just train longer.

Recommended next gate:

- B1.1: add gray-distribution regularization / intensity calibration objective or train with better normalization diagnostics, then rerun cheap50.
- If keeping current model unchanged, run B1 200ep only as a controlled scaling check, with the expectation that it may improve texture but may not fix maxCC.
- B2 trigger remains: if B1.1/200ep cannot reduce maxCC toward <=0.07 while keeping S₂ and Euler stable, move to `[sus,pore]` joint generation.
