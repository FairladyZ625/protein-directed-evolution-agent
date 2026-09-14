# 知识增强对照实验(AAV 主线):有/无知识库四策略对照 + 知识图谱接进决策链路

Task Contract: harness-task v1

## Brief

试题里有两条关于知识增强的**硬要求**,我们在 AAV 主线上没有兑现:

1. 「**比较有无知识增强时,Agent 推荐序列的差异**」——`no_knowledge` 开关只在 GB1 的四策略 campaign 用过(`agent_no_knowledge` vs `knowledge_agent`),AAV 主线 v0.1–v0.7 全程开着知识门禁跑,没有关掉它做对照。
2. 「结果分析与展示:**比较四种方法**——随机突变 / 适应度模型直接推荐 / LLM Agent 推荐 / **知识增强 LLM Agent 推荐**」——AAV 主线只有前三类的变体,第四类没有独立成线。

另有一条加分项也只做了一半:「使用知识图谱表示"位点—突变—性质—fitness"的关系」——`knowledge/validators.py` 里的 `build_knowledge_graph`(networkx MultiDiGraph)**只被 `tests/test_knowledge.py` 调用,没有接进 `agent/auto_researcher.py` 的决策链路**,等于存在但没用上。

## Goal

产出 `lab/reports/knowledge-ablation/report.md`(+ 指标 JSON + 事件链),交付三样:

1. **AAV 主线上的有/无知识增强对照**:同池、同预算 288、同 surrogate、同 seed 集合,唯一变量是知识库开/关。给出推荐序列差异(重合度、被拒候选的去向、HD 分布、BLOSUM 分布)与结果差异(strong 产量、cum_top10_max、达峰率)。
2. **四策略同图对照**:随机 / 模型直接贪心 / LLM Agent(无知识) / 知识增强 LLM Agent,各 ≥3 seed,一张对照表 + 一张曲线。
3. **知识图谱接线**:把 `build_knowledge_graph` 接进 Agent 的决策链路(至少让 Critic 或 Hypothesis 环节能查询"位点—突变—性质—fitness"关系并在 rationale 里引用图谱结论),并给出**接线前后推荐理由的差异样例**。若实验证明图谱对结果无改善,如实写——题目要的是"引入并比较",不是"必须变好"。

首个消费者:最终报告 v2.0 的"知识增强方法"章(试题要求的第 v 节)与"结果分析"章。

## Context

- **试题原文**:`lab/context/research/AI4S-assignment.md`,二、项目任务 → 「知识增强设计」与「结果分析与展示」两节;四、考核重点第 5 条「是否能合理引入氨基酸性质、突变规则或知识图谱」、第 6 条「是否能通过实验比较证明 Agent 的作用」;五、加分项第 5 条(知识图谱)。**这是硬要求,不是加分项**。
- **现有知识库**:`knowledge/rules.yaml`(20 种氨基酸理化属性 + 部分 BLOSUM62)、`knowledge/validators.py`(`validate_mutations` 实现 R-BLOSUM-CONSERVATIVE score≥1 与 R-BLOSUM-AGGRESSIVE score>−1;`validate_candidate(..., no_knowledge=)` 带开关;`build_knowledge_graph` 返回 networkx MultiDiGraph)。
- **现有接线**:`agent/auto_researcher.py` 只用到 `validate_candidate` 与内部 `_gate`(HD≤4 且 mean BLOSUM62≥0 → 门内 9533 候选)+ `check_knowledge` 工具。**图谱完全没接**。
- **已知的知识库债**(会影响本实验的解释,做之前先看):`lab/context/research/kb-iteration-research.md`(fact `F-159073F2`)指出 BLOSUM62 表只是部分条目、KB 含 GB1 遗留硬编码;独立评审另查出 `R-PRIORITIZE-HISTORICAL` 只声明未实现、某些突变(如 `C39M`)完全绕过 BLOSUM 判定。**这些债会让"关掉知识库"的对照失真**——若 BLOSUM 表有洞,开与关的差异会被低估。
- 口径基线:池 27832 / cold-start 10433 / 门内 9533 / 预算 288 / 池内 max 8.4162 / cold-start incumbent 9.536457。
- 最终定性 fact `F-885537A3`(两目标两策略),本实验的结果解释须放在这个框架下:知识增强影响的是**候选过滤**,采集策略影响的是**排序**,两者是正交的,报告里别混为一谈。

## Required Reading

按序(权威性递减):
1. `lab/context/research/AI4S-assignment.md`(**最高权威**:要求本身)。
2. `knowledge/validators.py` + `knowledge/rules.yaml`(**待改主体**)。
3. `agent/auto_researcher.py` 的 `_gate` / `check_knowledge` / `validate_candidate` 调用处(**接线点**)。
4. `lab/context/research/kb-iteration-research.md`(**权威**:知识库现状与已知债)。
5. `app/demo.py` 的 `agent_no_knowledge` / `knowledge_agent` 两策略(**已有范本**:GB1 上怎么做的对照,照它的口径迁到 AAV)。
6. `lab/context/research/v07-multiseed-robustness.md`(对照基线的 seed 与指标口径)。

## Entry Conditions

