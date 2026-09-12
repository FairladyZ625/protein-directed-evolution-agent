# 实验 v0.8-C:知识库残基对缺测覆盖引导探索落地

Task Contract: harness-task v1

## Brief

现在链路里的"知识库"只是二元门禁(HD≤4 且 mean BLOSUM62≥0),没有任何引导作用。KB 研究(`F-159073F2`)发现:cold-start 覆盖了全部 378 个位点对,但门内 11130 种**具体残基对**中有 7937 种从未被测(占 9533 个候选的 71.88%)。本任务把这个覆盖信号从"统计发现"变成"采集引导",并诚实测它有没有用。

## Goal

产出 `harness/reports/agentic-v0.8c/report.md`,交付一个把 KB 从**门禁**升级为**探索先验**的实现(候选按"引入多少未测残基对"+ 理化多样性打分,接进 explore 批次排序),并给出它对达峰率与 strong 产量的影响。**允许且预期结果是负的**——KB 研究已明说"未证明能提高达峰率"。

## Context

- `F-159073F2` 与 `harness/context/research/kb-iteration-research.md`:首选方案=具体残基对缺测覆盖 + 理化多样性;次选=结构接触软权重;DCA 与新 ESM 推理明确后置(ESM zero-shot 在本题已是实测负例)。
- 机制挂钩:`harness/context/research/v07-peak-mechanism.md` 判定峰隐形的根因之一正是"关键二阶组合缺测"。所以覆盖引导在机制上**应该**有用——但机制合理不等于有效,必须实测。
- 现有 KB:`knowledge/rules.yaml`(BLOSUM62 + 20 氨基酸理化属性)、`knowledge/validators.py`(两条规则);`build_knowledge_graph` 当前无调用点。

## Required Reading

1. `harness/context/research/kb-iteration-research.md`(**权威**:方案与接口草案)。
2. `harness/context/research/v07-peak-mechanism.md`(为什么覆盖可能有用)。
3. `knowledge/rules.yaml` + `knowledge/validators.py`(**待改主体**)。
4. `agent/auto_researcher.py` 的 `_gate` / `check_knowledge` / `explore_batch`(接线点)。
5. `analysis/esm_zeroshot_scan.py`(负例,别把 PLM 当银弹)。

## Entry Conditions

独立 worktree(建议 `t-v08c`),symlink 就位;UCB β=3 与 greedy 两条基线可复跑作对照。

## Dependencies

上游:KB 研究结论。下游:报告 v2.0 的知识库一节。并发:与 v0.8-A/B 同改 `agent/auto_researcher.py`,不得并行。相关:GB1 遗留清理任务(`task_ff24b0e33edb3412f4dd070e4b`)最好先做,否则会在脏代码上改。

## Execution Surface

分支 `t-v08c`;允许写 `knowledge/**`、`agent/auto_researcher.py` 的采集排序路径、`harness/reports/agentic-v0.8c/**` 与测试。禁区:池口径、surrogate 定义、已有 report、CI/oracle。

## Constraints

- **answer-agnostic 硬红线**:覆盖统计脚本**不得读取 fitness 列**(KB 研究的审计脚本已做到,照抄该边界)。
- 对照必须同预算同池;新引导只改排序,不改门禁口径(9533 不变)。
- 结果为负就如实写,不得调参到好看。

## Checkpoint

接线完成、能跑通一个 seed 即停并报:引导前后批次组成差异 + 首个 seed 的达峰与 strong。**异议型停**:若发现引导让 strong 明显下降而达峰没提升,这就是结论,停下来报,不要继续调权重。

## CI/Gate Authority Stop Condition

非 CI/gate 任务。本仓 standard-task 的 ci 门结构性不可满足(`F-8ED77039`);不绕门、不改 CI。

## Implementation Plan

- 实现残基对覆盖打分(只用序列身份与已测集合,不看标签)+ 理化多样性项。
- 接进 explore 批次排序,保留开关以做消融。
- 三档对照:关闭引导 / 开启引导 / UCB β=3 纯基线,各 ≥3 seed。
- `ha fact record --task task_135d946b4d8fa566d87b063fa6` 记结论(正负皆可)。

## Deliverable Contract

`harness/reports/agentic-v0.8c/report.md`(实现说明 + 三档对照表 + 诚实判定)、指标、事件链;≥1 fact;回报引导有没有用、代价是什么。

## Evidence Protocol

覆盖脚本的 answer-agnostic 边界要能被独立复核(贴出它读了哪些列);每个数标实测。

## Verification

停手点 = report + 三档对照 + ≥1 fact + 定向测试绿。CEO 语义验收:answer-agnostic 是否守住、负结果是否诚实。
