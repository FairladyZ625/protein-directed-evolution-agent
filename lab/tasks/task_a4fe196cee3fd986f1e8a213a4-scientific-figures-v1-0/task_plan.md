# Task Plan: Scientific Report 核心科学图表与架构图绘制

Task Contract: harness-task v1

## Brief
依据学术报告规范与 Figure Manifest，利用 Matplotlib 脚本与生图 Prompt 渲染学术报告所需的全部 5 张核心图表（含顶刊风格统计图、3D 能量面与系统控制流架构图），统一输出 300 DPI 高清图像。

## Goal
输出学术报告所需的 5 张核心高清图表，归档至 `reports/figures/`，并在主报告及各展示页中完成对齐嵌入：
- 图 1：受控五角色科学智能体架构与双层门禁流水线（`fig1_agent_architecture.png`）；
- 图 2：GB1 全景观四策略闭环对比收敛曲线（`fig2_gb1_convergence.png`，300 DPI 规范重绘）；
- 图 3：AAV 高阶上位效应断层与自旋玻璃能量面三维对比（`fig3_epistasis_landscape.png`）；
- 图 4：AAV 探索税动力学与消融对比图（`fig4_aav_exploration_tax.png`，更新 v0.5/v0.7 数据）；
- 图 5：递归自演进五机双循环与因果事件账本控制流（`fig5_five_machine_rsi.png`）。

## Context
学术主报告已完成 8 章全稿，引用了 30 篇顶刊文献，正文中预留了标准的 Figure 插入插桩。当前需要完成图表视觉工程：部分图表基于真实数据由 Python/Matplotlib 渲染（保证数据精确无误），部分概念架构图由结构化绘图/生图工具生成，统一风格与配色调色盘（9-color ramp）。

## Required Reading
1. `.skills/scientific-writing/references/figure-manifest.md` (图表清单契约与需求定义)
2. `artifacts/figures_data/` (已抽取的图表底层数据 JSON)
3. `reports/scientific_report_v1.0.md` (正文上下文与图注描述)

## Entry Conditions
1. `artifacts/figures_data/` 包含图表底层数据；
2. Python 环境具备 matplotlib, seaborn, PIL, scipy 等依赖。

## Dependencies
- 依赖上游：实验实测数据与报告正文图注规范；
- 下游接收：最终完整版学术报告与前端看板。

## Execution Surface
- 执行目录：`/Users/lizeyu/Projects/ai4s-directed-evolution-agent` (使用独立 worktree `.worktrees/t-scientific-figures`)
- 产物写入：`reports/figures/`

## Constraints
1. 数据图表必须忠实于实测数据，严禁虚构数值；
2. 图表字体与调色盘符合 Nature / Cell 标准（浅色高对比，坐标轴与图例清晰）；
3. 统一输出 PNG (300 DPI) 与 SVG 矢量格式。

## Checkpoint
- 完成全部绘图脚本编写时；
- 完成 5 张图表生成与高清度审查时；
- 图表嵌入报告并完成正文视觉核验时。

## CI/Gate Authority Stop Condition
图表绘制任务，不涉及系统代码或 CI 规则修改。

## Implementation Plan
1. 在专用 worktree 中建立绘图脚本目录 `scripts/figures/`；
2. 编写 `plot_fig1_architecture.py`：绘制五角色受控流与门禁；
3. 编写 `plot_fig2_gb1_convergence.py`：基于 GB1 实测指标绘制四策略收敛曲线；
4. 编写 `plot_fig3_epistasis_landscape.py`：绘制加性预测平面 vs 成对 Potts 势能曲面三维图，高亮 D0Q+S17E+V18A 真实峰的上位断层；
5. 编写 `plot_fig4_exploration_tax.py`：绘制各代际探索税对比与 v0.7 回溯达峰曲线；
6. 编写 `plot_fig5_cybernetic_loop.py`：绘制内环三机 + 外环二机的控制论架构；
7. 运行脚本渲染全量图表，保存至 `reports/figures/` 并同步至报告包。

## Deliverable Contract
- 绘图脚本：`scripts/figures/` 目录下的可复现源码
- 图像资产：`reports/figures/fig1` 至 `fig5`（PNG/SVG）
- 校验报告：`lab/tasks/task_a4fe196cee3fd986f1e8a213a4-scientific-figures-v1-0/artifacts/figure-generation-summary.md`

## Evidence Protocol
提供生成的图表文件列表、分辨率与尺寸信息，以及脚本运行成功的日志。

## Verification
- 确认全部 5 张图表均存在于 `reports/figures/`；
- 分辨率不低于 300 DPI 或矢量 SVG；
- 正文中 5 处图片链接均能正常加载渲染。
