# 报告修订交接单(给写文档的 Agent)

> **用途**:本文件只是**素材与修改建议**,不是报告。报告正文在 `reports/final-report-v0.5/report.md`,
> 由泽宇那条线维护,**本文件的作者没有、也不应直接修改它**。
>
> **日期**:2026-09-12 | **主线锚点**:`origin/main` = `d18457d`
>
> **怎么用**:第二节是必须改的(现有结论与新证据冲突);第三节是可以新增的(试题加分项);
> 第四节是数据保留与复现状态,写「实验可复现性」那段时引用;第五节是未完成项,
> 写「局限与未来工作」时引用。每条都给了产物路径,**引用时请落到文件路径,不要只写结论**。

---

## 一、一句话摘要

这一轮补齐了试题两个加分项(突变阶数比较、保守位点分析),修掉了四策略对比链路上一处
让两条 agent 策略静默空转的缺陷,推翻了一条关于表征优劣的既有结论,并抢救了三处面临
永久丢失的实验数据。**有三条既有结论必须改**,见第二节。

---

## 二、必须修正的既有结论(与新证据冲突)

### 2.1 四策略对比的数字要换口径(最要紧)

**现状问题**:若报告引的是 `reports/campaign_metrics.json`,那份产出于提交 `54821e7`
(2026-09-12 19:36),是**四策略链路修复之前**的口径,其中 greedy 的 `cum_top10_max` 是
**8.045152**。

**为什么是旧口径**:该链路此前有两处缺陷。一是 `no_knowledge=True` 被写死,策略③④在
五角色流水线层拿到同一个值,知识消融只体现在 UCB/BLOSUM 排序上;二是 `run_pipeline`
从「已测过的训练集」推导「oracle 能测什么」,导致每个新提名都被求交滤掉,
**两条 agent 策略实际跑 0 轮、静默、退出码仍为 0**(fact `F-6306819A`)。两处均已修复。

**新口径**(GB1,easy 冷启动,预算 96×3,候选空间 149,361,缺测 10,639):

| 策略 | cum_top10_max | cum_top10_mean | strong |
|---|---|---|---|
| random | 2.373537 | 1.376018 | 0 |
| greedy | **8.761966** | 7.000914 | 81 |
| agent_no_knowledge | **8.761966** | 7.045837 | 95 |
| knowledge_agent | **8.761966** | 7.005510 | 86 |

- 产物:`harness/reports/workflow-v1.1/gb1/campaign_easy.metrics.json`
- 事件流:`harness/reports/workflow-v1.1/gb1/campaign_easy.events.jsonl`(166 条,哈希链可验)
- 曲线:`harness/reports/workflow-v1.1/gb1/figures/campaign_easy.png`
- LLM 归属:`"deterministic (pool LLM port available via --use-llm)"`——**本轮未调商业 LLM**,
  报告里不得写成「LLM 驱动」。

**口径限制**:8.761966 是 GB1 的**全局最优 `FWAA`**。三条非随机策略都命中它,
所以在 GB1 上「谁更强」不能只看 `cum_top10_max`,要看 `cum_top10_mean` 与 `strong`。

> ⚠️ 本文件定稿时 hard / sparse 两档冷启动仍在重跑,数字未齐。**若报告要引三档对照,
> 请先确认 `harness/reports/workflow-v1.1/gb1/` 下已有 `campaign_hard.metrics.json` 与
> `campaign_sparse.metrics.json`**;只有 easy 一档时,必须写明只报了 easy。

### 2.2 「ESM-2 未稳定优于 one-hot」这个结论是错的,要反过来写

**原结论的来源**:`harness/reports/workflow-v1.0/gb1/predictor_ladder.json` 里
ridge 0.4925(esm2) vs 0.4840(one-hot)、xgboost 0.3768 vs 0.4741。

**为什么不成立**:那组数固定了 `Ridge(alpha=1)`,而 alpha=1 对两种特征意味着完全不同的
正则化强度——one-hot 逐维方差约 0.25,GB1 的 ESM-2 约 1e-4(实测中位数 1.06e-4、
最小 3.39e-5、最大 4.46e-3)。**先做标准化消融**(唯一变量是标准化):

