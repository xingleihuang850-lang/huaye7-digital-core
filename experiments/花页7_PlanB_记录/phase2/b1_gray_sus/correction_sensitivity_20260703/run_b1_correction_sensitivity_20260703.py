import json, subprocess, sys
from pathlib import Path
import numpy as np
import SimpleITK as sitk
from scipy.stats import ks_2samp, wasserstein_distance
from scipy.interpolate import interp1d
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path('/home/user/HXL/HY7_planb')
BASE = ROOT / 'phase2/ddpm_ct28_gray'
DATA = ROOT / 'phase2/slices_ct28_gray_128'
OUT = ROOT / 'phase2/b1_gray_sus_correction_sensitivity_20260703'
OUT.mkdir(parents=True, exist_ok=True)
(BASE / 'nnunet_corrected_in').mkdir(parents=True, exist_ok=True)
(BASE / 'nnunet_corrected_pred').mkdir(parents=True, exist_ok=True)

GEN = np.load(BASE / 'samples_gray.npy')
REAL = np.load(DATA / 'test.npy')[:len(GEN)]
REAL_PORE = str(DATA / 'test_pore.npy')
PHIS = [5.0, 5.5, 6.0, 6.4, 7.0, 7.5, 8.0]


def affine_match(gen, real):
    gm, gs = float(gen.mean()), float(gen.std())
    rm, rs = float(real.mean()), float(real.std())
    out = (gen - gm) / max(gs, 1e-6) * rs + rm
    return np.clip(out, -1, 1).astype(np.float32), {'gen_mean': gm, 'gen_std': gs, 'real_mean': rm, 'real_std': rs}


def quantile_match(gen, real, n=2048):
    qs = np.linspace(0, 100, n)
    gq = np.percentile(gen.ravel(), qs)
    rq = np.percentile(real.ravel(), qs)
    x, idx = np.unique(gq, return_index=True)
    y = rq[idx]
    f = interp1d(x, y, bounds_error=False, fill_value=(float(rq[0]), float(rq[-1])))
    out = f(gen).astype(np.float32)
    return np.clip(out, -1, 1), {'quantiles': n}


def summarize_gray(name, arr):
    flat = arr.ravel()
    rng = np.random.default_rng(0)
    n = min(1000000, len(flat), REAL.size)
    idxa = rng.choice(len(flat), n, replace=False)
    idxr = rng.choice(REAL.size, n, replace=False)
    ks = ks_2samp(REAL.ravel()[idxr], flat[idxa])
    return {
        'name': name,
        'shape': list(arr.shape),
        'mean': float(flat.mean()),
        'std': float(flat.std()),
        'min': float(flat.min()),
        'max': float(flat.max()),
        'p': {str(q): float(np.percentile(flat, q)) for q in [0, 0.5, 1, 5, 6.4, 25, 50, 75, 95, 99, 99.5, 100]},
        'vs_real': {
            'ks_stat_subsample_1e6': float(ks.statistic),
            'ks_p': float(ks.pvalue),
            'wasserstein_all': float(wasserstein_distance(REAL.ravel(), flat)),
            'mean_shift': float(flat.mean() - REAL.mean()),
        },
    }


def save_nifti(name, arr):
    raw = ((np.clip(arr, -1, 1) + 1.0) * 0.5 * (205 - 45) + 45).astype(np.float32)
    p = BASE / 'nnunet_corrected_in' / f'{name}_0000.nii.gz'
    img = sitk.GetImageFromArray(raw)
    img.SetSpacing((1.0, 1.0, 1.0))
    sitk.WriteImage(img, str(p))
    return str(p), {'raw_min': float(raw.min()), 'raw_max': float(raw.max()), 'raw_mean': float(raw.mean())}


variants = {'orig': GEN.astype(np.float32)}
aff, aff_meta = affine_match(GEN, REAL)
variants['affine'] = aff
qmt, q_meta = quantile_match(GEN, REAL)
variants['qmatch'] = qmt
for name, arr in variants.items():
    np.save(BASE / f'samples_gray_{name}.npy', arr)

report = {'real': summarize_gray('real', REAL), 'variants': {}, 'correction_meta': {'affine': aff_meta, 'qmatch': q_meta}}
for name, arr in variants.items():
    nifti, raw_meta = save_nifti(name.upper(), arr)
    report['variants'][name] = summarize_gray(name, arr)
    report['variants'][name]['nifti'] = nifti
    report['variants'][name]['raw_meta'] = raw_meta
json.dump(report, open(OUT / 'gray_correction_report.json', 'w'), indent=2)

fig, ax = plt.subplots(1, 3, figsize=(16, 4))
for name, arr in [('real', REAL), ('orig', variants['orig']), ('affine', variants['affine']), ('qmatch', variants['qmatch'])]:
    ax[0].hist(arr.ravel(), bins=120, density=True, alpha=0.45, label=name)
    ax[1].hist(arr.reshape(len(arr), -1).mean(1), bins=50, density=True, alpha=0.45, label=name)
    ax[2].hist(arr.reshape(len(arr), -1).std(1), bins=50, density=True, alpha=0.45, label=name)
ax[0].set_title('gray distribution')
ax[1].set_title('tile mean')
ax[2].set_title('tile std')
for a in ax:
    a.legend(fontsize=8)
plt.tight_layout()
plt.savefig(OUT / 'gray_correction_distribution.png', dpi=140)
plt.close()

sens = {}
for name, arr in variants.items():
    sens[name] = {}
    for phi in PHIS:
        tag = str(phi).replace('.', 'p')
        thr = float(np.percentile(arr.ravel(), phi))
        pore = (arr <= thr).astype(np.uint8)
        gen_path = OUT / f'{name}_threshold_phi{tag}.npy'
        np.save(gen_path, pore)
        eval_dir = OUT / f'eval_{name}_threshold_phi{tag}'
        subprocess.run([
            sys.executable, str(ROOT / 'src/hy7_phase2_eval.py'),
            '--real', REAL_PORE, '--gen', str(gen_path), '--out', str(eval_dir),
            '--n', '512', '--rmax', '48', '--seed', '0',
        ], check=True)
        metrics = json.load(open(eval_dir / 'metrics.json'))
        sens[name][str(phi)] = {'threshold_norm': thr, 'metrics': metrics}
json.dump(sens, open(OUT / 'threshold_sensitivity_summary.json', 'w'), indent=2)

with open(OUT / 'threshold_sensitivity_summary.csv', 'w') as f:
    f.write('variant,target_phi,threshold_norm,phi_real,phi_gen,S2_rmse,Euler_real,Euler_gen,maxCC_real,maxCC_gen\n')
    for name, byphi in sens.items():
        for phi, item in byphi.items():
            m = item['metrics']
            f.write(f"{name},{phi},{item['threshold_norm']},{m['porosity_pct']['real_mean']},{m['porosity_pct']['gen_mean']},{m['S2_radial']['rmse_gen']},{m['euler_chi']['real_mean']},{m['euler_chi']['gen_mean']},{m['connectivity']['max_cc_frac_real']},{m['connectivity']['max_cc_frac_gen']}\n")

print(json.dumps({'done': True, 'out': str(OUT), 'variants': list(variants)}, indent=2))
