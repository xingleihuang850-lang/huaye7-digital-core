# B1 gray sus controls after Fable5 review

Purpose: resolve the contradiction between B1-threshold success and B1-nnUNet over-segmentation.

## Control 1 — B1-reference-real nnUNet

Real `slices_ct28_gray_128/test.npy` first 512 slices were sent through the same inverse-normalization + NIfTI + nnUNetv2 2d 50ep pipeline used for generated gray.

Result:

```text
φ real/reference = 6.405% / 5.689%
S₂ rmse = 0.00187
Euler real/reference = 127.33 / 121.08
maxCC real/reference = 0.0597 / 0.0559
```

Interpretation: the nnUNet downstream pipeline is basically valid on real gray. Therefore generated-gray nnUNet φ=20.649% is not a generic pipeline bug; it is generated gray domain shift / intensity-distribution mismatch.

## Control 2 — real-gray-threshold method upper bound

Real test gray was thresholded with the same percentile-style pore extraction.

Result:

```text
threshold_norm = -0.6125000119
φ real/reference = 6.405% / 6.742%
S₂ rmse = 0.00071
Euler real/reference = 127.33 / 130.28
maxCC real/reference = 0.0597 / 0.0559
```

Interpretation: percentile thresholding is a strong method on real gray. B1-threshold maxCC=0.0880 is therefore a generated-structure issue, not just a threshold-method artifact.

## Control 3 — generated vs real gray distribution

Generated gray is substantially darker / shifted relative to real test gray:

```text
mean_shift_gen_minus_real = -0.3329927921
KS statistic ≈ 0.397856
Wasserstein distance ≈ 0.332993
real φ=6.4 threshold_norm = -0.6125
generated φ=6.4 threshold_norm = -0.9749291539
```

Interpretation: Fable5's suspicion was confirmed. The generated gray has learned useful spatial structure, but the absolute gray intensity distribution is not aligned to real CT. This explains nnUNet over-segmentation.

## Updated decision

Continue B1, do not switch to B2 yet.

Evidence now supports:

1. B1-threshold is structurally promising.
2. nnUNet over-segmentation is caused by generated gray distribution shift, not by the nnUNet pipeline itself.
3. real-gray-threshold shows the method upper bound is very strong, so B1's remaining maxCC bias is a real generation target.

Next recommended action:

1. Before B1 200ep, test simple gray-domain correction: histogram matching / affine mean-std alignment of generated gray to real test gray, then rerun nnUNet.
2. Run B1 200ep only if corrected-gray nnUNet improves or if threshold metrics remain the main evaluation route.
3. Add threshold sensitivity curve φ=5–8% for B1 cheap50 and future B1 200ep.
