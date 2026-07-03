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
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset


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


def load_binary(npy):
    a = np.load(npy)                          # (N,H,W) uint8 {0,1}
    x = torch.from_numpy(a.astype(np.float32) * 2.0 - 1.0)[:, None]   # → [-1,1]
    return x


@torch.no_grad()
def sample(model, sched, n, size, dev, bs=64, save_continuous=False):
    """反向扩散采样。
    save_continuous=True 时同时返回连续值数组（float32, 同 [-1,1] 尺度），
    用于 M7-v2 阈值标定诊断。
    """
    model.eval()
    outs_bin, outs_cont = [], []
    done = 0
    while done < n:
        b = min(bs, n - done)
        x = torch.randn(b, 1, size, size, device=dev)
        for t in sched.timesteps:
            pred = model(x, t).sample
            x = sched.step(pred, t, x).prev_sample
        cont = x[:, 0].cpu().numpy().astype(np.float32)   # [-1,1] 连续输出
        outs_bin.append((cont > 0).astype(np.uint8))
        if save_continuous:
            outs_cont.append(cont)
        done += b
    binary = np.concatenate(outs_bin)[:n]
    if save_continuous:
        return binary, np.concatenate(outs_cont)[:n]
    return binary


def save_grid(binimgs, path, k=8):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    k = min(k, len(binimgs))
    fig, ax = plt.subplots(1, k, figsize=(2 * k, 2))
    for i in range(k):
        ax[i].imshow(binimgs[i], cmap="gray_r", vmin=0, vmax=1); ax[i].axis("off")
    plt.tight_layout(); plt.savefig(path, dpi=110); plt.close()


def cmd_train(a):
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(a.seed); np.random.seed(a.seed)
    x = load_binary(os.path.join(a.data, "train.npy"))
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
            g = sample(model, sched, 8, size, dev)
            save_grid(g, os.path.join(a.out, f"grid_ep{ep:03d}.png"))
    torch.save(model.state_dict(), os.path.join(a.out, "final.pt"))
    json.dump({"size": size, "n_train": len(x), "epochs": a.epochs, "base": a.base,
               "bs": a.bs, "lr": a.lr, "best_Lsimple": round(best, 5), "params_M": round(npar, 2)},
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
                    save_continuous=getattr(a, "continuous", False))
    if isinstance(result, tuple):
        g, cont = result
        np.save(os.path.join(a.out, "samples_continuous.npy"), cont)
        print(f"[info] 连续值已保存 -> {a.out}/samples_continuous.npy  (float32, [-1,1])")
    else:
        g = result
    np.save(os.path.join(a.out, "samples.npy"), g)
    save_grid(g, os.path.join(a.out, "samples_grid.png"))
    por = g.reshape(len(g), -1).mean(1) * 100
    print(f"[done] {a.n} samples 孔隙度 均值={por.mean():.2f}% 中位={np.median(por):.2f}% -> {a.out}/samples.npy")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("train")
    p.add_argument("--data", required=True); p.add_argument("--out", required=True)
    p.add_argument("--epochs", type=int, default=80); p.add_argument("--bs", type=int, default=64)
    p.add_argument("--base", type=int, default=64); p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--amp", action="store_true"); p.add_argument("--seed", type=int, default=42)
    p.add_argument("--sample-every", type=int, default=20)
    p.set_defaults(func=cmd_train)
    s = sub.add_parser("sample")
    s.add_argument("--ckpt", required=True); s.add_argument("--out", required=True)
    s.add_argument("--n", type=int, default=512); s.add_argument("--size", type=int, default=128)
    s.add_argument("--base", type=int, default=64); s.add_argument("--bs", type=int, default=64)
    s.add_argument("--seed", type=int, default=123)
    s.add_argument("--continuous", action="store_true", help="同时保存连续值 samples_continuous.npy（M7-v2 用）")
    s.set_defaults(func=cmd_sample)
    a = ap.parse_args()
    a.func(a)
