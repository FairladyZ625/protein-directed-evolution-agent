# 主动学习/定向进化平台期的破局手段 —— 文献调研 + 本项目落地判断

> 目的:实验一/二证明了 AAV 真峰 8.42 对"加性/监督排序"(正上位隐形)和"ESM zero-shot 自然度先验"(反自然)双重隐形,7.53 是当前设定的天花板。本文档回答:**真实蛋白工程科学家在这种平台期会怎么合法(answer-agnostic)破局?** 并把每族方法映射到"我们池式、288 预算、in-silico 查表 oracle 的笼子里能否落地"。
>
> 证据等级:标 ✔已核实 的是本会话 ground-truth 过的;其余为文献扫描结果,关键项标"待核实",正式引用前需再核。综合与判断由 CEO(本 session)把关。
>
> **本文件是旧快照,不要当现行版本用(2026-09-14 补)**:全文 96 行,停在「勘误二」之前;现行版本是 `lab/context/research/plateau-breaking-methods.md`(209 行),其中三条关键断言已被推翻并改写——①「该峰结构性不可达」为假(池峰在池内,固定 UCB β=3 可确定性命中);②「加性单步上升路径不存在」为假(实测 `WT` −0.918194 → `S17E` 3.287418 → `S17E+V18A` 5.770209 → 真峰 8.416205,每步 HD=1 且严格单调);③行数口径须并列声明(38,293 为长度 28 的唯一取值,loader 清洗子集为 38,265)。本快照未含这些更正。
>
> **流程回执更正(2026-09-14)**:原写「检索由 Explore 只读子代理完成」**是假的,已删**。按派工台账,文献检索由 Harness 派发的 worker 执行,全程无 Claude Explore 参与;且其中至少两次派工的 worker 报告含 "subagents in Booster Mode" 痕迹,违反了原任务 `task_plan.md` 的硬约束「禁 Booster、禁 spawn 子代理」(见 fact `F-A18E4666`)。

## 0. 贯穿判断的失败模式画像(本项目特有)

真峰 `QEEEIRTTNPVATEQYGEASTNLQRGNR` = {D0Q, S17E, V18A},HD3,**正上位**(实测 8.42 ≫ 加性预测 6.3)。三个单点的**孤立单突变效应都是有益的**:S17E Δ+4.2、V18A Δ+1.8、**D0Q Δ+1.2**——但 D0Q 在 cold-start 的**共现富集仅 −0.01**(与别的突变一起时被拉平,故加性/共现视角看似中性)。

**由此推出破局的三个必要条件:**
1. 从测量里**显式建模上位/交互项**(而非加性可分解);
2. **不用自然度先验筛突变**(否则把反自然峰重新藏起来);
3. 能**主动提出 HD3 组合**,而非加性单步贪心游走。

**一个关键的自证观察(✔已核实,本仓数据):** cold-start(HD≤2,10433 个)**本就包含单突变与双突变的实测**——D0Q 的有益性(单点 +1.22)与 S17E/V18A 的上位信息**已经在数据里**。之所以看不见,是因为我们用的 surrogate(Ridge 加性 / kNN / GBM)**表达力不覆盖交互项**。**⇒ 瓶颈是"加性 surrogate 的表达力",不是数据量、不是预算、不是表征(one-hot/ESM)本身。** 这把最省力的实验三诊断直接点了出来(见 §3 提名 B)。

---

## 1. 方法族综述(按破顶潜力判断)

### 族 2 · 高阶上位效应建模 —— 本题核心族,破顶潜力【高】
显式含交互项的模型(pairwise Potts、Walsh–Hadamard 稀疏谱、因子分解机、交互 kernel、非参 Transformer),使正上位不被加性项吞掉。经验:适应度函数在上位谱上高度稀疏,可用远少于 20^L 的样本恢复主要交互。
- EVmutation(pairwise Potts)— Hopf et al., **Nat. Biotechnol. 35:128, 2017**.
- Walsh–Hadamard 稀疏谱 — Poelwijk et al., **Nat. Commun. 2019**;Brookes et al., **PNAS 118, 2022**;Aghazadeh et al.(Epistatic Net), **Nat. Commun. 2021**.
- ECNet(显式残基对相依,专攻高阶)— Luo et al., **Nat. Commun. 2021**.
- ProteinNPT(非参 Transformer,低标签联合建模序列+标签)— Notin et al., **NeurIPS 2023**.
- **笼内可行性:可直接用(换 surrogate,零新增测量)。破顶潜力:高。** 唯一能"看见"藏峰的表征族。前提:构成峰的交互在已测数据里可观测(本仓 cold-start 含 doubles,见 §0)。

