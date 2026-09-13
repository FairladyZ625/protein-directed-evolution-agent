# Report v0.6 复现补充

## Brief

报告 v0.6 独立复核后，主线收到 workflow-v1.2 与交接单 §7.14，作为最后的事实补充。

## Goal

在第6.3节增加同条件第二次运行两臂各5查询的观察，避免只读第一轮形成稳定性印象。

## Context

用户要求同步吸收实验线最新证据。已完成主体 task_7e641e8ff76735bb43b0449f53，独立评审 rev_de-reviewer_report-v06_20260913_01 通过。

## Required Reading

reports/final-report-v0.6/report.md 第6.3节；harness/reports/REPORT-HANDOFF.md §7.14；workflow-v1.2/gb1/campaign_llm.metrics.json 与 events.jsonl；前次评审回执。

## Entry Conditions

主体已提交 e007fc1；新复现产物已在主线。

## Dependencies

主体任务已完成；无实验重跑。

## Execution Surface

复用隔离 .worktrees/report-v06 与 codex/report-v06；仅 reports/final-report-v0.6。

## Constraints

只加一段稳定性观察，分别报告两个运行，不取平均，不断言 LLM 普遍好坏；保留原稿与参考。

## Checkpoint

直接核验新指标和事件中的实际提名数，再重建第9页和证据索引。

## CI/Gate Authority Stop Condition

不改 CI 或算法；未提供的新实验数据不填。

## Implementation Plan

冻结三个补充来源；修订一段与来源计数；重建 PDF 并核验第9页；独立定向复核增量；并入主目录。

## Deliverable Contract

更新18页PDF/HTML和源文、证据快照、机器核验记录；保存原讨论纪要。

## Evidence Protocol

从 rounds[].n_nominated 与 nomination 事件核实5/5查询；以 SHA256 固定补充资料。

## Verification

验证44项快照、13图、18页无溢出与原有预算/残差断言；独立评审只看增量。
