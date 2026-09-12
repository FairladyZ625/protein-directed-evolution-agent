# 前沿全景 synthesis:我们在"LLM/ML 定向进化"版图中的诚实定位

> 一句话:六路独立前沿调研 + 我们 v0.1→v0.4 的实测,共同指向一个**当前学界的诚实共识**——LLM agent 的增益在科研的**上游/外围**(假设生成、文献综合、协议与代码、大语义空间的探索 oracle),而在**优化决策内核**(利用好 surrogate、选下一批)上,尚无可靠证据表明它优于固定采集函数/贪心,严谨对照多数显示**更差**。我们的"确定性 greedy 8.416 > LLM 自主 7.829"不是我们做错了,是这条裂缝的又一次独立命中。

本文档综合六路并行调研(见文末来源)与本仓四版实测,回答用户的核心问题:**greedy 一跑就达峰,是不是说明"问题已解决"?** 结论:**不是**——是"方法与地形对齐 + benchmark 偏易"的共同结果,与前沿共识吻合,而非蛋白设计被解决。全程 answer-agnostic,不看测试峰。

---

## 1. 六路调研来源与各自核心发现

| 路 | 调研问题 | 核心发现(一句话) | 最强锚点 |
|---|---|---|---|
| ① GLM | V0.5 agent 决策如何改 | 3 提名:质量感知 prompt+退火探索 / exploit-default kernel+LLM 提名 / 工具鲁棒性 | `v05-agent-optimization-glm.md` |
| ② Gemini | V0.5 agent 决策如何改 | 独立收敛到同 3 提名(Prompt 纠偏+CV 透传 / compose_batch 自适应配比 / 四层防御) | `v05-agent-optimization-gemini.md` |
| ③ Explore | 我们的 benchmark 有多难 | FLIP-AAV 落在"简单方法强项区"(池内/中等数据/mutation-dense);greedy 达峰 ≠ 解决 | FLIP2、Hsu 2022、Sandhu 2025 |
| ④ Explore | de novo 生成前沿 | 真正难的是 de novo 设计(RFdiffusion/ESM3/ProteinMPNN);池内排序只是其下游一环 | RFdiffusion、ESM3 |
| ⑤ Explore | ML-DE 的 SOTA 与真实基线 | 2024-26 一波负结果论文:简单基线在 mutation-dense/中等数据上 competitive;UQ 不胜 greedy | FLIP2、Greenman UQ、Kermut |
| ⑥ Explore | LLM agent 做科研前沿 | LLM 增益在上游/外围;利用步 LLM 自主决策 ≤ 固定采集函数,且对反馈不敏感 | 2509.21403、2502.00225、2504.06265 |

---

## 2. 三个横切共识(六路交叉印证,非孤例)

### 共识 A:LLM agent 的增益集中在"上游/外围",不在优化决策内核

- **有增益的地方**(第⑥路):假设生成、文献综合、协议与代码生成、工具编排、大语义动作空间的**候选探索**(exploration oracle)、冷启动/先验注入。实证 case:Coscientist(自主跑通 Suzuki 偶联)、ChemCrow(9.24/10 vs 裸 GPT-4 4.79)、Robin(把 ripasudil 重定位为干性 AMD 候选)。
- **无可靠增益的地方**(第⑥路):在"利用 surrogate、选下一批"这一步,**没有可靠证据表明 LLM 自主决策 ≥ 固定采集函数/贪心**。最致命的反证:*Are We There Yet?*(2509.21403)——把真实实验结果**换成随机打乱的标签,LLM agent 表现不变**,即 LLM 在环里根本没用实验反馈做 in-context 决策;*Explore or Exploit?*(2502.00225)——"所有被测 LLM 在利用上都不如一个线性回归"。

### 共识 B:利用步,经典贪心/采集函数本就很强;简单基线在特定 regime competitive

