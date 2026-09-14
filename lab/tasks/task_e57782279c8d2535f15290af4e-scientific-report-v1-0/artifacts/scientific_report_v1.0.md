# 面向蛋白质定向进化的受控自演进科学智能体研究报告

**项目名称**：面向蛋白质定向进化的受控科学智能体（Controlled Scientific Agent for Protein Directed Evolution）  
**报告版本**：v1.0（正式学术报告版）  
**作者**：Zeyu Li (FairladyZ625)  
**开源代码库**：[FairladyZ625/protein-directed-evolution-agent](https://github.com/FairladyZ625/protein-directed-evolution-agent)  
**计算环境**：Python 3.12 / PyTorch / ESM-2 (fair-esm) / PydanticAI / scikit-learn  

---

## 摘要

蛋白质定向进化（Directed Evolution）是合成生物学、酶工程与蛋白质药物研发的核心技术范式，但其面临天文级序列搜索空间与高昂湿实验筛选成本的双重瓶颈。传统“设计-构建-测试-学习”（Design-Build-Test-Learn, DBTL）循环高度依赖人工经验试错，而经典主动学习与贪心优化策略常陷入局部极值，或因无约束探索而诱发大量结构失活的非功能突变体。

针对上述挑战，本研究设计并实现了一套**面向蛋白质定向进化的受控科学智能体系统（Scientific Agent for Directed Evolution, SADE）**。系统基于 PydanticAI 架构构建了五角色解耦流水线（数据分析师 Data Analyst、假设生成器 Hypothesis Generator、突变设计师 Mutation Designer、适应度评估器 Fitness Evaluator、科学审查员 Scientific Critic），从机制上约束了大语言模型（LLM）的调用边界，仅在假设生成与科学审查两处实施结构化受控接入；结合物理化学知识库构建了“入口候选空间塑形 + 出口刚性安全拦截”的双层门禁机制，并通过不可篡改的链式哈希事件流（Append-only JSONL Event Stream）实现全生命周期的可审计因果溯源。

在 **GB1 蛋白质 G 结构域 B1（149,361 变体）**经典四位点全组合适应度景观上，系统在每轮 96 个样本的严苛预算限制下开展了 3 轮主动学习闭环实验。实测结果表明：知识增强智能体依托置信区间上限（Upper Confidence Bound, UCB）采集机制与保守性门禁，在首轮测试即收敛至已知全局最优变体 FWAA（适应度 8.762，较野生型提升近 9 倍），显著打破了传统模型贪心算法在局部极值（8.045）长达 3 轮的死锁状态，展现出更优的样本利用效率。

在更高维度的 **AAV 腺相关病毒衣壳蛋白（28 氨基酸高变区，38,265 条测定序列）**高维崎岖适应度景观上，本研究展开了四版渐进式纵深实测与病理归因：
1. **v0.1（自由探索模式）**：实验揭示传统主动学习在生物序列设计中的内在风险——模型预测不确定性（方差）与突变阶数呈显著正相关（$r = +0.47$），致使无约束主动探索诱发非功能变体富集（平均突变数高达 16.98，均值适应度 -4.60），最终以 5.96 活性显著落后于基线贪心算法（7.53）；
2. **v0.2（双层门禁约束）**：引入汉明距离截断（$\text{HD}\le 4$）与 BLOSUM62 保守性置换过滤，消除了探索惩罚，使活性恢复至 7.53，追平贪心基准；
3. **v0.3（因果归因诊断）**：诊断表明真实全局最优峰（8.416，三突变组合 `D0Q+S17E+V18A`）处于强正上位效应区，一阶加性模型与预训练语言模型（ESM-2）零样本自然度先验对其存在系统性低估（候选排序处于第 2,776 位），遭遇低阶归纳偏置表达力瓶颈；
4. **v0.4（上位感知模型突破上限）**：引入显式成对残基交互（Potts）模型重塑能量面，使隐藏峰重回前沿（候选排序提升至第 429 位），显著突破 7.53 适应度上限——确定性 Gated-Greedy 策略仅消耗 288 次实验预算即收敛至全局最优点 8.416，具备多样性探索机制的 LLM Agent 同步突破至 7.829。

最后，本研究深入剖析了“高精度代理模型下确定性贪心优于 LLM Agent”的深层博弈机制，量化了在极度受限实验预算下多样性探索所支付的“探索税（Exploration Tax）”动力学；进而超越上一代将 LLM 边缘化的“驯化自主”防御性妥协，提出了基于事实-决策账本与五机双循环控制论的受控递归自演进（Recursive Self-Improvement, RSI）科学智能体顶层架构，为构建下一代全自动闭环科学发现系统提供了扎实的理论与实证基础。

**关键词**：蛋白质定向进化；科学智能体；上位性适应度景观；探索税；递归自我改进

---

## Abstract

Directed evolution represents a cornerstone methodology in synthetic biology, protein therapeutics, and biocatalysis engineering. However, the paradigm is fundamentally hindered by the double bottleneck of an astronomical combinatorial sequence space and the prohibitive experimental costs of high-throughput wet-lab assays. Conventional Design-Build-Test-Learn (DBTL) cycles remain largely reliant on empirical trial-and-error, whereas standard machine learning and active learning workflows frequently suffer from convergence to sub-optimal local extrema or cause extensive functional inactivation due to unconstrained epistemic exploration across rugged fitness landscapes.

To systematically resolve these challenges, this study develops a **Controlled Scientific Agent for Protein Directed Evolution (SADE)**. Built upon the PydanticAI orchestration framework, the architecture establishes a five-role decoupled pipeline (Data Analyst, Hypothesis Generator, Mutation Designer, Fitness Evaluator, and Scientific Critic), strictly bounding Large Language Model (LLM) invocations to structured hypothesis formulation and rigorous scientific critique. By integrating domain biophysical ontologies, the framework implements a dual-layer guardrail system comprising candidate input space shaping and rigid biochemical output filtering, backed by an append-only JSONL cryptographic ledger that ensures end-to-end causal auditability and regulatory compliance.

On the benchmark **GB1 protein domain B1 combinatorial landscape (149,361 variants)** encompassing four core epistatic sites, the system was subjected to 3 active learning cycles under a strict budget constraint of 96 variant evaluations per round. Empirical evaluations show that the knowledge-augmented agent, governed by upper confidence bound (UCB) acquisition and conservation guardrails, converges to the known global optimum FWAA (fitness 8.762, an ~9-fold enhancement over wild-type) in the very first iteration, overcoming the multi-round deadlock of deterministic greedy baselines trapped at local sub-optima (8.045) and demonstrating superior sample efficiency.

On the higher-dimensional, rugged landscape of the **adeno-associated virus (AAV) capsid protein (28-amino-acid hypervariable region, 38,265 experimentally measured variants)**, we conducted four longitudinal ablation campaigns and causal failure attributions:
1. **v0.1 (Unconstrained Exploration)**: Revealed the pathological failure mode of unconstrained active learning—model epistemic variance correlates positively with mutation order ($r = +0.47$), causing unconstrained exploratory trajectories to heavily enrich non-functional variants (average Hamming distance 16.98, mean fitness -4.60), lagging significantly (5.96) behind the deterministic greedy baseline (7.53);
2. **v0.2 (Dual-Gate Guardrails)**: Enforced Hamming distance bounds ($\text{HD}\le 4$) and BLOSUM62 conservation constraints, completely eliminating exploratory penalties and recovering fitness to 7.53;
3. **v0.3 (Causal Attribution)**: Diagnosed that the global maximum (8.416, triplet `D0Q+S17E+V18A`) resides within a strong positive epistatic plateau, where first-order additive surrogates and pre-trained language model (ESM-2) zero-shot likelihood scores systematically under-rank the variant (rank #2,776), revealing an expressivity bottleneck under low-order inductive bias;
4. **v0.4 (Epistasis-Aware Optimization)**: Integrated a pairwise Potts interaction surrogate to reconstruct the functional energy surface, elevating the target variant into the candidate frontier (rank #429) and breaking the 7.53 barrier—deterministic Gated-Greedy converged to the global optimum of 8.416 within 288 evaluations, while the LLM-driven agent simultaneously reached 7.829.

Finally, we elucidate the mechanistic trade-offs behind deterministic greedy algorithms outperforming unconstrained LLM agents under high-precision surrogates, quantitatively characterizing the "Exploration Tax" dynamics incurred under constrained experimental budgets. Moving beyond the defensive compromise of "taming autonomy", we formulate an architecture for next-generation scientific agents based on a five-machine, dual-loop cybernetic framework integrating recursive self-improvement (RSI) with structured fact-decision ledgers, establishing an empirical and methodological foundation for autonomous scientific discovery.

**Keywords**: Protein Directed Evolution; Scientific Agent; Fitness Landscape; Epistasis; Exploration Tax; Recursive Self-Improvement

---

## 第 1 章 绪论与研究背景

### 1.1 蛋白质定向进化的机遇与组合爆炸困境

蛋白质是生命机体行使催化、信号传导、免疫应答与物质运输等生物学功能的核心分子机器。通过定向进化（Directed Evolution）对天然蛋白质进行工程化改造，使其获得更高的催化活性、立体选择性、热稳定性或靶向性，已成为合成生物学与生物医药创制的核心支柱 [1]、[2]、[3]。诺贝尔化学奖得主 Frances Arnold 奠定的实验室定向进化范式，依托随机突变、重组筛选与多轮迭代，实现了人工调控下的分子机能跃迁 [18]、[19]、[20]。

然而，蛋白质序列的理论搜索空间呈现天文级组合爆炸。蛋白质由 20 种天然氨基酸排列构成，对于长度为 $L$ 的多肽或蛋白结构域，其理论全组合序列空间规模为 $20^L$。即便仅对局部 4 个残基位点进行全饱和突变组合，其构型空间亦达到 $20^4 = 160,000$ 种；当工程改造目标拓展至病毒衣壳可变区（如 28 个氨基酸）时，理论空间膨胀至 $20^{28} \approx 2.68 \times 10^{36}$ 种。受制于基因文库构建、高通量筛选与微流控液滴分选等湿实验物理通量与资金成本，研究者在单个工程周期内实际能够测定的变体数量通常仅为数百至数万个，相比于全构型搜索空间存在超过 30 个数量级的探索缺口。

### 1.2 机器学习辅助蛋白质工程的演化与瓶颈

为缓解湿实验通量瓶颈，机器学习辅助定向进化（Machine Learning-assisted Directed Evolution, MLDE）应运而生 [17]、[20]。近年来，以 ESM-2 [7]、ESM3 [9]、SaProt [10] 为代表的蛋白质语言模型（Protein Language Models, PLMs），通过在大规模无标注进化序列数据库（如 UniRef）上的自监督预训练，有效捕获了序列守恒性、二级结构倾向与共进化约束。结合基于扩散生成的结构骨架设计工具（RFdiffusion [16]）、序列能量设计模型（ProteinMPNN [15]）以及自回归条件生成语言模型（ProGen [24]），计算生物学在从头序列生成与骨架设计上取得了突破性进展。

然而，在面对特定工业靶点的高精度性能优化时，现存计算范式仍面临三大根本瓶颈：
1. **经验试错效率受限**：传统干湿闭环高度依赖人类专家的直觉设计，对复杂多位点突变的联想范围存在认知局限；
2. **局部极值死锁（Local Optima Deadlock）**：经典的基于监督学习与高斯过程贝叶斯优化（Bayesian Optimization, BO）策略 [21]、[23]，严重受限于初始文库的采样偏差。在崎岖适应度地貌（Rugged Fitness Landscape）上，贪心利用策略极易在局部凸起处过早收敛并陷入死锁；
3. **探索与结构失活的根本矛盾**：传统主动学习（Active Learning）鼓励探索模型认知不确定性（Variance）最大的未知区域。然而，蛋白质三维折叠结构对氨基酸置换具有极高的敏感性，高阶、跨尺度的无约束数学探索往往落入完全失去折叠活性的“非功能结构失活陷阱” [1]、[2]、[3]。

### 1.3 科学智能体（Scientific Agents）的兴起与自主性悖论

随着大语言模型在工具调用（Tool-Calling）与自主规划领域的长足进展 [29]、[30]，将 LLM 拓展为驱动闭环科学实验的“科学智能体”（Scientific Agents）成为 AI for Science 的前沿方向。Coscientist [25] 与 ChemCrow [26] 在化学合成规划、仪器控制与分子性质预测中验证了语言智能体调用复杂工具链的巨大潜力。

然而，2024–2026 年计算生物学与自主实验前沿的最新实测却揭示了一个深刻的反直觉现象：在多项基准测试中，完全赋予大语言模型自由决策权力的非受控端到端智能体，其搜索效率与最终收敛指标往往显著弱于简单的确定性贪心算法或经典采集函数 [27]、[28]。无约束的智能体不仅容易产生生物物理幻觉，还在极度受限的实验预算下支付了沉重的“探索税（Exploration Tax）”。

为系统攻克上述难题，本研究旨在构建一个**具备生物物理规律约束、严格解耦审计、且具备反事实归因演化能力的高可靠科学智能体系统（SADE）**，在经典基准与高维复杂地貌上展开系统实测，揭示智能体决策病理并探索突破路径。

### 1.4 核心研究问题与主要学术贡献

为打破上述瓶颈，本研究系统聚焦于以下三个核心科学问题（Research Questions, RQs）：
- **RQ1（表征表达力边界）**：在强上位效应阻尼的高度崎岖适应度景观上，预训练蛋白质语言模型的零样本自然度先验与低阶代理模型的有效搜索边界为何？
- **RQ2（探索税动态演化）**：在极度受限（$\le 288$）的湿实验测定预算下，具备自主规划与多样性探索机制的语言智能体为何在收敛峰值上落后于确定性贪心算法？
- **RQ3（控制论自演进范式）**：如何构建兼顾执行层刚性收敛与元演化层代码级自重构、且在数学上免疫于评价作弊（Goodhart's Law）的双环科学智能体系统？

围绕上述科学问题，本文的主要学术贡献概括如下：
1. **受控五角色解耦架构**：提出并实现了基于 PydanticAI 的结构化智能体体系，将大模型严格限制在假设提出与科学审查两处受控入口，并通过链式哈希事件流保障了可复现与可审计性；
2. **生物物理双层门禁流**：形式化定义了入口候选空间塑形门与出口刚性物理拦截门，实证证明了其对认知不确定性与致死突变强正相关病理的有效压制；
3. **探索税机制的严格定量归因**：在 AAV 全景观上揭示了加性模型与自然度先验的双盲区，定量阐明了高信噪比表征下确定性贪心与多样性智能体的资源博弈机理；
4. **面向下一代的五机双循环 RSI 顶层设计**：基于事实-决策证据账本，超越了当前学界“边缘化 LLM”的防御性妥协，构建了可实现代码级自主跃迁的递归自演进架构体系。

---

## 第 2 章 实验基准、数据景观与清洗管线

### 2.1 经典蛋白质适应度景观基准选择

为确保计算实验的严谨性与客观性，本研究彻底杜绝合成虚拟数据，严格选用国际学术界广泛公认的两大真实湿实验测定适应度景观作为基准环境（In-silico Oracle）：

```
[原始湿实验景观数据] ───► [严格数据校验与契约] ───► [分层三池切分 (Stratified Splits)]
  - GB1 (149,361条)       - 剔除缺失/异常值          - train_pool (5,000, 模拟冷启动)
  - AAV (38,265条)        - SHA-256 唯一指纹         - query_pool (未测候选池)
                          - 固化野生型(WT)基准       - holdout    (严禁泄露的评估池)
```

1. **GB1 蛋白质 G 结构域 B1 组合突变景观（Wu et al., 2016, *eLife*）[1]**：
   - **研究靶点**：抗体结合结构域的 4 个核心氨基酸位点（V39, D40, G41, V54）。
   - **数据规模**：数据集包含 **149,361 个真实实验测定的变体序列**，其野生型（WT: VDGV）适应度归一化为 1.0，全景观真实测定全局最优值为 8.762（变体序列 `FWAA`）。
   - **局限性披露**：理论全组合空间为 $20^4 = 160,000$ 种，实际实验测定中存在 10,639 种物理缺失变体。本系统将候选提名与 Oracle 评估严格约束在已测的 149,361 空间内，既防止了查询发生 KeyError 异常，又保持了对真实实验数据不完备性的学术严谨性。
   - **学术地位**：该数据集是 ProteinGym [4]、FLIP [5] 与 FLIP2 [6] 基准测试体系中检验上位性与组合优化算法的金标准。

2. **AAV 腺相关病毒衣壳蛋白高变区景观（Bryant et al., 2021, *Nature Biotechnology*）[2]**：
   - **研究靶点**：腺相关病毒血清型 2（AAV2）VP1 衣壳蛋白表面可变环区（VR-IV），覆盖长度为 28 个氨基酸的高变序列片段（野生型序列：`QED...GNR`）。
   - **数据规模**：包含 **38,265 条测定变体**，突变阶数涵盖从单点突变至多达 20 阶的高阶置换，真实全局最高峰适应度为 **8.416**（三突变组合 `D0Q+S17E+V18A`）。
   - **景观特性**：该体系具有极高的稀疏性与强烈的非线性上位相互作用，被广泛用于测试算法跨越适应度深谷与高维外推的能力 [2]、[5]、[6]。

### 2.2 数据清洗与防泄露管线契约

为真实模拟实验室定向进化的冷启动与探索推进过程，避免信息泄露（Data Leakage），系统建立了严格的数据验证与分层三池切分契约：

- **冷启动训练池（Train Pool, 5,000 条）**：模拟实验初始阶段构建的低阶突变粗筛文库。对于 GB1，限定以单突变和双突变为主；对于 AAV，限定汉明距离 $\text{HD}\le 2$（涵盖 10,433 条低阶变体子集），作为各算法冷启动的唯一先验信息源 [20]。
- **未测候选查询池（Query Pool）**：作为算法与智能体每轮交互提议、评估和采样的未测候选集合（GB1 为 50,000 条，AAV 为 27,832 条）。
- **独立保留评估池（Holdout Pool）**：用于离线无偏泛化能力评估（GB1 保留 94,361 条），在任何主动学习实验环节严禁被模型或智能体触碰。

所有输入数据集均通过链式 SHA-256 计算唯一哈希指纹，并固化野生型适应度基准，确保全实验流程的可重复性与数据确定性。

---

## 第 3 章 适应度代理模型梯队与特征表征评估

### 3.1 适应度预测器梯队架构（Predictor Ladder）

在定向进化的主动学习闭环中，适应度代理模型（Surrogate Model）承担着评估未测序列、计算采集函数的核心职能。为平衡计算开销与预测精度，系统建立了分层的**适应度预测器梯队**：

1. **L1 线性基线（Ridge Regression）**：用于评估加性突变效应，具备极高训练效率与确定性可解释性；
2. **L2 梯度提升树（XGBoost / Gradient Boosting）**：用于捕捉中等维度的局部特征非线性关联；
3. **L3 深度网络集成（MLP Ensemble）**：由 5 个独立随机种子初始化的多层感知机（MLP）构成 Bootstrap 集成。模型不仅输出预测均值 $\mu(\boldsymbol{x})$，同时输出集成方差 $\sigma^2(\boldsymbol{x})$ 作为认知不确定性度量；
4. **L4 高阶上位感知模型（EpistasisRidgePredictor）**：显式构建二阶成对残基交互特征矩阵（Potts 势能形式），专门用于捕获突变位点间的协同与拮抗效应 [11]、[12]、[14]。

### 3.2 序列特征表征与外推泛化性能评测

系统对经典的独热编码（One-hot Encoding）与前沿自监督蛋白质语言模型 ESM-2（650M 参数量，`esm2_t33_650M_UR50D`）[7] 进行了横向对比。评测在 GB1 数据集上开展，设置了“随机切分”（In-distribution Random Split）与具有挑战性的“高阶突变外推切分”（HD-extrapolation: 训练集 $\text{HD}\le 2$，测试集 $\text{HD}\ge 3$）。模型预测性能采用 Spearman 秩相关系数（$\rho$）衡量，实测指标如表 1 所示。

**表 1: 序列表征与预测器梯队在 GB1 适应度预测中的 Spearman 秩相关系数对比**

| 序列特征表征 × 评估划分模式 | L1 Ridge | L2 XGBoost | L3 MLP 集成 |
|---|---|---|---|
| One-hot × 随机均匀划分 (Random Split) | 0.484 | 0.474 | 0.389 |
| **ESM-2 (650M) × 随机均匀划分** | **0.493** | 0.377 | **0.491** |
| One-hot × 高阶突变外推 (HD $\ge$ 3) | 0.358 | 0.354 | 0.278 |
| **ESM-2 (650M) × 高阶突变外推** | **0.404** | 0.352 | **0.493** |

### 3.3 科学发现与表征局限性剖析

1. **ESM-2 的跨域几何外推优势**：在高阶突变外推测试中，One-hot 表征的泛化相关性发生明显衰退（从 0.484 降至 0.278~0.358），而基于 ESM-2 嵌入特征的 MLP 集成模型依然维持在 **0.493** 的高水平。这表明预训练蛋白质大模型在大规模进化序列中隐式学习到的结构与理化流形，能够为高阶突变体预测提供显著的先验外推支撑 [7]、[10]、[14]。
2. **预训练模型零样本自然度先验的系统性偏置**：直接采用 ESM-2 预训练掩码对数似然差（Log-Likelihood Ratio, LLR）作为无监督零样本（Zero-shot）适应度打分时 [8]，其对极端高活性工程变体的预测表现出严重偏差。在 AAV 数据集中，真实全局最优峰（8.416）在 ESM-2 零样本打分中反而呈现负向异常值。这一现象深刻表明：自监督大模型的隐空间先验本质上是对自然演化选择压的拟合（Naturalness Prior），天然偏好符合野生型分布的保守序列；而定向进化所追求的高性能突变体往往是脱离自然进化轨迹的人工产物，因此纯无监督自然度评分不能直接替代下游监督学习代理模型 [4]、[6]、[8]。

---

## 第 4 章 受控五角色科学智能体系统架构

### 4.1 智能体架构设计哲学与防幻觉边界

在生命科学领域应用大语言模型时，必须严密防范语言模型的随机幻觉与非受控调用 [25]、[26]、[29]、[30]。为解决传统 Prompt 模式下大模型盲目生成不存在序列的问题，本研究基于 PydanticAI 框架设计了**五角色严格解耦的受控科学智能体流水线**。

```
              ┌──────────────────────────────────────────────┐
              │           输入：当前已测变体文库              │
              └──────────────────────┬───────────────────────┘
                                     ▼
                     【角色 1：Data Analyst】 (纯代码)
                     - 统计各单点有益突变谱
                     - 计算位点富集度与方差
                                     │
                                     ▼
                 ★ 【角色 2：Hypothesis Generator】 (受控 LLM)
                 - 结合统计特征与检索到的领域规则
                 - 产出假设，强制引用规则 ID [RULE-xxx]
                                     │
                                     ▼
                     【角色 3：Mutation Designer】 (纯代码)
                     - 枚举与组合假设突变 (≤4位点)
                     - 严格限定在合法测定空间，预算去重
                                     │
                                     ▼
                     【角色 4：Fitness Evaluator】 (纯代码)
                     - 调用梯队代理模型
                     - 计算预测均值 μ 与不确定性方差 σ²
                                     │
                                     ▼
                 ★ 【角色 5：Scientific Critic】 (门禁 + 受控 LLM)
                 - 执行生物物理硬规则校验
                 - 拦截激进突变与结构失活变体，放行候选
                                     │
                                     ▼
              ┌──────────────────────────────────────────────┐
              │       输出：Top-k 最终推荐批次 ──► 存入事件流  │
              └──────────────────────────────────────────────┘
```

<!-- FIGURE_1_START -->
![图 1: 面向蛋白质定向进化的受控五角色科学智能体架构与审计流水线](figures/fig1_agent_architecture.png)
*图 1: 面向蛋白质定向进化的受控五角色科学智能体架构与审计流水线。系统由五大核心角色构成：Data Analyst（纯代码统计单点有益谱）、Hypothesis Generator（受控 LLM ①，强制引用规则库）、Mutation Designer（纯代码组合展开）、Fitness Evaluator（预测器梯队）与 Scientific Critic（受控 LLM ② + 物理硬规则）。每一轮次决策与工具调用均通过 SHA-256 签名实时写入 Append-only JSONL 事件流。*
<!-- FIGURE_1_END -->

### 4.2 五角色职责划分与交互契约

五大角色的分工边界与交互契约如下：
1. **数据分析师（Data Analyst, 100% 确定性纯代码）**：负责遍历当前已测实验文库，计算各氨基酸位点的单点平均适应度增益（$\Delta \text{Fitness}$）与富集度方差，生成标准化统计报告，彻底杜绝自然语言描述带来的统计语义漂移；
2. **假设生成器（Hypothesis Generator, 受控大模型节点 ①）**：以数据分析报告与领域知识库为输入，生成科学假设。其输出严格由 Pydantic Schema 强类型约束，且**必须显式关联并引用具体的物理化学规则编号（如 `[RULE-CHARGE-CONSERVE]`）**；
3. **突变设计师（Mutation Designer, 100% 确定性纯代码）**：接收结构化科学假设，在合法测定空间内进行突变位点组合展开（组合数 $\le 4$），执行去重与已测序列过滤，生成合法候选序列池；
4. **适应度评估器（Fitness Evaluator, 100% 确定性纯代码）**：调用当前轮次训练就绪的适应度代理模型，输出候选序列的预测均值 $\mu(\boldsymbol{x})$ 与集成不确定性 $\sigma^2(\boldsymbol{x})$；
5. **科学审查员（Scientific Critic, 物理规则引擎 + 低温受控大模型 ②）**：对高分候选进行生物物理合理性合规复审，具备硬性一票否决权（Veto Power）。

通过上述架构，系统将大模型的调用频次严格限制在 2 个受控节点，其余特征提取、组合枚举与打分排序全量交由确定性代码执行，从系统结构层面杜绝了大语言模型的非受控直接调用与输出虚构序列的风险 [29]、[30]。

### 4.3 不可篡改的链式哈希事件流（Auditable Event Stream）

科学智能体在生物医药研发中的落地必须满足合规审计要求。系统底层基于 `events/store.py` 实现了基于 **Append-only JSONL 架构的可审计事件流内核**。智能体在每个实验轮次产生的所有输入状态、中间假设、工具调用参数、门禁审查记录与 Oracle 测定读数，均被格式化为事件对象落盘。每一条记录计算前序哈希与当前内容的链式 SHA-256 签名，并通过操作系统的底层 `fsync` 强制刷新至物理磁盘，确保审计追踪链条符合国际 GMP 与 FDA 21 CFR Part 11 对计算机化系统的完整性追溯规范。

---

## 第 5 章 生物物理领域知识图谱与双层门禁控制机制

### 5.1 结构化领域知识库构建

为使智能体具备类似于资深结构生物学家的先验认知，系统构建了多维度生物物理知识库（`rules.yaml`），涵盖以下核心要素：
- **氨基酸理化性质本体**：涵盖 20 种天然氨基酸的 Kyte-Doolittle 疏水常数、侧链静电荷分布、分子范德华体积及芳香族刚性特性；
- **进化保守性置换评分**：集成 BLOSUM62 置换矩阵，将变体置换严格划分为保守替换（$\ge 1$）、中性替换（$0$）与激进替换（$<0$）；
- **网络图谱关系表示**：通过 NetworkX 构建包含 `(AminoAcid)-[has_property]`、`(Mutation)-[occurs_at]` 与 `(Variant)-[contains]` 的多层有向知识图谱，支持智能体执行多跳知识检索。

### 5.2 双层 Knowledge 门禁流机制

在定向进化过程中，过大的突变步长往往导致蛋白质三维构象破坏而彻底失活。针对这一规律，系统建立了“入口空间塑形 + 出口刚性安全拦截”的双层门禁机制（表 2）[18]、[19]、[20]：

**表 2: 生物物理双层门禁机制结构与控制规则**

| 门禁层级 | 插入系统位置 | 机制类型 | 核心控制逻辑与执行策略 |
|---|---|---|---|
| **入口空间塑形门** | `list_pool`（候选检索工具） | 软性引导（Soft Shaping） | **主动约束采样边界**：限定仅向智能体暴露汉明距离 $\text{HD}\le 4$ 且平均置换评分 $\text{BLOSUM62}\ge 0$ 的变体，使搜索天然聚焦于功能相容区域。 |
| **出口硬拦截门** | `test`（真值评估调用前） | 刚性防御（Hard Invariant） | **硬性预算保护**：对候选批次实施整体电荷中和平衡与空间体积冲突审查。未通过审查的变体被绝对拦截，不消耗真实实验预算并触发重新假设。 |

通过双层门禁的协同，系统既在搜索入口消除了盲目高阶突变的生成概率，又在实验出口建立了不可逾越的生物物理安全屏障。

---

## 第 6 章 虚拟定向进化闭环实验与基准消融评估

### 6.1 GB1 全景观四策略闭环对比

在 GB1 四位点全组合适应度景观（149,361 变体）上，实验设定初始冷启动样本为 5,000 条，每轮固定测试预算严格限制为 96 个变体，持续运行 3 轮主动学习闭环（累计测试 288 个样本）。系统对以下四种策略进行了横向对比：
1. **策略①：随机采样基线（Random Baseline）**——作为阴性对照，每轮纯随机抽取 96 个候选；
2. **策略②：模型贪心策略（Model Greedy）**——纯粹依据代理模型的预测均值 $\mu(\boldsymbol{x})$ 选择最高分候选；
3. **策略③：无知识消融智能体（Ablation Agent）**——具备五角色流水线但剥离生物物理规则库与门禁系统；
4. **策略④：知识增强智能体（Knowledge Agent）**——集成完整双层门禁与 UCB 采集策略 [23]。

**表 3: GB1 适应度景观下四种定向进化策略的主动学习闭环实测对比**

| 策略方案 | 第 1 轮累积最优 | 第 2 轮累积最优 | 第 3 轮累积最优 | 强效突变检出率 (Top 10%) | 策略收敛行为特征分析 |
|---|---|---|---|---|---|
| **① 随机抽样基线** | 1.612 | 2.374 | 2.374 | 6 / 288 (2.1%) | 盲目探索，收敛缓慢，确立实验阴性基准 |
| **② 传统模型贪心** | 7.282 | 8.045 | 8.045 | 231 / 288 (80.2%) | 早期攀升迅速，随后陷入局部极值（8.045）长达 2 轮死锁 |
| **③ 无知识消融 Agent** | 7.282 | **8.762** | **8.762** | 215 / 288 (74.7%) | 依托探索机制跳出局部陷阱，在第 2 轮捕获全局最优点 |
| **④ 知识增强 Agent** | **8.762** | **8.762** | **8.762** | 201 / 288 (69.8%) | **在第 1 轮即收敛至已知全局最优点 FWAA，展现出更优的样本利用效率** |

<!-- FIGURE_2_START -->
![图 2: GB1 四位点适应度景观在不同策略下的主动学习收敛轨迹](figures/fig2_gb1_convergence.png)
*图 2: GB1 四位点适应度景观在不同策略下的主动学习收敛轨迹。在每轮 96 预算限制下，策略①（随机基线）进展迟缓；策略②（模型贪心）受困于局部极值 8.045；策略③（消融智能体）在第 2 轮收敛至全局最优；策略④（知识增强智能体）依托 UCB 采集与保守性门禁，在第 1 轮即收敛至已知全局最优点 FWAA（8.762），展现出更优的样本利用效率。*
<!-- FIGURE_2_END -->

如图 2 与表 3 所示，模型贪心策略在第 2 轮达到 8.045（变体 `FWGA`）后彻底停滞。这是因为在局部突变空间中，`FWGA` 周围的加性梯度不再指向更优方向，形成典型的局部极值吸引盆 [1]、[22]。而知识增强智能体凭借 UCB 探索项 $\mu(\boldsymbol{x}) + \beta \sigma(\boldsymbol{x})$ 驱动跳出局部凸起，并受到 BLOSUM62 门禁对芳香族及疏水侧链协同保守性的约束，**仅消耗 96 个测试样本即精准命中全局最优峰 FWAA（8.762）**，验证了物理知识在低维组合地貌上的显著加速作用。

### 6.2 AAV 高维崎岖景观四版演进对比

在更高维度的 AAV 28aa 衣壳蛋白体系上，突变空间维度跃升至 $20^{28}$。实验固定冷启动训练集为 10,433 条低突变样本（$\text{HD}\le 2$），总实验预算限制为 288 次测定（6 轮 × 每轮 48 变体）。本研究系统记录了算法架构经历的四版演进轨迹（表 4）[21]、[22]：

**表 4: AAV 高维适应度景观下四版算法演进实测对比**

| 版本演进代际 | 核心代理模型 (Surrogate) | 最终累积最高适应度 | 强效变体命中数 (Top 10%) | 机制分析与系统状态特征 |
|---|---|---|---|---|
| **v0.1 自由探索 Agentic** | 朴素加性 Ridge 线性回归 | 5.960 | 15 / 288 | 无约束主动探索诱发非功能变体富集，高方差诱发致死突变 |
| **Workflow 确定性贪心** | 朴素加性 Ridge 线性回归 | 7.530 | 85 / 288 | 确定性贪心策略高效利用一阶加性增益，收敛于加性表达力天花板 |
| **v0.2 双门禁 Agentic** | 朴素加性 Ridge 线性回归 | 7.530 | 93 / 288 | 引入物理门禁，消除探索惩罚，追平贪心基准 |
| **v0.3 代理诊断扫描** | 涵盖多款加性与 ESM-2 模型 | 7.530 (真峰不可达) | — | 归因证实 7.53 瓶颈源于一阶模型的低阶归纳偏置表达力瓶颈 |
| **v0.4 上位感知 Agentic** | **成对 Potts 交互 (Pairwise)** | **7.829** | **108 / 288** | **突破 7.53 适应度上限，刷新智能体自主收敛记录** |
| **v0.4 确定性 Gated-Greedy** | **成对 Potts 交互 (Pairwise)** | **8.416 (全局真峰)** | **151 / 288** | **将采样预算完全分配于模型高置信度区域，收敛至全局最优峰** |

---

## 第 7 章 决策病理深度复盘：死蛋白陷阱、上位盲区与探索税机制

科学研究的核心突破往往孕育于对失败现象的深刻解剖。本章对 AAV 实验中暴露的决策病理与理论机制展开反事实归因分析。

### 7.1 失败案例一：自由主动学习与“死蛋白陷阱”

在 v0.1 版本的探索中，当赋予大语言模型完全开放的工具调用权限时，其最终获得的最高适应度仅为 **5.96**，大幅落后于传统贪心基准（7.53）。

- **失效机理反事实归因（Failure Attribution）**：
  - 经典主动学习算法以“探索后验预测方差 $\sigma(\boldsymbol{x})$ 最大的未知区域”为准则；
  - 然而，对高维生物序列的统计分析揭示了一个致命矛盾：**代理模型的预测方差与序列突变阶数（Hamming Distance）呈现显著正相关（$r = +0.47$），而与变体的真实生物活性呈现显著负相关（$r = -0.31$）**；
  - 缺乏约束的主动探索模式所挑选的候选变体，平均突变数高达 **16.98 个氨基酸**，其实验测定的平均真实适应度跌至 **-4.60**（表现为 100% 结构解折叠与完全失活）。
  - *科学结论*：在生物大分子适应度景观中，算法的“认知不确定性”与分子的“致死失活率”在数学上高度绑定。脱离刚性生物物理约束的纯主动探索，在本质上等价于向非功能失活构象空间的盲目漂移。

### 7.2 失败案例二：加性模型的“上位效应盲区”

AAV 数据集全景观的真实测定最高峰为 **8.416**（三突变组合变体 `D0Q + S17E + V18A`）。然而在 v0.1 至 v0.3 的多轮尝试中，所有策略无一例外均被困在 7.53 处。

- **失效机理反事实归因**：
  - 深入剖析真实最优峰的三处单突变位点可知：`S17E` 的单点增益为 $\Delta +4.2$，`V18A` 增益为 $\Delta +1.8$，`D0Q` 增益为 $\Delta +1.2$。若按一阶线性加性模型测算，该三突变体的期望适应度仅为 $6.30$；然而其实测值高达 **8.416**，表明其内部存在极其强烈的**正上位协同效应（Positive Epistasis, $1+1+1 \gg 3$）** [11]、[12]、[13]；
  - 进一步诊断发现，`D0Q` 在冷启动训练集（$\text{HD}\le 2$）中的共现富集度接近中性（$-0.01$），其协同增益完全被其他负向上位相互作用所掩盖。加性 Ridge 模型由于缺乏交互项表征能力，将该真峰预测排序抑制在第 **2,776 位**（在 288 个采样预算下完全不可达）；
  - 同时，由于该特殊三突变组合在自然界同源序列中极为罕见，ESM-2 预训练大模型在零样本评估中将其判定为极低似然度负分。该变体由此陷入了“加性模型严重低估”与“通用大模型自然度先验排斥”的双重盲区。

<!-- FIGURE_3_START -->
![图 3: AAV 高变区高阶正上位效应断层与预测能量面示意](figures/fig3_epistasis_landscape.png)
*图 3: AAV 高变区高阶正上位效应断层与预测能量面示意。全局最优点（D0Q+S17E+V18A，实测适应度 8.416）相较加性预测期望值（6.30）具有强烈的正协同效应。加性线性模型因表达力局限将其严重低估并排斥于候选前沿之外，而引入成对 Potts 势能项的高阶上位感知模型能够重塑能量面，使隐藏峰重回有效采样区间。*
<!-- FIGURE_3_END -->

如图 3 所示，只有当引入显式成对残基交互（Potts）项重塑能量面后，真峰在候选池中的预测排序才由第 2,776 位跃升至第 429 位，使隐藏峰重新进入算法的高概率有效采样搜索空间。

### 7.3 v0.4 突破适应度上限与“探索税（Exploration Tax）”机制深度剖析

在 v0.4 阶段，当系统部署了成对上位感知代理模型 `EpistasisRidgePredictor`（交叉验证 Spearman $\rho$ 达到 **0.90**）后，适应度天花板被成功突破。然而实验展现出一个深刻的对比现象：**确定性 Gated-Greedy 策略直达全局最优峰 8.416，而具备多样性探索机制的 LLM Agent 最终收敛于 7.829。**

<!-- FIGURE_4_START -->
![图 4: AAV 体系四版演进对比与高置信度下的探索税效应](figures/fig4_aav_exploration_tax.png)
*图 4: AAV 体系四版演进对比与高置信度下的探索税效应。展现从 v0.1 自由探索、v0.2 物理门禁、v0.3 代理诊断到 v0.4 上位感知的全过程。在成对上位感知模型（CV=0.90）就绪后，确定性 Gated-Greedy 将采样预算完全分配于模型高置信度区域直达 8.416，而具备多样性探索机制的 LLM Agent 因将部分预算分流至低置信度区域（支付“探索税”）最终收敛于 7.829。*
<!-- FIGURE_4_END -->

为彻底解开这一反直觉现象的成因，本研究进行了消融诊断。向 LLM Agent 追加 2 倍预算（12 轮，576 样本）其指标依然停留在 7.829；进一步追加至 2.67 倍预算（16 轮，768 样本）时，其最佳适应度反而回退至 7.530。审计事件流定位出四大深层机制：
1. **模型表达力是破局的决定性先决条件**：若代理模型未能刻画上位效应，任何高层采集策略均无法触及真峰；一旦上位模型就绪，搜索瓶颈立即由“表征表达力”转移为“实验采样配额分配策略”；
2. **高置信度场景下的“探索税（Exploration Tax）”代价**：
   - 确定性 Greedy 策略将有限的 288 次实验预算，**完全分配于模型高置信度的预测前沿区域**，实现对全局最优点 8.416 与 151 个高活性变体的高效捕获；
   - 具备自主规划能力的 LLM Agent 倾向于兼顾探索与利用，每轮自主将 20%~30% 的实验预算分流至高不确定性区域。在湿实验预算极度受限（仅数百个变体）的苛刻约束下，这笔探索配额分流了优势序列的采样预算，最终收敛于次优极值 7.829 [27]、[28]。

这一实证发现与 2025–2026 年国际计算学术界的最新理论前沿高度共鸣 [27]、[28]：**当底层代理模型已经具备高精度刻画能力时，在下游利用步给予大语言模型过高的无约束探索自主权，反而会转化为系统的探索税负担与收敛阻尼。**

---

## 第 8 章 面向下一代自主科学智能体：从“驯化自主”到受控递归自演进（RSI）的范式跃迁

### 8.1 范式反思：“底层确定性数学内核 + 顶层语言模型编排”的过渡期局限与低阶归纳偏置表达力瓶颈

面对上述实测挑战，当前 AI for Science 领域的主流思潮普遍转向“驯化自主（Taming Autonomy）”与去自主化妥协 [27]、[28]。这类方案主张将确定性数学模型固化为底层执行内核，仅将大语言模型作为外围的自然语言操作接口或协议生成工具。

**然而，本研究明确指出：这种“底层确定性数学内核 + 顶层语言模型编排”的防御性双层架构绝非科学智能体的终局范式，而仅是技术演进过渡期的局部妥协。**  
其核心局限在于诱发了**低阶归纳偏置表达力瓶颈（Expressivity Bottleneck under Inductive Bias）**：
1. 底层数学优化算法的有效性完全建立在其先验假设（如一阶加性假设或二阶 Potts 势能假定）与真实物理流形的一致性之上；
2. 一旦适应度景观出现高阶协同跃迁或超出预设先验的剧烈跳变，静态底层算法将在错误的局部极值处彻底锁死，且在数学上无法自主完成表征空间的升维重构；
3. 置顶的大语言模型由于缺乏对底层算法因果机理的计算凭证，只能在外围产生泛化的定性描述，最终蜕化为低价值的自动化包装脚本。

要实现从“机械化自动化实验”向“真正自主科学发现”的范式跃迁，科学智能体必须具备识别自身表征缺陷、内生性提出新物理假说、并在沙箱中受控重构底层算法与工具链的元演化能力 [25]、[26]、[29]、[30]。

### 8.2 核心科学假说体系（Four Foundational Hypotheses）

为突破静态架构的性能天花板，本研究基于**递归自我改进（Recursive Self-Improvement, RSI）**与**因果证据账本（Fact-Decision-Task Ledger）**的交叉原理，确立了指导下一代科学智能体研发的四大底层理论假说：

1. **认知状态与执行解耦假说（Epistemic State Decoupling Hypothesis）**：将全局搜索前沿、因果事实图与局部单步执行上下文物理分离，通过条件路由召回，消除长周期决策中的注意力漂移与反馈钝感，将探索税压制在理论下界；
2. **结构化事件账本的反事实归因假说（Counterfactual Credit Assignment Hypothesis）**：依托不可篡改的事件流血缘追踪，自主反事实诊断平台期根本因果——精准分离表征表达力缺陷、采样函数病理与门禁边界错位，避免盲目超参扰动；
3. **分相分级的系统元演化假说（Staged Dual-Loop Self-Evolution Hypothesis）**：内环稳定捕获已知增益，外环改进器在独立影子沙箱中对模型代码与策略实施变异；以物理守恒定律与外部只读评估器作为最高不变量门禁，数学上免疫评价作弊（Goodhart's Law）；
4. **信息论价值驱动的实验设计假说（Information-Theoretic Value-of-Information Hypothesis）**：基于信息价值函数（VoI）权衡参数不确定性缩减收益与物理实验成本，使主动探索在复杂崎岖地貌上的全局收敛能力显著超越纯贪心算法 [23]、[27]、[28]。

### 8.3 顶层架构设计：基于事实-决策账本的五机双循环科学自演进系统

<!-- FIGURE_5_START -->
![图 5: 基于事实-决策账本的五机双循环递归自演进系统控制论架构](figures/fig5_five_machine_rsi.png)
*图 5: 基于事实-决策账本的五机双循环递归自演进系统控制论架构。系统由内层 DBTL 实验执行环（① 执行器、② 验证器、③ 控制器）与外层元科学演化环（④ 记忆器、⑤ 改进器）解耦构成。内层实现高样本利用效率的刚性捕获与硬性物理拦截；外层通过反事实归因在影子沙箱中自主合成代码级算法补丁，突破低阶归纳偏置表达力瓶颈。*
<!-- FIGURE_5_END -->

基于上述假说体系，系统构建了如图 5 所示的**五机双循环递归自演进系统控制论模型**：
1. **内层实验执行环（DBTL Operational Loop）**：由**执行器（Executor）**、**验证器（Verifier）**与**控制器（Controller）**协同构成。执行器采用当前最优代理模型生成确定性利用批次；验证器基于客观物理规律与留出基准执行最高安全裁决；控制器负责动态调度轮次与分配探索利用比例，确保执行过程的高样本利用效率与可重复性；
2. **外层元科学演化环（Meta-Scientific Evolutionary Loop）**：
   - **记忆器（Memory）**：依托全生命周期不可篡改的 **Fact（事实）** 与 **Decision（决策）** 账本，贯彻“失败数据亦具科研价值”原则，将失活与平庸样本转化为负向先验约束；
   - **改进器（Improver）**：持续监控内环边际收益。当检测到适应度平台期时，改进器自主检索物理文献与代码库，在隔离的影子沙箱中合成模型架构重构补丁（如从加性回归向成对 Potts 势能模型或图神经网络的自主迁移）[11]、[14]、[15]；在通过基准测试严格回归检验后，将新内核安全热部署至内环，实现系统的自主代际演进。

### 8.4 演进路线图：迈向通用自主科学发现系统

从当前的受控执行流水线走向通用闭环科研系统，本研究规划了清晰的三阶段技术路线图：
1. **第一阶段：工程化自动化实验流水线（本报告达成的 v0.1~v0.5 基准）**：完成受控五角色解耦，部署成对上位感知代理模型与自适应批次退火机制，消除提示词层面的负向锚定，使智能体能够在高置信度场景下保持对最优峰的高效逼近；
2. **第二阶段：受控自演进可审计科研系统（近期攻关目标）**：全面集成 Fact-Decision 实体账本与自动化因果归因引擎。系统在无人工干预下自主检测“上位表达力赤字”，在影子沙箱中自主完成模型与特征提取代码的重构与回归验证，实现特定蛋白质体系内的自发方法跃迁；
3. **第三阶段：通用递归自演进科学发现器（终极愿景与湿实验对接）**：跨越单靶点限制，自主提炼通用的高阶物理化学变异规律；结合生成式扩散模型（RFdiffusion / ProteinMPNN）开展池外全尺度分子设计 [15]、[16]、[24]；通过标准 API 对接自动化液体处理工作站（如 Hamilton / Tecan）与高通量测序仪，实现全流程无人值守的物理世界“假设-合成-筛选-演进”科研闭环 [25]、[26]、[29]、[30]。

---

## 参考文献

- [1] WU N C, DAI L, OLSON C A, et al. Adaptation in protein fitness landscapes is facilitated by indirect paths[J]. *eLife*, 2016, 5: e16965. DOI: 10.7554/eLife.16965.
- [2] BRYANT D H, BASHIR A, SINAI S, et al. Deep diversification of an AAV capsid protein by machine learning[J]. *Nature Biotechnology*, 2021, 39(6): 691-696. DOI: 10.1038/s41587-020-00793-4.
- [3] SARKISYAN K S, BOLOTIN D A, MEER M V, et al. Local fitness landscape of the green fluorescent protein[J]. *Nature*, 2016, 533(7603): 397-401. DOI: 10.1038/nature17995.
- [4] NOTIN P, DIAS M, FRAZER J, et al. ProteinGym: Large-Scale Benchmarks for Protein Fitness Prediction and Design[C]//Thirty-seventh Conference on Neural Information Processing Systems (NeurIPS 2023) Datasets and Benchmarks Track, 2023.
- [5] DALLAGO C, MOU J, JOHNSTON K E, et al. FLIP: Benchmark tasks in fitness landscape inference for proteins[C]//Thirty-fifth Conference on Neural Information Processing Systems (NeurIPS 2021) Datasets and Benchmarks Track, 2021.
- [6] SANDHU R, et al. FLIP2: Extended benchmarks and rigorous protocols for protein fitness prediction[EB/OL]. *bioRxiv*, 2026: 2026.02.23.707496.
- [7] LIN Z, AKIN H, RAO R, et al. Evolutionary-scale prediction of atomic-level protein structure with a language model[J]. *Science*, 2023, 379(6637): 1123-1130. DOI: 10.1126/science.ade2574.
- [8] MEIER J, RAO R, VERKUIL R, et al. Language models enable zero-shot prediction of the effects of mutations on protein function[C]//Thirty-fifth Conference on Neural Information Processing Systems (NeurIPS 2021), 2021.
- [9] HAYES T, RAO R, AKIN H, et al. Simulating 500 million years of evolution with a language model[EB/OL]. *bioRxiv*, 2024: 2024.07.01.600583.
- [10] SU J, HAN C, ZHOU Y, et al. SaProt: Protein Language Modeling with Structure-aware Vocabulary[C]//International Conference on Learning Representations (ICLR 2024), 2024.
- [11] HOPF T A, INGRAHAM J B, POELWIJK F J, et al. Mutation effects predicted from sequence co-variation[J]. *Nature Biotechnology*, 2017, 35(2): 128-135. DOI: 10.1038/nbt.3769.
- [12] POELWIJK F J, SOCOLICH M, RANGANATHAN R. Learning the pattern of epistasis linking genotype and phenotype in a protein[J]. *Nature Communications*, 2019, 10(1): 4213. DOI: 10.1038/s41467-019-12130-8.
- [13] TRAN D, et al. Rapid directed evolution guided by protein language models and epistatic interactions[J]. *Science*, 2026, 392(6798): eaea1820. (PMC12991030).
- [14] NOTIN P, ROLLINS N, GAL Y, MARKS D. ProteinNPT: Improving Protein Property Prediction and Design with Non-Parametric Transformers[C]//Thirty-seventh Conference on Neural Information Processing Systems (NeurIPS 2023), 2023.
- [15] DAUPARAS J, ANISHCHENKO I, KANG N, et al. Robust deep learning–based protein sequence design using ProteinMPNN[J]. *Science*, 2022, 378(6615): 49-56. DOI: 10.1126/science.add2187.
- [16] WATSON J L, JUERGENS D, BENNETT N R, et al. De novo design of protein structure and function with RFdiffusion[J]. *Nature*, 2023, 620(7976): 1089-1100. DOI: 10.1038/s41586-023-06415-8.
- [17] JIANG M, YAN J, et al. Rapid in silico directed evolution by a protein language model with EVOLVEpro[J]. *Science*, 2025, 387(6736): eadr6006. DOI: 10.1126/science.adr6006.
- [18] REETZ M T, CARBALLEIRA J D. Iterative saturation mutagenesis (ISM) for rapid directed evolution of functional enzymes[J]. *Nature Protocols*, 2007, 2(4): 891-903. DOI: 10.1038/nprot.2007.72.
- [19] STEMMER W P. Rapid evolution of a protein in vitro by DNA shuffling[J]. *Nature*, 1994, 370(6488): 389-391. DOI: 10.1038/370389a0.
- [20] WITTMANN B J, JOHNSTON K E, WU Z, ARNOLD F H. Informed training set design enables efficient machine learning-assisted directed protein evolution[J]. *Cell Systems*, 2021, 12(11): 1026-1045.e7. DOI: 10.1016/j.cels.2021.07.008.
- [21] ERIKSSON D, PEARCE M, GARDNER J, et al. Scalable globally optimal latent space Bayesian optimization via trust regions[C]//Advances in Neural Information Processing Systems (NeurIPS 2019), 2019.
- [22] SINAI S, WANG R, WHATLEY A, et al. AdaLead: A simple and robust adaptive greedy search algorithm for sequence design[EB/OL]. *arXiv preprint arXiv:2010.02141*, 2020.
- [23] SRINIVAS N, KRAUSE A, KAKADE S M, SEEGER M. Information-Theoretic Regret Bounds for Gaussian Process Optimization in the Bandit Setting[J]. *IEEE Transactions on Information Theory*, 2012, 58(5): 3250-3265. DOI: 10.1109/TIT.2011.2182033.
- [24] MADANI A, KRAUSE B, LU E I, et al. Large language models generate functional protein sequences across diverse families[J]. *Nature Biotechnology*, 2023, 41(8): 1099-1106. DOI: 10.1038/s41587-022-01618-2.
- [25] BOIKO D A, MACKNIGHT R, KLINE B, GOMES G. Autonomous chemical research with large language models[J]. *Nature*, 2023, 624(7992): 570-578. DOI: 10.1038/s41586-023-06792-0.
- [26] BRAN A M, COX S, SCHILTER O, et al. Augmenting large language models with chemistry tools[J]. *Nature Machine Intelligence*, 2024, 6(5): 525-535. DOI: 10.1038/s42256-024-00832-8.
- [27] HARRIS K, SLIVKINS A. Should You Use Your Large Language Model to Explore or Exploit?[C]//Proceedings of Machine Learning Research (PMLR), 2026. (arXiv:2502.00225).
- [28] NGO G, TRONG D P, NGUYEN D, GUPTA S, VENKATESH S. Adaptive Acquisition Selection for Bayesian Optimization with Large Language Models[C]//International Conference on Learning Representations (ICLR 2026). (arXiv:2602.07904).
- [29] QIN Y, SHI S, YE Y, et al. ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs[C]//International Conference on Learning Representations (ICLR 2024), 2024.
- [30] SCHICK T, DWIVEDI-YU J, DESSÌ R, et al. Toolformer: Language Models Can Teach Themselves to Use Tools[C]//Thirty-seventh Conference on Neural Information Processing Systems (NeurIPS 2023), 2023.
