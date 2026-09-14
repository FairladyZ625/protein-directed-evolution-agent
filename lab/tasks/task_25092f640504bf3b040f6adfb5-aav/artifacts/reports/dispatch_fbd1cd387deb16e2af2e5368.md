实现与实验已完成并提交；Harness canonical 留痕因共享 daemon 未运行而阻塞。

- 本地提交：`ccb8b68 feat: add AAV knowledge ablation`
- 已成功 rebase 至最新 `origin/main`（`05d6e4d`）
- 未 push、未开 PR
- 报告与实验工件按纪律保持未提交：
  - [report.md](</Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-knowledge-ablation/lab/reports/knowledge-ablation/report.md>)
  - [metrics.json](</Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-knowledge-ablation/lab/reports/knowledge-ablation/metrics.json>)
  - [events.jsonl](</Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-knowledge-ablation/lab/reports/knowledge-ablation/events.jsonl>)
  - [rejected_candidates.json](</Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-knowledge-ablation/lab/reports/knowledge-ablation/rejected_candidates.json>)
  - [knowledge_ablation.png](</Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-knowledge-ablation/lab/reports/knowledge-ablation/knowledge_ablation.png>)

关键实测结论：

- 知识开/关 strong：162.3 vs 54.0，配对差值 +111/+107/+107。
- `cum_top10_max`：6.5309 vs 6.1862，每个 seed 均 +0.3447。
- 两组达峰率均为 0/3。
- 推荐平均仅重合 56/288，平均 Jaccard 0.1077。
- 知识门禁也排除了每 seed 平均 18 个 strong 候选，最高被拒 fitness 5.5985。
- 图谱已接入 `compose_batch` 的 Critic rationale，且只使用当轮已测数据；它提供可审计理由，但本实验未证明图谱本身改变排序。
- 阴性对照通过：观测 Spearman 0.905917，shuffle-label 0.025364。
- 事件链 252 条，`EventStore.verify()` 通过。
- 真实限制：36/36 个 LLM 轮次超时，结果来自统一确定性回退，不能宣称 LLM 推理增益。

验证：

```text
19 passed in 1.79s
artifact assertions passed; event chain verified
```

未完成的治理门：`fact record`、`task artifact add`、`task progress append` 和 `doc sync --submit` 均返回 `daemon_start_runtime_forbidden`。需要 operator shell 先运行 `ha daemon start --service`，再发布五个工件、记录 Fact 并重试：

```text
ha doc sync --submit --task task_25092f640504bf3b040f6adfb5
```

因此代码和实验交付已完成，但 canonical Fact/receipt 尚未登记。