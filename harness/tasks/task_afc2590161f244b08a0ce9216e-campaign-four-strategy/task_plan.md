# T7 campaign 对比引擎 + 四策略 × 3 轮闭环（题目⑤⑥核心）

Task Contract: harness-task v1

## Brief

把 T1 随机基线泛化成通用 campaign 引擎：统一预算/oracle/三池/提名口径,可插拔四种策略,做满 3 轮主动学习闭环（提名→查真值→回填重训）,产出四策略对比表+提升曲线+事件流记录。这是整份笔试的最重关卡。

## Goal

`evolution/campaign.py` + 对比产出（`reports/campaign_metrics.json` + 提升曲线图 + 每轮 Top-k）。四策略：①随机（复用 T1 `propose_random`,多 seed 均值±带）②模型贪心（T3 predict top-k）③LLM Agent 无知识（T6，`--no-knowledge`）④知识增强 Agent（T6 + T5 + UCB=mean+λ√var）。交付给 T8（看板）与 T9（失败分析/报告）；每轮每策略 append 事件到 T4。

## Context

- task：四策略对比闭环。decision：提名/评估空间统一限定 149,361 可测变体,四策略同口径,缺失 10,639 记为已知局限。fact：T1 已提供策略①实现与稳定 JSON schema（round/top10_max/top10_mean/n_hit_nonzero）。
- 关键实验诚实性：oracle=真值查表（非模型自评）;要测「样本效率」（固定预算下最优 fitness 与命中率）,不只看终值。

## Required Reading

1. `harness/context/research/AI4S-assignment.md`（题目⑤⑥：四方法对比、逐轮提升、集中关键位点）— 权威：题面。
2. `evolution/random_baseline.py`（策略①实现与 JSON 契约,直接复用）— 权威：现状。
3. `harness/context/architecture/AI4S-master-plan.html`（DBTL 闭环、UCB、四策略）— 权威：设计。
4. T3 模型接口、T6 Agent 接口、T4 事件 append 接口 — 权威：上游契约。

## Entry Conditions

- T3（模型）、T6（Agent）、T1（策略①）就绪；任一缺失则相应策略停等,但引擎骨架与策略①②可先行。

## Dependencies

- 上游：T3 + T6 + T1。下游：T8（读产出与事件）、T9（失败分析）。判定满足：四策略在同一预算/oracle 下跑满 3 轮,产出对比表+曲线。

## Execution Surface

独立 worktree + 任务分支，base=main。允许写入：`evolution/campaign.py`、`reports/`（campaign 产出）、`tests/`。绝对 cwd 由派工注入。

## Constraints

- 四策略共用同一预算（每轮 Top-10 或与 T1 一致的口径,写死一处）、同一 oracle、同一三池、同一提名空间（149,361）。
- 复用 T1 的 `propose_random/simulate/build_report`,不重写策略①;随机策略跑多 seed 画均值±带。
- 回填重训每轮把新测数据并入 train_pool 重训 T3 模型。外部/破坏性动作禁止。

## Checkpoint

命中即停：四策略口径不一致、提名越界、oracle 用了模型预测（自评陷阱）、牵连上游文件面。计划回报点：策略①②对比跑通后、四策略跑满 3 轮后。

## CI/Gate Authority Stop Condition

非 CI/gate 任务；需改门禁面则停止记 blocker。

## Implementation Plan

- 抽象 `Strategy` 接口 `propose(pool, budget)->candidates`;策略①②纯代码,策略③④调 T6。
- 统一 campaign loop：提名→查真值 oracle→回流→回填重训→下一轮;每步 append 事件到 T4。
- 产出：四策略对比表（逐轮 top-k_max/mean、命中率、累计最优）+ 提升曲线（随机带误差带）+ 每轮 Top-k 变体与集中位点分析。
- `ha fact record` 晋升「四策略 3 轮后各自累计最优 fitness 与样本效率」。

## Deliverable Contract

代码 + `reports/campaign_metrics.json` + 曲线图 + 事件流样例 + 定向测试。回报字段：四策略逐轮指标、累计最优、样本效率对比、事件条数。

## Evidence Protocol

阴性对照：策略①随机应显著弱于②③④（沿用 T1 的负对照口径）;策略④在样本效率上应≥②③（否则如实报告为失败案例）。reviewer 拒收：口径不统一、oracle 用模型预测、无样本效率视角。收口记一条 fact。

## Verification

- 停止点 = 便宜确定性门全绿 + 定向测试全绿 + 本地 commit。
- 定向测试：`tests/test_campaign.py`（策略接口、四策略同口径、oracle 查表、回填重训、事件落盘、复现性）;贴真实输出。
- 至少记录一条 fact。

## LLM Runtime 补充(GLM,策略③④)

- 策略③④ 通过 `agent.pipeline.run_pipeline(pool, predictor, llm_hypothesis=..., llm_critic=...)` 注入 LLM 端口(callable,输入/输出 Pydantic schema)。
- 本机可用 LLM = **GLM**(env:`GLM_API_KEY`;另有 `ANTHROPIC_GLM_BASE_URL` / `ANTHROPIC_GLM_AUTH_TOKEN` 的 Anthropic 兼容端点)。用 `openai` 客户端指向 GLM 的 OpenAI 兼容端点(base_url 从 env 读取,缺省用 GLM 默认如 `https://open.bigmodel.cn/api/paas/v4`),模型选 `glm-4` / `glm-4-flash` 一类;或用 Anthropic 兼容端点。
- **降级**:无 key 或 API 报错时,传 `None` 走 pipeline 的确定性 fallback(已支持);在事件/日志标注本轮策略③④走的是 GLM 还是 fallback,便于"看效果"时区分。
- 四策略同预算、同 oracle(真值查表)、同 149,361 提名口径;策略① 随机多 seed;策略④ 用 UCB=mean+λ√var 做主动选择。predictor 复用 models.train_ladder(one-hot 或 ESM,择一,注明)。
