# Review de-reviewer-20260912-pkgb

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_51297081bf4eeb7e466da8a3e1
- Execution: exe_4303b9cb9f113ef61674d86417
- Verdict: changes_requested
- Commit: 163c7a42a72f5d2d28f12dadf262922de3096c29
- Iteration: 0
- Content digest: sha256:5e2abf55bf7a29f581d621e566a6b092f9c47e6c0ef22cc1b2bcb1092d2ce090
- Submission digest: sha256:7adc78fec7ded17d2c99973c54c3aea6b514a888e63a207caf5fa377b97228fa
- Reviewed at: 2026-09-12T13:10:53.984Z
- Consent: pending
- Consent actor: pending
- Consent source: pending

## Reason

核心语义在提交 163c7a42 上可复现：点名测试 10 passed，validation seed 42/44 分别选择 alpha 0.01/10.0，shuffle-label Spearman=-0.038747，HD 三组结果与登记产物逐字节一致。但提交未满足任务合同的 handoff 前 rebase 要求：其父提交为 cee742a，而当前 origin/main 为 05d6e4d；git merge-tree 显示 models/evaluate_all.py 与 models/train_ladder.py 均 changed in both 且含冲突标记，故当前提交不可直接作为已复核的最新主线交付。请在最新 origin/main 上解决两处冲突，保留现有 standardize 修复与 validation 四角色语义，重新生成/核对产物并复跑同一组点名测试后 amend submission。

## Evidence checked

- git show 163c7a42 与 git diff 163c7a42^..163c7a42：7 个 deliverable 路径，diff --check 无报错
- 隔离 worktree 运行 .venv/bin/pytest -q -s tests/test_data_pipeline.py tests/test_eval_protocol.py tests/test_mutation_order.py：10 passed in 2.07s
- 隔离 worktree 运行 python -m analysis.mutation_order：alpha=0.01，shuffle=-0.038747，HD hit_rate=0.25/0.50/0.75，gain_per_assay=0.2385/0.5641/1.1277
- sha256sum：重跑 mutation_order.json/png 与登记产物哈希分别完全一致
- git merge-base 与 git merge-tree：共同祖先 cee742a；models/evaluate_all.py、models/train_ladder.py 对 origin/main 存在真实内容冲突
- 报告已披露 HD 候选池 24/668/49308、单 seed 与模型直推边界；未将描述性结果外推为跨策略因果结论
