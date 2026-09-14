已完成并提交第一次 checkpoint，按任务契约暂停，未继续铺开不可比矩阵。

- v0.4 deterministic 锚点：严格 `48×6=288`，`cum_top10_max=8.4162`，strong=151，事件链通过。
- v0.1 seed 42：严格 `48×6=288`，`cum_top10_max=7.5301`，strong=57。
- 相对原始 v0.1：峰值 `+1.5691`，strong `+42`。
- 但仅前两轮为 live LLM（96 条）；第 3–6 轮 `claude-sonnet-5` 连续返回 404 `model_not_found`，其余 192 条由预注册的 predicted-mean 补批完成。因此不能把结果解释为六轮全 live LLM，也不能继续生成 v0.2/v0.4 可比点。
- 阴性对照：正常标签 held-out Spearman `0.908743`；shuffle-label `0.054191`，按预注册阈值塌缩。
- 独立审计确认 288 条提名唯一，全部属于 HD>2 oracle 池，HD/fitness 逐条匹配，预测有限，指标可重算，两条事件链均有效。

产物见 [report.md](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-version-matrix/lab/reports/version-matrix/report.md) 和 [checkpoint-audit.json](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-version-matrix/lab/reports/version-matrix/checkpoint-audit.json)。

本地提交：`c86fc6dd5fd6209b2a7b32b44282dc2a8cb24e29`。

剩余阻塞：

- Harness daemon socket 不存在，无法写 canonical fact/progress；CLI 返回 `daemon_start_runtime_forbidden`。
- 当前分支与最新 `origin/main=be62937a…` 无共同 merge-base，无法安全 rebase。
- 需先恢复 `claude-sonnet-5` 稳定路由，再继续三 seed、v0.2/v0.4、产物汇总和最终排序。