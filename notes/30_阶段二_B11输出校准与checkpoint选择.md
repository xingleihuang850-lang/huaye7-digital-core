# 30｜B1.1 输出校准补查与 checkpoint 选择结论

日期：2026-07-03

## 1. Workflow 状态

本节点执行用户要求：

> B1.1 采样/输出校准补查 + 最小训练改造方案落地；运行后调用 Claude 4.8 核验，再由 GPT-5.5 综合下一步。

本笔记先记录真实运行证据和 GPT-5.5 初步读数，后续 Claude 4.8 复核结论另行补入。

代码提交：

```text
ff6c1bc feat(phase2): add B1 gray train-moments calibration
```

证据目录：

```text
experiments/花页7_PlanB_记录/phase2/b1_gray_sus/b11_output_calib_20260703/
```

远程源目录：

```text
hy7-linux:/home/user/HXL/HY7_planb/phase2/b1_gray_sus_b11_output_calib_20260703/
```

## 2. 本轮做了什么

新增 `hy7_phase2_ddpm.py sample` 输出校准选项：

```text
--intensity-calibration train-moments
--calibration-data <dataset_dir>
```

语义：对 gray sample 做输出后处理，把 generated gray 的 mean/std 仿射匹配到 `calibration-data/train.npy` 的 mean/std。注意：该校准只使用 train split 统计，不使用 test gray 分布；但它仍是显式后处理，不属于纯生成质量。

测试：

```text
11 passed in 0.34s
```

## 3. 运行 variants

| variant | checkpoint | 输出校准 |
|---|---|---|
| best_none | `best.pt` | 无 |
| best_train_moments | `best.pt` | 匹配 train mean/std |
| final_none | `final.pt` | 无 |
| final_train_moments | `final.pt` | 匹配 train mean/std |

## 4. 灰度统计

| variant | mean | std | p6.4 | mean shift vs train | mean shift vs test512 |
|---|---:|---:|---:|---:|---:|
| best_none | -0.4319 | 0.3733 | -0.9749 | -0.3393 | -0.3330 |
| best_train_moments | -0.0947 | 0.3670 | -0.6365 | -0.0021 | 0.0042 |
| final_none | -0.1344 | 0.4738 | -0.8511 | -0.0418 | -0.0355 |
| final_train_moments | -0.0926 | 0.3739 | -0.6582 | ~0.0000 | 0.0063 |

关键发现：

1. `best.pt` 的强暗移复现：mean=-0.4319。
2. `final.pt` 原始输出暗移显著较小：mean=-0.1344，接近 train/test，但 std 更大。
3. train-moments 校准可以修正一维 mean/std，但这不自动带来拓扑或 nnUNet 指标改善。

## 5. nnUNetv2-2d 下游结果

| variant | φ gen | S₂ rmse | Euler gen | maxCC gen |
|---|---:|---:|---:|---:|
| best_none | 20.649% | 0.05097 | 150.65 | 0.0804 |
| best_train_moments | 3.777% | 0.00584 | 115.14 | 0.1003 |
| final_none | 10.989% | 0.01808 | 124.52 | 0.0680 |
| final_train_moments | 5.601% | 0.00220 | 91.21 | 0.0823 |

真实参考：φ=6.405%、Euler=127.33、maxCC=0.0597。

## 6. 初步解释

### 6.1 输出校准不是 B1.1 解法

`train-moments` 可以修正 mean/std，但：

- `best_train_moments`：φ 太低、S₂ 仍差、maxCC 更差；
- `final_train_moments`：φ 接近真实、S₂ 接近门槛，但 Euler 崩到 91.21、maxCC 仍偏。

因此，train mean/std 输出校准不能作为 B1.1 主方案，只能作为诊断工具。

### 6.2 checkpoint 选择比预期更关键

`best.pt` 是按 `L_simple` 最低选择的，但它的下游 nnUNet 指标很差。

`final.pt` 虽然不是 best L_simple，却给出更好的拓扑相关指标：

```text
final_none Euler=124.52，接近 real 127.33
final_none maxCC=0.0680，接近阶段门槛 0.07
```

但 final_none 的 φ 和 S₂ 仍明显不合格：

```text
φ=10.989%，S₂ rmse=0.01808
```

这说明：

```text
L_simple 不能作为 B1/B1.1 唯一 checkpoint 选择指标。
```

## 7. 对 B1.1 的影响

B1.1 不应只改输出校准，也不应只加 epoch。下一步更合理的是：

1. 在训练过程中保存周期性 checkpoint；
2. 每 10ep 对小样本做 validation sampling；
3. 对每个 checkpoint 计算：
   - gray mean/std/KS；
   - threshold φ≈6.0/6.4 下的 S₂/Euler/maxCC；
   - 必要时加 nnUNet 小样本 proxy；
4. 用多目标指标选择 checkpoint，而不是只看 `L_simple`。

## 8. Claude 4.8 复核结论

复核会话：`20260704_094315_2c2c77`（`custom:dk-claude / claude-opus-4-8`）。

判定：

```text
PASS
```

Claude 4.8 认可本笔记的主结论：

1. `train-moments` 校准可以修一维 mean/std，但不能修拓扑，甚至会恶化拓扑：`best_train_moments maxCC=0.1003`、`final_train_moments Euler=91.21`。
2. `final_none` 的 `Euler=124.52`、`maxCC=0.0680` 最接近真实参考，但 `φ=10.989%`、`S₂=0.01808` 不合格；说明 `L_simple` 不是下游数字岩心质量的可靠代理指标。
3. 下一步应先消除 checkpoint 选择变量：做 `metric-aware checkpoint selection + periodic validation sampling`；暂不上复杂结构 loss，暂不转 B2。

Claude 4.8 额外指出一个机制解释：`final_train_moments` 的动态范围被 affine 压到约 `[-0.776, 0.803]`，改变了阈值邻域的形态学，因此出现 φ/S₂ 接近但 Euler 崩塌的结果。这进一步支持：`train-moments` 只能作为诊断/显式后处理，不能作为纯生成质量或 B1.1 解法来报告。

## 9. B1.1 下一步执行 gate

本轮已在代码侧起步加入最小 metric-aware 评分函数：

- `src/hy7_phase2_ddpm.py::score_checkpoint_metrics`
- `src/hy7_phase2_ddpm.py::select_metric_aware_checkpoint`
- 测试：`tests/test_hy7_phase2_ddpm_metric_selection.py`
- 当前四 variant 诊断输出：`experiments/花页7_PlanB_记录/phase2/b1_gray_sus/b11_output_calib_20260703/b11_metric_selection_probe.json`

B1.1 下一步应改为：

```text
metric-aware checkpoint selection + periodic validation sampling
```

本轮继续把训练期 periodic validation sampling 的本地框架落到 `hy7_phase2_ddpm.py train`：

```text
--save-every 10
--eval-every 10
--eval-n <small_n>
--eval-gray-test test.npy
--eval-real test_pore.npy
--eval-porosity-targets 6.0,6.4
--select-metric composite
```

已实现的轻量指标：

- 每 `save_every` 存 `ckpt_epXXX.pt`；
- 每 `eval_every` 对当前 checkpoint 生成小样本 gray；
- gray mean/std/min/max + two-sample KS；
- lower-tail threshold 到预注册 φ 目标（默认 6.0/6.4）；
- pore proxy：φ、S₂ RMSE、Euler、maxCC；
- 调用 `score_checkpoint_metrics` / `select_metric_aware_checkpoint` 写出 `validation_epXXX.json` 与 `periodic_validation_summary.json`。

本地验证：`python3 -m pytest tests -q` → `18 passed in 0.09s`；另用 `/var/folders/.../T/hermes-verify-*.py` 临时脚本完成 ad-hoc verification，并已清理脚本。

执行前先固定以下 gate，避免看结果后调参：

1. 披露验证样本量 `n` 与逐张方差/CI；当前四个 variant 的均值差异不能直接替代稳定性判断。
2. 预注册 held-out validation slices、checkpoint 网格（如每 10ep）、多目标打分公式与权重。
3. 统一 real/gen 评估代理：若 gen 走 nnUNet，real 参考也应明确是同一 nnUNet 代理或清楚标注为 GT 口径，避免混合口径比较。
4. 设现实止损门槛：例如 `maxCC ≤ 0.070` 且 `Euler ∈ real±15%`。如果 metric-aware selection 后 maxCC 仍系统偏高，再触发结构 loss / B1.1 结构改造；不是现在直接跳 B2。

先不急着设计复杂结构 loss；因为本轮已经证明同一 50ep run 的 best/final 差异很大，说明 checkpoint selection 本身就是未解决变量。

## 10. B1.1 periodic50 正式小规模周期验证结果（2026-07-05）

用户要求：正式运行 B1.1 小规模周期验证，配置为 `base=64, bs=64, epochs=50, eval_every=10, eval_n=16`，用多个 `validation_epXXX.json` 做 checkpoint 选择。

远程运行目录：

```text
hy7-linux:/home/user/HXL/HY7_planb/phase2/ddpm_ct28_gray_b11_periodic50_20260705/
```

本地证据目录：

```text
experiments/花页7_PlanB_记录/phase2/b1_gray_sus/b11_periodic50_20260705/
```

本地分析文件：

```text
analysis_b11_periodic50.md
analysis_b11_periodic50.json
```

运行环境与参数：

```text
torch 2.8.0+cu129; cuda=True; diffusers 0.38.0
train.npy (16600,128,128) float32 [-1,1]
test.npy (4150,128,128) float32 [-1,1]
test_pore.npy (4150,128,128) uint8 {0,1}
base=64, bs=64, epochs=50, lr=1e-4, amp=True, seed=42
save_every=10, eval_every=10, eval_n=16, sample_mode=gray
```

训练日志摘要：

```text
[ep   1] L_simple=0.0865  76.3s
[ep  35] L_simple=0.0446  76.4s  # best loss
[ep  50] L_simple=0.0457  76.4s
[eval ep  50] selected=6.400% score=0.2527 pass=True
[done] best L_simple=0.0446
END 2026-07-05T01:34:25+08:00
```

Checkpoint validation 汇总（当前轻量 proxy 口径）：

| epoch | pass | score | φ | S₂ rmse | Euler | maxCC | gray mean | gray KS | selected φ |
|---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | False | 101.1711 | 6.000 | 0.00488 | 80.25 | 0.0052 | -0.1351 | 0.1055 | 6.0 |
| 20 | False | 105.4390 | 6.000 | 0.01226 | 67.12 | 0.0194 | 0.3097 | 0.4473 | 6.0 |
| 30 | False | 102.3396 | 6.000 | 0.00711 | 76.94 | 0.0090 | -0.1544 | 0.1098 | 6.0 |
| 40 | True | 0.8802 | 6.000 | 0.00191 | 108.12 | 0.0061 | -0.1598 | 0.0973 | 6.0 |
| 50 | True | 0.2527 | 6.400 | 0.00123 | 122.50 | 0.0038 | 0.1081 | 0.2415 | 6.4 |

当前选择：`ckpt_ep050.pt`。理由：在预注册的 gated composite score 中通过 gate，且 score 最低；φ=6.400%、S₂ rmse=0.00123、Euler=122.50，明显优于 ep10/20/30，并优于 ep40 的综合分数。

重要限制：本轮 `metric_target.maxcc` 来自 `binary_pore_metrics(real_pore, real_pore)` 的同一轻量 2D proxy，数值为约 0.00415；它不同于 notes/27 中旧口径真实参考 maxCC≈0.0597。因此本轮 `maxCC=0.0038` 只能说明在当前轻量 proxy 内接近 reference，不可直接写成“已达到旧口径 maxCC 0.0597”。后续若要进入论文/主结论，必须用与 notes/27 同一正式评估口径复算 ep50（以及必要的 ep40）并报告 CI/方差。

初步判断：periodic checkpoint selection 是有效变量控制；ep50 是当前小样本 proxy 下最佳 checkpoint。但 gray mean/KS 在 ep50 反而不如 ep40，说明“拓扑/阈值 proxy 最优”和“一维灰度分布最优”并不一致。下一步不应直接宣称 B1.1 解决，应对 `ckpt_ep050.pt` 做更大样本正式采样/评估（至少 n=512 或沿用 B1 cheap50 的正式 threshold/nnUNet/qmatch 评估口径），同时把 ep40 作为对照。

证据 sha256：

