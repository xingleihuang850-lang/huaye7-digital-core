# 项目 Workflow 设计（Agent 执行规范）

> 目的：把“生成式数字井筒研究”从开放式 Agent 自由发挥，改成稳定、可复盘、可审计、可迭代的 Workflow。  
> 术语/写法统一见 [[04_项目术语表与写法规范]]。  
> 结论：**不需要重排或重命名现有 Claude/notes 文件**；先在现有结构上加一层 Workflow 索引与执行规范。后续如 workflow 增多，再增补 `03` 或拆出 `workflows/` 子目录。

## 0. 总原则

本项目不采用“让 Agent 自主决定科研路线”的模式，而采用：

```text
人类确定主线与门槛
→ Workflow 固定节点、状态、输入输出、证据要求
→ Agent 在节点内执行、审计、写文档、提建议
→ 关键节点多模型复核/用户确认
→ 通过门槛后进入下一节点
```

Agent 的角色：执行员、审计员、文档员、实验助手。  
Workflow 的角色：老板，负责约束路线、状态、证据和分支。  
用户的角色：最终决策者，尤其负责删除/重训/路线切换/论文结论确认。

## 1. 是否需要重新排布与命名

### 1.1 当前结论

**现在不建议重排或重命名现有文件。**

原因：

1. `CLAUDE.md` 已是项目入口，编码 agent 会自动读取。
2. `notes/README.md` 已有编号规则：`00` 总览、`1x` 阶段一、`2x` 阶段二、`3x` 阶段三、`4x` 阶段四、`9x` 工程。
3. 现有笔记之间已有 Obsidian 双链，贸然重命名会破坏链接。
4. 当前最缺的不是文件搬家，而是“每次任务怎么按节点执行、如何留痕、如何进入下一步”的 Workflow 规则层。

### 1.2 采用轻量新增方案

新增本文件：

```text
notes/03_项目Workflow设计.md
```

定位：总览层 Workflow 规范，和 `00/01/02` 同级。  
后续若新增更多 workflow，可选两种方式：

- 少量新增：继续在本文件追加 `WF-06`、`WF-07`。
- 大量新增：新建 `notes/workflows/`，每个 workflow 一个文件；但现在暂不需要。

### 1.3 现有文件职责保持不变

| 文件/目录 | 继续承担的职责 |
|---|---|
| `CLAUDE.md` | Agent 入口、项目全局上下文、当前状态、强约束。 |
| `notes/README.md` | Obsidian/MOC 索引，告诉人和 Agent 先读什么。 |
| `notes/00_研究主线路线图与任务分解.md` | 论文四阶段主线、任务拆分、当前状态。 |
| `notes/03_项目Workflow设计.md` | 本文件：定义执行 Workflow 与门槛。 |
| `notes/2x_*` | 阶段二实验设计、结果、诊断、迭代。 |
| `experiments/花页7_PlanB_记录/` | 轻量证据、图、metrics、stdout 摘要与 README。 |
| `docs/environment-remote.md` | 远程环境与运行口径。 |
| `REPRODUCE.md` | 复现链条。 |
| `experiments/WEIGHTS_MANIFEST.md` | 权重/大产物路径、hash、size、mtime、状态。 |

## 2. 状态词标准

后续所有 workflow 尽量使用统一状态词：

| 状态 | 含义 |
|---|---|
| `planned` | 已设计，未执行。 |
| `ready` | 输入、路径、命令、门槛齐备，可执行。 |
| `running` | 正在执行。 |
| `remote_done_not_evaluated` | 远程训练/计算已完成，但尚未采样/评估/解释。 |
| `trained_needs_sampling_eval` | 模型训练完成，缺采样与评估。M7-v3 当前即此状态。 |
| `evaluated_needs_review` | 已有评估结果，待解释/复核。 |
| `accepted` | 结果已通过门槛，可写入主线。 |
| `rejected_or_negative` | 结果为负，保留证据但不作为主线推进。 |
| `blocked` | 缺数据、缺权限、环境失败或结论不可信。 |
| `deprecated` | 历史方案，不再作为主线使用。 |

## 3. WF-01：项目主线 Workflow

### 目标

保证所有工作都服务于硕士论文主线：

```text
基于融合多尺度数据的页岩数字岩心-井筒建模
```

贡献点固定为：

```text
生成式/扩散 + 多模态融合 + 数字井筒
```

### 输入

每次新任务开始前必须读：

1. `CLAUDE.md` 的 ★ 主线任务与工作纪律。
2. `notes/README.md`。
3. `notes/00_研究主线路线图与任务分解.md`。
4. 当前阶段对应笔记，例如阶段二读 `notes/22`、`notes/24`。