- **greedy 出人意料地强**(第⑤路 ALDE, Nat Commun 2025):5 残基组合空间里纯贪心"出人意料地有竞争力",TS/UCB 只"一致略胜",且"校准好 ≠ 更能找到最优变体"。
- **不确定性采集不胜 greedy**(第⑤路 Greenman 2025):acquisition 里加不确定性未必胜 greedy;PLM 嵌入未必胜 one-hot。
- **简单基线在 mutation-dense/中等数据上 competitive**(第③⑤路 FLIP2、"Simple baselines rival PLMs"、"Intrinsic dataset features drive prediction"):ridge/one-hot/site-mean/zero-shot 与最复杂微调 PLM 差距常 1-3 Spearman 百分点,相当比例情形简单方法反超;性能主要由**数据集内在结构 + 训练-测试突变距离**决定,不是模型容量。

### 共识 C:"救回 LLM"的办法,一律是"去自主化"

- 套 BO 的不确定性框架(第⑥路 2504.06265:用不确定性感知目标训练后在 19 个化学问题平均排名第一,超传统 BO 与裸 LLM;核心信息"自主性本身要被驯服")。
- LLM 提供先验 + 最近邻/经典采集做后验批选(LLMNN);LLM 增强 BO 组件但价值在冷启动(LLAMBO)。
- **当前最优范式 = 混合式分工**:LLM 管先验/探索/编排,经典 BO·主动学习管后验/利用/选点。

---

## 3. 我们四版发现如何逐条对齐前沿

| 本仓发现 | 实测结果 | 前沿文献镜像 |
|---|---|---|
| **v0.1 自由探索有毒** | 自由 agentic 5.96,strong 15 | 2502.00225:LLM 利用弱于线性回归;2509.24923"When Greedy Wins":SFT/RL 后更贪婪、更早放弃探索 |
| **v0.2 知识门禁治决策** | 门禁后 7.53(=greedy),strong 93 | 共识 C 去自主化:用知识约束收束 LLM 动作空间 |
| **v0.4 表征是决定性杠杆** | 加性 7.53 → 上位感知破顶 | MULTI-evolve(Science 2026 显式建模成对上位);共识 B"性能由数据内在结构决定" |
| **v0.4 确定性 greedy(8.416) > LLM 自主(7.829)** | 同 surrogate、同预算 | 2509.21403 对反馈不敏感;ALDE greedy 出人意料强;Greenman UQ 不胜 greedy |
| **更多轮次不助 LLM 达峰**(12r=7.829,16r=7.53) | 2-2.67× 预算无效 | 共识 A:LLM 在利用内核无增量智能,长程反而漂移(context drift) |

**结论:我们的四版是这三条共识在一个具体地形上的一次干净复现。**这不是失败,是一个**方法-地形对齐的诚实负结果**——"当 surrogate 已经好用时,把选点交给 LLM 自主判断,不如直接贪心",且这正是当前多源独立的主流结论。

---

## 4. 回答核心问题:greedy 达峰 = 问题已解决吗?

**不是。分三层回答:**

