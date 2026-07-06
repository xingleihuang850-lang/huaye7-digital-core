#!/usr/bin/env python
"""M7.2/7.3 阶段二：2D DDPM 生成 ct28 孔隙结构（diffusers 实现 = Ho2020）。

依据精读卡①(notes/02_文献综述.md)：ε-预测 L_simple、T=1000、β 线性 1e-4→0.02、
数据缩放 [-1,1]、U-Net backbone。DDPMScheduler 即 Ho2020 的前向/反向过程。

子命令：
  train  —— 训练 + 存 best/final + 末尾出样本网格 png
  sample —— 载模型生成 N 张二值孔隙图 → samples.npy（供 M7.3 参数评估）

运行环境：
  目前按 hy7-linux/5090 GPU 环境运行，需要 diffusers；2026-07-01 已核实
  远程 nnunet_t28 环境为 diffusers==0.38.0。本机未安装 diffusers 时仍允许
  查看 --help，但执行 train/sample 会提示安装或切换远程环境。
"""
import argparse, json, os, time
import numpy as np
try:
    import torch
    import torch.nn.functional as F
    from torch.utils.data import DataLoader, TensorDataset
except ModuleNotFoundError:
    class _NumpyTensor:
        """Tiny torch.Tensor stand-in for local pure-function tests without torch."""
        def __init__(self, arr):
            self._arr = np.asarray(arr, dtype=np.float32)
            self.shape = self._arr.shape
            self.dtype = self._arr.dtype

        def __getitem__(self, item):
            return _NumpyTensor(self._arr[item])

        def __len__(self):
            return len(self._arr)

        def numpy(self):
            return self._arr

    class _TorchFallback:
        def no_grad(self):
            return lambda fn: fn

        def from_numpy(self, arr):
            return _NumpyTensor(arr)

        def __getattr__(self, name):
            raise ModuleNotFoundError(
                "src/hy7_phase2_ddpm.py train/sample requires torch; pure data/calibration helpers remain importable"
            )

    def _missing_torch_ctor(*_args, **_kwargs):
        raise ModuleNotFoundError("DataLoader/TensorDataset require torch")

    torch = _TorchFallback()
    F = None
    DataLoader = _missing_torch_ctor
    TensorDataset = _missing_torch_ctor


def require_diffusers():
    """Import diffusers lazily so CLI --help works on lightweight local envs."""
    try:
        from diffusers import UNet2DModel, DDPMScheduler
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "src/hy7_phase2_ddpm.py train/sample requires diffusers. "
            "Use the verified remote nnunet_t28 environment (diffusers==0.38.0) "
            "or install a compatible local diffusers version before running."
        ) from e
    return UNet2DModel, DDPMScheduler


def build_model(size, base=64):
    UNet2DModel, _ = require_diffusers()
    return UNet2DModel(
        sample_size=size, in_channels=1, out_channels=1, layers_per_block=2,
        block_out_channels=(base, base * 2, base * 4, base * 8),
        down_block_types=("DownBlock2D", "DownBlock2D", "AttnDownBlock2D", "AttnDownBlock2D"),
        up_block_types=("AttnUpBlock2D", "AttnUpBlock2D", "UpBlock2D", "UpBlock2D"),
    )


def make_sched():
    _, DDPMScheduler = require_diffusers()
    return DDPMScheduler(num_train_timesteps=1000, beta_schedule="linear",
                         beta_start=1e-4, beta_end=0.02)


def load_train_array(npy):
    """Load DDPM train.npy as (N,1,H,W) float tensor in [-1,1].

    Supports both legacy binary pore masks stored as uint8 {0,1} and B1 gray
    sus slices already stored as float32 in [-1,1].
    """
    a = np.load(npy)                          # (N,H,W)
    if a.ndim != 3:
        raise ValueError(f"expected train.npy shape (N,H,W), got {a.shape}")
    if np.issubdtype(a.dtype, np.integer):
        vals = np.unique(a)
        if not set(vals.tolist()).issubset({0, 1}):
            raise ValueError(f"integer train.npy must be binary {{0,1}}, got values {vals[:10]}")
        arr = a.astype(np.float32) * 2.0 - 1.0
    elif np.issubdtype(a.dtype, np.floating):
        mn, mx = float(np.nanmin(a)), float(np.nanmax(a))
        if not np.isfinite(mn) or not np.isfinite(mx) or mn < -1.0001 or mx > 1.0001:
            raise ValueError(f"float train.npy must already be scaled to [-1,1], got min={mn}, max={mx}")
        arr = a.astype(np.float32, copy=False)
    else:
        raise ValueError(f"unsupported train.npy dtype: {a.dtype}")
    return torch.from_numpy(arr)[:, None]


# Backward-compatible name for M7 binary pore-mask runs.
def load_binary(npy):
    return load_train_array(npy)


def postprocess_samples(cont, mode="binary"):
    """Convert continuous DDPM output to the requested saved sample representation."""
    if mode == "binary":
        return (cont > 0).astype(np.uint8)
    if mode == "gray":
        return np.clip(cont, -1.0, 1.0).astype(np.float32)
    raise ValueError(f"unknown sample mode: {mode}")


def make_intensity_calibration(reference, mode="none"):
    """Build an affine output-intensity calibration from reference gray data.

    mode="train-moments" matches generated gray samples to the reference mean/std.
    This is an explicit post-sampling calibration for B1.1 diagnostics, not a pure
    generation-quality metric. It uses only the train split when called from CLI.
    """
    ref = np.asarray(reference, dtype=np.float32)
    if mode == "none":
        return {"mode": "none", "reference_mean": float(ref.mean()), "reference_std": float(ref.std())}
    if mode != "train-moments":
        raise ValueError(f"unknown intensity calibration mode: {mode}")
    std = float(ref.std())
    if not np.isfinite(std) or std <= 1e-8:
        raise ValueError("reference std must be finite and positive for train-moments calibration")
    return {"mode": mode, "reference_mean": float(ref.mean()), "reference_std": std}


