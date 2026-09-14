# Agent 推理过程:补「为什么组合某些突变」(结果展示 d-iii)

产物版本:`workflow-v1.1`。

## Brief

试题「三、详细要求 → 结果展示 → d. 展示 Agent 的推理过程」四个子项里,本仓缺 iii
「为什么组合某些突变」。范围**已由 CEO 复核后缩小**:i「发现哪些位点可能重要」已由包2
交付(`AnalystReport.position_gains`,实测形如 `{39: 2.0, 40: 1.8, 41: 0.0, 54: 1.5}`),
ii 已有(`Hypothesis.rationale` + `rule_ids`),iv 已有(critic 拒收 + 失败分析章节)。
**本任务只做 iii。**

## Goal

`MutationDesigner` 组合单点成候选时,把组合理由结构化记录并落进事件流,
使 `app/demo.py` 的五角色回放能展示「为什么把这几个突变组合在一起」。

## Context

依赖已解除:包2(task_d72b24d5452f2e96e6a94769b1)已合入主线。
主线现在是 `origin/main` = `312ef0b`,自包含测试集合 42 passed。

## Required Reading

- `agent/pipeline.py` 全文(尤其 `MutationDesigner` 与 `AnalystReport`)
- `tests/test_agent.py`
- `evolution/campaign.py:193` 附近(`_llm_hypothesis` 的 `state["source"]` fallback 记账法)

## Entry Conditions

worktree `.worktrees/t-reasoning` 已建好(分支 `t-reasoning`,基于 `origin/main`),
`.venv` 与 `data/pools` 已符号链接。

## Dependencies

包2 已合入,无剩余阻塞。注意 `Makefile`/`README.md` 与 `app/demo.py` 另有 worker 在飞。

## Execution Surface

可动:`agent/pipeline.py`、`tests/test_agent.py`、`lab/reports/workflow-v1.1/` 下一份
展示样例。**不要动** `evolution/campaign.py`、`models/`、`knowledge/`、`events/`、
`app/demo.py`、`Makefile`、`README.md`。

## Constraints

**不得回退**(包2 与集成收口刚做的):
- `run_pipeline` 签名 `(pool, predictor, *, event_store, llm_hypothesis, llm_critic, budget,
  round_id, no_knowledge)` —— `evolution/campaign.py` 在调它。
- 候选与 149,361 实测集合**求交**的约束。
- 知识规则的 `enforcement: gate|advisory` 分类,`ScientificCritic` 只对 gate 类求 `all()`。
- `AnalystReport.position_gains`。

**诚实性**:组合理由里的统计量(单点增益等)是**从实测数据算出来的,不是 LLM 说的**,
字段命名与展示必须能区分「统计量」与「LLM 生成的自然语言」。LLM 不可用时走 fallback,
`state["source"]` 如实记 `fallback`,**不许把 fallback 的理由展示成 LLM 的推理**。

## Checkpoint

若发现 i 其实没交付完整、或组合理由无法在不改 `run_pipeline` 签名的前提下落进事件流,
**带证据回报并停手**。

## CI/Gate Authority Stop Condition

停止点 = `pytest tests/test_agent.py tests/test_campaign.py` 绿 + commit。
**不 push、不发 PR、不打 tag。** 不要跑全量矩阵(同机有其他 worker)。

## Implementation Plan

`MutationDesigner` 记录每个候选组合的理由,至少说明:哪几个单点被选中组合;
**为什么组合它们**(引用各自单点增益、位点是否互不冲突、命中了哪条规则);并引 `rule_ids`,
与现有 `Hypothesis.rationale` 做法一致。理由**进 schema**(不是只打印)并**落进事件流**。

## Deliverable Contract

- 改造后的 `agent/pipeline.py`。
- `tests/test_agent.py` 新增测试。
- `lab/reports/workflow-v1.1/` 下一份展示样例(一轮的若干组合理由)。

## Evidence Protocol

- 断言组合理由**非空**、**引了 `rule_ids`**、**能在事件流里找到**。
- **阳性对照**:把理由生成改坏后测试必须变红。空结果不算通过。
- 区分标注哪些字段是实测统计量、哪些是 LLM 文本。

## Verification

- `pytest tests/test_agent.py tests/test_campaign.py` 在冻结提交树上全绿。
- CEO 会自己在事件流里 grep 组合理由,并手算一个单点增益核对。
