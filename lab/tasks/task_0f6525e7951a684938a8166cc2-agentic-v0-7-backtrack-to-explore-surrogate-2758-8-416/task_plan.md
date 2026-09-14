# agentic v0.7:backtrack-to-EXPLORE——停滞时切探索捞 surrogate 隐形峰(#2758),追 8.416

Task Contract: harness-task v1

## Brief

基于一个已复现的重大更正:真峰 8.4162 对 surrogate 均值**隐形**(cold-start 排名 #2758),**纯利用/纯贪心 6 轮封顶 7.829**,那个达到 8.416 的"确定性基线"其实是 mean/diverse **交替**、峰是被**探索(diverse)轮**捞出来的。所以正确的破局方向不是"退回去纯利用"(v0.6 的错判据),而是 **backtrack-to-EXPLORE:停滞时切到探索(uncertainty/diverse)去捞 surrogate 看不见的高值变体**。保留 v0.5 的 C+A。做全自主 vs 半自主两变体,并多 seed 验证峰是否可靠可达(还是 seed42 运气)。全程 answer-agnostic。

## Goal

**可验证结果**:同池 27832/同 cold-start 10433/同 288 预算(48×6)/同门禁/同 EpistasisRidge surrogate 下,实现并跑 v0.7 的 backtrack-to-explore(full/semi 两变体),报告 cum_top10_max,对照四个参照点:纯均值 7.829(利用天花板)、朴素交替 mean/diverse 8.4162(seed42)、v0.4 LLM 7.829、v0.5 B 6.53。**多 seed(至少 42/0/7)跑参照与两变体,回答:探索能否可靠达峰(8.416),还是 seed42 运气?LLM 引导的探索能否打平/超过朴素 diverse?**

**诚实目标**:测"给 agent 元层自主 + 正确的探索导向,能否可靠捞出隐形峰"。赢=LLM 探索有价值(前沿说 LLM 是探索神器,这里验证);平/输=如实记(如探索达峰不稳、或 LLM 探索不如朴素 diverse)。不刷分、不按测试峰调参。

**交付**:`agent/auto_researcher.py`(+tests);结果落 `lab/reports/agentic-v0.7/`(report.md 含 full/semi × 多 seed 对照 + 参照点 + 达峰机制 + manifest + aav 产物)。首个消费者:CEO 验收 + 最终笔试报告。

## Context

- **重大更正(权威,fact F-8514C714 / F-6D7255DE,CEO 已独立复现)**:`agent/auto_researcher.py:535` 确定性 fallback 是 `by="predicted_mean" if rnd%2==0 else "diverse"`(交替,非纯贪心);v0.4 deterministic 曲线 `[7.391,7.391,7.829,8.4162,8.4162,8.4162]`,8.416 出现在 rnd3=diverse。纯均值 6 轮消融封顶 7.829(`[7.391,7.829×5]`);真峰在 cold-start EpistasisRidge 均值排名 **#2758**(门内)。**结论:纯利用够不到峰;达峰必须靠探索捞隐形峰;LLM 真短板是探索质量,不是利用不足。**
- **Astra 对抗分析(`lab/context/research/v06-backtrack-analysis.md`,fact F-6D7255DE)**:8 条"停滞→高均值/Jaccard redirect"续跑全停 6.5309;硬换构成可能排除目标;建议纯均值作基础、构成距离仅软约束——**但对 v0.7 更关键的是:redirect 要偏探索(uncertainty/diverse),不是偏利用**。
- **v0.5 C+A**(本 worktree 已含):C=工具鲁棒(0 崩溃);A=CV 透传(val_spearman/surrogate_status)。**保留。**
- **v0.6(GLM 并行,错判据版)**:高均值 redirect,作反面数据点,预期停 6.53。v0.7 不依赖它。
- **前沿定位**(`lab/context/research/frontier-landscape-synthesis.md` + 勘误):LLM 被认为是"探索神器";这里正是验证 LLM 探索能否捞出隐形峰的最佳场景。

## Required Reading

按序,标权威级:
1. `lab/context/research/v06-backtrack-analysis.md`(**权威·实测**:Astra 的重放/消融/rescue,含脚本与数字)。
2. `agent/auto_researcher.py`(**待改主体**:v0.5 的 compose_batch/surrogate_status/_gate_variants/safe_tool/list_pool(by=uncertainty/diverse)/确定性 fallback 交替逻辑 line~535)。
3. `models/train_ladder.py`(EpistasisRidgePredictor:predict 返回 (mean,var),var 供 UCB/uncertainty;val_spearman)。
4. `lab/reports/agentic-v0.4/report.md`(**带勘误**:确定性基线真相)、`lab/reports/agentic-v0.5/report.md`。
5. `evolution/datasets.py`(AAV 池/cold-start/oracle 口径)。

## Entry Conditions

- worktree(t-v07)从 v0.5 HEAD 分叉,含 C+A;`.venv`+`data/aav/full_data.csv` 已 symlink(冒烟:load('aav','one_hot')+EpistasisRidge OK)。
- 未满足即停并报。

## Dependencies

- 上游:v0.5 C+A、更正 fact F-8514C714/F-6D7255DE、Astra 分析。
- 下游:CEO 语义验收 + 最终报告。
- 并发:GLM 在 t-v06 改同名文件——**你在独立 worktree t-v07,天然无冲突;不要碰 t-v06。**

## Execution Surface

- 分支 t-v07(base=v0.5 HEAD);dispatcher 注入 cwd。
- **允许写范围**:`agent/auto_researcher.py`、`tests/`、`lab/reports/agentic-v0.7/`。
- 禁区:v0.1-v0.6 既有 report(只读对照);t-v06(GLM 在改);CI/门禁/oracle;其他文件面。
- **运行时已预置**:`.venv`、`data/aav/full_data.csv` symlink 好。

## Constraints

- **answer-agnostic 硬红线**:停滞检测只用已测 fitness 轨迹;探索候选只用 surrogate 的 (mean,var) + 门禁 + 已测数据(uncertainty/diverse/知识规则);**绝不用测试峰坐标、绝不按 #2758 的身份定向、绝不按目标峰调参**。探索是"去捞模型看不见的",不是"我知道峰在哪去拿"。
- **保留 C+A**;沿用 v0.5 的门禁/池/cold-start/预算/surrogate;唯一变量是决策层(探索导向的 backtrack + 两自主度)。
- **保留上一轮结果**:v0.1-v0.6 report 全留,v0.7 落新文件夹。
- 不做外部/破坏性动作;未分配文件面不写。

## Checkpoint

- 停手上报点:两变体 + 参照点多 seed 跑完 + 单测绿,先落盘再报,**不 push/不 PR**。
- 异议型停:若实测发现探索也达不到峰(多 seed 都够不到)、或 LLM 探索显著不如朴素 diverse,带证据如实记,不硬调。
- 越界即停:任何要改门禁/oracle/seed 或按测试峰身份选变体才能提分的路径,停并报=刷分信号。

## CI/Gate Authority Stop Condition

非 CI/gate 任务。若必须改 CI/gate authority surface 才能过,停实现、记 blocker、请 CEO 建治理任务。不削门/不绕 check/不调 oracle。

## Implementation Plan

在 v0.5 代码基础上增量:

**1. 停滞感知(共用)**:`state` 加 `top10_max_history` + `rounds_since_improvement`;`analyze_measured`(或新只读工具)透传轨迹 + 距上次提升轮数。

**2. explore 逃逸动作(核心,偏探索)**:
- 新工具/模式 `explore_batch(n=48)`:组一批**门内、高不确定性/高多样性**候选去捞隐形峰。判据(answer-agnostic):UCB(mean + β·sqrt(var))高分未测 + 序列空间 diverse spread(如相对已测集的突变构成距离),侧重 var/diversity 而非 mean。可参照 v0.5 已有的 diverse_score 与 list_pool(by="uncertainty"/"diverse"),但要能真正把 mean-rank 很低(如 #1000+)但 UCB 高的变体纳入。
- 默认非停滞时:强利用(top-mean),吸取 v0.6/rank-45 教训不无脑摊探索。

**3. 两自主度变体(`--backtrack full|semi`,或参数)**:
- **FULL**:prompt 交待"surrogate 顶端预测会在 ~7.8 处停住,真正最好的变体可能被 surrogate 严重低估(排名很靠后),要靠探索高不确定/多样区去捞;停滞时果断切探索";何时探索/探索多少全交 LLM。
- **SEMI**:硬规则——利用到停滞(cum_top10_max 连续 ≥2 轮不涨)自动置 stalled,强制若干探索轮;探索**怎么探**(uncertainty vs diverse vs 知识引导)由 LLM 定。

**4. 跑对照矩阵(多 seed 验证可靠性)**:同门禁/池/cold-start/上位 surrogate,每轮 48、6 轮。至少 seed ∈ {42, 0, 7}:
- 参照:纯均值(全利用)、朴素交替 mean/diverse(确定性,即现有 fallback);
- v0.7-full、v0.7-semi(LLM 驱动,模型用 GLM 或可用后端,以 llm.py 实际解析为准并如实记录)。
- 汇总:各配置 × 各 seed 的 cum_top10_max + 是否达峰(8.4162)+ strong。**核心回答:探索达峰是否 seed 稳健?LLM 探索 vs 朴素 diverse 谁更能捞峰?**
- 落 `lab/reports/agentic-v0.7/`;台账 `ha task progress append` + `ha fact record --task task_0f6525e7951a684938a8166cc2`(≥1 fact)。

> LLM 后端:本任务默认由 Astra/Sol(codex)或按 CEO 派发的实例驱动;model id 以 `agent/llm.py` 实际可用为准,report/manifest 如实记所用 model。核心是探索机制,不是后端。

## Deliverable Contract

- 代码:`agent/auto_researcher.py`(停滞感知 + explore 逃逸 + full/semi);tests(explore_batch 组批正确性 + 停滞检测 + answer-agnostic 单测)。
- 结果:`lab/reports/agentic-v0.7/report.md`(full/semi × 多 seed 对照 + 四参照点 + 达峰机制 + 是否 seed 稳健 + LLM vs 朴素 diverse)+ manifest + aav 产物。
- submit 带 completionClaim/deliverables/outputs(fact+report)/verificationNotes(实测命令+真实输出)/commitSha;本地 commit 为止,不 push 不 PR。

## Evidence Protocol

- 证据粒度:各配置×各 seed 的 cum_top10_max 曲线 + strong + 达峰标志 + 探索触发轮次 + 捞到峰时该变体在当轮 surrogate 的 mean-rank(证明"探索捞了隐形峰")。
- 阴性对照:shuffle 标签 CV 塌到 0;停滞检测在持续上升轨迹上不误触发。
- 诚实纪律:多 seed 达峰不稳/LLM 输给朴素 diverse 都如实写。不得为凑分改 oracle/门禁/seed 或按峰身份选变体。
- reviewer 拒收:answer-agnostic 违规、覆盖旧 report、削门凑分、把失败写成成功。
- 闭环:`ha fact record --task task_0f6525e7951a684938a8166cc2 ...` 记实测。

## Verification

- 停手点 = 触碰面定向测试绿 + 本地 commit(不 push/不 PR)。
- 定向测试集:新增 explore/停滞检测测试 + `tests/test_auto_researcher_compose.py`/`test_auto_researcher_gate.py`/`test_epistasis_surrogate.py` 不回归;`git grep` 改动的工具名/字段跑到的消费者测试。
- 贴真实 runner 输出,不写 "all green"。
- 完成门:`code-doc-reconciliation` 要求 ≥1 fact,已在 Implementation Plan 用 `--task` 记 fact 满足。
- 附加人评:CEO 语义验收(answer-agnostic + 达峰是否靠合法探索 + 多 seed 诚实)不可下放。