- 独立 worktree(建议 `t-knowledge-ablation`);`.venv` 与 `data/aav/full_data.csv` 需 symlink(两者 gitignored,不 symlink 跑不起来)。
- 能复现 v0.7 的 greedy 与 UCB β=3 基线数值作为对照锚点。复现不了就停下报,不要在没对齐的基线上做消融。
- **前置依赖**:知识库 GB1 遗留清理(`task_ff24b0e33edb3412f4dd070e4b`)最好先做完;若未做,在脏代码上跑要在报告里显式声明这个污染源。

## Dependencies

- 上游:KB 研究结论(`F-159073F2`)、独立评审查出的 KB 缺陷、v0.7 基线口径。
- 下游:最终报告 v2.0 的知识增强章与结果分析章;试题覆盖度审计(`task_d5e9455a1235d1554b1967c708`)会把本任务列为关键缺口的补齐动作。
- 并发:与 v0.8-A/B/C 同改 `agent/auto_researcher.py` 文件面,**不得并行**;各自独立 worktree 且合并前互不引用。

## Execution Surface

- 分支 `t-knowledge-ablation`;dispatcher 注入 cwd。
- **允许写**:`knowledge/**`(图谱接线与查询接口)、`agent/auto_researcher.py`(知识库开关与图谱调用路径)、`lab/reports/knowledge-ablation/**`、对应测试。
- 禁区:`evolution/datasets.py` 的池口径、`models/train_ladder.py` 的 surrogate 定义、v0.7 及更早的任何 report、CI/oracle。

## Constraints

- **对照唯一变量**:有/无知识增强两组必须同池、同 cold-start、同预算、同 surrogate、同 seed;除知识库开关外任何差异都要在报告里声明。
- **answer-agnostic 硬红线**:知识库与图谱的任何内容都不得编码测试峰身份、不得读取候选的 fitness 标签来构图(图谱只能用**已测**变体的 fitness,这正是题目"Mutation — improves — Fitness"的合法来源)。
- **允许且预期结果可能是负的**:知识门禁很可能降低达峰率(它会过滤掉非保守替换,而真峰 D0Q/S17E/V18A 里就有非保守项)。**这正是有价值的发现,如实写**,不得为了让知识库显得有用而调阈值。
- 不得改门禁口径本身(9533 是全线可比性基础);要比较不同阈值请另开消融维度并单独标注。

## Checkpoint

- 跑通"有/无知识增强"各 1 个 seed 即停并报:两组推荐序列的重合度、被知识库拒掉的候选里有没有高 fitness 的、首个 seed 的 strong 与 cum_top10_max。这个中间结果直接决定后面要不要扩 seed。
- 图谱接线完成后单独停一次,报:图谱在哪个环节被查询、rationale 里引用图谱的样例长什么样。
- **异议型停**:若发现"关掉知识库"在当前实现下无法干净做到(例如 `_gate` 的 HD 截断与 BLOSUM 过滤耦合在一起,关不掉其中一个),停下来报设计问题并提改法,不要用近似糊过去。

## CI/Gate Authority Stop Condition

非 CI/gate 任务。**已知本仓 standard-task 的 ci 完成门结构性不可满足(fact `F-8ED77039`)**,`ha task submit`/`complete` 会返回 `service_rejected`。不得新建 workflow、不得改 CI 配置、不得 `transition --force`;submit 失败即记录进度并停,交 CEO。

## Implementation Plan

- 先把 `no_knowledge` 开关贯通到 AAV 主线的 agentic 入口(GB1 侧已有范本,照搬口径)。
- 跑有/无知识增强对照,记录每轮被拒候选清单(含它们的真实 fitness,仅用于事后分析,不回灌决策)。
- 补齐四策略同图对照:随机 / 模型直接贪心 / LLM Agent(无知识) / 知识增强 LLM Agent,各 ≥3 seed。
- 图谱接线:给 `build_knowledge_graph` 加查询接口(按位点查已测突变及其 fitness、按性质查氨基酸),接进 Critic/Hypothesis 环节,rationale 里引用图谱节点/边。
- 出报告:三组结果 + 推荐序列差异分析 + 诚实判定。
- `ha task progress append` 留痕;`ha fact record --task task_25092f640504bf3b040f6adfb5` 记承重结论。

## Deliverable Contract

- `lab/reports/knowledge-ablation/report.md`:实验设计(唯一变量声明)、有/无知识增强对照表、四策略对照表+曲线、图谱接线说明与 rationale 样例、诚实判定(知识库到底帮了还是害了、图谱有没有改变决策)。
- 指标 JSON + 事件链 JSONL(可重放)。
- 至少一张可直接进最终报告的图。
- ≥1 条 fact。
- 回报:知识库开/关的三个关键数差多少、图谱接在哪、结论是正是负。

## Evidence Protocol

- 每个数字标明实测还是估算;阴性对照(shuffle-label held-out Spearman)必须跑。
- 被知识库拒掉的候选要给清单与其真实 fitness——这是"失败案例分析"的一手素材(试题四、考核重点第 7 条明确要求分析失败原因)。
- 图谱接线要贴出调用点 grep 证据,证明它真的在决策链路上,而不是又一个没有调用者的模块。

## Verification

- 停手点 = report + 三组结果 + 图谱接线证据 + ≥1 fact + 定向测试绿。
- CEO 语义验收(对照是否只变了一个变量、负结果是否诚实、图谱是否真接上)不可下放。
