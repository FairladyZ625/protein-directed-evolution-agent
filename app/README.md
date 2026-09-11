# T8 · GB1 定向进化 Streamlit 看板（可交互 demo）

单文件 `demo.py`，三模块，**全程只读**消费上游产物（`@st.cache_data` / `@st.cache_resource`，
不写事件流、不覆盖 `reports/` 下任何文件）。

## 运行

```bash
# 在仓库根（.venv 需含 requirements.txt 依赖，含 streamlit）
streamlit run app/demo.py     # 或 make demo
```

数据前置（均已在仓库或 `.gitignore` 约定内）：

| 文件 | 用途 | 缺失时行为 |
|---|---|---|
| `reports/campaign_metrics.json` | 模块①四策略曲线 | 模块①占位停等 |
| `reports/campaign_events*.jsonl` | 模块②五角色回放 | 模块②占位停等 |
| `data/pools/train_pool.csv` | 模块③ Ridge 拟合 | 模块③停等 |
| `data/four_mutations_full_data.csv`（46 MB，不入库） | 模块③真值/分位/推荐 oracle | 打分可用（无真值校验），推荐停等 |
| `.env`（可选，`API_KEY` 等） | 模块③(b) LLM 模式 | LLM 复选框自动禁用，不报错 |

## 三模块

1. **四策略对比**：读 T7 `campaign_metrics.json`（schema `t7.v2`），画累计 top-10 max 真实
   fitness 曲线；可选「随机多 seed 误差带」（T1 `simulate()` 只读重模拟，不触碰产物）。
2. **五角色回放**：读 T4 事件流（含 SHA-256 哈希链，页面会做链校验）。按（策略, 轮次）
   回放 Data Analyst → Hypothesis → Mutation Designer → Fitness Evaluator → Critic 的推理链；
   Critic 拒稿（若有）逐条展示。campaign 中 Critic 以 `no_knowledge=True` 运行，主事件流
   无拒稿属预期，页面如实说明。
3. **实时试玩**：
   - (a) 输入 4 位点变体 → one-hot → `RidgePredictor`（train_pool 拟合）秒级出预测 mean/var；
     有真值则给真实 fitness、全表分位与排名；越出 149,361 可测空间则明确提示「无真值」。
   - (b) 一键跑一轮 agent 推荐：复用 `evolution.campaign.run_campaign(n_rounds=1)`，展示
     top-k 推荐突变方案（预测 vs 真值）、`llm_source`、可选「严格知识校验预演」（只读跑
     `knowledge/validators`，展示知识规则与 agent 提名的「打架」），以及与模块②同源的
     五角色推理链。**事件收集进内存录制器，绝不 append 事件流文件。**