def apply_intensity_calibration(samples, calibration):
    """Apply B1.1 output calibration to gray samples and keep [-1,1] semantics."""
    arr = np.asarray(samples, dtype=np.float32)
    mode = calibration.get("mode", "none")
    if mode == "none":
        return np.clip(arr, -1.0, 1.0).astype(np.float32)
    if mode != "train-moments":
        raise ValueError(f"unknown intensity calibration mode: {mode}")
    mean = float(arr.mean())
    std = float(arr.std())
    if not np.isfinite(std) or std <= 1e-8:
        raise ValueError("sample std must be finite and positive for train-moments calibration")
    out = (arr - mean) / std * float(calibration["reference_std"]) + float(calibration["reference_mean"])
    return np.clip(out, -1.0, 1.0).astype(np.float32)


def invert_intensity_calibration(samples, calibration):
    """Compatibility hook for future train-space transforms; current modes are output-only."""
    return np.asarray(samples, dtype=np.float32)


def _metric_abs_rel(value, target_value, fallback_scale=1.0):
    """Absolute error normalized by target magnitude, with a fixed fallback scale."""
    v = float(value)
    t = float(target_value)
    scale = abs(t) if abs(t) > 1e-12 else float(fallback_scale)
    return abs(v - t) / scale


def score_checkpoint_metrics(metrics, target, weights=None, gates=None):
    """Score one B1.1 checkpoint candidate against digital-rock proxy metrics.

    Lower score is better. Inputs are plain dictionaries so this can be used both
    in lightweight local tests and in remote GPU validation scripts. Default gates
    encode the current HY7 B1.1 risk boundary from notes/30: avoid over-connected
    samples (maxCC) and large Euler drift before treating a checkpoint as viable.
    """
    weights = dict(weights or {"phi": 1.0, "s2_rmse": 1.0, "euler": 1.0, "maxcc": 1.0})
    gates = dict(gates or {"maxcc_max": 0.070, "euler_rel_tol": 0.15})
    target = dict(target)
    metrics = dict(metrics)

    terms = {}
    terms["phi"] = _metric_abs_rel(metrics["phi"], target["phi"])
    terms["s2_rmse"] = _metric_abs_rel(metrics["s2_rmse"], target.get("s2_rmse", 0.0), fallback_scale=0.01)
    terms["euler"] = _metric_abs_rel(metrics["euler"], target["euler"])
    terms["maxcc"] = _metric_abs_rel(metrics["maxcc"], target["maxcc"])

    failed = []
    if "maxcc_max" in gates and float(metrics["maxcc"]) > float(gates["maxcc_max"]):
        failed.append("maxcc")
    if "euler_rel_tol" in gates and terms["euler"] > float(gates["euler_rel_tol"]):
        failed.append("euler")

    score = sum(float(weights.get(k, 0.0)) * v for k, v in terms.items())
    if failed:
        score += 100.0 * len(failed)
    out = dict(metrics)
    out.update({"terms": terms, "failed_gates": failed, "passed_gate": not failed, "score": float(score)})
    return out


def select_metric_aware_checkpoint(candidates, target, weights=None, gates=None):
    """Return the best B1.1 checkpoint by gated multi-objective metric score."""
    scored = [score_checkpoint_metrics(c, target=target, weights=weights, gates=gates) for c in candidates]
    if not scored:
        raise ValueError("at least one checkpoint candidate is required")
    best = min(scored, key=lambda x: (not x["passed_gate"], x["score"], str(x.get("name", ""))))
    best = dict(best)
    best["candidates"] = {str(c.get("name", i)): c for i, c in enumerate(scored)}
    return best


def _ks_2sample(a, b):
    a = np.sort(np.asarray(a, dtype=np.float32).ravel())
    b = np.sort(np.asarray(b, dtype=np.float32).ravel())
    if len(a) == 0 or len(b) == 0:
        raise ValueError("KS inputs must be non-empty")
    x = np.sort(np.concatenate([a, b]))
    ca = np.searchsorted(a, x, side="right") / len(a)
    cb = np.searchsorted(b, x, side="right") / len(b)
    return float(np.max(np.abs(ca - cb)))


def gray_validation_stats(generated, reference):
    """Gray-domain validation stats for periodic B1.1 checkpoint sampling."""
    g = np.asarray(generated, dtype=np.float32)
    r = np.asarray(reference, dtype=np.float32)
    if g.ndim != 3 or r.ndim != 3:
        raise ValueError("gray validation arrays must have shape (N,H,W)")
    return {
        "n": int(g.shape[0]),
        "mean": float(g.mean()),
        "std": float(g.std()),
        "min": float(g.min()),
        "max": float(g.max()),
        "ks": _ks_2sample(g, r),
    }


def threshold_for_porosity(gray, porosity_percent):
    """Return lower-tail gray threshold whose pore fraction approximates porosity_percent."""
    arr = np.asarray(gray, dtype=np.float32).ravel()
    if len(arr) == 0:
        raise ValueError("gray array must be non-empty")
    q = min(max(float(porosity_percent) / 100.0, 0.0), 1.0)
    idx = int(np.ceil(q * len(arr)) - 1)
    idx = min(max(idx, 0), len(arr) - 1)
    return float(np.partition(arr, idx)[idx])


def _component_sizes(mask, value=True):
    m = np.asarray(mask, dtype=bool) == bool(value)
    seen = np.zeros(m.shape, dtype=bool)
    sizes = []
    h, w = m.shape
    for y in range(h):
        for x in range(w):
            if seen[y, x] or not m[y, x]:
                continue
            stack = [(y, x)]; seen[y, x] = True; n = 0
            while stack:
                cy, cx = stack.pop(); n += 1
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and m[ny, nx]:
                        seen[ny, nx] = True; stack.append((ny, nx))
            sizes.append(n)
    return sizes