```text
f697917f94c0dbddb4df9c3e12393a13e5dc07085c6ca6b3585996c57f1e1d23  validation_ep010.json
e5bc7d4af0586112c24266d09bdda4f2b29afd566d5237cce7666c4aee902a33  validation_ep020.json
d3076ac88dfe1f8f1508b58cc070946156bd128e9724bedc1adbcf9787671eaf  validation_ep030.json
16ffba8f16d9b1496530ef0c63b07fa745ccfe9b9551f49ec469afba0ff708a8  validation_ep040.json
213aaadb1150964829c24c75271214798519104a7cb3d515938762fef96402f8  validation_ep050.json
512cc69de5f1e666c95e3baa75ab87e2c403b8f8eff8cd25c36149b877a73e69  periodic_validation_summary.json
1211301983ae07042822c401557176e6012dac41d1824ca8abc83d52a1db2042  train_meta.json
36f238e4120dc7022af89a70b2c91f09b8e972f650d553be4ecd9566cc66bb22  analysis_b11_periodic50.json
e46413ad771474355b5555ff0014b5bcb73b6ff45c4a25ef70ffe7b5a44fdf75  analysis_b11_periodic50.md
```

## 11. B1.1 ep050/ep040 正式 n=512 复评结果（2026-07-05）

承接 §10 的小样本 checkpoint selection：对 `ckpt_ep050.pt` 做正式 `n=512` gray sampling，并把 `ckpt_ep040.pt` 作为对照；沿用 B1 cheap50 口径跑 threshold φ=5–8% sensitivity、qmatch diagnostic、nnUNet 下游、gray power spectrum / autocorr。

远程运行目录：

```text
hy7-linux:/home/user/HXL/HY7_planb/phase2/b1_gray_sus_b11_formal_eval_20260705/
```

本地证据目录：

```text
experiments/花页7_PlanB_记录/phase2/b1_gray_sus/b11_formal_eval_20260705/
```

核心汇总文件：

```text
formal_eval_summary.md
formal_eval_summary.json
formal_eval_pre_nnunet_report.json
nnunet_eval_summary.json
threshold_sensitivity_summary.csv
formal_eval_gray_structure.png
```

### 11.1 Threshold φ=6.4 与 best-S₂ 口径

| variant | φ target | φ | S₂ rmse | Euler | maxCC | best S₂ target | best S₂ |
|---|---:|---:|---:|---:|---:|---:|---:|
| ep040_orig | 6.4 | 6.400 | 0.00335 | 106.36 | 0.0725 | 5.5 | 0.00185 |
| ep040_qmatch | 6.4 | 6.742 | 0.00429 | 109.04 | 0.0734 | 5.5 | 0.00187 |
| ep050_orig | 6.4 | 6.400 | 0.00636 | 104.73 | 0.0699 | 5.0 | 0.00337 |
| ep050_qmatch | 6.4 | 6.742 | 0.00741 | 107.44 | 0.0703 | 5.0 | 0.00355 |

解释：正式 n=512 后，§10 小样本 proxy 选出的 ep050 并未在正式 threshold 口径下保持优势。ep040 的 S₂ 更好，但 Euler 仍偏低、maxCC 在 0.072–0.073，未明显优于 B1 cheap50 的结构偏差平台；ep050 的 maxCC 略低（约 0.070），但 S₂/Euler 更差。

### 11.2 nnUNet 下游口径

| variant | φ | S₂ rmse | Euler | maxCC |
|---|---:|---:|---:|---:|
| ep040_orig | 11.493 | 0.01652 | 145.57 | 0.0647 |
| ep040_qmatch | 5.404 | 0.00165 | 101.95 | 0.0725 |
| ep050_orig | 4.704 | 0.00293 | 95.07 | 0.0630 |
| ep050_qmatch | 5.111 | 0.00223 | 102.25 | 0.0609 |

解释：qmatch 对 nnUNet 的 φ/S₂ 有帮助，但 Euler 仍低（约 102），没有修复拓扑。ep040_orig 出现 φ=11.493%、S₂=0.01652 的过分割/域偏移；qmatch 后 S₂ 最好但 maxCC/Euler 仍不达标。ep050_qmatch maxCC 最接近 real 0.060，但 φ 偏低、Euler 偏低，不能作为“解决 B1.1”的证据。

### 11.3 Gray distribution / 频谱结构

| variant | mean | std | KS vs real | Wasserstein | low freq | mid freq | high freq |
|---|---:|---:|---:|---:|---:|---:|---:|
| ep040_orig | -0.1616 | 0.4275 | 0.1137 | 0.0833 | 0.4940 | 0.3920 | 0.1133 |
| ep040_qmatch | -0.0989 | 0.3539 | 0.0020 | 0.0004 | 0.5004 | 0.3885 | 0.1104 |
| ep050_orig | 0.0832 | 0.4404 | 0.2190 | 0.1824 | 0.3808 | 0.4712 | 0.1471 |
| ep050_qmatch | -0.1022 | 0.3446 | 0.0191 | 0.0036 | 0.3891 | 0.4674 | 0.1426 |

解释：qmatch 成功修正一维灰度分布，但不自动修复拓扑。ep040 低频比例仍高（约 0.50），类似此前“结构偏软/低频偏强”的问题；ep050 的频谱更偏中高频，但 threshold/nnUNet 的 Euler 反而更低，说明简单追求频谱比例也不能替代拓扑评价。

### 11.4 当前判断

1. `ckpt_ep050.pt` 是 §10 小样本 validation proxy 的最佳 checkpoint，但正式 `n=512` 复评不支持它成为最终 B1.1 最佳结论。
2. `ckpt_ep040.pt` 在正式 threshold 与 qmatch+nnUNet 的 S₂ 上更好，但 Euler 仍约 100–109，低于真实约 127；maxCC 也在 0.072 左右，仍接近旧问题平台。
3. `qmatch` 仍应定位为诊断性强度标定：能修一维分布与部分 S₂/φ，但不能修拓扑；不能作为纯生成质量证据。
4. 本轮说明“periodic validation sampling + metric-aware checkpoint selection”有助于发现 checkpoint 差异，但当前轻量 proxy 不足以替代正式评估；小样本 ep50 选择在正式 n=512 中未复现为最优。
5. 不建议直接转 B2，也不建议立刻 100/200ep scaling；下一步更合理的是改进 validation metric，使训练期选择指标与正式口径一致（例如 eval_n 增大、补充正式 S₂/Euler/maxCC 口径或小规模 nnUNet proxy），并考虑结构/topology-aware 改造。

### 11.5 证据 sha256（关键汇总）

```text
c4d15beced4a60d3d6eaf0edc74f00a8bcb3d13b69ce34b9e23e1b305af927c3  formal_eval_summary.json
bf0461258892211f5ffdf39d80a1bf7b2352aa8dbe071410633bd822388da037  formal_eval_summary.md
63314425a900484d5e770a45a20b32519798698387fa1587a3c14c74a4fd997b  nnunet_eval_summary.json
9e722658ae722cbe035d9fcca90917095884100d21f50772386caddf9c102f82  threshold_sensitivity_summary.csv
23403291264371d7810b10b372a717c58bb8ed9afdb894950597e9565ddf800c  formal_eval_pre_nnunet_report.json
```

## 12. B1.1 失败边界与改造需求（进入 B2 前的 gate）

本节用于防止从 B1.1 直接跳到 B2 或无依据扩大训练。基于 §10–§11 的真实证据，B1.1 当前不是“训练不够久”的单一问题，也不是 qmatch 后处理能解决的问题；核心失败边界是：灰度强度/局部 S₂ 可以被改善，但 Euler 与 connected-component topology 仍未稳定闭合。

### 12.1 已确认的失败边界

1. **训练期小样本 proxy 不足以替代正式评估。**  
   `eval_n=16` 的 periodic validation 在 §10 中选择 `ckpt_ep050.pt`，但正式 `n=512` 复评显示 ep050 在 threshold S₂/Euler 上不优于 ep040：ep050 φ=6.4 时 S₂=0.00636、Euler=104.73；ep040 φ=6.4 时 S₂=0.00335、Euler=106.36。这说明当前 checkpoint selection metric 与正式评价口径不一致。

2. **qmatch 是诊断性强度标定，不是拓扑修复。**  
   qmatch 能把灰度一维分布对齐到 real（例如 ep040_qmatch KS=0.0020、Wasserstein=0.0004），但 nnUNet/threshold 的 Euler 仍约 100–109，低于真实约 127；因此不能把 qmatch 后的 φ/S₂ 改善写成纯生成质量或 topology closure。

3. **S₂ 改善和 Euler/maxCC 改善不一致。**  
   ep040_qmatch 在 nnUNet 下游 S₂=0.00165，但 Euler=101.95、maxCC=0.0725；ep050_qmatch 的 maxCC=0.0609 最接近 real，但 Euler=102.25、φ=5.111 且 S₂=0.00223。单一指标最优不等于数字岩心结构闭合。

4. **频谱比例不是充分的拓扑代理。**  
   ep050 的 low-frequency 比例低于 ep040，中高频比例更高，但 Euler 并未改善；说明简单降低低频/提高高频不能替代 connected-component/Euler 目标。

5. **当前 B1.1 不能宣称达标。**  
   现有最佳组合仍未同时满足：S₂ ≤ 0.002–0.003、Euler ∈ [120,135]、maxCC ≤ 0.07 且 φ 接近 6.4%。因此阶段二仍处于 B1.1 改造门，不能作为最终生成式数字岩心证据直接推进。

### 12.2 A：训练期 validation metric 修正方案

目标：让训练期 checkpoint selection 更接近正式 n=512 口径，避免再次出现“小样本 ep50 最优、正式复评不最优”的分歧。

#### A1. 增大 eval_n 并固定抽样协议

- 将正式小周期验证的 `--eval-n` 从 16 增大到 **64 或 128**；若显存/时间允许，优先 128。
- 固定 sampling seed list，而不是每个 checkpoint 只用一个随机 seed；建议：`seed=[123, 124, 125, 126]` 或固定 64/128 样本一次性生成。
- `validation_epXXX.json` 需要记录：`eval_n`、`seed`、sample hash、每张 tile-level φ/Euler/maxCC 分布摘要，而不只记录均值。

#### A2. checkpoint selection 不能只用当前轻量 proxy

现有 `binary_pore_metrics()` 是轻量 2D proxy，可保留用于快速筛选，但不能作为唯一选择指标。下一版 `periodic_validation_summary()` 应至少输出两层结果：

```text
fast_proxy: 当前轻量 φ/S₂/Euler/maxCC
formal_proxy: 与 src/hy7_phase2_eval.py 口径一致的 n=64/128 评估摘要
```

选择规则应改为：

1. 先按 formal_proxy gate 过滤；
2. gate 内再按 composite score 排序；
3. 若 fast_proxy 与 formal_proxy 排名冲突，标记 `needs_formal_resample=true`，不自动认定最佳。

#### A3. 更接近正式口径的 S₂/Euler/maxCC

训练期 validation 需要与 B1 cheap50 的正式评估函数对齐：

- 直接调用或复用 `src/hy7_phase2_eval.py` 的 S₂/Euler/connectivity 逻辑；
- `rmax=48`、`n=64/128`、`seed=0`；
- threshold φ targets 保持 `[5.0, 5.5, 6.0, 6.4, 7.0, 7.5, 8.0]`，不只看 6.0/6.4；
- 输出 best-S₂ target、φ=6.4 target、以及 gate target 三套摘要，避免只报告最有利口径。

建议 gate：

```text
S₂ rmse ≤ 0.003 for threshold formal_proxy
Euler ∈ [120,135] or at least ≥115 with monotonic improvement evidence
maxCC ≤ 0.070
φ ∈ [5.8, 6.8] for φ=6.4 target口径
```

#### A4. 小规模 nnUNet proxy / 复核机制

nnUNet 很慢，不一定每 10ep 都跑全量，但必须有分歧复核机制：

- 每 20ep 或候选 top-2 checkpoint 运行 `nnUNet proxy n=64/128`；
- 或者当 fast_proxy 与 formal_proxy 排名不一致、或 gray KS/S₂/Euler 指向不同 checkpoint 时，触发 nnUNet 小样本复核；
- 对 real reference 使用同一 nnUNet/threshold 代理口径，避免混合 GT 与预测口径。

建议新增字段：

```json
{
  "selection_status": "accepted|needs_formal_resample|rejected",
  "fast_proxy_rank": 1,
  "formal_proxy_rank": 2,
  "nnunet_proxy_required": true,
  "reason": "fast/formal metric disagreement"
}
```

### 12.3 B：B1.1 topology-aware 改造方向