| | ridge |
|---|---|
| esm2 random raw | 0.4911 |
| esm2 random standardized | **0.2944** |
| esm2 hd_extrapolation raw | 0.4125 |
| esm2 hd_extrapolation standardized | **0.1226** |

结论随预处理反向 → **固定 alpha 下的任何一侧都不能支撑排序断言**。
产物:`harness/reports/workflow-v1.0/gb1/predictor_ladder_scaling_ablation.json`。

**再做 answer-agnostic 的 alpha 扫描**(每个组合在训练集内做 80/20 留出选 alpha,
不看测试集,alpha ∈ {0.01, 0.1, 1, 10, 100, 1000, 10000}):

| 划分 | one-hot raw / std | esm2 raw / std |
|---|---|---|
| random | 0.4840 / 0.4840 | 0.4893 / 0.4916 |
| hd_extrapolation | 0.3588 / 0.3530 | **0.4039 / 0.4090** |

两条结论:
1. **标准化伪影调过 alpha 后完全消失**(esm2 两侧从 0.4911/0.2944 收敛到 0.4893/0.4916,
   hd 档从 0.4125/0.1226 收敛到 0.4039/0.4090)。那 0.197 与 0.290 的落差 100% 是
   alpha 与特征尺度耦合的伪影。
2. **ESM-2 在 hd_extrapolation 上稳定高出 one-hot 约 0.05 Spearman,两种预处理下一致**;
   random 划分上也略高 0.005~0.008。hd_extrapolation 正是「向远端突变体外推」,
   是定向进化真正要的能力。

- 产物:`harness/reports/workflow-v1.0/gb1/predictor_alpha_sweep.json`
- 参照实现:`models/alpha_sweep.py`
- fact:`F-1E17A592`(标准化消融)、`F-5CC3FABA`(alpha 扫描)

**给报告的写法建议**:
- 表征章节把固定 alpha 的单点比较**换成 alpha 扫描表**。
- 真正的落差改述为:**不是声称不实,是闭环 campaign 没用上这个已验证更好的表征**——
  `evolution/pool_campaign.py:85` 至今是裸 `RidgePredictor(seeds=5)`,把已验证的收益
  留在桌上了。这是一条诚实且有分量的自我批评。
- **不要引用** `models/train_ladder.py:19-22` 注释里那个「AAV raw 0.47 → 标准化 0.60」
  作为通用结论——它是 AAV 专属,GB1 上方向相反。
- 范围限制:alpha 扫描只覆盖 Ridge 一级,xgboost/mlp 两级未扫。

### 2.3 事件流的并发边界表述是错的

报告若写「事件流跨进程靠文件锁串行化」,该表述为假:实现里**没有文件锁**,
实例级 `threading.Lock` 只保证**同一个 `EventStore` 实例内**的线程安全,
**不提供跨实例/跨进程保证**。正确表述就是前半句。

另有一处已修:截断尾行恢复。原先写入完整 `seq=1` 后追加不完整字节、重启再 append,
`iter_events`/`verify` 会抛 `JSONDecodeError` 而非保留完整前缀;现已能恢复,
并有 restart-after-truncated-tail 回归测试。产物:`events/store.py`、`tests/test_events.py`。

### 2.4 v0.1→v0.7 不能写成单调递进的消融链

**代码血缘是分叉的**:`t-v06` 与 `t-v07` 都从 `t-v05`(`ccbfce6`)分出,
**`t-v07` 不含 v0.6 的 `471536b`**。对照验证:v0.6 引入的标识符
`BACKTRACK_FULL_NOTE` / `BACKTRACK_SEMI_NOTE` 在 `t-v06` 的 `agent/evolution` 下命中 1 个
文件,在 `t-v07` 下命中 **0 个**。

所以 **v0.7 的结果不能读作「在 v0.6 基础上再改进」**,两者只能各自与 v0.5 比较。
三版代码分别固定在 tag `agentic-v0.5` / `agentic-v0.6` / `agentic-v0.7` 上。
fact:`F-84AE8976`。

