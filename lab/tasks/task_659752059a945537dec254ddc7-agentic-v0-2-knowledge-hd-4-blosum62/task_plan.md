# agentic v0.2:强制 Knowledge 门禁流(HD≤4截断+BLOSUM62硬过滤)治探索惩罚

Task Contract: harness-task v1

## Brief

给自主 agentic agent 的 `test`(花预算)前插一道不可绕过的 Knowledge Gate,拦掉高阶/非保守的死蛋白候选,验证结构化知识能否消除 v0.1 的探索惩罚、让 agent 追平或超过 greedy 的 7.53。

## Goal

在 AAV 池、同预算(288)、同 oracle 下,产出 agentic v0.2 跑分并与 v0.1(cum_top10_max 5.96)、greedy(7.53)对照:验证"test 前的 HD≤4 + 平均 BLOSUM62≥0 硬门(拒收不扣预算、返结构化错误让 agent 重提)"是否把探索从"选中死蛋白"扳回有效区。交付物形态:`lab/reports/agentic-v0.2/aav/` 下的 metrics/events(链校验)/figure + 中期报告 report.md;收件人 CEO 与泽宇;首个使用者是最终报告的"知识增强对 agentic 是否有效"章节。

## Context

v0.1(F-327D08B4/F-3169EBC2)已证:自由 agent 的"探索高不确定性"在蛋白地形上有毒——方差∝突变阶数∝死蛋白,纯 explorer top-288 均 HD 17、0 强命中,故 agent(5.96)输给 greedy(7.53)。knowledge_agent 的 BLOSUM 先验(workflow 线)正是压制此现象、达到 7.53。本任务把该守卫从"软先验"升级为 agent test 前的"硬门"。区分三原语:task=加门禁并跑对比,fact=门禁后指标变动的观察,decision=若门禁改变结论走向则记裁定。

## Required Reading

1. `agent/auto_researcher.py`(权威:agent 与 6 工具,门禁插在 `test` 内)。
2. `lab/reports/agentic-v0.1/report.md` + `aav/postmortem_*.json`(权威:v0.1 失败机制与基线数字)。
3. `evolution/pool_campaign.py` 的 `_blosum_lookup`/knowledge_agent 段(参考:BLOSUM 守卫既有实现)。
4. `knowledge/validators.py`(BLOSUM62 与规则来源)。

## Entry Conditions

auto_researcher.py 的 v0.1 正常(事件链校验通过);AAV one_hot 数据可加载;LLM 池(test-codex-sol 或 pool 端点)可用。任一不满足则停下报告,不伪造跑分。

## Dependencies

上游:v0.1 agent(已合入 master)、knowledge 规则库(T5,BLOSUM62)。无并发改 auto_researcher.py。下游:实验二(ESM 表征)与最终报告的知识增强章节。

## Execution Surface

仓库根(dispatcher 注入 cwd);写范围仅 `agent/auto_researcher.py`(加门禁参数与逻辑)+ 可补 `tests/`(门禁单测)+ 产物落 `lab/reports/agentic-v0.2/`。不改 workflow 线代码、不动 v0.1 产物。

## Constraints

- 保留 v0.1 行为:门禁默认关(`guardrail=False`),v0.2 用 `--guardrail` 显式开;两版都可跑、可对照。
- 公平对照:v0.2 与 v0.1/greedy 同池、同预算、同 oracle、同 seed;差异只在 test 前的门。
- 门禁拒收**不扣预算**、返结构化错误让 agent 重提;不得偷偷替 agent 改选。
- 诚实:若 v0.2 仍输 greedy,如实记录(这也是有价值结论);不调参数凑赢。
- 不做外部/破坏性动作。

## Checkpoint

- 门禁逻辑加好 + 单测绿后先自测一轮(--no-llm 确定性驱动)确认门禁真拦(n_gate_rejected>0)、不扣预算,再跑 LLM 版。
- 跑通后**先报一次**:贴 v0.2 vs v0.1 vs greedy 三方对比 + 门禁拦截率 + 是否突破 7.53,再谈是否进 v0.3。
- 若门禁把可达高值变体也误杀(过严),停下报 CEO 调 max_hd/blosum_min,不擅自反复调参。

## CI/Gate Authority Stop Condition

本任务不改 CI/gate/治理面。定向测试(门禁单测 + 回归)本地绿即可;完成的 CI witness 依仓库现状(见 HARNESS-UX-FEEDBACK.md,witness 机制正由 task_217ab535/Phase 0 修复)。

## Implementation Plan

- `run_autoresearch` 加 `guardrail/max_hd/blosum_min` 参数 + `_gate` helper(HD>max_hd 或 平均 BLOSUM62<blosum_min 则拒)。
- `test` 内:guardrail 开时先过 `_gate`,拒收的不扣预算、emit `agent.tool.knowledge_gate` 事件、返 `gate_rejected` 结构化错误;只测通过的。
- report 加 `guardrail/max_hd/n_gate_rejected` 字段;system prompt 开门禁时告知 agent 门的存在。
- main 加 `--guardrail`,开时产物写 `agentic@v0.2`(results_layout version=v0.2)。
- 加 `tests/` 门禁单测(拒高阶/非保守、不扣预算、放行低阶保守)。
- 跑 v0.2 LLM 版,入 ledger,写 `lab/reports/agentic-v0.2/report.md` 三方对比。
- `ha fact record --task` 记门禁后指标变动结论。

## Deliverable Contract

- `agent/auto_researcher.py`:门禁参数+逻辑(v0.1 默认不变)。
- `tests/` 门禁单测通过。
- `lab/reports/agentic-v0.2/aav/`:agentic.metrics.json + events.jsonl(链校验)+ figure;`lab/reports/agentic-v0.2/report.md`(v0.2 vs v0.1 vs greedy)+ manifest.json。
- ≥1 条 `ha fact record --task task_659752059a945537dec254ddc7`。
- experiment_log 入库一条 v0.2 跑。

## Evidence Protocol

- 门禁生效证据:事件流含 `agent.tool.knowledge_gate`、metrics `n_gate_rejected>0`、且 budget_spent 仍=288(拒收不扣)。
- 对比证据:三方 cum_top10_max/strong 命中表 + 曲线,数据取自各自 metrics.json。
- 事件链 `store.verify()` 通过。
- 单测 clean-env 可复现(定向 test 文件 + 通过数)。

## Verification

- 通过判据:v0.2 metrics 落库、事件链校验通过、门禁单测绿、三方对比表可复现;结论(突破/未突破 7.53)有数据支撑。
- 收尾自检:v0.1 产物未被覆盖(agentic-v0.1/ 原样);v0.2 在 agentic-v0.2/ 独立目录。
- 诚实性:若未突破,report 如实写明并给机制解释,不美化。