def _hole_count(mask):
    pore = np.asarray(mask, dtype=bool)
    bg = ~pore
    seen = np.zeros(bg.shape, dtype=bool)
    h, w = bg.shape
    holes = 0
    for y in range(h):
        for x in range(w):
            if seen[y, x] or not bg[y, x]:
                continue
            stack = [(y, x)]; seen[y, x] = True; touches_border = False
            while stack:
                cy, cx = stack.pop()
                touches_border |= cy in (0, h - 1) or cx in (0, w - 1)
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and bg[ny, nx]:
                        seen[ny, nx] = True; stack.append((ny, nx))
            holes += 0 if touches_border else 1
    return holes


def _two_point_curve(mask):
    m = np.asarray(mask, dtype=bool)
    max_lag = min(16, m.shape[-2] - 1, m.shape[-1] - 1)
    vals = []
    for lag in range(1, max_lag + 1):
        vals.append(float((m[:, :, :-lag] & m[:, :, lag:]).mean()))
        vals.append(float((m[:, :-lag, :] & m[:, lag:, :]).mean()))
    return np.asarray(vals, dtype=np.float32)


def binary_pore_metrics(generated, real):
    """Compute lightweight pore metrics: φ, S2 RMSE, Euler, max connected component.

    This is the historical fast proxy used by early B1.1 periodic validation. It is
    intentionally kept for cheap screening, but formal checkpoint selection should
    use ``formal_binary_pore_metrics`` because its S₂/connectivity semantics match
    ``src/hy7_phase2_eval.py``.
    """
    g = np.asarray(generated, dtype=bool)
    r = np.asarray(real, dtype=bool)
    if g.ndim == 2:
        g = g[None]
    if r.ndim == 2:
        r = r[None]
    if g.ndim != 3 or r.ndim != 3:
        raise ValueError("pore arrays must have shape (N,H,W) or (H,W)")
    eulers, maxccs = [], []
    for sl in g:
        sizes = _component_sizes(sl, True)
        eulers.append(float(len(sizes) - _hole_count(sl)))
        maxccs.append(float(max(sizes, default=0)) / sl.size)
    sg, sr = _two_point_curve(g), _two_point_curve(r)
    n = min(len(sg), len(sr))
    s2 = float(np.sqrt(np.mean((sg[:n] - sr[:n]) ** 2))) if n else 0.0
    return {"phi": float(g.mean() * 100.0), "s2_rmse": s2,
            "euler": float(np.mean(eulers)), "maxcc": float(np.mean(maxccs))}


def _formal_s2_radial(stack, rmax):
    stack = np.asarray(stack, dtype=bool)
    if stack.ndim == 2:
        stack = stack[None]
    n, h, w = stack.shape
    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.sqrt(np.minimum(yy, h - yy) ** 2 + np.minimum(xx, w - xx) ** 2)
    rbin = rr.astype(int)
    rmax = int(min(rmax, rbin.max()))
    s2_mean = np.zeros(rmax + 1, dtype=np.float64)
    mask = rbin <= rmax
    for i in range(n):
        f = np.fft.fft2(stack[i].astype(np.float64))
        ac = np.fft.ifft2(f * np.conj(f)).real / (h * w)
        acc = np.zeros(rmax + 1, dtype=np.float64)
        cnt = np.zeros(rmax + 1, dtype=np.float64)
        np.add.at(acc, rbin[mask], ac[mask])
        np.add.at(cnt, rbin[mask], 1)
        s2_mean += acc / np.maximum(cnt, 1)
    return s2_mean / max(n, 1)


def _formal_euler_numbers(stack):
    stack = np.asarray(stack, dtype=bool)
    if stack.ndim == 2:
        stack = stack[None]
    try:
        from skimage.measure import euler_number
        return np.asarray([euler_number(sl, connectivity=1) for sl in stack], dtype=np.float64)
    except ModuleNotFoundError:
        return np.asarray([len(_component_sizes(sl, True)) - _hole_count(sl) for sl in stack], dtype=np.float64)


def _formal_connectivity_stats(stack):
    stack = np.asarray(stack, dtype=bool)
    if stack.ndim == 2:
        stack = stack[None]
    try:
        from skimage.measure import label
        use_skimage = True
    except ModuleNotFoundError:
        label = None
        use_skimage = False
    frac, xpen, ypen = [], [], []
    for img in stack:
        if use_skimage:
            lbl = label(img, connectivity=1)
            if lbl.max() == 0:
                frac.append(np.nan); xpen.append(0.0); ypen.append(0.0); continue
            sizes = np.bincount(lbl.ravel()); sizes[0] = 0
            largest = int(np.argmax(sizes)); cc = (lbl == largest)
        else:
            sizes = _component_sizes(img, True)
            if not sizes:
                frac.append(np.nan); xpen.append(0.0); ypen.append(0.0); continue
            largest_size = max(sizes)
            # Fallback cannot recover labels cheaply; use aggregate size and no penetration.
            cc = None
        total_pore = int(img.sum())
        if use_skimage:
            frac.append(float(cc.sum()) / max(total_pore, 1))
            xpen.append(float(cc[:, 0].any() and cc[:, -1].any()))
            ypen.append(float(cc[0, :].any() and cc[-1, :].any()))
        else:
            frac.append(float(largest_size) / max(total_pore, 1))
            xpen.append(0.0); ypen.append(0.0)
    return {
        "maxcc": float(np.nanmean(np.asarray(frac, dtype=np.float64))),
        "x_penetrate": float(np.mean(xpen)),
        "y_penetrate": float(np.mean(ypen)),
    }


