# Review review-dispatch_f153d16e967bce8997cc6ff4

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_84fd80d36f4b5a871d7478a8ff
- Execution: exe_788bc1a57666b79ca82fa48e6d
- Verdict: changes_requested
- Commit: 2f769c5f827f25d48d940cc8f9d541cab1c600d8
- Iteration: 1
- Content digest: sha256:3f86d83161d7da87b7dd309975065d3745ffc32ffe8c225eb4c09ec351ab6e87
- Submission digest: sha256:b0de85e593373980db48ce08e950499dfc760b2734460c2a25bcbc8e15222f8d
- Reviewed at: 2026-09-12T13:10:06.691Z
- Consent: pending
- Consent actor: pending
- Consent source: pending

## Reason

打回：提交钉定 commit 2f769c5f 仅含 models/__init__.py 与 models/train_ladder.py，未交付合同要求的 reports/predictor_metrics.json、预测对比图、tests/test_predictor.py，也没有从 T2 三池/one-hot/ESM 接口训练的可执行入口、独立 train/val/test 评测或模型持久化加载接口。合成 ground-truth 显示 Ridge 5 个成员确定性相同，variance_max=3.08e-33；当前环境 XGBoost 亦为 1.97e-31，不能支撑供 T7 UCB 使用的非平凡 ensemble 不确定性。完成声明中的实测 Spearman、HD 分析与下游复用均无法由该冻结提交重现。

## Evidence checked

- execution exe_788bc1a57666b79ca82fa48e6d pins commit 2f769c5f827f25d48d940cc8f9d541cab1c600d8
- git show --stat/git diff: frozen commit adds only models/__init__.py and models/train_ladder.py
- git cat-file/git ls-tree: tests/test_predictor.py and reports/predictor_metrics.json absent; no predictor comparison figure
- git show frozen features/pools.py, one_hot.py, esm2.py versus frozen train_ladder.py: predictor accepts arbitrary X/y and never consumes T2 pool/feature interfaces
- pytest -q tests/test_predictor.py: ERROR file not found; no tests ran
- frozen-source synthetic control: perfect ordering yields Spearman≈1 and Top-k=1; shuffled labels Spearman=-0.2956
- frozen-source 5-seed probe: Ridge variance_max=3.081e-33, XGBoost variance_max=1.972e-31, MLP variance range=0.00149..0.10183
- git grep frozen tree: no trained-model loader/consumer; Makefile points at train_ladder.py but frozen module has no main execution block