### 4.1 greedy 达峰是"方法与地形对齐"的必然,不是侥幸
在有正上位、且 cold-start 已含单/双突变实测的地形上,一个表达力够(pairwise Potts)的 surrogate 能把真峰重排进射程(#2776→#447),纯贪心把预算全押 top 预测即达峰。这是"对的模型 + 对的地形"的自然结果,ALDE/EVOLVEpro 在真实湿实验里也观察到同样现象。

### 4.2 我们的 benchmark 落在"简单方法强项区"(benchmark 偏易)
三条证据(第③⑤路):
1. **池内 + 中等数据 + mutation-dense**:cold-start 10433 条 HD≤2 实测已覆盖构成真峰的单/双突变,任务退化为"从已见基元里组合",这正是简单方法最强、PLM 优势最小的 regime。
2. **训练-测试突变距离近**:真峰 HD3/HD4,与 cold-start 的 HD≤2 只差 1-2 步,是内插而非外推——文献指认"突变距离"是难度主因。
3. **单目标、离散、in-silico 查表 oracle**:无多目标权衡、无测量噪声、无合成可行性约束、无湿实验回合成本。

### 4.3 真正的前沿难度在别处(第④⑥路)
- **de novo 生成**:从零设计新骨架/新功能(RFdiffusion/ESM3/ProteinMPNN),池内排序只是其下游一环。
- **OOD 外推**:向远离训练分布的高阶变体外推(而非我们的近距离内插)。
- **多目标 + 合成可行性 + 湿实验闭环**:活性×稳定性×表达×免疫原性联合优化,真实实验回合有成本、有噪声、有失败。

**所以诚实定位:我们做出的是"在一个偏易、单目标、内插型 benchmark 上,方法与地形对齐时贪心达峰,而 LLM 自主性在利用步是负担"的干净负结果。它有科学价值(与前沿共识互证),但绝不等于"蛋白设计已解决"。**

---

## 5. 这给 V0.5 的科学依据

前沿共识 C("去自主化/套经典框架")直接指向 V0.5 的改法方向,而非推翻它。GLM(第①路)与 Gemini(第②路)**独立收敛到同一套 3 条改法**,且每条都有前沿背书:

| V0.5 改法 | 做什么 | 前沿背书 |
|---|---|---|
| **A 认知纠偏 + CV 透传** | 删掉旧 prompt 里"surrogate 很烂(~0.6)、别信它"的负向锚定(那是 v0.1 加性时代的遗留,v0.4 已 CV 0.90);把 CV Spearman 显式透传给 agent,证据驱动 | 2504.06265(须让 agent 感知不确定性/质量);病灶诊断:prompt 教唆过度探索 |
| **B 自适应配比采集** | 把 agent 从"逐条选序列"降维成"定 exploit_ratio",底层按数学最优填 48 条;高 CV+晚轮次→纯贪心退火 | Gemini 退火 UCB β(ρ,t);共识 C 混合式分工;AdaLead/GP-UCB |
| **C 工具鲁棒性** | 修 `_gate()` 越界(29aa/突变代号致 `string index out of range`);四层防御 | 事件流诊断:2/6 轮 round_error;ToolLLM 自愈反馈 |

**建议顺序 C→A→B**:C 是零风险工程底座(先让 12/16 轮 0 崩溃),A 拨乱反正(拔认知毒瘤),B 建数学护栏。三者都 100% answer-agnostic(只用已测数据的 CV,不碰测试峰)。V0.5 的诚实目标不是"证明 LLM 能超 greedy"(共识说大概率不能),而是**缩小 LLM 自主 7.829 与确定性 8.416 的差距、并搞清差距的机械成因**——这本身就是一个对齐前沿裂缝的、有发表价值的诚实实验。

---

## 6. 来源(六路调研,均附可核引用)

- 第①路 GLM:`harness/context/research/v05-agent-optimization-glm.md`
- 第②路 Gemini:`harness/context/research/v05-agent-optimization-gemini.md`(516 行,含四病灶事件流诊断 + β 退火公式 + 四层防御)
- 第③④⑤⑥路 Explore(benchmark 代表性 / de novo 前沿 / ML-DE SOTA / LLM agent 科研前沿):结论已归并入本文,关键引用:
  - benchmark/基线:FLIP2、Hsu et al. 2022、"Simple baselines rival PLMs in mutation-dense tasks"、"Intrinsic dataset features drive prediction"、Kermut、ProteinNPT
  - greedy/UQ:ALDE(Nat Commun 2025)、Greenman(2025)、EVOLVEpro(Science 2025)、MLDE eval(Cell Systems 2025)
  - LLM agent:Coscientist(Nature 2023)、ChemCrow(NMI 2024)、Robin(2505.13400)、*Are We There Yet?*(2509.21403)、*Explore or Exploit?*(2502.00225)、uncertainty-calibrated(2504.06265)、*When Greedy Wins*(2509.24923)
  - de novo:RFdiffusion、ESM3、ProteinMPNN、MULTI-evolve(Science 2026)
- 本仓实测:`harness/reports/agentic-v0.1..v0.4/report.md`、`plateau-breaking-methods.md`

> 纪律:本文所有对本仓结果的引用均来自实测 report/metrics;所有前沿结论均来自六路调研的可核引用。个别作者署名标"待核实"处见各路原文。全程 answer-agnostic:定位判断不依赖任何测试峰的上帝视角信息。
