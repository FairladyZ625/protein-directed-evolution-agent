已完成 T3 预测模型阶梯实现并提交本地 commit。

变更：

- [models/train_ladder.py](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t2-data-model/models/train_ladder.py)
  - 统一 `fit(X, y)` / `predict(X) -> (mean, var)` 接口
  - Ridge L1
  - XGBoost L2，未安装 XGBoost 时回退到 GradientBoosting
  - 5-seed MLP ensemble
  - Spearman、Pearson、MSE、Top-k recall 指标
  - 指标 JSON 导出函数
- [models/__init__.py](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t2-data-model/models/__init__.py)

验证证据：

- 三种模型均成功完成 `fit` 与 `predict`
- `predict` 返回 mean/variance 两个向量
- 指标函数输出四项指标
- 已记录 Harness fact：`F-5182F98C`
- 本地提交：`2f769c5 feat: add fitness predictor ladder and metrics`

尚未完成：

- 任务要求的完整 `reports/predictor_metrics.json` 与对比图尚未生成
- `tests/test_predictor.py` 当前仓库不存在，未能运行该定向测试
- 需要后续接入实际 T2 数据后执行完整 train/report 流程及 shuffle-label 阴性对照