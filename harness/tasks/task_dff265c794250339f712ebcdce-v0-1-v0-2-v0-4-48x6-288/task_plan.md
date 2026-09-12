# 版本矩阵统一复跑:v0.1/v0.2/v0.4 在严格 48×6=288 协议下重跑 + 全版本产物汇总进主树

Task Contract: harness-task v1

## Brief

报告要把 7 个版本写完整、数据也写完整,但现在有两个硬障碍:

**障碍一:版本间不可比(fact `F-186DC664`)。** CEO 逐轮复算发现 v0.1/v0.2/v0.4 的 LLM 主跑**都没有严格执行"每轮固定预算"**,而 v0.4-deterministic/v0.5/v0.6 是严格的 48×6=288。实测逐轮提名数:

| 版本 | 声称 b/r | 实际逐轮提名 | 轮数 | 实花 |
|---|---|---|---|---|
| v0.1 | 96 | 80 / 16 / 75 / 21 / 95 / 1 | 6 | 288 |
| v0.2 | 48 | 48 / 47 / 47 / 46 / 48 / 48 | 6 | **284** |
| v0.4 LLM | 48 | 48 / 47 / 48 / 48 / 46 / 42 / 9 | **7** | 288 |
| v0.4 det | 48 | 48 / 48 / 48 / 48 / 48 / 48 | 6 | 288 |
| v0.5 | 48 | 48 / 48 / 48 / 48 / 48 / 48 | 6 | 288 |
| v0.6 full/semi | 48 | 48 / 48 / 48 / 48 / 48 / 48 | 6 | 288 |

v0.1 的 `budget_per_round=96` 与行为完全不符(第 6 轮只提 1 个);v0.4 的核心对比"LLM 7.829 vs deterministic 8.4162"两侧**轮数不同(7 vs 6)、模型重训次数不同**,不是单因子对照。

**障碍二:没有一处能看到全部版本。** v0.5 只在 `.worktrees/t-v05`,v0.6 只在 `.worktrees/t-v06`,v0.7 只在 `.worktrees/t-v07`,主树 `harness/reports/` 只有 v0.1–v0.4。三个 worktree 没有任何一个同时拥有 v0.5+v0.6+v0.7。

## Goal

1. **统一协议复跑**:把 v0.1、v0.2、v0.4-LLM 三条在**严格 48×6=288**、同池、同 cold-start、同 seed 集合下重跑,产出可与 v0.4-det/v0.5/v0.6/v0.7 直接并排的数据点。
2. **补齐产物 schema**:新产物必须存**每轮全部提名序列及其 HD**(不只是 Top-10 与聚合),并把模型字段写成**实际解析值**。历史 metrics 的共性缺陷就是没存这些,导致任何按突变阶数的事后分组分析都无法从轨迹恢复(包B 已实证撞到)。
3. **全版本汇总进主树**:把 v0.5/v0.6/v0.7 的 report 与产物从各自 worktree 收进主树 `harness/reports/`,使一处可见全部 7 个版本。
4. **产出版本矩阵总表** `harness/reports/version-matrix/report.md`:每个版本一行,列出协议(轮数/每轮/总预算/实花)、surrogate、采集策略、是否用 LLM、cum_top10_max、strong、是否达峰,并**明确标注哪些数是原始记录、哪些是本次统一复跑**。

首个消费者:最终报告的"虚拟定向进化实验结果"章——那一章的版本演进曲线现在是拿不同协议的点连起来的,必须修。

## Context

- **承重事实**:`F-186DC664`(版本可比性缺陷,含上表全部实测数字)、`F-885537A3`(最终定性:两目标两策略)、`F-E9C38438`(峰隐形是关键二阶缺测+表达力双因素)。
- 口径基线(**不得改动**):AAV 池 27832 / cold-start 10433(HD≤2)/ 门内 9533(HD≤4 且 mean BLOSUM62≥0)/ 池内 max 8.4162 / cold-start incumbent 9.536457 / strong 阈值 2.6159。
- 各版本的语义差异(复跑时要保持,**只统一预算协议,不统一方法**):
  - v0.1 = 无门禁的自主 agent(裸跑,探索发散)
  - v0.2 = 加 Knowledge 门禁(HD≤4 + BLOSUM62 硬过滤)
  - v0.3 = **诊断版本,不是 campaign**(ESM-2 zero-shot 扫描 + surrogate scan),没有 `agentic.metrics.json`,复跑与它无关,但总表里要占一行并说明它是诊断
  - v0.4 = 上位感知 surrogate(EpistasisRidge)+ 那条被误标的 "deterministic" 基线(实为 `predicted_mean`/`diverse` **交替**,见 `F-6D7255DE`)
  - v0.5 = C+A 成功 / B(CV 质量自适应采集)失败,rank-45 截断
  - v0.6 = LLM 元层 backtrack/redirect(full vs semi),redirect 无效
  - v0.7 = backtrack-to-EXPLORE + 30seed×7方法矩阵
