# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-C08A6CF2

- Statement: 实验三提名B诊断(epistasis_surrogate_scan.py):上位感知 pairwise 交互 surrogate(one-hot degree-2 interaction + Ridge,157080特征)相比加性 Ridge,把AAV真峰8.416门内预测排名从 #2776 拉到 #429(alpha=10)。CV(3折,answer-agnostic选alpha):alpha=1 CV-Spearman0.851→峰#238(可达≤288);alpha=10 →0.884→#429;alpha=100(CV最优)→0.898→#447(>288)。CV最优alpha给#447仍差一点单发可达,但相比加性#2776是6倍提升、CV-Spearman 0.64→0.90。结论:天花板成因=加性surrogate表达力上限(证实F-851790B5假设);上位感知表征把真峰拉到striking distance,单发静态未过288线,需闭环主动学习(逐轮重排)验证能否实际破7.53。不按峰排名挑alpha(answer-agnostic)。
- Evidence source: lab/reports/agentic-v0.4/aav/epistasis_surrogate_scan.json
- Observed at: 2026-09-12T01:42:43.760Z
- Confidence: high
- State: standing

