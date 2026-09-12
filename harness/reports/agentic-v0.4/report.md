# 中期报告 04(实验三):上位感知 surrogate 破 7.53 —— 换对表征,天花板就塌了

> 一句话:v0.3 证明 7.53 天花板是"加性 surrogate 表达力上限"(真峰因正上位对加性/自然度双重隐形)。实验三换上**上位感知(pairwise 交互,Potts 式)surrogate**——同池、同 288 预算、同门禁、同 seed,唯一变量是 surrogate——**确定性 gated-greedy 直达真峰 8.416,LLM agentic 达 7.829,双双突破 greedy/v0.2 的 7.53**。全程 answer-agnostic:surrogate 只学已测标签 + one-hot 特征 + CV 选 alpha,从不看测试峰。

承接 [v0.3](../agentic-v0.3/report.md)(诊断:7.53 是表征×代理天花板)。本报告是**破顶报告**:v0.3 指出瓶颈是加性表达力,研究([plateau-breaking-methods.md](../../context/research/plateau-breaking-methods.md))指向"显式建模上位效应",实验三落地并验证。

---

## 1. 一刀:把加性 surrogate 换成上位感知

- 假设(v0.3 / F-851790B5):cold-start(HD≤2,10433)本就含单/双突变实测,S17E×V18A 上位、D0Q 有益单点都在数据里,**只是加性 Ridge/kNN 表达不了位点×位点交互**。
- 做法:`EpistasisRidgePredictor` = one-hot 的 **degree-2 interaction 特征(Potts 式)** + Ridge(alpha 由 CV 在训练集自选,answer-agnostic;稀疏实现,fit ~6s)。mean 用全数据拟合、方差用小 bootstrap 供 UCB。
- **诊断(确定性,单发静态)**:pairwise 把真峰门内预测排名从**加性 #2776 → #447**(6 倍),CV Spearman **0.64 → 0.90**。峰进射程,单发差一点过 288 线,交给闭环主动学习。

## 2. 结果:六方同预算(288)、同池、同 oracle、seed 42

| 方法 | cum_top10_max | strong 命中 | 一句话 |
|---|---|---|---|
| agentic v0.1(自由) | 5.96 | 15 | 探索有毒 |
| workflow greedy | 7.53 | 85 | 固定流到顶 |
| agentic v0.2(门禁,LLM) | 7.53 | 93 | 决策到顶 |
| v0.3 加性诊断(最好 esm2×knn) | 峰 #1283 不可达 | — | 表征×代理天花板 |
| **v0.4 上位 surrogate(LLM agentic)** | **7.829** | 108 | **破 7.53** |
| **v0.4 上位 surrogate(确定性 gated-greedy)** | **8.416 = 真峰** | 151 | **直达全局峰** |

- **LLM v0.4** 曲线 [7.39, 7.39, 7.39, **7.83**, 7.83, 7.83]:round4 起破 7.53(上位 surrogate 学够 doubles 后把峰重排进射程);最佳变体 `DEQEIATTNPVATEQYGEVSDNLQRGNR`(HD4);门禁拒 0(list_pool 全给门内);事件链 50 事件校验通过。
- **确定性 v0.4** 直接测到真峰 `QEEEIRTTNPVATEQYGEASTNLQRGNR`(8.416,HD3),strong 151。

## 3. 两个诚实结论

1. **7.53 天花板 = 加性表达力上限,被证实并被打破。** 唯一变量是 surrogate 从加性→上位感知,cum_top10_max 从 7.53 跳到 7.83(LLM)/ 8.42(确定性)。这是整条线第一次真正破顶,机制清楚:上位 surrogate 从已测 doubles 学到 S17E×V18A 的正上位并外推到 HD3 峰。
2. **surrogate 是关键杠杆,自主性此步无额外加成(甚至略拖后腿)。** 确定性 gated-greedy(8.416)> LLM agentic(7.829)——纯贪心在上位 surrogate 上把预算全押在 top 预测、直达真峰;LLM 的探索/利用混合分散了预算、止于第 2 峰。诚实记录:破顶来自表征,不来自 agent 的自主决策。

## 4. answer-agnostic 纪律(为什么这不是刷分)

- surrogate 特征 = one-hot(位点×残基),训练标签只用已测(cold-start + 逐轮所测),**从不使用测试峰成分**;alpha 由 CV(held-out 预测精度)选,**不按目标峰排名调参**(v0.3 明确排除了 alpha=1 凑可达的做法)。
- 这正是"科学家在牢笼里用合法工具破局":显式建模上位效应(EVmutation/ECNet/MULTI-evolve 一族的核心思想),而非上帝视角喂答案。破顶是"换了一个更有表达力、且科学上正确的模型"的自然结果。

## 5. 复现

```
# 诊断(确定性,便宜)
PYTHONPATH=. .venv/bin/python -m analysis.epistasis_surrogate_scan
# 确定性 gated-greedy + 上位 surrogate(直达真峰 8.416)
PYTHONPATH=. .venv/bin/python -m agent.auto_researcher --dataset aav --feature one_hot \
  --guardrail --surrogate epistasis --budget 48 --n-rounds 6 --seed 42 --no-llm
# LLM agentic + 上位 surrogate(7.829)
PYTHONPATH=. .venv/bin/python -m agent.auto_researcher --dataset aav --feature one_hot \
  --guardrail --surrogate epistasis --budget 48 --n-rounds 6 --seed 42 --model gpt-5.6-sol
```

- 产物:`agentic-v0.4/aav/agentic.metrics.json`(LLM,链校验)、`deterministic.metrics.json`(确定性)、`epistasis_surrogate_scan.json`(诊断)、figures/。
- 代码:`models/train_ladder.py` 的 `EpistasisRidgePredictor`;`agent/auto_researcher.py --surrogate`;单测 `tests/test_epistasis_surrogate.py`(XOR 纯上位:加性必失/pairwise 抓)。
- 台账:fact F-851790B5(假设)、F-C08A6CF2(诊断 #2776→#447)、F-8A58F305(破顶 7.829/8.416)。

## 6. 结论

实验一→四完成一条诚实的科学弧:**自由探索有毒(v0.1)→ 知识门禁治决策(v0.2)→ 诊断出天花板是加性表达力+反自然的双重隐形(v0.3)→ 换上位感知表征,破顶直达真峰(v0.4)**。核心科学结论:在有正上位的蛋白地形上,**表征的表达力(能否建模交互)是能否够到全局峰的决定性杠杆**,远比 agent 的决策自主性重要。下一步可选:让 LLM agent 学会更好地利用上位 surrogate(缩小与确定性贪心 8.416 的差距),或把该 surrogate 推广到 GB1/avGFP 验证普适性。