### 族 7 · 湿实验范式的 in-silico 类比 —— 第二高价值族,破顶潜力【高】
重组(DNA shuffling)、迭代饱和突变(ISM)、CASTing、组合库 + ML、间接路径游走。共同信息学内核:**系统测单/双突变 → 重组好基元 → 允许"先得后失"绕开 sign-epistasis 陷阱**。
- DNA shuffling — Stemmer, **Nature 370:389, 1994**.
- ISM/CASTing(明确指出其高效根因是正上位)— Reetz et al., **Nat. Protoc. 2007**.
- 组合库 + ML — Wu, Kan, Wittmann, Arnold, **PNAS 2019**.
- 间接路径逃 sign-epistasis(GB1 全地形)— Wu et al., **eLife 2016**;成对上位实测 — Olson et al., **Curr. Biol. 2014**.
- **笼内可行性:可直接用(采样设计层)。** 与我们 HD≤2 冷启动 + HD≤4 门禁天然契合:池内选双突变、重组、回溯游走都在笼内、answer-agnostic。

### 族 4 · 崎岖地形的主动采集 —— 破顶潜力【中,必要非充分】
信任域 BO(TuRBO)、批量/多样性(GFlowNet)、可行性门禁(viability-gated / 约束 BO)、离群预筛(ODBO)。治"高不确定=死蛋白"陷阱与探索踩空。
- TuRBO — Eriksson et al., **NeurIPS 2019**;GFlowNet 序列设计 — Jain et al., **ICML 2022**;BO-EVO — Yang et al., **Brief. Bioinform. 2023**;ODBO — Cheng et al., **arXiv:2205.09548**;AdaLead — Sinai et al., **arXiv:2010.02141**.
- **判断:采集再聪明,若 surrogate 仍加性也不会奖励藏峰。** 必须与族 2 联用。viability-gating 可借 AAV viability 分类器(Bryant 2021)思路。

### 族 3 · 结构/生物物理先验 —— 破顶潜力【中—中高,作提议器非排序主力】
FoldX / Rosetta cartesian_ddg 的 ΔΔG、AlphaFold 接触图 / 3D 共进化,把 HD3 组合限制在空间接触残基簇。
- FoldX — Schymkowitz et al., **NAR 2005**;Rosetta cartesian_ddg — Park et al.(**JCTC 2016,书目待核实**);AlphaFold — Jumper et al., **Nature 596, 2021**.
- **风险:** AAV 衣壳可变区多为柔性环,结构杠杆可能弱、AF 置信度低。需小幅扩展工具(结构/ΔΔG 计算)。

