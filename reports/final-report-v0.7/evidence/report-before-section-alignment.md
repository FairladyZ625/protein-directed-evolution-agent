# 面向定向进化的可审计科学智能体

<div class="metadata">预测工具、知识约束与实验反馈的受控研究<br>Zeyu Li · 研究报告 v0.6 · 2026 年 9 月 13 日</div>

::: {.abstract}
**摘要**　我们构建了连接预测、文库设计与测量反馈的定向进化系统，在 GB1 和 AAV 固定测量池上研究表征选择、知识配置与语言模型的作用。训练集内选择正则化参数后，ESM-2 在 GB1 跨距离测试中优于 one-hot；稀疏冷启动与 AAV 消融显示，知识配置能够改变候选组成及搜索结果。事件级对照进一步区分了语言模型的自述、工具动作与实际送测选择。研究表明，科学 Agent 的合理定位是组织预测工具与实验、依据观测修订假设，并以真实决策及测量结果评价其作用。
:::

![图 1　GB1 五角色与实际选样闭环。预测器评分进入批次选择；Critic 判定和评语进入审计记录。角色化执行把假设、候选与测量连接起来。完整接口与消费者接线见附录 C。](figures/f03_workflow_imagegen.png)

::: {.cols}
## 1　研究问题与贡献

定向进化在有限实验预算内，通过变体构建、测量和迭代选择寻找目标性质。[1–3] 我们将过程组织成可回放的计算实验：代理模型负责数值预测，知识配置约束或引导搜索，Agent 组织假设与工具调用，Oracle 揭示封存的实测标签。

本研究形成了三类结果：控制特征尺度与正则化的预测工具比较；分冷启动和候选范围的闭环对照；连接模型误差、工具动作与送测集合的行为分析。正文呈现这些研究发现，附录提供完整配置、数据表和复现资料。

我们关注三个相互连接的问题：在目标分布上，哪种预测工具更适合排序候选；在初始观测较少时，怎样组织有限预算；获得与预期不符的测量后，研究者接口是否真的改变了下一步选择。每个问题分别落到模型测试、配对搜索和事件级对照。

这样的设计使候选发现与机制解释可以相互支撑。实验既记录高分序列，也保留失败推荐的预测与实测差异；研究判断沿着数据、假设、工具和测量逐步建立，而不依赖模型对自身能力的描述。
:::
<!-- PAGE -->
## 2　预测工具的比较应对齐外推目标

![图 2　GB1 跨突变距离测试的 Ridge α 扫描。曲线为测试 Spearman，菱形表示训练集内验证所选 α 对应的测试值；不按测试峰选参。完整八组曲线与预测器阶梯见附录 B。](figures/f02_alpha.png)

| 测试划分 | one-hot raw / std | ESM-2 raw / std |
|---|---:|---:|
| random | 0.4840 / 0.4840 | 0.4893 / 0.4916 |
| HD extrapolation | 0.3588 / 0.3530 | 0.4039 / 0.4090 |

::: {.cols}
### 2.1　统一的计算实验协议

GB1 包含四个可变位点的 149,361 条实测组合；AAV 使用 28 残基窗口的替换子集。[4–6] 每轮先根据已测集合训练预测器并冻结提名，再由查表 Oracle 返回测量，新标签进入下一轮训练。

GB1 设置随机 5,000 条、HD≤2 的 2,168 条和 HD≤1 的 77 条三种冷启动，预算为 96×3；AAV 以 HD≤2 起步，预算为 48×6。我们分别报告新增最佳适应度、强命中数及实际查询量。AAV 候选池峰 8.4162 低于初始已知最优 9.5365，因此“达峰”表示找到新增池的峰。阈值、重复数和数据范围统一列于附录 A。

### 2.2　表征收益与参数配置分开检验

ESM 从蛋白质序列中学习上下文表征。[12,13] 不同特征的尺度改变了 Ridge 惩罚项的实际作用，直接使用相同 α 并非公平比较。我们对每种表征、划分与预处理分别扫描 α，在训练集内留出验证选择，再用外层测试评价。

调参后，ESM-2 在 HD 外推中比 one-hot 高 0.0451（raw）和 0.0560（std），方向在两种预处理下相同。随机划分的差距更小。这为在外推任务中使用蛋白质表征提供了具体依据，也说明训练协议本身是模型比较的重要组成部分。

Ridge、XGBoost 与 MLP 的阶梯测试则呈现指标分工：Ridge 的秩相关最高，MLP 的数值误差与 top-k 重合率更好。工具选择应对应后续采集目标；离线预测收益还要通过实际使用该工具的闭环运行来检验。[7–11,14–16]
:::
<!-- PAGE -->
## 3　角色分工与跨轮反馈

![图 3　三类跨轮信息通道。统计更新使预测器吸收新标签，单轮语言接口组织当前菜单，自主研究路径保留消息历史并调用有状态工具。具体输入输出见附录 C。](figures/f04_feedback_imagegen.png)

::: {.cols}
### 3.1　让假设成为可执行的文库

五角色流水线先由 Data Analyst 汇总已测替换与适应度；Hypothesis Generator 组织替换菜单；Mutation Designer 将各位点替换组合为可测文库；Fitness Evaluator 输出预测均值和方差；Scientific Critic 记录规则判定与预算内的评语。

GB1 默认每个位点最多选择八种替换，再与野生型残基组合，交给模型评分。无知识策略使用均值排序，知识配置加入不确定性探索与 BLOSUM 替换先验。[18,23] 假设因此可以通过文库改变实验的搜索范围。

冻结 GB1 路径的 selector 读取全部已评分 candidates，而不是 Critic 的 accepted 子集。因此正文将其知识作用描述为实际生效的采集配置；判定与最终选择的关系详见附录 C、D。AAV 自主路径则把 HD/BLOSUM 门禁用于候选池及测试验证。

### 3.2　闭环依赖哪些信息

每轮测量扩充训练集，下一轮重新拟合 surrogate。这条统计反馈在确定性运行中同样成立。GB1 的语言假设接口只接收当轮替换名称菜单；AAV 自主接口保留消息历史，并通过分析、组合、测试和知识查询工具读取更新后的状态。

两种接口提供的信息条件不同。保留对话帮助延续上下文，重拟合更新数值预测，而逐变体残差卡将“原先判断与后来测量的差异”显式交给下一轮决策者。把这三条通道分开，才能检验每项能力实际贡献了什么。

### 3.3　知识既服务选样，也服务解释

HD 与 BLOSUM 表达显式搜索范围和替换先验；由实测数据形成的共现与富集关系提供候选上下文。经验图谱把序列、观测和建议连接起来，用于提出可检验的组合假设。它所记录的关联受采样覆盖影响，应与实验对照共同解释。
:::
<!-- PAGE -->
## 4　GB1：冷启动与实际预算决定如何读结果

![图 4　GB1 不同冷启动的新增最佳适应度。随机曲线为五 seed 均值±总体标准差，其余策略为 seed 42；虚线为全局最优 8.761966。完整预算及语言调用对照见附录 D。](figures/f06_regimes.png)

| 冷启动 | 随机：最高值，均值±σ | 贪心：最高值 / 强命中 | 无知识：最高值 / 强命中 | 知识：最高值 / 强命中 |
|---|---:|---:|---:|---:|
| easy | 3.6742 ± 0.8200 | 8.7620 / 81 | 8.7620 / 95 | 8.7620 / 86 |
| hard | 4.6113 ± 1.8501 | 8.7620 / 43 | 8.7620 / 50 | 8.7620 / 65 |
| sparse | 4.0461 ± 0.7203 | 5.7720 / 29 | 5.7720 / 27 | 8.7620 / 33 |

