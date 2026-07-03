# phase2 实验证据说明

本目录是花页7阶段二 DDPM 生成实验的证据区，用于保存轻量结果、图表与大文件来源记录，避免把不同阈值口径混读。

| 路径/目录 | 语义 | 注意事项 |
|---|---|---|
| `phase2/` | 阶段二 DDPM 生成证据区 | 只放可复核证据与轻量产物；训练/采样大文件不直接入 git。 |
| `eval_v2/` | M7 原始评估补充版 | 这是原始 `T=0` 二值化口径，不是 `T*` 阈值标定后的评估；φ 仍为 gen 23.51% vs real 6.40%。 |
| `m7v2_calib/` | M7-v2 阈值标定诊断 | `T*=0.98732` 对齐真实孔隙度并把 S₂ rmse 从 0.07143 降到 0.00242；但 Euler 从真实 127.33 到 207.92，说明连通性/聚集仍是真问题。 |
| 大文件记录 | `samples.npy`、`samples_continuous.npy`、`ckpt/*.pt` 等 | 不入 git；只在笔记或清单中记录远程/本地路径、sha256、生成命令与日期。当前 M7 50ep 关键大文件 sha256/大小/mtime 已见 `remote_provenance_20260701/` 与 `experiments/WEIGHTS_MANIFEST.md`。 |
| `remote_provenance_20260701/` | 2026-07-01 远程只读核验证据 | 保存 `hy7-linux` 上 meta/train_meta/hash/env/log 的原始 stdout；确认 M7 主链为 `slices_ct28_128`，tile=128、z_step=6、axes=z。 |
| `m7v3_200ep/` | M7-v3 200ep cheap control 轻量证据 | 200ep 已采样/评估：T=0 φ=4.960%、S₂ rmse=0.00372、Euler=120.88；T* φ=6.4 后 S₂ rmse=0.01010、Euler=119.58。结论：单纯加 epoch 不闭合，转 B1 灰度介质生成。 |
