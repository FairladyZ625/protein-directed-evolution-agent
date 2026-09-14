# T5 知识库 / 突变规则库（题目④）

Task Contract: harness-task v1

## Brief

构建定向进化知识库：氨基酸理化性质表 + 突变规则（保守/激进替换、突变数上限、禁终止子等）+ networkx 三元组知识图谱，并提供 `--no-knowledge` 消融开关，供 T6 Agent 决策与 A/B 对比。

## Goal

`knowledge/rules.yaml`（业务级：20aa 理化性质、BLOSUM62 保守分级、突变数≤4、禁终止子/异常氨基酸、优先组合历史好单点）、`knowledge/validators.py`（实现级校验器）、networkx 三元组图谱（位点—突变—性质—fitness），`--no-knowledge` 开关。交付给 T6（规则检索/校验）与 T7（策略③无知识 vs ④知识增强对比）。

## Context

- task：搭知识/规则库。fact：题目④明列可包含的知识（理化性质/保守替换/突变数限制/禁终止子/优先历史好突变）与图谱三元组样例。decision：图谱用轻量 networkx，不上 neo4j。
- 规则须可被 Agent 的 rationale 引用（规则 ID），支撑「知识增强 vs 无知识」消融。

## Required Reading

1. `lab/context/research/AI4S-assignment.md`（题目④原文：知识内容清单与图谱三元组）— 权威：题面要求。
2. `lab/context/architecture/AI4S-master-plan.html`（知识增强层三层结构）— 权威：设计。

## Entry Conditions

- 无外部依赖，可 Day1 与 T2/T4 并行开工。

## Dependencies

- 上游：无。下游：T6（Hypothesis Generator 引规则 ID、Scientific Critic 校验）、T7（消融对比）。判定满足：validators 可对候选突变返回规则命中/违规，`--no-knowledge` 可关闭。

## Execution Surface

独立 worktree + 任务分支，base=main。允许写入：`knowledge/`、`tests/`（本任务测试）。绝对 cwd 由派工注入。文件面与 T2/T4 不重叠,可并行。

## Constraints

- 规则表数据可查证（BLOSUM62、标准理化性质），不编造数值。
- 每条规则有稳定 ID 供 rationale 引用；图谱三元组与题目④样例结构对齐。
- 知识「点到为止」，不堆砌无关蛋白学；外部/破坏性动作禁止。

## Checkpoint

命中即停：需触碰 T6/T7 文件面、规则口径与题面冲突。计划回报点：rules.yaml+validators 打通后、图谱构建后。

## CI/Gate Authority Stop Condition

非 CI/gate 任务；需改门禁面则停止记 blocker。

## Implementation Plan

- `rules.yaml`：20aa 理化性质（疏水性/电荷/大小/极性）、BLOSUM62 保守分级、突变数上限、禁终止子、递增/优先组合策略——每条带 ID。
- `validators.py`：输入候选突变 → 返回 `{rule_id, pass/violate, note}` 列表；`--no-knowledge` 短路。
- networkx 图谱：AminoAcid-has_property、Mutation-occurs_at-Position、Mutation-improves-Fitness、Variant-contains-Mutation。
- `ha fact record` 晋升「规则库覆盖的约束条数与图谱三元组数」。

## Deliverable Contract

代码 + rules.yaml + 图谱构建 + 定向测试。回报字段：规则条数与 ID 列表、图谱节点/边数、`--no-knowledge` 开关生效证据。

## Evidence Protocol

阴性对照：`--no-knowledge` 下 validators 不产生任何约束；激进替换应被规则命中、保守替换放行。reviewer 拒收：规则无 ID、图谱结构与题面不符、消融开关无效。收口记一条 fact。

## Verification

- 停止点 = 便宜确定性门全绿 + 定向测试全绿 + 本地 commit。
- 定向测试：`tests/test_knowledge.py`（规则命中/放行、图谱结构、消融开关）；贴真实输出。
- 至少记录一条 fact。
