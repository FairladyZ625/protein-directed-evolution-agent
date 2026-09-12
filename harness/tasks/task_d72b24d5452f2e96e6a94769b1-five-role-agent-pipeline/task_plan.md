# T6 五角色科学智能体流水线（题目③）

Task Contract: harness-task v1

## Brief

用 PydanticAI 实现五角色 Agent 流水线（Data Analyst → Hypothesis Generator → Mutation Designer → Fitness Evaluator → Scientific Critic），LLM 仅在两处受控出现（输出 Pydantic schema），模拟科学家「假设生成→突变设计→模型评估→反馈」流程,并把每步写入事件流供回放。

## Goal

`agent/` 下五角色模块 + 编排入口。角色分工：Data Analyst（纯代码，位点收益/突变谱统计，0% LLM）、Hypothesis Generator（LLM①，读报告+检索 T5 规则，rationale 须引规则 ID）、Mutation Designer（纯代码，≤4 突变组合生成/去重/预算控制）、Fitness Evaluator（纯函数 port，调 T3 模型返回 mean/var）、Scientific Critic（T5 规则校验 + LLM② 低温复核）。交付给 T7（策略③④调用）；每步 append 事件到 T4。

## Context

- task：搭 Agent 流水线。decision：runtime 用 PydanticAI（新版方案），LLM 走商业 API；LLM 只在 Hypothesis Generator 与 Scientific Critic 受控出现,其余纯代码,防「Agent 只是套壳调模型」。
- 叙事红线：不吹「学到科学家思维」,用消融数据说话（T7 负责对比）。

## Required Reading

1. `harness/context/research/AI4S-assignment.md`（题目③五角色功能清单）— 权威：题面。
2. `harness/context/architecture/AI4S-master-plan.html`（Agent 编排层：PydanticAI、受控两处、schema）— 权威：设计。
3. T3 模型加载接口、T4 事件 append 接口、T5 validators/规则检索接口 — 权威：上游契约。

## Entry Conditions

- T3（模型 predict）、T4（事件 append）、T5（规则/校验）三者接口就绪；任一缺失则停止等待。

## Dependencies

- 上游：T3 + T4 + T5（汇聚点）。下游：T7（四策略之策略③无知识 Agent、策略④知识增强 Agent）。判定满足：给定当前池，Agent 能产出带 rationale 的 Top-k 候选并落事件。

## Execution Surface

独立 worktree + 任务分支，base=main。允许写入：`agent/`、`tests/`（本任务测试）。绝对 cwd 由派工注入。

## Constraints

- LLM 只在 Hypothesis Generator + Scientific Critic 出现，且必须 `output_type=Pydantic schema`；其余角色纯代码。
- 提名候选限定在 149,361 可测变体空间（与 decision 一致）。
- rationale 必须可引用 T5 规则 ID；LLM 调用失败要有降级链。外部/破坏性动作禁止。

## Checkpoint

命中即停：LLM schema 遵循失败无降级、提名越出可测空间、需触碰上游文件面。计划回报点：单轮五角色跑通、事件落盘可回放后。

## CI/Gate Authority Stop Condition

非 CI/gate 任务；需改门禁面则停止记 blocker。

## Implementation Plan

- 定义各角色的 Pydantic 输入/输出 schema；PydanticAI `Agent` 驱动受控两处。
- Data Analyst：从当前池统计位点收益/突变谱。Hypothesis Generator：读统计+检索规则→提假设（引规则 ID）。Mutation Designer：把假设展开为 ≤4 突变的合法候选、去重、控预算。Fitness Evaluator：调 T3 模型打分（mean/var）。Scientific Critic：规则校验+低温 LLM 复核，三件套（score+rule_check+note）放行。
- 每角色步骤 append 事件到 T4。
- `ha fact record` 晋升「单轮五角色端到端产出 Top-k 候选」。

## Deliverable Contract

代码 + 定向测试 + 一段可回放的事件样例。回报字段：五角色接口、LLM 受控两处的 schema、单轮产出的 Top-k 候选与 rationale 样例。

## Evidence Protocol

阴性对照：Scientific Critic 应拒掉违反规则的候选（激进替换/超突变数）。reviewer 拒收：LLM 出现在受控两处之外、rationale 不引规则 ID、提名越界。收口记一条 fact。

## Verification

- 停止点 = 便宜确定性门全绿 + 定向测试全绿 + 本地 commit。
- 定向测试：`tests/test_agent.py`（各角色 schema、Critic 拒违规候选、提名空间约束、事件落盘）；贴真实输出。
- 至少记录一条 fact。
