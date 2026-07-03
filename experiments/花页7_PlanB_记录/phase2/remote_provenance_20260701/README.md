# 2026-07-01 远程只读 provenance 核验

本目录保存本次 M7-v2/M7-v3 前置核验的原始 stdout 证据。命令均为只读：`find`、`ls`、`stat`、`sha256sum`、`json.tool`、环境版本查询、`nvidia-smi`、git probe；未启动训练、未删除/移动远程文件、未写远程文件。

## 文件说明

| 文件 | 内容 |
|---|---|
| `01_inventory.txt` | 远程 `/home/user/HXL/HY7_planb/phase2` 目录与 JSON/log 清单 |
| `02_meta_and_train_meta.txt` | 初次 meta/train_meta/hash 采集；因远程默认 `python` 不存在，JSON 内容未全部展开，保留作原始失败记录 |
| `03_artifacts_hashes.txt` | M7 50ep、M7-v3 200ep、切片 `.npy` 大文件的大小、mtime、sha256 |
| `04_environment_snapshot.txt` | `nnunet_t28` 环境版本、CUDA/GPU、`nvidia-smi` |
| `05_remote_git_probe.txt` | 远程 `/home/user/HXL` / `HY7_planb` 不是 git 工作树的只读核验 |
| `06_json_contents_and_200ep_log.txt` | 用远程 conda python 重新展开 JSON，并保存 `ddpm_ct28_200ep.log` 头尾 |

## 关键核验结论

- M7 使用的 128 tile 数据集是 `/home/user/HXL/HY7_planb/phase2/slices_ct28_128/`，`meta.json` 显示：`tile=128`、`z_step=6`、`axes=z`、`seed=42`、`n_train=16600`、`n_test=4150`、test porosity mean `6.443%`、median `5.676%`。
- 另有旧/备用 `/home/user/HXL/HY7_planb/phase2/slices_ct28/`，`tile=256`、`z_step=4`、`n_train=4800`、`n_test=1200`；不应再与 M7 128² DDPM 主链混用。
- M7 50ep `ddpm_ct28/train_meta.json` 显示：`epochs=50`、`bs=64`、`base=64`、`lr=1e-4`、`best_Lsimple=0.01938`、`params_M=63.15`。
- M7-v3 200ep 权重已经训练完成：`ddpm_ct28_200ep/train_meta.json` 显示 `epochs=200`、`bs=64`、`base=64`、`lr=1e-4`、`best_Lsimple=0.01881`；`ddpm_ct28_200ep.log` 末行 `[done] best L_simple=0.0188 -> ddpm_ct28_200ep`。
- 200ep 目录目前只有权重和训练网格图，未发现 `samples.npy` / `samples_continuous.npy`；因此 200ep 尚未完成采样和 eval/calib，不能下最终 Euler/S₂ 结论。
- 远程 `m7v2_calib/calib_result.json` 的 verdict 仍是旧错判（“S₂/Euler 明显改善”）；本地入库的 `experiments/.../m7v2_calib/calib_result.json` 已修正为 “S₂ 明显改善，Euler 变差”。正式同步时以本地修正口径为准，不应把远程旧 verdict 覆盖回来。
