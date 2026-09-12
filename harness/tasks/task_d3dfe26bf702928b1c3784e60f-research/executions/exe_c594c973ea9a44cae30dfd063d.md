# Execution exe_c594c973ea9a44cae30dfd063d

Managed by `ha task start/submit`; hand edits are rejected.

- Task: task_d3dfe26bf702928b1c3784e60f
- Iteration: 1
- State: changes_requested
- Claimed: 2026-09-12T12:59:32.780Z
- Submitted: 2026-09-12T13:07:44.054Z
- Closed: 2026-09-12T13:10:18.090Z
- Commit: 01328291e5b2ac789337acb55ee1b3c737048490
- Completion claim: 交付 `harness/context/research/plateau-breaking-methods.md`:对"主动学习/定向进化撞上平台期时,真实蛋白工程科学家有哪些 answer-agnostic 破局手段"的文献调研,并把每个方法族映射回本题的笼子(池式、288 预算、in-silico 查表 oracle)判断能否落地。

本任务最承重的产出不是文献清单,而是一条自证观察:cold-start(HD≤2,10433 条)**本来就含有构成真峰的单突变与双突变实测**——D0Q 单点 +1.22、S17E Δ+4.2、V18A Δ+1.8 都在数据里。真峰之所以隐形,是因为当时的 surrogate(加性 Ridge / kNN / GBM)**表达力不覆盖交互项**,而不是数据量、预算或表征不足。这条判断直接推导出实验三/v0.4 的提名 B(上位感知 surrogate),后续被落地为 `EpistasisRidgePredictor`(one-hot 二阶交互),是整条 v0.4→v0.7 线的起点。

同时给出三条破局必要条件:①显式建模上位而非加性可分解;②不用自然度先验筛突变(否则把反自然峰重新藏起来——这一条后来被 ESM zero-shot 的实测失败证实);③能主动提出 HD3 组合而非加性单步贪心游走。

交付提交:`01328291e5b2ac789337acb55ee1b3c737048490`(平台期破局手段调研)。
- Reviews: de-reviewer-20260912-plateau-amend1/changes_requested
- Selected review: pending
- Consent: pending
- Checker witnesses: pending
- Code-doc witness: pending

## Deliverables

- harness/context/research/plateau-breaking-methods.md

## Outputs

- none

## Verification

- - 文档实存:`harness/context/research/plateau-breaking-methods.md`,已通过 `ha doc sync --submit` 登记为 canonical。
- 承重观察经 CEO 独立 ground-truth:真峰三个单突变的孤立效应值、D0Q 共现富集 −0.01、cold-start 含 HD≤2 全部实测,均由仓库内数据复算确认(文档中标 ✔已核实 的条目)。
- 落地闭环成立:本文档推出的提名 B 已实现为 `models/train_ladder.py` 的 `EpistasisRidgePredictor`,并在 v0.4–v0.7 全线服役;其"表达力不足"诊断被 `harness/context/research/v07-peak-mechanism.md` 独立复核后修正为更精确的版本(关键二阶组合**缺测** + 正则化模型头部外推失真),方向一致、机制更细。
- 条件②(不用自然度先验)被 `analysis/esm_zeroshot_scan.py` 的实测失败(峰 z 为负)证实。

## Known gaps

- - 文档中未标 ✔ 的文献条目为扫描结果而非逐篇核读,正式学术引用前需再核 DOI 与结论措辞;`harness/tasks/task_e57782279c8d2535f15290af4e-scientific-report-v1-0` 的 Crossref 校验体系应作为引用前置。
- "瓶颈是 surrogate 表达力"这一判断在 v0.7 被精炼:表达力之外还有**数据覆盖**(门内 11130 种具体残基对中 7937 种未测,fact F-159073F2)。本文档的原表述偏强,最终报告应以 v07-peak-mechanism 的双因素版本为准。
- 文档写于 v0.3 时期,其中"7.53 是天花板"的表述已被 v0.7 取代(纯利用上限 7.8290;UCB β=3 达峰 8.4162,30/30)。以 fact `F-885537A3` 为准。
- "把失败归因到数据量/表征,而真因是模型表达力或数据覆盖"这个误诊模式,在本项目至少复发两次:①实验二把希望寄托在 ESM 表征升级上(失败);②v0.6 把停滞归因于"没有 backtrack 机制"(redirect 实现后无效,因为根本无处可跳)。两次都是先换更贵的组件、后才去查机制。对应的通用纪律:平台期先做**只读反事实消融**定位瓶颈层,再决定换哪个组件——这条已写入 `harness/context/research/v07-consolidated-summary.md` 的方法论部分。

## Residual risks

- - 文档中未标 ✔ 的文献条目为扫描结果而非逐篇核读,正式学术引用前需再核 DOI 与结论措辞;`harness/tasks/task_e57782279c8d2535f15290af4e-scientific-report-v1-0` 的 Crossref 校验体系应作为引用前置。
- "瓶颈是 surrogate 表达力"这一判断在 v0.7 被精炼:表达力之外还有**数据覆盖**(门内 11130 种具体残基对中 7937 种未测,fact F-159073F2)。本文档的原表述偏强,最终报告应以 v07-peak-mechanism 的双因素版本为准。
- 文档写于 v0.3 时期,其中"7.53 是天花板"的表述已被 v0.7 取代(纯利用上限 7.8290;UCB β=3 达峰 8.4162,30/30)。以 fact `F-885537A3` 为准。
- "把失败归因到数据量/表征,而真因是模型表达力或数据覆盖"这个误诊模式,在本项目至少复发两次:①实验二把希望寄托在 ESM 表征升级上(失败);②v0.6 把停滞归因于"没有 backtrack 机制"(redirect 实现后无效,因为根本无处可跳)。两次都是先换更贵的组件、后才去查机制。对应的通用纪律:平台期先做**只读反事实消融**定位瓶颈层,再决定换哪个组件——这条已写入 `harness/context/research/v07-consolidated-summary.md` 的方法论部分。
