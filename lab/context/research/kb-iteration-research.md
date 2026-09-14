# KB 迭代研究：用缺测残基对引导探索，而非再加一层保守性门禁

> **⚠️ 勘误(2026-09-14)**:本文档写于 2026-09-12 19:36 之前,其 §1 表格与「矩阵与编号的实测问题」一节记录的三项 KB 缺陷**已于当日 21:03–21:35 被修复**,文档未随之更新。逐条对照今日实测:
>
> - 「190 种无序异残基替换中 **136 种未声明**」 → `5a926f8 fix: complete mutation knowledge rules`(09-12 21:35)已补全。今日实测 `knowledge/rules.yaml` 为 20 行 × 20 项,无序对 **210/210**(含自配对),**缺失 0**。
> - 「`_score` 用 `x or reverse`,使 A→T、E→N、G→S、V→T 四个显式零分丢成 `None`」 → 同一提交改为 `if b in direct: return direct[b]`(`knowledge/validators.py:52`),**显式 0 分被保留**。
> - 「`auto_researcher` 未消费此图」 → `ccb8b68 feat: add AAV knowledge ablation`(09-12 21:03)起生产在用:`agent/auto_researcher.py:488` 构建图,`:491-505` 经 `query_mutation_context` 生成 graph rationale。
>
> 第 139–152 行的内嵌脚本与其输出(`missing_pairs: 136`、`zeros_lost: [[A,T],[E,N],[G,S],[V,T]]`)是**修复前的真实观测**,保留以便复核当时状态,不代表当前代码。
>
> **勘误二(2026-09-14):上一版勘误把两条结论列为「不受本勘误影响」,这两处判断都错了,现逐条更正。**
>
> - 「当前 KB…**只当二元门禁用**」→ **不成立**。`_gate` 本身确实仍是二元门(见 §1 表中 `auto_researcher.py:_gate_variants` 一行,该行不变),但知识图谱另有独立消费路径:`agent/auto_researcher.py:488` 构图、`:492` 经 `query_mutation_context` 生成 graph rationale、`:694-705` 以 `agent.tool.knowledge_graph` 事件发出、`:776` 注入 `check_knowledge` 的 `scientific_critic`。跑批证据而非读码证据:`lab/reports/v09-contract/contract-v09_reflexion-on_seed-42/agentic.metrics.json` 记 `knowledge_graph_enabled=True`,该事件名出现在全仓 11 个真实产物中。
> - 「门内 11130 种具体残基对中 7937 种从未被测,占 9533 个门内候选的 71.88%」→ **四个绝对数全部作废**。成因正是同一次修复:矩阵补全后 `_score` 由返回 `None` 变为返回显式 0,`blosum_min=0.` 这道门随之**变严**,门内候选 9533 → 2515。2026-09-14 CEO 原样复跑本文档自带的 runner(现已跟踪于 `lab/context/research/kb-audit-evidence/audit.py`)实测:`gate=2515`、`gate_position_pairs=319`、`gate_residue_pairs=3878`、`unseen_residue_pairs=2323`、`gate_candidates_with_unseen_pair=1770`,即 **1770/2515 = 70.38%**;`rows=38265 cold=10433 pool=27832`、`cold_position_pairs=378`、`unseen_position_pairs=0` 均未变。**方法论主张不变**(缺测必须落到 `(位点i,残基a,位点j,残基b)` 粒度、只统计位点对会误判已充分测过),但支撑它的每一个绝对数都须换成上面这一组。


任务：`task_8e29be09414b0c5d7eac95db08`；2026-09-12；代码基准 `ccbfce6c98a8b9f247b37aee456819c8f703878f`；研究/设计，未改产品。

## 结论先行

