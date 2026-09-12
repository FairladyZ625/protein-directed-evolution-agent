# 面向蛋白质定向进化的受控科学智能体研究报告

版本 v0.3｜Zeyu Li｜2026-09-12  
代码：[protein-directed-evolution-agent](https://github.com/FairladyZ625/protein-directed-evolution-agent)  
**摘要**：基于 GB1 与 AAV 已测序列库，构建包含适应度代理、知识约束、受控语言模型调用与查表反馈的虚拟定向进化流程。原始 GB1 低阶冷启动记录中，知识增强智能体与模型贪心均在第二轮发现库内最高值 8.761966。AAV 固定协议中，纯均值策略获得 166 个强变体，UCB（β=3）获得 128 个，但后者在第三批发现未测池最高值 8.416205。30 次 UCB 记录对应同一确定性轨迹，不能解释为 30 次独立成功。历史 FULL 智能体三条轨迹均未达峰，最好结果与 UCB 相差 0.5872。本报告将池内发现、已有最佳值、模型泛化和人机协同研发分别评价，不把确定性重复或研发者干预写成自主科学发现的证据。

## 1 背景与问题定义

定向进化通过反复生成变体、测量表型并更新设计，提高蛋白质的目标性能；机器学习可辅助这一过程[[1]](https://doi.org/10.1038/s41592-019-0496-6)。DNA 重组[[2]](https://doi.org/10.1038/370389a0)与迭代饱和突变[[3]](https://doi.org/10.1038/nprot.2007.72)提供不同的实验搜索方式。本文研究给定序列池内的预算受限选样：四位点 GB1 理论空间为 $20^4=160000$，28 位点 AAV 为 $20^{28}\approx2.68\times10^{36}$，而本地查询仅覆盖已测子集。

令 $M_0$ 为初始已测集、$Q_0$ 为候选集，批次 $B_t\subset Q_{t-1}$ 冻结后才读取标签；随后 $M_t=M_{t-1}\cup B_t$、$Q_t=Q_{t-1}\setminus B_t$。分别报告新增最佳 $f_{\rm new}(T)=\max_{x\in\cup_{t\le T}B_t}f(x)$、包含冷启动的最佳 $f_{\rm all}(T)$、阈值命中数及首次达峰批次。池内峰值仅由事后评估端计算。查表实验禁止重复查询是本协议的预算规则；真实实验仍需技术重复与质量控制。

## 2 数据集介绍

GB1 原始研究测量四个可变位点的组合景观[[4]](https://doi.org/10.7554/elife.16965)；AAV 数据来自衣壳序列多样化与包装相关表型测量[[5]](https://doi.org/10.1038/s41587-020-00793-4)。FLIP 提供低资源与突变阶数外推划分[[6]](https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/file/2b44928ae11fb9384c4cf38708677c48-Paper-round2.pdf)，ProteinGym 强调跨测定的统一比较[[7]](https://proceedings.neurips.cc/paper_files/paper/2023/hash/cac723e5ff29f65e3fcbb0739ae91bee-Abstract-Datasets_and_Benchmarks.html)。本文在这些数据上定义自己的池式优化协议，不能把它称为 FLIP 官方全局寻优评测。GFP 景观研究进一步说明非加性效应需要按具体蛋白和测定解释[[8]](https://doi.org/10.1038/nature17995)。

| 数据与协议 | 初始已测集 | 可查询范围 | 野生型与代表序列 |
|---|---:|---|---|
| GB1 低阶冷启动、LLM 记录 | HD≤2，2168 条 | 149361 条已测变体中其余序列 | 四位点 WT：VDGV；FWAA：8.761966 |
| GB1 随机冷启动对照 | 随机 5000 条 | 同一已测全集的剩余序列 | 结果不可混入低阶冷启动曲线 |
| AAV 固定协议 | HD≤2，10433 条 | HD>2：27832 条；旧门禁后 9533 条 | 28 aa WT：DEEEIRTTNPVATEQYGSVSTNLQRGNR |

GB1 相比理论组合缺少 10639 条测量；不补造其标签。AAV 总计 38265 条。已知样本 `DEEEIRTTNPVATEQYGSYSTNLQQGNR` 的 HD=2、fitness=9.53645667；新增候选池最高序列 `QEEEIRTTNPVATEQYGEASTNLQRGNR` 的 HD=3、fitness=8.41620513。因此找到后者并未提高全体已知最佳值。AAV 分数不直接换算为亲和力、感染效率或“野生型的若干倍”。突变 D0Q/S17E/V18A 使用窗口零基编号，不冒充全蛋白坐标。

处理要求包括固定 WT、校验长度和字母表、去重、记录数据哈希与拆分清单。候选标签由 oracle 隔离；调参验证集从当前已测集划出。历史 GB1 另有 5000/50000/94361 的回归训练/查询/保留划分，不等于上表优化实验。AAV 两池已用尽全部记录，不能再声称另有独立最终 holdout；其 80/20 调参集也不能兼作无偏最终测试集。

## 3 适应度预测模型

模型梯队包括 one-hot Ridge[[9]](https://doi.org/10.1080/00401706.1970.10488634)、树提升模型（梯度提升原理见[[10]](https://doi.org/10.1214/aos/1013203451)）、MLP 集成及显式成对交互 Ridge。训练集设计影响定向进化的样本效率[[11]](https://doi.org/10.1016/j.cels.2021.07.008)。蛋白语言模型预训练[[12]](https://doi.org/10.1073/pnas.2016239118)及 ESM-2[[13]](https://doi.org/10.1126/science.ade2574)提供可迁移表示；低样本工程[[14]](https://doi.org/10.1038/s41592-021-01100-y)与进化生成模型[[15]](https://doi.org/10.1038/s41586-021-04043-8)为其应用提供依据，但不能替代本测定的外推评估。

表 1 为 v0.2 底本所载 GB1 Spearman 值，本次未重新训练，原始评测矩阵尚未逐项复核；不据小数差异宣称统计显著。表内各行的模型顺序相同。

| 表征／划分 | Ridge | 树模型 | MLP 集成 |
|---|---:|---:|---:|
| one-hot／随机 | 0.484 | 0.474 | 0.389 |
| ESM-2 650M／随机 | 0.493 | 0.377 | 0.491 |
| one-hot／HD≥3 外推 | 0.358 | 0.354 | 0.278 |
| ESM-2 650M／HD≥3 外推 | 0.404 | 0.352 | 0.493 |

加性模型 $\hat f(x)=b+\sum_i h_i(x_i)$ 不显式表示背景依赖；成对模型增加 $\sum_{i<j}J_{ij}(x_i,x_j)$。序列协变[[16]](https://doi.org/10.1038/nbt.3769)与上位性实验[[17]](https://doi.org/10.1038/s41467-019-12130-8)支持研究这类效应，但本模型是测定标签监督回归，不是分子自由能或天然序列 Potts 模型。其正则化目标为 $\min_w\|y-\Phi w\|^2+\lambda\|w\|^2$。

采集函数为 $a_t(x)=\hat\mu_t(x)+\beta\sqrt{\hat v_t(x)}$。GP-UCB 理论有明确先验及噪声条件[[18]](https://doi.org/10.1109/tit.2011.2182033)；期望提升是另一种昂贵黑盒优化准则[[19]](https://doi.org/10.1023/a:1008306431147)。本 AAV 实现的均值来自全已测集拟合，方差来自固定三个 bootstrap 模型（种子 0/1/2），不是通用五模型 MLP 配置，也不是已校准置信区间。固定 β=3 的成功不构成该 Ridge 实现的无遗憾定理。建议同时验证 Pearson、MSE、Top-k 召回和分 HD 校准；没有原始输出的指标不补写数值。

## 4 LLM Agent 设计

工具增强语言模型已用于化学任务[[20]](https://doi.org/10.1038/s42256-024-00832-8)和实验编排[[21]](https://doi.org/10.1038/s41586-023-06792-0)，科学自动化也早于当前语言模型[[22]](https://doi.org/10.1126/science.1165620)。本文五角色流程为：Data Analyst 汇总已测变体；Hypothesis Generator 提出可验证突变假说；Mutation Designer 将假说转换成合法候选；Fitness Evaluator 输出代理均值及方差；Scientific Critic 对推荐依据、失败与后续方案作结构化审查。

受控 workflow 在假说生成和审查两个接口调用 LLM，序列生成、打分、去重及查询由代码执行。历史 agentic FULL/SEMI 则具有不同工具调用自由度，不能将其混称为同一双接口实验。Pydantic 数据契约约束输出格式；审计记录应包含模型与提示版本、候选 ID、选择时预测、理由、随后才获取的真值及预算。哈希链在可信锚点存在时支持篡改检测，不等于物理不可修改或天然防泄漏。

<!-- FIGURE_1_START -->
**图 1（制图接口）**：五角色受控 workflow。实线表示统计、候选生成、预测与查询数据流，两个独立标记表示 LLM 调用点；候选预筛与查询前复核各设一道门禁。oracle 标签仅在批次冻结后返回。FULL/SEMI 另标为历史实验配置，避免把角色图误当所有版本的调用实录。
<!-- FIGURE_1_END -->

推荐理由应绑定已测背景与规则，而非仅生成流畅解释。例如 S17E 在若干背景有益，可成为待验证假说；不得把包含该突变的多突变体高分直接当作其独立因果效应。此流程实现了部分科研操作，现有对照尚不能证明 LLM 获得可迁移的“科学家思维”。

## 5 知识增强方法

规则库含氨基酸疏水性、简化电荷、大小类别及极性，辅以替换评分和 HD 上限。BLOSUM 的来源是序列保守区替换统计[[23]](https://doi.org/10.1073/pnas.89.22.10915)，不是包装成功概率。AAV 历史门禁使用 HD≤4、突变位点平均替换分≥0；知识审计发现本地矩阵为不完整表，190 种无序异残基对中有 136 种缺项，部分路径以零代替缺项。因此本结果只适用于当时的本地规则，不能称为完整标准 BLOSUM62 的生物物理保证。GB1 位点校验器与 AAV 窗口编号亦存在语义不一致，需另行修复后重新评估。

图谱可表示 Variant—contains→Mutation—occurs_at→Position 及 AminoAcid—has_property→Property。已有图谱边属于关联信息；尚无证据表明 AAV 采集实际利用了图谱推理。无门禁、单门禁、双门禁的严格等预算因子消融尚不完整；第 6 节仅报告已有对照。

未来以已测残基对计数 $N_{ia,jb}$ 描述覆盖缺口，再引入有来源和编号映射的结构接触软权重。结构预测能力[[24]](https://doi.org/10.1038/s41586-021-03819-2)本身不证明功能上位性。原知识审计中，7937/11130=71.31% 的具体残基对未见；含至少一个缺测对的门内候选为 6852/9533=71.88%。两个分母不可交换，结构加权的闭环收益尚未验证。

## 6 虚拟定向进化实验结果

本节为本次读取原始指标与专题报告后的证据汇编，未重新运行蛋白实验。GB1 采用 `campaign_llm.metrics.json`，每轮 96 条、共三轮、seed=42；随机和贪心为代码基线，智能体组使用该记录中的 LLM 接口。表 2 的数值是新增测量累计最大值。

| 策略 | 第1轮 | 第2轮 | 第3轮 | 有益变体数／288 |
|---|---:|---:|---:|---:|
| 随机 | 1.910588 | 1.910588 | 5.081244 | 7 |
| 模型贪心 | 5.772032 | 8.761966 | 8.761966 | 154 |
| 无知识 Agent | 5.772032 | 5.772032 | 8.761966 | 176 |
| 知识增强 Agent | 6.042078 | 8.761966 | 8.761966 | 125 |

知识增强组较无知识组早一轮达峰，但未快于贪心，且有益变体数较少；单轨迹不能证明总体优势。旧底本“首轮达峰、贪心止于 8.045”的组合不获此原始记录支持。各策略每轮 Top-10 序列及分数完整导出至随附 `evidence/gb1_top10.csv`，正文以代表序列说明：知识增强组由第一轮 IWAA（6.042078）转向第二轮 FWAA（8.761966）。

<!-- FIGURE_2_START -->
**图 2（制图接口）**：按表 2 绘制 GB1 四策略新增累计最大值，横轴累计查询数 96、192、288。知识增强和贪心均在 192 次预算内发现 FWAA。不得接入声称首轮达峰的旧图；单运行曲线不绘制虚构误差带。
<!-- FIGURE_2_END -->

AAV 历史加性阶段，无约束 Agent 新增最大 5.960，模型直接推荐 7.5301，门禁 Agent 7.5301；这些代际结果不是完全匹配的因子消融。上位模型的后续统一协议为 48×6 预算、固定冷启动与模型选择规则。专题 30-seed 报告提供表 3；本次未取得其逐轮原始目录，故不冒充重新审计了全部 60480 次提名。

| 采集方法 | 新增最大（均值±SD） | strong（均值±SD） | 达峰记录／30 | 唯一轨迹数 |
|---|---:|---:|---:|---:|
| 纯均值 | 7.8290±0 | 166±0 | 0/30 | 1 |
| mean/diverse 交替 | 7.8681±0.1490 | 148.73±3.49 | 2/30 | 30 |
| UCB β=0.5 / 1 / 2 | 均为6.5309±0 | 153 / 151 / 139 | 均0/30 | 各1 |
| UCB β=3 | 8.4162±0 | 128±0 | 30/30 | 1 |
| 边际 Gaussian-TS 近似 | 7.3017±0.6684 | 140.03±6.06 | 3/30 | 30 |

strong 阈值为全 clean 表第 90 百分位 2.615913579904，仅用于事后评价。UCB β=3 第三批达峰；历史交替 seed42 第四批达峰，二者不可混写。随机交替与 Gaussian-TS 的条件命中率 Wilson 95% 区间分别为 1.8%–21.3% 和 3.5%–25.6%；确定性重复不报告推断性二项区间。Gaussian-TS 是候选边际独立高斯采样，未保持后验函数相关性。

## 7 失败案例分析

**失效一：无约束探索。** 旧报告中，高方差候选平均 HD=16.98、平均分−4.60，提示训练外分布与低包装表型富集。未提供逐例功能判定和生物测量，不能将负分一律称为结构灭活。知识门禁改变可查询分布，能解释历史结果改善的一部分，但未单独识别各规则贡献。

**失效二：头部排序失真。** 专题机制审计给出目标初始均值 6.366779、全池排名 2758、门内排名 426；门内 Top-48 预测均值 11.306529，实测均值仅 2.883794。因而问题兼有目标低估与竞争候选高估。D0Q/S17E 双突变缺测，导致相关交互不可直接识别；静态排名超过预算不能证明逐轮重训的贪心永久不可达。

<!-- FIGURE_3_START -->
**图 3（制图接口）**：以 A=D0Q、B=S17E、C=V18A 展示 WT、单突变、已测双突变及 ABC 的测定表，AB 留空。连接线只表达变体关系，不画成实测连续能量面；示意的曲率、鞍点和空间接触均不作为已验证结构机制。
<!-- FIGURE_3_END -->

**失效三：LLM 选样与错误归因。** 历史 FULL 三条轨迹的新增最大为 7.829、6.5309、7.829，达峰 0/3，不能写成三次都停在 7.829。以最好 FULL 轨迹为参照，$\Delta=8.41620513-7.828968\approx0.5872$，下文沿用“探索税”作为这一有限预算结果差的简称。它不是已识别的探索因果代价，更不能由离散 token 机制推出“LLM 不会微积分”。v0.4 所谓纯贪心实际为 mean/diverse 交替；纠正该标记后，负结果指向现有 LLM 策略的探索质量，而非探索本身有害。

<!-- FIGURE_4_START -->
**图 4（制图接口）**：分别绘制 AAV 新增最大值和 strong 数；UCB β=3 与纯均值为不同目标的比较。FULL 三次结果单列为历史点，标出最好 FULL 与 UCB 的 0.5872 差值；不把未匹配轨迹画成配对实验，不沿用旧图“纯贪心达峰”标签。
<!-- FIGURE_4_END -->

## 8 改进建议与未来拓展

以预注册工程阈值、复测置信度及成本定义停止契约，而非追逐事后已知峰。多目标向量可包含活性、稳定性、免疫相关表型及表达量，以非支配解集表达权衡[[25]](https://doi.org/10.1109/4235.996017)。6–7 位点应视为待验证搜索预算，不是多目标改善的必需突变数；不得把单一 AAV 包装分数转换为临床目标。

优先在未参与设计的冷启动、蛋白与测定上比较纯均值、UCB、覆盖探索和 LLM 调度，分开评价模型替换、采集改变与知识增量。ProteinMPNN[[26]](https://doi.org/10.1126/science.add2187)、RFdiffusion[[27]](https://doi.org/10.1038/s41586-023-06415-8)、网络生成设计[[28]](https://doi.org/10.1038/s41586-021-04184-w)及功能序列语言模型[[29]](https://doi.org/10.1038/s41587-022-01618-2)提供超出固定池的设计方向，但本项目尚未验证其新增序列。真实自主实验室需要测量、设备与软件反馈闭环[[30]](https://doi.org/10.1016/j.trechm.2019.02.007)；SiLA 2 仅列为待选接口，尚未完成设备接入。

<!-- FIGURE_5_START -->
**图 5（制图接口）**：五机双循环拟议架构。执行器、验证器和控制器构成内环；记忆器记录证据与版本，改进器提出模型或策略修订。修订必须经过独立评估和批准后激活。外环研发目前由人类与软件智能体协同完成，图中虚线表示未完成的自动化能力。五机是控制职责，与补充报告五条研发流水线一一对应关系并不成立。
<!-- FIGURE_5_END -->

**证据与复现说明**：本次执行了原始 JSON 摘要与 Top-10 导出、分母重算、文献元数据核对及引用闭环检查；未重训 ESM、未重跑 LLM/30-seed campaign、未验证湿实验、CI 或最终 PDF 页数。参考文献及历史结果来源见随附证据索引。文本使用语言模型辅助撰写与审校；外部数据、预训练表征和研究论据分别按上述来源标注。详细推导、勘误及可证伪路线见补充思考报告。

### 参考文献

[1] YANG K K, WU Z, ARNOLD F H. Machine-learning-guided directed evolution for protein engineering[J]. Nature Methods, 2019, 16(8): 687-694. [原文](https://doi.org/10.1038/s41592-019-0496-6)

[2] STEMMER W P C. Rapid evolution of a protein in vitro by DNA shuffling[J]. Nature, 1994, 370(6488): 389-391. [原文](https://doi.org/10.1038/370389a0)

[3] REETZ M T, CARBALLEIRA J D. Iterative saturation mutagenesis (ISM) for rapid directed evolution of functional enzymes[J]. Nature Protocols, 2007, 2(4): 891-903. [原文](https://doi.org/10.1038/nprot.2007.72)

[4] WU N C, DAI L, OLSON C A, et al. Adaptation in protein fitness landscapes is facilitated by indirect paths[J]. eLife, 2016, 5: e16965. [原文](https://doi.org/10.7554/elife.16965)

[5] BRYANT D H, BASHIR A, SINAI S, et al. Deep diversification of an AAV capsid protein by machine learning[J]. Nature Biotechnology, 2021, 39(6): 691-696. [原文](https://doi.org/10.1038/s41587-020-00793-4)

[6] DALLAGO C, MOU J, JOHNSTON K E, et al. FLIP: Benchmark tasks in fitness landscape inference for proteins[C]//Proceedings of the Neural Information Processing Systems Track on Datasets and Benchmarks. 2021, 1. [原文](https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/file/2b44928ae11fb9384c4cf38708677c48-Paper-round2.pdf)

[7] NOTIN P, KOLLASCH A, RITTER D, et al. ProteinGym: Large-Scale Benchmarks for Protein Fitness Prediction and Design[C]//Advances in Neural Information Processing Systems. 2023, 36. [原文](https://proceedings.neurips.cc/paper_files/paper/2023/hash/cac723e5ff29f65e3fcbb0739ae91bee-Abstract-Datasets_and_Benchmarks.html)

[8] SARKISYAN K S, BOLOTIN D A, MEER M V, et al. Local fitness landscape of the green fluorescent protein[J]. Nature, 2016, 533(7603): 397-401. [原文](https://doi.org/10.1038/nature17995)

[9] HOERL A E, KENNARD R W. Ridge Regression: Biased Estimation for Nonorthogonal Problems[J]. Technometrics, 1970, 12(1): 55-67. [原文](https://doi.org/10.1080/00401706.1970.10488634)

[10] FRIEDMAN J H. Greedy function approximation: A gradient boosting machine[J]. The Annals of Statistics, 2001, 29(5): 1189-1232. [原文](https://doi.org/10.1214/aos/1013203451)

[11] WITTMANN B J, YUE Y, ARNOLD F H. Informed training set design enables efficient machine learning-assisted directed protein evolution[J]. Cell Systems, 2021, 12(11): 1026-1045.e7. [原文](https://doi.org/10.1016/j.cels.2021.07.008)

[12] RIVES A, MEIER J, SERCU T, et al. Biological structure and function emerge from scaling unsupervised learning to 250 million protein sequences[J]. Proceedings of the National Academy of Sciences, 2021, 118(15): e2016239118. [原文](https://doi.org/10.1073/pnas.2016239118)

[13] LIN Z, AKIN H, RAO R, et al. Evolutionary-scale prediction of atomic-level protein structure with a language model[J]. Science, 2023, 379(6637): 1123-1130. [原文](https://doi.org/10.1126/science.ade2574)

[14] BISWAS S, KHIMULYA G, ALLEY E C, et al. Low-N protein engineering with data-efficient deep learning[J]. Nature Methods, 2021, 18(4): 389-396. [原文](https://doi.org/10.1038/s41592-021-01100-y)

[15] FRAZER J, NOTIN P, DIAS M, et al. Disease variant prediction with deep generative models of evolutionary data[J]. Nature, 2021, 599(7883): 91-95. [原文](https://doi.org/10.1038/s41586-021-04043-8)

[16] HOPF T A, INGRAHAM J B, POELWIJK F J, et al. Mutation effects predicted from sequence co-variation[J]. Nature Biotechnology, 2017, 35(2): 128-135. [原文](https://doi.org/10.1038/nbt.3769)

[17] POELWIJK F J, SOCOLICH M, RANGANATHAN R. Learning the pattern of epistasis linking genotype and phenotype in a protein[J]. Nature Communications, 2019, 10(1): 4213. [原文](https://doi.org/10.1038/s41467-019-12130-8)

[18] SRINIVAS N, KRAUSE A, KAKADE S M, et al. Information-Theoretic Regret Bounds for Gaussian Process Optimization in the Bandit Setting[J]. IEEE Transactions on Information Theory, 2012, 58(5): 3250-3265. [原文](https://doi.org/10.1109/tit.2011.2182033)

[19] JONES D R, SCHONLAU M, WELCH W J. Efficient Global Optimization of Expensive Black-Box Functions[J]. Journal of Global Optimization, 1998, 13(4): 455-492. [原文](https://doi.org/10.1023/a:1008306431147)

[20] BRAN A M, COX S, SCHILTER O, et al. Augmenting large language models with chemistry tools[J]. Nature Machine Intelligence, 2024, 6(5): 525-535. [原文](https://doi.org/10.1038/s42256-024-00832-8)

[21] BOIKO D A, MACKNIGHT R, KLINE B, et al. Autonomous chemical research with large language models[J]. Nature, 2023, 624(7992): 570-578. [原文](https://doi.org/10.1038/s41586-023-06792-0)

[22] KING R D, ROWLAND J, OLIVER S G, et al. The Automation of Science[J]. Science, 2009, 324(5923): 85-89. [原文](https://doi.org/10.1126/science.1165620)

[23] HENIKOFF S, HENIKOFF J G. Amino acid substitution matrices from protein blocks[J]. Proceedings of the National Academy of Sciences, 1992, 89(22): 10915-10919. [原文](https://doi.org/10.1073/pnas.89.22.10915)

[24] JUMPER J, EVANS R, PRITZEL A, et al. Highly accurate protein structure prediction with AlphaFold[J]. Nature, 2021, 596(7873): 583-589. [原文](https://doi.org/10.1038/s41586-021-03819-2)

[25] DEB K, PRATAP A, AGARWAL S, et al. A fast and elitist multiobjective genetic algorithm: NSGA-II[J]. IEEE Transactions on Evolutionary Computation, 2002, 6(2): 182-197. [原文](https://doi.org/10.1109/4235.996017)

[26] DAUPARAS J, ANISHCHENKO I, BENNETT N, et al. Robust deep learning–based protein sequence design using ProteinMPNN[J]. Science, 2022, 378(6615): 49-56. [原文](https://doi.org/10.1126/science.add2187)

[27] WATSON J L, JUERGENS D, BENNETT N R, et al. De novo design of protein structure and function with RFdiffusion[J]. Nature, 2023, 620(7976): 1089-1100. [原文](https://doi.org/10.1038/s41586-023-06415-8)

[28] ANISHCHENKO I, PELLOCK S J, CHIDYAUSIKU T M, et al. De novo protein design by deep network hallucination[J]. Nature, 2021, 600(7889): 547-552. [原文](https://doi.org/10.1038/s41586-021-04184-w)

[29] MADANI A, KRAUSE B, GREENE E R, et al. Large language models generate functional protein sequences across diverse families[J]. Nature Biotechnology, 2023, 41(8): 1099-1106. [原文](https://doi.org/10.1038/s41587-022-01618-2)

[30] HÄSE F, ROCH L M, ASPURU-GUZIK A. Next-Generation Experimentation with Self-Driving Laboratories[J]. Trends in Chemistry, 2019, 1(3): 282-291. [原文](https://doi.org/10.1016/j.trechm.2019.02.007)