目标不是 qmatch 后处理，也不是单纯加 epoch；目标是在保持 S₂ ≤0.002–0.003、maxCC ≤0.07 的同时，把 Euler 从当前 100–109 拉回 120–135。

#### B1. 先做 loss 外 validation，不立即引入重型不可导拓扑 loss

Euler/connected components 对二值阈值不可导，直接加到 DDPM loss 风险高。第一步应把 topology-aware 作为 **model selection / sampling selection / validation gate**，不是马上塞进训练 loss：

- 用更强 validation metric 选择 checkpoint；
- 对同一 checkpoint 多 seed 采样，选择满足 topology gate 的 seed/ensemble；
- 若多个 checkpoint/seed 都无法进入 Euler 目标，再进入 loss/数据改造。

#### B2. 结构/topology-aware 训练改造候选

若 validation 修正后仍失败，优先级如下：

1. **多尺度结构统计正则（低风险）**  
   在训练或 fine-tune 中加入灰度域结构统计约束，例如 patch-level autocorr / spectrum matching / gradient energy matching，目标是约束孔隙簇尺度，而不是只对齐一维直方图。

2. **soft pore proxy 正则（中风险）**  
   用固定灰度阈值或可微 sigmoid lower-tail proxy 构造 soft pore probability，对 batch-level φ、soft S₂ 加弱正则；避免直接 Euler loss。示意：

   ```text
   p_pore = sigmoid((t_phi - gray) / tau)
   L = L_simple + λ_s2 * L_softS2 + λ_phi * L_phi
   ```

   其中 `t_phi` 只能来自 train split，不使用 test 分布；λ 从很小开始，先 cheap run。

3. **连通性惩罚的替代 proxy（中高风险）**  
   不能直接对 connected components 反传，可用局部 blob-size proxy / distance-transform-like smoothness / skeleton density proxy 做间接约束。必须先 spike，不直接进正式主线。

4. **数据/目标改造（高优先级但需重新设计）**  
   如果灰度单通道始终不能稳定闭合拓扑，再考虑 `[sus,pore]` 联合生成或条件生成，但这才是 B2 触发前的最后一步，不应现在直接跳。

#### B3. B1.1 改造验收门槛

cheap 改造 run 的最低验收：

```text
threshold formal_proxy:
  S₂ rmse ≤ 0.003
  Euler ≥115 且向 120–135 接近
  maxCC ≤0.070
  φ ∈ [5.8,6.8]

nnUNet/qmatch diagnostic:
  qmatch 后 S₂ ≤0.0025
  Euler ≥115
  maxCC ≤0.070
  不把 qmatch 作为纯生成质量，只作为诊断/下游稳定性
```

若 cheap 改造达到趋势改善，再跑 100/200ep scaling；若没有趋势改善，再考虑 B2 `[sus,pore]` 联合生成。

### 12.4 C：进入 B2 前必须满足的决策 gate

在动 B2 前，必须先完成以下三项，否则路线会从“B1.1 未解释清楚”跳到“B2 新复杂度”：

1. **写清失败边界。**  
   本节即为当前失败边界：B1.1 强度/局部 S₂ 可改善，但 Euler/maxCC 未稳定闭合；当前小样本 validation metric 与正式口径不一致。

2. **修正 validation metric 并复跑一次 cheap 周期验证。**  
   至少用 `eval_n=64/128 + formal_proxy + 分歧复核机制` 复跑小周期，确认 checkpoint selection 不再被 n=16 噪声误导。

3. **完成一个最小 topology-aware 改造 cheap run。**  
   先用低风险结构统计/soft pore proxy，不直接上 B2。只有在该 cheap run 仍不能把 Euler 拉向 ≥115 且 maxCC≤0.070 时，才触发 B2。

B2 触发条件建议写成：

```text
IF validation metric 已修正
AND topology-aware B1.1 cheap run 仍无法同时满足 S₂≤0.003、Euler≥115、maxCC≤0.070
THEN 转 B2 [sus,pore] 联合生成 / 条件生成
ELSE 继续 B1.1 scaling 或细化
```

当前结论：**先修 validation，再做 topology-aware B1.1 cheap 改造；暂不转 B2，暂不跑 100/200ep。**

## 13. validation metric 修正与 formal64 cheap 周期验证启动（2026-07-05）

已完成第一步“先修 validation metric”的代码修改：

```text
src/hy7_phase2_ddpm.py
```

新增/调整要点：

1. 保留历史 `fast_proxy`，但新增 `formal_proxy`：
   - `formal_binary_pore_metrics()` 使用与 `src/hy7_phase2_eval.py` 一致的 FFT radial S₂、skimage Euler(connectivity=1)、maxCC/total-pore semantics；
   - `periodic_validation_summary(..., formal_proxy=True, formal_rmax=48)` 会同时输出 `fast_proxy` 与 `formal_proxy`；
   - top-level `selected` 在 formal_proxy 开启时改由 formal 口径选择。
2. 新增 selection diagnostics：
   - `selection_status = accepted | needs_formal_resample | rejected`；
   - fast/formal 选择目标不一致时标记 `needs_formal_resample`；
   - 必要时设置 `nnunet_proxy_required=true`。
3. CLI 新增：

```text
--eval-formal-proxy
--eval-rmax 48
```

测试证据：

```text
local: python3 -m pytest tests -q  -> 19 passed
remote smoke: train --help shows --eval-formal-proxy/--eval-rmax;
remote smoke periodic_validation_summary(formal_proxy=True, rmax=8) 正常输出 selected/status/formal candidates。
```

随后已启动第二步“再跑 B1.1 cheap 周期验证”：

```text
Hermes process: proc_901b38e85cea
remote script: /home/user/HXL/HY7_planb/phase2/run_b11_periodic50_formal64_20260705.sh
remote out: /home/user/HXL/HY7_planb/phase2/ddpm_ct28_gray_b11_periodic50_formal64_20260705
```

本轮参数：

```text
base=64
bs=64
epochs=50
eval_every=10
eval_n=64
eval_formal_proxy=true
eval_rmax=48
porosity_targets=5.0,5.5,6.0,6.4,7.0,7.5,8.0
```

预期产物：`validation_ep010.json` ... `validation_ep050.json`、`periodic_validation_summary.json`、`ckpt_ep010.pt` ... `ckpt_ep050.pt`、`grid_ep*.png`、`train.log`。

### 13.1 formal64 cheap 周期验证完成结果

远程运行已正常结束：

```text
Hermes process: proc_901b38e85cea
END 2026-07-05T16:36:38+08:00
remote out: /home/user/HXL/HY7_planb/phase2/ddpm_ct28_gray_b11_periodic50_formal64_20260705
```

轻量证据已拉回本地：

```text
experiments/花页7_PlanB_记录/phase2/b1_gray_sus/b11_periodic50_formal64_20260705/
```

汇总：

| epoch | formal target | pass | status | score | φ | S₂ | Euler | maxCC | fast target/pass |
|---:|---:|:---:|---|---:|---:|---:|---:|---:|---|
| 10 | 6.0 | False | rejected | 201.4433 | 6.000 | 0.00406 | 84.00 | 0.0950 | 5.0/False |
| 20 | 5.5 | False | rejected | 201.4914 | 5.500 | 0.00447 | 77.58 | 0.0879 | 5.0/False |
| 30 | 7.5 | False | rejected | 101.6752 | 7.500 | 0.01101 | 110.42 | 0.0746 | 7.5/True |
| 40 | 6.0 | False | rejected | 200.9475 | 6.000 | 0.00156 | 95.38 | 0.0859 | 5.5/False |
| 50 | 8.0 | False | rejected | 101.6364 | 8.000 | 0.00871 | 111.03 | 0.0815 | 8.0/True |

结论：

1. **无 checkpoint 通过 formal gate**。所有 `validation_ep*.json` 的 top-level `selected.proxy=formal` 且 `passed_gate=false / status=rejected`。
2. 修正后的 formal_proxy 成功暴露了旧 fast_proxy 的乐观偏差：ep30 与 ep50 在 fast_proxy 下为 pass=True，但 formal_proxy 下仍被拒绝，主要因为 formal maxCC 和/或 Euler/S₂ 不达 gate。
3. ep40 的 S₂ 最好（0.00156），但 Euler=95.38、maxCC=0.0859，拓扑仍失败。
4. ep50 formal score 最低（101.6364），Euler=111.03 接近但仍低于 ≥115/120–135 目标，maxCC=0.0815 超过 ≤0.070，S₂=0.00871 也偏高。
5. 因此“先修 validation metric → 再跑 cheap 周期验证”已经完成，结果明确支持下一步进入 **B1.1 topology-aware cheap 改造**；不应转 B2，也不应直接 100/200ep scaling。

关键证据 sha256：

```text
7b845e6fdf43837f01b3df1d4b6df14ab035d2499ee407becad5fbd6bef7e16a  analysis_formal64.json
663e9ccda3f9f2cf3f80cb047916b7042b14a1cf0777239e32bb3dbd6af9cb73  analysis_formal64.md
e1ed8d94703f472b0022b2af6dc0f7b9ca5567a8e15242d54f6312889d88ec12  validation_ep010.json
f4860895634b69edc72eb44261e5ed63ea153122b9309785735de18d069f4e55  validation_ep020.json
a6ddd2df8b174c8260a10cae9fec098e814c987a3a721c87b31460dd8f1f9a52  validation_ep030.json
51d5efccc493c941a5ae67397ea7630778ea368ccd15769a53c41e6bafbc8309  validation_ep040.json
d215ad81de4ecd7b4fe8c61fe3e12075f4798e01f48411542d88108a92fb6d84  validation_ep050.json
39eb6345af54a68bf3ff198759f6b9dea8064d9fc869d21529a89400c50f74a3  periodic_validation_summary.json
259e8cd0c4a685f668809fc5f8b16218f1a6aa0fabbcbba7b9333b41cb9a5481  train_meta.json
```

## 14. B1.1 soft-pore formal64 失败判定与 B1.1 soft-S₂/φ 线关闭（2026-07-06）

承接 §13.1 的结论，本轮执行进入 B2 前的最小 topology-aware cheap 改造：soft pore φ/S₂ 正则。该实验用于验证“只用 soft φ + soft S₂ 约束，是否能把 formal_proxy 的 Euler/maxCC 拓扑瓶颈补齐”。

远程运行目录：

```text
hy7-linux:/home/user/HXL/HY7_planb/phase2/ddpm_ct28_gray_b11_softpore50_formal64_20260705/
```

运行结束：

```text
END 2026-07-06T00:33:05+08:00
```

关键参数：

```text
epochs=50, bs=64, base=64, eval_every=10, eval_n=64,
eval_formal_proxy=true, eval_rmax=48,
soft_phi_lambda=0.01, soft_s2_lambda=0.05,
soft_pore_phi=6.4, soft_pore_tau=0.08,
soft_s2_lags=1,2,4,8,16, soft_reg_ref_n=512
```

formal_proxy 汇总：

| epoch | selected φ target | pass | status | S₂ rmse | Euler | maxCC |
|---:|---:|:---:|---|---:|---:|---:|
| 10 | 6.0 | False | rejected | 0.00264 | 85.91 | 0.1111 |
| 20 | 5.0 | False | rejected | 0.00771 | 51.16 | 0.1499 |
| 30 | 6.4 | False | rejected | 0.00800 | 67.92 | 0.1533 |
| 40 | 5.5 | False | rejected | 0.00712 | 56.67 | 0.1425 |
| 50 | 5.0 | False | rejected | 0.01761 | 34.56 | 0.1623 |

对照 §13.1 无 soft-pore formal64：ep30 曾达到 Euler=110.42、maxCC=0.0746；ep50 曾达到 Euler=111.03、maxCC=0.0815。soft-pore 后 Euler/maxCC 不仅没有改善，反而显著恶化：ep30 Euler 降到 67.92、maxCC 升到 0.1533；ep50 Euler 降到 34.56、maxCC 升到 0.1623。

### 14.1 判定

```text
B1.1 soft-pore formal64: FAIL
B1.1 soft-S₂/φ topology repair line: CLOSED
```

解释：

1. 本轮无任何 checkpoint 通过预注册 gate：`S₂≤0.003, Euler≥115, maxCC≤0.070`。
2. 这不是“接近过线”的失败，而是方向性恶化；训练越久，Euler/maxCC 越偏离拓扑目标。
3. 当前证据说明 B1.1 的核心瓶颈不是 S₂ 单项，而是 Euler/maxCC connected-component topology closure。
4. 继续只调 `soft_s2_lambda` / `soft_phi_lambda` 不再合理；不应基于该分支做 100/200ep scaling。

