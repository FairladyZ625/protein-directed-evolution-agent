# T2 数据管线 + 特征提取（GB1 → 三池 → one-hot/ESM-2 特征）

Task Contract: harness-task v1

## Brief

把本地 GB1 全表加工成可训练的三池数据 + 两套特征（one-hot 与 ESM-2 650M 实时嵌入），作为 T3 预测模型与 T7 闭环的统一数据底座。

## Goal

产出可复现的数据管线与特征缓存：`evolution/mutations.py`（突变解析/序列重建/合法性校验）、`data/download_gb1.py`（本地落地校验，非真下载则记录来源与 SHA）、`features/`（one-hot 编码器 + ESM-2 实时提取器，带磁盘缓存）。交付给 T3/T7 复用，缓存文件进仓库以保证评委 CPU 可复现。第一个使用方：T3 训练脚本。

## Context

- task：搭数据+特征层。fact：GB1 全表已在本地 `data/four_mutations_full_data.csv`（149,361 行，WT=VDGV=1.0，max=8.762），被 `.gitignore` 排除。decision：提名/评估空间统一限定 149,361 个有真值变体（缺失 10,639 记为已知局限）。
- 三池：train_pool（第0轮 5k，HD 分层，WT 必入）/ query_pool（虚拟湿实验真值库）/ holdout（不可见）。切分带固定 seed 可复现。

## Required Reading

1. `lab/context/research/AI4S-domain-research.md`（GB1/FLIP、ESM-2 650M 选型）— 权威：领域事实。
2. `lab/context/architecture/AI4S-master-plan.html`（数据层设计、三池）— 权威：架构。
3. `evolution/random_baseline.py`（现有数据契约校验与 HD 分层抽样，复用其口径）— 权威：现状实现。

## Entry Conditions

- `data/four_mutations_full_data.csv` 存在且行数/表头校验通过；不成立则停止上报，不自造数据。

## Dependencies

- 上游：无（数据已落地）。下游接收：T3（特征+池）、T7（池+提名空间）。判定满足：三池文件与特征缓存生成且被 T3 冒烟加载成功。

## Execution Surface

独立 worktree + 任务分支，base=main。允许写入：`data/`、`evolution/mutations.py`、`features/`、`tests/`（本任务测试）。绝对 cwd 由派工注入，不手抄。

## Constraints

- 不改 `evolution/random_baseline.py` 的现有契约字段；不清洗/删改原始数据行。
- ESM-2 走本地实时提取（M3 Max/MPS 已确认可跑），但**必须落缓存**且提供 one-hot 兜底路径，评委机无 GPU 也能复现全流程。
- 外部下载/破坏性动作默认禁止。

## Checkpoint

命中即停上报：数据契约不符、提名空间口径与 decision 冲突、牵连面超出上列文件。计划回报点：三池+特征生成后、发 commit 前。

## CI/Gate Authority Stop Condition

本任务非 CI/gate/governance 任务；若需改门禁面才能过，停止并记 blocker，请求治理任务。

## Implementation Plan

- `mutations.py`：解析 `V39I` 式记法、由 WT 重建全长 56aa 序列、非法突变/终止子检查。
- `download_gb1.py`：校验本地 CSV（行数/唯一性/WT），记录来源与 SHA；缺失则给出清晰 hint。
- `features/`：one-hot（4×20=80 维）+ ESM-2 650M 实时提取（1280 维，MPS，带 `.npy`/parquet 缓存）。
- 三池切分函数（seed 固定，HD 分层，WT 必入），导出稳定接口供 T3/T7。
- 用 `ha task progress append` 记录关键进展；用 `ha fact record` 晋升「三池规模/特征维度/缓存命中」等承重观察。

## Deliverable Contract

代码 + 缓存 + 定向测试。完成回报字段：三池各自规模、one-hot/ESM 特征维度、缓存路径与大小、提名空间基数（=149,361）。

## Evidence Protocol

粒度到函数级。阴性对照：换 seed 三池成员应变化但规模不变；ESM 缓存命中与实时提取结果逐元素一致（容差）。reviewer 拒收条件：无缓存、无 one-hot 兜底、口径与 decision 不符。收口前至少记一条 fact 并把回执存入 Execution outputs。

## Verification

- 停止点 = 便宜确定性门全绿 + 本任务改动面定向测试全绿 + 本地 commit。
- 定向测试：`tests/test_data_pipeline.py`（数据契约、三池 HD 分层与规模、one-hot 维度、ESM 缓存一致性）；贴真实 runner 输出。
- 至少记录一条 fact（`code-doc-reconciliation` 以 `fact_missing` 拒绝无 fact 完成）。