---

## 三、可以新增的内容(试题加分项,此前未做)

### 3.1 单点/双点/多点突变效果比较(加分项③)

试题原文:「比较单点突变、双点突变和多点突变的优化效果」。此前本仓**完全没做**。

**加性外推随阶数衰减**(低阶训练 → 高阶测试,alpha 在训练集内 answer-agnostic 选出):

| 数据集 | 训练阶 → 测试阶 | n_train / n_test | alpha* | 测试 Spearman |
|---|---|---|---|---|
| AAV | 0..1 → 2 | 533 / 9,900 | 0.01 | **0.8749** |
| AAV | 0..2 → 3 | 10,433 / 6,124 | 1.0 | **0.6155** |
| GB1 | 0..1 → 2 | 77 / 2,091 | 0.01 | **0.6580** |
| GB1 | 0..2 → 3 | 2,168 / 26,019 | 10.0 | **0.5589** |

**低阶完整覆盖率**(该阶变体里「构成它的所有低阶组合都有实测」的比例)——**这是本节最有
价值的产出**:

| 阶数 | AAV 变体数 | fitness 中位 | 最大 | 上位残差中位 | 低阶完整率 |
|---|---|---|---|---|---|
| 1 | 532 | −0.6794 | 4.6987 | — | — |
| 2 | 9,900 | −2.1471 | 9.5365 | −2.5557 | **1.000** |
| 3 | 6,124 | 1.2922 | **8.4162** | −5.2012 | **0.312** |
| 4 | 5,941 | 0.8437 | 7.8290 | −8.0369 | **0.022** |

**要点**:AAV 真峰是 HD3,而 3 阶只有 31.2% 具备完整低阶覆盖。所以「构成真峰的
D0Q+S17E 组合缺测」不是个例,**是 3 阶的常态**。上位残差随阶数单调走低
(−2.56 → −5.20 → −8.04):加性模型越高阶越系统性高估。

**一个方法学细节值得写**:AAV 0..2→3 那行的**留出验证 Spearman 是 0.9094,而测试只有
0.6155**。留出集是同阶的,所以它**系统性高估了跨阶外推能力**——这对「怎么评估外推」
是一条有用的警示。

- 入口:`analysis/mutation_order.py`
- 产物:`harness/reports/analysis-v0.1/{gb1,aav}/mutation_order.json` + `figures/`
- 报告:`harness/reports/analysis-v0.1/report.md`
- 测试:`tests/test_mutation_order.py`(含阳性对照:纯加性合成地形上位量应近零)

### 3.2 保守位点分析(加分项④),首要产出是一个负结果

试题原文:「引入蛋白质结构信息**或**保守位点分析」。选保守位点、不碰结构
(结构路线要 PDB + FoldX/Rosetta ddG,新增工具链成本高,而 AAV 可变区多为柔性环、
结构杠杆本就弱、AlphaFold 置信度低)。方法:ESM-2 逐位置 masked-token 分布的
Shannon 熵作保守性代理,不需要 MSA。

**真峰三个位点的保守性名次(AAV 28 位中)**:

| 位点 | 保守性名次 | 熵(nats) |
|---|---|---|
| **D0Q**(第 0 位) | **第 1(最保守)** | 1.2339 |
| V18A(第 18 位) | **第 4** | 2.8555 |
| S17E(第 17 位) | 第 26 | 2.9035 |

**结论:用保守性先验筛候选,第一个被丢掉的就是 D0Q。** 而 D0Q 恰是共现富集只有 −0.01、
且与 S17E 的配对全表缺测的那个突变。

**这条可以和已有的两个发现合成一个很强的叙事**:AAV 真峰被**三个独立角度同时藏住**——
① 加性 surrogate 看不见正上位;② ESM zero-shot 判其反自然(片段排 #3743、全长 #4782,
z 为负);③ **保守性先验拒其构成突变**。