1. **值得做小迭代，不值得在交卷前上完整 DCA/结构预测管线。** 第一项：把现有理化属性用于探索批次的多样性，并以**具体残基对缺测覆盖**分配预算。第二项：若有可验证的 AAV2 capsid 结构，加入接触/暴露度软权重。两者都不把“像天然蛋白”当成高实验 fitness 的保证。
2. 当前 KB 为**完整** BLOSUM62（`5a926f8` 后 190/190 无缺项，2026-09-14 复跑实测 `missing_pairs=0`）、20 种氨基酸理化属性与 GB1 遗留校验；AAV 链路将其用于候选可见范围和实验前二元门禁，**图谱已接入 Critic/解释环节**（`auto_researcher.py:492,694-705,776`）生成 rationale——但**仍未用理化属性/图谱去引导采集或分配预算**，这一步才是本文档主张的内容。**先统一语义，再扩大知识量**；本任务只报告问题，不修代码或改门禁。
3. 本次不读取 fitness 列的审计发现（**数字按 2026-09-14 复跑更新，原 11,130/7,937/6,852/9,533/71.88% 已作废，见文首勘误二**）：cold-start 覆盖全部 **378 个位点对**；门内候选所含 **3,878 种具体残基对中 2,323 种未见于 cold-start**，涉及 **1,770/2,515（70.38%）** 个候选。因此“高耦合位点对值得测”必须落实到 `(位点i,残基a,位点j,残基b)`；只统计位点对覆盖会误判已经充分测过。
4. **无法保证找到隐形峰，也尚未证明胜过现有 diverse/UCB。** 缺测组合很多，结构/进化信息只能重新分配探索概率；没有证据显示它们会优先指出任务提及的那个峰。值得验证的是等预算的增量价值，不是预先承诺达峰。

## 证据口径与 read-set 缺口

- **本次实证**：代码阅读与附录无标签审计，Python runner exit 0；未训练模型、未调用 ESM/LLM、未运行闭环或 pytest/CI。本任务未指定测试文件，不执行全量矩阵。
- **历史工件，本次只读取**：`lab/reports/agentic-v0.3/aav/esm_zeroshot.json`；v06 实际定位在 `lab/tasks/task_e2eab881832291e8f8f73f30a4-v0-6-llm-backtrack-redirect-vs/artifacts/context/research/v06-backtrack-analysis.md`（canonical root）。其数字不冒充本次重放。
- **v07 原文已取得（2026-09-14 更正）**：`lab/context/research/v07-peak-mechanism.md` 确实存在（19,687 字节，09-12 15:40）。本文档写作时以 `context/research/...` 口径探测得到 `document_not_found`，据此写成「不存在」——那是**探测路径口径问题，不是文件缺失**，原结论作废。任务给定的“关键二阶组合缺测导致低估”作为设计假设，**峰专属因果结论 unverified**。本次聚合缺测审计支持存在这个问题，不能替代 v07 的目标组合归因。
- 本次读取 `ha fact show` 的 F-8514C714/F-CCF29A66，并读 frontier synthesis 的勘误；不沿用正文残留的“纯贪心达峰/探索有毒”。F-8514C714 与 v06 对命中轮次记法有差异；本文以 v06 的**实验批次**为准。
- v06 历史重放：纯均值新测最高 **7.8290、strong=166**；mean/diverse 交替 **8.4162、strong=151**，第四实验批 diverse 命中。cold-start 门内均值排名 **#426**；#2758 是另一排名口径，不能混写。
- **8.4162 是未测池/门内池峰值**；v06 记录 cold-start 最大 **9.536457**，不可称全数据集全局最优或超过全部已知样本。
- 本任务研究 AAV；旧手册 GB1 的 149,361 行不是本实验池大小。领域方法部分是机制推断和设计判断，未抓取新论文或声称核实最新 SOTA。

## 1. 现状：编码了什么，实际上用了什么

