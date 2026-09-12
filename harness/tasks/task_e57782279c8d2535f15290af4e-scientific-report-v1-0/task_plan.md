# Milestone: Final Scientific Report 高严谨中文学术报告与引证体系

Task Contract: harness-task v1

## Brief
编制并交付高学术严谨度的《面向蛋白质定向进化的受控自演进科学智能体研究报告（v1.0）》，实现去 AI 味、100% 真实文献引证（30 篇 GB/T 7714）、图文契约与独立生图解耦。

## Goal
输出符合国际计算生物学/AI4S 会议与期刊规范的正式中文学术报告。交付物为 `artifacts/scientific_report_v1.0.md` 并双向镜像至主仓 `reports/scientific_report_v1.0.md` 与用户 IDE 工作区 `protein-directed-evolution-agent/reports/scientific_report_v1.0.md`，作为最终答辩与评测交付物。

## Context
本项目的实验闭环与理论突破已完备（GB1 策略④首轮达 8.762；AAV v0.4 突破至 8.416 与 7.829，归因出死蛋白陷阱、上位盲区与探索税；第 8 章构建了五机双循环 RSI 架构）。现有报告草案 v0.2（344 行）存在口语化应试口吻、部分引证不够规范及图注未解耦的问题，需要重塑为高水准学术报告。

## Required Reading
1. `artifacts/input-draft-v0.2.md`: 现有 8 章报告底本（P0 事实基准）；
2. `.skills/scientific-writing/references/gbt-7714-2015-rules.md`: 30 篇真实可核验文献表（P0 引证标准）；
3. `.skills/scientific-writing/references/de-ai-chinese-rubric.md`: 中文学术去 AI 味替换清单（P0 表达标准）；
4. `.skills/scientific-writing/references/figure-manifest.md`: 图表接口与图注契约（P0 接口标准）；
5. `artifacts/frontier-synthesis.md` & `domain-research.md`: 前沿学术背景输入。

## Entry Conditions
1. 30 篇核心参考文献经核验全要素真实，无虚构作者或套用 DOI；
2. 既有 9 幅实验数据曲线与指标文件已就绪；
3. 本地 `.skills/scientific-writing/` 部署并与工作区同步。

## Dependencies
- 输入依赖：v0.1~v0.4 实验度量数据与 Chapter 8 RSI 理论架构；
- 下游接收：外部答辩评委会、生图独立任务（Figure Task）。

## Execution Surface
- 主执行工作区：`/Users/lizeyu/Projects/ai4s-directed-evolution-agent`
- 同步工作区：`/Users/lizeyu/Projects/protein-directed-evolution-agent`
- 写入范围：`harness/tasks/task_e57782279c8d2535f15290af4e-scientific-report-v1-0/artifacts/`, `reports/`, `.skills/`

## Constraints
1. 严禁编造文献元数据（作者、DOI、卷期）；
2. 严禁在报告中使用夸张、轻佻、网文化或第一人称抒情表达；
3. 严禁泄露内部专有 CLI 脚本命令，保持学术规范叙事；
4. 图表渲染交由独立任务，本任务仅负责精准图注与插桩锚点。

## Checkpoint
1. 完成学术去 AI 味与 8 章节重构初稿时检查；
2. 运行 `verify_citations.py` 实现 1:1 双向映射后检查；
3. 双仓交付文件一致性校验时检查。

## CI/Gate Authority Stop Condition
非 CI 权限改动，纯文档与规范交付。无需修改 CI 权威面。

## Implementation Plan
1. 【工件装配】：将 v0.2 底本、文献库、De-AI 清单与指标归档至 `artifacts/`；
2. 【学术重构】：依据 8 章架构与五步法摘要，进行全篇中文学术严肃化改写；
3. 【去 AI 味清洗】：逐段比对 De-AI 清单，消除口号式断言与情绪化修辞；
4. 【精准引证】：在正文关键论断处严格标注 `[1]`~`[30]`，并附录文末国标参考文献表；
5. 【图表契约】：预设 5 处图表锚点，补充完备的学术中文图注；
6. 【自检校验】：运行 `scripts/verify_citations.py` 自动化确保引用 100% 闭环；
7. 【双仓同步】：同步产物至两个项目的 `reports/` 目录。

## Deliverable Contract
- 交付物：`harness/tasks/task_e57782279c8d2535f15290af4e-scientific-report-v1-0/artifacts/scientific_report_v1.0.md`
- 双仓同步镜像：
  - `/Users/lizeyu/Projects/ai4s-directed-evolution-agent/reports/scientific_report_v1.0.md`
  - `/Users/lizeyu/Projects/protein-directed-evolution-agent/reports/scientific_report_v1.0.md`
- 引用校验输出：0 缺失、0 悬挂。

## Evidence Protocol
运行 `python .skills/scientific-writing/scripts/verify_citations.py <report_path>`，提供退出码 0 与对齐清单作为交付证据。

## Verification
- 运行 `python .skills/scientific-writing/scripts/verify_citations.py` 输出通过；
- 检查文件字数与 8 章节完整性；
- 确认图注包含所有 5 幅核心图表的科学论证定义。
