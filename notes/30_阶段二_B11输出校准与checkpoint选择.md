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

若要继续训练改造，最小代码方向是：

```text
hy7_phase2_ddpm.py train 增加：
--save-every 10
--eval-every 10
--eval-real test_pore.npy
--eval-gray-test test.npy
--select-metric composite
```

执行前先固定以下 gate，避免看结果后调参：

1. 披露验证样本量 `n` 与逐张方差/CI；当前四个 variant 的均值差异不能直接替代稳定性判断。
2. 预注册 held-out validation slices、checkpoint 网格（如每 10ep）、多目标打分公式与权重。
3. 统一 real/gen 评估代理：若 gen 走 nnUNet，real 参考也应明确是同一 nnUNet 代理或清楚标注为 GT 口径，避免混合口径比较。
4. 设现实止损门槛：例如 `maxCC ≤ 0.070` 且 `Euler ∈ real±15%`。如果 metric-aware selection 后 maxCC 仍系统偏高，再触发结构 loss / B1.1 结构改造；不是现在直接跳 B2。

先不急着设计复杂结构 loss；因为本轮已经证明同一 50ep run 的 best/final 差异很大，说明 checkpoint selection 本身就是未解决变量。
