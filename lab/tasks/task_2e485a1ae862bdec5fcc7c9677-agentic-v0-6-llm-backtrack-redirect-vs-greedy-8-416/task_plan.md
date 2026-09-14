# agentic v0.6:LLM 元层自主 backtrack/redirect 逃离局部停滞(全自主 vs 半自主对照,追 greedy 8.416)

Task Contract: harness-task v1

## Brief

保留 v0.5 的 C(工具鲁棒)+ A(CV 透传),放弃 B(自适应配比,已证有害)。给 agent 一个**元层自主能力**:当它在事件流里检测到自己陷入停滞(cum_top10_max 连续多轮不涨/下降),可以判定"当前这摊是局部陷阱"并**退回、把预算重定向到一个突变构成不同的高预测区域**(basin-hop)。做**全自主 vs 半自主**两个变体对照,同 seed,看谁更接近确定性 greedy 的 8.416。全程 answer-agnostic。

## Goal

**可验证结果**:在同池 27832/同 cold-start 10433/同 288 预算(48×6)/同门禁(HD≤4,BLOSUM62≥0)/seed 42/同 EpistasisRidge surrogate 下,跑 v0.6 两个变体的 LLM agentic,报告各自 cum_top10_max,对照 v0.4 的 7.829、v0.5 的 6.5309、确定性 greedy 的 8.416;给出事件流证据说明 backtrack 是否/何时触发、redirect 是否帮助逃离停滞。

**诚实目标**:不是硬证 LLM 超 greedy(前沿说难),而是测试"**给 agent 元层自主(判停滞+换区)能否救回它在利用步的短板**"。赢了=LLM 元层判断有价值;平/输=更坐实"这地形上任何绕路都是税"。两种结果都如实写。

**交付形态与落点**:代码改 `agent/auto_researcher.py`(+必要的 `tests/`);两个变体结果落 `lab/reports/agentic-v0.6/`(自包含 Report:report.md 含 full/semi 对照 + v0.1→v0.6 表 + 机制 + manifest.json + aav/ metrics/events/figures)。首个消费者:CEO 验收 + 最终笔试报告。

## Context

- **v0.5 结论(权威,`lab/reports/agentic-v0.5/report.md`,fact F-F7BC7554)**:C+A 成功(0 工具错误、CV 0.90 每轮透传);**B 自适应配比失败**——cum_top10_max 6.5309 < v0.4 7.829 < greedy 8.416。机制(CEO 已独立复现):CV=0.90 时 round-1 exploit_ratio=0.87→只测 top-42,真峰路径关键变体(真值 7.391)在预测 #45 名被 6 个 explore 挤掉;仅 4.2% 探索税就把高质量 surrogate 带离纯 greedy 路径,后续追不回。
- **本任务的失败模式定位(CEO 判定,重要)**:在本地形上确定性 greedy 纯利用能直达 8.416,**说明 surrogate 没把 greedy 带进陷阱**;LLM 版的失败模式是**它自己过度探索/摊散预算**造成的自造停滞(v0.4 停 7.829、v0.5 停 6.53)。所以 backtrack 在这里的真实职责 = **"检测到我自己的策略连续 N 轮不涨→判定自造死局→把预算重定向到我一直没充分测的高预测区"**,而非"逃离 surrogate 造的陷阱"。
- **用户裁定(V0.6 方向)**:给 agent 更多自主性(元层),让它把停滞路径当局部陷阱、退回换路;C+A 保留,B 留档为失败尝试。
- **文献背书**:AdaLead(Sinai 2020,`lab/context/research/v05-agent-optimization-gemini.md` §1.2 引)核心即"带自适应局部重置的贪心";前沿共识(`lab/context/research/frontier-landscape-synthesis.md`)指 LLM 增益在元策略/编排层而非微观利用步——本任务正是在元层加自主。
- **前沿裂缝**:2502.00225(LLM 利用弱)针对微观选点;本任务测的是元层(判停滞+换区),是 LLM 可能有价值的那一档。

## Required Reading