def formal_binary_pore_metrics(generated, real, rmax=48):
    """B1 cheap50-compatible pore metrics for formal periodic validation.

    Matches ``src/hy7_phase2_eval.py`` semantics: FFT radial S₂ with rmax,
    skimage Euler (connectivity=1), and max connected component divided by total
    pore pixels, not by total image pixels.
    """
    g = np.asarray(generated, dtype=bool)
    r = np.asarray(real, dtype=bool)
    if g.ndim == 2:
        g = g[None]
    if r.ndim == 2:
        r = r[None]
    if g.ndim != 3 or r.ndim != 3:
        raise ValueError("pore arrays must have shape (N,H,W) or (H,W)")
    s2g, s2r = _formal_s2_radial(g, rmax), _formal_s2_radial(r, rmax)
    n = min(len(s2g), len(s2r))
    conn = _formal_connectivity_stats(g)
    return {
        "phi": float(g.mean() * 100.0),
        "s2_rmse": float(np.sqrt(np.mean((s2g[:n] - s2r[:n]) ** 2))) if n else 0.0,
        "euler": float(_formal_euler_numbers(g).mean()),
        "maxcc": conn["maxcc"],
        "x_penetrate": conn["x_penetrate"],
        "y_penetrate": conn["y_penetrate"],
    }


def _score_threshold_candidates(gray, real, checkpoint, epoch, porosity_targets, metric_target,
                                weights, gates, metric_fn, proxy_name):
    candidates = []
    for por in porosity_targets:
        thr = threshold_for_porosity(gray, por)
        pore = gray <= thr
        metrics = metric_fn(pore, real)
        candidate = {
            **metrics,
            "name": f"{checkpoint}@phi{float(por):.3g}",
            "checkpoint": checkpoint,
            "epoch": int(epoch),
            "porosity_target": float(por),
            "threshold": thr,
            "proxy": proxy_name,
        }
        candidates.append(candidate)
    selected = select_metric_aware_checkpoint(candidates, target=metric_target, weights=weights, gates=gates)
    selected = {k: v for k, v in selected.items() if k != "candidates"}
    selected["proxy"] = proxy_name
    return candidates, selected, {str(c.get("name", i)): c for i, c in enumerate(
        [score_checkpoint_metrics(c, target=metric_target, weights=weights, gates=gates) for c in candidates]
    )}


def _selection_status(fast_selected, formal_selected):
    if not bool(formal_selected.get("passed_gate", False)):
        return "rejected"
    fast_phi = float(fast_selected.get("porosity_target", np.nan))
    formal_phi = float(formal_selected.get("porosity_target", np.nan))
    if np.isfinite(fast_phi) and np.isfinite(formal_phi) and abs(fast_phi - formal_phi) < 1e-9:
        return "accepted"
    return "needs_formal_resample"


def periodic_validation_summary(gray_samples, gray_reference, real_pore, checkpoint, epoch,
                                porosity_targets=(6.0, 6.4), metric_target=None,
                                weights=None, gates=None, formal_proxy=False,
                                formal_rmax=48, formal_metric_target=None):
    """Score one checkpoint's gray samples across pre-registered porosity thresholds.

    When ``formal_proxy`` is true, the returned top-level ``selected`` candidate is
    selected with B1 cheap50-compatible formal metrics, while the historical fast
    proxy remains under ``fast_proxy`` for disagreement diagnostics.
    """
    gray = np.asarray(gray_samples, dtype=np.float32)
    real = np.asarray(real_pore, dtype=bool)
    if metric_target is None:
        rm = binary_pore_metrics(real, real)
        metric_target = {"phi": rm["phi"], "s2_rmse": 0.0, "euler": rm["euler"], "maxcc": rm["maxcc"]}
    fast_candidates, fast_selected, fast_scored = _score_threshold_candidates(
        gray, real, checkpoint, epoch, porosity_targets, metric_target, weights, gates,
        binary_pore_metrics, "fast")
    summary = {
        "checkpoint": checkpoint,
        "epoch": int(epoch),
        "gray_stats": gray_validation_stats(gray, gray_reference),
        "metric_target": dict(metric_target),
        "threshold_candidates": fast_candidates,
        "selected": fast_selected,
        "scored_candidates": fast_scored,
        "fast_proxy": {
            "metric_target": dict(metric_target),
            "threshold_candidates": fast_candidates,
            "selected": fast_selected,
            "scored_candidates": fast_scored,
        },
        "selection_status": "accepted" if fast_selected.get("passed_gate", False) else "rejected",
    }
    if formal_proxy:
        if formal_metric_target is None:
            fm = formal_binary_pore_metrics(real, real, rmax=formal_rmax)
            formal_metric_target = {"phi": fm["phi"], "s2_rmse": 0.0, "euler": fm["euler"], "maxcc": fm["maxcc"]}
        formal_metric_fn = lambda pore, ref: formal_binary_pore_metrics(pore, ref, rmax=formal_rmax)
        formal_candidates, formal_selected, formal_scored = _score_threshold_candidates(
            gray, real, checkpoint, epoch, porosity_targets, formal_metric_target, weights, gates,
            formal_metric_fn, "formal")
        status = _selection_status(fast_selected, formal_selected)
        summary.update({
            "metric_target": dict(formal_metric_target),
            "threshold_candidates": formal_candidates,
            "selected": formal_selected,
            "scored_candidates": formal_scored,
            "formal_proxy": {
                "rmax": int(formal_rmax),
                "metric_target": dict(formal_metric_target),
                "threshold_candidates": formal_candidates,
                "selected": formal_selected,
                "scored_candidates": formal_scored,
            },
            "selection_status": status,
            "nnunet_proxy_required": status != "accepted",
            "selection_reason": "fast/formal metric disagreement" if status == "needs_formal_resample" else status,
        })
    return summary


@torch.no_grad()
def sample(model, sched, n, size, dev, bs=64, save_continuous=False, mode="binary"):
    """反向扩散采样。
    save_continuous=True 时同时返回连续值数组（float32, 同 [-1,1] 尺度），
    用于 M7-v2 阈值标定诊断；mode="gray" 时主输出保留灰度介质。
    """
    model.eval()
    outs_primary, outs_cont = [], []
    done = 0
    while done < n:
        b = min(bs, n - done)
        x = torch.randn(b, 1, size, size, device=dev)
        for t in sched.timesteps:
            pred = model(x, t).sample
            x = sched.step(pred, t, x).prev_sample
        cont = x[:, 0].cpu().numpy().astype(np.float32)   # [-1,1] 连续输出
        outs_primary.append(postprocess_samples(cont, mode))
        if save_continuous:
            outs_cont.append(cont)
        done += b
    primary = np.concatenate(outs_primary)[:n]
    if save_continuous:
        return primary, np.concatenate(outs_cont)[:n]
    return primary


