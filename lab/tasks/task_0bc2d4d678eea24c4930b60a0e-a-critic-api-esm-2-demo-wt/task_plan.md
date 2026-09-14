# 包A/主链真实性修复:Critic 真接线 + 商业 API 严格结构化输出 + ESM-2 回到主力 + demo 接受任意 WT

Task Contract: harness-task v1

## Brief

试题覆盖度审计(`lab/context/research/assignment-coverage-audit.md`)判定**打回**,根因集中在一句话:**我们声称的架构和实际跑的架构不一致**。三条自己立的裁定口径(D2/D4/D5)被打回,一个 P0 缺口(主跑 Critic 空转)直接影响试题明写的要求。本包一次性修掉"声称 vs 实际"的全部落差,因为它们纠缠在同一批文件里,拆开会互相踩。

## Goal

让下面四条从"声称"变成"可验证的事实",每条都要有**一条能跑出来的证据**,不接受只改文档:

1. **Critic 真执行**(P0,试题二·c-v 与 b-vi):`evolution/campaign.py:182-213` 调五角色管线时固定传 `no_knowledge=True` 且未注入 `llm_critic`,导致 Scientific Critic 在主跑中空转,知识只在管线之后叠加 UCB+BLOSUM acquisition。改为:知识组启用规则 Critic **并**注入 `llm_critic`;无知识组保留为明确消融对照。产出:事件流里能看到 Critic 真实否决过候选的记录。
2. **商业 API 严格结构化输出**(裁定 D4 被打回):`agent/llm.py:61-76` 已接 OpenAI-compatible 商业 API 且有 live 轮次记录,但 GB1 只让 Hypothesis 返回原始 JSON 数组后手工解析,未请求 provider 的结构化输出。改为用 provider schema / Pydantic 结构化输出,解析失败要有明确失败路径而不是静默降级。
3. **ESM-2 回到主力**(裁定 D2 被打回):`evolution/campaign.py:56-62` 与 `app/demo.py:104-112,532-536` 的实际 predictor 都是 80 维 one-hot,而我们锁定的口径是"ESM-2 650M 主力(L2)+ one-hot 作 L1"。改为主力 campaign 与 demo 读取**已提交的** ESM-2 缓存;one-hot 降为 L1/离线 fallback,并在产物里记录 feature provenance(这一跑到底用了哪一层)。
4. **demo 接受任意 WT**(加分项 B06):`app/demo.py:530-651` 只吃硬编码 GB1 四位点的 4 字符变体。加分项原文是「输入野生型序列后自动推荐突变方案」。**二选一,都可接受**:实现完整 WT 输入与任务配置;或把 demo 文案收窄为"GB1 四位点 demo"并在报告里不申领该加分。选哪条由你判断后报 CEO,不要两头含糊。

首个消费者:最终报告的"LLM Agent 设计"与"知识增强方法"两节——这两节现在只能写成"结构齐全但主跑未启用",修完才能正着写。

## Context

- **权威审计**:`lab/context/research/assignment-coverage-audit.md`,第 1 节 E5/E10 是本包的直接证据,第 7.1 节 P0/P1 表是本包的范围来源。相关条目:H14、H15、H45、H50(Critic 与理由)、D4(结构化输出)、D2(ESM-2)、B06(demo)。
- **审计的原话证据**:E10 双侧核对 `evolution/campaign.py:182-213` 与 `agent/pipeline.py:110-123`——"两个 Agent 策略调用五角色管线,但调用固定传 `no_knowledge=True`,且未注入 `llm_critic`;角色事件存在,不代表 Critic 实际执行知识否决或商业 LLM 审查"。
- **试题原文**:`lab/context/research/AI4S-assignment.md`,二·科学智能体 b-vi(给出推荐理由)、c-v(Scientific Critic 检查突变是否合理并解释结果);四·考核重点第 5 条;五·加分项第 6 条(交互 demo)。
- **已知数据卫生债**:`agent/llm.py` 实际解析到的网关模型是 `claude-sonnet-5`,而产物里标注 `gpt-5.6-sol`。**本包新产生的任何 metrics/manifest 必须写实际解析值**;历史产物的批量更正由包C(`task_6d1dc285d32628ed317b9bb4da`)负责,你不要动。
- **最终科学定性**以 fact `F-885537A3` 为准(两目标两策略)。本包**不改变任何科学结论**,只修"实现是否兑现了声称"。若修完发现数值变了,如实报告,不得为了对齐旧数字而回退实现。

## Required Reading

按序(权威性递减):
1. `lab/context/research/assignment-coverage-audit.md`(**最高权威**:本包的全部范围与证据,尤其 E5/E10 与 7.1 表)。
2. `lab/context/research/AI4S-assignment.md`(**标尺**:相关条目原文)。
3. `evolution/campaign.py`、`agent/pipeline.py`、`agent/llm.py`、`app/demo.py`(**待改主体**)。
4. `models/train_ladder.py` 与 `features/` 下的 ESM 缓存布局(第 3 项要用已提交缓存,先确认覆盖面)。
5. `tests/test_agent.py`、`tests/test_campaign.py`、`tests/test_demo_app.py`(现有断言边界,别改坏)。

## Entry Conditions

- 独立 worktree(`t-pkgA-mainline-truth`);`.venv` 与数据 symlink 就位。
- 先跑一次基线:`.venv/bin/pytest -q tests/test_agent.py tests/test_campaign.py tests/test_demo_app.py` 应全绿。不绿先报,不要在红的基线上改。
- 第 3 项开工前先确认**已提交的 ESM 缓存覆盖面**(审计 E7:已提交缓存覆盖 GB1 评测所需的 5000/2168/两个 2000 样本块,1280 维;149361 全表缓存只有 one-hot 80 维;另一个 38265×1280 文件当前未跟踪)。**若已提交缓存不足以支撑主力 campaign,停下来报,不要为了达成 D2 去跑未跟踪的大文件或把 44MB 级产物塞进 Git。**

