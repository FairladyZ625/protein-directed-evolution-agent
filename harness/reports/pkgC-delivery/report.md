# 包 C 交付面收口报告

日期：2026-09-12

## 结论

README、Makefile 和可提交的 16 变体 smoke fixture 已补齐；`make smoke` 在没有原始 CSV、模型下载、网络或 LLM 凭据时端到端通过（5 passed）。v0.4 实验 provenance 已从错误显示的 `gpt-5.6-sol` 更正为实际解析的 `claude-sonnet-5`，且未修改任何 fitness 或指标数值。

历史 v0.4–v0.7 使用 `claude-sonnet-5`；该模型已在网关下架。2026-09-12 之后的复跑改用 `gpt-5.6-sol`，两者不是同一模型，LLM 侧结果不可直接比较（事实 `F-7702E67B`）。

## 改动清单

### 已更正的实验模型标签

- `harness/reports/agentic-v0.4/manifest.json`：`agent_model`。
- `harness/reports/agentic-v0.4/aav/agentic.metrics.json`：顶层 `agent_model` 与嵌入的模型 provenance。
- `harness/reports/agentic-v0.4/aav/agentic_12rounds.metrics.json`：顶层 `agent_model` 与嵌入的模型 provenance。
- `harness/reports/agentic-v0.4/aav/agentic_16rounds.metrics.json`：顶层 `agent_model` 与嵌入的模型 provenance。
- `harness/reports/agentic-v0.4/report.md`：保留原历史文字、增加模型归属和可比性勘误。

原始 `*.events.jsonl` 为链式历史事件，保留其中当时写入的别名，不重写链式记录。

### 未改的 `gpt-5.6-sol` 派工身份

下列 `harness/agents/*.json` 中的 `model: gpt-5.6-sol` 是编排/派工 agent 身份，不是实验 LLM provenance，故未修改：

- `harness/agents/ai4s-ceo.json`
- `harness/agents/de-agent.json` 与 `harness/agents/de-agent/agent.json`
- `harness/agents/de-ml.json` 与 `harness/agents/de-ml/agent.json`
- `harness/agents/de-reviewer.json` 与 `harness/agents/de-reviewer/agent.json`

## 验证证据

执行命令：`make smoke`

输出：`5 passed`。该命令运行 `python -m pytest tests/test_campaign.py -q`，以提交的 `tests/fixtures/gb1_smoke_landscape.csv`（完整合成 16 变体景观）覆盖四种策略、两轮、知识/无知识分支和确定性复现。

执行 `git diff --check` 无空白错误。README 所链接的 `reports/current-results.md` 已存在；README 不再链接不存在的 PDF 或运行时产物。

## 风险与未验证项

- `claude-sonnet-5` 已下架，历史实验不能以同模型复跑；新旧 LLM 结果只可作为不同模型条件下的独立结果。
- 完整 GB1/AAV 数据与重型模型路径不属于 smoke 的验证范围，本轮未运行。
- 最终 3–5 页 PDF 由独立报告任务生成；README 仅链接当前存在的 Markdown 真源。