按序,标权威级:
1. `lab/reports/agentic-v0.5/report.md`(**权威·基线**:C+A/B 现状、rank-45 机制、复现命令、下一步建议)。
2. `agent/auto_researcher.py`(**待改主体**:v0.5 已有 `compose_batch`/`surrogate_status`/`_gate_variants`/`safe_tool`/`test_composed_batch`/事件 emit;`state` 里已有 `current_round`;`run_autoresearch` 的 per-round 循环)。本 worktree 已含 v0.5 全部改动。
3. `lab/context/research/v05-agent-optimization-gemini.md` §1.2(**佐证**:AdaLead 自适应重置、EVOLVEpro 4 轮范式)。
4. `lab/context/research/frontier-landscape-synthesis.md`(**权威·定位**:元层自主 vs 微观利用步)。
5. `events/store.py`(事件链 append/verify 接口)、`lab/reports/agentic-v0.4/aav/agentic.events.jsonl`(事件字段口径参照)。

## Entry Conditions

- 本 worktree(t-v06)从 v0.5 HEAD 分叉,已含 C+A+B 全部代码;`.venv` 与 `data/aav/full_data.csv` 已 symlink(冒烟已验证 load('aav','one_hot')+EpistasisRidge OK)。
- 未满足即停并报。

## Dependencies

- 上游:v0.5 的 C+A(已在本 worktree)、v0.5 report/fact、frontier synthesis。
- 下游:CEO 语义验收 + 最终笔试报告。
- 并发:无其他 worker 改 `agent/auto_researcher.py`。

## Execution Surface

- 仓库:ai4s-directed-evolution-agent;分支 t-v06(base=v0.5 HEAD);dispatcher 注入绝对 cwd。
- **允许写范围**:`agent/auto_researcher.py`、`tests/`(新增/扩展)、`lab/reports/agentic-v0.6/`(新结果树)。
- 禁区:v0.1-v0.5 既有 report(只读对照,不覆盖);CI/门禁/oracle(protected surface);其他文件面。
- **运行时已预置(别重建)**:`.venv`(→主仓)、`data/aav/full_data.csv`(→主仓 oracle)已 symlink;直接 `PYTHONPATH=. .venv/bin/python -m ...`。

## Constraints

- **answer-agnostic 硬红线**:停滞检测只用**已测 fitness 轨迹**(cum_top10_max 曲线、距上次提升轮数);redirect 的候选只用 **surrogate 预测均值 + 相对当前已测最优簇的突变构成差异**;**绝不使用测试峰成分、绝不按目标峰调 N 或阈值**。任何"上帝视角"=刷分,禁止。
- **保留 C+A,别退化**:v0.5 的工具鲁棒(C)与 CV 透传(A)保留;B 的"自适应配比强制早期探索"是失败尝试——**v0.6 默认采集不再强制早期探索税**(吸取 rank-45 教训,默认强利用),backtrack 只作为停滞时的逃逸机制。
- **保留上一轮结果**:v0.1-v0.5 report 全留,v0.6 落新文件夹。
- 唯一变量是决策层(元层 backtrack + 两个自主度);池/cold-start/预算/门禁/seed/surrogate 全不变。
- 不做外部/破坏性动作;未分配文件面不写。

## Checkpoint

- 停手上报点:两个变体实现完 + 单测绿 + 两个 campaign 跑完拿到 cum_top10_max,先落盘再报,**不 push、不开 PR**(PR 面归 CEO)。
- 异议型停:若实测发现 backtrack 无效或有害(如 redirect 反而更差),带事件流证据 challenge,如实记负结果,不硬调。
- 越界即停:任何需要改门禁/oracle/seed 或按测试峰调参才能提分的路径,停并报——那是刷分信号。

## CI/Gate Authority Stop Condition

本任务非 CI/gate/governance 任务。若必须改 CI/gate authority surface 才能过,停实现、记 blocker、请 CEO 建治理任务。不削门、不绕 check、不调 oracle。

## Implementation Plan

在 v0.5 代码基础上增量:

**1. 停滞感知(共用)**:
- `state` 加 `top10_max_history`(每轮结束记 cum_top10_max)、`rounds_since_improvement`。
- `analyze_measured`(或新只读工具 `campaign_trajectory()`)透传:`cum_top10_max` 轨迹、距上次提升轮数、当前已测最优簇的突变构成(top-K 已测变体的共有/富集突变位点)。全部只读已测数据。

