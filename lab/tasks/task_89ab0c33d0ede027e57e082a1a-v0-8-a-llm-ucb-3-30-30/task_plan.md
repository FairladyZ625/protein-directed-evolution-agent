# 实验 v0.8-A:显式给 LLM 重不确定性探索策略,测它能否追平 UCB β=3 的 30/30 达峰

Task Contract: harness-task v1

## Brief

v0.7 钉死了一个负结果:LLM 自主决策两个目标都没匹配上最优(FULL 达峰 0/3、bulk 也不如 greedy;SEMI 1/3 靠运气)。但这个负结果有歧义——**它是"LLM 没选对策略"(prompt 可救),还是"LLM 选对了也执行不出来"(能力不行)?** 本实验用一个受控对照把这两种解释分开。

## Goal

产出 `lab/reports/agentic-v0.8a/report.md` + 指标 JSON + 事件链,回答一个二选一的问题:当 SYSTEM_PROMPT **明确指示** LLM 采用重不确定性探索(等价于 UCB β=3 的决策规则:优先 mean+3·sqrt(var) 最高的候选)时,它的达峰率是

- **接近 30/30** → 结论收缩为"LLM 的失败是策略选择失败,不是执行失败;把策略写进 prompt 即可修复";
- **仍显著低于 30/30** → 结论加强为"即使给了正确策略,LLM 的执行层(工具调用、批次组装、轮次记忆)本身就是损耗源"。

两种结果都是可发表的,**不允许为了好看而调参重跑**。首个消费者:最终报告 v2.0 的"LLM 自主性是负担"一节。

## Context

- 最终定性以 fact `F-885537A3` 为准:两个目标两套相反策略。纯利用/greedy 赢"大量强变体"(strong=166);重不确定性探索 UCB β=3 赢"单个全局峰"(确定性 30/30 达峰 8.4162);LLM 自主两个都没匹配上。
- UCB β=3 的基线实现与 30 seed 矩阵见 `lab/context/research/v07-multiseed-robustness.md`;LLM-agentic 的 FULL/SEMI 变体见 `lab/reports/agentic-v0.7/report.md`。
- 关键机制(`lab/context/research/v06-backtrack-analysis.md`):真峰对纯均值排序隐形(门内均值排名 #426),只有在迭代累积了方差信息之后才会进入 UCB 头部(第 3 轮状态下 UCB 排名 #15)。所以本实验必须让 LLM 跑满同样的轮数,不能只测单轮。
- **数据卫生前置**:`agent/llm.py` 实际解析到的网关模型是 `claude-sonnet-5`,不是历史 metrics 里标注的 `gpt-5.6-sol`。本实验的 manifest 必须写实际值(另见 `task_c63438626decf11d080c1d9507`)。

## Required Reading

按序(权威性递减):
1. `lab/context/research/v07-multiseed-robustness.md`(**权威**:UCB β=3 的确切实现与 30 seed 结果口径)。
2. `agent/auto_researcher.py`(**待改主体**:SYSTEM_PROMPT、`explore_batch`、`compose_batch`、停滞检测)。
3. `lab/reports/agentic-v0.7/report.md` + `implementation-correction.md`(**权威**:FULL/SEMI 契约与已修过的 bug,别重蹈)。
4. `lab/context/research/v06-backtrack-analysis.md`(峰的路径依赖机制)。
5. `models/train_ladder.py`(surrogate 的 var 从哪来,β 怎么算)。

## Entry Conditions

- 独立 worktree(建议 `t-v08a`),从 v0.7 HEAD 分叉;`.venv` 与 `data/aav/full_data.csv` 需 symlink(两者均 gitignored,不 symlink 跑不起来)。
- UCB β=3 基线可复跑并复现 30/30。复现不了就停下报告,不要在未对齐的基线上做对照。

## Dependencies

- 上游:v0.7 的 UCB β=3 实现与 seed 口径。
- 下游:最终报告 v2.0(`task_db4ace109f72a92847c7349fe1`)。
- 并发:与 v0.8-B/v0.8-C 文件面可能重叠(都改 `agent/auto_researcher.py`),**三者不得并行**,或必须各自独立 worktree 且不合并前互不引用。

## Execution Surface

- 分支 `t-v08a`;dispatcher 注入 cwd。
- 允许写:`agent/auto_researcher.py`(仅 SYSTEM_PROMPT 与新增的策略指示路径)、`lab/reports/agentic-v0.8a/**`、对应测试。
- 禁区:`evolution/datasets.py` 的池口径、`models/train_ladder.py` 的 surrogate 定义、v0.7 及更早的任何 report、oracle/CI。

## Constraints

- **answer-agnostic 硬红线**:prompt 里只能写策略(用不确定性探索、β 取多大),**绝不能写任何关于真峰身份、位置、突变组合的信息**。写了就整个实验作废。
- **预注册**:β=3、shortlist 大小、轮数、seed 集合在开跑前写进 report 的"预注册参数"一节,跑完不得回头改。
- 对照组必须同预算(288)、同池、同 cold-start、同 surrogate。
- 不得用真峰结果做早停或选参。

## Checkpoint

- 跑完 1 个 seed 即停并报:LLM 在明确策略指示下第几轮命中/未命中、它实际提名的批次与 UCB β=3 的批次重合度多少。重合度这个量是本实验的核心诊断——它直接区分"没选对"与"选了执行不出来"。
- **异议型停**:若发现"明确指示"这件事本身无法干净实现(例如 LLM 拿不到 var、或工具接口不暴露 UCB 排序),停下来报设计问题,不要用近似糊过去。

## CI/Gate Authority Stop Condition

非 CI/gate 任务。**已知:本仓 standard-task 的 ci 完成门结构性不可满足(fact `F-8ED77039`)**,`ha task submit`/`complete` 会返回 `service_rejected`。不得新建 workflow、不得改 CI 配置、不得 `transition --force`;submit 失败即记录进度并停,交 CEO。

## Implementation Plan

- 在 SYSTEM_PROMPT 中加一个可开关的"策略指示"段,明确写出重不确定性探索规则;保留原自主版作为对照。
- 记录每轮 LLM 实际提名批次,与同一状态下 UCB β=3 会选的批次做逐候选比对,输出重合度序列。
- 至少跑 3 个 seed;若首 seed 结果与 UCB 重合度极高但仍不达峰,加跑到 10 seed 以分辨随机性。
- 每轮用 `ha task progress append` 留痕;承重结论用 `ha fact record --task <本任务id>` 记。

## Deliverable Contract

- `lab/reports/agentic-v0.8a/report.md`:预注册参数、逐 seed 达峰表、**每轮与 UCB β=3 的批次重合度**、结论二选一的明确判定。
- 指标 JSON + 事件链 JSONL(可重放)。
- ≥1 条 fact。
- 回报:达峰几/几、重合度区间、结论落在哪一支。

## Evidence Protocol

- 每个数字标明实测还是估算;阴性对照(shuffle-label held-out Spearman)必须跑。
- LLM 模型归属写实际解析值,不抄历史标签。
- 与 v0.7 对照的每个数,引用其在 `v07-multiseed-robustness.md` 中的原位置。

## Verification

- 停手点 = report + 指标 + 事件链落盘 + ≥1 fact + 定向测试绿。
- 结论是否成立由 CEO 做语义验收,不可下放;若结果是"LLM 给了策略也追不上",如实写,不得重跑到好看为止。