def save_grid(imgs, path, k=8, mode="binary"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    k = min(k, len(imgs))
    fig, ax = plt.subplots(1, k, figsize=(2 * k, 2))
    axes = np.atleast_1d(ax)
    for i in range(k):
        if mode == "gray":
            axes[i].imshow(imgs[i], cmap="gray", vmin=-1, vmax=1)
        else:
            axes[i].imshow(imgs[i], cmap="gray_r", vmin=0, vmax=1)
        axes[i].axis("off")
    plt.tight_layout(); plt.savefig(path, dpi=110); plt.close()


def _parse_float_list(text):
    return [float(x.strip()) for x in str(text).split(",") if x.strip()]


def _estimate_lower_tail_threshold(arr, porosity_percent):
    """Lower-tail threshold from train split only; used by soft pore proxy."""
    a = np.asarray(arr, dtype=np.float32).ravel()
    if len(a) == 0:
        raise ValueError("threshold reference array must be non-empty")
    return threshold_for_porosity(a, porosity_percent)


def _torch_soft_s2(stack, lags):
    """Differentiable horizontal/vertical soft two-point stats for (N,1,H,W)."""
    vals = []
    for lag in lags:
        lag = int(lag)
        if lag <= 0:
            raise ValueError("soft S2 lags must be positive")
        vals.append((stack[:, :, :, :-lag] * stack[:, :, :, lag:]).mean())
        vals.append((stack[:, :, :-lag, :] * stack[:, :, lag:, :]).mean())
    return torch.stack(vals)


def _torch_soft_euler_proxy(p):
    """Differentiable Euler-like proxy: count soft pore starts not supported by 4-neighbors.

    This is not a formal Euler number. It is a rescue-run topology proxy that
    explicitly pushes against the observed failure mode (large merged pore blobs):
    high values require pore probability to appear as separated local components.
    Formal gate decisions still use ``formal_binary_pore_metrics`` only.
    """
    if F is None:
        raise ModuleNotFoundError("soft Euler proxy requires torch.nn.functional")
    up = F.pad(p[:, :, :-1, :], (0, 0, 1, 0))
    down = F.pad(p[:, :, 1:, :], (0, 0, 0, 1))
    left = F.pad(p[:, :, :, :-1], (1, 0, 0, 0))
    right = F.pad(p[:, :, :, 1:], (0, 1, 0, 0))
    neigh = torch.maximum(torch.maximum(up, down), torch.maximum(left, right))
    starts = p * (1.0 - neigh.clamp(0.0, 1.0))
    return starts.flatten(1).sum(dim=1).mean()


def _torch_soft_maxcc_proxy(p, scales):
    """Differentiable maxCC-like proxy: largest multiscale soft pore window / total pore.

    It deliberately approximates the formal max connected component bottleneck with a
    cheap differentiable upper-pressure term: large dense connected pore regions raise
    the proxy and are penalized. The true maxCC gate remains the formal validation.
    """
    if F is None:
        raise ModuleNotFoundError("soft maxCC proxy requires torch.nn.functional")
    _n, _c, h, w = p.shape
    total = p.flatten(1).sum(dim=1).clamp_min(1e-6)
    vals = []
    for scale in scales:
        k = int(scale)
        if k <= 0:
            raise ValueError("soft maxCC scales must be positive")
        if k > h or k > w:
            continue
        pooled_mass = F.avg_pool2d(p, kernel_size=k, stride=1) * float(k * k)
        vals.append(pooled_mass.flatten(1).max(dim=1).values / total)
    if not vals:
        raise ValueError("at least one soft maxCC scale must fit the training tile size")
    return torch.stack(vals, dim=1).max(dim=1).values.mean()


def _build_soft_pore_regularizer(train_tensor, args, device):
    """Prepare train-only targets for weak topology-aware soft pore regularization.

    This is intentionally low-risk: it never uses test gray statistics, it is off by
    default, and it regularizes train-derived lower-tail pore-probability proxies.
    ``soft_euler_lambda`` / ``soft_maxcc_lambda`` are the one-off B1.1 rescue
    proxies; formal pass/fail remains based on held-out formal validation.
    """
    phi_lam = float(getattr(args, "soft_phi_lambda", 0.0) or 0.0)
    s2_lam = float(getattr(args, "soft_s2_lambda", 0.0) or 0.0)
    euler_lam = float(getattr(args, "soft_euler_lambda", 0.0) or 0.0)
    maxcc_lam = float(getattr(args, "soft_maxcc_lambda", 0.0) or 0.0)
    if phi_lam <= 0.0 and s2_lam <= 0.0 and euler_lam <= 0.0 and maxcc_lam <= 0.0:
        return None
    if F is None:
        raise ModuleNotFoundError("soft pore regularization requires torch.nn.functional")
    tau = float(getattr(args, "soft_pore_tau", 0.08) or 0.08)
    if tau <= 0:
        raise ValueError("--soft-pore-tau must be positive")
    phi_target = float(getattr(args, "soft_pore_phi", 6.4) or 6.4) / 100.0
    lags = [int(x) for x in _parse_float_list(getattr(args, "soft_s2_lags", "1,2,4,8,16"))]
    if not lags:
        raise ValueError("--soft-s2-lags must include at least one lag")
    maxcc_scales = [int(x) for x in _parse_float_list(getattr(args, "soft_maxcc_scales", "4,8,16,32"))]
    if maxcc_lam > 0.0 and not maxcc_scales:
        raise ValueError("--soft-maxcc-scales must include at least one scale")
    # Use train split only. Limit reference samples to keep GPU memory predictable.
    ref_n = int(getattr(args, "soft_reg_ref_n", 512) or 512)
    ref_cpu = train_tensor[:min(ref_n, len(train_tensor))]
    threshold = _estimate_lower_tail_threshold(ref_cpu.numpy(), float(getattr(args, "soft_pore_phi", 6.4)))
    ref = ref_cpu.to(device)
    with torch.no_grad():
        p_ref = torch.sigmoid((float(threshold) - ref) / tau)
        s2_target = _torch_soft_s2(p_ref, lags).detach()
        phi_ref = p_ref.mean().detach()
        euler_target = _torch_soft_euler_proxy(p_ref).detach()
        maxcc_target = _torch_soft_maxcc_proxy(p_ref, maxcc_scales).detach()
    return {
        "threshold": float(threshold),
        "tau": tau,
        "phi_target": torch.tensor(phi_target, dtype=torch.float32, device=device),
        "phi_ref": phi_ref,
        "s2_target": s2_target,
        "euler_target": euler_target,
        "maxcc_target": maxcc_target,
        "lags": lags,
        "maxcc_scales": maxcc_scales,
        "lambda_phi": phi_lam,
        "lambda_s2": s2_lam,
        "lambda_euler": euler_lam,
        "lambda_maxcc": maxcc_lam,
        "ref_n": int(ref.shape[0]),
    }


def _x0_from_eps_prediction(xt, pred_noise, timesteps, sched):
    """Estimate x0 from epsilon-prediction for differentiable regularization."""
    alphas = sched.alphas_cumprod.to(device=xt.device, dtype=xt.dtype)[timesteps]
    while alphas.ndim < xt.ndim:
        alphas = alphas.view(*alphas.shape, 1)
    return (xt - torch.sqrt(1.0 - alphas) * pred_noise) / torch.sqrt(alphas)


def _soft_pore_regularization_loss(x0_pred, reg):
    if F is None:
        raise ModuleNotFoundError("soft pore regularization requires torch.nn.functional")
    p = torch.sigmoid((float(reg["threshold"]) - x0_pred.clamp(-1.0, 1.0)) / float(reg["tau"]))
    loss = x0_pred.new_tensor(0.0)
    parts = {}
    if float(reg["lambda_phi"]) > 0.0:
        target = reg.get("phi_ref", reg["phi_target"])
        l_phi = F.mse_loss(p.mean(), target)
        loss = loss + float(reg["lambda_phi"]) * l_phi
        parts["soft_phi"] = float(l_phi.detach().cpu())
    if float(reg["lambda_s2"]) > 0.0:
        s2 = _torch_soft_s2(p, reg["lags"])
        l_s2 = F.mse_loss(s2, reg["s2_target"])
        loss = loss + float(reg["lambda_s2"]) * l_s2
        parts["soft_s2"] = float(l_s2.detach().cpu())
    if float(reg.get("lambda_euler", 0.0)) > 0.0:
        euler = _torch_soft_euler_proxy(p)
        target = reg["euler_target"]
        scale = target.abs().clamp_min(1.0)
        l_euler = ((euler - target) / scale).pow(2)
        loss = loss + float(reg["lambda_euler"]) * l_euler
        parts["soft_euler"] = float(l_euler.detach().cpu())
    if float(reg.get("lambda_maxcc", 0.0)) > 0.0:
        maxcc = _torch_soft_maxcc_proxy(p, reg["maxcc_scales"])
        l_maxcc = F.mse_loss(maxcc, reg["maxcc_target"])
        loss = loss + float(reg["lambda_maxcc"]) * l_maxcc
        parts["soft_maxcc"] = float(l_maxcc.detach().cpu())
    parts["weighted"] = float(loss.detach().cpu())
    return loss, parts


def _periodic_eval_ready(a):
    return int(getattr(a, "eval_every", 0) or 0) > 0


def _load_periodic_refs(a):
    if not _periodic_eval_ready(a):
        return None, None, None
    if a.sample_mode != "gray":
        raise ValueError("periodic validation requires --sample-mode gray")
    if not a.eval_gray_test or not a.eval_real:
        raise ValueError("periodic validation requires --eval-gray-test and --eval-real")
    gray_ref = np.load(a.eval_gray_test)
    real_pore = np.load(a.eval_real)
    target = binary_pore_metrics(real_pore, real_pore)
    target["s2_rmse"] = 0.0
    return gray_ref, real_pore, target


def _run_periodic_validation(model, sched, a, epoch, ckpt_path, size, dev, gray_ref, real_pore, target):
    gray = sample(model, sched, int(a.eval_n), size, dev, bs=a.bs, mode="gray")
    summary = periodic_validation_summary(
        gray,
        gray_reference=gray_ref,
        real_pore=real_pore,
        checkpoint=os.path.basename(ckpt_path),
        epoch=epoch,
        porosity_targets=_parse_float_list(a.eval_porosity_targets),
        metric_target=target,
        formal_proxy=bool(getattr(a, "eval_formal_proxy", False)),
        formal_rmax=int(getattr(a, "eval_rmax", 48)),
    )
    summary["eval_n"] = int(a.eval_n)
    summary["eval_seed"] = int(a.seed)
    path = os.path.join(a.out, f"validation_ep{epoch:03d}.json")
    json.dump(summary, open(path, "w"), indent=2)
    extra = f" status={summary.get('selection_status', 'accepted')}"
    if summary.get("nnunet_proxy_required"):
        extra += " nnunet_proxy_required=True"
    print(f"[eval ep {epoch:3d}] selected={summary['selected']['porosity_target']:.3f}% "
          f"proxy={summary['selected'].get('proxy', 'fast')} score={summary['selected']['score']:.4f} "
          f"pass={summary['selected']['passed_gate']}{extra} -> {path}")
    return summary


def cmd_train(a):
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(a.seed); np.random.seed(a.seed)
    x = load_train_array(os.path.join(a.data, "train.npy"))
    size = x.shape[-1]
    dl = DataLoader(TensorDataset(x), batch_size=a.bs, shuffle=True,
                    num_workers=4, drop_last=True, pin_memory=True)
    model = build_model(size, a.base).to(dev)
    sched = make_sched()
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr)
    scaler = torch.amp.GradScaler("cuda", enabled=a.amp)
    os.makedirs(a.out, exist_ok=True)
    soft_reg = _build_soft_pore_regularizer(x, a, dev)
    gray_ref, real_pore, metric_target = _load_periodic_refs(a)
    validation_summaries = []
    npar = sum(p.numel() for p in model.parameters()) / 1e6
    print(f"[i] size={size} tiles={len(x)} params={npar:.1f}M bs={a.bs} epochs={a.epochs} dev={dev}")
    if soft_reg is not None:
        print("[i] soft_pore_reg "
              f"phi_lambda={soft_reg['lambda_phi']} s2_lambda={soft_reg['lambda_s2']} "
              f"euler_lambda={soft_reg['lambda_euler']} maxcc_lambda={soft_reg['lambda_maxcc']} "
              f"phi={float(getattr(a, 'soft_pore_phi', 6.4)):.3f}% tau={soft_reg['tau']} "
              f"threshold={soft_reg['threshold']:.5f} lags={soft_reg['lags']} "
              f"maxcc_scales={soft_reg['maxcc_scales']} ref_n={soft_reg['ref_n']}")
    best = 1e9
    for ep in range(1, a.epochs + 1):
        model.train(); tot = 0.0; nb = 0; t0 = time.time()
        for (x0,) in dl:
            x0 = x0.to(dev, non_blocking=True)
            noise = torch.randn_like(x0)
            t = torch.randint(0, sched.config.num_train_timesteps, (x0.shape[0],), device=dev).long()
            xt = sched.add_noise(x0, noise, t)
            with torch.amp.autocast("cuda", enabled=a.amp):
                pred = model(xt, t).sample
                l_simple = F.mse_loss(pred, noise)          # ε-预测 L_simple
                loss = l_simple
                if soft_reg is not None:
                    x0_pred = _x0_from_eps_prediction(xt, pred, t, sched)
                    l_reg, _reg_parts = _soft_pore_regularization_loss(x0_pred, soft_reg)
                    loss = loss + l_reg
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward(); scaler.step(opt); scaler.update()
            tot += l_simple.item(); nb += 1
        avg = tot / max(nb, 1)
        print(f"[ep {ep:3d}] L_simple={avg:.4f}  {time.time()-t0:.1f}s", flush=True)
        if avg < best:
            best = avg
            torch.save(model.state_dict(), os.path.join(a.out, "best.pt"))
        ckpt_path = None
        if int(a.save_every) > 0 and ep % int(a.save_every) == 0:
            ckpt_path = os.path.join(a.out, f"ckpt_ep{ep:03d}.pt")
            torch.save(model.state_dict(), ckpt_path)
        if ep % a.sample_every == 0 or ep == a.epochs:
            g = sample(model, sched, 8, size, dev, mode=a.sample_mode)
            save_grid(g, os.path.join(a.out, f"grid_ep{ep:03d}.png"), mode=a.sample_mode)
        if _periodic_eval_ready(a) and (ep % int(a.eval_every) == 0 or ep == a.epochs):
            if ckpt_path is None:
                ckpt_path = os.path.join(a.out, f"ckpt_ep{ep:03d}.pt")
                torch.save(model.state_dict(), ckpt_path)
            validation_summaries.append(_run_periodic_validation(
                model, sched, a, ep, ckpt_path, size, dev, gray_ref, real_pore, metric_target))
    torch.save(model.state_dict(), os.path.join(a.out, "final.pt"))
    if validation_summaries:
        selection_target = validation_summaries[0].get("metric_target", metric_target)
        selected = select_metric_aware_checkpoint(
            [v["selected"] for v in validation_summaries], target=selection_target)
        json.dump({"summaries": validation_summaries, "selected": selected,
                   "selection_target": selection_target},
                  open(os.path.join(a.out, "periodic_validation_summary.json"), "w"), indent=2)
    train_meta = {"size": size, "n_train": len(x), "epochs": a.epochs, "base": a.base,
                  "bs": a.bs, "lr": a.lr, "seed": a.seed, "sample_mode": a.sample_mode,
                  "best_Lsimple": round(best, 5), "params_M": round(npar, 2)}
    if soft_reg is not None:
        train_meta["soft_pore_regularization"] = {
            "lambda_phi": float(soft_reg["lambda_phi"]),
            "lambda_s2": float(soft_reg["lambda_s2"]),
            "lambda_euler": float(soft_reg["lambda_euler"]),
            "lambda_maxcc": float(soft_reg["lambda_maxcc"]),
            "soft_pore_phi": float(getattr(a, "soft_pore_phi", 6.4)),
            "tau": float(soft_reg["tau"]),
            "threshold_train_only": float(soft_reg["threshold"]),
            "lags": list(soft_reg["lags"]),
            "maxcc_scales": list(soft_reg["maxcc_scales"]),
            "euler_target": float(soft_reg["euler_target"].detach().cpu()),
            "maxcc_target": float(soft_reg["maxcc_target"].detach().cpu()),
            "ref_n": int(soft_reg["ref_n"]),
        }
    json.dump(train_meta, open(os.path.join(a.out, "train_meta.json"), "w"), indent=2)
    print(f"[done] best L_simple={best:.4f} -> {a.out}")