保守性名次与实测效应的相关(带 p 值,不要省):AAV 名次 vs 最大 fitness 增益
Spearman **0.4028 / p=0.0335**;vs 有益突变比例 0.2972 / p=0.1246(不显著)。
GB1 只有 4 个可变位点,两项都是 0.2 / p=0.8,**不作结论**。

**硬边界(报告里必须写)**:保守性只用于**事后分析与解释**,绝不进入采集或筛选路径——
ESM-2 的熵是自然度先验,而本项目真峰已被证明反自然。已用阴性对照验证:
`grep conservation evolution/ agent/` 为空,未接线。

- 入口:`features/conservation.py`
- 产物:`harness/reports/analysis-v0.1/{gb1,aav}/conservation.json` + `figures/`
- 报告:`harness/reports/analysis-v0.1/conservation-report.md`
- 测试:`tests/test_conservation.py`(阳性对照:均匀分布熵应最大、one-hot 应为 0)

### 3.3 有无知识增强的对照:AAV 为正、GB1 为负,方向相反且机制自洽

**这条直接回答试题考核重点第 6 条「是否能通过实验比较证明 Agent 的作用」。**

**AAV**(FLIP clean substitution subset,预算 48×6=288,seed 0,池峰 8.416205130560002,
strong 阈值 2.615913579904):

| 策略 | cum_top10_max | strong | 达峰率 |
|---|---|---|---|
| random | 5.8015 | 29 | 0 |
| greedy | 6.1862 | 69 | 0 |
| agent_no_knowledge | 6.1862 | 69(atomic)/ 53(checkpoint) | 0 |
| **knowledge_agent** | **7.8290** | **166** | 0 |

配对差值(知识 − 无知识):**max +1.6428、strong +97(atomic)/ +113(checkpoint)**。
阴性对照通过:观测 CV Spearman **0.905917**、shuffle-label **0.025364**,
判据「observed > 0.8 且 |shuffle| < 0.1」。四条策略**达峰率均为 0**——无人触及 8.4162 真峰。

**GB1**(见 2.1):三条非随机策略都命中全局最优 8.761966,而 `knowledge_agent` 的
`cum_top10_mean`(7.005510)与 `strong`(86)都**略低于** `agent_no_knowledge`(7.045837 / 95)。

**机制解读(建议这样写)**:知识约束在**搜索空间大、surrogate 不可靠**时收益显著
(AAV 28 位点、真峰 greedy 够不着,+1.64 / +97~113);在**小空间、greedy 已饱和**时
只剩约束成本(GB1 四位点、greedy 本就达全局最优)。**两个方向相反的结果合起来比任何
单一方向都更有说服力**,不要只报对自己有利的那一半。

- 产物:`harness/reports/knowledge-ablation/{atomic-seed0,checkpoint-seed0}/metrics.json`
  (含 `events.jsonl`、`rejected_candidates.json`、`knowledge_ablation.png`)
- fact:`F-61F813F3`
- ⚠️ **口径限制**:AAV 侧只有 **1 个 seed**(`n_seeds: 1`),不能宣称跨 seed 统计显著。

### 3.4 固定池 in-silico 评测有一个与算法无关的上界

**这条建议写进「评测协议的局限」,而不是塞进「未来工作」。**

复核:`data/aav/full_data.csv` 的 `mutated_region` 列共 **38,293** 条唯一 28aa 序列,
其中 D0Q+V18A(2.08789430573)、S17E+V18A(5.77020873916)、
真峰 D0Q+S17E+V18A(8.416205130560002)三者都在,而 **D0Q+S17E 这一对在整张表里不存在**
——不是没被采进 cold-start,是全表没有这条测量。

而 oracle 是**固定池查表**,**池内采样无法补出池外不存在的测量,加预算也不能**。
因此:
- 因素 2(模型表达力)可在笼内解决;
- 因素 1(关键二阶缺测)只能**部分**在笼内解决;
- **没有任何笼内方案能让这个特定真峰进入可达区**,原因是 oracle 的池边界,不是算法不行。

fact:`F-E158724C`。相关论述已改入
`harness/context/research/plateau-breaking-methods.md` §0 与总纲。

