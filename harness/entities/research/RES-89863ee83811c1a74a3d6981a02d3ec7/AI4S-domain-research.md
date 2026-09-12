# AI4S 笔试题第一版领域 Research：蛋白质定向进化科学智能体

> 用途：明度数智 AI4S 笔试项目（面向蛋白质定向进化的科学智能体，周日 2026-09-13 交卷）的知识底座。
> 读者设定：工业软件 Agent 架构师，蛋白质/AI4S 零基础。本文承担教学功能，从零讲起。
> 性质：01-调研层材料，可堆料、全部标来源。第一版（2026-09-10），后续按项目推进迭代。
> 题目全文：`03-面试/AI4S笔试.docx`

---

## 0. 三十分钟科普：看懂这道题需要的全部生物学

### 0.1 蛋白质是什么

蛋白质是一条**氨基酸链**。20 种标准氨基酸，用单字母表示（A/C/D/E/F/…/V/W/Y），像一门只有 20 个字母的语言。一条典型蛋白长 100–500 个"字符"（残基，residue）。蛋白质自发折叠成三维结构，结构决定功能（催化反应 / 结合靶点 / 发光等）。

### 0.2 定向进化（Directed Evolution, DE）

2024 年诺贝尔化学奖工作（Frances Arnold）。思路完全来自育种：**随机突变 → 筛选最好的 → 以它为起点再突变 → 循环**。不需要理解机制，只需要一个可测量的功能指标。痛点：序列空间是 20^L（一个 100 氨基酸的蛋白有 20^100 种可能），随机筛选命中率极低；突变之间还有**上位性**（epistasis，见 0.4）。

### 0.3 DMS（Deep Mutational Scanning，深度突变扫描）

本题所有数据集的实验来源。一次实验批量构造几万到几十万个突变体，用高通量测序估计每个突变体的"功能分数"（fitness）。产出就是一张表：**突变序列 → 实测 fitness**。这正好是监督学习数据，所以 DMS 数据集 = 蛋白质版的"labelled dataset"。

### 0.4 上位性（Epistasis）——本题的灵魂考点

一个突变的效果**依赖于其他位点是什么**。例：单点突变 A 单独有益、B 单独有益，但 A+B 组合反而有害（reciprocal sign epistasis）。后果：
- fitness landscape（适应度景观）是**崎岖的**，不是光滑山坡；
- 贪心/加性模型（把单点效果加起来预测组合）会系统性失败；
- GB1 数据集（见 1.3）就是为研究它而生的，论文标题即 "Adaptation … is facilitated by indirect paths"——绕路（先加有害突变再减掉）才能登顶。

题目背景段提到"上位性效应"、加分项提到"知识图谱表示位点—突变—性质—fitness 关系"，考的正是这个。Agent 如果只会"把历史最优单点突变拼一起"，在 GB1 上会被打脸——这本身就是可以写进报告的失败案例分析素材。

### 0.5 评价指标（和 ML 惯例的差异）

| 指标 | 含义 | 为什么用 |
|---|---|---|
| **Spearman ρ** | 预测值与真值的**秩**相关 | DMS 领域默认主指标。fitness 与功能常呈非线性/双峰关系，秩相关更稳（ProteinGym 论文原话） |
| Pearson / MSE | 线性相关 / 均方误差 | 题目要求，作辅助。注意不同 assay 的 fitness 量纲不齐，MSE 只在单一数据集内可比 |
| **NDCG@10% / Top-k recall** | 头部命中率 | 定向进化只关心 top 变体——你只需要最好的 10 个，不在乎中段排序。ProteinGym 专门为此加了 NDCG |
| AUC / MCC | 二值化后的分类指标 | 双峰型 assay 用 |

一句话：**排序能力（Spearman/NDCG）> 绝对值精度（MSE）**。这决定了 loss 和评估的设计。

### 0.6 蛋白质语言模型（PLM）在做什么

把氨基酸序列当文本，用 BERT/T5/GPT 架构在海量天然序列（UniRef，几十亿条）上预训练。核心信念：**进化已经在序列里写下了"什么替换能容忍、什么替换致命"的统计规律**。两种用法：
1. **零样本（zero-shot）打分**：突变氨基酸在模型眼里的概率变化（LLR，log-likelihood ratio）≈ 突变的可容忍度 ≈ fitness 的代理。不需要任何实验数据。
2. **嵌入（embedding）+ 监督回归**：把序列编码成向量，套一个小回归器（ridge/RF/MLP）从 DMS 数据学 fitness。这是本项目适应度预测模型的标准形态，也是 EVOLVEpro（见 3.4）的形态。

