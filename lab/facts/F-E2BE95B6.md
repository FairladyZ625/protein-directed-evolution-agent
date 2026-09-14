# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-E2BE95B6

- Statement: ha agenda 的在飞线过滤条件:不按 packageDisposition 过滤(23 条里 8 条 archived 仍在列),但也不是简单的 status=active——全仓 11 条 active 里只有 3 条进在飞线。差出的 8 条执行状态全是 changes_requested,且在 agenda 四个分组(在飞线3/待裁2/球在别人手里2/可派队列21,共28条)里一条都不出现。即评审已打回、正等使用者修的任务恰好是议程完全看不见的那批。F-25DB52DD 中「只看 task.status」这半句为过度断言,「不看 packageDisposition」那半句成立。查这类任务须用 ha task list --status active 再逐条读 executions 最新一份的 State。
- Evidence source: ha agenda 与 ha task list --status active 交叉比对(2026-09-14 收口后)
- Observed at: 2026-09-14T14:59:32.121Z
- Confidence: high
- State: standing

