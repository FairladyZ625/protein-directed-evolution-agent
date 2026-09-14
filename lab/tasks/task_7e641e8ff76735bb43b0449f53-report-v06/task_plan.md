# report-v06

Task Contract: harness-task v1

## Brief

基于本会话交付的v0.5重写v0.6，补全实际机制和新增实证，恢复以已完成工作与研究发现为主的学术叙事。

## Goal

在reports/final-report-v0.6交付中文报告、PDF、图表与来源清单；先将计划和代码核对结果交用户对齐。V0.8实验结果随后交由v0.7报告整合。

## Context

用户指出v0.5反复使用不能/不足以/没有，冲淡贡献；要求继承v0.5底稿，吸收v0.6讨论纪要与REPORT-HANDOFF，而非在他人v0.6稿上改。用户另授权派人查看Demo、增加有解释价值的图表。

## Required Reading

reports/final-report-v0.5/report.md；reports/final-report-v0.6/discussion_summary_and_epistemology.md与README.md、report.md（参考）；lab/reports/REPORT-HANDOFF.md；reports/v0.8-proposal-event-stream-reflexion.md；agent/pipeline.py、agent/llm.py、evolution/campaign.py、agent/auto_researcher.py；实际workflow-v1.1、analysis-v0.1及alpha扫描产物；scientific-writing规范。当前用户指令优先，参考稿数字按产物核实。

## Entry Conditions

所列资料已存在；本轮以实际文件和代码为准。

## Dependencies

Demo图表子任务task_5455e0628aa237d1553e69befb；其余证据核对由主控亲做。实验 V0.8 由独立实验线开展；用户已于本轮交来第一轮冒烟，本报告纳入 n=1 机制证据，第二轮 2×2 在跑，本轮不启动实验。

## Execution Surface

规划阶段通过ha登记任务；实施阶段独立worktree和codex/report-v06分支。只更新reports/final-report-v0.6，保留收到的原参考稿与讨论纪要，完整保留v0.5。

## Constraints

不把免责声明作为正文主线；先陈述机制、结果和意义，把共同边界集中到方法和讨论。明确GB1 workflow与AAV autoresearcher差异，不照搬全部无状态判断；参考v0.6不作为数值权威。未经用户安排不开展V0.8实验。

## Checkpoint

本轮先完成材料阅读、代码/数据抽查和修改计划对齐；收到Demo清单后主控亲验并决定入选。正式写作时先固定事实矩阵，再编排图文。发现参考稿与代码冲突时列出证据，不凭故事选择。

## CI/Gate Authority Stop Condition

纯报告/只读任务，不修改CI、权限、实验策略或数据；遇阻塞记录并回报。

## Implementation Plan

1.归档参考稿但以v0.5为底稿。2.建立章节-事实-代码-数据图表映射。3.写清五角色输入输出、真实调用范围、提名与Oracle反馈。4.纳入新版四场景、参数扫描、阶数、保守性、知识消融和LLM对照。5.图表随论证增加。6.正文写 V0.8 研究问题、设计与用户新交付的第一轮冒烟，第二轮仍标进行中，另存 v0.7 数据接收接口。7.逐页验收与独立定向复核。

## Deliverable Contract

当前阶段交付可审核的修改计划及核对发现；最终交付reports/final-report-v0.6/report.md、PDF/HTML、图表、证据清单和v0.7数据接收说明。用户为首位审阅者。

## Evidence Protocol

每项关键数字落实际文件/字段；记录独立重复次数、阈值和版本。图表追溯原数据；记至少一个fact。读取代码调用者验证接线，不仅看类与注释。

## Verification

八章主题完整；五角色和跨轮信息传递清晰；真实贡献优先；保留研究者工具分工论述；统计口径匹配来源；V0.8 写设计及已收到的首轮冒烟，禁止填第二轮结果；所有图表可读、来源清楚；PDF逐页检查。