- **数据卫生**:产物里历史标注的 `gpt-5.6-sol` 是错的,实际解析模型是 `claude-sonnet-5`(包C 已实跑确认)。新产物写实际值。

## Required Reading

按序(权威性递减):
1. 本 plan 的 Brief 表 + fact `F-186DC664`(**最高权威**:要修什么)。
2. `agent/auto_researcher.py`(**待跑主体**:各版本的采集与预算执行路径)。
3. `.worktrees/t-v05|t-v06|t-v07/harness/reports/agentic-v0.5|0.6|0.7/report.md`(**权威**:待汇总的三个版本的原始结论,汇总时不得改写)。
4. `harness/context/research/v07-multiseed-robustness.md`(**权威**:v0.7 的 30seed×7方法口径,总表里 v0.7 一行以它为准)。
5. `harness/context/research/v06-backtrack-analysis.md`(**权威**:v0.4 "deterministic" 实为交替的证据)。
6. `harness/reports/agentic-v0.1|v0.2|v0.4/report.md`(原始叙事,**只读**,不得覆盖)。

## Entry Conditions

- 独立 worktree(`t-version-matrix`);`.venv` 与 `data/aav/full_data.csv` symlink 就位。
- 先复现一个已知严格点作为锚:跑 v0.4-deterministic 应得 `cum_top10_max=8.4162`、逐轮提名全 48。**复现不出来就停下报**,不要在没对齐的基线上做复跑矩阵。
- 汇总前先确认三个 worktree 的 v0.5/v0.6/v0.7 产物完整(report.md + metrics + events.jsonl)。

## Dependencies

- 上游:fact `F-186DC664`;包B 关于"历史 metrics 未存逐轮全部提名"的实证。
- 下游:最终报告 v2.0(`task_db4ace109f72a92847c7349fe1`)的实验结果章;图表重绘(`task_f9a282c594dbb92bf1b9e0a18b`)。
- **并发(硬约束)**:同期在飞——包A(`task_0bc2d4d678eea24c4930b60a0e`,动 `evolution/campaign.py`/`agent/pipeline.py`/`agent/llm.py`/`app/demo.py`)、包C(`task_6d1dc285d32628ed317b9bb4da`,**正在改 `harness/reports/**` 里 v0.1–v0.4 的模型标签与勘误段**)、知识增强实验(`task_25092f640504bf3b040f6adfb5`,动 `knowledge/**` 与 `agent/auto_researcher.py`)。

## Execution Surface

- 分支 `t-version-matrix`;dispatcher 注入 cwd。
- **允许写**:`harness/reports/version-matrix/**`(本任务的新产物与总表)、`harness/reports/agentic-v0.5/**`、`harness/reports/agentic-v0.6/**`、`harness/reports/agentic-v0.7/**`(从 worktree 汇总进主树的**新目录**)、本 worktree 内的复跑脚本。
- **禁区(极重要)**:
  - `harness/reports/agentic-v0.1/**`、`v0.2/**`、`v0.3/**`、`v0.4/**` —— **包C 正在改这些文件**。复跑结果一律写进 `version-matrix/`,**不要覆盖或修改任何历史版本目录**。保留原始记录本身就是诚实性证据。
  - `agent/auto_researcher.py`、`knowledge/**` —— 知识增强实验的文件面。复跑需要不同协议时,用**参数/配置**实现,不要改这个文件;若非改不可,停下来报。
  - `evolution/campaign.py`、`agent/pipeline.py`、`agent/llm.py`、`app/demo.py` —— 包A 的文件面。
  - `evolution/datasets.py` 的池口径、CI/oracle。
