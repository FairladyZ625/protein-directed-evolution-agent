# 蛋白质定向进化科学智能体 — GB1 × AAV

*[English version](README.md)(默认版本)*

一个小规模的**机器学习引导的虚拟定向进化**系统,跑在两个真实的深度突变扫描(DMS)景观上。
从实测突变数据训练适应度预测器,让 agent 逐轮提出突变方案,并用**真实实测景观**作为
「虚拟湿实验」的 oracle——**永远不用模型自己的打分**当真值。两个数据集、两条独立的
agent 架构、一套可审计的事件内核。

完整实验报告:
**[`reports/final-report-v0.6/scientific_report_v0.6_two_column.pdf`](reports/final-report-v0.6/scientific_report_v0.6_two_column.pdf)**
(markdown 源文件:[`reports/final-report-v0.6/report.md`](reports/final-report-v0.6/report.md))。

## 核心结论:工具契约决定 agent 自主性的上限

本项目最锋利的一个发现与模型无关。在某一套工具契约下,把上一轮的预测残差强制注入 agent 的
prompt,**什么都没有改变**:反思开与反思关产出的批次**逐位相同**,48/48 个变体 × 6 轮,
两种采集策略下皆然。agent 读了证据、在总结里讨论了那些致死 motif,然后提名了完全一样的候选。

这不是模型的失败。查代码后确认根因是**契约的形状**:`exploit_ratio` 是一个标量,而
**没有任何标量取值能表达「别选带 N21D 的候选」**。唯一可执行的入口根本不存在,
所以反思卡片末尾那条行动约束按构造就无处着力,只能落在叙述层。

加上一个残基级的排除入口(同时删掉劝退 agent 设定比例的提示词、释放利用比地板)之后,
结果立刻改变——**同一个模型、同一个 seed、同一份注入文本**:

| | v0.8 契约 | v0.9 契约 |
|---|---|---|
| agent 自己设定 `exploit_ratio` | **0 / 20 次调用** | **11 / 11 次调用** |
| 反思开/关是否让批次分叉 | **否**(六轮全同) | **是**,且逐轮发散(r1 46/48 → r6 8/48) |
| 后段致死 motif 复现率 | 13.9% | **6.2%** |

agent 排除的每一个 motif 都能追溯到此前注入的残差证据——20 次排除,**零凭空捏造**。
而且证据标记了 34 个 motif,它只排了 20 个:是**有选择**,不是一刀切。

**必须同时说明的边界:** 单 seed(42);契约是**复合处理**(提示词 + 地板 + 排除入口),
本工作**没有**拆开测各自的贡献;strong 命中差(158 / 153 / 160)太小,不能当效应量。
换协议的复现结果、以及被它证伪的一条早期结论,见
[`reports/final-report-v0.6/v07-handoff-02-protocol-and-chapter8.md`](reports/final-report-v0.6/v07-handoff-02-protocol-and-chapter8.md)。

## 仓库结构:两棵树,两种职责

- **`reports/`** —— *报告撰写*树:`final-report-v0.x/` 存放每一版报告的 markdown、
  图表、构建脚本与渲染出的 PDF。
- **`harness/reports/`** —— *实验产物*树:每个研究周期一个自包含文件夹,命名
  `<方法线>-v<版本>/`(布局的唯一真源是 `evolution/results_layout.py`)。当前的方法线:
  `workflow-v1.2`(GB1 上的交付流水线)、`agentic-v0.7`(AAV 上的自主研究者)、
  `v09-contract` / `v09-contract-b12`(工具契约因子实验)、`analysis-v0.1`(只读分析线)。
  给报告撰写者的修订摘要在
  [`harness/reports/REPORT-HANDOFF.md`](harness/reports/REPORT-HANDOFF.md)。

## 数据集

### GB1 —— 蛋白 G 结构域 B1,四位点组合空间

- 56 aa 蛋白,可变位点 V39/D40/G41/V54 —— Wu et al. 2016(*eLife*)。
  野生型 `VDGV`(适应度归一化为 1.0);全局最优 `FWAA` = **8.762**(HD=4)。
- 20⁴ = 160,000 种组合里有 **149,361 个实测变体**,其余 **10,639 个是真的没有实测数据**。
  所有策略的提名与评估都严格限制在实测集合内——这个局限如实报告,不掩盖。
