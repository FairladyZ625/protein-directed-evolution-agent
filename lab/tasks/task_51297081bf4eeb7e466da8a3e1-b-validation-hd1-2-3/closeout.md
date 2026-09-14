## Summary

在本地提交 `163c7a42a72f5d2d28f12dadf262922de3096c29` 完成两项交付：保留 GB1 外层 5,000/50,000/94,361 池口径，在 5,000 条历史池内建立 4,000 train + 1,000 validation，并让 Ridge alpha 只由 validation Spearman 选择；新增 query-test 上 HD=1/HD=2/HD>=3 各 24 次 assay 的模型直推受控比较。私有报告及完整提名清单已登记在 `lab/reports/pkgB-eval-protocol/`。

## Verification

- `.venv/bin/pytest -q -s tests/test_data_pipeline.py tests/test_eval_protocol.py tests/test_mutation_order.py`：`10 passed in 1.95s`。
- validation 行为证据：seed 42 选择 alpha=0.01（Spearman 0.509010），换 seed 44 选择 alpha=10.0（0.507889）。shuffle-label 阴性对照为 -0.038747。
- 冻结的一次 2,000 行 holdout 评分：Ridge/XGBoost/MLP Spearman 为 0.490405/0.495707/0.417261；对应 Top-1% 命中率为 0.40/0.60/0.65。
- 同预算 HD 实测：>WT 命中率 25%/50%/75%，单位 assay 正增益 0.2385/0.5641/1.1277。
- 晋升事实：`F-21EC1B3B`（validation 实际影响选参及 shuffle 阴性对照）、`F-E3A8D1A7`（HD 同预算结果与适用边界）。
- 独立 review 尚未执行，需由非本执行 actor 完成。

## Residual Risk

- HD=1 候选池仅 24 条而被穷举，HD=2/HD>=3 是从更大候选池模型筛出的 Top-24；实验预算相等，搜索机会数不等。
- 结果是单 seed、one-hot Ridge、模型直推的描述性比较，没有置信区间，不代表 AAV 或 Agent 策略的普遍收益。
- 历史 AAV metrics 只保留聚合值和 Top-10，无法恢复全部提名的 HD；后续轨迹应持久化全量候选级审计字段。
- `origin/main` 与当前本地开发史无 merge-base；直接 rebase 会重放 56 个非本任务提交并在首个骨架提交产生 add/add 冲突，已安全 abort。未改写共享历史，因而“rebase 到最新 origin/main”未完成。

## Same Mechanism Elsewhere

机制句：当选模 API 只接收训练集与最终评估集时，validation 容易被静默折叠进最终评估。使用 `rg -n "train_test_split|RidgeCV|GridSearchCV|X_train.*X_test|x_train.*x_test|validation" models analysis evolution --glob '*.py'` 搜索。结果只发现本次修复后的显式四角色路径，以及 `EpistasisRidgePredictor._select_alpha` 在训练数据内部做 80/20 选参且不接收最终评估标签；未发现第二处同机制的 final-test 泄漏。
