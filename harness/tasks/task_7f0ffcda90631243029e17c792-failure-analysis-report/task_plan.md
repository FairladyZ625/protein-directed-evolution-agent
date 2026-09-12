# T9 失败案例分析 + PDF 报告 + GitHub 交付（题目三·详细要求）

Task Contract: harness-task v1

## Brief

从 T7 四策略对比里挖失败案例（智力差异化,CEO 亲写）,产出 3–5 页 8 章 PDF 报告 + README（环境/数据来源/命令/主要结果/外部资源声明）+ 公开 GitHub 仓库交付。

## Goal

`reports/`/`report/` 下的 PDF（8 章：背景与问题定义/数据集/适应度预测模型/LLM Agent 设计/知识增强/虚拟进化实验结果/失败案例分析/改进建议与未来拓展）+ 更新的 README + 可公开的 repo。交付给明度数智笔试评审;第一个使用方：面试官。

## Context

- task：收口交付。fact：题目考核重点明列「能分析失败原因,而非只展示成功样例」「讨论 Agent 是否真学到科学家思维还是只调模型」。decision：失败分析由 CEO 亲写（承重智力差异化,不下放）。
- 外部资源（ESM-2/商业 LLM API/数据集/辅助工具）必须在报告注明来源与使用方式。

## Required Reading

1. `harness/context/research/AI4S-assignment.md`（题目三详细要求：报告 8 章目录、代码/README 要求、结果展示清单）— 权威：题面（逐条对齐）。
2. T7 `reports/campaign_metrics.json` 与曲线、T3 指标表 — 权威：实验数据源。
3. `harness/context/architecture/AI4S-master-plan.html`（报告 8 章对位、砍单顺序）— 权威：设计。

## Entry Conditions

- T7 四策略对比产出与 T3 指标表就绪；缺失则报告对应章节停等。

## Dependencies

- 上游：T7（对比数据）+ T3（模型指标）+ 全部前序任务。下游：最终交付。判定满足：PDF 8 章齐、README 可冷启动复现、repo 公开。

## Execution Surface

独立 worktree + 任务分支，base=main。允许写入：`reports/`、`report/`、`README.md`。绝对 cwd 由派工注入。CEO 主笔失败分析章,worker 辅助跑数与排版。

## Constraints

- 失败分析必须基于 T7 真实数据（上位性陷阱/过度自信/激进替换翻车/知识规则错杀等）,不编造成功。
- 报告不吹「学到科学家思维」,用消融数据说话。README「组合完备」措辞改为「149,361/160,000,缺 10,639 为已知局限」。
- 外部资源全声明。破坏性/外部发布动作（推公开 repo）先与 CEO 确认。

## Checkpoint

命中即停：实验数据不足以支撑某章结论、需公开发布 repo（先确认）。计划回报点：8 章草稿齐、README 冷启动验证后。

## CI/Gate Authority Stop Condition

非 CI/gate 任务;涉及 repo 公开为发布动作,归 CEO 裁定。

## Implementation Plan

- 从 T7 产出提取每轮 Top-k、集中位点、四策略对比数字与曲线入报告。
- CEO 亲写失败案例分析章 + 「Agent 是否只是调模型」讨论。
- README：运行环境、数据来源与 SHA、`make` 命令、主要结果、外部资源声明。
- 冷启动验证：无前情 agent 只凭 README 跑通。
- `ha fact record` 晋升「报告 8 章齐 + README 冷启动复现通过」。

## Deliverable Contract

PDF（3–5 页 8 章）+ README + 公开 repo。回报字段：8 章完成状态、README 冷启动复现证据、外部资源声明清单、repo 链接（发布经 CEO 确认后）。

## Evidence Protocol

使用性验收：不带前情的 fresh agent 只凭 README 跑通实验流程。reviewer 拒收：失败分析空泛/无数据、外部资源未声明、README 不可复现。收口记一条 fact（含冷启动证据）。

## Verification

- 停止点 = README 冷启动复现通过 + PDF 8 章齐 + 本地 commit。
- 使用证明：fresh agent 冷启动跑通（使用性验收，可委托）。
- 语义验收由 CEO 亲做（对齐题面 8 章逐条）。
- 至少记录一条 fact。
