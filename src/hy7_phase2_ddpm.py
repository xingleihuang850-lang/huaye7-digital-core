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
    npar = sum(p.numel() for p in model.parameters()) / 1e6
    print(f"[i] size={size} tiles={len(x)} params={npar:.1f}M bs={a.bs} epochs={a.epochs} dev={dev}")
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
                loss = F.mse_loss(pred, noise)          # ε-预测 L_simple
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward(); scaler.step(opt); scaler.update()
            tot += loss.item(); nb += 1
        avg = tot / max(nb, 1)
        print(f"[ep {ep:3d}] L_simple={avg:.4f}  {time.time()-t0:.1f}s", flush=True)
        if avg < best:
            best = avg
            torch.save(model.state_dict(), os.path.join(a.out, "best.pt"))
        if ep % a.sample_every == 0 or ep == a.epochs:
            g = sample(model, sched, 8, size, dev, mode=a.sample_mode)
            save_grid(g, os.path.join(a.out, f"grid_ep{ep:03d}.png"), mode=a.sample_mode)
    torch.save(model.state_dict(), os.path.join(a.out, "final.pt"))
    json.dump({"size": size, "n_train": len(x), "epochs": a.epochs, "base": a.base,
               "bs": a.bs, "lr": a.lr, "seed": a.seed, "sample_mode": a.sample_mode,
               "best_Lsimple": round(best, 5), "params_M": round(npar, 2)},
              open(os.path.join(a.out, "train_meta.json"), "w"), indent=2)
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
