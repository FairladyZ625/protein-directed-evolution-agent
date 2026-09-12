# Review review-dispatch_02950692f432dbe6cae9d16b

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_823620225b20cdb87c7ddbd1bd
- Execution: exe_c78866ca6efd21e75b4976d3dd
- Verdict: changes_requested
- Commit: 4f456890ca43dfe007e4b17c63c06c3fa26f147f
- Iteration: 0
- Content digest: sha256:15c4da9a7a44091c20266d6f1c46038dab6b61974ec1c447493e0a9428e48ad2
- Submission digest: sha256:5585a7d97c6d1eccca1198bd0641c7bbbcb426222eeb9798f863e7eaa244f2a6
- Reviewed at: 2026-09-12T12:28:51.966Z
- Consent: pending
- Consent actor: pending
- Consent source: pending

## Reason

核心事件流功能满足合同且定向测试通过，但 submitted closeout 的并发边界陈述与冻结实现不一致：文档称“跨进程靠文件锁串行化”，events/store.py 实际仅使用每个 EventStore 实例独立的 threading.Lock。双实例竞争阳性对照产生 seq=[1,1]，verify() 报 chain broken at seq=1。任务允许 campaign 单写者，因此无需扩展为跨进程安全；但必须把回执改为真实边界（同一实例内线程安全，跨实例/跨进程不保证），再 amend submission。另应让交付/代码文档见证覆盖合同要求的 events/project.py 与 tests/test_events.py，当前见证仅列 store.py、replay.py。

## Evidence checked

- 冻结 commit 4f456890ca43dfe007e4b17c63c06c3fa26f147f；当前 events/store.py、events/project.py、events/replay.py、tests/test_events.py 与冻结树 git diff 为零
- python -m pytest -q tests/test_events.py：7 passed in 0.10s
- 手工正常链：2 events，64 位 head hash，verify PASS；单字符 FWAA→AAAA 后 DETECTED chain broken at seq=2
- SQLite rebuild 两次均返回 2；events=2、v_proposals=1；只读连接写入报 attempt to write a readonly database
- replay --round 2 --strategy knowledge_agent 仅输出 seq=2 proposal.validated FWAA
- 并发阴性边界阳性对照：两个 EventStore 实例同时 append 得 seq=[1,1]，verify FAILED chain broken at seq=1；grep 仅见 threading.Lock，无 flock/fcntl
- execution/code-doc witness paths 仅 events/store.py、events/replay.py，未覆盖 events/project.py、tests/test_events.py
