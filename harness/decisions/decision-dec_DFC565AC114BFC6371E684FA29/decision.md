---
schema: decision-package/v1
decision_id: dec_DFC565AC114BFC6371E684FA29
workspaceRevision: 1282
title: "修订 D2 表征口径:ESM-2 降为预测器阶梯的表征对照,闭环 campaign 用 one-hot 并记录 provenance"
state: proposed
riskTier: medium
urgency: high
vertical: "software/coding"
preset: "decision-conformance"
decisionClass: ordinary
applies_to: {"modules":[],"productLines":[]}
proposer: {"executor":{"id":"claude-session:a11ed5b6-6214-43b0-b577-d3e16d449705","kind":"agent"},"principal":{"personId":"person-ai4s"}}
arbiter: null
proposedAt: "2026-09-12T11:17:51.577Z"
decidedAt: null
provenance: [{"boundAt":"2026-09-12T11:17:51.577Z","runtime":"claude","sessionId":"a11ed5b6-6214-43b0-b577-d3e16d449705","transcriptReachability":"by_session_id"}]
question: "D2 声称『ESM-2 650M 主力(L2)+ one-hot(L1)』,但闭环实际跑的是 one-hot。是补齐全空间 ESM 缓存去兑现声称,还是把声称改成实测支持的样子?"
chosen: [{"id":"CH1","rationale":"实测不支持『ESM 主力』:GB1 predictor ladder 上 ESM-2 仅在 ridge(0.4925 vs 0.4840)与 mlp(0.4914 vs 0.3892)略胜,在 xgboost 上反而大幅落后(0.3768 vs 0.4741);v0.3 的 ESM zero-shot 更是实测失败(真峰 z 为负)。把没有证据支持的东西写成主力,是声称与实现不一致的另一种形态。","text":"修订 D2:ESM-2 定位为『预测器阶梯上的表征对照』(已提交样本块可复现),闭环 campaign 明确使用 one-hot 特征并在产物中记录 feature provenance;报告把『ESM 未带来稳定增益』作为诚实负结果写出来。"}]
rejected: [{"id":"RJ1","text":"补齐 149,361 条全空间 ESM-2 嵌入以兑现原 D2。","whyNot":"1280 维 float32 约 765MB,不可提交,评委无法复现;试题四·考核重点明确『不要求训练大型蛋白质模型』;且即便补齐,实测也不支持 ESM 优于 one-hot——那是花大代价去兑现一个错误的声称。"},{"id":"RJ2","text":"维持 D2 原文不动,报告里回避表征口径。","whyNot":"这正是审计判定 D2 打回的原因,回避等于把已知的声称-实现不一致带进交付物。"},{"id":"RJ3","text":"把全空间 ESM 缓存做成本地生成、不提交、README 说明。","whyNot":"技术上可行且更接近原 D2,但仍建立在『ESM 更强』这个未被实测支持的前提上,收益不确定而复现门槛显著抬高;留作 future-work,不在本次交付。"}]
claims: [{"fulfillment":null,"id":"C1","loadBearing":true,"text":"GB1 预测器阶梯实测:ESM-2 表征未稳定优于 one-hot——ridge 0.4925 vs 0.4840、mlp 0.4914 vs 0.3892,但 xgboost 0.3768 vs 0.4741 显著落后;因此『ESM-2 为主力表征』缺乏实证支持。"},{"fulfillment":null,"id":"C2","loadBearing":true,"text":"已提交的 1280 维 ESM 缓存仅覆盖 5000/2168/两个 2000 样本块,不含 149361 全空间,故闭环 campaign 在可提交范围内无法以 ESM 特征对全池排序。"}]
judgmentConsents: []
---

# 修订 D2 表征口径:ESM-2 降为预测器阶梯的表征对照,闭环 campaign 用 one-hot 并记录 provenance
