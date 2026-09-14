# 前端补齐:五个「有数据没界面」的展示面板

## Brief

`app/demo.py` 现有三个模块(① 四策略对比 / ② 五角色回放 / ③ 实时试玩)做得不错,
但 CEO 逐条核对试题后发现**五项要求的数据已经产出、界面一次都没展示**。
这些不是新实验,是把已有产物接到界面上。

## Goal

评委打开 demo 能看到试题「结果分析与展示」和加分项要求的**全部**内容,
不需要去翻 JSON 文件。

## Context

试题相关原文:
- 「二、结果分析与展示 b. 分析推荐突变是否集中在关键位点」
- 「三、详细要求 → 结果展示 → d. 展示 Agent 的推理过程 … iii. 为什么组合某些突变」
- 加分项③「比较单点突变、双点突变和多点突变的优化效果」
- 加分项④「引入蛋白质结构信息或保守位点分析」

CEO 核对结果(`grep` 实测):`topk_concentration` / `combination_rationale` /
`mutation_order` / `conservation` / `alpha_sweep` 在 `app/demo.py` 里出现 **0 次**。

## Required Reading

先读这些产物,**它们是唯一真源,界面只做展示不做计算**:

| 面板 | 数据文件 | 关键字段 |
|---|---|---|
| 位点集中分析 | `lab/reports/workflow-v1.1/gb1/campaign_easy.metrics.json` | `strategies.<策略>.topk_concentration.positions.<位点>` 下的 `residue_counts` / `dominant_residue` / `dominant_fraction` / `mutation_fraction`,以及 `n_topk_observations` |
| 组合理由 | `lab/reports/workflow-v1.1/agent_combination_rationales.json` | `selected_single_mutations` / `empirical_position_gains` / `positions_non_conflicting` / `rule_ids` / `deterministic_summary` / `evidence_source` / `narrative_source` |
| 突变阶数 | `lab/reports/analysis-v0.1/{gb1,aav}/mutation_order.json` | `distribution_by_order` / `additive_extrapolation` / `epistasis_by_order` / `lower_order_coverage_by_order` |
| 保守位点 | `lab/reports/analysis-v0.1/{gb1,aav}/conservation.json` | `positions` / `correlations` / `true_peak_positions` / `entropy_definition` |
| alpha 扫描 | `lab/reports/workflow-v1.0/gb1/predictor_alpha_sweep.json` | 每个 `<特征>__<划分>__<预处理>` 的 `alpha_selected` / `test_spearman_at_selected` / `test_spearman_by_alpha` |

也读 `app/demo.py` 现有三个模块的写法,新面板要与它们风格一致。

## Entry Conditions

worktree 与分支由 CEO 备好(见 Execution Surface),基于最新 `origin/main`。
`.venv` 已符号链接。`streamlit run app/demo.py` 应能直接起来。

## Dependencies

无阻塞。数据全部已在主线。

## Execution Surface

**只动** `app/demo.py`、`tests/test_demo_app.py`、`README.md` 的 demo 一节。

**不要动** `evolution/`、`agent/`、`models/`、`knowledge/`、`events/`、
`lab/reports/` 下任何数据文件。界面**只读**产物,不重算、不覆盖。

## Constraints

- **保住现有的只读纪律**:`@st.cache_data` / `@st.cache_resource` 缓存加载,
  绝不 append 事件流、绝不覆盖 `reports/` 或 `lab/reports/` 下任何产物。
  模块③的推荐事件只进内存 recorder。**这条纪律不得因为加面板而破坏。**
- 模块①②③ 现有行为不变,新面板**并列新增**,不要重构掉现有的。
- **数据缺失要诚实降级**:任一 JSON 不存在时,该面板显示明确提示
  (缺哪个文件、跑哪条命令能生成),**不静默空白、不假装有数据**。