::: {.cols}
### 4.1　信息覆盖改变策略分层

easy 中三条模型策略均达到全局最优，此时最高值已经饱和，批次统计继续提供区分：无知识策略的强命中为 95，知识策略为 86；后者的有益命中却更多，250 对 244。高阈值尾部产量与优于野生型的广度回答不同问题。

sparse 只有 77 条低阶测量。贪心与无知识策略停在 5.7720，知识策略依次达到 6.0421、7.5547 和 8.7620。这一单 seed 分层提示：当均值排序的观测支持较弱时，探索项与先验的联合配置可能帮助搜索转移。其组成项和稳定性应通过后续因子消融与重复检验。

### 4.2　语言接入首先改变了文库和吞吐

GB1 live-LLM 与 hard 使用相同名义预算，但无知识和知识臂实际只完成 105、197 次查询，对照均为 288。绝对强命中从 50/65 降到 32/59；按实际查询归一化后，比例却由 17.36%/22.57% 升到 30.48%/29.95%。

同条件复现中，两条 LLM 臂又各只完成 5 次查询。这将问题定位到语言菜单、回退和有效文库的接口：终局产量差包含预算使用差异，不能直接解释为候选质量或独立知识收益。完整逐轮提名、调用成功与 Critic 消费路径审计置于附录 D。
:::
<!-- PAGE -->
## 5　AAV：知识配置与采集目标的权衡

![图 5　AAV atomic 消融，seed 0、48×6 次查询。知识配置提高本次运行的最佳值和强命中产量，并改变候选阶数组成。完整 atomic/checkpoint 对照和固定池采集矩阵见附录 E。](figures/f08_aav_ablation.png)

| 对照 | 无知识 Agent | 知识 Agent |
|---|---:|---:|
| 新增最佳 fitness | 6.1862 | 7.8290 |
| 强命中（atomic） | 69 | 166 |
| 平均提名 HD | 8.53 | 3.42 |
| 实际查询 | 288 | 288 |

::: {.cols}
### 5.1　约束改变了被测序列

AAV 的较宽搜索空间使训练覆盖成为突出问题。知识臂将预算限制在 HD≤4、BLOSUM≥0 的区域，提名由 167 条 HD3 与 121 条 HD4 构成；与无知识臂的集合交集为 65，Jaccard 系数为 0.1272。

该配置相对无知识臂提高最佳值 1.6428，并增加 97 个强命中。它改变的是实际送测组成，表明搜索范围与先验可以作为实验设计变量。这里观测到的是联合配置的效果；两种执行模式与完整策略表分别保留于附录。

### 5.2　找峰与积累高分候选并不等价

固定预测器、统一候选门禁后，Mean 产生 166 个强命中但停在 7.8290；UCB 3 找到 8.4162 的候选峰，强命中为 128。较强探索在这次配置中换来了峰值发现，同时改变了批次产量。[18,19]

探索参数也没有单调收益：UCB 0.5、1、2 均停在 6.5309。随机采集的 30 seed 实验显示，Alternating 与 Gaussian Thompson 分别达峰 2 次和 3 次。确定性配置的重复记录对应同一轨迹；独立轨迹数、误差范围和达峰区间在附录 E 中完整呈现。

这些结果把策略选择转化为明确的研究决策：是希望积累较多高质量候选，还是愿意为稀有峰投入探索预算。Agent 应帮助研究者明确目标、选择工具并解释权衡，而不是用一个最终分数概括全部表现。
:::
<!-- PAGE -->
## 6　组合效应：发现高峰与解释高峰

![图 6　AAV 候选峰的局部组合。A=D0Q，B=S17E，C=V18A；AB 缺测保留为 NA。ABC 实测值高于由 WT 与三个单点推得的加性预期。完整值表和跨阶分析见附录 F、G。](figures/f11_epistasis.png)

::: {.cols}
### 6.1　外推验证揭示模型适用范围

AAV 用 0..1 阶训练预测 HD2，测试 Spearman 为 0.8749；用 0..2 阶训练预测 HD3，测试为 0.6155，低于该训练范围内的留出验证 0.9094。评价分布应与目标阶数对应，随机留出能力不能替代跨阶能力。

测量拓扑也影响解释。AAV HD3 变体中，仅 31.17% 拥有全部直接 HD2 组成变体的测量；HD4 的对应比例为 2.24%。GB1 的覆盖密集得多。完整按阶数分布、训练规模与覆盖定义见附录 F。

### 6.2　一组可以逐项追溯的上位效应

ABC 的单点加性预期为 6.3154，实测为 8.4162，偏离 +2.1008。这说明单点相加低估了该组合，为进一步研究相互作用提供了明确对象。[17]

AB 在整个查表池中缺失，因此上述差值应称为相对单点加性的偏离，而不是已经分离出的纯三阶系数。缺失对照影响机制识别，却不阻止找到 ABC 本身：固定采集矩阵中的 UCB 3 已在第 3 轮达峰。

若目标是发现池内高值，可继续改进排序与采集；若目标是解释局部组合机制，则需要补测缺失对照或明确采用统计假设。两种任务需要不同的证据。

### 6.3　失败推荐同样需要进入反馈

局部分析中，ABC 的模型均值为 6.3668，在门禁池中排第 426；而首批 48 个高预测候选平均预测 11.3065、平均实测 2.8838。模型同时存在低估有效组合与高估其他区域的情况。

因此下一轮诊断应看到完整送测批次的预测—测量配对，而不只看到成功的 top-10。逐变体残差让失败案例具有具体序列、数值与背景，为研究者修改实验提供对象。
:::
<!-- PAGE -->
## 7　研究者定位：借助工具检验先验

![图 7　知识先验与候选组成。左：AAV 位点熵与候选峰的三个替换位置；右：GB1 easy 知识策略三轮 top-10 记录的残基集中度。保守性为事后分析；统计量与坐标约定见附录 G。](figures/f05_knowledge.png)

::: {.cols}
### 7.1　自然序列先验需要实测检验

ESM-2 的逐位 masked-token 熵提供一种保守性代理。AAV 候选峰中的 D0Q 位于该窗口最保守的位置，V18A 为第 4，S17E 为第 26。若用强保守性规则提前排除替换，可能移除组成有利组合的候选。

这也说明，蛋白质序列的统计规律与特定 assay 的功能并非同一目标。ESM 可以改善表征，同时仍需要任务数据和实验校准；第二章的预测收益与第六章的组合失配能够同时成立。

### 7.2　Agent 负责组织研究过程

通用 LLM 的训练主要围绕语言与知识表征；特定环境下的序列—功能映射需要领域数据、归纳偏置与测量校准。直接让通用语言生成承担适应度数值预测，会引入任务目标与训练目标之间的错配。

我们据此将 Agent 定位为研究者接口：选择预测工具，检查其适用范围，组织候选与对照实验，并在新证据到来时修订假设。人类研究者同样依赖模型和测量判断序列功能，专业性体现在提出有区分力的实验、发现误差并处理冲突证据。

工具型科学 Agent、自动化实验和自主实验室提供了相关研究背景。[20–22,30] 在本项目中，评价这一能力要追踪新观测是否被读取、工具参数是否改变，以及最终是否产生不同的送测序列。结构预测、序列设计和生成模型可以作为未来工具扩展，[24,26–29] 多目标采集则需显式定义功能与成本之间的权衡。[25]
:::
<!-- PAGE -->
## 8　从残差反思到实际实验选择