### 3.5 预测器阶梯:方差退化已修

历史冻结提交里 Ridge 的 ensemble 方差**退化为 0**(实测 `variance_max=3.08e-33`),
根因是提交 `fe5a1a5` 之前每个集成成员拟合的是**同一份完整训练集**(5 次确定性 Ridge),
之后才改成 bootstrap 重采样(fact `F-67F4D429`)。**T7 的 UCB 探索项消费的正是这个方差**,
退化到 0 意味着探索项失效。

现状(GB1,含独立 train/validation/test 三分):

| 模型 | test Spearman | var_min | var_max |
|---|---|---|---|
| ridge | 0.5119 | 9.67e-06 | 0.0176 |
| xgboost | 0.5034 | 1.25e-06 | 0.6461 |
| mlp | 0.4499 | 3.56e-05 | 0.5684 |

产物:`harness/reports/workflow-v1.1/gb1/predictor_metrics.json` +
`figures/predictor_comparison.png`;测试 `tests/test_predictor.py`。

### 3.6 小规模复现路径(试题「代码」硬要求)

试题:「代码应能在小规模数据集上复现实验流程」。此前只有全量入口,且依赖那份
**未提交的 44MB 地形**,评委 clone 下来跑不动任何东西。

现在 `make smoke` 用内置合成小地形跑通「数据 → 预测器 → 五角色 Agent → 四策略 campaign」,
**不需要 44MB 地形、不需要 ESM 缓存、不需要 API key**。阳性对照:把整个 `data/` 目录
移走后仍跑通,产出 6 个产物并打印
`SYNTHETIC SMALL-SCALE DATA — not comparable to formal results` 横幅,事件哈希链校验通过。
另有 `make check-gb1-data`:全量入口在地形缺失时明确报缺哪个文件并提示先跑 smoke,
不静默失败。入口:`scripts/smoke.py`。

### 3.7 Agent 推理过程(试题「结果展示 d」四子项)

| 子项 | 状态 | 落点 |
|---|---|---|
| i. 发现哪些位点可能重要 | ✅ | `AnalystReport.position_gains`,如 `{39: 2.0, 40: 1.8, 41: 0.0, 54: 1.5}` |
| ii. 为什么选择某些替换 | ✅ | `Hypothesis.rationale` + `rule_ids` |
| iii. 为什么组合某些突变 | ✅ 新增 | `CombinationRationale`(见下) |
| iv. 哪些推荐失败及原因 | ✅ | critic 拒收 + `rejected_candidates.json` |

`CombinationRationale` 的字段设计值得在报告里提一句,因为它**把实测统计量与 LLM 文本
明确分开**:`selected_single_mutations` / `empirical_position_gains` /
`positions_non_conflicting` / `rule_ids` / `deterministic_summary`,外加两个 provenance
字段 `evidence_source="measured_data"` 与 `narrative_source="deterministic"`。
LLM 不可用时走 fallback 且 `state["source"]` 如实记 `fallback`,
**不会把 fallback 的理由展示成 LLM 的推理**。

### 3.8 知识规则的 gate / advisory 分类

原先所有规则都被 critic 当硬门(`ok = all(x["pass"] for x in rules)`),导致
`R-PRIORITIZE-HISTORICAL`(「优先历史好单点」,语义上是排序建议)在无历史数据时
`pass=False`,**把全部候选都拒了**。现在 `enforcement: gate|advisory` 挂在
`knowledge/rules.yaml` 的规则自身上,critic 只对 gate 类求 `all()`;未标注默认 `gate`
(新规则漏标会被强制执行而非静默忽略)。BLOSUM62 也从残缺的 10 行/88 个有向条目补全。

---

## 四、数据保留与复现状态(写「可复现性」那段时引用)

### 4.1 版本口径(已写进代码强制)

`evolution/results_layout.py` 的 `VERSIONS` 现为
`{"workflow": "v1.1", "agentic": "v0.7", "analysis": "v0.1"}`,三条线语义:

