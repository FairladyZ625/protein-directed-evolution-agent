# 重新框定优化目标:池内 top-k 确认产量 vs 单峰命中

Task Contract: harness-task v1

## Brief

红队第一击命中了整个任务设定:我们一直在追的"池内全局峰"fitness = 8.4162,而 **cold-start 起点里已经有 9.5365 的 incumbent**。也就是说"成功达峰"并不等于"拿到了更好的蛋白"。本任务决定最终报告用什么指标来定义成功,并把这个选择的理由与代价写清楚。

## Goal

产出 `lab/context/research/objective-reframing.md`(≤200 行,结论优先),给出一个**可辩护的目标函数定义**并说明为什么其它候选被否掉。候选至少包括:(a) 单峰命中率(现状);(b) 预算内实测确认的 top-k 强变体产量;(c) 相对 cold-start incumbent 的净提升;(d) 简单后悔(regret)。对每个候选写:它奖励什么行为、它在本题下会不会退化成平凡解、它能不能跨数据集迁移。首个消费者:最终报告 v2.0 的"问题设定"章。

## Context

- 事实基线:池 27832 / cold-start 10433 / 门内候选 9533 / 预算 288;池内 max = 8.4162(`QEEEIRTTNPVATEQYGEASTNLQRGNR`,HD3);**cold-start 已含 9.536457**。
- `F-885537A3`:两个目标要求相反的策略——greedy 赢 top-10% 产量(strong=166),UCB β=3 赢单峰(30/30)。**目标定义直接决定谁是赢家**,这正是本任务必须谨慎的原因。
- 红队原文:`lab/context/research/v07-redteam-critique.md` 第一击。
- 建设性收口:`lab/context/research/v07-constructive-conclusion.md` 已倾向"最大化实测确认的强变体期望产量"。
- FLIP-AAV 原生是**回归基准**(比 Spearman),稀疏 ~284k、无规范全局最优——"池式优化+达峰"是本项目自造的任务构造,报告必须声明。

## Required Reading

1. `lab/context/research/v07-redteam-critique.md`(**权威**:为什么现有目标有问题)。
2. `lab/context/research/v07-constructive-conclusion.md`(**权威**:决策论候选答案)。
3. `lab/context/research/v07-multiseed-robustness.md`(两指标下的实测排名反转)。
4. `evolution/datasets.py`(池与 cold-start 的确切口径)。
5. `lab/context/research/v07-consolidated-summary.md` 第 4 节(诚实边界清单)。

## Entry Conditions

上述五份文档可读;9.5365 这个数可在 cold-start 数据里复算确认。复算不出来就停下报。

## Dependencies

上游:v0.7 红队与建设性两路结论。下游:最终报告 v2.0(`task_db4ace109f72a92847c7349fe1`)、图表重绘(`task_f9a282c594dbb92bf1b9e0a18b`)——两者都依赖本任务定下的指标。并发:无文件面冲突(只写一份新研究文档)。

## Execution Surface

仓库根或独立 worktree;允许写 `lab/context/research/objective-reframing.md`。禁区:所有产品代码、已有 report、v0.7 及更早研究文档(只读)。

## Constraints

- 不得为了让某个已有结论好看而选指标——**先定义,再看谁赢**,并在文档里明示定义顺序。
- 不得删除或淡化"峰 < incumbent"这个事实;报告必须正面自曝。
- 不改产品代码、不重跑实验。

## Checkpoint

写完即停并报:选定指标一句话 + 它奖励什么行为 + 在这个指标下 greedy/UCB β=3/LLM 三者的排名会不会变。**异议型停**:若结论是"现有单峰指标其实是对的、不该换",如实说,不硬造改动。

## CI/Gate Authority Stop Condition

非 CI/gate 任务(docs-task 无 CI 门)。不碰 CI/门禁/oracle。

## Implementation Plan

- 复算 cold-start incumbent 与池内 max,确认 9.5365 > 8.4162。
- 对四个候选指标各写:定义式、奖励的行为、退化风险、跨数据集可迁移性。
- 在选定指标下重算 greedy / UCB β=3 / LLM 三者排名,明确说明排名是否反转。
- `ha fact record --task task_cec65c821f05a08d9a86681332` 记承重结论。

## Deliverable Contract

`lab/context/research/objective-reframing.md`(≤200 行);≥1 fact;回报选定指标 + 排名是否反转。不改代码、不 push。

## Evidence Protocol

每个数标明实测/推断;指标定义顺序(先定义后看结果)必须在文档中可核。

## Verification

停手点 = 文档 + ≥1 fact + 摘要回报。CEO 语义验收(指标是否可辩护、是否诚实)不可下放。
