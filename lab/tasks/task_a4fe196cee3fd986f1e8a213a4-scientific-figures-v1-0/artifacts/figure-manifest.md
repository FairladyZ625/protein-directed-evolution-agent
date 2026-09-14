# 科学报告图表接口与生图任务边界契约（Figure Manifest）

本契约用于明确**科学报告撰写任务（Text Task）**与**生图独立任务（Figure Task）**之间的边界与协作接口。

## 1. 任务分工边界
- **科学报告撰写任务（Text Task）**：
  - 负责定义各图在正文中的论证逻辑与前后呼应；
  - 编写详尽规范的中文图注（Figure Caption & Sub-captions），严禁图注缺失；
  - 在正文预设标准占位插桩锚点：`<!-- FIGURE_X_START -->` ... `<!-- FIGURE_X_END -->`；
  - 整理图表所依赖的底层度量数据至 `artifacts/figures_data/`。
- **生图独立任务（Figure Task）**：
  - 依据本清单定义的视觉需求与底层数据进行渲染；
  - 统一输出矢量图（`.svg`）或 300 DPI 高清位图（`.png`），归档至 `reports/figures/`；
  - 保持图表字号、调色盘（9-color ramp）与坐标轴线宽在全篇报告中的一致性。

---

## 2. 核心图表装配与需求清单

| 图号 | 文件标识符 | 处理类型 | 数据源与既有资产 | 论证目标（图表证明什么） | 对应章节 |
|---|---|---|---|---|---|
| **图 1** | `fig1_agent_architecture` | **全新概念架构图**（生图任务完成） | `agent/orchestrator.py` / `events/store.py` | 展现受控五角色流水线、大模型仅 2 处受控调用边界、双层生物物理门禁与不可篡改 JSONL 事件流 | 第 4 章 / 第 5 章 |
| **图 2** | `fig2_gb1_convergence` | **既有实测数据图接入**（已有资产） | `workflow-v1.0/gb1/figures/campaign_llm.png` | 展示 GB1 149k 全景观四策略收敛轨迹，证明知识增强 Agent 第 1 轮一击命中 8.762，贪心锁死在 8.045 | 第 6 章 6.1 节 |
| **图 3** | `fig3_epistasis_landscape` | **全新机理示意图**（生图任务完成） | `plateau-breaking-methods.md` §0 | 呈现 AAV 28aa 真实峰（D0Q+S17E+V18A）的正上位性断层，对比加性线性预测面与成对交互势能面 | 第 7 章 7.2 节 |
| **图 4** | `fig4_aav_exploration_tax` | **既有实测数据图接入**（已有资产） | `agentic-v0.4/aav/figures/agentic.png` | 直观展示 AAV 四版演进；定量呈现高置信度下纯贪心直达 8.416 与 LLM Agent 支付“探索税”止步 7.829 的资源博弈 | 第 7 章 7.3 节 |
| **图 5** | `fig5_five_machine_rsi` | **全新系统控制流图**（生图任务完成） | `scientific_report_v0.2.md` §8.3 | 展现面向下一代的内层 DBTL 执行环（执行器、验证器、控制器）与外层元演化环（记忆器、改进器）双循环控制论模型 | 第 8 章 8.3 节 |

---

## 3. 图注规范模版（示例）

```markdown
<!-- FIGURE_1_START -->
![图 1: 面向蛋白质定向进化的受控五角色科学智能体架构与审计流水线](figures/fig1_agent_architecture.png)
*图 1: 面向蛋白质定向进化的受控五角色科学智能体架构与审计流水线。系统由五大核心角色构成：Data Analyst（纯代码统计单点有益谱）、Hypothesis Generator（受控 LLM ①，强制引用规则库）、Mutation Designer（纯代码组合展开）、Fitness Evaluator（预测器梯队）与 Scientific Critic（受控 LLM ② + 物理硬规则）。每一轮次决策与工具调用均通过 SHA-256 签名实时写入 Append-only JSONL 事件流。*
<!-- FIGURE_1_END -->
```
