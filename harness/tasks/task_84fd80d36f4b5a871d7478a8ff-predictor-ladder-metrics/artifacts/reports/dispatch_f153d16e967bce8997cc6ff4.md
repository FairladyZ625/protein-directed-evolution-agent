Verdict：打回（`changes_requested`）。

已通过 Harness 记录独立评审：`review-dispatch_f153d16e967bce8997cc6ff4`，对应冻结提交 `2f769c5f827f25d48d940cc8f9d541cab1c600d8`。

主要缺陷：

- 提交仅包含 `models/__init__.py`、`models/train_ladder.py`。
- 缺少 `reports/predictor_metrics.json`、对比图和 `tests/test_predictor.py`。
- 未实际接入 T2 的三池、one-hot、ESM-2 接口。
- 没有独立 train/val/test 评估，也没有模型持久化/加载接口。
- `train_ladder.py` 无可执行入口，Makefile 调用不能生成声明产物。
- 5-seed 合成验证中，Ridge `variance_max=3.081e-33`、XGBoost `1.972e-31`，无法提供 T7 UCB 所需的非平凡不确定性。
- 完成声明中的 Spearman、HD 外推分析和下游复用无法从冻结提交复现。
- 指定测试实跑结果：`tests/test_predictor.py` 不存在，`no tests ran`。

修复方向：补齐冻结提交中的指标 JSON、图和定向测试；直接消费 T2 三池及两类特征；实现真实可复现的 train/val/test 流程、shuffle 对照、seed 复现测试和模型保存/加载；确保主力 L2 的 ensemble 方差非退化，并用实际下游加载测试证明 T7 可消费。