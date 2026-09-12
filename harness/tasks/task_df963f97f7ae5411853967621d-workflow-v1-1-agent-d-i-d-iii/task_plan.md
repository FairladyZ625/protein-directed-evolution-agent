# Agent 推理过程显式化(位点重要性 + 突变组合理由)

产物版本:`workflow-v1.1` —— 交付主线下一版。

## Objective

### 依赖(重要:不要提前开工)


本任务与 `task_d72b24d5452f2e96e6a94769b1`(包2:五角色流水线补三项硬约束)**改同一个文件**
`agent/pipeline.py`。包2 在先,本任务必须在包2 的交付合入后、基于其结果开工,否则文件面冲突。
派工由 CEO 在包2 落地后触发。

### 缺口(CEO 已核实)


笔试题「三、详细要求 → 结果展示 → d. 展示 Agent 的推理过程」有四个子项,本仓**缺两个**:

| 子项 | 状态 | 现状证据 |
|---|---|---|
| i. 发现哪些位点可能重要 | ❌ 缺 | 全仓 grep 无位点重要性输出 |
| ii. 为什么选择某些氨基酸替换 | ✅ 有 | `Hypothesis.rationale` + `rule_ids` |
| iii. 为什么组合某些突变 | ❌ 缺 | `MutationDesigner` 组合时不记理由 |
| iv. 哪些推荐失败,原因可能是什么 | ✅ 有 | critic 拒收 + 失败分析章节 |

## Scope

### 要做什么


1. **位点重要性(子项 i)**:`DataAnalyst` 已经在统计替换频次,把它显式产出成
   **位点重要性排序**——每个可变位点给一个重要性度量(至少两种口径:观测到的有益替换比例、
   以及该位点上的最大实测增益),写进 `AnalystReport` 的结构化字段,并落进事件流。
   不要只打印,要进 schema —— 前端要读它。
2. **组合理由(子项 iii)**:`MutationDesigner` 把每个候选组合的**生成理由**记下来:
   哪几个单点被选中、为什么组合它们(例如各自的单点增益、位点是否互不冲突、
   是否命中某条规则)。理由要引 `rule_ids`,与现有 `Hypothesis.rationale` 的做法一致。
   落进事件流,让模块②的五角色回放能展示出来。
3. **前端可见**:`app/demo.py` 的五角色回放模块要能把上面两样展示出来。
   注意 demo 另有 worker 在改(`task_2f3e8c6ef4a9fe116477c3b70c` 加 WT 输入),
   本任务开工时那边应已合入;若仍在飞,**只改 pipeline 侧并把前端改动留成后续任务**,
   不要和它抢同一个文件。

### 交付物


- 改造后的 `agent/pipeline.py`(位点重要性进 `AnalystReport`;组合理由进候选与事件流)。
- `tests/test_agent.py` 补测试:断言位点重要性字段存在且数值与手算一致;
  断言组合理由非空且引了 `rule_ids`;**阳性对照**——把重要性统计改坏后测试要红。
- `harness/reports/workflow-v1.1/` 下一份展示样例(一轮的位点重要性表 + 若干组合理由)。

## Approach

### 诚实性约束


- 「位点重要性」是**从实测数据统计出来的**,不是 LLM 说的。要在字段命名与报告里区分清楚
  哪些是统计量、哪些是 LLM 生成的自然语言理由。
- LLM 不可用时走 fallback,`state["source"]` 要如实记成 `fallback`(沿用现有机制),
  **不许把 fallback 的理由展示成 LLM 的推理**。

## Verification

### 验收(CEO 亲验)


- `pytest tests/test_agent.py` 在冻结提交树上全绿,阳性对照真的能红。
- 我会自己手算一个位点的重要性数值核对,并在事件流里 grep 组合理由。

## Handoff

### 边界


- 独立 worktree,基于包2 合入后的 `origin/main`。
- **只动** `agent/pipeline.py`、`tests/test_agent.py`、`harness/reports/workflow-v1.1/`。
- 停止点 = 点名测试绿 + commit。**不 push、不发 PR。**
