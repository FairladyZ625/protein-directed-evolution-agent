---
schema: decision-package/v1
decision_id: dec_DFC565AC114BFC6371E684FA29
workspaceRevision: 1708
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
amendments: [{"actor":{"executor":{"id":"claude-session:a11ed5b6-6214-43b0-b577-d3e16d449705","kind":"agent"},"principal":{"personId":"person-ai4s"}},"amendedAt":"2026-09-12T13:18:36.868Z","amendmentId":"dam_14100752a8e1d388e69f206c64","fields":["body"],"schema":"decision-amendment/v1"}]
contentPins: [{"action":"amend","actor":{"executor":{"id":"claude-session:a11ed5b6-6214-43b0-b577-d3e16d449705","kind":"agent"},"principal":{"personId":"person-ai4s"}},"digest":"sha256:d139325725b687d36313d4371f2a0cdf21ece89e2d7905b07912fd1704e8ac22","evidence":"fields:body","pinId":"dcp_14100752a8e1d388e69f206c64","pinnedAt":"2026-09-12T13:18:36.868Z","schema":"decision-content-pin/v1","state":"proposed"}]
---
## 背景

D2 原声称「ESM-2 650M 主力(L2)+ one-hot(L1)」。审计发现闭环 campaign 实际跑的是 one-hot
(`evolution/pool_campaign.py:85` 返回 `RidgePredictor(seeds=5)`,无 ESM、无标准化),于是提出本裁定:
是补齐全空间 ESM 缓存去兑现声称,还是把声称改成实测支持的样子。

本裁定最初选择了后者——把 ESM-2 从主力降为「表征对照」——依据是预测器阶梯里 ESM 未稳定优于
one-hot(ridge 0.4925 vs 0.4840、xgboost 0.3768 vs 0.4741)。

**该依据已被推翻(fact F-5CC3FABA)。** 那组数出自固定 `Ridge(alpha=1)`,而 alpha=1 对两种特征
意味着完全不同的正则化强度:one-hot 逐维方差约 0.25,GB1 的 ESM-2 约 1e-4(实测中位数 1.06e-4)。
先做标准化消融(F-1E17A592):同一份数据、唯一变量是标准化,esm2 ridge 从 raw 0.4911 掉到
standardized 0.2944,结论随预处理反向——说明固定 alpha 下的任何一侧都不能支撑排序断言。
再做 answer-agnostic 的 alpha 扫描(训练集内 80/20 留出选 alpha,不看测试集):

| 划分 | one-hot raw / std | esm2 raw / std |
|---|---|---|
| random | 0.4840 / 0.4840 | 0.4893 / 0.4916 |
| hd_extrapolation | 0.3588 / 0.3530 | 0.4039 / 0.4090 |

两点结论:标准化伪影在调过 alpha 后完全消失(esm2 两侧收敛到 0.489/0.492 与 0.404/0.409);
**ESM-2 在 hd_extrapolation 上稳定高出 one-hot 约 0.05 Spearman,两种预处理下一致**,random 划分上
也略高 0.005~0.008。hd_extrapolation 正是「向远端突变体外推」,是定向进化真正要的能力。

## 裁定

撤回「把 ESM-2 降为表征对照」这一选择,改为:

1. **D2 关于表征优劣的声称成立,不必下调**——ESM-2 在外推划分上实测优于 one-hot(Ridge 一级)。
2. **真正的落差改述为:闭环 campaign 没有用上这个更好的表征。** 这不是声称不实,而是主路径
   把已验证的收益留在桌上。`pool_campaign` 的 predictor 应接入 ESM-2 + answer-agnostic 的 alpha 选择。
3. **禁止在任何比较里固定 alpha。** 表征之间、预处理之间的比较,alpha 必须在训练集内独立选;
   `models/alpha_sweep.py` 是本仓的参照实现。`train_ladder.py:19-22` 注释里的 AAV 数字(raw 0.47 →
   标准化 0.60)是 AAV 专属,不得当通用结论引用。

## 影响

- 范围限制:本裁定的实测只覆盖 Ridge 一级,xgboost/mlp 两级未做 alpha 扫描,不得外推。
- 派生工作:把 ESM-2 与 alpha 选择接入 `pool_campaign`,并重跑受影响的 campaign 版本;
  未接入前,所有 campaign 结果应标注「one-hot + 固定 alpha=1」这一口径。
- 报告口径:表征章节应呈现 alpha 扫描表,而不是固定 alpha 的单点比较。