### 族 1 · 蛋白语言模型 zero-shot —— 破顶潜力【低,对本题近乎反指标】
ESM-1v(Meier et al., **NeurIPS 2021**)、ESM-2(Lin et al., **Science 2023**)、Tranception/ProteinGym(Notin et al., **ICML 2022 / NeurIPS 2023**)、EVE(Frazer et al., **Nature 2021**)、SaProt(Su et al., **ICLR 2024**)。
- **判断:已用尽(我们实测片段#3743/全长#4782,真峰 z 为负)。** zero-shot 是自然度先验 + 近加性,对反自然、正上位峰系统性失效。只可作特征之一,不能当排序主力。

### 族 5 · 迁移/低数据微调 —— 破顶潜力【低—中,有陷阱】
EVOLVEpro(Jiang/Yan et al., **Science 2025,✔已核实存在**)、Low-N(Biswas et al., **Nat. Methods 2021**)、ftMLDE 知情训练集设计(Wittmann/Arnold, **Cell Systems 2021**)。
- **警告:** 顶层回归多近加性 + 继承 PLM 自然度偏置;**任何"用自然度/PLM 排序缩小候选/挑训练集"的流程,在本题会把峰重新藏起来**,须排除。ftMLDE 的"用先验挑训练集"方法论可借鉴,但先验必须换成 answer-agnostic 且非自然度(如实测边际/覆盖度)。

### 族 6 · 生成式设计 —— 破顶潜力【闭合池低】
ProGen(Madani et al., **Nat. Biotechnol. 2023**)、EvoDiff(Alamdari et al., 2023)、DPLM(Wang et al., **ICML 2024**)、AAV 衣壳多样化(Bryant et al., **Nat. Biotechnol. 2021**)。
- **判断:** 价值在提出**池外**新序列;但我们 oracle 是**固定池**,池外序列无法测量,除非放开池定义。其 viability 分类器思路对族 4 有用。

---

## 2. 候选清单(合法性 answer-agnostic × 笼内可行性 × 破顶潜力)

| 排名 | 方法 | 合法 | 笼内可行 | 破顶 | 备注 |
|---|---|---|---|---|---|
| 1 | 双突变扫描 → 交互模型外推 HD3+(MULTI-evolve in-silico) | ✅ | ✅ 高(~120–250 次) | 高 | 直击成对/高阶正上位;单突变选择**禁用自然度门禁** |
| 2 | **代理换上位感知表征**(pairwise/FM/ECNet/ProteinNPT) | ✅ | ✅ 高(零新增测量) | 高 | 最省力;本仓 cold-start 已含 doubles(§0),先做这个 |
| 3 | 信任域 + viability-gated 采集 联用上位代理 | ✅ | ✅ 高 | 中 | 治死蛋白陷阱/探索踩空;单用加性代理无效 |
| 4 | 回溯/间接路径游走(逃 sign-epistasis) | ✅ | ✅ 高 | 中—高 | 与 HD≤4 门禁契合;破加性贪心锁死 |
| 5 | 结构接触引导 HD3 组合 | ✅ | 🧩 需结构工具 | 中—中高 | VR 环区结构杠杆存疑 |
| 6 | GFlowNet 多样批量提议 + 上位代理 | ✅ | ✅ | 中 | 奖励仍受代理限 |
| 7 | EVOLVEpro/Low-N 顶层回归 | ⚠️ | ✅ | 低—中 | 近加性+自然度偏置;含自然度筛选则违规 |
| 8 | zero-shot PLM 再排序 | ✅ | ✅ | 低(反指标) | 已用尽 |
| 9 | 生成式池外提议 | ⚠️ | 🧪 闭合池不可测 | 低 | 需放开池边界 |
| 10 | 物理重组/ISM 本体 | ✅ | 🧪 湿实验 | 高(湿) | 信息学等价物见 #1/#4 |

---

## 3. 实验三提名(给 CEO 裁定)

**提名 B(首选先做,最省最决定性)—— 上位感知 surrogate 消融。**
完全不改现有主动学习环(同池、同 288 预算、同 HD 门禁、同采集),**只把加性 Ridge/kNN/GBM 换成 pairwise 交互 / 因子分解机 / ECNet-style 代理**,在同一 cold-start 上训练,先做确定性诊断:**真峰门内预测排名是否从 #1283 降进可达区(≤288)?** 为何首选:§0 已证 cold-start 本就含 doubles,瓶颈是加性表达力——这是最干净地验证"天花板 = 加性 surrogate 表达上限"的一刀,成本近零、answer-agnostic。若诊断把真峰排进可达区,再接 LLM/闭环跑分。

**提名 A(若 B 的诊断显示 cold-start doubles 不够)—— 主动双突变扫描 + 交互外推(MULTI-evolve in-silico 复刻)。**
✔已核实蓝本:**Tran et al., "Rapid directed evolution guided by protein language models and epistatic interactions," Science 392(6798):eaea1820, 2026-05-07**(Arc Institute;Hie/Hsu)——实测 top~15 突变全部两两组合(~100-200 doubles)训模型外推到高阶,做到 5-7 突变、最高 256 倍。in-silico 复刻:answer-agnostic 选位点(如实测单突变边际 top + 全 VR 覆盖,**禁用 PLM 自然度筛**)→ 池内测双突变 → 浅层交互模型外推打分 HD3 → 末轮验证。预算 ~120-250 落在 288 内。**风险预登记:** 若峰的构成突变纯高阶/sign-epistasis(成对投影不显),双突变扫描仍可能漏;需先查"该峰在成对投影上是否显正上位"作可行性 gate。

**提名 C(可选,做成因归因)—— 信任域 + viability-gated 采集 + 回溯游走。**
用 TuRBO/BO-EVO/ODBO 信任域 + 可行性门禁替换自由探索,允许 HD 在 ≤4 门禁内先升后降(间接路径,Wu 2016)。与 B 组合可完整归因:平台期到底是"采集踩空/死蛋白陷阱"还是"表征看不见峰"。

**总纲:** 现有所有变体都困在"加性表征 + 自然度先验"两条对本峰无效的轴上;破顶几乎必然要跨到"上位感知表征(+ 必要时主动测成对上位)"。**建议顺序:先做 B 的确定性诊断(便宜、决定性),据结果再决定是否上 A。**

---

## 附:引用核实状态
- ✔已核实:MULTI-evolve(Science 2026,PMC12991030);EVOLVEpro(Science 2025);§0 本仓数据观察。
- 其余引用来自文献扫描,大部分为知名工作(EVmutation/ECNet/ProteinNPT/TuRBO/GFlowNet/ISM/EVE/Tranception 等),但**正式写入最终报告前应逐条核对**;明确标"待核实":cartesian_ddg 原始书目(Park et al. 2016 JCTC?)、"Higher-order epistasis creates idiosyncrasy"(Thornton 实验室)、WH 扩展 PLOS Comput Biol 2024、Signal Transduct Target Ther 2026 整合框架作者。
