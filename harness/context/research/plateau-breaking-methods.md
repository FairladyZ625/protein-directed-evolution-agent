# 主动学习/定向进化平台期的破局手段 —— 文献调研 + 本项目落地判断

> ⚠️ **勘误(2026-09-12,fact F-E9C38438 supersedes F-5A4B6556)**:本文档 §0 的核心论断「cold-start 本已包含构成真峰的全部单突变与双突变实测 ⇒ 瓶颈是加性 surrogate 的表达力,不是数据覆盖」**为假**。CEO 用 `data/aav/full_data.csv` 的 `score` 列独立复算(38293 条 28aa 序列)确认:三个单突变的有益性成立(D0Q=0.302016、S17E=3.287418、V18A=0.889606,WT=-0.918194,即 +1.220/+4.206/+1.808),二阶 D0Q+V18A=2.087894、S17E+V18A=5.770209 都在,**但 D0Q+S17E 这一对在数据表中根本不存在**。正确表述是双因素:**关键二阶组合缺测(即 D0Q+S17E)+ 模型表达力与头部外推失真**,与 `v07-peak-mechanism.md` 的独立结论一致。本文档由该错误论断推出的排序清单与首选实验论证,均需按此重读。


> 目的:实验一/二证明了 AAV 真峰 8.42 对"加性/监督排序"(正上位隐形)和"ESM zero-shot 自然度先验"(反自然)双重隐形,7.53 是当前设定的天花板。本文档回答:**真实蛋白工程科学家在这种平台期会怎么合法(answer-agnostic)破局?** 并把每族方法映射到"我们池式、288 预算、in-silico 查表 oracle 的笼子里能否落地"。
>
> 证据等级:标 ✔已核实 的是本会话 ground-truth 过的;其余为文献扫描结果,关键项标"待核实",正式引用前需再核。检索由 Explore 只读子代理完成,综合与判断由 CEO(本 session)把关。

## 0. 贯穿判断的失败模式画像(本项目特有)

真峰 `QEEEIRTTNPVATEQYGEASTNLQRGNR` = {D0Q, S17E, V18A},HD3,**正上位**(实测 8.42 ≫ 加性预测 6.3)。三个单点的**孤立单突变效应都是有益的**:S17E Δ+4.2、V18A Δ+1.8、**D0Q Δ+1.2**——但 D0Q 在 cold-start 的**共现富集仅 −0.01**(与别的突变一起时被拉平,故加性/共现视角看似中性)。

**由此推出破局的三个必要条件:**
1. 从测量里**显式建模上位/交互项**(而非加性可分解);
2. **不用自然度先验筛突变**(否则把反自然峰重新藏起来);
3. 能**主动提出 HD3 组合**,而非加性单步贪心游走。

**一个关键的观察(✔已核实,本仓数据,2026-09-12 修正):** cold-start(HD≤2,10433 个)包含三个单突变的实测(D0Q +1.22、S17E +4.206、V18A +1.808,相对 WT −0.918194),也包含两对二阶组合的实测(D0Q+V18A=2.087894、S17E+V18A=5.770209),**但构成真峰所必需的第三对 D0Q+S17E 在数据表中根本不存在**——不是未被采样进 cold-start,而是 `data/aav/full_data.csv` 里就没有这条测量。

因此瓶颈是**两个因素叠加**,不是单一因素:

1. **关键二阶组合缺测**:D0Q+S17E 这一对没有任何实测,任何 answer-agnostic 的 surrogate——包括完全能表达交互项的模型——都无法从数据中学到这一对的正上位。
2. **模型表达力与头部外推失真**:在已测的两对二阶组合上,加性 Ridge/kNN/GBM 确实表达不了交互,这部分是真的。

**⇒ 换上位感知 surrogate 只能解决因素 2,解决不了因素 1。** 这一点直接决定了 §3 的提名排序:单靠换 surrogate 不足以保证真峰进入可达区,必须同时有一条**主动补测二阶组合**的路径。

> 本段的早先版本曾断言「cold-start 本已包含构成真峰的全部单突变与双突变实测 ⇒ 瓶颈仅是加性 surrogate 的表达力」,该断言为假(fact F-E9C38438 supersedes F-5A4B6556),已按上文改写。

---

## 1. 方法族综述(按破顶潜力判断)

