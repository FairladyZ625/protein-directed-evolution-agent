实现已完成并停在干净的本地提交 `163c7a4`（作者 ZeyuLi）。

- Validation 已真实接入选模：seed 42 选 `alpha=0.01`，更换 validation 为 seed 44 后选 `alpha=10.0`。
- Shuffle-label 阴性对照 Spearman 从 `0.509010` 降至 `-0.038747`。
- 冻结模型后仅执行一次 holdout 评分；Ridge/XGBoost/MLP Spearman 分别为 `0.4904 / 0.4957 / 0.4173`。
- 同预算 Top-24 中，HD=1/2/≥3 的 >WT 命中率为 `25% / 50% / 75%`，单位 assay 正增益为 `0.2385 / 0.5641 / 1.1277`。本设置下多点突变值得投入预算，但结果限于单 seed，且候选池规模不等。
- 定向测试：`10 passed in 1.95s`。

交付物：

- [完整报告](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/lab/reports/pkgB-eval-protocol/report.md)
- [分组数据](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/lab/reports/pkgB-eval-protocol/mutation_order.json)
- [比较图](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/lab/reports/pkgB-eval-protocol/mutation_order.png)
- [分组统计脚本](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-pkgB-eval-protocol/analysis/mutation_order.py)
- [选模实现](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-pkgB-eval-protocol/models/train_ladder.py:177)

已晋升事实 `F-21EC1B3B`、`F-E3A8D1A7`。

生命周期仍为 active：`ha task submit` 被已知的 `rewrite-ci.yml` HTTP 404 门禁阻断，未绕门。另因当前本地开发史与 `origin/main` 无 merge-base，rebase 会重放 56 个非任务提交并立即产生 add/add 冲突，已安全中止，未改写共享历史。下一步需 CEO 处理 CI/分支历史后安排独立 review。