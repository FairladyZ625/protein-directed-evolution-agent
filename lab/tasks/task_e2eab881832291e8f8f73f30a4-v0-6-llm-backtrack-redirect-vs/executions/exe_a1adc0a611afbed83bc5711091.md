# Execution exe_a1adc0a611afbed83bc5711091

Managed by `ha task start/submit`; hand edits are rejected.

- Task: task_e2eab881832291e8f8f73f30a4
- Iteration: 1
- State: changes_requested
- Claimed: 2026-09-14T09:46:32.834Z
- Submitted: 2026-09-14T09:46:33.104Z
- Closed: 2026-09-14T09:53:33.444Z
- Commit: none (artifact delivery)
- Artifact: tasks/task_e2eab881832291e8f8f73f30a4-v0-6-llm-backtrack-redirect-vs/artifacts/v06-backtrack-analysis.md@2321 (ef9d587d2d04ef208c32eb4c9049e321394457559eee1157cb12a1c333b1bbb1)
- Completion claim: 交付 `lab/context/research/v06-backtrack-analysis.md`(278 行,含可复跑的内嵌 runner 脚本):对 v0.6 "LLM 元层自主 backtrack/redirect"的对抗性分析——停滞是怎么产生的、backtrack 能不能达峰、redirect 判据该用"纯高均值"还是"换构成"。

本任务产出了整个项目**第一次结论翻转**,也是最重要的一次。此前 v0.4 报告与前沿综述都写着"确定性 gated-greedy 纯利用直达真峰 8.416,探索有毒,去自主化是解药"。本分析查代码 + 做纯均值消融后钉死:那条所谓的"确定性 greedy"基线,实现上是 `by = "predicted_mean" if rnd % 2 == 0 else "diverse"`——**mean/diverse 交替**,不是纯贪心;真峰出自第 4 轮的 diverse 批(当时均值排名 #1384),纯均值消融的上限只有 7.8290。

第二条机制发现同样承重:8 条 mean-redirect 续跑全部停在 6.5309,redirect 无效的原因不是实现错误,而是"无处可跳"——已测最优簇的突变签名为空(T20E 仅 4/10 < 阈值 5/10),redirect 退化为普通 greedy 批。这条否掉了"给 agent 更多自主性让它自己退回另一条路径"这个方案的可行性前提。

交付锚点:artifact:artifacts/v06-backtrack-analysis.md
- Reviews: review_de_reviewer_20260914_v06_iter1/changes_requested
- Selected review: pending
- Consent: pending
- Checker witnesses: pending
- Code-doc witness: pending

## Deliverables

- tasks/task_e2eab881832291e8f8f73f30a4-v0-6-llm-backtrack-redirect-vs/artifacts/v06-backtrack-analysis.md

## Outputs

- none

## Verification

- - 文档实存并已 canonical 登记:`lab/context/research/v06-backtrack-analysis.md`;fact `F-6D7255DE`。
- 翻转结论经 CEO 独立复核:我自己读 `agent/auto_researcher.py` 确认了交替采集那一行,并独立跑纯均值消融复现 7.8290 / strong=166,与本文档数值一致。
- 8 条停滞-redirect 续跑全部收敛到 6.5309,内嵌 runner 可复跑。
- 下游影响已落实:`lab/context/research/frontier-landscape-synthesis.md` 与 `lab/reports/agentic-v0.4/report.md` 均已加勘误横幅;fact 链 `F-EE89324D`(错)→ `F-8514C714`(部分错)→ `F-885537A3`(最终)在台账中成立。

## Known gaps

- - 本文档的结论"达峰必须靠探索、纯利用封顶 7.829"在当时成立,但它引出的下一句"没有方法能可靠够到这根针"**已被推翻**:`lab/context/research/v07-multiseed-robustness.md` 的 30seed × 7 方法矩阵显示 UCB β=3 确定性 30/30 达峰。最终定性以 `F-885537A3` 为准,阅读本文档时须带这个时效。
- redirect 无效的判定基于本实现的签名阈值(5/10),换判据未必同结论;本文档已声明这是对**该判据**的否定,不是对 backtrack 思想的全称否定。
- 分析过程中使用了测试峰身份做事后诊断(排名 #1384、#15 等),这是诊断而非调参;但它意味着本文档本身不是 answer-agnostic 产物,不能作为方法设计的输入。
- "基线被错标,导致整条叙事建立在不存在的现象上"是最贵的一类错误,本项目在 v0.4 中招。同族风险在别处仍在:①`agent/llm.py` 实际解析到的网关模型是 `claude-sonnet-5`,而 metrics/manifest 自 v0.4 起标注 `gpt-5.6-sol`——同样是标签与实现不一致,最终报告必须按实际值改写;②图表任务发现的 GB1 冷启动 regime 混用与 AAV incumbent/新查询最大值混淆,也是同一族。通用纪律:任何"某方法赢了"的结论,先去读那个方法的实现,不读代码不写结论。

## Residual risks

- - 本文档的结论"达峰必须靠探索、纯利用封顶 7.829"在当时成立,但它引出的下一句"没有方法能可靠够到这根针"**已被推翻**:`lab/context/research/v07-multiseed-robustness.md` 的 30seed × 7 方法矩阵显示 UCB β=3 确定性 30/30 达峰。最终定性以 `F-885537A3` 为准,阅读本文档时须带这个时效。
- redirect 无效的判定基于本实现的签名阈值(5/10),换判据未必同结论;本文档已声明这是对**该判据**的否定,不是对 backtrack 思想的全称否定。
- 分析过程中使用了测试峰身份做事后诊断(排名 #1384、#15 等),这是诊断而非调参;但它意味着本文档本身不是 answer-agnostic 产物,不能作为方法设计的输入。
- "基线被错标,导致整条叙事建立在不存在的现象上"是最贵的一类错误,本项目在 v0.4 中招。同族风险在别处仍在:①`agent/llm.py` 实际解析到的网关模型是 `claude-sonnet-5`,而 metrics/manifest 自 v0.4 起标注 `gpt-5.6-sol`——同样是标签与实现不一致,最终报告必须按实际值改写;②图表任务发现的 GB1 冷启动 regime 混用与 AAV incumbent/新查询最大值混淆,也是同一族。通用纪律:任何"某方法赢了"的结论,先去读那个方法的实现,不读代码不写结论。
