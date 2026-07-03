# B1 gray sus 50ep cheap run evidence

Remote run directory:

```text
hy7-linux:/home/user/HXL/HY7_planb/phase2/ddpm_ct28_gray/
```

Local commit/script sync:

```text
commit: a9b7196 feat(phase2): support B1 gray DDPM training
src/hy7_phase2_ddpm.py sha256: d908df602af6af5132a56834bee57932cf29d936e25d22f426701ac23ba71d12
```

## Training

Command is archived at `remote_run/run_b1_train_50ep_20260703.sh`.

Key config from `train_meta.json`:

```text
n_train=16600
size=128
epochs=50
bs=64
base=64
lr=1e-4
seed=42
sample_mode=gray
best_Lsimple=0.04448
params_M=63.15
```

Large remote artifacts, not in git:

```text
best.pt
final.pt
samples_gray.npy
samples_continuous.npy
samples_pore_threshold_phi64.npy
samples_pore_nnunet2d.npy
```

Hashes are recorded in:

```text
remote_run/b1_cheap50_hashes_20260703.txt
remote_run/b1_nnunet2d_hashes_20260703.txt
```

## Sampling

512 gray samples were generated with `--sample-mode gray --continuous`.

```text
samples_gray.npy: float32 [-1,1], n=512
samples_continuous.npy: same continuous output archive
samples_grid.png: lightweight visual evidence
```

Sample gray summary from `threshold_phi64_meta.json`:

```text
gray_min=-1.0
gray_max=1.0
gray_mean=-0.4318853617
```

## Downstream pore extraction and metrics

Two first-pass downstream pore extraction routes were run.

| route | φ real | φ gen | S₂ rmse | Euler real | Euler gen | maxCC real | maxCC gen | read |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| B1-threshold φ=6.4 | 6.405% | 6.400% | 0.00105 | 127.33 | 111.00 | 0.0597 | 0.0880 | strong S₂; Euler close-ish but maxCC high |
| B1-nnUNetv2-2d | 6.405% | 20.649% | 0.05097 | 127.33 | 150.65 | 0.0597 | 0.0804 | over-segments generated gray; not acceptable as-is |

Threshold route:

```text
threshold_norm=-0.9749291539
target_phi_pct=6.4
phi_pct_mean=6.4000249
```

nnUNet route:

```text
trainer=nnUNetTrainer_50epochs__nnUNetPlans__2d fold_0 checkpoint_best
input conversion: raw=(clip(gray,-1,1)+1)/2*(205-45)+45
output unique labels=[0,1]
phi_pct_mean=20.6486464
```

## Interpretation

B1 50ep is a meaningful improvement over binary M7-v2/v3 under the calibrated threshold proxy:

- S₂ rmse improves to 0.00105, better than M7-v2 T* 0.00242 and M7-v3 200ep T=0 0.00372.
- Euler is 111.0 vs real 127.33, closer than M7-v2 T* 207.92 and not a trivial naive-spray pattern.
- maxCC is 0.0880 vs real 0.0597, so generated pore clusters are still too connected/large.

The nnUNet downstream route currently over-segments generated gray (φ≈20.65%). Treat this as a domain-shift warning, not as final B1 failure: generated gray intensity distribution differs enough that the E3 nnUNetv2 segmenter is not calibrated for it without an adapter/reference-real control.

## Next decisions

1. Do not jump to B2 yet. B1-threshold is already better than the binary DDPM line on S₂/Euler.
2. Add a B1-reference-real control: apply the same inverse-normalization/nnUNet pipeline to real test gray slices to separate model failure from nnUNet domain shift.
3. Inspect gray histogram/texture versus real test gray before deciding whether to run B1 200ep or improve normalization/loss.
4. If B1 remains promising after reference-real control, consider 200ep B1; if pore extraction remains unstable, then design B2 `[sus,pore]`.
