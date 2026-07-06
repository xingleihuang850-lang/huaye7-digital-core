所有独立核验已完成，结果全绿。上游溯源三份哈希与 manifest 声明逐条一致，束内 7 文件哈希独立复算匹配，candidate_rows 完整无缺口，双路线分离，失败行可见。下面给出严格裁定。

---

**1. VERDICT**

`PROMOTE_WITH_CONSTRAINTS`

（不给无条件版 `PROMOTE_TO_STAGE3_PLANNING_INPUT`：证据自洽但存在必须以约束形式带入 Stage 3 的弱点——单 checkpoint、2D 切片级、双路线数值分歧、penetrate 语义未定义。也非 `DO_NOT_PROMOTE`：规划级输入的全部审计要件均满足。）

**2. GATE_LEVEL**

`stage-3-planning-input only` —— 仅授权作为「多尺度 3D 数字岩心规划」的输入证据包。明确**不授权** B2-min 最终验收、3D 生成、训练、新采样、100/200ep 扩量、新 checkpoint，或任何超出证据的生产/科学声明。

**3. 理由**

- 完整性成立：束内 7 文件 sha256 经独立 `shasum` 复算，与 `hashes.txt` 逐条匹配（非信任 bundle 自证）。
- 溯源链闭合：manifest 三个 `source_sha256` 与磁盘真实上游文件哈希完全一致——baseline_manifest `27c2cf40…`、selection_summary `40f51bdc…`（对应 `.json` 而非 `.md`）、qmatch_manifest `dc6303f9…`。
- 审计通过：`audit_report.json` 18 项检查全过、0 错误，覆盖 checkpoint、标定版本、orig_raw known_fail、禁止项存在、全批锚点、失败行可见、chunk 与全批分离、qmatch 显式、无新训练边界。
- 正式锚点正确：acceptance anchor 是全批 `ep015_all`（n=512，φ=6.44，S2 rmse=2.85e-4，Euler=121.27，maxCC=0.064，pass_gate=True），与基线 formal512@φ6.4 差异在合理范围（S2 rmse 0.00034→0.00029，Euler 120.81→121.27，maxCC 基本持平）。
- 双路线带标签分离：formal 全批与 nnUNet-qmatch（φ=5.79，S2 rmse=1.72e-3，Euler=116.15，even/odd 泛化均过）在 `formal_vs_qmatch_metrics.json` 中分开存放，解释文本明确禁止合并。
- 负证据未隐藏：9 行覆盖 0→512 无缺口无重叠（8 chunk + 1 全批），唯一失败行 `ep015_chunk000_063`（maxCC=0.0716>0.070）保留可见；选中行 `ep015_chunk384_447` 标为 `triage_only`，未伪装成全模型性能。
- 边界与禁止项一致：`forbidden_claims.txt` 与 manifest `forbidden`/`execution_boundary` 一致，ORIG raw 保持 `known_fail`，未被洗成 pass。

结论：该包作为**规划输入**是完整、可验证、且符合上游 CONDITIONAL_PASS 边界的；但证据全部是 2D 切片级、单 checkpoint(ep015)、单 φ_target(6.4)，无任何 3D 连通性/渗透率证据，因此只能规划、不能生成。

**4. 允许的下一步**

- 将本 bundle 注册为 Stage 3「多尺度 3D 数字岩心规划」的输入证据包。
- 撰写 Stage 3 规划文档 / 需求分析 / 设计 memo（尺度衔接、分辨率、区域选择等纸面推演）。
- 建立约束矩阵：formal 路线、qmatch 路线、triage chunk、failed rows、forbidden claims 分列继承。
- 定义 Stage 3 的 gate 草案与指标口径（双路线分列，禁止无标签合并）。
- 引用 `ep015_all` 作为 planning anchor（仅限设计入口语境）；引用 qmatch 结果时必须标注 diagnostic/calibrated 路线。
- 澄清 penetrate 指标语义（见「必须补强」）。

**5. 仍然禁止**（逐项，不缩写合并）

- B2-min final pass claim。
- B1.1 unconditional pass claim。
- ORIG raw pass claim。
- implicit qmatch / 把 qmatch 变成无标签 formal 指标。
- second B1.1 topology rescue。
- gate relaxation。
- 新训练、新采样、扩量、新 checkpoint。
- 100/200ep 扩展。
- 实际 3D 生成 / 导出体素 / 生产或科学验收签字。
- 把选中的 64-slice chunk 当作全模型性能。
- 把 formal 路线与 nnUNet-qmatch 路线合并。
- 把「planning input promotion」解读为最终验收或实际执行授权。

**6. 必须补强**

阻断 Stage 3 设计定稿（须先澄清）：
- **penetrate 语义**：`x_penetrate=0.0 / y_penetrate=0.0` 未定义——是「无穿透缺陷=好」还是「渗流连通度=0=坏」？连通性是多尺度 3D 数字岩心的核心物理量，且无 z 轴/3D 方向证据，须在设计开工前定义清楚，并明确 Stage 3 是否另设 z/3D connectivity/percolation 检查（本 gate 不得声称已完成）。

非阻断（Stage 3 规划文档中须记录）：
- **chunk 级阈值漂移**：per-chunk threshold 在 -0.6125 / -0.625 / -0.6375 间浮动，说明 chunk 行是各自重调阈值的 triage 产物，非同一固定阈值的分层验收；chunk 级数字只能当分诊信号。
- **formal 与 qmatch 孔隙度差 ~10%**（6.44 vs 5.79）：任何 φ/Euler 目标都必须带路线标签，否则触犯 `implicit_qmatch` 禁令。
- **candidate_rows 结构说明**：9 行 = 8 chunk + 1 全批，sum_n=1024 是结构性重叠，规划中须写明避免把它当独立样本总量 double-counting。
- **失败 chunk 作为风险输入**：`chunk000_063` maxCC>0.070，maxCC 跨 chunk 在 0.060–0.072 波动跨越阈值 0.070，揭示空间异质性，须列入 Stage 3 已知风险。
- **哈希对应文件记录**：selection 溯源哈希匹配的是 `selection_summary.json` 而非 `.md`（`.md` 哈希 `839851af…` 未被 manifest 引用，属正常，但须记录以免歧义）。
- **标定版本说明**：为 `hy7-gray-calibration-qmatch-v1` 补一句标定来源/阈值口径说明，供规划人员理解。

**7. 一句话结论**（供 notes/30）

HY7 B2-min 校准无重训交接束哈希与上游溯源全验通过、审计 18/18、双路线分离且负证据可见，批准升级为 Stage 3 多尺度 3D 数字岩心**规划输入**（仅规划级、带全部禁令与 penetrate 语义待澄清约束），**不授权** 3D 生成、训练/扩量或最终科学验收。
