# v0.6 附录与插画修订

## Brief

按用户反馈重排v0.6，补充资料入附录，修复首页留白，沿用v0.5生成图风格。

## Goal

交付正文聚焦、附录自足、首页紧凑且三张机制图使用内置生图工具的v0.6修订PDF。

## Context

用户明确喜欢原Image插画风格，要求新版继续使用，并适配当前机制口径；附带两张截图为视觉反馈，不是额外指令。

## Required Reading

reports/final-report-v0.6/report.md、README.md、build/、evidence/sources.json；v0.5/figures/fig1_workflow.png、fig5_proposal.png；imagegen/PDF技能。

## Entry Conditions

已交付v0.6正文和证据完整；本轮不变更实验结果。

## Dependencies

生图工具输出需检查图中文字与箭头；无实验依赖。

## Execution Surface

隔离.worktrees/report-v06-polish，分支codex/report-v06-polish；仅reports/final-report-v0.6。

## Constraints

数值图保留数据绘制；三张机制图真实生图，保留提示词与来源；不声称工具未暴露的具体模型版本；所有移出的材料写入附录而非丢弃。

## Checkpoint

先生成三张插画，同时重组正文与附录，再嵌入并逐页检验。

## CI/Gate Authority Stop Condition

不修改实验代码、CI或权限；生图失败如实记录，不以SVG冒充。

## Implementation Plan

冻结本轮前稿；重组正文/附录；生成五角色、跨轮反馈、残差设计图；首页加入总览图并压紧标题；修订动态页数验证；独立审阅视觉/论断一致性后合入。

## Deliverable Contract

v0.6 PDF/HTML/Markdown、三张生图、提示词清单、附录证据索引和更新验证。

## Evidence Protocol

44项既有快照不改；数值图源不改；机制图逐标签和箭头对照附录接线说明。

## Verification

全部附加材料可在附录阅读；首页无大块空白；生图无文字/逻辑错误；PDF图片加载/溢出检查与逐页目视；独立复核。