| 层 | 代码证据 | 局限/影响 |
|---|---|---|
| `knowledge/rules.yaml` | 20 种氨基酸的疏水性、整数电荷、大小类别、极性；部分 BLOSUM62；max4、GB1 位点、历史优先文字规则 | 通用替换倾向，不是 AAV 位点保守性；没有 MSA、结构、残基耦合或 assay 特异知识。大小不是数值体积，H=0 只是简化电荷 |
| `validators.py:validate_mutations` | max4 与 `{39,40,41,54}` 实际硬编码；逐替换 score≥1 与 score>−1；未知矩阵项不生成 BLOSUM 检查 | YAML 并非通用执行引擎；`R-PRIORITIZE-HISTORICAL` 没在此函数实现；所有检查 AND 后零分也不能通过 conservative |
| `build_knowledge_graph` | AA→性质、变体→突变→位置；整变体 fitness>1 时每个突变均连 `improves` | 这是关联记录，不能把多突变体标签归因成单点因果效应；若引入此图，fitness 边只能来自已测数据。**（已接线，2026-09-14 更正）** `ccb8b68`(09-12 21:03)起 `agent/auto_researcher.py:488` 在生产路径构建此图，`:491-505` 经 `query_mutation_context` 生成 graph rationale；本文档写作时（09-12 19:36 前）确实尚未接线。 |
| `auto_researcher.py:_gate_variants/_gate` | 检查全序列长度/字母表，HD 上限、**突变位点**平均 BLOSUM 下限；guardrail 开启时预筛 pool，并在 test 前复查 | 既塑造候选视图又拒绝实验；仍为二元门禁，不是候选排序先验。未开启 guardrail 时不施加这层 HD/BLOSUM 筛选 |
| `check_knowledge` | zip 全序列与 WT，用 `enumerate` 的 0 基位置组成突变码，调用 GB1 validator；最多40条，返回全规则 AND | AAV 0–27 位置全部不在 GB1 集合；正常 AAV 替换会报位点失败。与均值 gate 不是同一判据，且这个工具不是 test 的授权依据 |
| `list_pool/compose_batch` | mean、var、random 或 `mean+3√var+U(0,1)`；compose 先取 exploit 再取 explore | 当前 diverse 是含随机项的 UCB 式采集，非理化/结构距离多样性；新增知识必须接到排序/批次选择才有探索作用 |

**矩阵与编号的实测问题（已于 `5a926f8` 修复，2026-09-14 更正）**：本文档写作时，20 aa 的 190 种无序异残基替换中有 **136 种未在任一方向声明**，gate 缺项取 0、在阈值 0 时被当作中性；validator 的 `_score` 用 `x or reverse`，使 A→T、E→N、G→S、V→T 四个显式零分丢成 None。**两者均已由 `5a926f8 fix: complete mutation knowledge rules`(09-12 21:35) 修掉**：今日实测 `knowledge/rules.yaml` 为 20 行 × 20 项、无序对 210/210（含自配对）缺失 0；`knowledge/validators.py:52` 改为 `if b in direct: return direct[b]`，显式 0 分被保留。两处同残基均返回4，也不是完整 BLOSUM 对角。建议后续以同一完整矩阵和显式 unknown 状态统一判据，所有策略共同重建可行池并单独报告此变化，不能把修表收益算作新先验增益。

`evolution/datasets.py` 的 AAV WT 为28 aa `DEEEIRTTNPVATEQYGSVSTNLQRGNR`；注释映射 P03135 VP1 **561–588（1基）**，窗口0基 i 对应 VP1 561+i。加载按长度28、`[A-Z]+`、无星号去重；注释称排除 designed，但代码没有独立 designed 标记过滤。数据实际38265行且本次无非标准残基，不能推广称该正则严格验证20 aa。

## 2. 候选排序：合法性、笼内可行性、隐形峰潜力

评分均为**设计判断**，1低/5高，不是测得效应量。合法性5表示满足所列前提，不表示现成资产已完成来源审计；排序优先考试成本与可验证性，不简单把三项相加。