### 14.2 rock 多专家复核结论

已用 `digital-rock-gate` 做多模型复核：

```text
provider=moa
preset=digital-rock-gate
refs=openai-codex:gpt-5.5, deepseek:deepseek-v4-pro,
     openrouter:z-ai/glm-5.2, custom:dk-claude:claude-fable-5
aggregator=custom:dk-claude:claude-opus-4-8
```

复核意见一致：soft φ/S₂ 正则没有直接优化 Euler 或 maxCC，且本轮实验证明其会以牺牲拓扑连通性为代价改变结构；因此 soft-pore 线应关闭。

### 14.3 下一步决策

不建议继续 100/200ep scaling；也不建议再做“只调 soft S₂/φ”的 B1.1 变体。

允许的唯一 B1.1 rescue 条件：若能立即实现显式 Euler/maxCC proxy，可做一次 `epochs≤20, eval_n=64, eval_every≤5` 的 rescue cheap run；该 run 必须回到无 soft-pore baseline，`soft_s2_lambda=0` 或极小（≤0.005），并预注册 stop rule：ep10–20 若无 Euler 回升、maxCC 下降趋势，立即终止。

若没有现成 Euler/maxCC proxy，则转入 B2-min。B2-min 不应从 soft-pore 失败模型继续，而应从 §13.1 中最接近 gate 的无 soft-pore baseline checkpoint 出发：

```text
candidate baseline:
  ep30: Euler=110.42, maxCC=0.0746
  ep50: Euler=111.03, maxCC=0.0815
```

B2-min 第一枪建议定义为 topology post-processing / constrained selection：小连通分量裁剪、形态学开闭、孔道桥接或连通性约束选择；每个变体必须回算 formal S₂/Euler/maxCC，只有三指标同时过 gate 才能进入 n=512 formal validation。若 B2-min 后处理无效，再进入 `[sus,pore]` 联合生成或条件生成。

### 14.4 Workflow 状态

```text
B1.1 validation metric 修正：DONE
B1.1 soft-pore topology-aware cheap run：DONE / FAIL
B1.1 soft-S₂/φ 修拓扑方向：CLOSED
Next gate：B2-min 设计，或唯一一次显式 Euler/maxCC proxy rescue cheap run（二选一）
```

## 15. 唯一一次显式 Euler/maxCC proxy rescue cheap run 预注册（2026-07-06）

用户选择执行 §14.3 中允许的唯一一次 B1.1 rescue cheap run。本节点不是继续 soft-S₂/φ 方向，而是验证“显式 Euler/maxCC proxy 是否能在 cheap 预算内给出拓扑改善梯度”。

代码侧新增 CLI：

```text
--soft-euler-lambda
--soft-maxcc-lambda
--soft-maxcc-scales
```

本地测试：

```text
python3 -m pytest tests -q  -> 22 passed
```

远程 smoke：

```text
hy7-linux nnunet_t28: train --help shows --soft-euler-lambda/--soft-maxcc-lambda/--soft-maxcc-scales
TOPO_PROXY_OK: _build_soft_pore_regularizer + _soft_pore_regularization_loss 可反传
```

预注册参数：

```text
out=/home/user/HXL/HY7_planb/phase2/ddpm_ct28_gray_b11_eulermaxcc_rescue20_formal64_20260706
epochs=20
bs=64
base=64
lr=1e-4
seed=42
sample_mode=gray
sample_every=5
save_every=5
eval_every=5
eval_n=64
eval_formal_proxy=true
eval_rmax=48
porosity_targets=5.0,5.5,6.0,6.4,7.0,7.5,8.0
soft_phi_lambda=0.0
soft_s2_lambda=0.0
soft_euler_lambda=0.20
soft_maxcc_lambda=0.50
soft_pore_phi=6.4
soft_pore_tau=0.08
soft_s2_lags=1
soft_maxcc_scales=4,8,16,32
soft_reg_ref_n=512
```

停止/决策规则：

1. 这是 B1.1 最后一次 rescue cheap run；不得再追加“再试一个权重”的 B1.1 变体。
2. 若 ep10–20 未出现 Euler 回升、maxCC 下降趋势，立即关闭 B1.1 rescue，转 B2-min。
3. 趋势改善的最低标准：相对 §13.1 无 soft-pore formal64，至少接近或超过 `Euler≈110` 且 `maxCC≤0.080`；若仍停留在 soft-pore 失败区间（Euler<90 或 maxCC>0.10），判定为无效。
4. 若任一 checkpoint 达到 `S₂≤0.003, Euler≥115, maxCC≤0.070`，也不能直接宣称成功；必须做 n=512 formal validation + nnUNet/disagreement review。
5. 不允许基于该 rescue 直接 100/200ep scaling；只有 n=512 formal validation 通过后才讨论 scaling。

运行已启动：

```text
START 2026-07-06T01:26:34+08:00
remote script=/home/user/HXL/HY7_planb/phase2/run_b11_eulermaxcc_rescue20_formal64_20260706.sh
remote out=/home/user/HXL/HY7_planb/phase2/ddpm_ct28_gray_b11_eulermaxcc_rescue20_formal64_20260706
remote PID=1825670
Hermes monitor=proc_fa421a1a0bb2
```

### 15.1 rescue20 formal64 完成结果

远程运行正常结束：

```text
END 2026-07-06T02:09:36+08:00
```

formal_proxy 汇总：

| epoch | φ target | pass | status | score | φ | S₂ rmse | Euler | maxCC |
|---:|---:|:---:|---|---:|---:|---:|---:|---:|
| 5 | 6.4 | True | accepted | 0.1338 | 6.400 | 0.000169 | 119.08 | 0.0611 |
| 10 | 6.4 | True | accepted | 0.2068 | 6.400 | 0.000326 | 117.11 | 0.0635 |
| 15 | 6.4 | True | accepted | 0.1950 | 6.400 | 0.000284 | 119.23 | 0.0640 |
| 20 | 6.4 | True | accepted | 0.3129 | 6.400 | 0.000664 | 115.30 | 0.0669 |

`periodic_validation_summary.json` 当前选择 `ckpt_ep005.pt@phi6.4`：S₂=0.000169、Euler=119.08、maxCC=0.0611，无 failed gates。

本轮说明显式 Euler/maxCC proxy rescue 在 `eval_n=64 formal_proxy` 下给出了强改善梯度，且所有 checkpoint 均通过预注册 cheap gate。但按 §15 停止/决策规则，这不能直接宣称 B1.1 最终成功；下一步必须对候选 checkpoint（优先 ep005，同时保留 ep010/ep015/ep020 对照）做 n=512 formal validation + nnUNet/disagreement review。

n=512 formal validation 已启动：

```text
START 2026-07-06T11:25:08+08:00
remote script=/home/user/HXL/HY7_planb/phase2/run_b11_rescue20_formal512_20260706.sh
remote out=/home/user/HXL/HY7_planb/phase2/b1_gray_sus_b11_rescue20_formal512_20260706
remote PID=1850115
Hermes monitor=proc_6b9711dc80c4
candidate checkpoints=ckpt_ep005.pt, ckpt_ep015.pt
```

### 15.2 rescue20 n=512 formal validation 完成结果

n=512 采样已完成，但第一次 analysis 内联脚本因字符串索引引号丢失报错：`NameError: name 'mean' is not defined`。采样产物已完整生成，随后只重跑 analysis（未重新采样），生成 `formal512_ep005.json`、`formal512_ep015.json`、`formal512_summary.json/md`。

n=512 formal threshold sensitivity：

| variant | φ target | φ | S₂ rmse | Euler | maxCC | pass |
|---|---:|---:|---:|---:|---:|:---:|
| ep005_orig | 5.0 | 5.000 | 0.00321 | 103.90 | 0.0661 | False |
| ep005_orig | 5.5 | 5.500 | 0.00211 | 109.60 | 0.0639 | False |
| ep005_orig | 6.0 | 6.000 | 0.00098 | 115.11 | 0.0624 | True |
| ep005_orig | 6.4 | 6.400 | 0.00015 | 119.42 | 0.0612 | True |
| ep005_orig | 7.0 | 7.000 | 0.00143 | 124.99 | 0.0605 | False |
| ep005_orig | 7.5 | 7.500 | 0.00269 | 129.50 | 0.0601 | False |
| ep005_orig | 8.0 | 8.000 | 0.00398 | 133.57 | 0.0593 | False |
| ep015_orig | 5.0 | 5.000 | 0.00335 | 105.65 | 0.0682 | False |
| ep015_orig | 5.5 | 5.500 | 0.00228 | 111.75 | 0.0668 | False |
| ep015_orig | 6.0 | 6.000 | 0.00118 | 116.98 | 0.0652 | True |
| ep015_orig | 6.4 | 6.400 | 0.00034 | 120.81 | 0.0641 | True |
| ep015_orig | 7.0 | 7.000 | 0.00121 | 126.64 | 0.0631 | False |
| ep015_orig | 7.5 | 7.500 | 0.00242 | 131.20 | 0.0627 | False |
| ep015_orig | 8.0 | 8.000 | 0.00369 | 135.27 | 0.0625 | False |

灰度分布提示：ep005 gray_mean=0.1929、KS=0.3474；ep015 gray_mean=0.0602、KS=0.2169。ep015 的灰度分布比 ep005 更接近 test gray，但两者仍存在明显分布偏移；这应在 nnUNet/disagreement review 中继续检查。

判定：在 n=512 formal threshold 口径下，ep005 与 ep015 在 φ=6.0 与 6.4 均通过 gate；其中 ep015@φ6.4 的 Euler=120.81、maxCC=0.0641、S₂=0.00034，略优于 ep005 的灰度分布，适合作为下一步主候选；ep005@φ6.4 S₂ 更低且 maxCC 更低，可作为对照。

关键证据 sha256：

```text
c606c06730334d7e6f984c2e2fb165d529b67176845e5070f781eaaf8bd24b5a  formal512_ep005.json
45c565aaa4e7adfee2ddc0e04c882320e03b2d4adf6139d01614fb4073285737  formal512_ep015.json
42d5b06ae697e4c5b1c1711994c11ea4046e160c1e05ae001a14dffd2243093c  formal512_summary.json
dc295491e7a3b15ffa151880b8ee0fffe7c4c895345006860a28b5ac793977f2  formal512_summary.md
```

下一步：对 ep015 与 ep005 做 nnUNet/disagreement review；若 nnUNet 口径未出现反向失败，再调用 `digital-rock-gate` 做 B1.1 阶段性闭合复核。

### 15.3 rescue20 nnUNet/disagreement review 完成结果

nnUNet/disagreement review 已完成，预测变体包括 ep005/ep015 的 ORIG 与 QMATCH。结果显示：ORIG 口径出现反向失败；QMATCH 口径未出现反向失败，且与 threshold φ6.4 的 Dice≈0.95。

| variant | φ | S₂ rmse | Euler | maxCC | Dice vs threshold φ6.4 | IoU | reverse fail |
|---|---:|---:|---:|---:|---:|---:|:---:|
| ep005_orig | 2.178 | 0.00872 | 58.93 | 0.0931 | 0.507 | 0.340 | True |
| ep005_qmatch | 5.787 | 0.00159 | 113.78 | 0.0621 | 0.949 | 0.903 | False |
| ep015_orig | 3.687 | 0.00603 | 88.03 | 0.0743 | 0.731 | 0.576 | True |
| ep015_qmatch | 5.795 | 0.00172 | 116.15 | 0.0651 | 0.950 | 0.905 | False |

解释：

- ORIG nnUNet 对 rescue20 灰度的直接分割偏保守，孔隙率被压低到 2.18%/3.69%，导致 S₂、Euler、maxCC 全部或部分反向失败。
- QMATCH 后 nnUNet 输出与 threshold φ6.4 高度一致（Dice≈0.95、IoU≈0.90），说明反向失败主要来自灰度分布/强度校准，而非生成结构本身完全崩坏。
- ep015_qmatch 满足 Euler≥115、S₂≤0.003、maxCC≤0.070，是 nnUNet 口径下最强候选；但因 ORIG 口径失败，B1.1 不应无条件宣称闭合，必须交给 rock 多专家判断是否按“需 qmatch/calibration 约束”的阶段性闭合。

关键证据 sha256：

```text
b1c3d1988a7b507950b57fc6604a09c5815dbb8315056d9e74b36a08d5c2c724  nnunet_input_manifest.json
5b4251322b0f5665ffc881e751d4f973c66ec60214136940606d19c4d8f1e061  nnunet_disagreement_summary.json
e14b8461c39851ceb9955ab1018624cdced1efa9ba114622be63c1a1cc65e0cb  nnunet_disagreement_summary.md
```

