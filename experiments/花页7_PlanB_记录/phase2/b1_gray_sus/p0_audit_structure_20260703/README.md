# B1.1 P0 normalization audit and gray structure diagnostics

## Key normalization facts

- train mean/std: -0.092578 / 0.373912
- test512 mean/std: -0.098893 / 0.353681
- generated orig mean/std: -0.431885 / 0.373314
- generated - train mean: -0.339308
- generated - test512 mean: -0.332993
- generated minus1 saturation: 0.025450

## Loader checks

```json
{
  "load_train_array_shape": [
    16600,
    1,
    128,
    128
  ],
  "load_train_array_dtype": "torch.float32",
  "load_train_array_min": -1.0,
  "load_train_array_max": 1.0,
  "load_train_array_mean": -0.09257781505584717,
  "postprocess_gray_identity": true
}
```

## Structure diagnostics

See `gray_structure_diagnostics.json` and `gray_structure_diagnostics.png` for FFT radial power and gray autocorrelation.

- generated qmatch mean/std: -0.101044 / 0.358748
