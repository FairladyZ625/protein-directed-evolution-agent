# Research:主动学习/定向进化遇到平台期时,人类蛋白工程科学家的合法破局手段

Task Contract: harness-task v1

## Brief

我们的定向进化 agent 在 AAV 靶点上遇到了一个真实的平台期:同预算(288 次测量)、HD≤2 冷启动下,无论自由探索(v0.1=5.96)、知识门禁(v0.2=7.53)、还是换表征×代理(one_hot/ESM embedding × Ridge/kNN/GBM),cum_top10_max 都卡在 7.53,从第 3 轮起不再提升;池中真峰 8.42 是一个 HD3 的**正上位效应**变体,对代理排序和加性排序都"隐形"。本 Research 要回答:**面对这种平台期,真实的蛋白工程/定向进化科学家会用哪些合法手段破局?** 并把每种手段映射到"我们的 agent 在其工具牢笼里能否合法使用"。

## Goal

产出一份研究文档 `harness/context/research/plateau-breaking-methods.md`,系统梳理"主动学习/定向进化在 in-silico 代理预测遇到天花板时,人类科学家的破局策略",每条给出:①方法原理 ②代表文献/工具 ③它为什么可能突破"上位效应隐藏的峰" ④在我们的 agent 工具笼(池式、oracle=测量表查询、288 预算、工具 analyze_measured/predict/list_pool/check_knowledge/test)里能否合法落地、需要新增什么工具 ⑤**是否 answer-agnostic**(绝不能是"看着测试答案倒推")。最后给一个**按"合法性×可行性×破顶潜力"排序的候选清单**,供 CEO 裁定下一步实验。

## Context

- 关键约束(项目哲学,CEO 泽宇裁定):我们不是刷分,是让 agent **在合理范围内、用人类 researcher 的思维**解决问题。任何"上帝视角看着答案、把答案编进方法"的做法=过拟合/泄题,禁止。方法必须 answer-agnostic。
- 已知机制(供理解平台期,不是让你去命中答案):真峰 8.42 = HD3 正上位效应,其中一个突变在低阶数据里看似中性 → 代理与加性排序都排不到可达区(最好 esm2×knn 也把它排在门内 #1283,预算 288 够不着)。
- 一个已识别的自身盲点:我们只把 ESM-2 当**向量化器**(embedding+回归),**没用 ESM 的 zero-shot 突变效应打分(LM head,如 ESM-1v)**——这是 answer-agnostic 的真预测工具,应作为重点调研对象之一,但不要把结论局限在 ESM。

## Required Reading

1. `harness/context/research/AI4S-assignment.md` + `AI4S-domain-research.md`(试题与既有领域调研,理解任务设定)。
2. `harness/reports/agentic-v0.2/report.md` 与 `agentic-v0.3/aav/surrogate_scan.json`(平台期与诊断的定量证据)。
3. 自主检索:蛋白工程/定向进化/机器学习引导进化(ML-guided directed evolution)/active learning for protein fitness/zero-shot variant effect prediction 的近年综述与代表工作。

## Entry Conditions

agy(Gemini)可联网检索;可写 `harness/context/research/`。若联网受限,如实说明并给出基于已有知识的最佳综述,不编造引用。

## Dependencies

上游:实验一/二的平台期结论(agentic-v0.2/v0.3)。下游:CEO 据此裁定实验三的合法方法(很可能含 ESM zero-shot 与其他 answer-agnostic 手段);反哺最终报告"agent 如何像科学家一样面对瓶颈"章节。

## Execution Surface

只读检索 + 写 `harness/context/research/plateau-breaking-methods.md`(可附一个 `plateau-breaking-shortlist.md` 或在同文档内给排序清单)。不改代码、不动实验产物、不做破坏性操作。

## Constraints

- **单代理模式(硬性,本仓 agy headless 约束):禁 Booster、禁 spawn 子代理**——异步子代理在 headless 单轮 dispatch 下不落盘。单代理顺序覆盖各方法族:LM/zero-shot 预测器、结构/物理先验、组合与上位效应设计、主动学习采集策略、迁移/微调、生成式设计、湿实验/预算迭代范式,当轮亲自综合并写文件。
- **answer-agnostic 硬约束**:所有方法都不得依赖"已知测试峰的成分";凡是只有看着答案才成立的招,明确标注并排除。
- 引用要真实可核(给标题/作者/年份/出处);拿不准的标注为"待核实",不伪造 DOI。
- 结论区分"人类实验室能做但我们 in-silico 笼子里做不了"(如真做湿实验)与"agent 在现有/小幅扩展工具下能合法做"。
- 中文输出,面向 CEO 决策;技术术语保留英文。

## Checkpoint

- 检索铺开后,若发现方法族远超预期,先在文档里列出方法族目录 + 每族一句话,再展开——避免只深挖一族。
- 若判断"在 288 预算、in-silico oracle 的笼子里,任何 answer-agnostic 方法都无法破 7.53",这本身是重要结论,如实写,并说明需要放宽哪个约束(预算/冷启动/oracle/工具)才可能破,以及那样是否仍公平。

## CI/Gate Authority Stop Condition

docs-task,无 CI/gate;产出研究文档即可。不触碰治理/CI 面。

## Implementation Plan

1. 多代理分族检索(见 Constraints 的分工),每族收集 3–6 篇代表工作 + 核心方法。
2. 汇总成 `plateau-breaking-methods.md`:方法族 → 每条按 Goal 的五要素填表。
3. 给"合法性×可行性×破顶潜力"排序候选清单(标出哪些 answer-agnostic 且在我们笼子里可落地)。
4. 特别评估 ESM zero-shot(LM head / ESM-1v 类)在我们池式设定下的可行性与预期。
5. 文末给 CEO 3 条以内的"建议下一步实验"提名(仅提名,裁定归 CEO)。

## Deliverable Contract

- `harness/context/research/plateau-breaking-methods.md`:方法族综述 + 五要素表 + 排序候选清单 + 3 条以内实验提名。
- 真实可核引用;answer-agnostic 标注齐全。

## Evidence Protocol

- 每条方法附可核引用(标题/作者/年份/出处);不可核的标"待核实"。
- 破顶潜力的判断给出理由(为何可能触及上位效应隐藏的峰),不空断言。

## Verification

- 通过判据:文档覆盖 ≥5 个方法族、每条五要素齐全、有排序清单与实验提名、引用可核、answer-agnostic 约束贯彻。
- CEO 语义验收:提名的方法确实是"人类科学家会做且我们笼子里能合法做"的,不含泄题式招法。
