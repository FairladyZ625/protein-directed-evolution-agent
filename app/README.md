# GB1 × AAV 定向进化科学智能体看板

**单一入口 `app/demo.py`**,顶层两个视图,**全程只读**消费上游产物
(`@st.cache_data` / `@st.cache_resource`,不写事件流、不覆盖 `reports/` 或 `harness/reports/`)。

```bash
streamlit run app/demo.py     # 或 make demo
```

`app/timeline.py` 仍可独立运行(`streamlit run app/timeline.py`),
但它已作为「研究演进」视图挂在主看板下,**日常只需要开一个网址**。

## 两个视图

### 🔬 实验看板 —— 系统现在能做什么

两个数据集、两条独立的 agent 线:

- **GB1**(四位点组合空间 V39/D40/G41/V54,野生型 `VDGV`,真值表 149,361 / 160,000)
  走**五角色 workflow 线**(`agent/pipeline.py` + `evolution/campaign.py`)
- **AAV**(28 aa,可测变体 38,265)走**自主 agent 线**(`agent/auto_researcher.py`)

| 模块 | 内容 | 数据线 |
|---|---|---|
| ① 四策略对比 | 同预算下 random / greedy / agent / knowledge_agent 的累计 top-10 真实 fitness,可选随机多 seed ±1σ 带 | GB1 |
| ② Agent 思考回放 | 读 T4 事件流(带 SHA-256 哈希链,页面做链校验),按(策略, 轮次)回放 Data Analyst → Hypothesis → Mutation Designer → Fitness Evaluator → Critic | GB1 |
| ③ 实时试玩 | (a) 变体打分 (b) 输入野生型自动推荐一轮 —— 对应试题加分项「可交互 demo」 | GB1 |
| ④ 位点集中 & 组合理由 | top-k 残基集中度;mutation_designer 的组合理由快照 | GB1 |
| ⑤ 阶数 · 保守性 · alpha | 单点/双点/多点突变优化效果、ESM-2 逐位熵保守性、预测器 alpha 扫描 | ⑤-a 用 AAV,其余 GB1 |
| ⑥ Agent 工具契约 | v0.9 契约 2×2:改工具契约后同一模型的提名是否分叉;含致死 motif 复现率与排除证据对账 | AAV |

### 🛰️ 研究演进 —— 它为什么长成这样

逐代的认知转折、当时的证据、以及被推翻过的结论。读 `app/timeline_evidence/` 的
**冻结快照**(非实时产物),含逐版本 metrics、事件回放与 SHA-256 溯源。

**收录 v0.1 → v0.9 全九代**(v0.3 是纯诊断阶段,无端到端闭环,按设计只展示代理模型扫描)。
每一代的事件流在页面加载时**重算链式 SHA-256**,哈希不符会直接报错而不是静默展示。
主线包括:v0.6 逃逸机制跑通但暴露「工具动作变了 ≠ 送测批次变了」的判据危机;
v0.8 强制注入残差而四臂送测集合逐位相同;v0.9 换契约后同一模型的提名立刻分叉。

## 数据前置

缺文件时对应面板**占位停等并给出补齐命令**,不静默空白,其余面板不受影响。

| 数据 | 用于 | 缺失时 |
|---|---|---|
| `harness/reports/workflow-v1.*/gb1/campaign_*.metrics.json` | 模块① | ① 停等,提示 `make campaign` |
| 同目录 `campaign_*.events.jsonl[.gz]` | 模块② | ② 停等(`.jsonl` 会透明回退到 `.gz`) |
| `data/pools/train_pool.csv` | 模块③ Ridge 拟合 | ③ 停等 |
| `data/four_mutations_full_data.csv`(46 MB,不入库) | 模块③ 真值/分位/推荐 oracle | 打分可用(无真值校验),推荐停等 |
| `harness/reports/analysis-v0.1/<ds>/` | 模块④⑤ | 对应面板停等 |
| `harness/reports/v09-contract/<四臂>/` | 模块⑥ | ⑥ 停等,提示 `scripts/run_v09_contract.sh` |
| `.env`(可选,`API_KEY` 等) | 模块③(b) LLM 模式 | LLM 复选框自动禁用,不报错 |

## 测试

`tests/test_demo_app.py` 与 `tests/test_timeline.py`,**两者都在 CI 门里**
(`.github/workflows/ci.yml`)。覆盖首屏渲染、六个 tab、顶层视图切换、模块③打分与
越界提示、模块⑥的批次分叉判据与排除证据对账、以及只读纪律。
