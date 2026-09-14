已完成并停在本地提交 `ed3b4f2212415fb6e2ffe29b3a77019ea4c98713`，未 push/PR。

- [agent/pipeline.py](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-reasoning/agent/pipeline.py)：新增结构化 `CombinationRationale`，记录实测位点增益、组合单点、位点冲突检查、规则 ID 与确定性摘要，并进入事件流。
- [tests/test_agent.py](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-reasoning/tests/test_agent.py)：验证理由非空、统计量可手算、规则引用及事件落盘。
- [展示样例](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-reasoning/lab/reports/workflow-v1.1/agent_combination_rationales.json)：包含一轮三个组合理由。

工具证据：

- 冻结提交树：`21 passed, 1 warning`
- 阳性对照：临时清空摘要后新增测试如期失败，恢复后全绿。
- `origin/main` 仍为 `312ef0b`，提交基于最新主线。
- 作者：`ZeyuLi <zeyuli@users.noreply.github.com>`
- Harness Fact：`F-C355C852`

风险：

- 唯一警告来自 `pydantic_graph` 的 event-loop 弃用提示，不影响测试。
- 未跟踪的 `data/pools/pools` 为既有非任务项，未修改、未提交。

下一步：CEO 可直接 grep 事件中的 `combination_rationale`，并按样例 `measured_rows` 手算 `empirical_position_gains`。