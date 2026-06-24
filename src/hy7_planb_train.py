#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
花页7 Plan B —— 3D U-Net 三相分割训练（torch，跑在 hy7-linux GPU）。

**在线采样**：直接读完整体素（sus 灰度 + pore/feng 掩膜），每个 epoch 现采 patch，
无需预烤 .npz 数据集、无需本机 35G 拷贝。任务：灰度→{0 基质/1 孔隙/2 裂缝}，
ignore=255（柱塞外）。相值由已核校孔隙度自动反推（见 hy7_planb_io）。

在 hy7-linux 上直接指到 rsync 来的原始数据即可：
  python src/hy7_planb_train.py --scale ct14 \
      --root /home/user/HXL/HY7_source/吉林大学数据报告归总 --layout source \
      --epochs 60 --steps 400 --bs 2 --patch 128 --amp

本机(Mac, 无 torch/GPU)只写脚本、用 io.py 的 numpy 工具自检；不在本机训练。
"""
import os, sys, json, argparse, time

IGNORE = 255


def _need_torch():
    try:
        import torch  # noqa
    except Exception:
        sys.exit("[x] 未装 torch —— 本脚本在 hy7-linux GPU 机上运行（Mac 端只用 io.py 的 numpy 工具）。")


def make_dataset(scale, root, layout, patch, steps, min_fg, mean, std, train):
    import numpy as np, torch
    from torch.utils.data import Dataset
    from hy7_planb_io import ScaleVolumes

    class OnTheFly(Dataset):
        def __init__(self):
            self._sv = None                      # 每个 worker 进程内惰性重开 memmap
        def sv(self):
            if self._sv is None:
                self._sv = ScaleVolumes(scale, root=root, layout=layout, norm_samples=0)
            return self._sv
        def __len__(self):
            return steps
        def __getitem__(self, i):
            rng = np.random.default_rng()        # 现采，新随机
            ic, lbl = self.sv().sample(patch, rng, min_fg=min_fg)
            x = (ic.astype("float32") - mean) / std
            y = lbl.astype("int64")
            if train:
                for ax in (0, 1, 2):
                    if np.random.rand() < 0.5:
                        x = np.flip(x, ax); y = np.flip(y, ax)
                x, y = np.ascontiguousarray(x), np.ascontiguousarray(y)
            return torch.from_numpy(x)[None], torch.from_numpy(y)
    return OnTheFly()


def make_unet(n_cls, base=16):
    import torch, torch.nn as nn

    def cbr(i, o):
        return nn.Sequential(nn.Conv3d(i, o, 3, padding=1, bias=False),
                             nn.InstanceNorm3d(o), nn.LeakyReLU(0.01, inplace=True),
                             nn.Conv3d(o, o, 3, padding=1, bias=False),
                             nn.InstanceNorm3d(o), nn.LeakyReLU(0.01, inplace=True))

    class UNet3D(nn.Module):
        def __init__(self):
            super().__init__()
            b = base
            self.e1, self.e2, self.e3 = cbr(1, b), cbr(b, b*2), cbr(b*2, b*4)
            self.bott = cbr(b*4, b*8)
            self.pool = nn.MaxPool3d(2)
            self.u3 = nn.ConvTranspose3d(b*8, b*4, 2, 2); self.d3 = cbr(b*8, b*4)
            self.u2 = nn.ConvTranspose3d(b*4, b*2, 2, 2); self.d2 = cbr(b*4, b*2)
            self.u1 = nn.ConvTranspose3d(b*2, b,   2, 2); self.d1 = cbr(b*2, b)
            self.out = nn.Conv3d(b, n_cls, 1)
        def forward(self, x):
            c1 = self.e1(x); c2 = self.e2(self.pool(c1)); c3 = self.e3(self.pool(c2))
            bo = self.bott(self.pool(c3))
            x = self.d3(torch.cat([self.u3(bo), c3], 1))
            x = self.d2(torch.cat([self.u2(x), c2], 1))
            x = self.d1(torch.cat([self.u1(x), c1], 1))
            return self.out(x)
    return UNet3D()


def dice_ce_loss(logits, target, n_cls):
    import torch, torch.nn.functional as F
    ce = F.cross_entropy(logits, target, ignore_index=IGNORE)
    valid = (target != IGNORE)
    t = target.clone(); t[~valid] = 0
    oh = F.one_hot(t, n_cls).permute(0, 4, 1, 2, 3).float() * valid.unsqueeze(1)
    p = torch.softmax(logits, 1) * valid.unsqueeze(1)
    inter = (p * oh).sum((0, 2, 3, 4)); denom = p.sum((0, 2, 3, 4)) + oh.sum((0, 2, 3, 4))
    dice = (2 * inter + 1) / (denom + 1)
    return ce + (1 - dice.mean()), dice.detach()


def build_val(scale, root, layout, patch, n, mean, std):
    """固定一组验证 patch（一次采样，跨 epoch 不变），稳定评估。"""
    import numpy as np, torch
    from hy7_planb_io import ScaleVolumes
    sv = ScaleVolumes(scale, root=root, layout=layout, norm_samples=0)
    rng = np.random.default_rng(12345)
    xs, ys = [], []
    for _ in range(n):
        ic, lbl = sv.sample(patch, rng)
        xs.append(((ic.astype("float32") - mean) / std)[None]); ys.append(lbl.astype("int64"))
    return torch.from_numpy(np.stack(xs)), torch.from_numpy(np.stack(ys))


def main():
    _need_torch()
    import numpy as np, torch
    from torch.utils.data import DataLoader
    from hy7_planb_io import ScaleVolumes, SCALE_COMPONENTS

    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", required=True, choices=list(SCALE_COMPONENTS))
    ap.add_argument("--root", default=None, help="体素根；Linux 原始数据用 …/吉林大学数据报告归总")
    ap.add_argument("--layout", default=None, choices=["local", "source"])
    ap.add_argument("--patch", type=int, default=128)
    ap.add_argument("--steps", type=int, default=400, help="每 epoch 在线采样多少 patch")
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--bs", type=int, default=2)
    ap.add_argument("--base", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--min-fg", type=float, default=0.005)
    ap.add_argument("--val-n", type=int, default=40)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--amp", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    sv0 = ScaleVolumes(a.scale, root=a.root, layout=a.layout)   # 主进程：拿 norm / n_cls / 相值
    n_cls, mean, std = sv0.n_cls, sv0.mean, sv0.std
    outdir = a.out or os.path.join("runs", f"train_{a.scale}")
    os.makedirs(outdir, exist_ok=True)
    print(f"[i] scale={a.scale} dims={sv0.dims} n_cls={n_cls} pore_val={sv0.pore_val} "
          f"frac_val={sv0.frac_val} norm=({mean:.1f},{std:.1f}) dev={dev}")

    tr = make_dataset(a.scale, a.root, a.layout, a.patch, a.steps, a.min_fg, mean, std, True)
    dl = DataLoader(tr, batch_size=a.bs, shuffle=False, num_workers=a.workers, drop_last=True)
    vx, vy = build_val(a.scale, a.root, a.layout, a.patch, a.val_n, mean, std)

    net = make_unet(n_cls, a.base).to(dev)
    opt = torch.optim.AdamW(net.parameters(), lr=a.lr, weight_decay=1e-4)
    scaler = torch.amp.GradScaler("cuda", enabled=a.amp)
    log, best = [], -1.0

    for ep in range(1, a.epochs + 1):
        net.train(); t0 = time.time(); tl = 0.0
        for x, y in dl:
            x, y = x.to(dev), y.to(dev); opt.zero_grad()
            with torch.amp.autocast("cuda", enabled=a.amp):
                loss, _ = dice_ce_loss(net(x), y, n_cls)
            scaler.scale(loss).backward(); scaler.step(opt); scaler.update()
            tl += loss.item()
        net.eval(); dices = []
        with torch.no_grad():
            for i in range(0, len(vx), a.bs):
                x, y = vx[i:i+a.bs].to(dev), vy[i:i+a.bs].to(dev)
                with torch.amp.autocast("cuda", enabled=a.amp):
                    _, d = dice_ce_loss(net(x), y, n_cls)
                dices.append(d.cpu().numpy())
        vdice = np.mean(dices, 0)
        rec = {"epoch": ep, "train_loss": round(tl / max(1, len(dl)), 4),
               "val_dice": [round(float(v), 4) for v in vdice],
               "val_dice_mean": round(float(vdice.mean()), 4), "sec": round(time.time() - t0, 1)}
        log.append(rec); print(rec)
        json.dump(log, open(os.path.join(outdir, "trainlog.json"), "w"), ensure_ascii=False, indent=2)
        if rec["val_dice_mean"] > best:
            best = rec["val_dice_mean"]
            torch.save({"model": net.state_dict(), "n_cls": n_cls, "base": a.base,
                        "norm": [mean, std], "scale": a.scale, "epoch": ep,
                        "pore_val": sv0.pore_val, "frac_val": sv0.frac_val},
                       os.path.join(outdir, "best.pt"))
    print(f">> done. best val_dice_mean={best:.4f}  ckpt={outdir}/best.pt")


if __name__ == "__main__":
    main()