---

## 1. 板块一：数据集全景与选型

### 1.1 ProteinGym —— 领域的标准 benchmark（不是单个数据集）

- **是什么**：217 个 DMS 替换实验 + 66 个 indel 实验，共约 **250 万+ 突变体**，横跨 200+ 蛋白家族；另有临床变异 benchmark。Harvard Marks lab 维护。
- **格式**：每个 assay 一个 CSV：`DMS_id, mutated_sequence, DMS_score`（+突变串），v1.3 版约 1.0 GB。同时提供现成的 cross-validation 切分（singles / multiples）和所有 baseline 的预测分数（4.4 GB）——**意味着你不用跑大模型也能拿到 ESM-2/SaProt 等对每个突变的零样本分数做对照**。
- **用法**：不做训练大库用，而是**从中挑一个 assay** 当自己的任务；或用它对照 SOTA。
- 来源：https://proteingym.org / https://github.com/OATML-Markslab/ProteinGym / 论文 Notin et al. 2023, bioRxiv 2023.12.07.570727（"ProteinGym: Large-Scale Benchmarks for Protein Design and Fitness Prediction"）

### 1.2 FLIP —— 最贴合"工程任务"的基准

- **是什么**：NeurIPS 2021 benchmark track 论文（Dallago et al.），把 3 个蛋白质工程数据集（GB1 / AAV / Meltome thermostability）整理成**统一 CSV 格式 + 生物学动机的 train/test 切分**。2026 年推出 FLIP2（新增酶活/PPI/光敏蛋白等 7 个数据集，结论：简单模型常打平微调 PLM）。
- **格式**：`sequence, target, set(train/test)`，一个 zip 搞定。数据托管：http://data.bioembeddings.com/public/FLIP（FASTA 版也有）。
- **切分哲学（这是它最大的价值）**：`one_vs_rest`（train=WT+单点，test=其余）、`two_vs_rest`、`low_vs_high`（train=低于 WT 的，test=高于 WT 的——最难、最贴近真实优化场景）。比随机切分诚实得多，报告里引用这套协议会很加分。
- 来源：https://github.com/J-SNACKKB/FLIP / https://flip.protein.properties / 论文 bioRxiv 2021.11.09.467890；FLIP2：bioRxiv 2026.02.23.707496

### 1.3 六个候选数据集逐个看

| 数据集 | 蛋白/长度 | 规模 | fitness 含义 | 结构/上位性 | 一周 demo 适配度 |
|---|---|---|---|---|---|
| **GB1**（Wu 2016, eLife） | 蛋白 G B1 结构域，56 aa | **20⁴=160,000 组合全部实测**（149,361 个有效值）；FLIP 下采样版 8,733 条 | IgG 抗体结合富集度（log enrichment） | 4 个可变位点 V39/D40/G41/V54 **组合完备**，上位性极强（reciprocal sign epistasis 论文主题） | ★★★★★ |
| **GFP/avGFP**（Sarkisyan 2017, Nature） | 绿色荧光蛋白，238 aa | ~51,000 个随机突变体（多为 1–7 点突变）；FLIP fluo 任务约 5.2k 条 | 荧光强度（FACS 分选） | 景观"窄"：4 突变体一半完全不发光；30% 多点突变体有上位性 | ★★★★ |
| **AAV**（Bryant 2021, Nat Biotech） | AAV2 衣壳蛋白 28 aa 片段 | 201,426 个变异体（110,689 可包装） | 衣壳包装活力（基因治疗载体场景） | 稀疏采样、12–29 个突变；two_vs_rest 等切分 | ★★★ |
| **β-lactamase TEM-1**（Firnberg 2014；Jacquier 2013） | TEM-1 β-内酰胺酶，286 aa | Firnberg ~5.2k 变体（单点全覆盖为主）；Jacquier 10,000 克隆、990 个单点错义测 MIC | 氨苄抗性 MIC / 酶活 | 单点为主，上位性故事弱；蛋白较长 | ★★ |
| **ProteinGym 全集** | 217 assay | 2.5M+ | 各异 | 太大，做单任务要从里面挑 | 基准对照用 |
| **FLIP/Meltome** | 跨家族 | ~28k | 热稳定性 Tm | 跨蛋白泛化任务，与"定向进化单蛋白"场景不符 | ★ |