### 固定四阶段

1. 阶段一：分割地基。
2. 阶段二：2D 扩散生成。
3. 阶段三：多模态 3D 数字岩心。
4. 阶段四：数字井筒。

### 节点规则

每次任务必须先回答：

1. 属于哪一阶段？
2. 是否推进“生成式 + 多模态融合 + 数字井筒”？
3. 是否只是继续做分割？如果是，是否必要？
4. 是否有文献/物理/地质依据？
5. 输出会写入哪个笔记和哪个证据目录？

### 禁止事项

- 禁止 Agent 自行改变论文主线。
- 禁止把“分割效果提升”误当作最终贡献。
- 禁止无依据新增实验分支。
- 禁止没有证据就写“已完成”“已改善”“可用于论文”。

### 当前应用

当前处于：

```text
阶段二：2D 扩散生成
M7-v3：200ep cheap control 已采样评估，单纯加 epoch 不闭合
```

下一主线节点不是重训，而是：

```text
M7-v4/B1-gray-sus-design
```

## 4. WF-02：实验节点 Workflow

### 目标

把每个实验变成“输入明确、动作明确、输出明确、门槛明确”的节点。

### 节点模板

```text
节点名：
状态：
所属阶段：
输入：
动作：
输出：
证据目录：
更新文档：
通过门槛：
失败/负结果处理：
是否需要多模型复核：
是否需要用户确认：
```

### 必填字段

| 字段 | 要求 |
|---|---|
| 节点名 | 稳定、可引用，例如 `M7-v3-200ep-sampling-eval`。 |
| 状态 | 使用第 2 节状态词。 |
| 输入 | 数据、权重、配置、对照指标的真实路径。 |
| 动作 | 明确命令或脚本，不写“让 AI 看看”。 |
| 输出 | metrics、图、JSON、README、笔记更新。 |
| 证据目录 | 轻量证据写入 `experiments/...`。 |
| 通过门槛 | 例如 S₂/Euler/连通簇是否改善。 |
| 失败处理 | 保留负结果，不覆盖旧结果。 |

### M7-v3 当前节点定义

```text
节点名：M7-v3-200ep-sampling-eval
状态：ready / trained_needs_sampling_eval
所属阶段：阶段二 2D 扩散生成

输入：
- 远程权重：/home/user/HXL/HY7_planb/phase2/ddpm_ct28_200ep/best.pt
- 远程 test set：/home/user/HXL/HY7_planb/phase2/slices_ct28_128/test.npy
- 对照：M7 50ep eval_v2 与 M7-v2 calib 结果

动作：
1. 远程只读确认 best.pt、test.npy、环境。
2. 对 200ep best.pt 采样，生成 samples.npy。
3. 同口径生成 samples_continuous.npy。
4. 跑 T=0 eval。
5. 跑 T* threshold calib。
6. 对比 50ep 与 200ep 的 porosity、S₂、Euler、max_cc_frac、penetration。
7. 归档轻量结果。
8. 更新 notes/24、notes/00、WEIGHTS_MANIFEST、REPRODUCE。
9. 多模型复核结论。

输出：
- experiments/花页7_PlanB_记录/phase2/m7v3_200ep/metrics.json
- experiments/花页7_PlanB_记录/phase2/m7v3_200ep/calib_result.json
- fig_eval.png / fig_calib.png
- README.md
- hash/size/mtime/provenance

通过门槛：
- 若 Euler / 连通簇明显优于 50ep，考虑继续该路线。
- 若 S₂ 好但 Euler 不改善，说明欠训练不是主因，转 B1/B2。
- 若采样失败，先查环境/路径/脚本，不重训。
```

## 5. WF-03：远程计算 Workflow

### 目标

让远程 GPU 操作稳定、可恢复、可审计，避免重复训练或丢证据。

### 适用场景

- 远程训练。
- 远程采样。
- 远程 eval/calib。
- 大文件 hash/size/mtime 核验。

### 标准步骤

1. **只读预检**
   - 确认远程路径存在。
   - 确认输入文件 hash/size/mtime。
   - 确认当前任务不是重复执行。

2. **环境快照**
   - Python 版本。
   - torch/diffusers/numpy/scipy/skimage/SimpleITK。
   - CUDA / nvidia-smi。
   - conda/venv 名称。

3. **命令准备**
   - 命令写入本地笔记或临时 run plan。
   - 明确 `--data`、`--ckpt`、`--out`、`--seed`、`--bs`、`--n`、`--rmax`。
   - 明确 stdout/stderr 日志路径。

