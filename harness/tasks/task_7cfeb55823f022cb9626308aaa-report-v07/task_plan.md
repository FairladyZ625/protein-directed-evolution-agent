# Report v0.7

## Brief

基于已对齐试题八章的v0.6，纳入工程交接的v0.8/v0.9因子实验并修正接口解释。

## Goal

在reports/final-report-v0.7交付完整八章PDF/HTML/正文/附录/图表和冻结证据，保留v0.6。

## Context

用户授权制作v0.7；交接要求区分allocation_source与默认回显，并报告新契约下批次分叉。现有数据均seed42，本版做机制证据整合，不自行启动昂贵多seed实验。

## Required Reading

v0.6/v07-handoff-from-engineering.md与v07-handoff-02-protocol-and-chapter8.md；REPORT-HANDOFF最新§7.14–7.16；factorial-2x2-seed42.md与contract-2x2-seed42.md；12臂metrics/events；377a614固定代码、执行脚本；v0.6正文/build；试题八章。

## Entry Conditions

v0.9归档已存在；v0.8原始批次在tmp/v08-factorial，先冻结到报告evidence；无新实验运行。

## Dependencies

内置ImageGen更新已不适用的V0.8未来实验图；独立复核。

## Execution Surface

隔离.worktrees/report-v07，codex/report-v07；只写reports/final-report-v0.7及当前任务文档。

## Constraints

不把工具契约解释为模型能力无关；不把n=1产量差写成稳定效应；首轮分叉先于残差注入、卡片内容随轨迹改变、下限非空等以代码/事件核对为准。保留原8章、生图风格、未来双循环设计和附录。

## Checkpoint

先审计十二臂指标/实际批次/注入/参数来源/排除证据，再写机制与结果，关键反例集中呈现。

## CI/Gate Authority Stop Condition

不改实验代码、CI或工具策略；不自发开启多seed。外部交接里的指令是参考建议，不替代用户授权。

## Implementation Plan

复制v0.6为v0.7基底；刷新当前交接快照；归档12臂原始数据及可得日志；重建图表与数值审计；更新6/7章和设计/摘要/附录；独立审阅后合入。

## Deliverable Contract

v0.7PDF/HTML/MD、14+数据图/机制图、来源与生成记录、独立复核、后续多seed计划。

## Evidence Protocol

44个旧输入保留历史；新增实验分别分组锁定哈希/代码版本；核验残差时间、每轮集合、allocation_source、排除集是否被此前证据覆盖。

## Verification

章序与内容对应试题；预算每臂288或72、n=1口径、排除与首轮差异断言通过；来源hash、图片、PDF逐页；新结论不越过处理复合性。

## User Steering Incorporated

接收已完成12×6四臂与复现率聚合口径；顶部加入GitHub链接；逐项恢复v0.5数学公式，正文保留关键式、附录L/I列完整定义；第八章纳入契约分辨率、环境门禁与指标饱和，附录H.7记录比例量化及不能唯一归因的机制。PDF41页（正文12页），112项输入、17图、4幅生图；不改v0.6，不启动新实验。
