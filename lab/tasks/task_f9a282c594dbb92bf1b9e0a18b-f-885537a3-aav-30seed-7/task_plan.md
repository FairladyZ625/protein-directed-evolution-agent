# 科学图表按 F-885537A3 重绘 AAV 面板

Task Contract: harness-task v1

## Brief

现有五张核心科学图(`reports/figures/`)生成于 v0.7 早期的 12 配置矩阵,AAV 面板尚未反映后来的翻转结论。本任务只重绘 AAV 相关面板,GB1 面板与生成管线保持不变。

## Goal

更新 `reports/figures/` 中的 AAV 面板,使其呈现 `F-885537A3` 的最终定性:30 seed × 7 方法矩阵、**两指标分裂**(纯利用 strong=166 但达峰 0/30;UCB β=3 达峰 30/30 但 strong=128),并在图注里标明确定性方法的 30 次不是独立样本。首个消费者:最终报告 v2.0。

## Context

- 数据源:`lab/context/research/v07-multiseed-robustness.md` 的完整表(含 † 标注的无效 CI)。
- 现有生成管线:`scripts/figures/generate_all.py` + `scripts/figures/verify_figures.py` + `artifacts/figures_data/` 的 13 份源钉度量快照(上一轮验收通过,机制可靠,复用不重写)。
- 上一轮已修过的两个科学性问题**必须继续守住**:GB1 冷启动 regime 不得混用;AAV 的 cold-start incumbent 不得与新查询最大值混为一谈。
- 指标口径若被 `task_cec65c821f05a08d9a86681332` 改动,以那个任务的结论为准。

## Required Reading

1. `lab/context/research/v07-multiseed-robustness.md`(**权威**:所有新数字)。
2. `reports/figures/figure-generation-summary.md`(**权威**:现有管线与已修问题)。
3. `scripts/figures/generate_all.py` + `verify_figures.py`(**待改主体**)。
4. `lab/context/research/v07-consolidated-summary.md` 第 1、4 节(定性与边界)。

## Entry Conditions

现有管线可复跑并通过 `verify_figures.py`。跑不通先修管线再改图,不要在坏管线上出图。

## Dependencies

上游:v0.7 多 seed 矩阵、目标重框定任务。下游:报告 v2.0。并发:与报告 v2.0 共享 `reports/`,**本任务只写 `reports/figures/**` 与 `scripts/figures/**`**,不碰报告正文。

## Execution Surface

仓库根或独立 worktree;允许写 `reports/figures/**`、`scripts/figures/**`、`artifacts/figures_data/**`。禁区:`reports/scientific_report_v*.md`、所有产品代码、CI/oracle。

## Constraints

- 图注不得出现"我们预见到 β=3 有效"这类事后合理化。
- 确定性方法的 30 次重复必须在图注标明非独立样本。
- 不得删除 GB1 面板或改动其已验收的 regime 分离。
- 新增度量快照必须源钉(记录来源文件与哈希),沿用现有机制。

## Checkpoint

出第一张新 AAV 面板即停并报(贴图 + 图注全文),CEO 目视验收后再出其余。**异议型停**:若发现两指标分裂在一张图里画不清楚,带替代版式来谈,不要硬塞。

## CI/Gate Authority Stop Condition

非 CI/gate 任务(docs-task 无 CI 门)。不碰 CI/门禁/oracle。

## Implementation Plan

- 从 `v07-multiseed-robustness.md` 抽数并落成新的源钉快照。
- 改 `generate_all.py` 的 AAV 分支;同步扩展 `verify_figures.py` 的断言(新快照哈希、DPI、矢量、图链)。
- 逐张目视检查(交叉标签、遮挡图例),这是上一轮实际踩过的坑。
- `ha fact record --task task_f9a282c594dbb92bf1b9e0a18b` 记交付。

## Deliverable Contract

更新后的 AAV 面板(300DPI PNG + SVG)+ 新源钉快照 + `verify_figures.py` 通过记录;≥1 fact;回报改了哪几张、图注怎么写的。

## Evidence Protocol

每个图上的数字给出处;区分实测与示意(如 Figure 3 是解析示意,须继续标明)。

## Verification

停手点 = 图落盘 + verify 脚本通过 + ≥1 fact。CEO 目视验收不可下放。
