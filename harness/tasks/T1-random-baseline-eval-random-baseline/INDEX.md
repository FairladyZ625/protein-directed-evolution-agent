---
schema: task-package/v2
task_id: T1-random-baseline
title: "随机策略基线：三轮虚拟进化 eval + 指标表（random baseline）"
parent: M1-baseline-eval
lifecycle:
  engine: kernel/task-lifecycle/v1
  status: in_review
packageDisposition: archived
workKind: feat
riskTier: low
urgency: high
vertical: software/coding
preset: standard-task
profile: baseline
packagePath: tasks/T1-random-baseline-eval-random-baseline
owner: machine
---
# 随机策略基线：三轮虚拟进化 eval + 指标表（random baseline）

Preset: standard-task/baseline

## Documents

- `INDEX.md` — machine
- `task-contract.json` — machine
- `task_plan.md` — doc-sync
- `closeout.md` — doc-sync
- `artifacts/.gitkeep` — doc-sync

## Next

Run `ha task complete T1-random-baseline`.

## Gate Checks

- ci: blocked
- code-doc-reconciliation: blocked