- **workflow** —— 交付主线:数据管线 → 预测器 → 五角色 Agent → 四策略 campaign → demo。跑 GB1。
- **agentic** —— 自主 agentic researcher 线,跑 AAV。
- **analysis** —— 只读分析线:不跑新实验,只在已测数据上做分析(突变阶数、保守性)。

### 4.2 每个版本的数据落点

| 版本 | 数据落点 | 状态 |
|---|---|---|
| agentic-v0.1 ~ v0.4 | `harness/reports/agentic-v0.{1,2,3,4}/` | 在主线 |
| agentic-v0.5 / v0.6 | `harness/reports/agentic-v0.{5,6}/` | **本轮从分支取入主线**(只取数据,代码留在 tag) |
| agentic-v0.7 | `harness/context/research/v07-*.md`(5 份)+ `v07-multiseed-evidence/` | **本轮抢救入库**,见 4.3 |
| workflow-v1.0 | `harness/reports/workflow-v1.0/` | 在主线 |
| workflow-v1.1 | `harness/reports/workflow-v1.1/` | 本轮新增 |
| analysis-v0.1 | `harness/reports/analysis-v0.1/` | 本轮新增 |
| 知识消融 | `harness/reports/knowledge-ablation/` | **本轮抢救入库** |

三版代码的复现锚点是 tag:`agentic-v0.5` / `agentic-v0.6` / `agentic-v0.7`
(分支会移动,tag 不会)。26 个工作分支也都推到了远端做保留。

### 4.3 抢救出来的数据(此前面临永久丢失)

全 worktree 扫描发现多处实验证据处于 **git 未跟踪**状态,worktree 一删即丢:

1. **v0.7 证据包**:整个目录 **134MB 全未跟踪**,只存在于 worktree `t-astra-seeds` 的
   文件系统里。已纳入其中 336KB 证据文件到
   `harness/context/research/v07-multiseed-evidence/`:`protocol.md`、`run.py`、
   `verify_ucb3.py`、`results.json`(78KB)、`summary.json`、
   `reference-seed42.json`(55KB)、`controls.json`、
   `ucb3-uncached-verification.json`、治理留痕与三个 worker 的原始日志。
   128MB 的 `cache/` 是派生预测缓存,不入库;`ucb3-uncached-verification.json` 即
   绕开缓存的复核,证明结论不依赖缓存。
2. **知识消融对照**:13 个文件 1.5MB,此前只在 worktree `t-knowledge-ablation`。
3. **AAV 池式 campaign** 与 **KB 审计**:各 3 个文件。

### 4.4 v0.7 的口径限制(引用时不得省略)

`harness/context/research/v07-multiseed-robustness.md` 自己写明,这三条必须带上:

- 那 30 个 seed 是**同一轨迹的确定性重复**(这些方法不消费采集 RNG),
  因此 **n=30 的 Wilson 置信区间不可用于统计推断**,有效独立轨迹只有 1 条。
  文档列出 CI 是为满足形式要求并已显式标注不可用。
- 全程使用**本地真值查表**,未调用 LLM/网络。
- 「峰」指 **HD>2 未测池内的最优 8.41620513**,cold-start 最大值为 9.53645667;
  既不是整个数据集最优,更不是蛋白真实序列空间的全局最优。

其核心结果:UCB β=3 → 8.4162 ± 0.0000、strong 128;Greedy strong 166;
交替 mean/diverse 7.8681 ± 0.1490;Gaussian-TS 近似 7.3017 ± 0.6684。

### 4.5 复现脊柱现状(诚实披露)

`harness/reports/experiment_log.jsonl` 是声明的「版本脊柱」(记录每个产物的 git commit
与 SHA-256),现有 **15 条**,**覆盖不全**:缺 agentic-v0.1/v0.3/v0.5/v0.6/v0.7、
analysis-v0.1、workflow-v1.1 的 predictor/alpha 扫描/标准化消融、以及三份 final-report。
补全工作已立任务 `task_5c6e3951aafc21310d1c0d6d6c`,**报告若要声称「每个产物都可追溯」,
请先确认该任务已完成**;未完成时应如实写「脊柱覆盖主要闭环实验,分析线与部分历史版本
待补」。

