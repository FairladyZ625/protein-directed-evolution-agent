---
schema: decision-package/v1
decision_id: dec_016C25D18F5C1C17F9A7173E75
workspaceRevision: 1119
title: "锁定最终科学定性:两个目标、两套相反的最优策略;LLM 自主在优化内核是负担"
state: proposed
riskTier: high
urgency: high
vertical: "software/coding"
preset: "decision-conformance"
decisionClass: ordinary
applies_to: {"modules":[],"productLines":[]}
proposer: {"executor":{"id":"claude-session:a11ed5b6-6214-43b0-b577-d3e16d449705","kind":"agent"},"principal":{"personId":"person-ai4s"}}
arbiter: null
proposedAt: "2026-09-12T09:37:45.147Z"
decidedAt: null
provenance: [{"boundAt":"2026-09-12T09:37:45.147Z","runtime":"claude","sessionId":"a11ed5b6-6214-43b0-b577-d3e16d449705","transcriptReachability":"by_session_id"}]
question: "本项目对外的核心科学结论,应该锁定为哪一句?"
chosen: [{"id":"CH1","rationale":"这是唯一同时容纳了 30seed×7方法实测、前沿 Greenman(FLIP-AAV 上 greedy>uncertainty>random)与我们自己 LLM 负结果的表述;它不需要任何一方被淡化。","text":"以两指标分裂为最终定性:目标为'找大量强变体'时纯利用/greedy 最优(strong=166);目标为'找单个全局峰'时重不确定性探索 UCB β=3 最优(确定性 30/30 达峰 8.4162);两个最优都由简单固定采集函数达成,LLM 自主决策两个都没匹配上。"},{"id":"CH2","rationale":"评委考的是科研能力与科研思维而非分数;被证据逼着精炼四次、每次都公开推翻自己,是本项目最不可复制的部分。","text":"把四次证据驱动的结论翻转写进报告正文作为科研能力证据,而不是藏进附录。"},{"id":"CH3","rationale":"红队第一击命中的是任务设定本身;自曝的代价远小于被评委抓出来的代价,且自曝本身就是科研诚实的证据。","text":"六条诚实边界必须逐条在正文自曝,其中'池内峰 8.4162 低于 cold-start incumbent 9.5365'必须正面写清。"}]
rejected: [{"id":"RJ1","text":"沿用 v0.4 的'确定性 greedy 直达真峰、探索有毒、去自主化是解药'。","whyNot":"实证为假:那条基线实现上是 mean/diverse 交替(agent/auto_researcher.py),纯均值消融封顶 7.8290,真峰出自 diverse 批。"},{"id":"RJ2","text":"沿用中间版本的'没有方法能可靠够到这根针'。","whyNot":"被 30seed×7方法矩阵推翻:UCB β=3 确定性 30/30 达峰,不是谁都够不到。"},{"id":"RJ3","text":"只报单峰命中率,不提 bulk 强变体产量。","whyNot":"会与前沿 Greenman 在同一数据集上的结论正面冲突,且会掩盖 greedy 的真实优势,属选择性汇报。"},{"id":"RJ4","text":"把 UCB β=3 写成事前设计的预见。","whyNot":"β=3 是预注册 sweep 的事后发现,先验并不知道;写成预见即为叙事污染。"}]
claims: [{"fulfillment":"evidenced","id":"C1","loadBearing":true,"text":"在同池同预算(27832池/10433 cold-start/9533门内/288预算)下,纯利用 greedy 的 top-10% 强变体产量为全场最高 strong=166 且达峰 0/30;UCB β=3 达峰 30/30、cum_top10_max=8.4162 但 strong=128;低 β(0.5/1/2)全停 6.5309;LLM-agentic 两个指标都未匹配最优。"},{"fulfillment":"evidenced","id":"C2","loadBearing":true,"text":"池内峰 8.4162 低于 cold-start 已含的 incumbent 9.536457,因此'发现池内峰'不等于'超越已知最优',该优化目标设定本身有局限。"}]
judgmentConsents: []
amendments: [{"actor":{"executor":{"id":"claude-session:a11ed5b6-6214-43b0-b577-d3e16d449705","kind":"agent"},"principal":{"personId":"person-ai4s"}},"amendedAt":"2026-09-12T09:38:09.876Z","amendmentId":"dam_36e382afdc67d80d5b7255a675","fields":["body"],"schema":"decision-amendment/v1"}]
contentPins: [{"action":"amend","actor":{"executor":{"id":"claude-session:a11ed5b6-6214-43b0-b577-d3e16d449705","kind":"agent"},"principal":{"personId":"person-ai4s"}},"digest":"sha256:e9ace132def39908583752f81e6a08dcc325ea6e366b3b6faa00432c576e1aa0","evidence":"fields:body","pinId":"dcp_36e382afdc67d80d5b7255a675","pinnedAt":"2026-09-12T09:38:09.876Z","schema":"decision-content-pin/v1","state":"proposed"}]
---
## 背景

本项目对外的核心结论,在 v0.1→v0.7 的过程中被证据推翻了四次:

1. v0.4 起初写:"确定性 greedy 纯利用直达 8.416,探索有毒,去自主化是解药。"
2. 自证伪:查 `agent/auto_researcher.py` 发现那条"确定性 greedy"实现上是 `predicted_mean`/`diverse` **交替**;纯均值消融封顶 7.8290;真峰在门内均值排名 #426 处隐形,是被 diverse 批捞出来的。结论改为"达峰必须靠探索"。
3. 联网证伪:Greenman 等人在 FLIP-AAV 上的不确定性量化基准显示 greedy 强于 uncertainty 强于 random。发现前一步是**指标混淆**,改为"两指标分开看"。
4. 多 seed 硬化:30 seed × 7 方法的 β-sweep 显示 UCB β=3 确定性 30/30 达峰。最终收敛为本裁定 CH1。

每一次都是被证据逼着收缩,不是一开始蒙对。

## 裁定

采纳 CH1/CH2/CH3。最终定性锁定为两指标分裂:目标不同,最优策略相反;两个最优都由简单固定采集函数达成;LLM 的自主决策在优化内核是负担,两个最优都没匹配上。四次翻转写进正文,六条边界逐条自曝。

驳回 RJ1(实证为假)、RJ2(已被 30/30 推翻)、RJ3(选择性汇报)、RJ4(叙事污染)。

## 影响

- 最终报告 v1.0 的结论章作废,须按本裁定重写(派生 `task_db4ace109f72a92847c7349fe1`)。
- AAV 科学图表须重绘以呈现两指标分裂(派生 `task_f9a282c594dbb92bf1b9e0a18b`)。
- 优化目标的指标定义需要单独定夺,因为 CH3 暴露了"峰 < incumbent"(派生 `task_cec65c821f05a08d9a86681332`)。
- 所有早于本裁定的报告与研究文档,凡结论与本裁定冲突处,以 fact `F-885537A3` 为准;`frontier-landscape-synthesis.md` 与 `agentic-v0.4/report.md` 已加勘误横幅。
