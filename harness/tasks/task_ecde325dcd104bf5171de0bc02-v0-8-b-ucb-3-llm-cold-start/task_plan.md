# 实验 v0.8-B:UCB β=3 达峰结论的稳健性(训练随机性与 cold-start 扰动)

Task Contract: harness-task v1

## Brief

v0.7 的 30 seed × 7 方法矩阵给出了 UCB β=3 确定性 30/30 达峰,但红队指出这 30 次**不是 30 个独立样本**:均值/UCB 路径不消耗采集随机数,30 次跑的是同一条确定性轨迹,Wilson 置信区间对它无效。本任务在**真正会变的两个维度**上测稳健性。

## Goal

产出 `harness/reports/agentic-v0.8b/report.md`,回答:UCB β=3 的达峰在(a)surrogate 训练随机性(alpha 选择的 CV 划分 seed)与(b)cold-start 组成扰动(重采样 cold-start 子集)两个维度下还成立吗?给出达峰率与置信区间(这次是**有效的**区间,因为样本确实独立),以及失败时 β 需要多大才能补回来。首个消费者:最终报告 v2.0 的稳健性一节。

## Context

- `F-885537A3` 与 `harness/context/research/v07-multiseed-robustness.md` 表格:UCB β=3 → 30/30、cum_top10_max 8.4162±0、strong=128;低 β(0.5/1/2)反而全停 6.5309;纯均值 0/30 但 strong=166。
- 红队原文标注了 † 的无效 CI:`harness/context/research/v07-redteam-critique.md` 第三击。
- 机制约束(`v06-backtrack-analysis.md`):真峰进入 UCB 头部是**路径依赖**的(第 3 轮状态下 UCB 排名 #15,cold-start 状态下各 β 都在 #426–539)。所以扰动 cold-start 很可能直接改变达峰,这正是要测的。

## Required Reading

1. `harness/context/research/v07-multiseed-robustness.md`(**权威**:基线口径与 † 声明)。
2. `harness/context/research/v06-backtrack-analysis.md`(路径依赖机制)。
3. `models/train_ladder.py`(alpha 选择与 CV 划分在哪引入随机性)。
4. `agent/auto_researcher.py`(采集路径)。
5. `evolution/datasets.py`(cold-start 口径,重采样必须保持 HD≤2 定义不变)。

## Entry Conditions

独立 worktree(建议 `t-v08b`),`.venv` 与 `data/aav/full_data.csv` symlink 好;能复现 UCB β=3 的 30/30 基线。复现不了就停。

## Dependencies

上游:v0.7 UCB 实现。下游:报告 v2.0 稳健性一节。并发:与 v0.8-A/C 同改 `agent/auto_researcher.py` 文件面,**不得并行**或各自独立 worktree。

## Execution Surface

分支 `t-v08b`;允许写 `harness/reports/agentic-v0.8b/**` 与实验脚本;`models/train_ladder.py` 仅允许加可选的随机种子参数,不得改默认行为。禁区:池口径、surrogate 模型定义、已有 report、CI/oracle。

## Constraints

- **answer-agnostic**:重采样 cold-start 不得看 fitness 标签来挑子集(按 HD 与序列身份随机采,不按适应度)。
- 预注册:扰动幅度、重复次数、β 取值范围开跑前写进 report。
- 不得因为结果不好就换扰动方式。

## Checkpoint

跑完第一个扰动维度即停并报达峰率。**异议型停**:若发现 cold-start 一扰动达峰率就崩到接近 0,这是重要负结果,停下来先报,不要自动去加大 β 补救。

## CI/Gate Authority Stop Condition

非 CI/gate 任务。已知本仓 standard-task 的 ci 门结构性不可满足(fact `F-8ED77039`),submit/complete 会被拒;不绕门、不改 CI,失败即记录停手。

## Implementation Plan

- 维度 a:固定 cold-start,变 surrogate 训练随机性(≥20 次独立),统计达峰率 + 有效 Wilson CI。
- 维度 b:固定训练 seed,重采样 cold-start 子集(≥20 次),同上。
- 若某维度达峰率显著下降,做 β ∈ {3,4,5,6} 扫描看能否补回,并如实报告"需要多大 β"。
- 进度用 `ha task progress append`;承重结论 `ha fact record --task task_ecde325dcd104bf5171de0bc02`。

## Deliverable Contract

`harness/reports/agentic-v0.8b/report.md`(预注册参数 + 两维度达峰率 + 有效 CI + β 补救扫描)、指标 JSON、事件链;≥1 fact;回报两个达峰率与结论。

## Evidence Protocol

明确区分"确定性重复"与"独立样本";本任务的 CI 必须是有效的并说明为何有效。阴性对照必跑。

## Verification

停手点 = report + 指标 + ≥1 fact + 定向测试绿。CEO 语义验收:CI 有效性论证是否站得住。
