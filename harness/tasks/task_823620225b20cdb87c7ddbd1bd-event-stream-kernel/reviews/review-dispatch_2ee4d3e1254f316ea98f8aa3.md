# Review review-dispatch_2ee4d3e1254f316ea98f8aa3

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_823620225b20cdb87c7ddbd1bd
- Execution: exe_94e2b3131039ec7df1cc26cfcf
- Verdict: changes_requested
- Commit: d9a92049f00df67181922e4890649957e5bd6ab2
- Iteration: 1
- Content digest: sha256:77439365ffd3abb4bd1e5aea5b91fc467349478a0f3949198673d417d34f61ff
- Submission digest: sha256:60445f6b847b3973eb077105502031d42f5ae42ff0f63c20e53a6ae7b8a9580f
- Reviewed at: 2026-09-12T13:10:50.356Z
- Consent: pending
- Consent actor: pending
- Consent source: pending

## Reason

打回。iteration 1 修正了 code-doc witness 覆盖面，但冻结提交与回执仍不一致，且截断尾行恢复存在合同级缺陷。提交 pin 为 d9a92049f00df67181922e4890649957e5bd6ab2；该树的 tests/test_events.py 只有 6 tests，不含回执声称的 200 并发 append 回归测试，该测试及 threading.Lock 只存在于后续提交。closeout/Execution 仍称‘跨进程靠文件锁串行化’，而实现没有文件锁，实例级 threading.Lock 也不提供跨实例/跨进程保证。另按 master-plan 的‘容忍截断尾行’要求做故障恢复阳性对照：完整 seq=1 后追加不完整字节 {"seq":2，重启 EventStore 再 append；随后 iter_events/verify 触发 JSONDecodeError，而不是保留完整前缀并形成可验证新链。修复方向：将 submission 冻结到实际欲交付且已测试的 commit；把回执边界改为同一 EventStore 实例内线程安全、跨实例/跨进程不保证；在 append 前检测并截除不完整尾行（或明确拒绝追加并给出恢复动作），补 restart-after-truncated-tail 回归测试，再 amend submission。

## Evidence checked

- read-set: ai4s-worker-handbook.md, task_plan.md, dec_D054AAF358178C453FA1A4CEA8 decision.md, AI4S-master-plan.html §4.1-4.2, AI4S-revision-report.md, AI4S-assignment.md
- frozen commit d9a92049f00df67181922e4890649957e5bd6ab2; code-doc witness covers events/__init__.py, project.py, replay.py, store.py, tests/test_events.py
- git diff d9a9204..HEAD -- events tests/test_events.py shows store.py and tests differ; concurrent regression is absent from frozen tree
- frozen-tree python -m pytest -q tests/test_events.py: 6 passed in 0.07s
- normal/tamper control: 2 events, 64-char head, verify PASS; FWAA→AAAA detected as chain broken at seq=2
- SQLite/replay control: rebuild=2 twice; counts events=2/v_proposals=1; readonly write rejected; round=2+knowledge_agent output only proposal.validated FWAA
- truncated-tail restart control: incomplete final bytes followed by EventStore restart+append causes JSONDecodeError Expecting ',' delimiter
