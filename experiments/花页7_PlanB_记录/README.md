# 花页7 Plan B —— 证据包

本目录是「对齐+分割」工作的**原始证据**，配合实验记录
`notes/13_阶段一_PlanB实验记录_E0.md` 使用。所有数字/图均可由此追溯，**不编造**。
（E1/E2/E3/S3 及阶段二证据后续陆续沉淀于本目录及 `phase2/`，完整清单见 `experiments/INDEX.md`；下表为 E0 时期初始清单。）

| 文件 | 内容 | 复现命令 |
|---|---|---|
| `evidence_inspect_volumes.json` | 7 体素取值分布 + 相值反推（sus=灰度、相值=0） | `python src/hy7_planb_io.py inspect` |
| `evidence_align_summary_ct14.json` | 三体同 shape、孔隙∩裂缝重叠=0% | `python src/hy7_planb_check_alignment.py --scale ct14` |
| `ct14_z*.png`（4） | 灰度+标签叠加图 | 同上 |
| `evidence_trainlog_ct14.json` | 100 epoch 全曲线（dice 原始记录，final mean=0.831） | 见实验记录步骤 7 命令 |
| `evidence_training_meta.txt` | 机器/env/best.pt sha256/脚本 sha256/数据源 raw | Linux 快照 |
| `evidence_src_sha256_mac.txt` | 本机脚本 sha256（与 Linux 比对一致 → 跑的就是这份码） | `shasum -a 256 src/hy7_planb_*.py` |

> best.pt（22MB）未入 git，在 `hy7-linux:~/HXL/HY7_planb/experiments/hy7_planb/train_ct14/best.pt`，
> sha256 `ed6fc55e24ce69cdca1632132bb897f7cd5b760a180e35ccad4735362e56fc1f`。
