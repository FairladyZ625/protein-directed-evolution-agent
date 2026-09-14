# Review review-dispatch_beedc95d75d75f5c6a765058

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_84fd80d36f4b5a871d7478a8ff
- Execution: exe_e8ba945b11b9574e429f32a7b6
- Verdict: changes_requested
- Commit: 4f456890ca43dfe007e4b17c63c06c3fa26f147f
- Iteration: 0
- Content digest: sha256:9655bfeb40dbd97b6b7d78b5c84c943516e0bf782ca6740494e3b78c2b71cfea
- Submission digest: sha256:5e59b9bb3da275eda2b0f45dd304755f1726ca058e7b0e9e75485f1b290d27a4
- Reviewed at: 2026-09-12T11:53:27.470Z
- Consent: pending
- Consent actor: pending
- Consent source: pending

## Reason

冻结 cut 虽有三级 fit/predict(mean,var) 实现和四组指标，但缺 task contract 硬性要求的 tests/test_predictor.py、预测对比图及声明路径的指标表；无模型持久化/加载接口，T7 实际重训 Ridge 而非加载 ESM+XGBoost；HD Spearman 低于 checkpoint 后无对齐诊断，且 JSON 的 Ridge 零方差与冻结源码默认 5-seed bootstrap 的独立复现不一致、缺 provenance。

## Evidence checked

- ha task show：task in_review；execution exe_e8ba945b11b9574e429f32a7b6；commit 4f456890ca43dfe007e4b17c63c06c3fa26f147f
- git show 冻结 models/train_ladder.py、models/evaluate_all.py、lab/reports/workflow-v1.0/gb1/predictor_ladder.json
- 冻结源码合成对照：阳性 Spearman=0.996832，shuffle=0.032842，5-seed variance_max=0.001866，同 seed 精确一致
- 冻结 JSON：四 feature/split 组合指标齐全；HD 最佳 esm2/mlp Spearman=0.492912；四组 Ridge variance_max 为 0 或浮点舍入量级
- git cat-file：冻结 cut 缺 reports/predictor_metrics.json 和 tests/test_predictor.py；未找到 predictor 对比图
- git grep：下游重新构造 RidgePredictor，无已训练模型 loader，也未消费 ESM+XGBoost 主力
- python -m pytest -q tests/test_data_pipeline.py：6 passed in 0.89s；任务指定 predictor 测试不存在