## Dependencies

- 上游:覆盖度审计(`task_d5e9455a1235d1554b1967c708`)。
- 下游:最终报告 v2.0(`task_db4ace109f72a92847c7349fe1`)的 Agent 设计与知识增强两节。
- **并发(硬约束)**:同期在飞的有——包B(`task_51297081bf4eeb7e466da8a3e1`,动 `features/pools.py`/`models/evaluate_all.py`/`analysis/`)、包C(`task_6d1dc285d32628ed317b9bb4da`,动 `README.md`/`Makefile`/`lab/reports/**`)、知识增强对照实验(`task_25092f640504bf3b040f6adfb5`,动 `knowledge/**` 与 `agent/auto_researcher.py`)。**这些是禁区,不要碰。**

## Execution Surface

- 分支 `t-pkgA-mainline-truth`;dispatcher 注入 cwd。
- **允许写**:`evolution/campaign.py`、`agent/pipeline.py`、`agent/llm.py`、`app/demo.py`,以及它们对应的测试。
- **禁区(在飞 worker 的文件面)**:`knowledge/**`、`agent/auto_researcher.py`、`features/pools.py`、`models/evaluate_all.py`、`analysis/**`、`README.md`、`Makefile`、`lab/reports/**`、`reports/**`。
- 其余路径:禁区之外自行判断,事后汇报动了哪些我没预见的面。
- 绝对禁区:`evolution/datasets.py` 的池口径、CI/oracle。

## Constraints

- **不许只改文档**。每一条都要给出可跑的证据:Critic 否决记录、结构化输出的 provider 调用、feature provenance 字段、demo 的实际输入范围。
- **不许静默降级**:结构化输出解析失败必须显式失败或显式记为 fallback,不能悄悄退回手工解析后当成 live LLM。审计已经点名"不能把整条轨迹笼统写成 LLM"。
- **无知识组必须保留为干净消融**,不要顺手也给它接 Critic——那会毁掉对照。
- 新产物的模型字段写**实际解析值**,不抄 `gpt-5.6-sol`。
- 不得为了让数字好看而回退实现;数值变化如实报告。
- 外部 API 调用:允许(这正是 D4 要验证的),但要控制预算并记录实际调用次数与失败次数。

## Checkpoint

- **第 1 项做完即停并报**:贴出一条 Critic 真实否决候选的事件记录原文。这是本包最承重的一条,先确认它成立再做后面三项。
- 第 3 项(ESM-2)开工前若发现缓存覆盖不足,**停下来报**,不要自行扩大数据面。
- 第 4 项做完报你选了哪条路(实现通用 WT / 收窄文案)及理由。
- **异议型停**:若你判断某一条修完会让科学结论发生变化(例如 ESM-2 主力后 GB1 结果不同于历史报告),**停下来报,不要自己决定怎么叙述**——那是 CEO 的语义裁决。

## CI/Gate Authority Stop Condition

非 CI/gate 任务。**已知本仓 standard-task 的 ci 完成门结构性不可满足(fact `F-8ED77039`,上游修复在飞)**,`ha task submit`/`complete` 必返回 `service_rejected`。不得新建 workflow、不得改 CI 配置、不得 `transition --force`;submit 失败即 `ha task progress append` 记录后停手,交 CEO。

## Implementation Plan

- 基线测试跑绿 → 记录当前 GB1 四策略数值作为对照锚点。
- 第 1 项:改 campaign 的管线调用,知识组启用规则 Critic + 注入 `llm_critic`;补一条"Critic 否决了候选"的断言测试。
- 第 2 项:`agent/llm.py` 改用 provider 结构化输出 / Pydantic schema;补解析失败的负例测试。
- 第 3 项:campaign 与 demo 的 predictor 改读已提交 ESM 缓存;产物加 feature provenance 字段;补一条断言"主力跑用的是 1280 维而非 80 维"。
- 第 4 项:按你选的路改 demo;补对应测试或文案。
- 全程 `ha task progress append <本任务id>` 留痕;承重结论 `ha fact record --task task_0bc2d4d678eea24c4930b60a0e`。

## Deliverable Contract

- 四项改动 + 对应测试全绿(点名 `tests/test_agent.py`、`tests/test_campaign.py`、`tests/test_demo_app.py` 及你新增的;**不要跑全量矩阵**)。
- 一份 `lab/reports/pkgA-mainline-truth/report.md`:四项各自的"改前 vs 改后"证据,含 Critic 否决事件原文、结构化输出调用记录、feature provenance 字段样例、demo 输入范围说明;以及数值是否发生变化的如实说明。
- ≥1 条 fact。
- 本地 commit,**不 push、不开 PR**。
- 回报:四项各自成立与否 + 数值有没有变 + demo 选了哪条路。

## Evidence Protocol

- "Critic 真执行"要贴事件流原文,不接受"测试通过"作为唯一证据——测试可以断言角色事件存在而 Critic 仍空转,审计就是这么被骗过一次的。
- 区分 live LLM 调用与 fallback,给实际次数。
- 结构断言(如"不再传 `no_knowledge=True`")要 grep 两侧。
- 每个数标明实测还是沿用历史。

## Verification

- 停手点 = 四项落盘 + 点名测试绿 + report + ≥1 fact + 本地 commit。
- CEO 语义验收(声称与实际是否真的对齐、无知识组消融是否仍干净)不可下放。
