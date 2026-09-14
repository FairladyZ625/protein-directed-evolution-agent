# Review rev_t2c

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_f50ce371b24c0c4396c76f8a4a
- Execution: exe_1705de7cba0eef07a48e2c0248
- Verdict: changes_requested
- Commit: 1563a756374fb6265b32cd9070a9b3a65432ed12
- Iteration: 3
- Content digest: sha256:30552930e318500c92aba7eb67f6a97939a5f0f05b45da84abc3945eef65e335
- Submission digest: sha256:cc087239d3f7416073fba67a51b367d626f77bbd031d9877fdcd1078a31dbcdb
- Reviewed at: 2026-09-14T13:31:24.483Z
- Consent: pending
- Consent actor: pending
- Consent source: pending

## Reason

打回（changes_requested）。本轮冻结提交 exe_1705de7cba0eef07a48e2c0248 的 commit 是 1563a756374fb6265b32cd9070a9b3a65432ed12，但其机器登记 Deliverables 只有 .gitignore、evolution/datasets.py、evolution/pool_campaign.py、reports/experiment_log.jsonl、reports/figures/pool_curve_aav_one_hot.png、reports/pool_events_aav_one_hot.jsonl、reports/pool_metrics_aav_one_hot.json；这些全部越出 task_plan 声明的 data/、evolution/mutations.py、features/ 和本任务 tests 面，且没有登记本任务核心交付。closeout.md 反而把完整交付指向 149f69be904d8f9e37ac93b41960a9813fe231af，和当前 execution commit 不一致，不能以祖先树中碰巧存在的文件替代本 execution 的 delivery proof。冻结 1563 快照的功能本身可运行，但这不消除 delivery cut 错配。修复：重新 amend/resubmit 一个只含 T2 自有路径的交付 cut，并让机器派生 Deliverables 与提交 SHA 同步；保留 ESM 边界的诚实表述。另，真实 ESM-2 650M live-forward 与缓存逐元素一致性本轮仍未验证，现有测试是注入 deterministic backend 的缓存语义测试，应继续标为 residual/unverified。

## Evidence checked

- task_plan.md: Execution Surface 仅允许 data/、evolution/mutations.py、features/、tests/（本任务测试）；Deliverable Contract 要求三池、one-hot/ESM 特征缓存与 149361 口径。
- executions/exe_1705de7cba0eef07a48e2c0248.md: iteration 3、state submitted、commit 1563a756374fb6265b32cd9070a9b3a65432ed12；机器 Deliverables 仅列 7 个路径且与 T2 面不符；closeout.md Summary 指向另一提交 149f69be904d8f9e37ac93b41960a9813fe231af。
- git diff-tree --no-commit-id --name-status -r 1563a756374fb6265b32cd9070a9b3a65432ed12: 7 个修改路径全部为 .gitignore、evolution/datasets.py、evolution/pool_campaign.py、reports/*，T2 允许面匹配为 0。
- git archive 1563a756374fb6265b32cd9070a9b3a65432ed12 加入契约声明的 gitignored 原始 CSV 后，在冻结临时树运行 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider --basetemp <tmp> tests/test_data_pipeline.py，真实输出 6 passed in 0.80s。
- 冻结实现直接复核：landscape 149361 unique、WT fitness [1.0]；pools train/query/holdout = 5000/50000/94361，overlaps [0,0,0]，union 149361，WT in train=True；seed 43 规模不变且 train 成员变化。
- 冻结缓存直接复核：one-hot variants (149361,), embeddings (149361,80), uint8，每行 4 个 active bits；train ESM cache variants (5000,), embeddings (5000,1280), float16 finite；禁用 backend 时 train cache hit 返回 (5000,1280) 且 backend_calls=0，改动首个 variant 的阳性对照触发 LIVE_BACKEND_CALLED。
- tests/test_data_pipeline.py 的 ESM 检查注入 deterministic backend；本轮没有真实 ESM-2 650M live-forward 与缓存逐元素比较证据。
