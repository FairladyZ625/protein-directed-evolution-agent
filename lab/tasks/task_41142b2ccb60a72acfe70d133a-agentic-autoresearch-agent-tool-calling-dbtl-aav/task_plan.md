# Agentic AutoResearch agent（真 tool-calling 自主 DBTL，双模式对比，AAV 主战场）

Task Contract: harness-task v1

## Brief

现有"五角色 agent"是固定工作流 + 单次结构化 API 调用，不是真 Agentic。本任务用 **pydantic-ai** 建一个**真正自主的 tool-calling 研究智能体**（AutoResearch）：LLM 拿一组工具，自己跑定向进化的 DBTL 循环——分析已测数据、提假设、决定 exploit/explore、调用"做实验"工具花预算、看结果、跨轮改策略。**保留现有 workflow 模式不动**，新增 agentic 模式，二者与 greedy/random 在 AAV 上同预算对比。诚实检验：agentic 能否突破 greedy 在 AAV 上**可证明的天花板 7.53**（外推池真峰 8.42，预测器把峰排在 #6051/27832，纯 exploitation 数学上够不到）。

## Goal

`agent/auto_researcher.py`：pydantic-ai 驱动的自主 agent（工具 + 循环 + 事件流）。CLI 跑 AAV，产出 `reports/pool_metrics_aav_agentic.json` + 事件流 + 曲线，并与 workflow/greedy/random 对比。诚实结论写 `artifacts/agentic-findings.md`。

## Context