![图 8　V0.8 残差反馈与行为检验。提名时预测与测量成对记录，前轮证据进入研究者接口；是否改变实验选择通过实际批次核验。首轮完整证据与后续因子设计见附录 H、I。](figures/f12_v08_imagegen.png)

| AAV 首轮冒烟，seed 42 | control | reflexion |
|---|---:|---:|
| 跳转工具触发轮次 | 5 | 2、5 |
| 六轮送测集合交集 | 48/48 × 6 | 与 control 相同 |
| 查询 / 强命中 / 新增最佳值 | 288 / 157 / 8.4162 | 288 / 157 / 8.4162 |

::: {.cols}
### 8.1　区分信息、动作和送测行为

两臂均记录残差，只有 reflexion 臂将前轮证据注入下一轮 prompt。反思臂提前到第 2 轮调用跳转，但事件中的簇签名大小为 0；两臂六轮送测集合完全一致。该次调用改变了工具动作，却没有在纯利用构型下改变实验选择。

反思臂的总结声称依据残差排除低适应度背景，而实际送测集合与对照相同。这使研究者能力的评估有了具体判据：语言中的证据修订，应当与执行层的选择变化分别核验。

首轮 n=1 用于定位机制，不承担反思普遍有效或无效的结论。其 240 秒超时下的轮次成功率，也不与 GB1 90 秒 Critic 尝试成功率作直接改善比较。完整调用条件和后续构型×反思的设计置于附录，后续实验数据由报告 v0.7 单独整合。

### 8.2　研究结论

预测工具需要公平的训练协议和目标分布验证；知识配置应与初始覆盖、搜索空间和实验目标一起设计；科学 Agent 的作用应落实到可追溯的决策与测量。

本阶段交付了上述问题的执行链、对照结果与失败案例。下一步重点是使研究者接口拥有能够实际影响批次的操作空间，并在一致预算和独立重复下检验其是否利用新证据改善实验选择。
:::
<!-- PAGE -->
<!-- REFERENCES -->
## 参考文献

::: {.refs}