下一步：调用 `digital-rock-gate` 对“formal512 pass + nnUNet ORIG fail/QMATCH pass”的混合证据做 B1.1 阶段性闭合复核。

### 15.4 digital-rock-gate 阶段性闭合复核结论

已用 `digital-rock-gate` 对 §15.2–15.3 的混合证据做正式 MoA 复核。调用口径：

```bash
hermes -z "$(cat /Users/hxl/Documents/Hermes工作区/99_临时文件与一次性输出/rock_b11_closure_mixed_evidence_20260706.md)" --provider moa -m digital-rock-gate
```

聚合结论：B1.1 判为 **Conditional Pass（有条件阶段性闭合）**，不是 full pass，也不是 fail，不直接转 B2。

硬性限定：

- B1.1 闭合只在“后续使用必须包含 qmatch / gray calibration”的前提下成立。
- ORIG raw nnUNet 为 known fail / unresolved risk，不得声称已通过。
- 主候选为 **ep015@φ6.4 / ep015_qmatch**。formal512：S₂=0.00034、Euler=120.81、maxCC=0.0641；nnUNet qmatch：S₂=0.00172、Euler=116.15、maxCC=0.0651、Dice≈0.950、reverse_fail=False。
- ep005 仅保留为 ablation / 对照；ep005_qmatch 的 Euler=113.78 <115，不能作为主通过证据。

下一步最小行动：

1. 冻结 B1.1 topology 侧：冻结 rescue20 proxy 与主候选 ep015，不再做第二次 topology rescue。
2. 将 qmatch / gray calibration 从 ad-hoc review 步骤升级为 documented、版本化、可复现的 inference preprocessing。
3. 在 held-out / 独立 split 上验证 gray calibration 泛化性。
4. rock gate 批准后，B2-min 只能在 calibrated/qmatch pipeline 前提下启动。

明确禁止：

- 禁止声称 B1.1 无条件通过。
- 禁止声称 ORIG nnUNet 已通过。
- 禁止继续改 topology proxy 或做二次 rescue。
- 禁止事后放宽 gate。
- 禁止把 qmatch 当隐式步骤；必须显式化、文档化、版本化。
- 禁止在 qmatch 形式化 + gate 批准前进入 B2 实质工作。

一句话状态：**HY7 B1.1 = conditional pass / 阶段性闭合候选已获 rock 复核支持；主候选 ep015；下一阶段工作从 topology 训练切换到灰度校准 pipeline 形式化与泛化验证。**

### 15.5 qmatch / gray calibration 形式化与 held-out split 泛化验证

已将 qmatch 从 ad-hoc review 步骤升级为版本化 inference preprocessing 模块：

```text
local module=/Users/hxl/Documents/Hermes工作区/01_Claude接管剩余工作/claude/src/hy7_gray_calibration.py
remote module=/home/user/HXL/HY7_planb/phase2/hy7_gray_calibration.py
version=hy7-gray-calibration-qmatch-v1
method=empirical_quantile_match_rank_preserving
raw-intensity mapping=[-1,1] -> [45,205]
```

算法约束：

- 只做 inference preprocessing / gray calibration，不改变 B1.1 topology gate。
- qmatch 使用固定 reference gray `.npy` 的经验 CDF 做 rank-preserving quantile match。
- 支持 `all/even/odd` reference split；`even/odd` 用于 held-out split 泛化检查。
- qmatch 必须显式记录 manifest，包括 version、method、reference_path、reference_split、input/calibrated stats。

代码验证：

```text
python3 -m pytest tests -q
26 passed in 0.10s
```

按 verification hygiene 另做了临时脚本 ad-hoc verification：

```text
/var/folders/l6/qjrw5dps6s96b9ddgnmlbh8m0000gn/T/hermes-verify-*.py
ADHOC_VERIFY_OK
4 passed in 0.02s
```

held-out split 泛化验证（reference split=even/odd）已在 Linux + nnUNet 口径完成：

```text
remote out=/home/user/HXL/HY7_planb/phase2/b1_gray_sus_b11_qmatch_generalization_20260706
```

| variant | φ | S₂ rmse | Euler | maxCC | pass |
|---|---:|---:|---:|---:|:---:|
| ep005_qmatch_even | 5.785 | 0.00159 | 113.74 | 0.0621 | False |
| ep005_qmatch_odd | 5.789 | 0.00159 | 113.84 | 0.0620 | False |
| ep015_qmatch_even | 5.793 | 0.00173 | 116.14 | 0.0651 | True |
| ep015_qmatch_odd | 5.797 | 0.00172 | 116.17 | 0.0651 | True |

判定：qmatch / gray calibration 对 ep015 在 disjoint reference split 下保持稳定通过；这支持 ep015 不是单点偶然通过。ep005 在 even/odd split 下仍因 Euler<115 不通过，继续仅作为 ablation / 对照，不升级为主候选。

关键证据 sha256：

```text
6f8512445c200f43c4a3d71309678a95e06f10aff205b24f8ee65d9c1bbea8c1  qmatch_generalization_manifest.json
4044881ebdd1ad1c3b2a7c4807ddba579ef60e764b12cd44a0c0a48807df1f27  qmatch_generalization_summary.json
72ab5e839918f2fd01ed55d31374fda3ba9251bc45c897a991c0d566379c7a1b  qmatch_generalization_summary.md
```

当前状态：B1.1 topology 已冻结；qmatch/gray calibration 已形式化并通过 held-out split 泛化验证；下一步可准备 calibrated B2-min 设计，但 B2-min 必须显式依赖 `hy7-gray-calibration-qmatch-v1`，且仍不得声称 ORIG raw 已通过。

### 15.6 calibrated B2-min 设计入口

已创建 calibrated B2-min 实施计划：

```text
/Users/hxl/Documents/Hermes工作区/01_Claude接管剩余工作/claude/.hermes/plans/2026-07-06_141348-calibrated-b2-min.md
```

B2-min 入口约束：

- B2-min 从 `ep015` 主候选进入。
- `hy7-gray-calibration-qmatch-v1` 是强制 inference preprocessing 依赖。
- ORIG raw 仍是 known fail，不得作为通过口径。
- B2-min 第一阶段只做 calibrated baseline packaging / reproducibility，不直接启动新训练。
- 若后续做 constrained selection，也必须是无 retraining 的 calibrated selection；不得回到 B1.1 topology rescue。

下一步执行建议：先实现/运行 B2-min packaging baseline，生成 `b2_min_manifest.json`、`b2_min_readme.md`、`hashes.txt`，再决定是否做 constrained selection smoke。

### 15.7 calibrated B2-min baseline package 已生成

已实现本地 packaging 脚本并运行到 Linux：

```text
local script=/Users/hxl/Documents/Hermes工作区/01_Claude接管剩余工作/claude/src/hy7_b2_min_package.py
remote script=/home/user/HXL/HY7_planb/phase2/hy7_b2_min_package.py
remote out=/home/user/HXL/HY7_planb/phase2/b2_min_calibrated_baseline_ep015_20260706
```

本地验证：

```text
python3 -m pytest tests/test_hy7_b2_min_package.py tests/test_hy7_gray_calibration.py -q
6 passed in 0.03s
python3 -m pytest tests -q
28 passed in 0.09s
```

按 verification hygiene 做了临时脚本 ad-hoc verification：

```text
/var/folders/l6/qjrw5dps6s96b9ddgnmlbh8m0000gn/T/hermes-verify-*.py
ADHOC_VERIFY_OK b2_min_package
2 passed in 0.01s
```

B2-min baseline package 内容：

```text
b2_min_manifest.json
b2_min_readme.md
hashes.txt
```

package 摘要：

- status=`calibrated_b2_min_candidate`
- main_checkpoint=`ep015`
- calibration_version=`hy7-gray-calibration-qmatch-v1`
- orig_raw_status=`known_fail`
- formal512 ep015@φ6.4：S₂=0.000340、Euler=120.81、maxCC=0.0641、passed_gate=True
- nnUNet ep015_qmatch：S₂=0.001721、Euler=116.15、maxCC=0.0651、reverse_fail=False
- qmatch generalization：even/odd split 均 pass

package hashes：

```text
27c2cf40476f78e69480ba364011bb86a394a01d99750c8cc3037ec4d04439df  b2_min_manifest.json
6458295a689dbcfc193a3f1774d690ccc6aba0840bee3a232527beb785bff7ae  b2_min_readme.md
658f3ff9f392c609b04b88f53479524a31709d79d14c5591961f624b9921634c  hashes.txt
```

当前状态：calibrated B2-min baseline reproducibility package 已完成；尚未启动任何 B2 新训练。下一步若继续推进，应先做 constrained selection smoke 设计/执行，仍然禁止 retraining 与 ORIG raw 通过声称。

### 15.8 calibrated constrained selection smoke 完成

已实现并运行 B2-min constrained selection smoke。该步骤不做 retraining，只对 frozen `ep015` 的 n=512 gray samples 应用 `hy7-gray-calibration-qmatch-v1`，再按 64-slice chunks + full batch 做 formal metrics 选择。

脚本与测试：

```text
local script=/Users/hxl/Documents/Hermes工作区/01_Claude接管剩余工作/claude/src/hy7_b2_min_select.py
remote script=/home/user/HXL/HY7_planb/phase2/hy7_b2_min_select.py
local test=/Users/hxl/Documents/Hermes工作区/01_Claude接管剩余工作/claude/tests/test_hy7_b2_min_select.py
```

验证：

```text
python3 -m pytest tests/test_hy7_b2_min_select.py -q
3 passed in 0.02s
python3 -m pytest tests -q
31 passed in 0.09s

/var/folders/l6/qjrw5dps6s96b9ddgnmlbh8m0000gn/T/hermes-verify-*.py
ADHOC_VERIFY_OK b2_min_select
3 passed in 0.02s
```

远程输出：

```text
/home/user/HXL/HY7_planb/phase2/b2_min_constrained_selection_smoke_ep015_20260706
```

selection 规则：先要求 `pass_gate=True`，再按 `S₂ rmse`、`abs(Euler-120)`、`maxCC`、`abs(φ-6.4)` 排序；禁止 retraining、二次 topology rescue、gate relaxation、ORIG raw pass claim、implicit qmatch。

候选结果：

| variant | n | φ | S₂ rmse | Euler | maxCC | pass |
|---|---:|---:|---:|---:|---:|:---:|
| ep015_chunk000_063 | 64 | 6.435 | 0.00052 | 123.95 | 0.0716 | False |
| ep015_chunk064_127 | 64 | 6.405 | 0.00033 | 122.09 | 0.0629 | True |
| ep015_chunk128_191 | 64 | 6.458 | 0.00071 | 121.00 | 0.0639 | True |
| ep015_chunk192_255 | 64 | 6.755 | 0.00111 | 120.81 | 0.0647 | True |
| ep015_chunk256_319 | 64 | 6.562 | 0.00179 | 123.59 | 0.0600 | True |
| ep015_chunk320_383 | 64 | 6.598 | 0.00073 | 121.97 | 0.0626 | True |
| ep015_chunk384_447 | 64 | 6.463 | 0.00021 | 121.17 | 0.0643 | True |
| ep015_chunk448_511 | 64 | 6.642 | 0.00059 | 123.61 | 0.0611 | True |
| ep015_all | 512 | 6.443 | 0.00029 | 121.27 | 0.0640 | True |

selected=`ep015_chunk384_447`，理由：通过 gate 且 selection score 最低。

```text
selected phi=6.4629
selected S₂=0.0002107
selected Euler=121.17
selected maxCC=0.0643
```

注意：`ep015_all` 也稳定通过，说明 constrained selection smoke 没有破坏 full-batch 证据；但 chunk 选择只可作为 B2-min smoke / candidate triage，不能替代 full-batch formal/nnUNet gate。

证据 sha256：

```text
40f51bdc04da5c5a373a948f5a874cdda134447f88a257392b0ac8bc96eebae4  selection_summary.json
839851afbc29f2dab8b523f784b89aad9e7e753ad9b054ff9c3e52825d0e764f  selection_summary.md
dc6303f99902e9717f086718397afc4d96e3e495ac8f7f549dabfa617fb071e7  qmatch_manifest.json
```

当前状态：calibrated constrained selection smoke 通过；B2-min 仍未启动任何新训练。下一步如果推进 B2，应先用 rock gate 复核“B2-min baseline package + constrained selection smoke”是否足以进入下一阶段设计。

