# Directed Evolution Scientific Agent: Report v0.6 交付包指南

本目录包含面向《蛋白质定向进化科学智能体》最终评审的 v0.6 权威报告资产包。

## 1. 资产全景与阅读指引

| 文件 | 性质与用途 | 目标受众 | 核心贡献 |
|:--|:--|:--|:--|
| [report.md](./report.md) | **v0.6 完整权威科学报告** | 评审专家、技术委员会 | 融合题目必备/加分项全覆盖、五角色回环深度机理解构、五大全新基准数据与真实控制组反思。 |
| [discussion_summary_and_epistemology.md](./discussion_summary_and_epistemology.md) | **全景讨论沉淀与认知方法论纪要** | 算法设计者、系统架构师 | 详尽记录人机对话的所有关键洞见：非生物背景大白话精解、知识图谱六问六答、四位点基准合法性、加性与上位性本质、无状态管线局限与 v0.8 反思设计。 |
| [../v0.8-proposal-event-stream-reflexion.md](../v0.8-proposal-event-stream-reflexion.md) | **v0.8 工程架构演进设计案 (RFC)** | 核心研发团队 | 针对“单轮失忆”与“事件流只写不读”痛点，提出跨轮会话延续与残差强制注入的具体改造代码规范。 |
| [../v0.5-to-v0.6-explainer.html](../v0.5-to-v0.6-explainer.html) | **单文件交互式图文看板** | 汇报演示、快速通读 | 纯静态零 CDN 纸质质感 HTML，涵盖机制图谱解构、五大实验数据对比与评审审计对照。 |

## 2. 相对 v0.5 的四大核心演进
1. **五角色闭环机制彻底解构**：针对 v0.5 模糊的“五角色协作”表述，精确展开 `DataAnalyst`、`HypothesisGenerator`、`MutationDesigner`、`FitnessEvaluator`、`ScientificCritic` 各自的代码契约、数据流转与边界。
2. **五大全新实测基准融入**：
   - GB1 稀疏冷启动（96 样本冷启动下 Agent 突破 8.762 全局峰，击败贪心）；
   - AAV 3-seed 多种子鲁棒性验证（强结合变体产量达 288，显著超越单轨迹）；
   - Hard 极端冷启动与 Live LLM 真实负对照（实事求是证明 LLM 并非通用灵丹妙药）；
   - 突变阶数衰减律（HD 1→2→3→4 适应度塌缩分析）；
   - 保守性三难困境（解释为何简单 BLOSUM 保守先验在核心结合口袋会失效）。
3. **生物物理真实性辩护**：明确指出 GB1 四位点（39/40/41/54）是 Wu et al. (2016) 国际公认的基准定义（而非作弊），并配合 AAV 28 位点长窗口证明系统的通用泛化性。
4. **从无状态管线到反射型智能体（v0.8）的演进蓝图**：坦诚披露当前系统“事件流仅作审计日志、未入认知回路”的架构边界，并率先提出 EventStream-as-Memory 的 Reflexion 架构。
