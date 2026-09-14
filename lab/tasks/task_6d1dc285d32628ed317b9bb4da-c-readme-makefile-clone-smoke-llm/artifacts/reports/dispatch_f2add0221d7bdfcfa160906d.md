已收口并本地提交：`b49f1e4 docs: complete delivery smoke and provenance corrections`，已 rebase `origin/main`，未 push/PR。

- v0.4 勘误补充了：历史 v0.4–v0.7 使用 `claude-sonnet-5`、其后网关下架、2026-09-12 后复跑使用 `gpt-5.6-sol`，两者不可直接比较。
- 已更正 v0.4 manifest 与三份 metrics 的实验模型标签；未改 `lab/agents/*.json` 中正确的派工身份标签。
- 交付报告：[report.md](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-pkgC-delivery/lab/reports/pkgC-delivery/report.md)
- 已记录 smoke 事实：`F-2A43B3A3`。
- 验证：`make smoke` → `5 passed in 2.86s`；`git diff --check` 通过。
- 收据同步执行结果：`doc-submit: no_changes`。

风险：历史模型已不可复跑；完整 GB1/AAV 与重型模型路径本轮未运行。