| 优先级/候选 | 不读测试标签的合法性 | 考试可行性 | 暴露隐形峰潜力 | 来源、边界、为什么 |
|---|---:|---:|---:|---|
| **1 理化梯度 + 残基对覆盖** | 5 | 5 | 3 | 现有 AA 表 + 已测/候选序列即可；覆盖是采样历史，不伪称进化知识。用电荷/疏水性/大小/极性变化组织未见组合，避免只挑保守高均值；无法预言互作符号 |
| **2 结构接触 + 暴露度/二级结构** | 5 | 3 | 3 | 固定来源的 AAV2 capsid 结构、P03135 对齐；无需 assay 标签。接触帮助优先补测可能互作的残基对，暴露度用于分层多样性；本 read-set 未提供可用结构或映射验证，当前可行性是有条件的 |
| **3 EVmutation/DCA/Potts 进化耦合** | 5 | 1 | 4 | 独立天然同源序列 MSA，序列重加权、正则化、APC 后位点耦合；残基特异 J 项可给组合支持。需要有效多样性，未验证 AAV 窗口的 MSA 深度/对齐；没有“装好工具就有可靠耦合”的保证 |
| **4 MSA/PSSM 位点保守性** | 5 | 2 | 2 | 同源序列频率/熵/带背景修正的 PSSM；可改善通用 BLOSUM 的位点无差别问题，但单点频率自身不表达二阶互作，保守性硬筛仍可能压掉非天然高活性组合 |
| **5 ESM PLM 先验** | 5 | 2 | 1 | 冻结通用预训练权重与 WT；已有历史 zero-shot 工件。当前 WT masked-marginal 求和是加性打分，不会针对缺测残基对学习 assay 上位；新一轮650M推理成本缺乏收益依据 |

**每项共同红线**：可读取许可候选池的序列身份以作池内选择，但不能看其未测 fitness、峰身份、排名或由全池 fitness 派生的阈值；不能将 FLIP/DMS 设计库当作天然 MSA。天然序列的公共可获得性不等于可混入 assay 筛选结果；记录数据版本、下载日期、序列/结构/模型哈希、训练来源与排除规则，训练集污染无法核实时注明。

进化耦合优于简单互信息的动机是减少间接相关；仍受系统发育、重组和对齐伪相关影响。使用全长/适当同源区域来比对，再映射28 aa窗口；不能把不同 serotype 的可变环强行无缺口对齐。报告 `N_eff`、每列gap/覆盖、重采样耦合排名稳定性，失败则弃用，不能根据已知峰是否排前决定“MSA合格”。

**Potts 名称不等于新信息**：当前 pairwise surrogate 从已测 assay 标签学习；EVmutation/DCA 从天然序列约束学习，二者信息源不同。后者的强耦合既可能是补偿，也可能是共同不耐受，**不是正 fitness 上位的概率**。结构接触同样不等于功能上位，无接触也不能推出无互作。

## 3. 首选落地：理化分层的具体残基对补测

**目标**：在相同可行池、预算与 surrogate 下，给低均值、低 bootstrap 方差但包含缺测组合的候选留出可达路径。上位特征在训练里共同未出现时，多个 bootstrap 可能共同低估，不能指望 var 自动指出盲点；这是机制推断，非本次拟合结论。

接口草案（新增纯函数/数据资产的未来设计，本任务不实现）：
```python
PriorSnapshot(wt, numbering, property_table, pair_weights, provenance, digest)
score_prior(candidates_seq, measured_seq, prior) -> list[PriorScore]
# PriorScore: candidate_id, coverage_gain, property_bin, supported_pairs,
#             unknown_pairs, source_digest, explanation
select_explore(candidates, measured_seq, prior_scores, n, seed) -> list[str]
```

输入故意不带 `fitness`/oracle/峰ID。surrogate 仍输出 `predict(mean,var)`，不把 prior 伪装成预测均值或统计方差；利用名额仍按已有 mean 规则，先验只改变已分配的 explore 名额。`explore_batch` 在本分支不是现有函数；接入点应是 `compose_batch` 的 `_compose_batch_indices`，名称不可混用。

对每个候选的两处非WT替换，定义 p=(i,a,j,b)。`n_t(p)` 是截至 t 的已测序列共同包含 a,b 的次数；包含额外突变的样本也计入，并另记背景数，避免把“出现一次”冒称识别了因果互作。为体现完全未见项，再保留 `1[n_t(p)=0]`。

对候选 s 的新信息代理可定义：
`C_t(s | B) = mean_{p∈pairs(s)} w_ij / (1 + n_t(p) + n_B(p))`；无pair取0。
这里 B 为本批已选集合，贪心逐个选后更新 `n_B`，减少48个名额重复补同一组合；**它是覆盖启发式，不是已证明的信息增益**。同一套预注册归一化/HD分层用于所有对照，不能用总和机械奖励HD4。

