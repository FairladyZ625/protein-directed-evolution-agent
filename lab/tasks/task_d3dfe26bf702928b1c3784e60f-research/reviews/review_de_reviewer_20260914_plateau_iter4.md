# Review review_de_reviewer_20260914_plateau_iter4

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_d3dfe26bf702928b1c3784e60f
- Execution: exe_79ccd5ab2eeb4ab3d06b7992b5
- Verdict: changes_requested
- Commit: null
- Iteration: 4
- Content digest: sha256:2416d2bae878a83d58b14ad2d2e7b1489bd0a5bff67110458d766392838de802
- Submission digest: sha256:86770c0874517b47c79eb54cc368ddbf41ab63b7eb4608467d3a2aefa3b67e13
- Reviewed at: 2026-09-14T11:32:35.498Z
- Consent: pending
- Consent actor: pending
- Consent source: pending

## Reason

打回：最新 artifact 已正确 pin 且修正了 7.53/池边界与 D0Q+S17E 缺测的主要事实，但仍未满足交付契约。① 引用验收未通过：文档明确承认大多数条目只有作者/期刊/年份、无完整标题、DOI 或稳定链接且未逐篇核验；artifact 中仅 2 个可定位 URL/例外条目，不能称‘真实可核引用’，也不能把这些待核文献作为 CEO 排序/提名的可靠支撑。请逐条补齐可定位书目，或从承重论证中删除并明确只作待核背景。② 五要素仍按 7 个‘方法族’合并，而候选清单列出 10 个具体手段、族内又列多个模型/工具；没有对每个具体方法逐一给出原理、代表文献/工具、破隐藏峰机制、笼内可行性/新增工具、answer-agnostic 判定，‘逐族五要素’不能替代 task_plan 的‘每种手段’要求。③ 正文第 142–143 行仍称‘现有所有变体都困在加性表征 + 自然度先验’，与本仓 v0.7 的实测协议冲突：v0.7 明确使用 EpistasisRidgePredictor（one-hot 二阶交互）和 BLOSUM 门禁，且 UCB beta=3 在同池同预算确定性命中 8.4162；应把该句限定为历史纯利用/自然度路线，或删除‘所有变体’，避免把已证伪的总括性机制重新写回正文。修复后重新 sync/submit 并复审。

## Evidence checked

- lab/tasks/task_d3dfe26bf702928b1c3784e60f-research/task_plan.md
- lab/context/development/ai4s-worker-handbook.md
- lab/context/research/AI4S-assignment.md
- lab/context/research/AI4S-domain-research.md
- lab/reports/agentic-v0.2/report.md
- lab/reports/agentic-v0.3/aav/surrogate_scan.json
- lab/tasks/task_d3dfe26bf702928b1c3784e60f-research/artifacts/plateau-breaking-methods.md@03c356d32c5879cc9953242859878545153d8cdee42df661515662479a2b1660
- lab/context/research/v07-multiseed-robustness.md
- lab/context/research/v07-peak-mechanism.md
- PYTHONPATH=. .venv/bin/python load_aav lookup: rows=38265; D0Q+S17E n=0; peak=8.416205130560002; max=9.53645667061
- sha256sum/cmp artifact vs canonical: identical
