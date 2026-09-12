已完成并提交本地 commit：

`399f8f257ae8639a2b8978476ffc00d6b5c7dd6a`

交付内容：

- 新增 `tests/test_predictor.py`：5 项测试全绿。
- 接入 T2 三池，使用独立 train/validation/test：5000/2000/2000。
- 新增训练入口：`make train`。
- 新增 `save_predictor()` / `load_predictor()`，并生成三个可跨进程加载的模型工件。
- 生成 [指标表](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-predictor/reports/predictor_metrics.json)及 workflow-v1.1 版本化副本。
- 生成 [预测对比图](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-predictor/harness/reports/workflow-v1.1/gb1/figures/predictor_comparison.png)。
- Ridge alpha 在训练集内部选择，本次选择 `0.01`；未使用测试标签调参。
- 保留 CEO 的标准化对称约束、双档消融和 `alpha_sweep.py`。

实测 test 指标：

| 模型 | Spearman | Pearson | MSE | Top-1% recall | variance_max |
|---|---:|---:|---:|---:|---:|
| Ridge | 0.5119 | 0.4116 | 0.1017 | 0.50 | 0.0176 |
| XGBoost | 0.5034 | 0.6013 | 0.0780 | 0.50 | 0.6461 |
| MLP | 0.4499 | 0.8191 | 0.0410 | 0.65 | 0.5684 |

验证证据：

- `pytest -q tests/test_predictor.py` → `5 passed in 1.60s`
- 三个持久化工件均在独立进程成功加载，且含 5 个 ensemble 成员。
- 已 rebase 至最新 `origin/main` 后复测。
- Fact：`F-3FAE0D4D`
- 未 push、未创建 PR。
- 工作区仅余运行时注入的未跟踪链接 `data/pools/pools`，未纳入提交。