- 原始 44 MB 的 `four_mutations_full_data.csv` **不入库**。请自行下载放到 `data/` 下
  (来源:<https://doi.org/10.7554/eLife.16965.024>),然后 `make data` 校验。
  **自动下载是刻意关闭的**——脚本永远不会伪造数据。

### AAV —— 腺相关病毒衣壳,28 aa 窗口

- 野生型 `DEEEIRTTNPVATEQYGSVSTNLQRGNR`(实测适应度 −0.918);**38,265 个实测变体**。
- campaign 按汉明距离切分:**冷启动 HD≤2(10,433 个)** 代表「已完成的实验」;
  **候选池 HD>2(27,832 个)** 是 agent 要去提名的未知空间。
- **一条必须写清的设定事实:** 候选池的真实最大值是 **8.416205**,而冷启动里已经含有一个
  更高的 incumbent **9.536457**——全表最优本身就落在 HD=2。候选池里超过它的候选是
  **0 个**。所以「agent 从未超越 incumbent」是**切分方式的性质,不是 agent 的失败**,
  不得写成后者。

## 适应度预测模型

三级梯队,统一的 `fit → predict(mean, var)` 接口,5-seed 深度集成给出不确定性
(`models/train_ladder.py`):one-hot + Ridge、梯度提升、MLP;特征为 one-hot(80 维)
或 ESM-2 650M 嵌入(1280 维)。指标:Spearman(主)、Pearson、MSE、Top-k 命中率,
外加显式的 `high_fitness_analysis.top_1pct_recall`。

| 特征 × 切分 | Ridge | GBoost | MLP |
|---|---|---|---|
| one-hot × 随机切分 | 0.484 | 0.474 | 0.389 |
| ESM-2 × 随机切分 | 0.493 | 0.377 | 0.491 |
| one-hot × HD 外推(训练 HD≤2 → 测试 HD≥3) | 0.358 | 0.354 | 0.278 |
| ESM-2 × HD 外推 | 0.404 | 0.352 | **0.493** |

留出集上的 Spearman。在更难的 HD 外推切分上 one-hot 急剧退化,而 ESM-2 明显更能泛化——
这是本项目使用蛋白质语言模型的主要论据。AAV 的 campaign 用的是**成对交互(上位感知)代理**,
它把真峰的预测排名从第 2,776 位提到第 429 位——加性特征会把真峰甩到任何 288 次提名预算之外。

## 两条 agent 线

本仓有**两套独立的 agent 架构**。它们共用事件内核与知识库,但**没有交叉 import**,
回答的也是不同的问题。

### 一、五角色 workflow 线 —— `agent/pipeline.py` + `evolution/campaign.py`(GB1)

模块化流水线,每个角色的输入输出都由 Pydantic 校验;LLM 被限制在两个可注入端口内,
其余全部确定性、可审计:

1. **Data Analyst** —— 从训练池统计逐位点替换的适应度。
2. **Hypothesis Generator**(*LLM 端口*)—— 提出值得组合的替换;未配置 LLM 或调用失败时
   回退到确定性的「每位点 top-k」生成器。
3. **Mutation Designer** —— 枚举组合文库(每位点最多 1 个替换)。
4. **Fitness Evaluator** —— 用预测器给候选打分 `(mean, var)`。
5. **Scientific Critic**(*LLM 端口 + 知识规则*)—— 带理由地校验/接受/拒稿;
   `no_knowledge` 开关可关闭知识门禁用于消融。

### 二、自主研究者线 —— `agent/auto_researcher.py`(AAV)

一个真正的工具调用 agent(pydantic-ai),跨轮保留 `message_history`,自己决定调什么:
`analyze_measured`、`predict`、`list_pool`、`compose_batch`、`redirect_batch`、
`check_knowledge`、`test_composed_batch`。采集比例归它自己掌握;在 v0.9 契约下还多一个
残基级的 `exclude_motifs` 入口。**契约实验跑的就是这条线。**

LLM 端口通过 `agent/llm.py` 调用 OpenAI 兼容的模型池,凭据读本地 `.env`
(见 `.env.example`,永不入库)。没有 key 或任何报错时自动降级到确定性路径,
所以**本项目可以完全离线运行**;每一轮都会记录它用的是实时 LLM 还是回退路径。

## 四策略闭环对比

`evolution/campaign.py` 在**同一预算**、**同一 oracle**(实测表查表,绝不用模型打分)、
**同一提名空间**下跑完四个策略。三种冷启动设定用来诚实地评估难度:

- `--cold-start random`(**easy**):稠密随机种子池(约 98% 已经是 HD≥3)。
- `--cold-start low_hd`(**hard**,推荐默认):只从 HD≤2 起步,向 HD≥3 外推。
- `--cold-start low_hd --max-cold-hd 1`(**sparse**):只用 77 个单突变起步。

hard 档(HD≤2 外推),seed 42:

| 策略 | 累计最高适应度 | strong(≥4) | 有益命中 |
|---|---|---|---|
| random 随机基线 | 5.08 | 1 | 7 |
| greedy 贪心(Ridge 全空间) | 8.762 | 43 | 154 |
| agent(无知识) | **8.762** | **56** | **187** |
| knowledge agent(UCB + BLOSUM 先验) | **8.762** | **57** | **190** |

**诚实的发现:** GB1 的四位点景观本身是**可解的**——哪怕只从 77 个单突变起步,
基于模型的策略也能在第 2 轮达到全局最优,而随机基线远远落后。所以「能否达峰」不是区分点,
真正有意义的差异是**样本效率**与**批次产出**。同样的饱和现象在 AAV 上也出现:
八个契约实验臂**全部在第 2 轮(共 6 轮)达到候选池真实最优**,即
**67% 的预算花在答案已经找到之后**。把每轮预算减半后达峰推到第 4 轮(浪费降到 33%),
但没有消除。**指标一旦饱和就失去区分力**——因此 campaign 同时报告
**致死 motif 复现率**,这个指标不饱和。

## 知识增强与可审计轨迹

`knowledge/` 存放氨基酸理化性质、BLOSUM62 分级、突变数量 / 终止密码子规则(`rules.yaml`)、
校验器,以及一个小型 `networkx` 三元组图,实现了
`has_property` / `occurs_at` / `contains` / `improves` / `changes_to` 五种关系。
知识增强 agent 额外加了 UCB 探索(`mean + λ·√var`)与 BLOSUM62 保守性先验;
`--no-knowledge` 同时消融两者。

`events/` 是一个只追加、链式 SHA-256 的事件日志(外加 SQLite 投影与回放 CLI):
每一个 campaign 步骤与 agent 工具调用都被记录且可 `verify()`,其中包含**逐变体的
提名时刻预测与残差**(`campaign.oracle.residuals`、`agent.tool.test.residuals`)。
另外,**每一次实验运行**都会向主台账
[`harness/reports/experiment_log.jsonl`](harness/reports/experiment_log.jsonl)
追加一条不可变记录(命令、参数、git commit、产物 SHA-256、摘要)。

**范围说明(诚实起见):** 该台账覆盖主要的闭环实验,但**尚未覆盖全部历史运行**——
`analysis-v0.1` 线与部分早期 `agentic` 版本没有登记在内。请把它当作一条局部的、
只追加的主干;每个版本目录自己的 `manifest.json` 与逐次运行的 `metrics.json`
才是该次运行的权威。

## 交互式看板

`app/demo.py` —— 单文件 **Streamlit** 看板(全程只读),顶层两个视图。

**🔬 实验看板** —— 六个 tab:

| tab | 内容 | 数据线 |
|---|---|---|
| ① 四策略对比 | 同预算下的累计 top-10 真实 fitness,可选冷启动设定,随机基线可开多 seed ±1σ 带 | GB1 |
| ② 五角色思考回放 | 读 T4 事件流,页面内做哈希链校验,按(策略, 轮次)回放五个角色的推理链 | GB1 |
| ③ 实时试玩 | (a) 变体打分 (b) **输入野生型自动推荐一轮** | GB1 |
| ④ 位点集中 & 组合理由 | 逐策略的 top-k 残基分布;agent 的组合理由与实测单点增益(`evidence_source` 与 `narrative_source` 分开展示——确定性回退的叙述**绝不**冒充 LLM 推理) | GB1 |
| ⑤ 阶数 · 保守性 · alpha | 单点/双点/多点突变对比、ESM-2 逐位保守性(**如实展示其负结果**)、Ridge alpha 扫描 | ⑤-a 用 AAV,其余 GB1 |
| ⑥ Agent 工具契约 | v0.9 因子实验:改契约后同一模型的提名是否分叉——批次分叉表、致死 motif 复现率、以及**排除的 motif 与注入证据的逐轮对账** | AAV |

**🛰️ 研究演进** —— 这套系统自己是怎么长出来的:逐代的认知转折、当时手上的证据、
以及后来被推翻的结论。

每个面板都**诚实降级**:缺产物时明确显示缺哪个文件、以及重新生成它的确切命令——
不会静默空白,也不会崩。

```bash
streamlit run app/demo.py     # 或 make demo
```

## 安装与运行

对于全新 clone 的 Linux / macOS 环境,推荐的首次运行是两条命令:

```bash
./scripts/install.sh       # Python 3.11+,离线 smoke/demo/test 档;不装 torch、不下载数据
./scripts/run_all.sh       # 必跑 smoke;CSV 存在时再跑预测器 + GB1 campaign
```

第一条命令创建 `.venv` 并安装与自包含 CI 测试相同的科学计算栈,外加 smoke 路径所需的
离线 agent 运行时。它**刻意不安装** PyTorch、也不下载数据。需要本地跑 ESM-2 特征提取时用
`./scripts/install.sh --full` 追加 PyTorch 与 fair-esm;GB1 的 CSV 始终是一次独立、
显式的下载,说明见 [`data/README.md`](data/README.md)。CSV 缺失时 `run_all.sh` 会打印
明确的降级提示并在 smoke 之后正常结束。

手工入口:

```bash
# 全新 clone 的第一条命令:不需要 CSV、ESM 缓存或 API key
make smoke                                            # 合成小景观 -> tmp/smoke/
make test                                             # 自包含测试(与 CI 同一组)
make data                                             # 校验本地提供的完整 GB1 CSV
python -m models.evaluate_all                         # 预测器梯队 + 标准化消融
python -m models.alpha_sweep                          # 逐特征的答案无关 alpha 选择
python -m evolution.campaign --cold-start low_hd      # GB1 四策略 campaign(hard 档)
python -m agent.auto_researcher --dataset aav --guardrail \
    --surrogate epistasis --backtrack semi            # AAV 自主研究者
scripts/run_v09_contract.sh tmp/v09 42                # 工具契约 2×2(四臂,约 25 分钟)
python3 scripts/compare_v08_arms.py tmp/v09           # 各臂对照:批次分叉 + 复现率
streamlit run app/demo.py                             # 交互式看板
cp .env.example .env                                  # 可选:填 LLM 池 key,然后加 --use-llm
```

**`make smoke` 是推荐的首次运行。** 它在一个固定的、合成的 16 变体景观上跑通
数据 → 预测器 → 五角色 agent → 四策略 campaign 全链路,并把带标签的 CSV、metrics、
事件流、SQLite 读投影、图和 README 写到 `tmp/smoke/`。它走离线确定性 LLM 回退路径。
**它那些合成小规模的数字只是可复现性演示,绝不可与正式结果并列比较。**

## 目录结构

```
data/             GB1/AAV 加载器与校验、三池切分、manifest
features/         one-hot 与 ESM-2 特征提取(带缓存)、保守性熵
models/           预测器梯队 + 指标 + alpha 扫描
agent/            五角色流水线(GB1)与自主工具调用研究者(AAV)
evolution/        突变解析、随机基线、四策略 campaign、实验台账
knowledge/        突变规则 + 知识图谱 + 校验器 + 消融
events/           可审计事件流内核、残差反思
analysis/         只读分析(突变阶数、ESM zero-shot 扫描)
app/              Streamlit 看板(实验视图 + 研究演进视图)
scripts/          安装、run_all、smoke、因子实验跑批、引用检查器
reports/          报告撰写树(final-report-v0.x:markdown、图、构建、PDF)
harness/reports/  实验产物,每周期一个文件夹 + 实验台账
tests/            单元测试(CI 那组是自包含的:不需要 CSV、网络或 API key)
```

## 外部资源

GB1 数据集(Wu et al. 2016 / *eLife*);AAV 深度突变扫描数据;ESM-2(`fair-esm`,
`esm2_t33_650M_UR50D`);scikit-learn / PyTorch。LLM agent 通过可注入端口调用
OpenAI 兼容的模型池(凭据在本地、不入库的 `.env` 中);所有外部模型/数据的使用
均已在报告中声明。