### 族 2 · 高阶上位效应建模 —— 本题核心族,破顶潜力【高】
显式含交互项的模型(pairwise Potts、Walsh–Hadamard 稀疏谱、因子分解机、交互 kernel、非参 Transformer),使正上位不被加性项吞掉。经验:适应度函数在上位谱上高度稀疏,可用远少于 20^L 的样本恢复主要交互。
- EVmutation(pairwise Potts)— Hopf et al., **Nat. Biotechnol. 35:128, 2017**.
- Walsh–Hadamard 稀疏谱 — Poelwijk et al., **Nat. Commun. 2019**;Brookes et al., **PNAS 118, 2022**;Aghazadeh et al.(Epistatic Net), **Nat. Commun. 2021**.
- ECNet(显式残基对相依,专攻高阶)— Luo et al., **Nat. Commun. 2021**.
- ProteinNPT(非参 Transformer,低标签联合建模序列+标签)— Notin et al., **NeurIPS 2023**.
- **笼内可行性:可直接用(换 surrogate,零新增测量)。破顶潜力:单用为中,与主动补测合用为高。** 这是唯一能在**已测**组合上"看见"交互的表征族。但对本项目的真峰,其前提只部分成立:构成真峰的第三对组合 D0Q+S17E 在数据表中无任何实测(见 §0 修正),故本族解决的是「已测组合上的交互表达」这一半,无法凭空学到缺测的那一对。

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
| 2 | **代理换上位感知表征**(pairwise/FM/ECNet/ProteinNPT) | ✅ | ✅ 高(零新增测量) | 高 | 最省力,但只解决因素 2;缺测的 D0Q+S17E 需靠提名 A 补(见 §0 修正) |
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
完全不改现有主动学习环(同池、同 288 预算、同 HD 门禁、同采集),**只把加性 Ridge/kNN/GBM 换成 pairwise 交互 / 因子分解机 / ECNet-style 代理**,在同一 cold-start 上训练,先做确定性诊断:**真峰门内预测排名是否从 #1283 降进可达区(≤288)?** 为何仍值得先做:成本近零、answer-agnostic,能干净地**量化因素 2 单独的贡献**。但按 §0 修正,它不足以让真峰必然进可达区——D0Q+S17E 缺测属因素 1,换 surrogate 解决不了。故本提名的预期产出是「加性表达力值多少排名」,不是「破顶」;真要破顶须与提名 A(主动补测二阶)合用。

**提名 A(按 §0 修正已升为必需项,不再是 B 的备选)—— 主动双突变扫描 + 交互外推(MULTI-evolve in-silico 复刻)。** 理由:真峰所需的 D0Q+S17E 在数据中缺测,这是因素 1,只有主动补测这一路能解决。
✔已核实蓝本:**Tran et al., "Rapid directed evolution guided by protein language models and epistatic interactions," Science 392(6798):eaea1820, 2026-05-07**(Arc Institute;Hie/Hsu)——实测 top~15 突变全部两两组合(~100-200 doubles)训模型外推到高阶,做到 5-7 突变、最高 256 倍。in-silico 复刻:answer-agnostic 选位点(如实测单突变边际 top + 全 VR 覆盖,**禁用 PLM 自然度筛**)→ 池内测双突变 → 浅层交互模型外推打分 HD3 → 末轮验证。预算 ~120-250 落在 288 内。**风险预登记:** 若峰的构成突变纯高阶/sign-epistasis(成对投影不显),双突变扫描仍可能漏;需先查"该峰在成对投影上是否显正上位"作可行性 gate。

**提名 C(可选,做成因归因)—— 信任域 + viability-gated 采集 + 回溯游走。**
用 TuRBO/BO-EVO/ODBO 信任域 + 可行性门禁替换自由探索,允许 HD 在 ≤4 门禁内先升后降(间接路径,Wu 2016)。与 B 组合可完整归因:平台期到底是"采集踩空/死蛋白陷阱"还是"表征看不见峰"。

**总纲(2026-09-12 按 §0 修正重写):** 现有所有变体都困在"加性表征 + 自然度先验"两条对本峰无效的轴上。但破顶需要的不止换表征:真峰所需的 D0Q+S17E 组合在数据中**缺测**,这一半只有主动补测能解决。**因此 A 与 B 是互补的两半,不是二选一。建议顺序:先做 B(成本近零),用它量化"加性表达力值多少排名";无论 B 结果如何都要做 A,因为缺测那一对不会因换模型而出现。** 若 B 之后真峰仍在可达区外,那正是因素 1 在起作用的正面证据,而非 B 失败。

---

## 附:引用核实状态
- ✔已核实:MULTI-evolve(Science 2026,PMC12991030);EVOLVEpro(Science 2025);§0 本仓数据观察。
- 其余引用来自文献扫描,大部分为知名工作(EVmutation/ECNet/ProteinNPT/TuRBO/GFlowNet/ISM/EVE/Tranception 等),但**正式写入最终报告前应逐条核对**;明确标"待核实":cartesian_ddg 原始书目(Park et al. 2016 JCTC?)、"Higher-order epistasis creates idiosyncrasy"(Thornton 实验室)、WH 扩展 PLOS Comput Biol 2024、Signal Transduct Target Ther 2026 整合框架作者。
