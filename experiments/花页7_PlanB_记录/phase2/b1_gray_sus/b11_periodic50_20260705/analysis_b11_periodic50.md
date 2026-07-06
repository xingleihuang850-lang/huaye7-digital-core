# B1.1 periodic50 checkpoint selection analysis

Remote dir: `/home/user/HXL/HY7_planb/phase2/ddpm_ct28_gray_b11_periodic50_20260705`
Local evidence dir: `/Users/hxl/Documents/Hermes工作区/01_Claude接管剩余工作/claude/experiments/花页7_PlanB_记录/phase2/b1_gray_sus/b11_periodic50_20260705`
Validation files: 5

## train_meta
- size: 128
- n_train: 16600
- epochs: 50
- base: 64
- bs: 64
- lr: 0.0001
- seed: 42
- sample_mode: gray
- best_Lsimple: 0.04459
- params_M: 63.15

Loss: first=0.0865, last=0.0457, best=0.0446 @ ep35

## checkpoint table
| epoch | pass | score | phi | S2 rmse | Euler | maxCC | gray mean | gray std | gray KS | selected phi | failed | file |
|---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 10 | False | 101.1711 | 6.000 | 0.00488 | 80.25 | 0.0052 | -0.1351 | 0.4440 | 0.1055 | 6.00 | ['euler'] | validation_ep010.json |
| 20 | False | 105.4390 | 6.000 | 0.01226 | 67.12 | 0.0194 | 0.3097 | 0.4862 | 0.4473 | 6.00 | ['euler'] | validation_ep020.json |
| 30 | False | 102.3396 | 6.000 | 0.00711 | 76.94 | 0.0090 | -0.1544 | 0.4334 | 0.1098 | 6.00 | ['euler'] | validation_ep030.json |
| 40 | True | 0.8802 | 6.000 | 0.00191 | 108.12 | 0.0061 | -0.1598 | 0.4075 | 0.0973 | 6.00 | [] | validation_ep040.json |
| 50 | True | 0.2527 | 6.400 | 0.00123 | 122.50 | 0.0038 | 0.1081 | 0.4304 | 0.2415 | 6.40 | [] | validation_ep050.json |

## selected best_by_gate_score
```json
{
  "file": "validation_ep050.json",
  "epoch": 50,
  "checkpoint": "ckpt_ep050.pt",
  "porosity_target": 6.4,
  "threshold": -0.5293521881103516,
  "score": 0.2527432766689729,
  "passed_gate": true,
  "failed_gates": [],
  "phi": 6.400299072265625,
  "s2_rmse": 0.0012348366435617208,
  "euler": 122.5,
  "maxcc": 0.00379180908203125,
  "gray_mean": 0.1081250011920929,
  "gray_std": 0.4303878843784332,
  "gray_ks": 0.24154327944100618,
  "gray_min": -1.0,
  "gray_max": 1.0
}
```

## train.log tail
```text
[ep  17] L_simple=0.0450  76.3s
[ep  18] L_simple=0.0468  76.4s
[ep  19] L_simple=0.0475  76.5s
[ep  20] L_simple=0.0459  76.4s
[eval ep  20] selected=6.000% score=105.4390 pass=False -> /home/user/HXL/HY7_planb/phase2/ddpm_ct28_gray_b11_periodic50_20260705/validation_ep020.json
[ep  21] L_simple=0.0461  76.3s
[ep  22] L_simple=0.0462  76.3s
[ep  23] L_simple=0.0467  76.4s
[ep  24] L_simple=0.0459  76.5s
[ep  25] L_simple=0.0473  76.4s
[ep  26] L_simple=0.0465  76.4s
[ep  27] L_simple=0.0467  76.4s
[ep  28] L_simple=0.0463  76.4s
[ep  29] L_simple=0.0462  76.4s
[ep  30] L_simple=0.0465  76.5s
[eval ep  30] selected=6.000% score=102.3396 pass=False -> /home/user/HXL/HY7_planb/phase2/ddpm_ct28_gray_b11_periodic50_20260705/validation_ep030.json
[ep  31] L_simple=0.0458  76.3s
[ep  32] L_simple=0.0465  76.4s
[ep  33] L_simple=0.0470  76.4s
[ep  34] L_simple=0.0453  76.4s
[ep  35] L_simple=0.0446  76.4s
[ep  36] L_simple=0.0460  76.5s
[ep  37] L_simple=0.0468  76.4s
[ep  38] L_simple=0.0462  76.4s
[ep  39] L_simple=0.0468  76.4s
[ep  40] L_simple=0.0471  76.5s
[eval ep  40] selected=6.000% score=0.8802 pass=True -> /home/user/HXL/HY7_planb/phase2/ddpm_ct28_gray_b11_periodic50_20260705/validation_ep040.json
[ep  41] L_simple=0.0466  76.5s
[ep  42] L_simple=0.0462  76.4s
[ep  43] L_simple=0.0456  76.4s
[ep  44] L_simple=0.0467  76.4s
[ep  45] L_simple=0.0461  76.4s
[ep  46] L_simple=0.0454  76.4s
[ep  47] L_simple=0.0457  76.5s
[ep  48] L_simple=0.0454  76.5s
[ep  49] L_simple=0.0464  76.4s
[ep  50] L_simple=0.0457  76.4s
[eval ep  50] selected=6.400% score=0.2527 pass=True -> /home/user/HXL/HY7_planb/phase2/ddpm_ct28_gray_b11_periodic50_20260705/validation_ep050.json
[done] best L_simple=0.0446 -> /home/user/HXL/HY7_planb/phase2/ddpm_ct28_gray_b11_periodic50_20260705
END 2026-07-05T01:34:25+08:00
```