- 禁区之外自行判断,事后汇报动了哪些我没预见的面。

## Constraints

- **只统一预算协议,不统一方法**。每个版本的 surrogate、门禁、采集策略保持它当时的样子——我们要回答的是"在同一预算协议下这些方法各自多强",不是"把所有版本改成同一个方法"。
- **不得覆盖历史产物**。原始 v0.1/v0.2/v0.4 记录连同它们的不一致一起保留;总表里用两列区分"原始记录"与"统一复跑"。
- **预注册**:seed 集合、轮数、每轮预算、shortlist 大小在开跑前写进 report 的预注册一节,跑完不得回头改。
- **answer-agnostic**:复跑过程不得使用测试峰身份做早停或选参。
- 多 seed:每条至少 3 个 seed;若某条 seed 间方差很大,加跑到 10 并说明。
- 新产物模型字段写 `claude-sonnet-5`(实际解析值),不抄 `gpt-5.6-sol`。
- 预算控制:这是复跑矩阵,注意 LLM 调用成本;先跑 1 个 seed 验证协议再铺开。

## Checkpoint

- **第一次停**:锚点复现(v0.4-deterministic 得 8.4162 且逐轮全 48)+ v0.1 单 seed 统一协议复跑完成,报两个数:v0.1 在严格 48×6 下的 `cum_top10_max` 与 `strong`,以及它与原始记录(5.961 / strong 15)差多少。这一条决定整个矩阵值不值得铺开。
- **第二次停**:汇总完成后报一句,主树 `harness/reports/` 下是否已能看到全部 7 个版本。
- **异议型停**:若发现某个版本在统一协议下**跑不出来**(例如 v0.1 的裸跑本质上就无法约束每轮提名数),**停下来报**——那本身是重要发现("早期版本的 agent 连预算都控制不住"),不要强行改造它的行为来凑协议。

## CI/Gate Authority Stop Condition

非 CI/gate 任务。已知本仓 standard-task 的 ci 完成门结构性不可满足(fact `F-8ED77039`,上游 harness-anything 修复在飞);`ha task submit`/`complete` 必返回 `service_rejected`。不得新建 workflow、不得改 CI 配置、不得 `transition --force`;失败即 `ha task progress append` 记录后停手。

## Implementation Plan

- 锚点复现 v0.4-deterministic → 停报。
- v0.1 单 seed 统一协议复跑 → 停报。
- 通过后铺开:v0.1/v0.2/v0.4-LLM 各 ≥3 seed。
- 新 schema:每轮记录全部提名序列 + HD + 预测均值/方差 + 是否被门禁拒 + 实测 fitness;模型字段写实际值。
- 汇总 v0.5/v0.6/v0.7 产物进主树(原样拷贝,不改写结论)。
- 写 `harness/reports/version-matrix/report.md` 总表。
- `ha task progress append` 留痕;`ha fact record --task task_dff265c794250339f712ebcdce` 记承重结论。

## Deliverable Contract

- `harness/reports/version-matrix/report.md`:预注册参数、版本矩阵总表(原始记录 vs 统一复跑两列)、每条的 seed 方差、诚实判定(统一协议后版本排序有没有变)。
- `harness/reports/version-matrix/` 下的指标 JSON 与事件链(新 schema,含逐轮全部提名及 HD)。
- 主树 `harness/reports/agentic-v0.5|v0.6|v0.7/` 齐全。
- ≥1 条 fact;本地 commit,不 push、不开 PR。
- 回报:统一协议后哪些版本的数变了、变了多少、版本排序有没有翻转。

## Evidence Protocol

- 每个数标明"原始记录"还是"本次复跑";两者不得混在同一列。
- 逐轮提名数必须逐版本列出,证明协议这次被严格执行。
- 阴性对照(shuffle-label held-out Spearman)每条复跑都要跑。
- 区分 live LLM 调用与 fallback,给实际次数。

## Verification

- 停手点 = 矩阵总表 + 新 schema 产物 + 主树汇总齐全 + ≥1 fact + 本地 commit。
- CEO 语义验收(协议是否真统一、历史记录是否完整保留、排序翻转是否如实报告)不可下放。
