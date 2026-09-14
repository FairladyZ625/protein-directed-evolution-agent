# 对齐试题章节与未来架构

## Brief

对齐试题八章并恢复v0.5未来架构。

## Goal

章名和顺序逐项匹配AI4S-assignment；未来双循环架构在第八章有完整图文。

## Context

用户认可现有内容，仅要求章节匹配和找回未来架构；新实验由后续v0.7整合。

## Required Reading

lab/context/research/AI4S-assignment.md；reports/final-report-v0.5/report.md第2、8章和fig5_proposal.png；v0.6/report.md与build脚本。

## Entry Conditions

v0.6已有完整已审证据、附录及3张生图；v0.5未来架构图可直接复用。

## Dependencies

无新实验依赖。

## Execution Surface

隔离.worktrees/report-v06-sections，分支codex/report-v06-sections；仅reports/final-report-v0.6。

## Constraints

不更改44项冻结测量证据；不把未来方案写成已实现；保留附录和首页排版；不修改试题文件。

## Checkpoint

先章节映射，再移动正文并补独立数据集章和未来架构章，最后渲染检查。

## CI/Gate Authority Stop Condition

不改CI或实验逻辑；无新实验结果纳入。

## Implementation Plan

正文按原八章重组；恢复双循环图及内外环职责、停止、多目标与设备接口；更新交叉引用/文档计数/图像校验；独立定向复核后合入。

## Deliverable Contract

更新v0.6 PDF/HTML/Markdown和章节映射、未来图与来源记录；原附录保留。

## Evidence Protocol

复用已审数据；未来图按v0.5原图字节复制，保留其生图提示词出处；章节对照写入verification。

## Verification

八个准确章名依次出现；3/6/7跨页时不重复编号；未来架构完整且标提案；动态页数/图像哈希/44项来源及逐页目视通过。