来源：GB1 — Wu et al. 2016 eLife, https://elifesciences.org/articles/16965（原始 160k 数据在补充材料；FLIP 版从 PDB 5LDE 推断 WT 序列）；GFP — Sarkisyan et al. 2017 Nature, http://europepmc.org/articles/pmc4968632；AAV — Bryant et al. 2021, https://www.nature.com/articles/s41587-020-00793-4；TEM-1 — Jacquier et al. 2013, https://pmc.ncbi.nlm.nih.gov/articles/PMC3740883（10,000 突变体、990 单点测 MIC）；Firnberg 2014（ProteinGym 内 assay id `BLAT_ECOLX_Firnberg_2014`）。

### 1.4 推荐：GB1 主攻 + GFP 备胎（理由）

**主推 GB1（经 FLIP 的 two_vs_rest 切分，或直接用 Wu 2016 原始 149k 全表）**，五个理由：

1. **组合完备 = 完美的"虚拟实验评估器"**。题目要求"使用测试集中真实 fitness 或训练好的预测模型作为虚拟实验评估器，模拟 2–3 轮迭代"。GB1 只突变 4 个位点、几乎全部 160,000 组合都有实测值——**Agent 无论提出什么 4 位点组合，都能查到真实 fitness**，虚拟闭环不需要任何近似，也不会因为"候选不在测试集里"而作弊或落空。其他所有数据集都做不到这点（GFP 突变空间 20^238，测试集只覆盖极小角落）。
2. **序列只有 56 aa**。ESM-2 嵌入在 CPU 上秒级；ProtT5 也可行。数据加载、嵌入缓存、Agent 多轮打分全部轻量，一周工期内无 GPU 依赖风险。
3. **上位性故事完整**，天然支撑"知识增强 vs 朴素 Agent"的对比实验和失败案例分析（题目考核重点最后两条）。
4. **切分协议现成**（FLIP one_vs_rest / two_vs_rest），指标预期有文献锚点（见 3.5），报告里可以写"我们的 baseline 与 FLIP 论文/排行榜对齐"。
5. **文献纵深**：ProGen 在 GB1 景观上做过生成采样实验；CombinGym（2026, bioRxiv 2026.03.24.714074）等新基准也拿 GB1 当主案例——讨论部分有话可说。

**备选 GFP（Sarkisyan，FLIP "fluo" 任务）**：如果想要更贴题的叙事（题目例子就是"提高荧光强度"），GFP 的故事性最好、公众认知度高。代价：238 aa、组合空间开放（Agent 提的候选大概率不在数据集里，必须用预测模型当评估器，闭环里引入了模型误差）、下采样后 5k 条。**建议：GB1 为主任务，GFP 作为泛化性展示或报告讨论素材**——工期紧就砍掉。

工程注意：FLIP 的 GB1 下采样版（8,733 条）压掉了大量零 fitness 变体，适合训模型；但如果要当"虚拟评估器"，直接用 Wu 2016 原始表（149,361 条，ProteinGym 内 assay id `SPG1_STRSG_Wu_2016`）查表更完整。两份都用、各自说明用途。

---

## 2. 板块二：蛋白质语言模型（PLM）选型与推理成本

### 2.1 候选模型对比

| 模型 | 机构/年 | 参数 | 架构 | 获取 | CPU 可行性 | 对本项目 |
|---|---|---|---|---|---|---|
| **ESM-2** (Lin et al. 2023, Science) | Meta | 8M/35M/150M/**650M**/3B/15B | BERT 式 masked LM | HF `facebook/esm2_t33_650M_UR50D`，MIT 友好 | **650M 完全可行**（56aa 序列秒级/条）；有 CPU 专用推理引擎 esm.cpp（INT8 量化） | **主力**：嵌入 + 零样本 LLR |
| ESM-1v (Meier 2021) | Meta | 5×650M ensemble | masked LM，为变异效应而生 | HF / fair-esm | 单模型可行，5 模型 ensemble 偏重 | 对照基线（文献里常引用） |
| **ESM3** (Hayes et al. 2024) | EvolutionaryScale | 1.4B open / 7B / 98B | 多模态（序列+结构+功能）生成式 | `pip install esm`；**仅 1.4B 开放权重，Cambrian 非商业许可**；7B/98B 走 Forge API | 1.4B CPU 慢，API 有速率限制 | 引用其 esmGFP（生成全新荧光蛋白）作讨论素材；不当主力 |
| **ProtT5-XL-UniRef50** (Elnaggar 2021/2022, IEEE TPAMI) | Rostlab | ~3B（encoder-only 推理时砍半） | T5 encoder-decoder | HF `Rostlab/prot_t5_xl_uniref50` | CPU 需 float32，**慢但能跑**（GB1 56aa 尚可，238aa 的 GFP 吃力）；GPU 上 fp16 单卡 12GB | 嵌入对照：1024 维/残基，回归特征质量老牌口碑 |
| **SaProt** (Su et al., ICLR 2024) | 西湖大学 | 35M/650M/1.3B | **AA+3Di 结构感知词表**（ESM-2 骨干） | HF `westlake-repl/SaProt_650M_AF2` | 同 ESM-2 650M；**但要先有结构 → Foldseek 编 3Di token**，多一道管线 | 加分项素材：引入结构信息（题目加分项"引入蛋白质结构信息"）。ProteinGym 零样本 0.478 vs ESM-2 0.475（提升小），但在结构类任务优势明显 |

