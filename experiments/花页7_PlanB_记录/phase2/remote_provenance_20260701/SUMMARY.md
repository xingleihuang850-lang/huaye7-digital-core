# 2026-07-01 多agent远程只读核验与文档同步小结

## 执行范围

- 已启动 2 个后台子agent：
  - 本地文档一致性审计 agent
  - 远程 hy7-linux 只读核验 agent
- 主agent同步执行了远程只读核验，并将原始 stdout 保存到：
  `experiments/花页7_PlanB_记录/phase2/remote_provenance_20260701/`
- 未执行删除、移动、训练、采样、git add/commit。

## 远程只读核验关键发现

1. M7 128² 主链数据集已确认：
   - `/home/user/HXL/HY7_planb/phase2/slices_ct28_128/`
   - `tile=128`
   - `z_step=6`
   - `axes=z`
   - `seed=42`
   - `n_train=16600`
   - `n_test=4150`
   - test φ mean `6.443%`，median `5.676%`
   - `meta.json` sha256: `993b1d3220fd81c37aebfe15d4be13cad332f5c49cdf48cc5d0a0d4424ad4c9d`

2. 旧/备用切片目录存在，但不是主链：
   - `/home/user/HXL/HY7_planb/phase2/slices_ct28/`
   - `tile=256`
   - `z_step=4`
   - `n_train=4800`
   - `n_test=1200`

3. M7 50ep DDPM 已核验：
   - `best.pt` sha256: `ee15bb0ab5a67c1d22ad38b9bbd4f870f42ebb8ed4c41053da8989143449bb98`
   - `final.pt` sha256: `12665a44821b59e858640332986fb226d8aa07559e678ddbe58ac42a4b852ba9`
   - `samples.npy` sha256: `bc7cfecb572cc250341dbe077f36da802e98f3453f8ec073b0510ed39dfa7a0e`
   - `samples_continuous.npy` sha256: `fdd2f264fdfb5127843b38f9e869fb9fb5c7747ac0036dbefb0b4c5b2032996d`
   - train_meta: epochs=50, bs=64, base=64, lr=1e-4, best_Lsimple=0.01938

4. M7-v3 200ep 已经训练完成：
   - `/home/user/HXL/HY7_planb/phase2/ddpm_ct28_200ep/`
   - `best.pt` sha256: `f009973ce37228644e6158ed46d9e08b1dfdb8c892754b6e327933b970646a6d`
   - `final.pt` sha256: `4975ed241dc4af15178199ee32370ad39a45763e745fbdda285fc2484634ae78`
   - train_meta: epochs=200, bs=64, base=64, lr=1e-4, best_Lsimple=0.01881
   - log 末行：`[done] best L_simple=0.0188 -> ddpm_ct28_200ep`

5. M7-v3 200ep 尚未采样/评估：
   - 未发现 `ddpm_ct28_200ep/samples.npy`
   - 未发现 `ddpm_ct28_200ep/samples_continuous.npy`
   - 因此不能下 S₂/Euler/连通性是否改善的结论。

6. 远程 m7v2_calib JSON 的 verdict 仍是旧错判：
   - 远程 verdict 写“标定后 S₂/Euler 明显改善”
   - 本地入库版已修正为“S₂ 明显改善，Euler 变差”
   - 后续不能用远程旧 JSON 覆盖本地修正版。

## 已同步的本地文档

- `CLAUDE.md`
- `notes/00_研究主线路线图与任务分解.md`
- `notes/24_阶段二_M7v3_连通性迭代设计.md`
- `REPRODUCE.md`
- `docs/environment-remote.md`
- `experiments/WEIGHTS_MANIFEST.md`
- `experiments/花页7_PlanB_记录/phase2/README.md`
- `configs/phase2_m7v2.example.json`
- 新增 `experiments/花页7_PlanB_记录/phase2/remote_provenance_20260701/README.md` 与 6 个原始 stdout 文件。

## 校验

- `python3 -m json.tool configs/phase2_m7v2.example.json`：通过。
- `git diff --check`：通过（无 whitespace error）。
- 搜索残留：未再发现 `ct28_tiles`、`z-step <TODO>`、`bs <TODO>`、`sample-every <TODO>`、`planned_or_running_TBD`、`sample-every 20`、`example_template`、`reported_sha256_from_note`。

