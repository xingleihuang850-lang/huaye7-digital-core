# M7-v3 200ep cheap control evidence

目的：只改变 DDPM 训练 epoch（50ep → 200ep），用同一 ct28 128² 二值孔隙切片、同一采样 seed=123、同一 eval/calib 口径检验“欠训练”是否是 M7-v2 连通性问题主因。

## 远程执行

- host：`hy7-linux` / `/home/user/HXL/HY7_planb`
- conda env：`nnunet_t28`
- 采样权重：`phase2/ddpm_ct28_200ep/best.pt`
- 采样输出（大文件，不入 git）：
  - `phase2/ddpm_ct28_200ep/samples.npy`
  - `phase2/ddpm_ct28_200ep/samples_continuous.npy`
- 远程原始日志：`remote_run/m7v3_200ep_run_20260703.log`
- 当前 eval/calib 重跑 hash：`remote_run/m7v3_200ep_hashes_rerun_20260703.txt`

## 关键 sha256

大文件（远程，不入 git）：

```text
42101fdd97f531608d33f6c7a7b2be649b777210d36d48ef63aa7a2a47331288  phase2/ddpm_ct28_200ep/samples.npy
7184d08955c36137da82632b2a2d0028abc1d8e9de8e4490806b563ba9de61  phase2/ddpm_ct28_200ep/samples_continuous.npy
8ab0db9d1d527778a1e71ff34caa988048baac33840870a7b832a0caeb18323e  phase2/ddpm_ct28_200ep/samples_grid.png
```

入 git轻量证据：

```text
c753d5fb73e19c774b0dee81ada96d77ed714de06c5ddeaa56934d4f0bef1006  eval/fig_eval.png
988db3f9499c107a789a8833112dd4f1273f386563ea73cb047045237c651178  eval/metrics.json
f2932a49edcd4351f799a01de65a1594fece034b40c47f58e2ca1049b547d661  calib/calib_result.json
dcf29686f54fe6f721bfd98c47b34996f7540cfd5dae8a6f77b0d65d06b38d8c  calib/fig_calib.png
8ab0db9d1d527778a1e71ff34caa988048baac33840870a7b832a0caeb18323e  samples_grid.png
```

## 指标结论

| 口径 | φ mean | S₂ rmse | Euler χ mean | max CC frac | 判读 |
|---|---:|---:|---:|---:|---|
| real 512 | 6.405% | — | 127.33 | 0.0597 | 真实对照 |
| 50ep T=0 | 23.506% | 0.07143 | 146.24 | 0.1588 | 阈值伪影导致严重过孔隙 |
| 50ep T* | 6.400% | 0.00242 | 207.92 | — | S₂ 修好但 Euler 变差，连通性真错 |
| 200ep T=0 | 4.960% | 0.00372 | 120.88 | 0.0467 | 欠训练不是主因；孔隙偏少但 Euler 接近 |
| 200ep T* | 6.400% | 0.01010 | 119.58 | — | 强行标定 φ 后 S₂/Euler 反而变差 |

结论：200ep cheap control 没有证明“多训二值 DDPM”能闭合主线。它把 50ep 的过孔隙问题推向偏少孔隙，T=0 下 Euler 接近真实但 φ 偏低，T* 标定后 S₂/Euler 均变差。下一步不应继续单纯加 epoch，而应转 B1 灰度介质生成（优先）或 B2 `[sus,pore]` 双通道联合生成，让灰度空间语境参与生成。