来源：ESM-2 — https://github.com/facebookresearch/esm（含 `scripts/extract.py` 批量提嵌入、zero-shot variant prediction 示例）、HF 模型卡；ESM3 — https://github.com/evolutionaryscale/esm、https://evolutionaryscale.ai/blog/esm3-release（esmGFP：与已知荧光蛋白仅 58% 同源，"5 亿年进化"）；ProtT5 — HF `Rostlab/prot_t5_xl_uniref50` 模型卡（encoder 优于 decoder、fp16 推理建议）；SaProt — https://github.com/westlake-repl/SaProt + ICLR 2024 论文（注意其 README 提示：35M/650M 版**必须带 3Di 结构输入**，AA-only 冻结嵌入无效）；CPU 推理 — esm-cpp 项目（pypi `esm-cpp`，W8A8 量化，ProteinGym Spearman 漂移 <0.01）。

### 2.2 嵌入提取与零样本打分（具体怎么做）

**嵌入（监督回归模型的输入特征）**：
```python
# fair-esm 官方姿势（CPU 可跑）
model, alphabet = esm.pretrained.esm2_t33_650M_UR50D()
batch_converter = alphabet.get_batch_converter()
with torch.no_grad():
    results = model(tokens, repr_layers=[33], return_contacts=False)
seq_emb = results["representations"][33].mean(0)   # 序列级：平均池化, 1280 维
# 进阶（对突变更敏感）：只对突变位点取 per-residue 向量/WT 与突变体向量差
```
官方批量脚本：`python scripts/extract.py esm2_t33_650M_UR50D seqs.fasta out_dir --repr_layers 33 --include mean per_tok`（来源：facebookresearch/esm README）。

**零样本 LLR 打分（masked marginal，ESM 系标准做法）**：把突变位置 mask 掉，取模型在该位置输出氨基酸分布，`LLR = log p(突变氨基酸) − log p(野生型氨基酸)`。多位点突变对各位置求和（加性近似——在 GB1 这种强上位性数据上这就是个已知短板，可在失败案例分析里讨论）。参考 ProteinGym 的推理流程：每个位置需一次前向（来源：bioRxiv 2025.04.25.650688 对 ESM-2 masked-marginal 协议的复述 + NVIDIA BioNeMo 教程 docs.nvidia.com/bionemo-recipes）。

**选型结论（对齐一周工期 + CPU only）**：
- 嵌入特征：**ESM-2 650M**（1280 维序列级 + 突变位点 per-residue 拼接），GB1 全量 149k 条 × 56aa 一次离线缓存（CPU 数小时内），之后所有轮次查缓存。
- 零样本分数：ESM-2 masked-marginal LLR，作为 (a) baseline 行、(b) 监督模型附加特征（ProteinNPT 论文证明"监督模型 + 零样本分数作特征"普遍提升）。
- 若时间富余：SaProt（需 PDB 1PGB/5LDE 结构 + Foldseek）做结构增强对照，直接回应加分项。

### 2.3 一个反直觉的教学点（报告里可写）

**PLM 不是越大越好**。bioRxiv 2025.04.25.650688（"Understanding Protein Language Model Scaling…"）系统验证：ESM-2 **650M 在突变效应零样本预测上反超 3B 和 15B**——模型对某蛋白的困惑度存在 3–6 的"最甜区间"，过大的模型把野生型概率推到接近 1，LLR 动态范围塌缩，区分度反而下降。SaProt 论文也报告 ESM-2 15B 不及 650M。对工程选型这是好消息：**CPU 上正好用不大不小的模型就是当前最优实践**。

