# report-v06-demo-figures

Task Contract: harness-task v1

## Brief

亲自查看已运行的Streamlit Demo，选出适合v0.6学术报告的图表与机制展示。

## Goal

交付图表清单、截图、数据路径与建议图注；供主控亲验后选择正文/附录内容。

## Context

用户说Demo里有很多好图，包括alpha相关，授权派人去看并把有价值的图纳入报告。Demo目前在本机8501监听。主控同时在核对报告材料，不会编辑Demo。

## Required Reading

先读/Users/lizeyu/.claude/skills/fable-gpt-worker-orchestration/references/codex-worker-handbook.md；lab/context/development/ai4s-worker-handbook.md；本task_plan；app/demo.py（重点render_alpha_sweep_panel及五个tab）；lab/reports/REPORT-HANDOFF.md按图表需要路由；用户要求本轮只读，优先于身份旧实现指令。

## Entry Conditions

所列资料已存在；本轮以实际文件和代码为准。

## Dependencies

本机http://localhost:8501已运行；五个tab为四策略、Agent回放、试玩、位点与组合理由、阶数/保守性/alpha。无需任何新实验。

## Execution Surface

只读仓库和已运行Demo；允许在.harness/report-v06-demo-scratch中保存截图、检查脚本和报告，再经ha task artifact add登记到本任务artifacts。你不是代码库唯一执行者，禁止改业务/报告/他人文件，不建实现worktree、不提交代码。

## Constraints

必须真实打开浏览器查看并操作tab，不能只读源码声称看过。可点纯读取图表筛选，不运行新campaign、不触发昂贵推荐、不更改现有浏览器tab或重启服务。截图只是取证，正式图建议从原数据重绘。工具不可用需明确标未视觉验证。禁止外部发送、push、PR及子代理。

## Checkpoint

时间预算5分钟，先完成alpha和四策略，再覆盖余下tabs；任何UI阻塞不修业务代码，记录后继续其他可读面。目标或数据口径有误时带证据challenge。

## CI/Gate Authority Stop Condition

纯报告/只读任务，不修改CI、权限、实验策略或数据；遇阻塞记录并回报。

## Implementation Plan

打开localhost:8501；逐tab查看与截图，特别是alpha扫描、固定alpha标准化反转、阶数外推/覆盖、保守位点、候选构成/角色回放。查app/demo.py确定各图来源。形成8至12项以内候选清单，排正文/附录优先级，记录重复图与新信息。

## Deliverable Contract

artifacts/demo-figure-inventory.md及截图；每项含UI位置、截图、源JSON/字段、图讲什么、建议对应章节、沿用/重绘/附录建议、数值或交互异常。汇报主控，不自行改报告。

## Evidence Protocol

报告结论只基于真实截图与读到的数据；图表缺失如实记录；至少一个fact带当前task，不能把计划当证据。资料按块落盘。

## Verification

确认截图文件存在且可读；来源文件路径真实；清单包含alpha；分清亲眼看到和源码推断。最终只返回摘要与工件路径，不跑全量测试。