### 15.9 B2-min gate 复核（remote ordered view 起点）

承接本地清理与远程 `00_ORDERED_VIEW` 建立后的下一步，已从 ordered view 重新复核 B2-min gate。

复核记录：

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/gate_review_20260706.md
```

复核范围：

1. 远程 ordered view 完整性：`LINK_COUNT=42`、`BROKEN_COUNT=0`；`05_b2_min_calibrated/00_baseline_package_ep015` 与 `01_constrained_selection_smoke_ep015` 均可解析到原始远程目录。
2. baseline package：`status=calibrated_b2_min_candidate`、`main_checkpoint=ep015`、`calibration_version=hy7-gray-calibration-qmatch-v1`、`orig_raw_status=known_fail`，证据摘要与已记录 formal512 / nnUNet qmatch / qmatch split 泛化一致。
3. constrained selection smoke：`status=calibrated_constrained_selection_smoke`，9 行候选中 8 行通过 gate；selected=`ep015_chunk384_447`，full-batch `ep015_all` 也通过 gate。
4. 本地测试：`python3 -m pytest tests -q -> 31 passed in 0.12s`。

复核结论：

```text
B2-min gate review = PASS_WITH_CONSTRAINTS
```

允许下一步：用 baseline package + constrained selection smoke 作为证据进入正式 B2-min design / rock gate 复核。若获准，下一阶段仍应以 calibrated/qmatch pipeline 为硬依赖，且默认 no-retraining，除非新的 gate 明确授权训练。

仍然禁止：B1.1 unconditional full pass 声称、ORIG raw nnUNet pass 声称、隐式 qmatch、第二次 B1.1 topology rescue、gate relaxation、用 64-slice selected chunk 替代 full-batch formal/nnUNet gate。

### 15.10 digital-rock-gate 多专家 B2-min design-entry 复核

已按用户要求直接进入 “B2-min baseline package + constrained selection smoke 是否足以开启下一阶段设计” 的 rock gate / multi-expert 复核。

MoA 调用口径：

```text
provider=moa
preset=digital-rock-gate
refs=openai-codex:gpt-5.5, deepseek:deepseek-v4-pro,
     openrouter:z-ai/glm-5.2, custom:dk-claude:claude-fable-5
aggregator=custom:dk-claude:claude-opus-4-8
smoke=OK-ROCK
```

复核输入：

```text
/Users/hxl/Documents/Hermes工作区/99_临时文件与一次性输出/rock_b2_min_gate_review_20260706.md
```

复核记录：

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/rock_gate_review_20260706.md
```

聚合判定：

```text
B2-min design-entry gate = CONDITIONAL_PASS
```

判定含义：baseline package + full-batch control 的 constrained selection smoke **足以开启 B2-min 设计**，但这只是 design-entry 级别，不是 B2-min 结果验收。有效域限定在 `ep015 + hy7-gray-calibration-qmatch-v1 + no-retraining + explicit qmatch`。

允许行动：

1. 撰写 B2-min design memo，定义目标、组件分解、验收 gate、失败回退路径、forbidden claims。
2. 继续 no-retraining calibrated selection / packaging 的设计与审计固化，只限现有 artifacts。
3. 设计下一 B2 component 的最小实验卡 / dry-run，不触发训练。
4. 将 baseline package 作为 frozen reference，后续可补 pin commit / schema / ordered-view / qmatch explicitness / forbidden-claim lint。

禁止行动：

1. 不得声称 B1.1 unconditional full pass 或 ORIG raw passed。
2. 不得 implicit qmatch；所有 downstream path 必须显式声明 `hy7-gray-calibration-qmatch-v1`。
3. 不得第二次 B1.1 topology rescue、gate relaxation、100/200ep scaling、新训练或新 checkpoint。
4. 不得用 selected chunk (`ep015_chunk384_447`, n=64) 替代 full-batch formal/nnUNet gate；B2-min 阈值必须锚定 full-batch `ep015_all`，不是 selected chunk。

MoA 建议的非阻塞补强中，已立即完成两项：

```text
BASE_HASH_CHECK
b2_min_manifest.json: 成功
b2_min_readme.md: 成功

SELECTION_FAIL_ROWS
variant=ep015_chunk000_063
failed=maxCC>0.070
phi=6.435489654541016
S2 rmse=0.0005247734726096197
Euler=123.953125
maxCC=0.07163110510281959
```

第三项需在 B2-min design memo 中落位：显式说明 formal-vs-qmatch 系统差异，例如 formal512 `phi=6.4/Euler=120.81` vs nnUNet qmatch `phi≈5.79/Euler≈116.15`；reverse_fail=False 不受影响，但下游若对 φ/Euler 敏感，需要声明容忍区间与适用范围。

一句话结论：**B2-min design-entry gate 判定 CONDITIONAL_PASS：ep015 + hy7-gray-calibration-qmatch-v1 的 full-batch pass、baseline package 与含 full-batch control 的 constrained selection smoke 足以开启 B2-min 设计；边界为 calibrated / no-retraining / explicit qmatch / full-batch 为唯一验收口径，ORIG raw remains known_fail，selected chunk 仅限 triage 不得替代 full-batch gate，100/200ep scaling 与新训练未获授权。**

### 15.11 B2-min design memo 已落地

承接 §15.10 的 `CONDITIONAL_PASS` design-entry gate，已撰写 B2-min design memo：

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/design_memo_20260706.md
```

memo 将下一步限定为 **design / dry-run planning**，不是 B2-min 结果验收或训练启动。核心边界：

1. frozen checkpoint 仍为 `ep015`。
2. required calibration 仍为 `hy7-gray-calibration-qmatch-v1`，所有 downstream path 必须显式声明。
3. 验收锚点必须是 full-batch `ep015_all`，不是 selected chunk。
4. selected chunk 只能作为 triage-only；`ep015_chunk000_063` 的失败原因 `maxCC>0.070` 已作为负样本记录。
5. formal route 与 nnUNet-qmatch route 的系统差异已写入风险项：formal512 `phi=6.4/Euler=120.81` vs nnUNet qmatch `phi≈5.79/Euler≈116.15`。
6. memo 明确禁止新训练、100/200ep scaling、新 checkpoint、第二次 topology rescue、gate relaxation、ORIG raw pass claim。

建议的第一个 B2-min design component 方向：

```text
calibrated pore-mask / gray-pore handoff bundle for downstream multiscale 3D fusion
```

理由：它仍是 no-retraining、artifact/manifest based，可为阶段三多尺度 3D digital core 入口准备校准后的孔隙/灰度交接包，而不提前引入 `[sus,pore]` 联合生成训练或新模型复杂度。

### 15.12 B2-min design-entry audit checklist 与 Component C design card

已将 §15.10–15.11 的 design-entry 约束转成可机器检查的 audit checklist，并完成 Component C handoff bundle design card。

新增代码与测试：

```text
src/hy7_b2_min_audit.py
tests/test_hy7_b2_min_audit.py
```

audit checklist 覆盖：

1. `main_checkpoint=ep015`。
2. `calibration_version=hy7-gray-calibration-qmatch-v1` 显式存在。
3. `orig_raw_status=known_fail`。
4. selection summary 必须包含 full-batch `ep015_all`。
5. failed/rejected row 必须可见。
6. selected chunk 与 full-batch 必须分离，selected chunk 只能作为 triage。
7. design/report text 中必须出现 `CONDITIONAL_PASS`、`triage_only`、formal route、nnUNet qmatch route、no-new-training boundary。
8. 禁止将 unsafe claims 写成正向结论；允许它们出现在 “Forbidden / do not write” 列表中。

已用远程 ordered-view 中真实 `b2_min_manifest.json` 与 `selection_summary.json` 加本地 `design_memo_20260706.md` 跑 audit；远程小 JSON/MD/hash 证据也已镜像到本地：

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/baseline_package_ep015/
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/constrained_selection_smoke_ep015/
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/MIRRORED_REMOTE_EVIDENCE.md
```

audit 结果：

```text
passed=true
errors=[]
checks=18 items
```

审计记录：

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/audit_report_20260706.json
```

测试证据：

```text
python3 -m pytest tests/test_hy7_b2_min_audit.py -q -> 5 passed
python3 -m pytest tests -q -> 36 passed
```

Component C design card：

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/component_c_handoff_bundle_design_20260706.md
```

Component C 定义：

```text
calibrated pore-mask / gray-pore handoff bundle for downstream multiscale 3D fusion
```

该 design card 仍只授权 design，不授权 dry-run package；其 dry-run 若后续获准，必须输出 `handoff_manifest.json`、`handoff_readme.md`、`formal_vs_qmatch_metrics.json`、`candidate_rows.json`、`forbidden_claims.txt`、`hashes.txt`，并通过 `hy7_b2_min_audit.py`。

当前状态：no-retraining calibrated handoff 已具备可审计设计入口；下一步可由用户决定是否批准执行 handoff bundle dry-run package。

### 15.13 Component C no-retraining handoff bundle dry-run 已执行

用户批准继续后，已按 Component C design card 执行 **no-retraining handoff bundle dry-run package**。本步骤只打包既有本地镜像证据与设计文本，不训练、不采样、不引入新 checkpoint。

新增脚本与测试：

```text
src/hy7_b2_min_handoff.py
tests/test_hy7_b2_min_handoff.py
```

本地 dry-run 输出目录：

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/handoff_bundle_ep015_20260706/
```

输出文件：

```text
handoff_manifest.json
handoff_readme.md
formal_vs_qmatch_metrics.json
candidate_rows.json
forbidden_claims.txt
audit_report.json
ordered_view_links.txt
hashes.txt
```

核心 manifest 字段：

```text
status=calibrated_b2_min_handoff_design_dry_run
main_checkpoint=ep015
calibration_version=hy7-gray-calibration-qmatch-v1
orig_raw_status=known_fail
execution_boundary=no_retraining_no_new_sampling_no_scaling_no_new_checkpoint
acceptance_anchor=ep015_all
selected_chunk_policy=triage_only
formal_route=threshold_formal_full_batch
nnunet_route=qmatch_nnunet_diagnostic
downstream_target=multiscale_3d_digital_core_planning
```

审计结果：

```text
python3 src/hy7_b2_min_audit.py \
  --manifest handoff_bundle_ep015_20260706/handoff_manifest.json \
  --selection-summary constrained_selection_smoke_ep015/selection_summary.json \
  --design-text handoff_bundle_ep015_20260706/handoff_readme.md

passed=true
errors=[]
checks=18 items
```

hashes 内部校验：

```text
handoff_manifest.json: OK
handoff_readme.md: OK
formal_vs_qmatch_metrics.json: OK
candidate_rows.json: OK
forbidden_claims.txt: OK
audit_report.json: OK
ordered_view_links.txt: OK
```

当前判定：Component C handoff bundle dry-run 已完成且通过 audit。它仍是 **design/dry-run handoff package**，不是 B2-min 结果验收；下一步若要将其升级为阶段三多尺度 3D digital core planning 输入，应再做一次 promotion / stage-entry gate，确认 full-batch anchor、qmatch 显式、formal-vs-qmatch 差异、forbidden claims 仍被保留。

### 15.14 Handoff bundle → Stage 3 planning promotion gate

已对 `handoff_bundle_ep015_20260706/` 执行 digital-rock-gate MoA promotion / stage-entry 复核，问题为：该 bundle 是否可作为 Stage 3 `multiscale 3D digital core planning` 输入。

MoA evidence：

```text
provider=moa
preset=digital-rock-gate
refs=openai-codex:gpt-5.5, deepseek:deepseek-v4-pro, openrouter:z-ai/glm-5.2, custom:dk-claude:claude-fable-5
aggregator=custom:dk-claude:claude-opus-4-8
smoke=OK-ROCK
```

完整 gate 记录：

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/handoff_stage_entry_gate_20260706.md
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/handoff_stage_entry_gate_moa_output_20260706.md
```

Gate verdict：

```text
PROMOTE_WITH_CONSTRAINTS
GATE_LEVEL=stage-3-planning-input only
```

一句话结论：HY7 B2-min 校准无重训交接束哈希与上游溯源全验通过、审计 18/18、双路线分离且负证据可见，经 digital-rock-gate 判定 `PROMOTE_WITH_CONSTRAINTS`，批准升级为 Stage 3 多尺度 3D 数字岩心**规划输入**（仅规划级，带全部禁令与 2D/3D connectivity 语义补强约束），不授权 3D 生成、训练/扩量或最终科学验收。