---

## 3. 板块三：适应度预测 baseline 与 2025–2026 SOTA 坐标系

### 3.1 零样本（PLM 不训练直接打分）能到什么水平

ProteinGym v1.3 替换基准官方榜（217 assay 平均 Spearman，来源 https://proteingym.org/benchmarks 及 GitHub 内 CSV）：
- #1 AIDO Protein-RAG (16B, Structure+MSA)：**0.518**
- ProSST / S3F-MSA 等结构+MSA 混合系：0.49–0.51 档
- Tranception / TranceptEVE（自回归+MSA 混合）：~0.47–0.49
- **SaProt 650M：0.478；ESM-2 650M：0.475**（SaProt 论文 Table 1）
- 多智能体新秀 Rank-and-Reason/VENUSRAR（arXiv 2602.00197）宣称 0.551 ——尚待同行检验，引用时注明

**经验区间：单序列零样本 0.40–0.50；带 MSA/结构检索 0.47–0.52。** 单个 assay 上方差极大（同一个模型在不同蛋白上可以从 -0.1 到 0.8），报告里必须报自己那一个数据集的数，不能拿全集平均冒充。

### 3.2 监督式（DMS 数据训小模型）能到什么水平

- ProteinGym 论文监督榜第一 **ProteinNPT 0.613**（Random CV 下 0.65；Contiguous/Modulo 切分 0.48/0.51）——来源 Notin et al., NeurIPS 2023。关键教学法：**切分方式决定分数**，Random CV 高分很大程度上是"同位点不同氨基酸"泄漏，Contiguous（按区段外推）才考验真泛化。
- 同论文的实用梯队：one-hot + 零样本分数增广 0.42–0.44；**PLM 嵌入 + 零样本分数 + 线性/浅层模型 0.51**；即"嵌入+小回归器"离 SOTA 不远，完全在一周工期内。
- **FLIP2（2026）的重要冷水**：在贴近真实工程的切分上，"简单模型（线性/浅层）经常打平或超过微调 PLM"。写进报告的失败分析/改进建议部分很有说服力（来源：bioRxiv 2026.02.23.707496 / flip.protein.properties）。

### 3.3 具体到 GB1 / GFP 的合理预期（给自己定锚）

| 任务 | 设定 | 合理 Spearman 预期 | 依据 |
|---|---|---|---|
| GB1 two_vs_rest（train=单点+双点，test=3–4 点组合） | PLM 嵌入+GBM/MLP | **0.55–0.75** | FLIP 排行榜量级；组合外推上位性使加性模型明显掉分 |
| GB1 one_vs_rest（train 仅 29 条） | 零样本为主 + 少样本回归 | 0.4–0.6 | 低数据区 PLM 零样本（0.4x）+ EVOLVEpro 式 few-shot |
| GB1 low_vs_high（最难，train=差变体 test=好变体） | 任意 | 0.2–0.4 | NVIDIA BioNeMo 基准：ESM2-15B 仅 0.340（docs.nvidia.com/bionemo-framework） |
| GFP fluo（FLIP 下采样） | 嵌入+回归 | 0.6–0.7 | FLIP 论文 baseline 区间 |

（GB1 具体名次随实现浮动，赛前先用 FLIP 官方 baseline 数字校准一次；关键是把"我们到了哪个档位"说清楚。）

### 3.4 2024–2026 的方法论主线：few-shot 主动学习取代大规模监督

这是本轮笔试最该蹭的方法论前沿：

1. **EVOLVEpro**（Jiang et al., Science 387, 2025; bioRxiv 2024.07.17.604015; 开源 https://github.com/mat10d/EvolvePro）：**PLM 嵌入（ESM-2 等）→ 顶层随机森林回归 → 主动学习选批次 → 每轮仅 ~10 条实验数据**，4 轮内 6 个蛋白（Cas9、PE2、tRNA、抗体等）最高 **100 倍**活性提升。**这就是题目"Fitness Evaluator + 虚拟迭代"的现成科学模板**，代码可读、结构极简（本质：嵌入差分 + RF + acquisition）。
2. **MULTI-evolve**（Tran et al., 2026, PMC12991030）：PLM + 上位性模型联合打分，单轮 ML-DE 10 倍提升——"上位性建模"组件可直接借鉴到知识增强环节。
3. **PRIMO**（arXiv 2512.02315）：in-context learning + test-time training 的少样本 fitness 预测器，越过"零样本 vs 全监督"的老对立。
4. 低数据微调路线：bioRxiv 2402.02004（少样本样本扩增大 PLM 微调）。