4. **执行保护**
   - 长任务使用 caffeinate/setsid/nohup 或远程等价方式。
   - 不只依赖终端滚动输出。
   - 必须有日志和结束 sentinel。

5. **结束核验**
   - 检查 exit code / sentinel。
   - 检查输出文件存在。
   - 计算 sha256、size、mtime。
   - 保存 train_meta / eval metrics / calib_result。

6. **本地轻量归档**
   - 大文件不入 git。
   - 轻量 JSON/PNG/README/stdout 摘要入 `experiments/...`。

7. **状态更新**
   - 更新 `WEIGHTS_MANIFEST.md`。
   - 更新阶段笔记。
   - 更新 `REPRODUCE.md` / `docs/environment-remote.md`。

### 禁止事项

- 未确认输入路径就启动训练。
- 输出目录与旧实验混用。
- 覆盖旧结果。
- 用远程旧 verdict 覆盖本地修正版。
- 未经用户确认删除大文件、权重、原始数据。

## 6. WF-04：多模型复核 Workflow

### 目标

在关键节点避免单模型误判，尤其是科研结论、路径/hash、文档同步、实验设计。

### 触发条件

以下情况建议多模型复核：

1. 新实验设计前。
2. 远程训练/采样结束后。
3. 指标解释有争议时，例如 S₂ 改善但 Euler 变差。
4. 文档同步后。
5. 准备把结论写进中期汇报或论文前。
6. 发现 Agent 与历史笔记冲突时。

### 标准步骤

1. 生成审计包：
   - 当前 diff。
   - 关键文件。
   - 远程证据摘要。
   - 校验输出。

2. 分配模型角色：
   - 模型 A：研究叙事/中文口径。
   - 模型 B：复现工程/路径/hash。
   - 模型 C：严格找错/下一步可执行性。
   - GPT5.5/主模型：汇总裁决。

3. 输出格式：

```text
PASS/BLOCK
P0：阻塞问题
P1：应尽快修
P2：可后续修
最终建议
```

4. 处理方式：
   - P0 必须修完再继续。
   - P1 尽量本轮顺手修。
   - P2 记录为后续事项。

5. 清理临时文件：
   - 删除 prompt 与大审计包。
   - 保留模型 review 与 final summary。

### 已实践案例

2026-07-01 多模型复核已采用该模式，结论 PASS，并清理了临时 prompt/audit_bundle。

## 7. WF-05：用户确认 Workflow

### 目标

把高风险动作与最终科研判断交给用户确认，防止 Agent 越权。

### 必须确认的动作

以下动作必须先问用户，不得自动执行：

1. 删除文件、权重、远程目录、原始数据、用户数据。
2. 重跑大训练或占用大量 GPU。
3. 改变论文主线或放弃某个阶段。
4. 将某个实验结论写成正式论文结论。
5. 合并/重命名大量笔记文件。
6. 修改外部原始数据路径或覆盖服务商原件。
7. 提交 git、推送远程、发布成果。

### 可以直接执行的低风险动作

以下动作通常可以直接做：

1. 只读检查。
2. 读取文件。
3. 生成临时审计包。
4. 写入新的轻量说明文档。
5. 修正文档中的已核实错误。
6. 清理明确临时且重复的 prompt/audit_bundle。

### 用户确认模板

```text
我准备执行：
影响范围：
会修改/删除的路径：
可回滚方式：
不执行的替代方案：
请确认是否继续。
```

## 8. 新增 Workflow 的规则

后续如果要添加新的 workflow，按以下规则：

1. 先判断是“全局 workflow”还是“实验节点 workflow”。
2. 全局 workflow 加到本文件，编号 `WF-06` 起。
3. 具体实验节点写入对应阶段笔记，例如阶段二写 `notes/2x_*`。
4. 若 workflow 数量超过 10 个，再考虑新建：

```text
notes/workflows/
```

5. 新增后必须更新：
   - `notes/README.md`
   - 必要时更新 `CLAUDE.md` ★节接力提示。

## 9. 当前推荐执行顺序

当前不要重排文件；先按现有结构执行下一节点：

```text
WF-01 主线确认
→ WF-02 M7-v3-200ep-sampling-eval 实验节点
→ WF-03 远程采样/评估
→ WF-04 多模型复核
→ WF-05 用户确认是否进入 B1/B2
```

## 10. 一句话规范

```text
Agent 不当老板；Workflow 当老板；用户做最终决策。
```

本项目要的是稳定、可控、可落地、可复现、可审计的研究 Workflow，不是自由发挥的“玄学 Agent”。
