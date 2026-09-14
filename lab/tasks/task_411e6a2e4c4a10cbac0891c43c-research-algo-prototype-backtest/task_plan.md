# Implementation: VoI 采集与高阶上位原型算法及 AAV 离线回测

Task Contract: harness-task v1

## Brief
将前置理论中的信息价值采样（VoI）方程与低秩稀疏上位特征投影实现为可执行 Python 算法模块，并在 AAV 真实数据集（38,265 条测定变体）上开展离线反事实回测仿真。

## Goal
输出一套独立的算法原型代码与离线回测验证战报：`artifacts/backtest-report.md`，定量对比标准贪心、启发式退火（v0.4/v0.5）与全新 VoI 算子在 288 预算下的达峰速度与探索税消融数据。

## Context
前序理论白皮书给出了 VoI 采集算子与残基接触图低秩张量投影的解析式。实测 v0.5 表明，简单启发式批次分配（48×6）在小批量下仍面临探索税稀释。需要在独立隔离 worktree 中构建真实算法原型并基于 AAV 真实历史池进行无偏离线回测。

## Required Reading
1. `reports/theoretical_foundations/01_higher_order_epistasis_theory.md`
2. `reports/theoretical_foundations/02_exploration_tax_and_voi_formalization.md`
3. `agent/auto_researcher.py` (现有 compose_batch 与门禁逻辑)
4. `models/train_ladder.py` (现有 EpistasisRidgePredictor)

## Entry Conditions
1. 真实数据 `data/aav/pools/` 存在且可读；
2. 独立 Worktree `.worktrees/t-algo-backtest` 已挂载且拥有独立执行环境。

## Dependencies
- 下游接收：AI4S 算法引擎升级、报告实证消融章节。

## Execution Surface
- 执行 Worktree: `/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-algo-backtest`
- 产物写入：`lab/tasks/task_411e6a2e4c4a10cbac0891c43c-research-algo-prototype-backtest/artifacts/`

## Constraints
1. 严禁修改主仓库已测试的生产模型代码，所有新算法原型均编写于独立原型目录中；
2. 严禁偷看未测候选标签，所有评估严格遵循冷启动与分轮查询协议；
3. 回测代码必须具备确定性随机种子（Seed 42），结果可完全复现。

## Checkpoint
- 完成 `voi_acquisition.py` 采集算子单元测试时；
- 完成低秩稀疏特征投影与 Ridge 拟合测试时；
- 跑通 6 轮回测并产出对比数据图表与报告时。

## CI/Gate Authority Stop Condition
算法原型实验任务，运行于隔离 worktree，无需修改 CI 权限。

## Implementation Plan
1. 在 worktree 中构建原型模块 `research/prototypes/voi_acquisition.py` 与 `sparse_epistasis_tensor.py`；
2. 编写回测驱动脚本 `research/prototypes/run_offline_backtest.py`；
3. 加载 AAV 10,433 冷启动数据，模拟在总预算 288（96×3 与 48×6）下的闭环采样；
4. 记录每轮候选累积最高适应度、强变体命中数与探索税指标；
5. 生成回测对比战报并落盘至 `artifacts/backtest-report.md`。

## Deliverable Contract
- 算法代码：`research/prototypes/voi_acquisition.py` 及回测脚本
- 回测报告：`lab/tasks/task_411e6a2e4c4a10cbac0891c43c-research-algo-prototype-backtest/artifacts/backtest-report.md`
- 结构化数据：`artifacts/backtest_metrics.json`

## Evidence Protocol
运行回测脚本，输出定量对比表格，并在报告中提供实测数据的详细日志与图表。

## Verification
- 运行单元测试验证 VoI 算子在退化条件下能平滑退火为贪心策略；
- 验证回测指标在 AAV 真实数据上可稳定复现。