**对项目的直接结论**：baseline 采用 **"ESM-2 嵌入 + 零样本 LLR 作附加特征 + 梯度提升树/MLP"**，评估报 Spearman + NDCG + Top-k recall；Agent 的虚拟进化循环里，每轮用已"测"（查表）数据重训回归器 = 复刻 EVOLVEpro 的主动学习环（同时拿下题目加分项"主动学习"）。不确定性估计用 RF 自带的树间方差或 GP——再拿加分项"不确定性估计"。

---

## 4. 板块四：LLM Agent × 定向进化 / 科学发现（2024–2026）

> 注：任务描述里提到的 "Creon" 在文献检索中**查无此名**——大概率是语音输入错词（最接近的真实工作是 ProGen / Genie / EVOLVEpro 系）。已按真实文献覆盖；下表即"Creon/ProGen 等"想指的那批工作。

### 4.1 与本题直接同构的工作（重点精读 3 篇）

| 工作 | 年份/出处 | 一句话 | 对本题的可偷之处 |
|---|---|---|---|
| **EVOLVEpro** | Science 2025（§3.4） | PLM 嵌入 + RF 主动学习，4 轮少样本进化 | Fitness Evaluator 的科学模板；"每轮 10 条"的批次预算叙事 |
| **ProteinEngine** | arXiv 2405.06658 | LLM 扮 AI-PM / AI-Domain-Expert / AI-Presenter 三角色编排蛋白工程工具链（MSA Transformer、ESM-IF1、docking…） | **模块化角色设计**的先例：与题目要求的 Data Analyst / Hypothesis Generator / Mutation Designer / Fitness Evaluator / Scientific Critic 五模块几乎一一对应；论证"prompt + 工具调用即可，不需要重框架" |
| **STELLA** | bioRxiv 2025.07.01.662467 | 自进化多智能体（Manager/Developer/Critic/Tool-Creation），在 strictosidine synthase 上完成全流程定向进化，M276L 活性 >2× | Critic 角色 + 工具库自扩展；湿实验验证的 DE 全流程 agent 叙事 |

### 4.2 更大的图景（报告"背景/相关工作"段用）

- **Lab-in-the-loop / 自动生物工厂**：
  - SAMPLE（Nat Chem Eng, 2024, s44286-023-00002-4）：自驱动实验室 + GP 代理模型搜糖苷水解酶热稳定性——pre-LLM 时代的经典闭环。
  - iBioFAB 平台（Nat Comms 2025, s41467-025-61209-y）：ESM-2 + EVmutation 设计库 + 自动化湿实验 + 低样本 ML，4 周 4 轮，16–26 倍活性；含自然语言交互界面——题目最后一问"如何连接真实自动化实验平台"的答案模板。
  - PLM + 自动生物铸造厂（Nat Comms 2025, s41467-025-56751-8）：PLM 指导进化 + biofoundry 闭环整合。
- **多智能体 / 环境**：
  - PRIME（bioRxiv 2025.09.22.677756）：65+ 蛋白工具的多智能体环境，动态工作流合成，213 任务基准，SARS-CoV-2 抗体 de novo 验证。
  - VenusFactory2（arXiv 2603.27303）：自进化多智能体做蛋白发现与定向进化，"从静态工具调用到动态工作流合成"。
  - Genie-CAT（arXiv 2511.19423）：RAG + PDB 解析 + 静电计算 + ML 预测的金属酶设计 agent——"工具增强、可验证执行防幻觉"论点。
  - Rank-and-Reason / VENUSRAR（arXiv 2602.00197）：Computational Expert + Virtual Biologist 双智能体审 PLM 输出，ProteinGym 0.551——**"LLM 审模型输出"正是题目 Scientific Critic 模块的最新学术依据**。
- **LLM 直接当序列优化器**：
  - "Large Language Model is Secretly a Protein Sequence Optimizer"（arXiv 2501.09274）：把定向进化循环直接套在通用 LLM 上（进化式 prompting + Pareto/预算约束），合成与实验景观上均成功——支持"LLM Agent 推荐突变"不是玄学的正面证据。