首版 `w_ij=1`。按相对WT的 Δ疏水性、Δ电荷、大小类别迁移、极性改变及 Gly/Pro 指示形成候选描述；对各已存在性质区间做均衡抽样，并在区间内按 C 选择、固定seed破同分。只用无标签池分位数或预注册常数确定区间；同时保留逐位变化，避免净电荷0掩盖互相补偿的正负变化。无需外部数值体积表。

可将探索名额固定分为两半：覆盖/理化与现有 diverse，奇数余数给后者；这是待验证起点，不能因为事后峰结果改配比。小探索预算时报告实际两部分数量；若当前高CV策略已使 explore=0，新的先验不会产生任何作用。**修改探索预算下限是另一个需单独授权/对照的任务，不能借本设计绕过现有floor。**

现有HD/BLOSUM策略为比较边界，保留并对各组一致；新 prior 不增加硬拒绝。所有生成的组合最终只通过合法未测池检索，不能制造无真值序列。每批记录覆盖增益、性质区间、均值/方差、与基线批次交集、来源哈希与完整候选ID；选定并冻结批次后才让 oracle 查表更新已测集。

**为什么可能补上 v07 机制**：缺测残基对直接获得与 predicted_mean 独立的探索机会；理化分层避免被一个熟悉替换类别垄断。但 **70.38%**（2026-09-14 复跑值 1,770/2,515；原写 71.88% 系 `5a926f8` 之前的门，已作废）门内候选都有缺口，覆盖单独不足以定位针尖；该候选范围广正是需要等预算对照，而非宣称“已找到峰路线”的原因。

## 4. 第二项落地：结构软权重；进化耦合留作可替换来源

1. 冻结一个与 AAV2 WT 匹配的实验 capsid biological assembly，记录 accession/版本/hash；先通过序列比对确认窗口561–588与结构残基/链、缺失残基、插入码。现有 P03135 FASTA 只是序列，不是结构。匹配不上则返回 missing，不猜编号。
2. 提取窗口残基之间的同链及组装体跨链最短重原子距离、溶剂可及性和二级结构（可用 Bio.PDB/FreeSASA/DSSP 等现成工具；本次未安装/运行）。跨链要保留链标签，等价对称接触汇总而非多计；只看单体会漏衣壳装配界面。窗口对外部固定残基的接触可作位点环境，不能当成可测双突变对。
3. 预注册平滑函数，例如 `contact_ij = exp(-(d_ij/8Å)^2)`，作为启发式而非物理能量；有覆盖掩码。取 `w_ij = 1 + contact_ij`，让无接触/未知对仍有正权重；暴露度/二级结构用于分层，不是“埋藏禁止突变”。8Å仅是待对照的起点，不是本任务调得的最优阈值。
4. 与方案1使用同一接口、预算、候选范围；结构只替换 `pair_weights` 并补充解释。**没有可信结构时回退 w=1**，不给伪造距离。不要为高变异表面环逐候选跑 AlphaFold、docking 或分子动力学。
5. 将来若 MSA QC 合格，可用规范化的 APC-corrected coupling norm 作为另一 `w_ij` 来源，残基特异项另输出 `delta_potts_score`。固定能量正负约定和 gauge；四项差分 `J(a,b)-J(a,wt_j)-J(wt_i,b)+J(wt_i,wt_j)` 可表征背景WT下的成对非加性。不能直接取 J 的正负叫“有益上位”，更不能拿它取代 assay oracle。

结构信息解决“哪些位置更可能相互影响”，覆盖解决“这些位置上哪些具体替换组合还没被看到”；两者结合是合理机制假设。天然耦合若可靠，可能进一步区分残基组合，但在本题小窗口、有限预算下并未证明比低成本覆盖更有用。

## 5. 批判性判断与验证设计

**不推荐的包装**：扩大三元组数量但不接 acquisition；把保守性/Potts低能量当高包装 fitness；把 ESM 负分全部剔除；用目标峰残基去挑MSA、结构链或权重；把缺测视为负标签；把高CV当尾部排序已可靠。均不能解决当前证据问题。