已核实的一条正面证据:`workflow-v1.0/gb1/predictor_ladder.json` 的 SHA-256
`119c04495c5726197ac0e722e3ed2599cc501208bb4db4eb911f91e52a4dd259` 与脊柱第 1 条记录
**逐字节一致**,产出于 `d28189f13b059220dcf35537cf97a709b15f4798`。

### 4.6 一条重要的可复现性教训(建议写进报告)

`workflow-v1.0/gb1/predictor_ladder.json` **无法用当前代码复现**,但归档没坏:
提交 `fe5a1a5` 名为 "add bootstrap uncertainty",实际**改掉了估计器本身**——改前 5 个集成
成员全拟合同一份完整训练集,改后每个拟合一个 bootstrap 重采样。阳性对照坐实身份:
归档里四个组合的 ridge `variance_min/max` 全是 `0.0` 或 1e-32 量级浮点噪声,
正是「5 次确定性拟合同一份数据」的退化特征。

**教训**:一次被描述为「加功能」的提交换掉了估计器,使此前所有归档数字不再可复现。
这比「归档丢了」更隐蔽。fact `F-67F4D429`。

---

## 五、未完成项与已知风险(写「局限」时引用)

| 项 | 状态 | 说明 |
|---|---|---|
| 四策略 hard / sparse 两档 | **重跑中** | 定稿前确认 `campaign_{hard,sparse}.metrics.json` 是否已在 |
| 复现脊柱补全 | 未完成 | 见 4.5,任务 `task_5c6e3951aafc21310d1c0d6d6c` |
| 仓库双报告树 | 未收敛 | 根 `reports/`(149 文件)与 `harness/reports/`(141 文件)并存,而 `results_layout.py` 声明后者为 canonical。评委会看到两份看似都权威的产物树 |
| `tests/test_demo_app.py` | **3 个失败** | 既存缺陷(在 `f3a4179`/`f40e901`/`HEAD` 三点完全一致,非本轮回归)。模块①②在 AppTest 下不渲染,未定位到具体分支。**该文件因此未纳入 CI 门控**,以免 main 变红 |
| 强化学习(加分项①后半) | **不做** | 在本任务上要么是给采集策略套个 bandit 薄壳(无科学价值),要么时间不够。**建议在报告里写明为什么不做**,这比硬凑更体现判断力 |
| 结构信息(加分项④前半) | 不做 | 走了保守位点这条替代路径,理由见 3.2 |
| `pool_campaign` 未接 ESM-2 | 未做 | 见 2.2,已验证 ESM 在外推划分上更好,但主路径仍是裸 `RidgePredictor(seeds=5)` |
| xgboost/mlp 的 alpha 扫描 | 未做 | 2.2 的结论只覆盖 Ridge 一级 |
| AAV 知识消融只有 1 个 seed | 已披露 | 见 3.3 口径限制 |

### 一条给 CI 的说明(若报告提到工程质量)

CI 门控范围此前只有 3 个测试文件,导致 `tests/test_demo_app.py` 坏了很久无人发现——
**没被门控的测试等于不存在**。现已扩到 6 个自包含测试文件,并用阳性对照验证安全:
把整个 `data/` 目录移走后新入门控的文件仍全绿,不依赖未提交的 44MB 地形与 ESM 缓存。
fact `F-89963893`。

---

## 六、引用规范提醒

- 每个数字请落到**产物文件路径**,不要只写结论;本文件每节都给了路径。
- 区分**实测**与**估算**:本文件里标了 `source: measured` / `estimated from ...` 的,
  在 JSON 产物里也有同名字段,照抄即可。
- 凡引用 v0.7 的数字,**必须带上 4.4 的三条口径限制**。
- 凡引用 AAV 知识消融,**必须写明只有 1 个 seed**。
- 凡引用四策略对比,**必须写明本轮未调商业 LLM、LLM 归属为 deterministic/fallback**。