- **生成式 PLM（ProGen 系）**：
  - ProGen（Salesforce, arXiv 2004.03497 → Nat Biotech 2023）：自回归蛋白生成模型；**正是在 GB1 景观上验证了条件采样能获得高 fitness 样本**。
  - ProGen2（2022）：ProteinGym indel 零样本榜首之一（0.467，与 TranceptEVE 并列）。
  - DPLM-Evo（arXiv 2605.00182）：扩散式 PLM 的进化编辑版，GFP 定向进化案例 + 单序列设定下 ProteinGym SOTA——2026 前沿。
  - ESM3/esmGFP（§2.1）：生成式新荧光蛋白，报告"未来拓展"段的好结尾。

### 4.3 对 Agent 设计的直接结论（与你的架构经验对位）

题目要求的五模块（Data Analyst → Hypothesis Generator → Mutation Designer → Fitness Evaluator → Scientific Critic）本质是一条**带评审门的流水线 + 外部评估器闭环**，映射到工业软件 Agent 的成熟套路：

- Data Analyst = 事件流/指标聚合（对 top variants 做位点频率、氨基酸替换偏好统计——GB1 上就是 4 个位点的 20 面骰子分布）；
- Hypothesis Generator + Mutation Designer = 受约束的代码生成（输出必须是合法突变对象：位点 ∈ {39,40,41,54}，氨基酸 ∈ 20 标准aa，突变数 1–4）——schema 校验 + 拒绝重试，等价于工具调用的参数校验层；
- Fitness Evaluator = 纯函数工具（查表 oracle 或 ESM-2+GBM 打分），Agent 不许自己"脑补"分数——防幻觉即 PRIME/Genie-CAT 的"可验证执行"原则；
- Scientific Critic = 合并前的 review gate（检查终止密码子、突变数上限、上位性冲突、与历史失败序列重复）；
- 虚拟进化循环 = 外层事务：每轮"提议 → 评估 → 提交结果 → 更新训练集重训模型"，天然可回滚可复现（记录每轮快照）。

这套对应关系本身就是笔试报告"Agent 设计"一节的差异化卖点：**别人写 prompt 串接，你写带校验门、可验证工具调用、事务化迭代日志的系统**。

---

## 5. 一周技术栈建议（汇总）

| 层 | 选型 | 备注 |
|---|---|---|
| 数据 | GB1（Wu 2016 全表做 oracle；FLIP two_vs_rest 做建模切分） | 见 §1.4 |
| PLM | ESM-2 650M（HF，CPU），嵌入离线缓存；零样本 masked-marginal LLR | 见 §2.2 |
| 适应度模型 | ESM-2 嵌入(+LLR) → LightGBM / sklearn MLP / GP | EVOLVEpro 同款；GP 顺带不确定性 |
| Agent | Python + OpenAI 兼容 API + 函数调用（不引重框架，题目明示允许）；五模块 = 五个 prompt 角色 + 工具层 | 见 §4.3 |
| 知识增强 | 20 氨基酸理化性质表（疏水性/电荷/体积）→ 突变规则库（保守替换打分 BLOSUM62、突变数上限、终止子检查）+ 简单三元组知识图谱（题目给的 4 种关系） | 有无知识增强做 A/B 对比（题目硬性要求） |
| 评估 | Spearman 主指标 + NDCG@10% + Top-k 命中率；四路对比：随机 / 模型直推 / LLM Agent / 知识增强 Agent（题目硬性要求） | 随机基线别忘：GB1 上 77% 变体 fitness≈0，随机很弱，容易赢——也说明为什么要报 NDCG |
| 交付 | PDF 报告 3–5 页 + GitHub repo（README 含环境/命令/结果） | 题目硬性要求 |

时间盒建议（周四晚起算）：D1 数据管线+oracle 查表 → D2 ESM-2 嵌入+baseline 回归 → D3 Agent 五模块+循环 → D4 知识增强+A/B → D5 2–3 轮虚拟进化跑通+收数 → D6 报告+README → D7 缓冲。

---

## 6. 来源清单（去重汇总）