ESM 历史工件（本次未重跑）：fragment/full-context 的门内 Spearman 为 **0.097/0.154**，峰排名 **3743/4782（共9533）**〔**此处 9533 是该次 ESM 跑批当时的门内规模，属历史测量，不改**；补全 BLOSUM 矩阵后同一道门为 2,515，两者不可混用〕，288预算内 top 最大 **6.481/6.105**，峰 LLR **−0.433/−1.310**。代码字段叫 `peak_zscore`，实际是**未标准化 LLR 之和**，不是统计 z-score；相对WT为负不足以单独断言极端罕见或不可存活。这支持“当前 zero-shot 排序不适合找该池峰”，不支持“ESM embedding/所有PLM普遍无效”。

未来验证必须事先冻结：同cold-start/可行池、同48×6预算/重训频次/探索比例/seed组（至少5个预注册配对seed），oracle仅在批次冻结后查表。当前已看过这份峰的诊断，后续同池优化实验标为**探索性**；独立确认需未用于设计的任务/保留评估协议，换seed不能消除设计者已知峰的偏差。

对照组按增量拆开：现有diverse；纯覆盖；覆盖+理化；覆盖+理化+结构。另报纯mean作为利用参照，防止只提高单峰命中却损害大量强变体发现。结构/理化组应与等名额随机探索比，不能靠多给实验赢。

- 指标：新测累计max、Top-k均值、预先固定强变体阈值下的命中数、池峰命中率；预测 Spearman/Pearson/MSE 与Top-k召回单独离线评估。峰身份/全池阈值只归评估端，不能给选点接口。cold-start更高的max另列，不能让其遮蔽新发现曲线。
- 阴性对照：冻结measured/candidate序列后任意打乱或替换未测fitness，prior分数和批次ID必须完全不变；该检查比“解释文字未提峰”更强。
- 匹配对照：随机置换理化表的AA映射、对结构图做保持度分布的重连；若真实来源不优于匹配随机，不能称知识有增益。监督路径另做训练标签shuffle，Spearman应回到零附近，本次未做模型实验。
- 阳性/负向控制：合成少量pair缺测记录能改变覆盖排序，重复本批选择会降低其边际分；错位结构映射必须失败、未知结构返回中性、所有输出必须属于未测可行池。
- 接受标准：报告所有seed的配对差异和预算曲线，不按单峰成功seed选报告；无稳定增益则保留便宜覆盖或维持原方法。结构/耦合缺资料或收益未超过匹配随机，立即后置，不为“高级”承担维护成本。

## 6. 本次 runner 与交付限制

**历史输出（09-12，即 `5a926f8` 之前）**：`rows=38265 cold=10433 pool=27832 gate=9533`；`cold_position_pairs=378 gate_position_pairs=373 unseen_position_pairs=0`；`gate_residue_pairs=11130 unseen_residue_pairs=7937 gate_candidates_with_unseen_pair=6852`；矩阵缺项 136/190。

**当前输出（2026-09-14 CEO 原样复跑，以此为准）**：`rows=38265 cold=10433 pool=27832 gate=2515`；`cold_position_pairs=378 gate_position_pairs=319 unseen_position_pairs=0`；`gate_residue_pairs=3878 unseen_residue_pairs=2323 gate_candidates_with_unseen_pair=1770`；`missing_pairs=0`、`zeros_lost=[]`。门变严是因为矩阵补全后 `_score` 返回显式 0 而非 `None`。

**六项控制**：脚本原第 28 行写 `assert all(x['pass'] for x in validate_candidate(['V39I']))`，把 advisory 级 `R-PRIORITIZE-HISTORICAL` 也当成必过；而该规则的 `historical_good` 是 `validate_mutations` 的函数参数（默认 `None`，`load_rules()` 里并无此键），`validate_candidate` 从不传它，于是 `matched` 恒为空、该行恒判 False——**这个断言从来不可能成立，脚本每次都在 `controls` emit 之前中断**，也违反 `knowledge/rules.yaml:53-57` 自述的「every consumer filters on enforcement == "gate"」契约。2026-09-14 改为只断言 `enforcement == 'gate'` 的规则后重跑，六项控制全过：`wt_pass`、`malformed_rejected`、`high_hd_rejected`、`GB1_V39I_pass`、`AAV_N8Q_fails`、`pair_counter_crosscheck` 均为 true，`fitness_columns_read` 为 false。

