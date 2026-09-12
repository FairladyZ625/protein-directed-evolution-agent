# Task Plan: Research 全版本时间线交互看板 (Timeline Showcase)

Task Contract: harness-task v1

## Brief
开发一套高美观度、全版本沉浸式交互的前端展示看板，顶部以清晰时间线导航（v0.1 至 v0.7），逐版本解构研究叙事、核心指标卡、真实事件流回放与变体检视器。

## Goal
输出一套现代化可交互的前端看板系统（集成至 `app/` 或单文件富交互 Web 应用），实现全版本时间线切换。每个版本展示固定的四大组件：
1. 版本背景与演进叙事（当时发生了什么、为什么迭代、破局假说）；
2. 核心指标卡片（最高适应度、强变体数、探索税代价、相较基准的增益）；
3. 真实事件流回放器（解析真实的 JSONL 事件流日志，支持轮次与决策步回放）；
4. 变体序列结构与能量检视器（展示关键突变、打分与成对上位互作）。

## Context
项目经历了从 v0.1 自由探索掉入死蛋白陷阱、v0.2 物理门禁、v0.3 代理扫描、v0.4 上位感知突破 7.53、v0.5 批次退火、到 v0.7 停滞回溯精准命中全局真峰 8.4162 的全历程。所有历史运行数据均在 `harness/reports/` 下有完备的 JSONL 事件流与 metrics。需要将这一波澜壮阔的科研攻坚历程以直观、高颜值的交互形式呈现。

## Required Reading
1. `reports/scientific_report_v1.0.md` (完整 8 章学术报告与 6 代演进数据)
2. `harness/reports/agentic-v0.4/aav/agentic.events.jsonl` (v0.4 事件流样例)
3. `harness/reports/agentic-v0.2/aav/agentic.events.jsonl` (v0.2 事件流样例)
4. `app/demo.py` (现有 Streamlit 骨架代码)

## Entry Conditions
1. 全版本实验事件流文件均存在且格式合法；
2. Python 环境已安装 Streamlit / Altair / Plotly 等可视化组件。

## Dependencies
- 依赖上游：各代际实测数据与事件流日志；
- 下游交付：项目 Demo 展示、答辩与评审验收。

## Execution Surface
- 执行目录：`/Users/lizeyu/Projects/ai4s-directed-evolution-agent` (使用独立 worktree `.worktrees/t-frontend-showcase`)
- 产物写入：`app/` 与 `reports/`

## Constraints
1. 界面必须美观现代，具备专业科研产品质感（浅色适读、信息层次分明）；
2. 严禁虚构伪造事件数据，所有回放必须绑定真实的 `agentic.events.jsonl`；
3. 不影响主分支核心算法代码。

## Checkpoint
- 完成时间线导航与组件架构设计时；
- 完成事件流解析与各版本数据绑定时；
- 跑通完整前端并在浏览器验证各版本切换无错时。

## CI/Gate Authority Stop Condition
前端展示开发任务，不触碰 CI/Gate 核心规则。

## Implementation Plan
1. 在专用 worktree 中检出代码，设计时间线多版本数据适配层 `app/timeline_data.py`；
2. 构建通用固定组件：
   - 顶部时间线胶囊导航栏（v0.1, v0.2, v0.3, v0.4, v0.5, v0.7, 理论白皮书）；
   - 叙事卡（背景、为什么迭代、实测发现）；
   - 指标看板（累积最高分、达峰轮次、探索税、优良变体率）；
   - 事件流序列步步回放（带 JSON 格式化与重要决策高亮）；
   - 变体对比试玩器；
3. 在 `app/demo.py` 或独立的现代化 Web 前端中实现完整交互；
4. 运行端到端测试，验证所有版本切换无报错。

## Deliverable Contract
- 前端源码：`app/` 目录下的时间线看板源码与静态资源
- 演示文档：`harness/tasks/task_3b0820bb05c79b2b9fa80d9cdb-research-timeline-frontend-showcase/artifacts/frontend-showcase-summary.md`

## Evidence Protocol
提供各版本交互界面截图或可直接运行的 `streamlit run app/demo.py` 验证指令。

## Verification
- 启动服务验证页面正常加载；
- 点击切换每个版本，确认对应数据、叙事与事件流准确呈现；
- 至少记录一条关于组件解耦的 Fact。
