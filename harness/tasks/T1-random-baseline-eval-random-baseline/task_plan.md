# 随机策略基线：三轮虚拟进化 eval + 指标表（random baseline）

Task Contract: harness-task v1

## Brief

实现随机突变策略的虚拟定向进化基线：在 GB1 数据上跑三轮「随机提名 96 变体 → 查全量真值表 → 回流」闭环，产出每轮 top-10 真实 fitness 与指标表。这是四策略对比（题目 5.c）的第一条曲线。

## Goal

可验证结果：`evolution/random_baseline.py` 一条命令跑通，产出 `reports/random_baseline_metrics.json` 与 `reports/figures/random_baseline_curve.png`。交付物形态：Python 脚本 + 指标 JSON + 曲线图。落点：本仓库。接收者：泽宇与后续 M3 闭环仿真（该脚本将被 campaign.py 复用为策略①实现）。第一个使用方：M1 milestone 的验收（Spearman/Top-k 指标表）与周日报告的基线章节。

## Context

- 数据已落 `data/four_mutations_full_data.csv`（149,361 变体全量，Wu 2016，列含 Variants/HD/Fitness/sequence）；FLIP 切分在 `data/splits/`。
- GB1 野生型 4 位点 V39/D40/G41/V54（Variants 字段 4 个字母，位置 1-4 对应）；fitness>0.01 的占 23.1%。
- WT=VDGV Fitness=1.0；全表即完美 oracle（组合完备）。
- 环境：.venv（torch 2.14 + mps + fair-esm + pandas + scikit-learn）已就绪。
- 已知事实：77% 变体 fitness≈0，随机策略很弱——这正是基线的意义（衬托策略②③④）。

## Required Reading

1. `README.md`（仓库结构）— 权威：工程入口
2. `data/README.md`（FLIP 原始说明）— 权威：数据语义
3. 知识库作战文档（ZeYu-AI-Brain 06-PERSONAL-DOCS/12-JOB-SEARCH/01-COMPANIES/09-明度数智/02-准备/2026-09-10-AI4S笔试完整作战文档.html §4.4 四策略定义）— 权威：策略语义（本任务只做策略①）

## Entry Conditions

- `data/four_mutations_full_data.csv` 存在且 149,361 行（已满足，2026-09-10 验证）。
- `.venv` 可用（已满足）。

## Dependencies

- 无上游代码依赖。下游：M3 campaign.py 将 import 本模块的策略①函数；指标表格式需稳定（JSON schema 固定字段：round/top10_max/top10_mean/n_hit_nonzero）。

## Execution Surface

仓库根 `~/Projects/ai4s-directed-evolution-agent`，分支 master。允许写入：`evolution/`、`reports/`、`tests/`。不得改动：`data/`（只读）、`harness/`、`models/`。

## Constraints

- 数据文件只读，不得写入 data/。
- 随机种子固定（seed=42）保证可复现。
- 不得引入 heavy 依赖（本任务不需要 ESM/LLM）。
- 每轮预算 96 变体（96 孔板隐喻），共 3 轮；轮 0 冷启动池从全表按 HD 分层抽样 5,000 条（与作战文档一致）。
- 候选生成空间：4 位点 × 20 aa 的合法组合（Variants 字段形态），去重后随机抽。

## Checkpoint

- 若全量表读取/解析出现行数不符或 fitness 解析失败 → 停止上报，不自行清洗。
- 完成后必须回报：commit hash + 指标 JSON 全文 + 脚本运行命令。

## CI/Gate Authority Stop Condition

本任务不涉及 CI/gate/governance 修改。若发现需要改 Makefile 之外的门（如 harness walls），停止并上报。

## Implementation Plan

- 确认 `data/four_mutations_full_data.csv` 可读（149,361 行）。
- 实现 `evolution/random_baseline.py`：冷启动池构造（HD 分层 5k）→ 三轮循环（随机提名 96 → 查表真值 → 回流池）→ 指标输出（每轮 top-10 max/mean、非零命中率、累计曲线 PNG）。
- 用 `ha task progress append T1-random-baseline --text "..." --evidence type:PATH:summary` 记录关键进展。
- 指标 JSON 写 `reports/random_baseline_metrics.json`；图写 `reports/figures/random_baseline_curve.png`（matplotlib，中文字体缺失时用英文标签）。
- 跑通并自检：三轮 top10_max 数值合理（GB1 顶级变体 fitness 可 >1）、JSON 可解析。

## Deliverable Contract

交付：`evolution/random_baseline.py`（含 `if __name__ == "__main__"` 可直接跑）+ `reports/random_baseline_metrics.json` + `reports/figures/random_baseline_curve.png` + Makefile `make baseline` 已可用。回报字段：commit hash、运行命令、三轮 top10_max/top10_mean、非零命中率。接收者：泽宇（验收）→ M3（复用）。

## Evidence Protocol

证据粒度：脚本 stdout 打印每轮摘要；JSON 存全部三轮指标。阴性对照：随机策略 top10_mean 应显著低于全表 top-1% 均值（若反常说明查询逻辑有 bug）。reviewer 拒收条件：seed 不固定、改动了 data/、指标 JSON 字段缺失、图未生成。

## Verification

- `make baseline` 一条命令成功退出。
- `reports/random_baseline_metrics.json` 存在且含 rounds=3、每轮 top10_max/top10_mean/n_hit_nonzero。
- git status 干净（除 reports/ 新增产物）。
- 测试：`tests/test_random_baseline.py` 至少断言冷启动池=5,000、轮预算=96、结果可复现（同 seed 两次运行指标一致）。