允许下一步：

- 注册 handoff bundle 为 Stage 3 planning input。
- 撰写 Stage 3 planning memo / requirements / design card。
- 建立 formal route、qmatch route、triage chunks、failed row、forbidden claims 的约束矩阵。
- 定义 Stage 3 gate 草案与指标口径。
- 仅以 `ep015_all` 作为 planning anchor；qmatch 结果必须保持 diagnostic/calibrated 路线标签。

仍然禁止：B2-min final pass claim、B1.1 unconditional pass claim、ORIG raw pass claim、implicit qmatch、second B1.1 topology rescue、gate relaxation、新训练、新采样、100/200ep 扩量、新 checkpoint、实际 3D 生成/voxel export/生产或科学验收签字、selected 64-slice chunk 代表全模型性能、formal route 与 nnUNet-qmatch route 无标签合并。

必须补强：

- Stage 3 design 定稿前必须澄清 connectivity/percolation 语义。`src/hy7_phase2_eval.py` 定义 `x_penetrate/y_penetrate` 为最大连通簇同时接触左右/上下边界的 tile 比例；因此当前 `0.0/0.0` 只能解释为当前 2D tile-level largest-CC 没有 x/y spanning，不能解释为 3D 渗流或 3D connectivity 证据。
- Stage 3 planning memo 必须记录 chunk threshold drift、formal vs qmatch porosity difference、candidate_rows 8 chunk + 1 full-batch 的结构性重叠、失败 chunk `ep015_chunk000_063` 风险、selection hash 指向 `.json` 而非 `.md`、以及 `hy7-gray-calibration-qmatch-v1` 的来源/阈值说明。

### 15.15 B2 continuation: Stage 3 planning memo 与约束矩阵

按“继续 B2 实验”的指令，已将 handoff promotion gate 转化为下一步 B2→Stage3 桥接实验设计，而不是直接启动训练或 3D 生成。

新增：

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/b2_continuation_stage3_planning_memo_20260706.md
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_planning_constraints_matrix_20260706.json
```

当前决策：继续 B2 的 immediate next experiment 是 **B2-D1 constraints and connectivity semantics closure**：

```text
APPROVED_TO_DESIGN
NOT_APPROVED_TO_TRAIN
NOT_APPROVED_TO_GENERATE_3D
```

目的：把 Stage 3 planning gate 的补强要求转成可审计设计输入，包括 formal/qmatch/triage/failed/forbidden/3D-connectivity 五类约束矩阵。

关键矩阵约束：

```text
formal route anchor=ep015_all, n=512, pass_gate=True, allowed_use=planning_anchor_only
nnUNet-qmatch route=diagnostic_calibrated_route_only
selected_chunk=ep015_chunk384_447, policy=triage_only
failed_risk_chunk=ep015_chunk000_063, failure=maxCC>0.070
x/y penetrate current meaning=2D tile-level largest-CC spanning ratio, not 3D permeability/connectivity evidence
```

文献/理论支撑已挂到 memo：

- 2D→3D reconstruction / GAN / SliceGAN：`Mosser2017_3D_porous_media_GAN.pdf`, `Kench2021_SliceGAN_2D_to_3D.pdf`。
- digital rock validation：`Andra2013` Part I/II, `Blunt2013`，以及 S2、Euler/Minkowski、connectivity/percolation、permeability 指标族。
- 3D porous diffusion / controlled latent diffusion / multiphase pore images：`Liu2025_Controlled_Latent_Diffusion_3D_porous.pdf`, `Zhu2025_diffusion_3D_multiphase_poreImages.pdf`, `Hou2026_limited_core_multimodal_diffusion_3D.pdf`。
- shale/multimineral context：`Loucks2012_mudrock_pore_types.pdf`，并明确页岩/多矿物 2D→3D 不能直接套砂岩假设。

大胆探索分支已预注册但分级：

1. **Branch A — 2D-to-3D statistical reconstruction planning from calibrated B2 handoff**：`PRIMARY_NEXT_DESIGN`，下一步写 Stage 3 Branch A design card。
2. **Branch B — conditional [gray,pore]/[sus,pore] generation**：有理论支撑，但需要新训练 gate。
3. **Branch C — topology/percolation-controlled generative sampling**：有潜力，但须先定义 3D connectivity/percolation 指标。

下一步文件建议：

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_branch_a_2d_to_3d_reconstruction_design_20260706.md
```

### 15.16 Stage 3 Branch A 2D→3D reconstruction 正式设计卡

已按指令直接写入 Branch A 正式设计卡：

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_branch_a_2d_to_3d_reconstruction_design_20260706.md
```

设计卡状态：

```text
DESIGN_CARD_PRE_REGISTRATION
Execution boundary=design only; no training, no new sampling, no actual 3D generation, no voxel export, no new checkpoint
```

Branch A 一句话决策：使用已批准的 calibrated B2 handoff bundle 作为受约束规划输入，为 2D→3D digital-rock reconstruction 实验预注册体尺寸、route label、morphology/topology/percolation 指标和 fail-closed gate；在 Stage 3 design gate 通过前不启动任何生成或训练。

设计卡将 Branch A 分成三级：

```text
A0 no-generation planning package: CURRENTLY_ALLOWED
A1 tiny synthetic dry-run: NOT_YET_APPROVED, future gate required
A2 real 2D→3D reconstruction experiment: NOT_YET_APPROVED, future gate required
```

候选算法族：

- SliceGAN-style dimensionality expansion；
- MPS / statistic-constrained reconstruction planning；
- controlled latent diffusion / statistic-conditioned 3D diffusion。

已预注册 target volume candidates：

```text
A0-table: no volume, allowed now
A1-toy: 32^3–64^3, metric plumbing only, future gate required
A2-small: 128^3, first real 3D reconstruction candidate, future gate required
A2-medium: 256^3, higher-FOV planning target, future gate required
```

3D 必加指标：3D porosity、3D S2 x/y/z、3D connected porosity ratio、x/y/z percolation flags、3D LCC fraction、3D Euler/Minkowski、pore-size distribution / granulometry proxy；permeability/proxy 只能在真实 3D volume 存在后讨论。

下一步工作项：写 machine-readable Branch A gate metrics schema：

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_branch_a_gate_metrics_20260706.json
```

### 15.17 Stage 3 Branch A gate metrics schema

已写入 machine-readable gate metrics schema：

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_branch_a_gate_metrics_20260706.json
```

Schema 状态：

```text
workflow_node=HY7-stage3-branch-A-gate-metrics-schema
status=A0_SCHEMA_PRE_REGISTRATION
current_level=A0 no-generation planning package
```

当前允许：定义 target volumes、metrics、candidate algorithms、gate levels、compute/data budget、fail-closed criteria。

当前仍不授权：3D voxel generation、training、new sampling、checkpoint creation、voxel export、B2-min final-pass claim。

Schema 固化了：

- inherited 2D anchor：formal route `ep015_all`、nnUNet-qmatch diagnostic route、selected triage row、failed risk row。
- required 2D metrics：phi、S2、2D Euler、2D maxCC、2D x/y penetrate（只能解释为 2D tile-level）。
- required 3D metrics：3D porosity、3D S2 x/y/z、3D connected porosity ratio、x/y/z percolation flags、3D LCC fraction、3D Euler/Minkowski、pore-size/granulometry proxy，真实 3D volume 后才可谈 permeability/proxy。
- volume candidate requirements：A0-table allowed now；A1-toy/A2-small/A2-medium 均需要 future gate。
- artifact/provenance requirements：future package 必须包含 manifest/readme/input slice manifest/route constraints/2D inherited metrics/3D schema/connectivity semantics/forbidden claims/hashes；大体数据和权重不得入 git。
- fail-closed conditions：route label 缺失、full-batch anchor 缺失、selected chunk 被当全模型、failed chunk 消失、2D penetrate 被解释成 3D percolation、3D connectivity 缺失、hash 缺失、volume size/voxel spacing/modality 未记录、未经 gate 启动 A1/A2 等均 fail-closed。

下一道 gate question 已预注册：

```text
May Branch A A1 tiny synthetic metric-plumbing dry-run be started under toy/no-scientific-evidence constraints?
```

候选 verdicts：

```text
ALLOW_A1_TOY_METRIC_PLUMBING_ONLY
ALLOW_A1_WITH_CONSTRAINTS
DO_NOT_START_A1
```

### 15.18 Stage 3 Branch A A1 toy metric-plumbing gate

已运行 `digital-rock-gate` MoA，对 “是否允许启动 Branch A A1 tiny synthetic metric-plumbing dry-run” 做严格 stage gate。

Gate record：

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_branch_a_a1_toy_gate_moa_output_20260706.md
```

MoA evidence：

```text
provider=moa
preset=digital-rock-gate
smoke=OK-ROCK
refs=openai-codex:gpt-5.5, deepseek:deepseek-v4-pro, openrouter:z-ai/glm-5.2, custom:dk-claude:claude-fable-5
aggregator=custom:dk-claude:claude-opus-4-8
```

Verdict：

```text
ALLOW_A1_WITH_CONSTRAINTS
```

解释：A0 schema 已完整、哈希验证、内部一致，并且预注册了此 gate；A1 是在真实 2D→3D reconstruction 前去除 3D metric code paths 与 artifact package 形状风险的最小步骤。但 reviewer 明确指出，A1 必须是带约束的 toy metric-plumbing，不是“跑通即通过”。

授权范围：

```text
volume_size <= 64^3
input_type=synthetic toy/mock volume only
scientific_status=not_evidence
purpose=verify 3D metric code paths and artifact package shape only
no HY7 scientific claim
no B2-min final-pass claim
no training
no new sampling from any model
no checkpoint
no actual 2D→3D reconstruction claim
no large artifacts committed to git
outputs under dry-run path only
```

A1 新增强制条件：

- C1 Known-answer phantom suite：必须用 >=2–3 个解析 phantom 验证指标，例如 all-solid/all-pore/single straight through-channel/isolated voxel 或 block；不 crash 不是通过。
- C2 `connectivity_semantics.md` 必须声明 pore-phase 与 complementary solid 的 6/18/26 connectivity convention。
- C3 必须显式定义 percolation：同一 pore-phase connected component 同时接触某轴两个 opposing faces。
- C4 Euler 未实现时必须 fail-closed：`"euler_3d": {"status": "NOT_IMPLEMENTED_FAIL_CLOSED"}`。
- C5 toy-route label hygiene：所有 A1 JSON 必须有 `input_type=synthetic_toy`、`scientific_status=not_evidence`、独立 toy route label；toy 数值不得携带 `threshold_formal_full_batch` 或 `nnUNet ep015_qmatch` 标签。
- C6 deterministic：随机 toy volume 必须记录 seed + generator，可复现。

A1 required outputs：

```text
branch_a_a1_manifest.json
branch_a_a1_readme.md
metrics_3d_toy.json
connectivity_semantics.md
forbidden_claims.txt
hashes.txt
```

可选：`toy_volume_path.txt`，只记录 path/hash/size，不提交体数据。

仍然禁止：real 3D reconstruction、training、new sampling、new checkpoint、科学 voxel export、大体数据或权重入 git、B2-min final pass、B1.1 unconditional pass、ORIG raw pass、qmatch optional/implicit、selected chunk 代表全模型、formal/qmatch 混标、2D penetrate 解释成 3D permeability/connectivity、A2 或任何真实重建无新 gate 启动。

A1 输出绝不能作为 HY7 scientific evidence；所有 A1 artifact 必须包含 `scientific_status=not_evidence`。

下一步：按 gate 约束写 A1 toy metric-plumbing dry-run 的实现/包结构，优先生成 metric code path 与 known-answer phantom tests，但仍不得提交 toy volume 或宣称科学结果。

### 15.19 Stage 3 Branch A A1 toy metric-plumbing implementation/package

已按 A1 gate 的 `ALLOW_A1_WITH_CONSTRAINTS` verdict 写入实现、测试与轻量 package；本步骤仍不产生 HY7 scientific evidence，不训练、不采样、不生成真实 3D reconstruction，不提交 toy volume。

实现与测试：

```text
src/hy7_stage3_branch_a_a1_toy.py
tests/test_hy7_stage3_branch_a_a1_toy.py
```