def cmd_sample(a):
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(a.seed)
    os.makedirs(a.out, exist_ok=True)
    size = a.size
    model = build_model(size, a.base).to(dev)
    model.load_state_dict(torch.load(a.ckpt, map_location=dev))
    result = sample(model, make_sched(), a.n, size, dev, bs=a.bs,
                    save_continuous=getattr(a, "continuous", False), mode=a.sample_mode)
    if isinstance(result, tuple):
        g, cont = result
        np.save(os.path.join(a.out, "samples_continuous.npy"), cont)
        print(f"[info] 连续值已保存 -> {a.out}/samples_continuous.npy  (float32, [-1,1])")
    else:
        g = result
    calibration_mode = getattr(a, "intensity_calibration", "none")
    if a.sample_mode == "gray" and calibration_mode != "none":
        if not getattr(a, "calibration_data", None):
            raise ValueError("--calibration-data is required when --intensity-calibration is not none")
        ref = np.load(os.path.join(a.calibration_data, "train.npy"))
        calibration = make_intensity_calibration(ref, mode=calibration_mode)
        calibration["sample_mean_before"] = float(np.asarray(g, dtype=np.float32).mean())
        calibration["sample_std_before"] = float(np.asarray(g, dtype=np.float32).std())
        g = apply_intensity_calibration(g, calibration)
        calibration["sample_mean_after"] = float(np.asarray(g, dtype=np.float32).mean())
        calibration["sample_std_after"] = float(np.asarray(g, dtype=np.float32).std())
        calibration["calibration_data"] = a.calibration_data
        json.dump(calibration, open(os.path.join(a.out, "sample_intensity_calibration.json"), "w"), indent=2)
        print(f"[info] intensity calibration {calibration_mode} -> {a.out}/sample_intensity_calibration.json")
    sample_name = "samples_gray.npy" if a.sample_mode == "gray" else "samples.npy"
    np.save(os.path.join(a.out, sample_name), g)
    save_grid(g, os.path.join(a.out, "samples_grid.png"), mode=a.sample_mode)
    if a.sample_mode == "gray":
        print(f"[done] {a.n} gray samples min={float(g.min()):.3f} max={float(g.max()):.3f} mean={float(g.mean()):.3f} -> {a.out}/{sample_name}")
    else:
        por = g.reshape(len(g), -1).mean(1) * 100
        print(f"[done] {a.n} samples 孔隙度 均值={por.mean():.2f}% 中位={np.median(por):.2f}% -> {a.out}/{sample_name}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("train")
    p.add_argument("--data", required=True); p.add_argument("--out", required=True)
    p.add_argument("--epochs", type=int, default=80); p.add_argument("--bs", type=int, default=64)
    p.add_argument("--base", type=int, default=64); p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--amp", action="store_true"); p.add_argument("--seed", type=int, default=42)
    p.add_argument("--sample-every", type=int, default=20)
    p.add_argument("--save-every", type=int, default=0,
                   help="save periodic ckpt_epXXX.pt checkpoints; B1.1 uses 10")
    p.add_argument("--eval-every", type=int, default=0,
                   help="run periodic gray validation every N epochs; B1.1 uses 10")
    p.add_argument("--eval-n", type=int, default=32,
                   help="small validation sample count for periodic checkpoint scoring")
    p.add_argument("--eval-gray-test", default=None,
                   help="gray reference .npy for mean/std/KS during periodic validation")
    p.add_argument("--eval-real", default=None,
                   help="real pore .npy evaluated with the same proxy for S2/Euler/maxCC targets")
    p.add_argument("--eval-porosity-targets", default="6.0,6.4",
                   help="comma-separated lower-tail porosity thresholds to evaluate")
    p.add_argument("--eval-formal-proxy", action="store_true",
                   help="also run B1 cheap50-compatible S2/Euler/maxCC formal proxy and select checkpoints by it")
    p.add_argument("--eval-rmax", type=int, default=48,
                   help="radial S2 rmax for --eval-formal-proxy; B1 cheap50 uses 48")
    p.add_argument("--select-metric", choices=["composite"], default="composite",
                   help="checkpoint selection metric; currently gated composite score")
    p.add_argument("--soft-phi-lambda", type=float, default=0.0,
                   help="weak differentiable lower-tail soft porosity regularization weight; off by default")
    p.add_argument("--soft-s2-lambda", type=float, default=0.0,
                   help="weak differentiable soft two-point-statistics regularization weight; off by default")
    p.add_argument("--soft-euler-lambda", type=float, default=0.0,
                   help="one-off B1.1 rescue: differentiable Euler-like topology proxy weight; off by default")
    p.add_argument("--soft-maxcc-lambda", type=float, default=0.0,
                   help="one-off B1.1 rescue: differentiable maxCC-like topology proxy weight; off by default")
    p.add_argument("--soft-pore-phi", type=float, default=6.4,
                   help="train-split lower-tail porosity percent used to derive soft pore threshold")
    p.add_argument("--soft-pore-tau", type=float, default=0.08,
                   help="sigmoid temperature for soft pore proxy")
    p.add_argument("--soft-s2-lags", default="1,2,4,8,16",
                   help="comma-separated lags for differentiable soft S2 regularization")
    p.add_argument("--soft-maxcc-scales", default="4,8,16,32",
                   help="comma-separated window sizes for differentiable soft maxCC proxy")
    p.add_argument("--soft-reg-ref-n", type=int, default=512,
                   help="number of train slices used to build train-only soft topology targets")
    p.add_argument("--sample-mode", choices=["binary", "gray"], default="binary",
                   help="checkpoint grid sample representation: binary for pore masks, gray for B1 sus")
    p.set_defaults(func=cmd_train)
    s = sub.add_parser("sample")
    s.add_argument("--ckpt", required=True); s.add_argument("--out", required=True)
    s.add_argument("--n", type=int, default=512); s.add_argument("--size", type=int, default=128)
    s.add_argument("--base", type=int, default=64); s.add_argument("--bs", type=int, default=64)
    s.add_argument("--seed", type=int, default=123)
    s.add_argument("--continuous", action="store_true", help="同时保存连续值 samples_continuous.npy（M7-v2 用）")
    s.add_argument("--sample-mode", choices=["binary", "gray"], default="binary",
                   help="primary saved sample representation: samples.npy for binary, samples_gray.npy for gray")
    s.add_argument("--intensity-calibration", choices=["none", "train-moments"], default="none",
                   help="gray samples only: optional output calibration; train-moments uses --calibration-data/train.npy")
    s.add_argument("--calibration-data", default=None,
                   help="dataset directory containing train.npy for --intensity-calibration train-moments")
    s.set_defaults(func=cmd_sample)
    a = ap.parse_args()
    a.func(a)