- **技术栈已由 CEO 验证可用**（pydantic-ai 2.42 + 我们的 OpenAI 兼容池 + claude-sonnet-5，tool-calling 实测通过 11.8s/轮）。照此骨架，勿另起炉灶：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel      # 2.42 类名（旧版是 OpenAIModel，import 兜底）
from pydantic_ai.providers.openai import OpenAIProvider
from agent.llm import llm_config                            # 读 .env：base_url(/v1)、api_key、model
cfg = llm_config()
model = OpenAIChatModel(cfg["model"], provider=OpenAIProvider(base_url=cfg["base_url"], api_key=cfg["api_key"]))
agent = Agent(model, system_prompt=SYSTEM_PROMPT)
@agent.tool_plain
def predict(variants: list[str]) -> list[float]: ...        # 用 @agent.tool_plain 注册工具
result = agent.run_sync(USER_GOAL)                           # 同步跑；result.output 是最终产物
```
  无 key/超时/池子报错要 try/except 降级（不能崩），并在事件里标注本轮用了 LLM 还是降级。

- **数据与既有件**（master，worktree `.worktrees/t-agentic` 已建 + AAV 已 symlink，勿重建）：
  - `evolution/datasets.py::load_aav(feature="one_hot")` → DatasetSpec(df[seq,fitness,hd], wt, feature_fn)。AAV 干净替换子集 38,265；冷启动 HD≤2=10,433；外推池 HD>2=27,832；峰 8.42。
  - `evolution/pool_campaign.py`：DatasetSpec + 池式口径 + 事件写法参考；`run_pool_campaign` 是 workflow 基线（勿改它，只读参考）。
  - `models/train_ladder.py::RidgePredictor`：`fit(X,y)` + `predict(X)->(mean,var)`。
  - `events/store.py::EventStore`：`append(event_type, round_id, strategy, actor, payload)` 哈希链。
  - `agent/llm.py`：池子配置。`knowledge/validators.py`：规则/BLOSUM。

## Required Reading

1. 上述接口文件 + `evolution/pool_campaign.py`（池式口径、预算 288=96×3、oracle=查表）。
2. `reports/report.html` §7 与 de-agent 声明里的**叙事红线：不吹 Agent 学到科学家思维，用消融/对比数据说话**。
3. `lab/context/development/ai4s-worker-handbook.md`（若存在）。

## Entry Conditions

- 技术栈已验证（已满足）。AAV 数据已在 worktree symlink。

## Dependencies

- 只读依赖 `evolution/datasets.py`、`evolution/pool_campaign.py`、`models/`（另一 worker de-ml 正在改这些——**你绝对不要写它们**，见 Execution Surface）。下游：CEO 汇入报告的"workflow vs agentic"章节。

## Execution Surface

- worktree `.worktrees/t-agentic`（已建，勿重建）。
- **只允许写**：`agent/auto_researcher.py`（新）、`tests/test_auto_researcher.py`（新）、`reports/pool_metrics_aav_agentic.json` / `reports/pool_events_aav_agentic.jsonl` / `reports/figures/pool_curve_aav_agentic.png`、本任务 `artifacts/`。
- **禁区（在飞 worker 正在改，绝不碰）**：`models/`、`evolution/datasets.py`、`evolution/pool_campaign.py`、`evolution/campaign.py`。这些只读复用，需要什么就 import。

## Constraints

- **工具契约**（LLM 只能通过工具与世界交互；工具内部是确定性 Python）：
  1. `analyze_measured()` → 当前已测集统计：各位点富集的替换、目前最好的若干变体+fitness、fitness 分布、（可选）上位提示。
  2. `predict(variants)` → 预测 (mean, uncertainty)，用 RidgePredictor（fit 在当前已测集上，可缓存本轮）。
  3. `list_pool(n, by)` → 从**未测外推池**取 n 个候选：`by ∈ {predicted_mean, uncertainty, random, diverse}`（池太大不能全列，给 LLM 具体候选去推理）。
  4. `test(variants)` → **做实验**：对最多"剩余预算"个变体查真值 fitness、并入已测、返回结果。**严格扣预算**（总预算=budget×n_rounds=288，同 greedy）。只有在已测池中的变体能测（oracle 查表）；不在池中的返回"无真值"。
  5. `best_so_far()` → 目前发现的最优变体与 fitness。
  6. `check_knowledge(variants)` → 规则/BLOSUM 评估（保守/激进/违规）。
- **系统提示**要让 agent 真有 agency：你是做定向进化的蛋白工程师；目标=有限实验预算内找到最高 fitness 变体；**预测器不完美（Spearman≈0.6），不要盲信它的 top**；要在 exploit（预测高分）与 explore（高不确定/上位可能/多样性）间权衡；用工具、看结果、逐轮调整。**不得在提示里泄漏峰、真值表或答案**——agent 只能通过 `test` 学习。
- **公平**：同 288 预算、同 oracle、同外推池；agentic 与 workflow/greedy/random 可比。
- **红线·不造假**：不把答案喂给 agent；如实测——agentic 若突破不了 7.53，就如实报（本身是有价值结论）。
- 事件：**每次工具调用 + 每轮 LLM 决策/推理摘要**都 append 到事件流（这是"过程报告"的数据底座，务必详尽且真实）。
- commit 作者 ZeyuLi、不提 AI；停本地 commit，不 push/PR；不碰 CI/门禁；外部/破坏性动作禁止。

## Checkpoint

- **第一回报点（务必先报再往下）**：agentic 在 AAV 上跑通一轮后，贴 **LLM 的真实工具调用轨迹**（证明它自主决策 explore/exploit，不是伪装的 greedy）+ 是否突破 7.53。命中即停并回报：pydantic-ai 接池子失败（则退 openai 原生 function-calling，同样交真 tool-calling agent）；预算扣减不对；agent 退化成纯 greedy（如实报，别掩饰）。

## CI/Gate Authority Stop Condition

- 需改门禁面则停记 blocker。

## Implementation Plan

1. `agent/auto_researcher.py`：按上方骨架建 pydantic-ai Agent + 6 个工具（闭包持有 DatasetSpec/predictor/EventStore/预算计数器）；`run_autoresearch(spec, budget, n_rounds, seed, event_store) -> report`（report schema 对齐 pool_campaign 的 `pool.v1`，strategy 名 `agentic`，便于并表）。
2. CLI：`python -m agent.auto_researcher --dataset aav --feature one_hot`，产 metrics/events/curve，并 append 主台账 `reports/experiment_log.jsonl`（用 `evolution.experiment_log.log_run`）。
3. 对比：读 workflow/greedy/random（`reports/pool_metrics_aav_one_hot.json` 已有）与本次 agentic，写 `artifacts/agentic-findings.md`：四者累计最优/强命中/样本效率；**agentic 有没有真比 greedy/workflow 强**；贴 LLM 工具轨迹节选证明"自主"。
4. `ha fact record` 记结论。

## Deliverable Contract

- `agent/auto_researcher.py` + `tests/test_auto_researcher.py`（工具预算扣减、只测池内变体、事件落盘、降级路径、复现性——LLM 部分可 mock）。`reports/pool_metrics_aav_agentic.*`。`artifacts/agentic-findings.md`（含工具轨迹节选 + 诚实结论）。回报：agentic vs greedy(7.53)/workflow/random 指标、工具调用轨迹证据、是否突破天花板（诚实）、LLM/降级占比。

## Evidence Protocol

- 阴性对照：random 最弱。真 agentic 的证据 = **事件流里 LLM 自主发起了 explore（如 list_pool by uncertainty/diverse 后 test 了预测器不看好的变体）**，不是每轮都 test 预测器 top-k。凑不出突破就如实说 agentic≈greedy 并分析原因（预测器主导 / 预算太小 / 峰不可达）。reviewer 拒收：提示泄漏答案、预算不扣、把 greedy 包装成 agentic、事件流造假。收口记一条 fact。

## Verification

- 停止点 = 定向测试绿 + 本地 commit；贴真实 agentic 输出 + LLM 工具轨迹。
- 至少记录一条 fact。
