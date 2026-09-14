# T8 Streamlit 看板 + 可交互 demo（题目⑥ + 加分项）

Task Contract: harness-task v1

## Brief

单文件 Streamlit 看板三模块：四策略对比曲线、五角色 Agent 思考过程回放（读 T4 事件流）、任意序列实时试玩器（输入变体→调 T3 模型秒级出分）。对应题目「可交互 demo」加分项。

## Goal

`app/demo.py`（单文件，只读消费 T7 产出与 T4 事件流）。三模块：①四策略曲线看板（读 `reports/campaign_metrics.json`）②Agent 思考回放（读事件流，按轮/策略回放五角色推理与积木「打架」案例）③实时试玩器（输入 4 位点变体→ESM/one-hot 特征→T3 模型出 mean/var）。交付给评审与泽宇演示；第一个使用方：面试 demo。

## Context

- task：搭前端看板。decision：前端收敛为极简 Streamlit 单文件三模块（新版方案）;event-stream 是回放模块的数据底座。
- 读写分离红线：Streamlit 只读（`@st.cache_data`），严禁顶层 append 事件。

## Required Reading

1. `lab/context/architecture/AI4S-master-plan.html`（交付层：Streamlit 三模块、演示动线）— 权威：设计。
2. T7 `reports/campaign_metrics.json` schema、T4 replay 读取接口、T3 模型加载接口 — 权威：上游契约。

## Entry Conditions

- T7 产出与 T4 事件流样例、T3 模型接口就绪；缺失则相应模块占位并停等。

## Dependencies

- 上游：T7 + T4 + T3。下游：面试 demo / T9 录屏素材。判定满足：三模块本地 `streamlit run` 可交互。

## Execution Surface

独立 worktree + 任务分支，base=main。允许写入：`app/`、`requirements.txt`（补 streamlit）、`tests/`（如有）。绝对 cwd 由派工注入。

## Constraints

- 单文件、只读消费上游产物,不重算实验、不写事件流。
- 实时试玩器提名限定 149,361 可测变体或明确提示「无真值」。外部/破坏性动作禁止。

## Checkpoint

命中即停：需改上游产物 schema、试玩器越出可测空间无提示。计划回报点：三模块本地跑通后。

## CI/Gate Authority Stop Condition

非 CI/gate 任务；需改门禁面则停止记 blocker。

## Implementation Plan

- 模块①：读 campaign_metrics.json 画四策略曲线（随机带误差带）。
- 模块②：读事件流,slider 回放某轮某策略的五角色推理链与 Critic 拒稿案例。
- 模块③：输入框收 4 位点变体→特征→T3 predict→显示 mean/var 与在 landscape 的分位。
- `ha fact record` 晋升「三模块本地可交互」。

## Deliverable Contract

`app/demo.py` + 运行说明。回报字段：三模块运行截图/说明、`streamlit run` 命令、依赖补充。

## Evidence Protocol

CEO 亲验：本地 `streamlit run` 跑一遍三模块。reviewer 拒收：模块写事件流、试玩器越界无提示、依赖未声明。收口记一条 fact（含运行证据）。

## Verification

- 停止点 = 便宜确定性门全绿 + 本地 `streamlit run` 三模块可交互 + 本地 commit。
- 验收：CEO 亲自上手用一遍（使用满意度门）。
- 至少记录一条 fact。

## CEO 补充（现状接口 + 交互动线，以最新 master 为准）

四策略引擎与五角色 Agent 已合入 master 并跑通，demo 只读消费其产出。**streamlit 已在 .venv 装好**（也已进 requirements.txt 待你确认），可直接 `streamlit run`。

**模块① 四策略对比**：读 `reports/campaign_metrics.json`（schema `t7.v2`）。字段：
`strategies.<name>.rounds[]` 每轮含 `round / top10_max / top10_mean / n_hit_beneficial / hit_rate_beneficial / cum_top10_max / cum_top10_mean / cum_n_strong / top10(=[[variant,fitness],...]) / pool_size_after`，agent 策略额外有 `llm_source`；顶层有 `summary`（每策略 `cum_top10_max_curve` 等）、`oracle`、`candidate_space_size(=149361)`、`budget_per_round(=96)`。四策略名：`random / greedy / agent_no_knowledge / knowledge_agent`。画累计 top10_max 提升曲线（random 可多 seed 画误差带，选做）。

**模块② 五角色推理回放**：读 `reports/campaign_events.jsonl`（每行一个 JSON 事件，字段 `seq/ts/event_type/round_id/strategy/actor/payload/prev_hash/hash`）。`actor` ∈ {campaign, data_analyst, hypothesis_generator, mutation_designer, fitness_evaluator, scientific_critic}；`event_type` ∈ {campaign.started, campaign.round.completed, campaign.completed, agent.role.completed}。用 slider 选（策略, 轮次）回放该轮五角色事件链：Data Analyst 的 position_gains、Hypothesis 的 rationale/rule_ids、Mutation Designer 的候选、Fitness Evaluator 的 mean/var、Scientific Critic 的 rule_check/接受与否。可直接读 jsonl，或用 `from events.replay import ...`（先 inspect 接口）。

**模块③ 实时试玩 + 自动推荐（对应题目「输入野生型序列后自动推荐突变方案」）**：两个动作——
- (a) *打分*：输入 4 位点变体（WT=`VDGV`，位点 V39/D40/G41/V54）→ 特征 `from features.one_hot import encode_one_hot` → 模型 `from models.train_ladder import RidgePredictor`（在 `data/pools/train_pool.csv` 上 `fit`，用 `@st.cache_resource` 缓存）→ 显示 mean/var 及在 landscape 的分位（`from evolution.random_baseline import load_landscape`；越出 149361 可测空间要提示「无真值」）。
- (b) *自动推荐*：给定预算/策略（agent_no_knowledge / knowledge_agent）/知识开关 → 跑一轮 agent 推荐 → 展示 Top-k 推荐突变方案 + 五角色推理。推荐逻辑复用 campaign：`from agent.pipeline import run_pipeline` 或直接调 `from evolution.campaign import run_campaign`（`n_rounds=1`，传 `event_store` 收集事件供模块②同源展示）。**默认确定性**（不调 LLM，秒级出结果）；提供一个「用 LLM（较慢，可能降级）」checkbox → 走 `use_llm=True`（`agent.llm` 读 `.env`，异常自动降级，UI 要显示本轮 `llm_source`）。

**纪律**：单文件 `app/demo.py`；只读，`@st.cache_data`/`@st.cache_resource`，**绝不 append 事件、不重算并覆盖 campaign 产出**；不做外部/破坏性动作。产出附 `app/README` 或 demo 顶部说明 + `streamlit run app/demo.py` 命令。`.env` 不存在时模块③(b) 的 LLM 选项自动禁用并提示，不报错。