[1] YANG K K, WU Z, ARNOLD F H. Machine-learning-guided directed evolution for protein engineering[J]. Nature Methods, 2019, 16(8): 687-694. [DOI: 10.1038/s41592-019-0496-6](https://doi.org/10.1038/s41592-019-0496-6)

[2] STEMMER W P C. Rapid evolution of a protein in vitro by DNA shuffling[J]. Nature, 1994, 370(6488): 389-391. [DOI: 10.1038/370389a0](https://doi.org/10.1038/370389a0)

[3] REETZ M T, CARBALLEIRA J D. Iterative saturation mutagenesis (ISM) for rapid directed evolution of functional enzymes[J]. Nature Protocols, 2007, 2(4): 891-903. [DOI: 10.1038/nprot.2007.72](https://doi.org/10.1038/nprot.2007.72)

[4] WU N C, DAI L, OLSON C A, et al. Adaptation in protein fitness landscapes is facilitated by indirect paths[J]. eLife, 2016, 5: e16965. [DOI: 10.7554/elife.16965](https://doi.org/10.7554/elife.16965)

[5] BRYANT D H, BASHIR A, SINAI S, et al. Deep diversification of an AAV capsid protein by machine learning[J]. Nature Biotechnology, 2021, 39(6): 691-696. [DOI: 10.1038/s41587-020-00793-4](https://doi.org/10.1038/s41587-020-00793-4)

[6] DALLAGO C, MOU J, JOHNSTON K E, et al. FLIP: Benchmark tasks in fitness landscape inference for proteins[C]//Proceedings of the Neural Information Processing Systems Track on Datasets and Benchmarks. 2021, 1. [会议原文](https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/file/2b44928ae11fb9384c4cf38708677c48-Paper-round2.pdf)

[7] NOTIN P, KOLLASCH A, RITTER D, et al. ProteinGym: Large-Scale Benchmarks for Protein Fitness Prediction and Design[C]//Advances in Neural Information Processing Systems. 2023, 36. [会议原文](https://proceedings.neurips.cc/paper_files/paper/2023/hash/cac723e5ff29f65e3fcbb0739ae91bee-Abstract-Datasets_and_Benchmarks.html)

[8] SARKISYAN K S, BOLOTIN D A, MEER M V, et al. Local fitness landscape of the green fluorescent protein[J]. Nature, 2016, 533(7603): 397-401. [DOI: 10.1038/nature17995](https://doi.org/10.1038/nature17995)

[9] HOERL A E, KENNARD R W. Ridge Regression: Biased Estimation for Nonorthogonal Problems[J]. Technometrics, 1970, 12(1): 55-67. [DOI: 10.1080/00401706.1970.10488634](https://doi.org/10.1080/00401706.1970.10488634)

[10] FRIEDMAN J H. Greedy function approximation: A gradient boosting machine[J]. The Annals of Statistics, 2001, 29(5): 1189-1232. [DOI: 10.1214/aos/1013203451](https://doi.org/10.1214/aos/1013203451)

[11] WITTMANN B J, YUE Y, ARNOLD F H. Informed training set design enables efficient machine learning-assisted directed protein evolution[J]. Cell Systems, 2021, 12(11): 1026-1045.e7. [DOI: 10.1016/j.cels.2021.07.008](https://doi.org/10.1016/j.cels.2021.07.008)

[12] RIVES A, MEIER J, SERCU T, et al. Biological structure and function emerge from scaling unsupervised learning to 250 million protein sequences[J]. Proceedings of the National Academy of Sciences, 2021, 118(15): e2016239118. [DOI: 10.1073/pnas.2016239118](https://doi.org/10.1073/pnas.2016239118)

[13] LIN Z, AKIN H, RAO R, et al. Evolutionary-scale prediction of atomic-level protein structure with a language model[J]. Science, 2023, 379(6637): 1123-1130. [DOI: 10.1126/science.ade2574](https://doi.org/10.1126/science.ade2574)

[14] BISWAS S, KHIMULYA G, ALLEY E C, et al. Low-N protein engineering with data-efficient deep learning[J]. Nature Methods, 2021, 18(4): 389-396. [DOI: 10.1038/s41592-021-01100-y](https://doi.org/10.1038/s41592-021-01100-y)

[15] FRAZER J, NOTIN P, DIAS M, et al. Disease variant prediction with deep generative models of evolutionary data[J]. Nature, 2021, 599(7883): 91-95. [DOI: 10.1038/s41586-021-04043-8](https://doi.org/10.1038/s41586-021-04043-8)

[16] HOPF T A, INGRAHAM J B, POELWIJK F J, et al. Mutation effects predicted from sequence co-variation[J]. Nature Biotechnology, 2017, 35(2): 128-135. [DOI: 10.1038/nbt.3769](https://doi.org/10.1038/nbt.3769)

[17] POELWIJK F J, SOCOLICH M, RANGANATHAN R. Learning the pattern of epistasis linking genotype and phenotype in a protein[J]. Nature Communications, 2019, 10(1): 4213. [DOI: 10.1038/s41467-019-12130-8](https://doi.org/10.1038/s41467-019-12130-8)

[18] SRINIVAS N, KRAUSE A, KAKADE S M, et al. Information-Theoretic Regret Bounds for Gaussian Process Optimization in the Bandit Setting[J]. IEEE Transactions on Information Theory, 2012, 58(5): 3250-3265. [DOI: 10.1109/tit.2011.2182033](https://doi.org/10.1109/tit.2011.2182033)

[19] JONES D R, SCHONLAU M, WELCH W J. Efficient Global Optimization of Expensive Black-Box Functions[J]. Journal of Global Optimization, 1998, 13(4): 455-492. [DOI: 10.1023/a:1008306431147](https://doi.org/10.1023/a:1008306431147)

[20] BRAN A M, COX S, SCHILTER O, et al. Augmenting large language models with chemistry tools[J]. Nature Machine Intelligence, 2024, 6(5): 525-535. [DOI: 10.1038/s42256-024-00832-8](https://doi.org/10.1038/s42256-024-00832-8)

[21] BOIKO D A, MACKNIGHT R, KLINE B, et al. Autonomous chemical research with large language models[J]. Nature, 2023, 624(7992): 570-578. [DOI: 10.1038/s41586-023-06792-0](https://doi.org/10.1038/s41586-023-06792-0)

[22] KING R D, ROWLAND J, OLIVER S G, et al. The Automation of Science[J]. Science, 2009, 324(5923): 85-89. [DOI: 10.1126/science.1165620](https://doi.org/10.1126/science.1165620)

[23] HENIKOFF S, HENIKOFF J G. Amino acid substitution matrices from protein blocks[J]. Proceedings of the National Academy of Sciences, 1992, 89(22): 10915-10919. [DOI: 10.1073/pnas.89.22.10915](https://doi.org/10.1073/pnas.89.22.10915)

[24] JUMPER J, EVANS R, PRITZEL A, et al. Highly accurate protein structure prediction with AlphaFold[J]. Nature, 2021, 596(7873): 583-589. [DOI: 10.1038/s41586-021-03819-2](https://doi.org/10.1038/s41586-021-03819-2)

[25] DEB K, PRATAP A, AGARWAL S, et al. A fast and elitist multiobjective genetic algorithm: NSGA-II[J]. IEEE Transactions on Evolutionary Computation, 2002, 6(2): 182-197. [DOI: 10.1109/4235.996017](https://doi.org/10.1109/4235.996017)

[26] DAUPARAS J, ANISHCHENKO I, BENNETT N, et al. Robust deep learning–based protein sequence design using ProteinMPNN[J]. Science, 2022, 378(6615): 49-56. [DOI: 10.1126/science.add2187](https://doi.org/10.1126/science.add2187)

[27] WATSON J L, JUERGENS D, BENNETT N R, et al. De novo design of protein structure and function with RFdiffusion[J]. Nature, 2023, 620(7976): 1089-1100. [DOI: 10.1038/s41586-023-06415-8](https://doi.org/10.1038/s41586-023-06415-8)

[28] ANISHCHENKO I, PELLOCK S J, CHIDYAUSIKU T M, et al. De novo protein design by deep network hallucination[J]. Nature, 2021, 600(7889): 547-552. [DOI: 10.1038/s41586-021-04184-w](https://doi.org/10.1038/s41586-021-04184-w)

[29] MADANI A, KRAUSE B, GREENE E R, et al. Large language models generate functional protein sequences across diverse families[J]. Nature Biotechnology, 2023, 41(8): 1099-1106. [DOI: 10.1038/s41587-022-01618-2](https://doi.org/10.1038/s41587-022-01618-2)

[30] HÄSE F, ROCH L M, ASPURU-GUZIK A. Next-Generation Experimentation with Self-Driving Laboratories[J]. Trends in Chemistry, 2019, 1(3): 282-291. [DOI: 10.1016/j.trechm.2019.02.007](https://doi.org/10.1016/j.trechm.2019.02.007)

:::
<!-- PAGE -->
## 附录 A　完整数据与评测协议

| 维度 | GB1 | AAV |
|---|---|---|
| 研究对象 | 四个可变位点，WT 为 VDGV | 28 残基变异窗口 |
| 数据来源 | 组合突变适应度测量 [4] | 衣壳变体测量、FLIP 清洗子集 [5,6] |
| 冷启动 | easy 5,000；hard 2,168；sparse 77 | HD≤2，10,433 条 |
| 单轮预算 × 轮数 | 96 × 3 | 48 × 6 |
| 强命中阈值 | fitness ≥ 4.0 | 原消融 ≥ 2.615913579904 |
| 查询返回 | 固定池已有测量 | 固定池已有测量 |

::: {.cols}
### 先预测，再揭示测量

每轮先根据已测集合训练模型并冻结提名，再由查表 Oracle 揭示这些序列的适应度。模型与候选选择过程使用当时已测标签；完整测量表承担离线模拟实验的功能。GB1 理论组合数为 160,000，实测池包含 149,361 条，缺测的 10,639 条不作为可查询候选。

AAV 使用可对齐的替换子集；候选为冷启动之外的 HD>2 序列。这里的 HD 是相对参考序列的 Hamming 距离。知识消融允许无知识臂访问较宽的候选范围，而固定预测器矩阵对所有配置使用同一 HD≤4、BLOSUM≥0 的门禁。两类实验分别回答“约束整个搜索空间”和“在相同空间中改变采集”的问题。

### 把找峰与批次产量分开

本文报告新增查询中的最高适应度、累计 top-10 均值、强命中数和实际查询数。GB1 有益命中定义为 fitness>1.0，即优于野生型。最佳值回答是否找到高峰，命中数回答有限预算产生多少候选，命中比例则以实际查询数为分母。

AAV 候选池最高值为 8.416205，但冷启动中已有适应度 9.536457 的序列。因此 AAV 的“达峰”指找到新增候选池的峰，不表示超过初始已知最优。该定义在后文统一沿用。

### 重复与版本

GB1 随机策略报告五个 seed 的均值与总体标准差；三条模型策略为 seed 42 的轨迹。AAV 知识消融为 seed 0，atomic 与 checkpoint 是执行模式。固定预测器实验区分确定性重复与随机采集的 30 个 seed。图表只在实际具有随机重复的地方绘制误差棒。

报告 v0.6 是文档版本；agentic-v0.5、v0.6、v0.7 与 V0.8 是实验或代码版本，二者不一一对应。历史 v0.6 与 v0.7 从 v0.5 分叉，故其结果应各自与共同基线比较。本文冻结既有产物，并单列新收到的 V0.8 第一轮证据。
:::
<!-- PAGE -->
## 附录 B.1　预测器阶梯与评价指标

![图 S1　GB1 one-hot 预测器阶梯。相同 5,000/2,000/2,000 训练、验证与测试划分下，排序相关与平方误差呈现不同的模型优势。来源：evidence/predictors.json。](figures/f01_predictors.png)

| 模型 | 测试 Spearman | 测试 Pearson | 测试 MSE | top-k 重合率 |
|---|---:|---:|---:|---:|
| Ridge | 0.5119 | 0.4116 | 0.1017 | 0.50 |
| XGBoost | 0.5034 | 0.6013 | 0.0780 | 0.50 |
| MLP | 0.4499 | 0.8191 | 0.0410 | 0.65 |

::: {.cols}
### 排序与数值误差提供互补证据

Ridge 的测试 Spearman 最高，MLP 的 Pearson、MSE 与 top-k 重合率更好。这个结果表明，“最佳预测器”依赖决策目标：若采集只使用排序，秩相关更直接；若比较预期收益或校准不确定性，数值误差同样重要。蛋白质基准也强调多种测量任务和评价方式的区别。[7,8]

Ridge 提供可检查的线性基线；梯度提升与 MLP 引入非线性拟合能力。[9,10] 模型复杂度增加并未在本次划分中同步提升所有指标。因此系统保留预测器接口，通过一致的数据划分与指标表选择工具，而不是预先把复杂模型当作优胜者。

### 不确定性需要实际变化

GB1 预测链采用 bootstrap 重采样训练多个估计器，以预测分歧构成候选方差。该做法使相同模型族能够输出均值之外的信息，为探索项提供输入。当前表中三类预测器均具有非零方差范围。

模型分歧反映重采样和拟合的敏感性，并非经过独立校准的概率保证。我们将其作为采集启发式，与均值排序进行对照；这样可以直接观察探索项是否改变实际批次和最终产量。低样本蛋白质工程中的模型不确定性和表征选择，需要结合具体实验预算进行评价。[11]

### 预测器验证与闭环验证衔接

离线测试回答已定义分布上的预测能力，闭环实验回答选样后能否取得更好的观测。模型可能在总体误差上更优，却在高分尾部或外推区间排序失准。后续结果因此同时保留预测表、逐轮轨迹与候选级证据，避免用一个相关系数代替整个搜索过程。
:::
<!-- PAGE -->
## 附录 B.2　完整正则化扫描

![图 S2　全部八组 Ridge 扫描。灰色虚线为训练集内验证 Spearman，蓝线为测试 Spearman；点标记验证所选 α 对应的测试值。各面板纵轴独立，便于观察参数敏感性；不以测试峰选择参数。来源：evidence/alpha.json。](figures/fs1_alpha_full.png)

::: {.cols}
完整曲线保留随机划分与 HD 外推、raw 与 standardized、one-hot 与 ESM-2 的全部组合。读图时先比较验证选择得到的测试值，再观察参数敏感性；仅比较曲线中的最高测试点会改变训练协议。


:::



| 表征 | 划分 | 预处理 | 验证所选 α | 测试 Spearman |
|---|---|---|---:|---:|
| one_hot | random | raw | 0.01 | 0.4840 |
| one_hot | random | std | 10 | 0.4840 |
| esm2 | random | raw | 10 | 0.4893 |
| esm2 | random | std | 10000 | 0.4916 |
| one_hot | HD 外推 | raw | 10 | 0.3588 |
| one_hot | HD 外推 | std | 10000 | 0.3530 |
| esm2 | HD 外推 | raw | 1 | 0.4039 |
| esm2 | HD 外推 | std | 10000 | 0.4090 |

<div class="note">α∈{0.01,0.1,1,10,100,1000,10000}。原实现的标准化器在外层训练集拟合，内层80/20留出选择α，再在全训练集重拟合；外层测试标签不参与选择。表征比较范围为 Ridge，不延伸为所有模型族的结论。</div>
<!-- PAGE -->
## 附录 C　角色接口与实际消费者接线

::: {.cols}
### 分析、假设与文库设计

Data Analyst 读取已测序列和适应度，汇总位点及替换信息。代码中的 position gains 是含相应位置突变样本的平均适应度，并不是以野生型为对照识别出的因果增益。这个汇总为设计提供经验线索。

Hypothesis Generator 输出替换菜单。确定性路径按已测支持选取每个位点的候选替换；接入 LLM 时，由语言接口从菜单组织组合建议。Library Designer 将各位置替换与野生型残基做笛卡尔积，去除全野生型、冲突或不可测组合。GB1 默认每位点最多八种替换，形成至多 9⁴ 个含野生型的原始组合，再经过集合处理得到可评估文库。

这使“假设”具有执行含义：它改变哪些序列进入下一步评估，而不只是附在结果旁的一段解释。

### 评分、规则与批次选择

Fitness Evaluator 用当轮代理模型输出文库中各候选的预测均值和方差。Critic 则运行确定性知识规则，并对预算内、通过规则的候选请求自然语言评语。默认每轮最多十条 LLM 评语，按传入候选顺序分配；这不是对全库进行十条“最高分专家评审”。

冻结 GB1 consumer 的一个关键接线事实是：selector 读取 `candidates`，而不是 `accepted`。因此规则判定在该 consumer 中承担审计角色，实际选择由采集分数和可测、未测条件驱动。我们据此描述结果中的知识作用，不将所有 Critic 拒绝都解释为已生效的筛除。

无知识策略按均值排序；知识策略使用均值 + 0.75×标准差 + 0.30×BLOSUM 得分。BLOSUM 提供替换先验，[23] 探索项鼓励关注模型分歧较大的候选。[18] 排序完成后冻结批次，再交给 Oracle 返回测量。

### 统计学习形成基础闭环

每轮查询产生新标签，扩充已测集合，并在下一轮重新拟合 surrogate。即使语言端口采用单轮调用，这条反馈仍持续工作。GB1 sparse 轨迹中，知识策略的新增最佳值依次为 6.0421、7.5547 和 8.7620；它体现了采集与更新相互作用的执行结果。

反馈的可解释性来自记录：当时掌握了哪些数据，模型如何评分，哪些候选被提名，以及实验返回了什么。事件流把这些步骤保留下来，使最终指标可以回到产生它的决策过程。

### 两条语言路径有不同的信息条件

GB1 的 LLM 假设接口虽然接收 report 参数，但冻结实现实际发给模型的是替换名称菜单，没有传入完整分析数值，也未携带历史消息。该接口适合检验“语言模型组织菜单”对文库的影响，不能与能够读取历轮残差的研究者接口混为一谈。

AAV 的自主研究路径保留 message history，由模型调用 `analyze_measured`、文库构造、测试及知识图查询工具。分析工具暴露已测高分序列、富集信号和模型验证结果；回溯配置还提供轨迹与停滞状态。每轮工具状态随新观测更新。

### 历史、测量与反思卡的区别

保留对话历史使模型能够延续上下文；统计重拟合使预测器吸收新标签；结构化残差卡则把“原先预测与后来测量的差异”显式交给下一轮决策者。三者是不同的实现能力。

V0.8 在这一基础上新增逐变体的提名时预测、测量与残差事件，并将异常观测注入反思臂的下一轮 prompt。正文第八节单列首轮冒烟结果，用实际批次比较检验这条新增通道是否产生行为效果。
:::
<!-- PAGE -->
## 附录 D　GB1 语言调用、预算与复现实验

![图 S3　GB1 workflow-v1.1 的 hard 与 live-LLM 对照。相同名义预算 96×3 下，LLM 接入改变了文库与实际查询数；因此产量与实际分母一并展示。单 seed 42。来源：gb1_hard/llm.json 与 event-audit.json。](figures/f07_llm.png)

| 配置 | 实际查询 | 强命中 | 强命中 / 查询 | 有益命中 | 有益 / 查询 |
|---|---:|---:|---:|---:|---:|
| 确定性，无知识 | 288 | 50 | 17.36% | 182 | 63.19% |
| Live LLM，无知识 | 105 | 32 | 30.48% | 88 | 83.81% |
| 确定性，知识 | 288 | 65 | 22.57% | 204 | 70.83% |
| Live LLM，知识 | 197 | 59 | 29.95% | 140 | 71.07% |

::: {.cols}
### 数值下降对应怎样的执行变化

两次运行具有相同冷启动、名义预算与 Oracle；随机和贪心路径不经过语言端口，保留相同对照行为。接入 gpt-5.6-sol 后，两条 Agent 的绝对强命中和有益命中均下降，但实际查询也从 288 减少到 105 和 197。

事件流显示，无知识臂三轮分别测了 5、96、4 条，知识臂测了 5、96、96 条。预算利用率为 36.46% 和 68.40%。以实际查询为分母，两条 LLM 臂的强命中比例反而更高。由此可见，绝对产量下降包含了文库收缩与吞吐变化，不能直接等同于候选质量下降。

### 语言参与度与消费者接线

本次 GB1 Critic 在 90 秒超时设置下，50 次尝试中产生 27 条实质评语，23 次回退。假设来源为无知识臂 llm/fallback/llm、知识臂 llm/fallback/fallback。该运行测量的是包含回退的语言接入系统。

审计还发现，知识臂实际提名的 197 条候选均对应同轮 Critic 的 rejected 判定。原因是附录 C 所述 selector 读取全部 candidates。故该路径实际生效的是采集分数；在实际预算与回退路径不同的条件下，观测差值不能单独归因于知识，更不能归功于 Critic 拒绝过滤或自然语言评语。

同为 90 秒超时条件的 workflow-v1.2 独立复现中，两条 LLM 臂各只完成 5 次查询，强命中均为 3，随后因无新候选停止。与 v1.1 的 105/197 次查询分开观察，两次运行显示语言菜单与回退路径会造成较大的预算使用差异。这进一步将改进重点落在有效文库、预算填充与等实际查询量比较，而非从绝对产量判断语言模型的普遍优劣。来源：evidence/gb1_llm_replication.json 及配套事件。
:::
<!-- PAGE -->
## 附录 E.1　AAV 知识消融与执行模式


| 策略 | 新增最佳 fitness | 强命中（atomic） | 强命中（checkpoint） |
|---|---:|---:|---:|
| random | 5.8015 | 29 | 29 |
| greedy | 6.1862 | 69 | 69 |
| Agent，无知识 | 6.1862 | 69 | 53 |
| 知识 Agent | 7.8290 | 166 | 166 |

::: {.cols}
### 约束对搜索组成产生直接影响

知识臂相对无知识臂的最佳值提高 1.6428，强命中增加 97（atomic）或 113（checkpoint）。所有策略完成 288 次查询，知识臂提名的 167 条 HD3 与 121 条 HD4 占满预算；无知识臂平均 HD 为 8.53，知识臂为 3.42。

两臂提名集合交集为 65，Jaccard 系数为 0.1272。这表明知识配置确实改变了被测候选，而不只是给同一批序列附上不同的解释。HD 与 BLOSUM 门禁在此路径中实际参与候选池构造和测试验证。

### 将预测支持与组合搜索相衔接

AAV 的 28 位点空间较宽，低阶训练数据对较远组合的支持不均匀。门禁将预算集中于更接近训练分布的组合，在本次运行中获得更多强命中。与 GB1 easy 的最高值饱和对照，这一结果支持按冷启动覆盖与搜索空间设计知识处理。

标签打乱对照给出观测 CV Spearman 0.9059、打乱后 0.0254，说明该验证管线捕获了标签相关的可预测信号。跨阶测试仍需另行考察，附录 F 展示其与同分布验证的差别。

### 解释联合处理的效果

本实验的知识增强包含搜索范围和先验规则，Agent 路径还具有历史语言调用及回退。因此 97 个额外强命中是这一配置的配对差值，不能进一步拆成某个语言模块的独立贡献。atomic 与 checkpoint 是执行方式对照，分别报告；重复实验将用于检验该差值的稳定程度。
:::
<!-- PAGE -->
## 附录 E.2　固定预测器与采集矩阵

![图 S4　AAV 固定预测器、统一知识门禁下的采集矩阵。随机配置为 30 seed 均值±总体标准差；确定性配置的重复记录对应同一轨迹。来源：aav_multiseed.json。](figures/f09_aav_fixed.png)

| 采集配置 | 最佳值，均值±σ | 强命中，均值±σ | 达峰 | 独特轨迹 |
|---|---:|---:|---:|---:|
| Mean | 7.8290 | 166 | 否 | 1 |
| UCB 0.5 | 6.5309 | 153 | 否 | 1 |
| UCB 1 | 6.5309 | 151 | 否 | 1 |
| UCB 2 | 6.5309 | 139 | 否 | 1 |
| UCB 3 | 8.4162 | 128 | 是，第 3 轮 | 1 |
| Alternating | 7.8681 ± 0.1490 | 148.73 ± 3.49 | 2/30 | 30 |
| Gaussian Thompson | 7.3017 ± 0.6684 | 140.03 ± 6.06 | 3/30 | 30 |

::: {.cols}
### 最高值与命中数形成真实权衡

在相同门禁下，Mean 取得 166 个强命中但停在 7.8290；UCB 3 找到 8.4162 候选峰，强命中降至 128。更强探索并未沿所有指标单调改善：UCB 0.5、1、2 都停在同一较低峰。

这说明探索参数应与目标函数和实验成本一起确定。若希望积累一批高质量候选，均值策略在该配置下更有吸引力；若任务重视发现稀有峰，容忍较低批次产量的探索可能值得测试。贝叶斯优化中的 UCB 与改进量方法均体现了对采集目标的显式建模。[18,19]

### 随机重复提供另一层证据

Alternating 与 Gaussian Thompson 分别在 30 次运行中达峰 2 次和 3 次，对应 Wilson 95% 区间约 1.85%–21.32% 与 3.46%–25.62%。小次数的差别不足以稳定排序两者，却揭示了达峰事件的稀疏性。

确定性策略即使保存了多条 seed 记录，候选轨迹仍一致；将其计作 30 次独立随机成功会夸大证据量。本表直接列独特轨迹，使重复的含义可检查。该矩阵固定模型与门禁，不包含 LLM，因此用于解释采集行为本身。
:::
<!-- PAGE -->
## 附录 F　完整突变阶数与覆盖分析

![图 S5　突变阶数分析。左：所有直接（k−1）阶组成变体均有测量的比例；中：低阶训练向高阶测试的 Spearman；右：AAV 已测样本按 HD 的 fitness 中位数与四分位区间。来源：aav/gb1_mutation_order.json。](figures/f10_order.png)

| 数据集 | 训练阶 → 测试阶 | 训练 / 测试数 | 所选 α | 测试 Spearman |
|---|---|---:|---:|---:|
| AAV | 0..1 → 2 | 533 / 9,900 | 0.01 | 0.8749 |
| AAV | 0..2 → 3 | 10,433 / 6,124 | 1 | 0.6155 |
| GB1 | 0..1 → 2 | 77 / 2,091 | 0.01 | 0.6580 |
| GB1 | 0..2 → 3 | 2,168 / 26,019 | 10 | 0.5589 |

::: {.cols}
### 验证分布必须对应研究问题

AAV 0..2→3 的内层留出验证相关为 0.9094，而 HD3 测试相关为 0.6155。前者描述训练阶数范围内的预测，后者直接检验跨阶外推。两者的落差提醒我们，随机留出分数不能替代目标外推分布上的验证。

这也是设置 GB1 冷启动分层的原因：改变初始测量覆盖，可以观察模型在低阶数据起步时如何组织组合搜索，而不仅是在较密集的随机样本中继续插值。

### 测量拓扑影响机制解释

对 k 阶变体，本文的“直接低阶完整率”要求其全部 k 个（k−1）阶组成变体均已测量；这不等于所有更低阶子集都完整。AAV HD3 的完整率为 31.17%，HD4 为 2.24%；GB1 对应为 96.22% 与 94.26%。

因此 AAV 高阶组合经常缺少用于分解相互作用的直接对照。其按阶数统计的 fitness 中位数也反映各阶已测样本的选择组成，不能单凭这些组间统计断言“增加一次突变”的因果效果。

### 残差把高分与失配联系起来

AAV HD2、HD3、HD4 的加性残差中位数分别为 −2.56、−5.20、−8.04，表现出随阶数加深的系统性高估。这提供了选择更丰富模型和设计诊断组合的依据。高阶上位效应研究也强调，组合测量与所用参考背景决定了相互作用的定义。[17]
:::
<!-- PAGE -->
## 附录 G　保守性与局部组合的补充统计

| 替换（零基坐标） | 保守性名次 / 28 | 熵（nats） |
|---|---:|---:|
| D0Q | 1 | 1.2339 |
| S17E | 26 | 2.9035 |
| V18A | 4 | 2.8555 |

::: {.cols}
### 可执行知识与经验图谱

系统中的知识既包括 HD 和 BLOSUM 等显式规则，也包括从已测标签形成的突变共现、富集和上下文关系。前者表达允许搜索的范围，后者把已有实验压缩为候选解释。AAV 自主路径从 measured set 构建图，并针对提名调用突变上下文查询。

这种图谱的主要价值是连接具体替换、观测与建议。富集表示已有样本中的关联；它会受采样策略和覆盖影响。因此图谱适合帮助研究者形成可检验的组合假设，而不是把共现直接解释为突变之间的因果机制。

GB1 的残基集中度给出一种直观的搜索诊断：该运行的 top-10 记录中，V54 位点全部选择 A，而其他位置保留更多变化。它说明高分提名收敛到了怎样的组成，便于进一步检查是否过早缩窄文库。

### 保守性作为可检查的先验

我们用 ESM-2 逐位 masked-token 的 20 种氨基酸分布熵表示位置保守性。熵越低，分布越集中。AAV 候选峰含 D0Q、S17E 与 V18A：对应保守性名次为第 1、第 26 和第 4，熵为 1.2339、2.9035 与 2.8555 nats（窗口零基坐标）。

这构成对硬保守性筛选的具体提醒：若排除最保守位置上的替换，D0Q 可能先于组合评估被移除。当前实现将保守性用于事后分析，没有把它接入在线筛选，因此这里讨论的是潜在筛选后果。

AAV 的保守性名次与最大单点增益相关为 ρ=0.4028（p=0.0335，n=28），与有益比例相关为 0.2972（p=0.1246）。这些不同指标表明自然序列先验与特定 assay 功能之间存在需要实测检验的关系。GB1 仅四个位点，相应 ρ=0.2、p=0.8，作为描述保留。

### 局部组合的完整测量

WT −0.918194；A 0.302016；B 3.287418；C 0.889606；AB 缺测；AC 2.087894；BC 5.770209；ABC 8.416205。A=D0Q、B=S17E、C=V18A。

相对单点加性的偏离为 +2.1008，缺失 AB 使纯三阶分解无法直接识别。ABC 的预测均值为 6.366779，全池排名 2,758、门禁池排名 426；首批高预测 48 条的平均预测/实测为 11.306529/2.883794。上述数值属于局部分析配置，不能与不同门禁构型的排名直接互换。
:::
<!-- PAGE -->
## 附录 H　V0.8 首轮冒烟：配置与行为证据

| AAV 冒烟对照，seed 42 | control | reflexion |
|---|---:|---:|
| 残差记录 / 下一轮注入 | 记录 / 不注入 | 记录 / 注入 |
| 跳转工具触发轮次 | 5 | 2、5 |
| 六轮送测集合的逐轮交集 | 48/48，全部六轮 | 与 control 相同 |
| 实际查询 / 强命中 | 288 / 157 | 288 / 157 |
| 新增最佳 fitness | 8.4162 | 8.4162 |
| LLM 轮次成功（超时 240 秒） | 6/6 | 6/6 |

::: {.cols}
### 把预测与观测成对记录

首轮实验使用 one-hot 与成对交互 surrogate、48×6 预算、知识门禁和纯利用构型。两臂都在提名时记录预测，再获得 Oracle 测量并计算 residual=measured−predicted；只有 reflexion 臂将前轮残差信息注入下一轮 prompt。因此处理变量是残差的语言可见性。

这项记录使失败推荐具有可检查的对象。例如第 1 轮的一条序列预测为 8.3319，实测 −0.2235，残差 −8.5554；它被纳入下一轮的高估低适应度案例。运行预先设置的低值阈值为 0.2，报告将其视为本实验的操作性分类，而非独立的生物学致死判定。

### 动作提前，送测集合保持一致

反思臂在第 2 轮调用 `redirect_batch`，对照臂在第 5 轮调用。原始事件显示，提前调用时 `signature_size=0`，尚无用于跳离的簇签名。批次比较进一步显示，两臂六轮每轮的 48 个序列集合完全相同，最终 288 个查询及测量产量也一致。

纯利用路径的 compose 事件均记录 requested=1.0、effective=1.0；该运行没有表现出利用比例的实际调整。因而新增反思信息改变了工具动作，却没有通过当前构型转化为不同的实验选择。提前调用本身不作为搜索收益。

### 自述与行为应分别验证

反思臂总结声称依据残差排除了两个低适应度背景并优先采用实测支持的 motif。然而该臂实际测量的序列集合与对照完全一致。这个案例表明，包含“根据失败调整”的自然语言总结，并不自动证明选择行为已经调整。

首轮为单 seed 冒烟，适合定位信息、动作与执行之间的连接，不用于断言反思普遍有效或无效。本轮每臂 6/6 的成功率对应 240 秒超时，与 GB1 的 90 秒 Critic 调用属于不同任务、不同计数单位和运行条件，不作可靠性升幅比较。
:::
<!-- PAGE -->
## 附录 I　后续因子设计与报告数据交接

::: {.cols}
### 采集构型 × 反思开关

后续方案将纯利用与质量感知混合分别配对反思关闭/开启。先核验反思信息是否到达模型，再比较 requested/effective 参数、跳转簇签名和实际批次；候选分叉后，通过多 seed 配对估计检验稳定性。本版保持首轮证据范围，后续轮次由报告 v0.7 独立整合。

### 接收内容

四臂分别交付代码提交或不可变版本、完整命令、seed、特征、surrogate、门禁、采集构型、反思开关、LLM 模型、超时、重试设置与环境说明。提供原始压缩事件、metrics、运行日志、实际预算、逐轮成功/回退计数，以及数据和候选池标识。

逐候选记录必须包含提名时预测均值/方差、测量值、残差和序列，并可关联到轮次与模型。反思注入原文与来源轮次、requested/effective 采集参数、跳转签名大小应一起保留。

### 分析次序

1. 检查四臂只在声明因子上变化；区分固定与可调整的采集参数。
2. 验证残差在揭示标签及重拟合前冻结预测，避免事后重算形成伪残差。
3. 逐轮比较实际送测集合哈希与交集，再比较工具动作和模型自述。
4. 按实际查询预算报告强命中、有益指标（如适用）、峰值、失败 motif 再现率。
5. 候选开始分叉后，在独立 seed 中作配对估计，汇报不确定性与完整配置。

第一轮 n=1 不能承担反思有效/无效的一般结论。第 2 轮提前跳转时 signature_size=0，所有六轮送测集合一致；该事实不因后续实验结果改变。90 秒 GB1 Critic 尝试与 240 秒 AAV 完整轮次成功率不放在同一改善曲线上。AAV 达候选池峰不等同于超过冷启动中 9.536457 的已知最优。

:::
<!-- PAGE -->
## 附录 J　工程交付、复现与图像制作

::: {.cols}
### 已完成的工程交付

系统交付包含预测器接口、角色与工具执行、规则验证、事件回放和交互 Demo。新版 Demo 展示预测器阶梯、α 扫描、冷启动轨迹及知识分析；本报告从对应数据重绘静态图，保证打印可读性和数字来源一致。

归档事件使用 gzip 保留完整记录，清单保存产物哈希；事件存储支持截断尾部恢复。其锁的保证限于同一 EventStore 实例内的线程，不延伸为跨进程写入保证。安装与运行入口、生产脚本和版本产物共同构成复现链，报告图表另附冻结快照和重建脚本。

### 当前证据指向的改进重点

研究的主要不确定性集中在策略重复、外推校准与执行接口。GB1 非随机策略和 AAV 知识消融需要更多独立运行；表征比较中的 Ridge 收益需要转移到闭环再检验；GB1 的 Critic 消费路径需要与其预期职责对齐。

这些问题具有明确的下一步：按同一查询预算重做语言介入对照，分别控制知识组成项，并将失败残差与下一轮实际决策绑定。我们以这些可检验的改进为后续实验目标。




### 报告重建与附属材料

正文与附录共同构成可阅读报告；原始 JSON、事件和代码快照随 evidence/ 交付。以 `sources.json` 固定 44 项输入。v0.5 底稿、本轮重排前稿以及收到的另一版 v0.6 均予保留；参考稿用于理解讨论，科学结论以源代码和冻结测量为准。

依次运行 `python3 build/figures.py`、`python3 build/build.py`、`node build/render.cjs` 与 `python3 build/verify.py` 重建、检查报告。Python 需 numpy、matplotlib、beautifulsoup4、PyMuPDF；另需 Pandoc、Playwright 与 Chrome。此过程不运行实验或在线 LLM。

### 插画与数据图的制作

图 1、3、8 使用内置生图工具，延续 v0.5 的纯白背景、柔和蓝绿与简洁图标风格；提示词和输出哈希见 imagegen-prompts.json。接口未提供具体模型版本选择。其余统计图从冻结数值生成，保留可编辑 SVG 与高分辨率 PNG。插画用于解释机制，不承担定量证据。

所有图像内嵌在离线 HTML 中。引用记录、配置、调用与缺测细节在本附录直接呈现，原始事件保留机器可复核版本。
:::

<!-- PAGE -->
## 附录 K.1　证据文件与原始来源索引

<div class="note">快照路径相对 evidence/，原始路径相对仓库；完整 SHA-256 见 sources.json。基础快照与后续 V0.8、workflow-v1.2 资料分别记录来源，不合并实验效应。</div>

| # | 快照 | 原始来源 |
|---|---|---|
| 1 | `gb1_easy.json` | `harness/reports/workflow-v1.1/gb1/campaign_easy.metrics.json` |
| 2 | `gb1_hard.json` | `harness/reports/workflow-v1.1/gb1/campaign_hard.metrics.json` |
| 3 | `gb1_sparse.json` | `harness/reports/workflow-v1.1/gb1/campaign_sparse.metrics.json` |
| 4 | `gb1_llm.json` | `harness/reports/workflow-v1.1/gb1/campaign_llm.metrics.json` |
| 5 | `alpha.json` | `harness/reports/workflow-v1.0/gb1/predictor_alpha_sweep.json` |
| 6 | `scaling.json` | `harness/reports/workflow-v1.0/gb1/predictor_ladder_scaling_ablation.json` |
| 7 | `predictors.json` | `harness/reports/workflow-v1.1/gb1/predictor_metrics.json` |
| 8 | `aav_atomic.json` | `harness/reports/knowledge-ablation/atomic-seed0/metrics.json` |
| 9 | `aav_checkpoint.json` | `harness/reports/knowledge-ablation/checkpoint-seed0/metrics.json` |
| 10 | `aav_multiseed.json` | `harness/context/research/v07-multiseed-evidence/summary.json` |
| 11 | `epistasis.json` | `reports/final-report-v0.5/evidence/epistasis.json` |
| 12 | `aav_mechanism.md` | `harness/context/research/v07-peak-mechanism.md` |
| 13 | `multiseed_protocol.md` | `harness/context/research/v07-multiseed-robustness.md` |
| 14 | `handoff.md` | `harness/reports/REPORT-HANDOFF.md` |
| 15 | `v08-proposal-received.md` | `reports/v0.8-proposal-event-stream-reflexion.md` |
| 16 | `gb1_mutation_order.json` | `harness/reports/analysis-v0.1/gb1/mutation_order.json` |
| 17 | `gb1_conservation.json` | `harness/reports/analysis-v0.1/gb1/conservation.json` |
| 18 | `aav_mutation_order.json` | `harness/reports/analysis-v0.1/aav/mutation_order.json` |
| 19 | `aav_conservation.json` | `harness/reports/analysis-v0.1/aav/conservation.json` |
| 20 | `code/agent/pipeline.py` | `agent/pipeline.py` |
| 21 | `code/evolution/campaign.py` | `evolution/campaign.py` |
| 22 | `code/agent/auto_researcher.py` | `agent/auto_researcher.py` |

<!-- PAGE -->
## 附录 K.2　证据文件与原始来源索引

<div class="note">快照路径相对 evidence/，原始路径相对仓库；完整 SHA-256 见 sources.json。基础快照与后续 V0.8、workflow-v1.2 资料分别记录来源，不合并实验效应。</div>

| # | 快照 | 原始来源 |
|---|---|---|
| 23 | `code/agent/llm.py` | `agent/llm.py` |
| 24 | `code/knowledge/validators.py` | `knowledge/validators.py` |
| 25 | `code/knowledge/rules.yaml` | `knowledge/rules.yaml` |
| 26 | `code/events/store.py` | `events/store.py` |
| 27 | `code/models/train_ladder.py` | `models/train_ladder.py` |
| 28 | `code/models/alpha_sweep.py` | `models/alpha_sweep.py` |
| 29 | `code/features/conservation.py` | `features/conservation.py` |
| 30 | `code/analysis/mutation_order.py` | `analysis/mutation_order.py` |
| 31 | `code/app/demo.py` | `app/demo.py` |
| 32 | `gb1_easy.events.jsonl.gz` | `harness/reports/workflow-v1.1/gb1/campaign_easy.events.jsonl.gz` |
| 33 | `gb1_hard.events.jsonl.gz` | `harness/reports/workflow-v1.1/gb1/campaign_hard.events.jsonl.gz` |
| 34 | `gb1_sparse.events.jsonl.gz` | `harness/reports/workflow-v1.1/gb1/campaign_sparse.events.jsonl.gz` |
| 35 | `gb1_llm.events.jsonl.gz` | `harness/reports/workflow-v1.1/gb1/campaign_llm.events.jsonl.gz` |
| 36 | `v08-smoke-1seed.md` | `harness/tasks/task_91e931121d3ae400a0a2be246b-v0-8-aav/artifacts/smoke-1seed.md` |
| 37 | `handoff-update-v08.md` | `harness/reports/REPORT-HANDOFF.md` |
| 38 | `v08-control.metrics.json` | `harness/tasks/task_91e931121d3ae400a0a2be246b-v0-8-aav/artifacts/smoke-control.metrics.json` |
| 39 | `v08-control.events.jsonl.gz` | `harness/tasks/task_91e931121d3ae400a0a2be246b-v0-8-aav/artifacts/smoke-control.events.jsonl.gz` |
| 40 | `v08-reflexion.metrics.json` | `harness/tasks/task_91e931121d3ae400a0a2be246b-v0-8-aav/artifacts/smoke-reflexion.metrics.json` |
| 41 | `v08-reflexion.events.jsonl.gz` | `harness/tasks/task_91e931121d3ae400a0a2be246b-v0-8-aav/artifacts/smoke-reflexion.events.jsonl.gz` |
| 42 | `gb1_llm_replication.json` | `harness/reports/workflow-v1.2/gb1/campaign_llm.metrics.json` |
| 43 | `gb1_llm_replication.events.jsonl` | `harness/reports/workflow-v1.2/gb1/campaign_llm.events.jsonl` |
| 44 | `handoff-update-replication.md` | `harness/reports/REPORT-HANDOFF.md` |
