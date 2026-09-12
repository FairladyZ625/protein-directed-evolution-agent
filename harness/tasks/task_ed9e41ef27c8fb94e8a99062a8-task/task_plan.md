# 调研更难的定向进化基准数据集（把流程推到边界）

Task Contract: harness-task v1

## Brief

我们已在 GB1（4 位点、149,361/160,000 密集测量）上跑通完整流程：数据→预测器→五角色 Agent→知识增强→3 轮闭环→四策略对比。但 GB1 太容易——即便只用 77 个单突变冷启动，模型类策略也在第 2 轮达到全局最优，四策略拉不开差距、知识增强显不出价值。现需调研一个/几个**更难的公开基准数据集**，把同一套流程推到边界，让四策略真正分化。

## Goal

产出一份 markdown 调研报告（落本任务 `artifacts/`），对候选数据集按下方硬判据打分对比，给出 **Top-1 推荐 + 1-2 备选**，并为每个推荐写清**接入我们流程的具体方案**（下载源、字段/列、可变位点、如何定义 oracle 与提名空间、相对 GB1 难在哪、预计四策略会如何分化）。目标读者：CEO（据此拍板选数据集，下一步派 worker 接入）。

## Context

- 现有流程的关键约束（决定数据集是否适配）：
  1. **oracle = 真值查表**：Agent 只能提名/评估**已测量的变体**（在测得 fitness 的集合内），不能评估无真值的变体。所以数据集必须有一个够大的"已测变体 + fitness"表。
  2. **主动学习闭环**：低阶冷启动 → 逐轮提名高阶 → 查真值回填重训。需要landscape里同时有低阶与高阶变体，且高阶峰不能被低阶数据线性外推出来（否则又太易）。
  3. **特征**：one-hot 需定长/定位点；**ESM-2 支持变长序列**，故变长/多位点数据集更适合 ESM 路线（这也是我们已有的能力）。
- 参考："我们的痛点"= 达峰太快、四策略同质。理想的更难数据集应让 **random 明显垫底、greedy 陷入局部、Agent/知识增强能靠推理与探索显出优势**。

## Required Reading

1. `harness/context/research/AI4S-assignment.md` — 题面（可用资源里点名 ProteinGym / FLIP / GFP / AAV / β-lactamase）。
2. `reports/report.pdf` §6–7 — 我们对 GB1"为何太易"的诚实分析（三档冷启动结论）。
3. `README.md` — 现有流程结构与接口（数据加载/特征/campaign 口径）。

## Entry Conditions

- 无阻塞；纯调研。

## Dependencies

- 无上游。下游：CEO 选定后派 worker 写新数据集 loader + 跑 campaign。

## Execution Surface

- 只读调研 + 写一份 markdown 报告到本任务 `artifacts/harder-dataset-survey.md`。不改代码、不下数据。

## Constraints

- **硬判据（逐项给候选打分/标注）**：
  a. **空间规模**：可变位点数 / 序列长度 / 理论组合数——要远大于 GB1 的 4 位点（使 greedy 无法廉价全扫、组合库无法平凡枚举）。
  b. **崎岖度/上位效应**：低阶（HD≤1/≤2）数据能否线性外推到高阶峰——越不能越好（越难）。给出文献里关于该数据集 epistasis / ML 外推难度的证据。
  c. **测量稀疏度**：已测变体数 / 理论空间——越稀疏，random/greedy 越吃力。
  d. **oracle 可行性**：已测"变体+fitness"表规模（能否支撑多轮查表 oracle）；WT 与目标（活性/亮度/稳定性/结合）明确。
  e. **可获取性**：公开、可下载、许可清楚（优先 FLIP / ProteinGym / 已发表 DMS）；给下载 URL 与大致文件大小。
  f. **接入成本**：相对我们现有 GB1 loader 的改造量（定长 vs 变长、位点定义、特征选择 one-hot/ESM）。
- **诚实纪律**：凡是凭模型知识给出的数字（规模/URL/split），**明确标注 [需核实]**，不要伪造精确统计或链接；不确定就说不确定。若 worker 具备联网检索能力则用之并附来源，否则如实说明是基于知识。
- 外部/破坏性动作禁止（不实际下载数据）。

## Checkpoint

- 命中即停：判据打分缺失、只罗列不推荐、编造精确数字或链接冒充已核实。计划回报点：候选清单 + 打分表 + Top-1 推荐 + 接入方案成稿即交。

## CI/Gate Authority Stop Condition

- 非 CI/gate 任务（docs-task，无门禁）。

## Implementation Plan

1. 枚举候选（至少覆盖）：**GFP/avGFP（Sarkisyan 2016）、AAV（FLIP）、β-lactamase/TEM-1、ProteinGym 里的高难 DMS assay、GB1 更难 split（FLIP low-vs-high / 1-vs-rest）、Meltome/热稳定**，可再补。
2. 对每个候选按判据 a–f 打分（表格），标注 [需核实] 项。
3. 结合"oracle=真值查表 + 主动学习闭环"的适配性筛选：哪些能直接插入、哪些需要改造。
4. 给 **Top-1 推荐 + 1-2 备选**，每个写：为何更难（对照 GB1）、下载源、字段、可变区/位点、如何切低阶冷启动、预计四策略分化、接入改造量与建议特征（one-hot vs ESM-2）。
5. 附一段"多数据集项目结构建议"（如 `data/<dataset>/` 一套 loader/manifest 的组织方式）。

## Deliverable Contract

- `artifacts/harder-dataset-survey.md`：候选打分表 + Top-1/备选推荐 + 每个推荐的接入方案 + 多数据集结构建议。回报：结论(选哪个)+ 依据(判据打分)+ 风险([需核实]项)+ 下一步(接入改造点)。

## Evidence Protocol

- 每个"更难"论断要有依据（判据打分或文献现象），不能只凭"感觉更大"。凡精确数字/链接未核实一律标 [需核实]，交 CEO 二次核实后再采信。

## Verification

- 报告含：≥5 个候选 × 6 项判据打分表；明确的 Top-1；每个推荐的可执行接入方案；[需核实] 项清单。CEO 亲自 ground-truth Top-1 的关键数字后拍板。