- **口径标注不得省略**(诚实性要求):
  - 保守位点面板必须写明「ESM-2 熵是自然度先验,仅用于事后分析,**未接入采集或筛选路径**」;
    并突出真峰三位点的名次(D0Q 第 1、V18A 第 4、S17E 第 26)——
    这说明保守性先验会先丢掉 D0Q,是个负结果,不要美化成正面卖点。
  - 突变阶数面板要标出 AAV `0..2→3` 那行的**留出验证 0.9094 vs 测试 0.6155**,
    并说明留出集是同阶的、系统性高估了跨阶外推能力。
  - alpha 扫描面板要说明**为什么不能固定 alpha**:固定 `alpha=1` 时 esm2 从 raw 0.4911
    掉到标准化 0.2944,结论随预处理反向;调过 alpha 后收敛到 0.4893/0.4916。
  - 组合理由面板要把 `evidence_source`(实测统计量)与 `narrative_source`(LLM/确定性文本)
    分开显示,**不许把 fallback 的理由展示成 LLM 推理**。
- 图表内文字用英文(评测机可能缺中文字体,现有 `FIGURE_LABELS` 就是为此)。

## Checkpoint

若某个面板在不改数据文件的前提下做不出来(例如字段形状不够),
**带证据回报并停手**,不要自己去改产物或重算数据。

## CI/Gate Authority Stop Condition

停止点 = `pytest tests/test_demo.py tests/test_demo_app.py` 绿 + commit。
**不 push、不发 PR。** 不要跑全量测试矩阵。

注:`tests/test_demo_app.py` 目前有 **3 个既存失败**
(`test_module1_renders_strategy_metrics`、`test_module2_renders_role_chain_and_chain_status`、
`test_recommender_button_runs_one_round_in_memory`)。CEO 已二分确认它们在
`f3a4179`/`f40e901`/`HEAD` 三点完全一致,**是既存缺陷不是回归**,真因是模块①②在
AppTest 下不渲染内容,未定位到具体早返回分支。**顺手修掉它更好**(那样这个文件就能进
CI 门控);修不掉就在 closeout 里写明,不要为了变绿去削断言。

## Implementation Plan

新增五个面板,建议做成主 tab 的第④⑤两个(分析类合并)或各自独立,你判断:

1. **位点集中分析**:按策略 × 位点展示残基分布(柱图)、主导残基及其占比、突变占比。
   这直接回答「推荐突变是否集中在关键位点」。
2. **组合理由**:表格或卡片,每个候选一行,展示选了哪几个单点、各自实测增益、
   位点是否冲突、命中哪些规则、以及那句 `deterministic_summary`。
3. **突变阶数比较**:四层数据各一图/表;**低阶完整覆盖率那一列是重点**
   (2 阶 1.000 → 3 阶 0.312 → 4 阶 0.022),它解释了为什么高阶峰学不到。
4. **保守位点**:逐位置熵曲线 + 保守性名次表 + 真峰三位点高亮 + 与实测效应的相关(带 p 值)。
5. **alpha 扫描**:每个组合的 `test_spearman_by_alpha` 曲线,标出选中的 alpha。

## Deliverable Contract

- 改造后的 `app/demo.py`。
- `tests/test_demo_app.py` 补测试:每个新面板至少一条断言它渲染出了关键字段;
  数据缺失时断言出现明确提示而非空白。
- `README.md` 的 demo 一节列出全部面板。

## Evidence Protocol

- **阳性对照必做**:把某个 JSON 临时改名,断言对应面板给出「缺文件」提示而不是空白或崩溃。
- 每个面板上的数字要能在源 JSON 里找到同名字段,**不要在界面里重算**。
- 截图或 `AppTest` 输出作为渲染证据。

## Verification

- CEO 会自己 `streamlit run app/demo.py` 逐个面板点一遍。
- CEO 会抽查面板上的数字与源 JSON 是否一致。
- CEO 会临时改名一个 JSON,确认降级提示出现。