## 当前剩余问题

1. 训练 seed 仍未在 `train_meta.json` 中记录；当前 `--seed 42` 来自既有命令模板/记录，尚未从 shell history 原始命令二次确认。
2. 200ep 已训练完成但缺采样与评估；下一步应对 `ddpm_ct28_200ep/best.pt` 做同口径采样、eval、calib。
3. 本机 `.venv` 仍缺 `diffusers`；本机不能直接跑 DDPM train/sample。
4. 远程 `/home/user/HXL/HY7_planb` 不是 git 工作树；权重对应的代码 commit 只能以后通过本地同步记录/rsync时间补足。
5. 未跟踪文件仍存在：`src/hy7_ct14_make_nnunet_3phase.py`、`experiments/花页7_PlanB_记录/figs_ppt/`。本轮未处理，因为用户指令是先做远程只读核验和文档同步。

## 下一步建议

优先不要重跑 200ep。下一步应：

1. 远程对 `ddpm_ct28_200ep/best.pt` 执行 sample，生成 `samples.npy` 与 `samples_continuous.npy`。
2. 用同一 test set `/home/user/HXL/HY7_planb/phase2/slices_ct28_128/test.npy` 跑 eval_v2 与 threshold calib。
3. 将轻量结果放入 `experiments/花页7_PlanB_记录/phase2/m7v3_200ep/`。
4. 再判断 Euler/S₂/连通簇是否相对 50ep 改善，决定是否转 B1 灰度介质生成。

## 子agent回传后的追加处理（2026-07-01）

后台本地文档审计 agent 返回后，已继续处理其中仍有效的项：

- 已将 `CLAUDE.md` 中入口摘要的 `T*=0.9873` 改为 `T*=0.98732`，并把 `S₂ rmse` 与 Euler 数值改为更精确的 `0.07143→0.00242`、`207.92→127.33`。
- 已将 `configs/phase2_m7v2.example.json` 的 `reported_T_star_from_M7v2_note` 改为 `0.98732`。
- 子agent指出的 `ct28_tiles`、`z-step <TODO>`、`bs <TODO>`、`sample-every <TODO>`、`planned_or_running_TBD` 等项此前已在本轮同步中清理。
- 子agent提到的工程根“旧路径”不作为错误处理：`/Users/hxl/Documents/claude` 是指向 `/Users/hxl/Documents/Hermes工作区/01_Claude接管剩余工作/claude` 的符号链接，两者当前都可用；文档中优先保留 `/Users/hxl/Documents/claude` 作为兼容入口。
- `configs` 中远程 `output_directory_T0` 暂未改成本地路径：该 config 表示远程正式运行口径；本地归档路径已在 `output.local_review_artifacts_expected` 与 REPRODUCE/docs 中说明。

## 多模型复核后的轻量修正（2026-07-01）

本轮又用 Claude4.8、DeepSeek v4 Pro、GPT5.5 对审计包复核；三者均给出 PASS，无 P0 阻塞。GLM5.2 调用因 OpenRouter 401 失败，失败记录另存于多模型复核目录。根据三模型共同指出的问题，已继续做轻量修正：

- `experiments/WEIGHTS_MANIFEST.md`：将 M7 50ep `samples.npy`、`samples_continuous.npy`、`slices_ct28_128/meta.json` 的 status 从 `needs_*` 改为 `known_remote_verified_20260701`；更新过时的“待补命令清单”和 `samples_continuous.npy` 口径警告。
- `docs/environment-remote.md`：把“TODO 补环境快照”改为已保存 `remote_provenance_20260701/04_environment_snapshot.txt`；修复重复的 `## 7` 标题为 `## 8`。
- `notes/00_研究主线路线图与任务分解.md`：updated 改为 2026-07-01；“现在”改为 2026-07-01；M7-v2 指标精度对齐到 T*=0.98732、S₂ 0.07143→0.00242、Euler 207.92 vs 127.33。

仍保留为后续事项：

- `notes/22` 与少数历史/工程笔记中仍可能有四舍五入值（0.9873 等）；不影响执行，但若追求全库精度一致，可再清。
- `configs/phase2_m7v2.example.json` 中远程输出目录保留远程正式运行口径；本地归档路径在 `output.local_review_artifacts_expected` 中说明。
