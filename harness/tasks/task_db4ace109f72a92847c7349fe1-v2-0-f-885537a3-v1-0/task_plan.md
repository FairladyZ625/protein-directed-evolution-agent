# 最终报告 v2.0:按 F-885537A3 重写结论,复用 v1.0 引证体系

Task Contract: harness-task v1

## Brief

`reports/scientific_report_v1.0.md` 的体裁、引证体系与写作规范是合格的(30 篇文献经 Crossref 全要素校验、GB/T 7714-2015 顺序编码、正文与文末 1:1 闭环),但它的**核心科学结论写于 v0.4 叙事之下,此后被证据推翻了四次**。本任务产出 v2.0:保留引证与体裁基座,重写结论。

## Goal

产出 `reports/scientific_report_v2.0.md`,核心变更三项:
1. **结论章按 `F-885537A3` 重写**:两个目标两套相反策略——纯利用/greedy 赢"大量强变体"(strong=166,与 Greenman 在 FLIP-AAV 上 greedy>uncertainty>random 一致);重不确定性探索 UCB β=3 赢"单个全局峰"(确定性 30/30 达峰 8.4162);LLM 自主决策两个都没匹配上。
2. **新增"自我纠错"一章**,把四次结论翻转写成正文而非附录——这是本项目最不可复制的科研能力证据。
3. **诚实边界章**逐条自曝(见下)。

首个消费者:笔试评委。

## Context

- 最终定性:`F-885537A3`;supersession 链 `F-EE89324D` → `F-8514C714` → `F-885537A3`。
- 四次纠错弧与六路加固结果已整理在 `harness/context/research/v07-consolidated-summary.md`。
- 必须自曝的边界:①池内峰 8.4162 **低于** cold-start incumbent 9.5365;②β=3 是预注册 sweep 的**事后**发现,先验不知;③确定性方法 30 次是同一轨迹,Wilson CI 无效;④适应性泄漏(单轮采集盲于标签,但研发过程是人在环逐版改方法);⑤FLIP-AAV 原生是回归基准、无规范全局最优,"池式优化+达峰"是本项目自造构造;⑥知识库含 GB1 遗留硬编码。
- **数据卫生**:v0.4 起 metrics/manifest 标注的 `gpt-5.6-sol` 与实际解析模型 `claude-sonnet-5` 不符,v2.0 的 LLM 归属必须写实际值。
- v1.0 的引证脚本与规范在 `.skills/scientific-writing/`。

## Required Reading

1. `harness/context/research/v07-consolidated-summary.md`(**权威**:最终定性与边界清单)。
2. `harness/context/research/v07-multiseed-robustness.md`(**权威**:30seed×7方法的确切数字)。
3. `reports/scientific_report_v1.0.md`(**体裁与引证基座**,结论部分只读不抄)。
4. `harness/context/research/v07-redteam-critique.md` + `v07-peak-mechanism.md` + `v07-constructive-conclusion.md`。
5. `harness/context/research/frontier-landscape-synthesis.md`(**注意已打勘误横幅**,以 F-885537A3 为准)。

## Entry Conditions

- 目标指标已由 `task_cec65c821f05a08d9a86681332` 定下(若未定,先按 v0.7 两指标并列写,并在文中标注待定)。
- `.skills/scientific-writing/scripts/verify_citations.py` 可跑。

## Dependencies

上游:目标重框定任务、图表重绘任务(`task_f9a282c594dbb92bf1b9e0a18b`)。下游:笔试交付。并发:与图表任务共享 `reports/`,**图表任务只写 `reports/figures/**`,本任务只写 `reports/scientific_report_v2.0.md` 与其 manifest**,互不越界。

## Execution Surface

仓库根或独立 worktree;允许写 `reports/scientific_report_v2.0.md`、`reports/figure-manifest-v2.md`。禁区:`reports/scientific_report_v1.0.md`(保留为历史版本,不得覆盖)、所有产品代码、`reports/figures/**`。

## Constraints

- **不得重复 v1.0 的错误结论**;凡引用旧结论处必须标明已被 F-885537A3 取代。
- 引证必须 1:1 闭环,新增文献同样过 Crossref 校验。
- 不得声称未验证的能力(自演进、因果归因引擎等均为 future-work 设计,不是已实现)。
- 不得把"β=3 有效"写成"我们预见到了"。

## Checkpoint

写完结论章与自我纠错章即停并报大纲 + 结论章全文,由 CEO 语义验收后再续写其余章节。**异议型停**:若发现某条边界自曝会使整篇失去说服力,带替代表述来谈,不要私自淡化。

## CI/Gate Authority Stop Condition

非 CI/gate 任务(docs-task 无 CI 门)。不碰 CI/门禁/oracle。

## Implementation Plan

- 先出大纲 + 结论章,报 CEO。
- 通过后补齐其余章节,复用 v1.0 的引证条目并补新引用。
- 跑 `verify_citations.py`,确保 1:1 闭环。
- `ha fact record --task task_db4ace109f72a92847c7349fe1` 记交付与残留风险。

## Deliverable Contract

`reports/scientific_report_v2.0.md` + 图表清单;≥1 fact;回报:结论章一句话 + 引证校验结果 + 哪些边界已自曝。

## Evidence Protocol

每个数字给出处(报告/研究文档的具体路径);区分实测与推断;LLM 归属写实际值。

## Verification

停手点 = 报告落盘 + 引证校验通过 + ≥1 fact。CEO 亲做语义验收:结论是否等于 F-885537A3、六条边界是否逐条出现在正文。
