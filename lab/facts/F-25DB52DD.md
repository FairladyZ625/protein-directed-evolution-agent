# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-25DB52DD

- Statement: ha agenda 的在飞线计数只看 task.status,不看 packageDisposition;实测 23 条在飞任务里已有 8 条 packageDisposition=archived 却仍全部显示在在飞线,全仓 77 个任务包中 63 active/14 archived。故「归档」不能让任务离开在飞线,F-1E2E7002 据此作出的「归档 20 个」裁定前提无效。另更正:ha task reopen <id> --reason 存在(Reopen a nonterminal archived or tombstoned Task package),归档可逆;先前判断单向是因只 grep 了 unarchive|restore、漏了 reopen。不带 --json 的 ha task show 只打印三行且不显示 disposition,这是该事实长期不可见的原因。
- Evidence source: ha task show --json; lab/context/development/lifecycle-archive-20260914.md
- Observed at: 2026-09-14T14:48:43.662Z
- Confidence: high
- State: standing

