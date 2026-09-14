已完成独立评审，结论：打回（`changes_requested`）。

已登记：[rev_t2c.md](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/lab/tasks/task_f50ce371b24c0c4396c76f8a4a-data-pipeline-features/reviews/rev_t2c.md)，Harness 返回 `accepted_durable`。

证据：

- 冻结快照定向测试：`6 passed`。
- 三池：`5000 / 50000 / 94361`，互斥并集 `149361`，WT 在 train；换 seed 后成员变化。
- one-hot：`(149361, 80)`；train ESM 缓存：`(5000, 1280)`，缓存命中时 backend 调用 `0`。
- 提交 `1563a756…` 的 7 个 Deliverables 全部越出 T2 execution surface，未登记 `data/`、`features/`、`evolution/mutations.py` 或本任务测试。
- `closeout.md` 指向另一提交 `149f69be…`，与本 execution commit 不一致，不能用祖先树中的历史文件替代本次交付证明。
- 真实 ESM-2 650M live-forward 与缓存逐元素一致性仍未验证；当前测试使用注入 backend。

修复方向：重新 amend/resubmit 仅包含 T2 自有路径的 delivery cut，并同步 execution、Deliverables 与 closeout 的提交 SHA；继续明确 ESM 的已验证边界。