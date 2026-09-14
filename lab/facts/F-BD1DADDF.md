# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-BD1DADDF

- Statement: Harness 的执行记录(executions/exe_*.md)只从 closeout.md 派生,不从 task artifacts 派生。2026-09-14 实测判据:对 task_ed9e41ef 的同一次 ha task submit --amend 后,字符串「不对本行下选型结论」与「为何此处可下结论」在 artifacts/harder-dataset-survey.md 中分别出现 3 次与 1 次、在 closeout.md 中均为 0 次,故在 exe_499602fd 中均为 0 次;反向对照字符串「一律以 wc -l 为准」在 artifact 中 0 次、closeout 中有、执行中 2 次;两份文档都含的「modes/full_context」与「需核实:本任务未按契约核验」在执行中为 2 次。执行文件 mtime(21:48:54 本地)与其 Submitted 字段(13:48:54Z)同一时刻,证明 amend 确实重写了该文件,排除「amend 未生效」这一解释。后果:凡只修订 artifact 而不同步修订 closeout 的处置,都不会出现在执行回执里,独立评审据执行回执判读时会报「execution 声明与 artifact 不一致」——task_ed9e41ef 的第六轮评审即为该机制的产物。正确做法是每轮处置同时写入 artifact 与 closeout。
- Evidence source: lab/tasks/task_ed9e41ef27c8fb94e8a99062a8-task/{closeout.md,artifacts/harder-dataset-survey.md,executions/exe_499602fd19b231c42c6448dc7e.md}; stat mtime 对照 Submitted 字段
- Observed at: 2026-09-14T13:51:26.126Z
- Confidence: high
- State: standing