A1 package：

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_branch_a_a1_toy_metric_plumbing_20260706/
```

Package files：

```text
branch_a_a1_manifest.json
branch_a_a1_readme.md
metrics_3d_toy.json
connectivity_semantics.md
forbidden_claims.txt
hashes.txt
```

未提交、未生成：`toy_volume.npy`。本 package 只提交 metrics/provenance/semantics/hash，不提交体数据。

实现范围：

```text
workflow_node=HY7-stage3-branch-A-A1-toy-metric-plumbing
verdict=ALLOW_A1_WITH_CONSTRAINTS
input_type=synthetic_toy
scientific_status=not_evidence
route_label=synthetic_toy_plumbing
volume_size=8^3
voxel_spacing=synthetic_no_physical_spacing
```

Known-answer phantom suite：

- `all_solid`：phi=0，x/y/z percolation=false，LCC=0。
- `all_pore`：phi=1，x/y/z percolation=true，LCC=1。
- `x_channel`：phi=1/64，x percolation=true，y/z=false。
- `isolated_voxel`：phi=1/512，x/y/z percolation=false。

3D metric plumbing：

- 3D porosity：implemented。
- 3D S2：`lag_1_valid_pairs_no_wrap` proxy，axes x/y/z，no periodic wrap。
- connected porosity ratio：implemented，记录 pore_voxel_basis 与 total_volume_basis。
- x/y/z percolation flags：implemented。
- largest connected component fraction：implemented。
- 3D Euler/Minkowski：`NOT_IMPLEMENTED_FAIL_CLOSED`，显式 fail-closed，不省略、不置空。

Connectivity semantics：

```text
pore-phase connectivity: 6-neighborhood
complementary solid connectivity: 26-neighborhood declared for future Euler/Minkowski work
percolation definition: a single pore-phase connected component touches both opposing faces along axis k
```

验证：

```text
python3 -m pytest tests/test_hy7_stage3_branch_a_a1_toy.py -q  # 3 passed
python3 -m pytest tests -q  # 42 passed
sha256sum -c hashes.txt  # package files OK
```

下一步如果继续，应对 A1 package 做一次 A1 completion review/gate：确认它是否只完成 toy metric-plumbing，可否进入 A2 设计（不是执行 A2），并明确 3D Euler/Minkowski 是否必须先实现还是可继续作为 fail-closed placeholder。

### 15.20 Stage 3 Branch A A1 completion review/gate

已对 A1 package 做 `digital-rock-gate` MoA completion review，确认是否满足 “toy metric-plumbing only”，以及是否允许进入 A2 **design only** 阶段。

Gate record：

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_branch_a_a1_completion_gate_moa_output_20260706.md
```

MoA evidence：

```text
provider=moa
preset=digital-rock-gate
smoke=OK-ROCK
refs=openai-codex:gpt-5.5, deepseek:deepseek-v4-pro, openrouter:z-ai/glm-5.2, custom:dk-claude:claude-fable-5
aggregator=custom:dk-claude:claude-opus-4-8
```

Verdict：

```text
A1_COMPLETE_WITH_CONSTRAINTS_ALLOW_A2_DESIGN_ONLY
```

判定：A1 满足 toy metric-plumbing only。证据包括：8³ synthetic volume、`synthetic_no_physical_spacing`、`route_label=synthetic_toy_plumbing`、`scientific_status=not_evidence`、known-answer phantoms 正确、3/3 focused tests 与 42/42 suite 通过、5/5 package hashes OK、无 `.npy`/toy volume 提交。

A1 outputs 不能作为 HY7 scientific evidence；它们只验证 synthetic phantom 上的 3D metric code paths 与 artifact package shape。

允许进入：

```text
A2 DESIGN ONLY
```

A2 design 可包含：

- design docs / interface / schema specs；
- 3D Euler/Minkowski algorithm design；
- 扩展 phantom suite 设计，包含 sphere / torus / hollow cube 等有解析 Euler 的 phantoms；
- asymmetric phantom，用于区分 periodic vs non-periodic S2；
- metric acceptance criteria；
- real 2D→3D reconstruction pipeline architecture（design only）；
- provenance/hash/manifest conventions；
- test plan / risk register / A2 execution gate criteria。

仍然禁止：A2 execution、real 2D→3D reconstruction、training/fine-tuning、new sampling、checkpoint、voxel volume export 或 git commit、基于 A1 或 A2 design 的 HY7 scientific claims。

A2 execution 前新增硬条件：

1. 3D Euler/Minkowski 可在 A2 design 阶段保持 fail-closed，但若 A2 execution 的 metric/acceptance/claim 依赖 topology，执行前必须实现并用 phantom 验证；否则必须在 A2 design 中明确 de-scope，并在 manifests 里保持 fail-closed。
2. Toy-volume reproducibility 需要二选一：提交 toy volume（当前不推荐）或提供 deterministic-regeneration proof（seed + source-hash round-trip test）。
3. S2 boundary condition 必须钉住 periodic vs non-periodic，并用 asymmetric phantom 验证。
4. 需要超过 8³ 的 scale-up validation 设计。
5. A2 execution 前必须另做 fresh strict gate。

下一步：写 A2 design-only card，重点是 Euler/Minkowski 设计、S2 boundary convention、deterministic-regeneration proof、扩展 phantom suite 与 A2 execution gate criteria；不得执行 A2。

### 15.21 Stage 3 Branch A A2 design-only card 与 execution gate checklist

已按 A1 completion gate 的 `A1_COMPLETE_WITH_CONSTRAINTS_ALLOW_A2_DESIGN_ONLY` verdict 写入 A2 **design-only** card 与 machine-readable execution gate checklist；本步骤未执行 A2，不训练、不采样、不生成真实 2D→3D reconstruction、不导出 voxel、不产生 HY7 scientific claim。

新增：

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_branch_a_a2_design_only_card_20260706.md
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_branch_a_a2_execution_gate_checklist_20260706.json
```

状态：

```text
A2_DESIGN_ONLY_PRE_EXECUTION
execution_authorized=false
```

A2 design card 固化的设计范围：

- 3D Euler/Minkowski algorithm design；
- expanded phantom suite design；
- asymmetric S2 boundary-condition phantom；
- deterministic-regeneration proof；
- scale-up validation design beyond 8^3；
- A2 metric interface schema；
- future A2 execution gate question。

A2 execution 前 checklist 硬条件：

- algorithm family / training-or-non-training path / compute budget / output volume size / voxel spacing 明确；
- input 2D slice manifest 与 route labels 明确；
- `ep015_all` 只作为 planning anchor；formal route 与 nnUNet-qmatch route 保持分离；
- selected chunk 仍为 triage-only；failed chunk `ep015_chunk000_063` 仍保留 risk label；
- Euler/Minkowski 若用于 topology metric/acceptance/claim，执行前必须 implement + phantom validate；否则必须 explicit de-scope 且 manifests 保持 fail-closed；
- S2 boundary condition 必须钉住 periodic/non-periodic，并用 asymmetric phantom 验证；
- deterministic-regeneration proof 必须记录 seed/source hash/exact command/environment/metrics hash 或 reproducible subset；
- scale-up validation design 包含 8^3、16^3、32^3，且 scientific_status=not_evidence；
- large volumes / model weights 不得入 git。

预注册 future A2 execution gate question：

```text
May Branch A A2 execution begin under the specified algorithm, data, compute, artifact, and metric constraints?
```

future allowed verdicts：

```text
ALLOW_A2_EXECUTION_WITH_CONSTRAINTS
ALLOW_A2_TOY_SCALEUP_ONLY
DO_NOT_START_A2_EXECUTION
```

仍然禁止：A2 execution、real 2D→3D reconstruction、training/fine-tuning、new model sampling、checkpoint、voxel export/git commit、任何 HY7 scientific claim、B2-min final pass、ORIG raw pass、implicit qmatch、formal/qmatch route 混标、2D x/y penetrate 解释成 3D permeability/connectivity。

### 15.22 Stage 3 Branch A A2 phantom suite design 与 metric interface schema

已继续补齐 A2 design-only package 的两个配套文件；本步骤仍是 design only，未执行 A2，不训练、不采样、不生成真实 2D→3D reconstruction、不导出 voxel、不产生 HY7 scientific claim。

新增：

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_branch_a_a2_phantom_suite_design_20260706.md
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_branch_a_a2_metric_interface_schema_20260706.json
```

Phantom suite design 覆盖：

- `all_solid`：zero-pore baseline；
- `all_pore`：full-pore baseline；
- `isolated_voxel`：single-component / denominator sanity；
- `straight_channel_x/y/z`：axis-specific percolation 与 axis mapping；
- `two_disconnected_blobs`：component count 与 LCC denominator；
- `hollow_cube_shell_or_cavity`：cavity / foreground-background ambiguity；
- `torus_like_ring`：handle/genus sensitivity；
- `asymmetric_s2_boundary`：区分 periodic vs non-periodic S2；
- `sparse_random_seeded_toy`：deterministic-regeneration proof。

默认 topology/semantics：

```text
pore phase foreground connectivity=6-neighborhood
complementary solid/background connectivity=26-neighborhood
percolation=a single pore-phase connected component touches both opposing faces along axis k
axis mapping: x/y/z -> ndarray axes 0/1/2
```

Scale-up matrix：

```text
8^3: P0-P5 + P8
16^3: P0-P5 + P8
32^3: P0-P8 where feasible
scientific_status=not_evidence
```

Metric interface schema 固化：future A2 package required files、manifest required fields、route constraints schema、2D inherited metrics schema、3D reconstruction metrics schema、connectivity semantics schema、S2 boundary semantics schema、phantom validation schema、provenance / deterministic regeneration schema、fail-closed conditions。

关键 fail-closed 条件：execution 无 fresh strict gate、algorithm family 缺失、input slice manifest 缺失、route labels 混并、failed chunk 风险消失、S2 boundary convention 缺失、asymmetric S2 phantom 缺失、Euler/Minkowski 未验证却用于 topology claims、deterministic regeneration proof 缺失、大 volume/weights 入 git、scientific_status 边界缺失，均 fail-closed。

### 15.23 Stage 3 Branch A A2 risk register

已写入 A2 design-only risk register；本步骤仍不执行 A2，不训练、不采样、不生成真实 2D→3D reconstruction、不导出 voxel、不产生 HY7 scientific claim。

新增：

```text
experiments/花页7_PlanB_记录/phase2/b2_min_calibrated/stage3_branch_a_a2_risk_register_20260706.md
```

Risk register 状态：

```text
A2_DESIGN_ONLY_RISK_PRE_REGISTRATION
execution_authorized=false
ready_for_A2_execution=false
eligible_next_step=A2 design package completion gate review
```

登记范围覆盖：

- gate authorization / scope creep；
- algorithm ambiguity；
- input manifest / route contamination；
- selected chunk triage misuse；
- failed chunk `ep015_chunk000_063` negative evidence loss；
- 2D/3D semantic overreach；
- S2 boundary drift / axis omission；
- connectivity/percolation convention ambiguity；
- Euler/Minkowski placeholder misuse and convention error；
- phantom insufficiency and scale hard-coding；
- deterministic-regeneration gap；
- large artifact / hash / provenance / environment risks；
- permeability overclaim；
- A2-small and A2-medium premature execution；
- claim-language drift；
- missing negative-result handling；
- MoA routing risk。

Stage-specific controls：A1 toy metric-plumbing 只继承为 controls，不作为 HY7 evidence；A2-small 必须 fresh A2 execution gate + algorithm/input/route/metric/provenance/negative-evidence package；A2-medium 不得绕过 A2-small review，必须新增 strict gate。

关键 fail-closed 条件：fresh strict gate 缺失、algorithm/input manifest 缺失、formal/qmatch route 混并、failed chunk 风险消失、S2 boundary convention 或 asymmetric phantom 缺失、Euler/Minkowski placeholder 被用作 topology claim、deterministic regeneration proof 缺失、大 volume/weights 入 git、scientific_status 边界缺失、A1/A2 design 输出被当成 HY7 evidence。

关键证据 sha256：

```text
88753f0fe79c8bc7392b288169abe1209fe0191893a2e51aa55f1ebe76256f17  validation_ep005.json
3127746d060212384b79d731f1e6e2f14b476f5df7cbf393afd829beb5a854ab  validation_ep010.json
0b1a06da90feacb4bf9333c9a88251272b9fb92ebbcd3e77b4207ccfc0b1d8d6  validation_ep015.json
816059d7cb9a16aff0f2bde5e2ba2615a0d3caa479d6a2b09f7361e02f6e02b8  validation_ep020.json
df45f58be5ce10d20a06921b6b60369fe81e908518e85db94880ff98a42ce40f  periodic_validation_summary.json
df15782df4d67704c3837c3f18e0bdb93bcd331e8f11da595af8a4deff37ea25  train_meta.json
```
