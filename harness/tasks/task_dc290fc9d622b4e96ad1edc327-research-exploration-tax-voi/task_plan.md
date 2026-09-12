# Research: 探索税动力学与信息论实验选择形式化

Task Contract: harness-task v1

## Brief
基于信息论与贝叶斯优化理论，对蛋白质工程极小实验预算（$\le 288$）场景下的“探索税（Exploration Tax）”展开严格的数学形式化定义与界分析，构建基于信息价值函数（Value-of-Information, VoI）的自适应采样准则。

## Goal
输出一份形式化理论报告：`artifacts/exploration-tax-formalization.md`，给出探索税的数学定义、极小预算下的渐近后悔界（Regret Bounds）以及兼顾上位方差缩减与均值收割的 VoI-Acquisition 方程。

## Context
实验 v0.4 证明，在高置信度代理模型就绪后，确定性贪心策略因 100% 聚焦于预测高值区而命中全局峰 8.416，而自主 LLM Agent 因固执地进行多样性探索止步于 7.829，支付了探索税。传统多臂老虎机与 GP-UCB 假设实验步数 $T \to \infty$，但在蛋白质湿实验中通常 $T \le 3 \sim 6$，轮次预算极度稀缺。现存理论缺乏对“有限步强先验截断下探索惩罚”的严格建模。

## Required Reading
1. `reports/scientific_report_v1.0.md` 第 7 章
2. 文献 [23] Srinivas et al., 2012 (GP-UCB 理论界); 文献 [27] Harris & Slivkins, PMLR 2026 (LLM 探索还是利用); 文献 [28] Ngo et al., ICLR 2026 (LMABO)

## Entry Conditions
1. AAV 各轮实验数据与探索/利用比率已记录在案；
2. 基础概率论与贝叶斯优化先验模型就绪。

## Dependencies
- 下游接收：AI4S 批次生成算法（`compose_batch` 形式化升维）、理论报告附录。

## Execution Surface
- 工作区：`/Users/lizeyu/Projects/ai4s-directed-evolution-agent`
- 产物写入：`harness/tasks/task_dc290fc9d622b4e96ad1edc327-research-exploration-tax-voi/artifacts/`

## Constraints
1. 必须使用标准测度论、信息论与优化理论符号（互信息 $I(y; f)$、相对熵 $D_{\text{KL}}$、贝叶斯简单后悔 $R_T$）；
2. 避免宽泛的大模型定性分析，聚焦于有限步实验采样的凸优化与后验收敛性。

## Checkpoint
- 形式化推导探索税数学定义式；
- 完成有限视界（Finite-Horizon）后悔界证明；
- 最终文档落盘验收。

## CI/Gate Authority Stop Condition
纯理论学术任务，无需修改 CI 权限。

## Implementation Plan
1. 形式化定义“蛋白质定向进化有限视界简单后悔（Finite-Horizon Simple Regret）”；
2. 严格定义探索税（Exploration Tax）泛函 $\mathcal{T}_{\text{exp}}(\pi, \mathcal{M}, B)$；
3. 证明在单峰高信噪比地貌上纯贪心策略的局部极值击穿概率与探索税的凸性关系；
4. 提出信息论价值加权采集函数（VoI-Acquisition Policy）；
5. 撰写理论报告并落盘。

## Deliverable Contract
- 产物：`harness/tasks/task_dc290fc9d622b4e96ad1edc327-research-exploration-tax-voi/artifacts/exploration-tax-formalization.md`

## Evidence Protocol
产物文件存在，字数不低于 3,500 字，包含定理命题陈述、数学证明、后悔界不等式及收敛性分析。

## Verification
- 检查数学符号严密性与推导逻辑自洽性；
- 确认与本项目的 v0.1~v0.5 实测数据在数值量级上完全吻合。
