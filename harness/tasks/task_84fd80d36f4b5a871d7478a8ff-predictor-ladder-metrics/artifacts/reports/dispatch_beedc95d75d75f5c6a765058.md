# Independent execution review

## Verdict

**changes_requested（打回）**。

冻结提交 `4f456890ca43dfe007e4b17c63c06c3fa26f147f` 中存在三级预测器接口和四组指标 JSON，但没有满足 task contract 的完整交付与证据协议。当前缺口会阻止对指标可复现性、Top-k 语义和下游模型加载能力的独立验收。

## Ground-truth evidence

- `ha task show task_84fd80d36f4b5a871d7478a8ff` 与 execution 文档均显示状态 `in_review`、execution `exe_e8ba945b11b9574e429f32a7b6`、commit `4f456890...`；本轮按派工给定 digest `sha256:5e59...27a4` 的冻结 cut 评审，未改换提交。
- `git show 4f456890...:models/train_ladder.py`：存在 `RidgePredictor`、`XGBoostPredictor`、`MLPPredictor`，共同支持 `fit` 与 `predict -> (mean, var)`；`metrics` 包含 Spearman、Pearson、MSE、Top-k recall。
- 对冻结源码执行合成阳性/阴性对照：接口输出 shape `(60,) / (60,)`，5-seed variance max `0.001866`，重复训练逐元素一致；阳性 Spearman `0.996832`，shuffle 后降至 `0.032842`。检测器本身可出声。
- `git show 4f456890...:harness/reports/workflow-v1.0/gb1/predictor_ladder.json`：四种 feature/split 组合均含三模型的 Spearman/Pearson/MSE/Top-k/variance；最佳 HD 外推是 `esm2/mlp` Spearman `0.492912`，低于任务锚点 `0.55–0.75`。
- `git cat-file -e` 对冻结 cut 的 `reports/predictor_metrics.json` 与 `tests/test_predictor.py` 均返回 exit `128`；快照中也未找到 predictor 对比图。
- `git grep` 冻结 cut：下游 `agent/auto_researcher.py`、`evolution/campaign.py`、`evolution/pool_campaign.py` 都直接重新构造并训练 `RidgePredictor`；没有已训练模型的保存/加载接口，且没有使用任务指定的 L2 主力 `ESM + XGBoost`。
- `python -m pytest -q tests/test_data_pipeline.py` 实跑为 `6 passed in 0.89s`，仅证明上游数据接口正常；任务点名的 `tests/test_predictor.py` 不存在，故其定向门未执行、不可视为通过。

## Defects

1. **硬性交付缺失**：任务要求 `reports/predictor_metrics.json`、对比图和 `tests/test_predictor.py`；冻结 cut 只有迁移后的 `harness/reports/workflow-v1.0/gb1/predictor_ladder.json`，没有图和预测器定向测试。closeout 也未声明这项偏离或替代关系。
2. **证据协议未满足**：要求的接口契约、指标正确性、shuffle 阴性对照、同 seed 复现性没有提交测试。评审虽然独立证明冻结源码在合成样本上可通过这些性质，但不能替代交付内的回归测试。
3. **指标 provenance/方差不一致**：冻结源码默认 5-seed bootstrap；独立运行冻结源码的 Ridge 会产生非零方差，但提交 JSON 的四组 Ridge `variance_max` 均为 `0`（或浮点舍入量级），且没有运行清单、版本/seed/cache digest 解释该结果。因而“5-seed 方差非平凡供 UCB”的宽泛 verification 不能证明各模型结果由该冻结实现生成。
4. **下游加载契约未交付**：task goal 明确要求 T7 能加载模型 predict，回报模型加载接口签名。当前只提供类和评估 JSON，不保存模型，也无 loader；实际下游重新训练 Ridge，未加载 L2 `ESM + XGBoost` 主力。
5. **异常指标排查与高-fitness 分析不足**：HD 外推 Spearman `0.278–0.493` 命中 checkpoint 的“显著低于 0.55–0.75”，但 closeout 只称“真实困难”，没有标签/特征对齐核验或与 two_vs_rest 口径差异的诊断。JSON 仅贴数字，也没有契约要求的“能否识别高 fitness 变体”分析；Top-k 只有比例且未明确 `k=1%`/样本数 20 的语义。

## Actionable repair

1. 补齐 `tests/test_predictor.py`，覆盖三模型统一接口、Top-k 手算样例、同 seed 精确复现、shuffle Spearman 塌陷，并运行该文件给出真实输出。
2. 由冻结代码重新生成指标，记录 commit、Python/依赖版本、seed、split 行数与 ESM cache digest；逐模型校验 5-seed 方差，解释或修复 Ridge 方差为零的不一致。
3. 按 task contract 输出/明确迁移映射后的机器可读指标表与对比图，并增加高 fitness 识别分析（明确 top 1%、命中数/分母、随机基准和失败案例）。
4. 实现并测试模型持久化/加载接口，证明 T7 可加载 `ESM + XGBoost` 的 `(mean, var)` 预测；若架构已改为下游在线重训 Ridge，应先正式修订任务合同/decision，而不是在 closeout 中隐式替代。
5. 对低于锚点的 HD 结果执行特征—标签行对齐检查，并明确当前 `HD<=2 / HD>=3` 与文献 FLIP `two_vs_rest` 是否严格等价；保留诚实低分，但提交排查证据。

## Unverified

- 未重跑完整 ESM-2 650M 四组合评估；该操作昂贵，且提交缺少 task 定向测试与 provenance，现有硬缺口已足以判定打回。
- 未核验派工摘要 digest 的 daemon 内部计算方式；execution 的 commit、completion claim、deliverables 和当前状态与派工冻结内容一致。
