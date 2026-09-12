# T3 适应度预测模型阶梯 + 指标表（题目②）

Task Contract: harness-task v1

## Brief

在 T2 的三池+特征上建三级预测模型阶梯（one-hot+Ridge → ESM+XGBoost 主力 → MLP），统一 `fit→predict(mean,var)` 接口，产出 Spearman/Pearson/MSE/Top-k 指标表与图，供 T6 Agent 打分与 T7 闭环复用。

## Goal

`models/train_ladder.py` + 指标表（`reports/predictor_metrics.json`）+ 对比图。三级模型统一接口，L2（ESM+XGBoost）为主力；5-seed deep ensemble 方差作为不确定性（供 T7 UCB）。交付给 T6/T7；第一个使用方：T7 campaign 的策略②模型贪心。

## Context

- task：建预测模型并量化其识别高 fitness 变体的能力。fact：GB1 two_vs_rest 合理 Spearman 预期 0.55–0.75；L1≈0.2–0.4，L2≈0.4–0.6。decision：ESM-2 650M 本地实时（新版方案），one-hot 作 L1。
- 不确定性用 5-seed ensemble 方差替代 GP（CPU/算力友好）。

## Required Reading

1. `harness/context/research/AI4S-domain-research.md`（ML-guided DE、指标口径、SOTA 坐标）— 权威：领域。
2. `harness/context/architecture/AI4S-master-plan.html`（模型层设计、UCB）— 权威：架构。
3. T2 交付的 `features/` 与三池接口 — 权威：上游契约。

## Entry Conditions

- T2 的三池与 one-hot/ESM 特征缓存已生成且可加载；不成立则停止，等待 T2。

## Dependencies

- 上游：T2（特征+池）。下游：T6（Fitness Evaluator 调用）、T7（策略②/④）。判定满足：指标表生成且 T7 能加载模型 predict。

## Execution Surface

独立 worktree + 任务分支，base=main。允许写入：`models/`、`reports/`（预测指标产出）、`tests/`。绝对 cwd 由派工注入。

## Constraints

- 只从 T2 导出的接口取特征/池，不自行重切分。
- 指标口径固定：Spearman（主）+ Pearson + MSE + Top-k 命中率；报告须含「能否识别高 fitness 变体」的分析，不只贴数字。
- 不改 T2 文件面；外部/破坏性动作禁止。

## Checkpoint

命中即停：Spearman 显著低于预期区间（疑特征/标签错位，需回 T2 核对）、牵连面超出。计划回报点：指标表出炉后、发 commit 前。

## CI/Gate Authority Stop Condition

非 CI/gate 任务；需改门禁面则停止记 blocker 请求治理任务。

## Implementation Plan

- 统一模型基类 `fit(X,y)` / `predict(X)->(mean,var)`；L1 Ridge、L2 XGBoost（主力）、L3 MLP。
- 5-seed ensemble 训练，方差作不确定性；导出模型加载接口供 T6/T7。
- 指标脚本：Spearman/Pearson/MSE/Top-k，train/val/test 三分，出对比表+图。
- `ha fact record` 晋升三级模型 Spearman 实测值。

## Deliverable Contract

代码 + `reports/predictor_metrics.json` + 图 + 定向测试。回报字段：三级模型各自 Spearman/Pearson/MSE/Top-k、ensemble 方差范围、模型加载接口签名。

## Evidence Protocol

粒度到模型级。阴性对照：打乱标签后 Spearman 应塌到 ~0；同 seed 复现一致。reviewer 拒收：无 Top-k、无高 fitness 识别分析、Spearman 异常未排查。收口记一条 fact 并存回执。

## Verification

- 停止点 = 便宜确定性门全绿 + 定向测试全绿 + 本地 commit。
- 定向测试：`tests/test_predictor.py`（接口契约、指标计算正确性、shuffle 阴性对照、复现性）；贴真实输出。
- 至少记录一条 fact。
