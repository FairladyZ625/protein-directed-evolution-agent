# Report v0.5：科学措辞校准、双栏重排与学术架构生图

Task Contract: harness-task v1

## Brief
根据用户批准的 v0.4 审阅意见交付 v0.5 PDF，保留八章主题并用用户给定风格生成两张学术架构图。

## Goal
交付可阅读的 v0.5 PDF、可重建的 HTML/Markdown、图像及数据来源清单，供用户审阅。

## Context
父任务 task_ee0e0b26e540664dac1e6c3f29。v0.4 已完整审阅17页，观察记录在 task_4a9443419cf15f296dc4e3c03a 的 artifacts/v04-review.md。用户授权修订并生成概念图；另授权主分支现状提交，已完成55a0bcf。

## Required Reading
用户当前指令优先；其次 v0.4 PDF及报告；scientific-writing/SKILL.md及其参考规范；v07-multiseed-robustness.md、v07-peak-mechanism.md；final-report-v0.3/evidence/gb1_summary.json及 bibliography-audit.json。旧任务及skill中夸张断言以用户批准审阅意见和原始证据纠正。

## Entry Conditions
上述输入存在，图像生成工具可用，隔离工作树已建立。

## Dependencies
使用既有实验结果，不等待或启动新实验。生成图由本会话亲自检查，报告消费者为用户。

## Execution Surface
仓库隔离 worktree .worktrees/report-v05，分支 codex/report-v05，基于55a0bcf。仅新增reports/final-report-v0.5；登记材料通过ha工具写入当前任务。

## Constraints
保留v0.4。不得伪造缺测值或把确定性重复当独立实验；不得把提案写为已验证功能。概念图用ImageGen，数据图用本地数据代码绘制。不得修改CI或实验代码。

## Checkpoint
图生成后检查标签与箭头；初版PDF后逐页检查；数据和版式通过后交付。无法证实的实现陈述降格为设计边界，不猜测。

## CI/Gate Authority Stop Condition
docs-task无代码CI门。若治理门阻塞，记录真实状态，不绕门、不改CI。

## Implementation Plan
固定输入快照；修订八章文字和引用；生成两张概念图并重绘数据图与缺测图；编译双栏PDF；检查每页、关键数字与引用；提交本地交付物，登记fact与closeout。

## Deliverable Contract
reports/final-report-v0.5/scientific_report_v0.5_two_column.pdf、report.md、同名HTML、figures、evidence、build脚本和修改记录。保存完整生图prompt及工具类型。

## Evidence Protocol
保留输入哈希、统计重算结果、页面边界检查及逐页PNG审阅记录。核对GB1轨迹和产量、AAV确定性独立轨迹数与随机方法统计、AB缺测及差分、30条引用身份。

## Verification
11页左右A4双栏排版以实际验收为准；八章完整；无公式裁切、表格溢出、图中文字不可读；数据与来源相符；新增文件路径完整。纯文档定向验证，不跑全量实验或CI。