**数据集/benchmark**
1. ProteinGym 官网+下载：https://proteingym.org ；GitHub：https://github.com/OATML-Markslab/ProteinGym ；论文：Notin et al. 2023, bioRxiv 2023.12.07.570727（PMC10723403）
2. FLIP：GitHub https://github.com/J-SNACKKB/FLIP ；数据 http://data.bioembeddings.com/public/FLIP ；论文 bioRxiv 2021.11.09.467890
3. FLIP2：https://flip.protein.properties ；bioRxiv 2026.02.23.707496
4. GB1：Wu et al. 2016, eLife, https://elifesciences.org/articles/16965
5. GFP：Sarkisyan et al. 2017, Nature, http://europepmc.org/articles/pmc4968632
6. AAV：Bryant et al. 2021, Nat Biotech, https://www.nature.com/articles/s41587-020-00793-4 ；Ogden et al. 2019, Science 366:1139
7. β-lactamase：Jacquier et al. 2013, https://pmc.ncbi.nlm.nih.gov/articles/PMC3740883 ；Firnberg et al. 2014（ProteinGym 内 BLAT_ECOLX_Firnberg_2014）
8. CombinGym：bioRxiv 2026.03.24.714074

**PLM**
9. ESM-2/ESM-1v/代码与提嵌入脚本：https://github.com/facebookresearch/esm ；Lin et al. 2023 Science
10. ESM3：https://github.com/evolutionaryscale/esm ；https://evolutionaryscale.ai/blog/esm3-release ；Hayes et al. 2024, bioRxiv 2024.07.01.600583
11. ProtT5：HF `Rostlab/prot_t5_xl_uniref50` ；Elnaggar et al., IEEE TPAMI 2022
12. SaProt：https://github.com/westlake-repl/SaProt ；Su et al., ICLR 2024（bioRxiv 2023.10.01.560349）
13. esm.cpp（CPU 推理引擎）：https://pypi.org/project/esm-cpp/
14. ESM-2 规模效应反直觉：bioRxiv 2025.04.25.650688
15. NVIDIA BioNeMo 模型基准（FLIP 任务）：https://docs.nvidia.com/bionemo-framework/latest/models/model-benchmarks.html

**适应度预测 SOTA**
16. ProteinGym 榜单（AIDO Protein-RAG 0.518 等）：https://proteingym.org/benchmarks
17. ProteinNPT：Notin et al., NeurIPS 2023, bioRxiv 2023.12.06.570473（监督 0.613；嵌入+零样本 0.51）
18. EVOLVEpro：Jiang et al., Science 387:eadr6006 (2025)，https://doi.org/10.1126/science.adr6006 ；https://github.com/mat10d/EvolvePro
19. MULTI-evolve：Tran et al. 2026, PMC12991030
20. PRIMO few-shot in-context：arXiv 2512.02315
21. 少样本微调：arXiv 2402.02004

**LLM Agent / 科学发现**
22. ProteinEngine：arXiv 2405.06658
23. STELLA：bioRxiv 2025.07.01.662467
24. PRIME 多智能体环境：bioRxiv 2025.09.22.677756
25. VenusFactory2：arXiv 2603.27303
26. Genie-CAT：arXiv 2511.19423
27. Rank-and-Reason (VENUSRAR)：arXiv 2602.00197
28. LLM as protein sequence optimizer：arXiv 2501.09274
29. SAMPLE 自驱动实验室：Nat Chem Eng 2023, https://www.nature.com/articles/s44286-023-00002-4
30. iBioFAB 自主酶工程平台：Nat Comms 2025, https://www.nature.com/articles/s41467-025-61209-y
31. PLM+biofoundry 闭环进化：Nat Comms 2025, https://www.nature.com/articles/s41467-025-56751-8
32. ProGen：arXiv 2004.03497（GB1 景观采样）；ProGen2：arXiv 2206.13517
33. DPLM-Evo：arXiv 2605.00182
34. AI-Biology 生物安全视角（讨论段可选）：Front Microbiol 2025, 10.3389/fmicb.2025.1734561

---

## 7. 遗留问题 / 下一版补

- [ ] GB1 two_vs_rest 上 FLIP 官方 baseline 的精确 Spearman 数字表（写报告时到 FLIP 仓库 splits/gb1 的 baseline 页核一遍）
- [ ] "Creon" 一词的出处确认（语音词表？）——当前判断为 ProGen/Genie/EVOLVEpro 混音
- [ ] ESM-2 650M 在本机 CPU 的实测吞吐（决定嵌入缓存预算，D1 实测后回填）
- [ ] SaProt 是否值得排进主线程（倾向：加分项时间富余才做）
- [ ] GFP 备选数据在 D1 结束时决定是否保留