**2. redirect/escape 动作(共用)**:
- 新工具 `redirect_batch(n=48)`:组一批**高预测均值、但突变构成显著区别于当前已测最优簇**的门内候选(basin-hop)。实现:在门内池按 predicted_mean 降序,过滤掉与当前最优簇突变集合重叠度高的变体(或按突变位点 Jaccard 距离排序取高距离+高均值),返回 gate-safe 批次,复用 compose_batch 的暂存+`test_composed_batch` 原样测试。
- 默认(非停滞时):强利用(predicted_mean top-n,吸取 v0.5 教训不强制早期探索税)。

**3. 两个自主度变体**(用 CLI flag 或参数区分,如 `--backtrack full|semi`):
- **FULL(全自主)**:prompt 把轨迹/停滞信号/最优簇构成 + `redirect_batch` 动作都交给 LLM,**何时判停滞、是否 redirect、redirect 到哪**全由 LLM 判断。最纯的元层自主测试。
- **SEMI(半自主)**:停滞检测用硬规则(如 cum_top10_max 连续 ≥2 轮不涨 → 自动置 `stalled=true` 并在 prompt 明示);**redirect 到哪仍由 LLM 判断**。隔离出"LLM 的 redirect 判断质量"这一变量。

**4. 跑两个 campaign**(同 seed42/门禁/上位 surrogate,每轮 48,6 轮):
- `... --guardrail --surrogate epistasis --budget 48 --n-rounds 6 --seed 42 --model GLM-5.3 --backtrack full`(GLM 是 zcode/bypass,模型名以实际 llm.py 解析为准;若 GLM 端点模型名不同,按 agent/llm.py 的 config 用可用模型)。
- 同上 `--backtrack semi`。
- 落 `lab/reports/agentic-v0.6/`(可用子目录或文件名区分 full/semi)。
- 台账:`ha task progress append` 记进展;`ha fact record --task task_2e485a1ae862bdec5fcc7c9677` 记两变体实测结果(≥1 fact 满足完成门)。

> 注:LLM 后端。本任务由 GLM(zcode-glm-5-3)驱动;若 `agent/llm.py`/pydantic-ai 对 GLM 端点的 model id 与 `gpt-5.6-sol` 不同,用该端点实际可用的 model,并在 report/manifest 如实记录所用 model。核心是决策机制,不是具体后端。

## Deliverable Contract

- 代码:`agent/auto_researcher.py`(停滞感知 + redirect_batch + full/semi 变体);必要 `tests/`(redirect_batch 组批正确性 + 停滞检测硬规则 + answer-agnostic 单测)。
- 结果:`lab/reports/agentic-v0.6/report.md`(full vs semi 对照 + v0.1→v0.6 表 + backtrack 触发/生效机制 + 事件流)+ manifest.json + aav/ 产物(两变体各一套 metrics/events)。
- submit 带:completionClaim、deliverables、outputs(fact + report)、verificationNotes(实测命令 + 真实 runner 输出)、commitSha;本地 commit 为止,不 push 不 PR。

## Evidence Protocol

- 证据粒度:两变体各自 cum_top10_max 曲线 + strong 命中 + 事件链校验 + backtrack 触发次数/轮次 + redirect 批次的真值命中。
- 阴性对照:redirect 前后对比;停滞检测在"持续上升"的合成/真实序列上不误触发。
- 诚实纪律:full/semi 谁赢如实报;若都到不了 8.416,写清负结果 + 机制。不得为凑分改 oracle/门禁/seed/N 或按测试峰调 redirect。
- reviewer 拒收条件:answer-agnostic 违规、覆盖旧 report、削门凑分、把失败写成成功。
- 闭环:`ha fact record --task task_2e485a1ae862bdec5fcc7c9677 ...` 记实测,收据存 Execution outputs。

## Verification

- 停手点 = 触碰面定向测试绿 + 本地 commit(不 push/不 PR)。
- 定向测试集:(1) 新增 redirect/停滞检测测试 + `tests/test_auto_researcher_compose.py`(不回归)、`tests/test_auto_researcher_gate.py`、`tests/test_epistasis_surrogate.py`;(2) `git grep` 改动的工具名/字段名(redirect_batch、stalled、top10_max_history 等)跑到的消费者测试。
- 贴真实 runner 输出,不写 "all green"。
- 完成门:`code-doc-reconciliation` 要求 ≥1 fact,已在 Implementation Plan 用 `--task` 记 fact 满足。
- 附加人评:CEO 语义验收(answer-agnostic + 结果诚实 + full/semi 机制是否钉死)不可下放。
