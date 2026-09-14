# Agent 推理过程:补「为什么组合某些突变」(结果展示 d-iii)

依赖已解除:包2(五角色硬约束)已合入主线,可以开工。范围**已缩小**,见下。

## 范围已缩(CEO 复核后)

试题「结果展示 → d. 展示 Agent 的推理过程」四个子项:

| 子项 | 状态 |
|---|---|
| i. 发现哪些位点可能重要 | ✅ **已交付** —— 包2 已把 `position_gains` 加进 `AnalystReport`(实测形如 `{39: 2.0, 40: 1.8, 41: 0.0, 54: 1.5}`) |
| ii. 为什么选择某些氨基酸替换 | ✅ 已有 —— `Hypothesis.rationale` + `rule_ids` |
| **iii. 为什么组合某些突变** | ❌ **缺,本任务只做这一条** |
| iv. 哪些推荐失败,原因可能是什么 | ✅ 已有 —— critic 拒收 + 失败分析章节 |

**只做 iii。** 不要重做 i,也不要改 `position_gains` 的现有实现。

## 要做什么

`MutationDesigner` 在把单点组合成候选时,**把组合理由记下来**。理由要说清:
- 哪几个单点被选中组合进这个候选;
- **为什么组合它们** —— 至少引用:各自的单点增益(可从 `AnalystReport.position_gains` 取)、
  位点是否互不冲突、以及命中了哪条规则;
- 引 `rule_ids`,与现有 `Hypothesis.rationale` 的做法保持一致。

理由要**进 schema**(不是只打印),并**落进事件流**,让 `app/demo.py` 的五角色回放能展示。

## 诚实性约束

- 组合理由里的**统计量(单点增益等)是从实测数据算出来的,不是 LLM 说的**。
  字段命名与展示上必须能区分「统计量」与「LLM 生成的自然语言」。
- LLM 不可用时走 fallback,`state["source"]` 如实记 `fallback`(沿用现有机制),
  **不许把 fallback 的理由展示成 LLM 的推理**。

## 不得回退(包2 与集成收口刚做的)

- `run_pipeline` 的签名:
  `run_pipeline(pool, predictor, *, event_store, llm_hypothesis, llm_critic, budget, round_id, no_knowledge)`
  —— `evolution/campaign.py` 在调它,**不要改签名**。
- 候选与 149,361 实测集合**求交**的约束。
- 知识规则的 `enforcement: gate|advisory` 分类,以及 `ScientificCritic` 只对 gate 类求 `all()`。
- `AnalystReport.position_gains`。

## 验收(CEO 亲验)

- `pytest tests/test_agent.py tests/test_campaign.py` 在冻结提交树上全绿
  (当前主线是 42 passed 的自包含集合,别弄红)。
- 新增测试:断言组合理由**非空**、**引了 `rule_ids`**、且**能在事件流里找到**;
  **阳性对照** —— 把理由生成改坏后测试必须变红。
- 我会自己在事件流里 grep 组合理由,并手算一个单点增益核对。

## 边界

- worktree `.worktrees/t-reasoning`(分支 `t-reasoning`,基于最新 `origin/main`)。
- 可动:`agent/pipeline.py`、`tests/test_agent.py`、`lab/reports/workflow-v1.1/` 下
  一份展示样例(一轮的若干组合理由)。
- **不要动** `evolution/campaign.py`、`models/`、`knowledge/`、`events/`、`app/demo.py`、
  `Makefile`、`README.md` —— 另有 worker 在飞。
- 停止点 = 点名测试绿 + commit。**不 push、不发 PR。**
- 发现 CEO 判断有误就带证据回报并停手。
