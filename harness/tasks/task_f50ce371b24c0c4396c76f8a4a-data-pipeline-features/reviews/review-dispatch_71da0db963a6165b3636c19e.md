# Review review-dispatch_71da0db963a6165b3636c19e

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_f50ce371b24c0c4396c76f8a4a
- Execution: exe_4dd139967a33e33d760b091cdc
- Verdict: changes_requested
- Commit: 91d9a17154617c0b068a44bcb99f1e44c1ee7fd1
- Iteration: 2
- Content digest: sha256:86141938456e5eea8fa29a1c9b2b4e05f86be72fe3223fb7f3bc4e5c6bf18d57
- Submission digest: sha256:ca6ca0150320117a719d5f24fca23f941f6e70602ea52fcec304be1a51d0e868
- Reviewed at: 2026-09-12T12:09:01.632Z
- Consent: pending
- Consent actor: pending
- Consent source: pending

## Reason

冻结提交快照中的 T2 实现可运行：定向测试 6/6 通过，三池、149361x80 one-hot 和有序 5000x1280 train ESM 缓存均经冻结树复核成立。但本 execution 的 content-pinned Deliverables 只有无关的 HARNESS-UX-FEEDBACK.md，且冻结 commit 自身也只修改该文件；没有任何契约要求的 data/、evolution/mutations.py、features/ 或本任务测试路径。树中历史文件的存在不能替代本 execution 的任务交付，因此 completion claim 与机器冻结 delivery 不一致，必须打回并以任务自有交付面重新 amend/resubmit。

## Evidence checked

- Frozen submission digest sha256:ca6ca0150320117a719d5f24fca23f941f6e70602ea52fcec304be1a51d0e868 and delivery commit 91d9a17154617c0b068a44bcb99f1e44c1ee7fd1
- execution projection: iteration 2, state submitted, commit 91d9a17154617c0b068a44bcb99f1e44c1ee7fd1; ha task show reports in_review
- git show --stat/--name-status 91d9a...: only HARNESS-UX-FEEDBACK.md modified; frozen Deliverables likewise list only HARNESS-UX-FEEDBACK.md
- git-archive frozen snapshot plus contract-declared gitignored raw CSV; .venv/bin/pytest -q tests/test_data_pipeline.py: 6 passed in 0.95s
- frozen pools: 5000/50000/94361, zero pairwise overlap, union 149361, WT VDGV in train
- frozen gb1-all-one-hot.npz: variants (149361,), embeddings (149361,80), uint8
- frozen keyed train ESM cache dbfd1ecc45bd4b72148d: variants (5000,), embeddings (5000,1280), float16, ordered against train pool, finite and non-constant
- cache mismatch positive control: intact repeat kept backend calls at 1; swapped cached variant order caused calls to increase 1 -> 2
- real ESM-2 650M live-forward equality was not independently verified; directed test uses an injected deterministic backend
