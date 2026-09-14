# Review rev_frontend_timeline_1

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_3b0820bb05c79b2b9fa80d9cdb
- Execution: exe_1e164f4d40ab675d756aa57206
- Verdict: changes_requested
- Commit: e26a1528557b0f32a88d5295b2c8c37db5bd9eb8
- Iteration: 0
- Content digest: sha256:58738653767edf675dcce9904fdf98b1b7d5b227e6cdc4e40f357ce6b2103405
- Submission digest: sha256:d0d89c6c0b645f46884640697c3e9730489d3513dc4e0e852f04117dd09d014e
- Reviewed at: 2026-09-12T13:10:55.693Z
- Consent: pending
- Consent actor: pending
- Consent source: pending

## Reason

功能与主要语义核验通过，但提交未满足强制 handoff 条件，故打回。提交 e26a152 并未 rebase 到最新 origin/main：git merge-base --is-ancestor origin/main e26a152 返回 1，origin/main...e26a152 为 4/1。另有可复现性缺口：provenance 将 scientific_report_v1.0.md 指向 reports/ 下源文件，但该路径不在提交树中；当前 canonical 文件也已与快照不一致。请先 rebase 最新 origin/main，解决 app/timeline.py 与 app/timeline_data.py 的主线重叠，确保 provenance 对提交内容可验证，再重跑定向测试和浏览器切换并 amend 当前 submission。

## Evidence checked

- 提交绑定：ha task show 与 execution 文件确认 exe_1e164f4d40ab675d756aa57206 / e26a1528557b0f32a88d5295b2c8c37db5bd9eb8 / state submitted
- 定向复跑：canonical .venv python -m pytest app/tests/test_timeline.py -q -> 4 passed in 1.67s
- 阳性对照：test_corrupt_stream_rejected 篡改第4条 payload 及追加破损末行，parse_events 均抛 ValueError；测试通过
- 快照核验：provenance 中 20 项快照 SHA-256 全部吻合；v0.1/v0.2/v0.4/v0.5/v0.7 metrics+events、v0.3 scan、baseline 与六篇白皮书和当前声明源逐字节一致
- 数据语义：五组 JSONL 共 179 条通过链校验；测试核对预算、top10 峰值、强变体累积，且确认 v0.5=163、v0.7 llm_used=false、第4批达峰
- UI/截图：人工查看 reports/timeline-showcase/screenshots/v0.7.png，首屏明确标注确定性参考、非 LLM 自主回溯、backtrack=null、8.4162 非全数据集最高分
- 实现检查：v0.3 明确显示无 campaign；四指标、轮次/步回放、原始 JSONL 下载、序列替换、WT 背景实测 epsilon 与缺失值不补零均存在
- 流程硬门：git merge-base --is-ancestor origin/main e26a152 -> exit 1；git rev-list --left-right --count origin/main...e26a152 -> 4 1
- 可复现性：git show e26a152:reports/scientific_report_v1.0.md 报路径不存在；当前 canonical 源与快照非 byte-identical，而 manifest 只记录快照哈希