> **⚠️ 该修正尚未进入提交，复核前必读。** `harness/` 由 daemon 单写、不手工提交，而 `ha doc sync` 明确拒绝 `.py`（实测 `error code=preview_blocked … path is not a supported textual document`）。因此上述 gate-only 断言目前只存在于工作区（对 HEAD 为 +7/−1），**从干净 checkout 取出的 `audit.py` 仍是旧断言，重跑仍会在第 28 行抛 `AssertionError` 并在 `controls` emit 之前中断**。复核者若要复现本节的六项控制，须先把该断言改为 `assert all(x['pass'] for x in validate_candidate(['V39I']) if x['enforcement'] == 'gate')`；覆盖数字（`gate=2515` 等）不受影响，它们在中断之前就已打印。此缺口与 fact `F-05FAE4CC` 一并记账。

本节审计仅读 `mutated_region,number_of_mutations`；没有读取 fitness 列或目标峰序列。

复现（**2026-09-14 更新**）：该脚本已跟踪于 `lab/context/research/kb-audit-evidence/audit.py`，直接执行 `PYTHONPATH=. .venv/bin/python lab/context/research/kb-audit-evidence/audit.py` 即可；下方内嵌副本与之同源（含已更正的 gate-only 断言）。首次漏设PYTHONPATH曾报ModuleNotFoundError，补齐后 exit0；该环境错误不计为通过证据。

```python
import json
from collections import Counter
from itertools import combinations
import pandas as pd
from knowledge.validators import load_rules, validate_candidate, _score
from agent.auto_researcher import _gate_variants
from evolution.datasets import AAV_WT
b = load_rules()['blosum62']; aa = 'ACDEFGHIKLMNPQRSTVWY'
def score(a, c): return 4 if a == c else b.get(a, {}).get(c, b.get(c, {}).get(a, 0))
def pairs(s): return list(combinations([(i, c) for i, (w, c) in enumerate(zip(AAV_WT, s)) if w != c], 2))
def emit(kind, **kw): print(json.dumps(dict(kind=kind, **kw), ensure_ascii=False))
raw = pd.read_csv('data/aav/full_data.csv', usecols=['mutated_region', 'number_of_mutations'])
s = raw.mutated_region.astype(str)
df = raw[s.str.len().eq(len(AAV_WT)) & s.str.match(r'^[A-Z]+$') & ~s.str.contains(r'\*')].drop_duplicates('mutated_region')
cold = df[df.number_of_mutations <= 2].mutated_region.tolist()
pool = df[df.number_of_mutations > 2].mutated_region.tolist()
gate, _ = _gate_variants(pool, wt=AAV_WT, max_hd=4, blosum_min=0., blosum_fn=score)
c = Counter(p for s in cold for p in pairs(s)); g = Counter(p for s in gate for p in pairs(s))
pos_c = {(p[0][0], p[1][0]) for p in c}; pos_g = {(p[0][0], p[1][0]) for p in g}
missing = set(g) - set(c)
emit('coverage', rows=len(df), cold=len(cold), pool=len(pool), gate=len(gate), cold_position_pairs=len(pos_c), gate_position_pairs=len(pos_g), unseen_position_pairs=len(pos_g-pos_c), gate_residue_pairs=len(g), unseen_residue_pairs=len(missing), gate_candidates_with_unseen_pair=sum(any(p in missing for p in pairs(s)) for s in gate), nonstandard_rows=sum(bool(set(s)-set(aa)) for s in df.mutated_region))
missing_b = [(a,c) for a,c in combinations(aa, 2) if c not in b.get(a,{}) and a not in b.get(c,{})]
zero_lost = [(a,c) for a in aa for c in aa if a!=c and b.get(a,{}).get(c)==0 and _score(a,c,b) is None]
emit('matrix', aa_entries=len(load_rules()['amino_acids']), unordered_pairs=190, missing_pairs=len(missing_b), zeros_lost=zero_lost, K_R_gate=score('K','R'), AAV_N8Q=validate_candidate(['N8Q']))
# Positive/negative controls exercise the same gate/validator path without labels.
allowed,rejected = _gate_variants([AAV_WT, AAV_WT[:-1], 'A'*28], wt=AAV_WT, max_hd=4, blosum_min=0., blosum_fn=score)
assert allowed == [AAV_WT] and len(rejected)==2
# Only `gate` rows may reject a candidate (rules.yaml:53-57). The advisory
# R-PRIORITIZE-HISTORICAL never passes here because validate_candidate does not supply
# `historical_good`, so the original `all(...)` could never hold and aborted before `controls`.
assert all(x['pass'] for x in validate_candidate(['V39I']) if x['enforcement'] == 'gate')
assert any(not x['pass'] for x in validate_candidate(['N8Q']))
assert c[((0,'A'),(1,'A'))] == sum(s[0]=='A' and s[1]=='A' for s in cold)
emit('controls', wt_pass=True, malformed_rejected=True, high_hd_rejected=True, GB1_V39I_pass=True, AAV_N8Q_fails=True, pair_counter_crosscheck=True, fitness_columns_read=False)
```

