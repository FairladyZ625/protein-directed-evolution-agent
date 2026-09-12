结论：v0.5 未追平 v0.4，触发任务的异议型停条件。未依据 oracle 继续调参。

- 正式结果：`cum_top10_max=6.5309`、`cum_top10_mean=6.1922`、strong=163、预算 288/288。
- v0.4 对照：LLM 7.829，deterministic greedy 8.4162。
- C/A 生效：CV Spearman `0.9002–0.9059` 成功透传；0 tool error、0 round error、0 fallback、0 gate reject。
- B 有害：首轮只保留 predicted-mean top-42，挤掉了排名 #45、真值 7.391 的候选；后续纯利用未能追回。
- 阴性对照：shuffle-label held-out Spearman `-0.119960`。
- 定向测试：`14 passed in 2.44s`；事件链校验通过，共 25 条。

产物：

- [v0.5 报告](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-v05/harness/reports/agentic-v0.5/report.md)
- [指标](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-v05/harness/reports/agentic-v0.5/aav/agentic.metrics.json)
- [事件链](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-v05/harness/reports/agentic-v0.5/aav/agentic.events.jsonl)
- [核心实现](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-v05/agent/auto_researcher.py)
- [Surrogate CV 透传](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-v05/models/train_ladder.py)

承重事实：`F-F7BC7554`。本地提交：`ccbfce6c98a8b9f247b37aee456819c8f703878f`，未 push、未开 PR。

Harness closeout 已同步，但 `ha task submit` 被治理层阻塞：默认分支不存在 `rewrite-ci.yml`，GitHub 返回 HTTP 404。另因任务分支与 `origin/main` 无 merge-base，无法安全 rebase。两项均未绕过或修改，execution 仍为 active/pending，需 CEO 修复治理配置后重新提交。