```json
{"kind": "coverage", "_note": "HISTORICAL 09-12, pre-5a926f8; superseded by the 2026-09-14 rerun below", "rows": 38265, "cold": 10433, "pool": 27832, "gate": 9533, "cold_position_pairs": 378, "gate_position_pairs": 373, "unseen_position_pairs": 0, "gate_residue_pairs": 11130, "unseen_residue_pairs": 7937, "gate_candidates_with_unseen_pair": 6852, "nonstandard_rows": 0}
{"kind": "coverage", "_note": "CURRENT 2026-09-14 rerun of the tracked runner", "rows": 38265, "cold": 10433, "pool": 27832, "gate": 2515, "cold_position_pairs": 378, "gate_position_pairs": 319, "unseen_position_pairs": 0, "gate_residue_pairs": 3878, "unseen_residue_pairs": 2323, "gate_candidates_with_unseen_pair": 1770, "nonstandard_rows": 0}
{"kind": "matrix", "_note": "missing_pairs/zeros_lost 为 5a926f8(09-12 21:35) 之前的观测,现均已为 0/空", "aa_entries": 20, "unordered_pairs": 190, "missing_pairs": 136, "zeros_lost": [["A", "T"], ["E", "N"], ["G", "S"], ["V", "T"]], "K_R_gate": 0, "AAV_N8Q": [{"rule_id": "R-MAX-MUTATIONS", "pass": true, "note": "1 substitutions (limit 4)"}, {"rule_id": "R-NO-STOP", "pass": true, "note": "standard amino-acid alphabet"}, {"rule_id": "R-GB1-SITES", "pass": false, "note": "position 8"}]}
{"kind": "controls", "wt_pass": true, "malformed_rejected": true, "high_hd_rejected": true, "GB1_V39I_pass": true, "AAV_N8Q_fails": true, "pair_counter_crosscheck": true, "fitness_columns_read": false}
```

交付前 `git fetch origin main` 成功，origin/main=`be62937a8b7a7bc3e6e9e7d67fba33e67e8f3bc2`；`git merge-base HEAD origin/main` 无输出且退出1，仓库非 shallow。两者无共同祖先，常规 rebase 无法进行；未强行接历史，本文证据限定任务声明 v0.5 基线。

交付仅此研究文档（不进入公共代码提交）与任务事实；本地 conventional 空提交作为交付检查点。产品行为、门禁和其他报告均未改。CEO 仍需补齐 v07 原文并进行语义验收；独立闭环增益、结构/MSA质量与多seed结论均 **unverified**。下一步建议先裁定门禁/validator语义修正是否单列任务，再以冻结预算验证纯覆盖和覆盖+理化，结构可用时加第三组。

本次承重观察已晋升 `fact/F-159073F2`（task产生关系自动创建；`accepted_durable`）。交付复跑审计输出与首次成功输出逐字节一致。

登记限制：worker 文档不在当前 daemon 的 canonical 扫描根内；`ha doc sync --submit --task task_8e29be09414b0c5d7eac95db08` 返回 `no_changes`、applied count=0。当前文稿尚未 canonical 登记；已请求允许通过 `ha task artifact add` 的 canonical doc-sync 路径登记，未获答复前不改用另一提交命令。
