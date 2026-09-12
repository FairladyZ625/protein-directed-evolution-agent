# Research: 知识库因果反事实归因状态机与影子沙箱自演进蓝图

Task Contract: harness-task v1

## Brief
深度挖掘 ZeYu-AI-Brain 知识库中的《Memory 编译器与本能假说》、《RSIBench-Data》及 Harness ADR 规范，为计算生物学自演进智能体设计“因果反事实归因状态机与影子沙箱代码自演进”的落地工程蓝图。

## Goal
输出一份系统工程蓝图与架构设计规范：`artifacts/causal-attribution-engine-blueprint.md`，给出无需人类干预的平台期自动检测、上位赤字反事实归因算法，以及在影子沙箱中自动生成并回归测试模型代码补丁的完备状态机设计。

## Context
当前定向进化 Agent 在 v0.1~v0.4 的跃迁依赖人类在场进行离线诊断并手写成对 Potts 模型。如何消除这一人机断层，使系统在内环停滞时能够基于不可篡改的 Fact 账本自动判断瓶颈因果、并在隔离沙箱中自主合成代码 Patch，是实现真正自主演进的核心缺失环节。

## Required Reading
1. `/Users/lizeyu/Documents/ZeYu-AI-Brain/03-KNOWLEDGE/01-READING/01-DOMAINS/Agent-RSI/2026-08-31-memory-compiler-instinct-thesis.md`
2. `/Users/lizeyu/Documents/ZeYu-AI-Brain/03-KNOWLEDGE/01-READING/01-DOMAINS/Agent-RSI/2026-08-04-rsibench-data-centric-research-benchmark.md`
3. `reports/theoretical_foundations/03_rsi_cybernetic_ai4s_system_spec.md`
4. `harness/context/research/plateau-breaking-methods.md`

## Entry Conditions
1. ZeYu-AI-Brain 相关知识库笔记存在且可读；
2. 独立 Worktree `.worktrees/t-causal-attribution` 已挂载。

## Dependencies
- 下游接收：AI4S 自动化科研引擎开发、架构演进路线图实施。

## Execution Surface
- 执行 Worktree: `/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-causal-attribution`
- 产物写入：`harness/tasks/task_ad43836db4be99ab3e3b1cebd5-research-causal-attribution-engine/artifacts/`

## Constraints
1. 方案必须具备明确的数据结构与接口签名（Pydantic Schema / JSON-Schema）；
2. 状态机迁移逻辑必须涵盖异常回滚机制（Rollback Transaction）；
3. 影子沙箱变异严格受物理不变量（Verifier）只读拦截约束。

## Checkpoint
- 完成反事实归因 DAG 数据模型定义时；
- 绘制完备的状态转移图与沙箱隔离协议时；
- 最终工程蓝图落盘验收时。

## CI/Gate Authority Stop Condition
纯系统架构与工程设计任务，无需修改 CI 权限。

## Implementation Plan
1. 深入研读 Brain 中关于 Memory 编译器、经验本能固化与反事实分析的核心文献；
2. 抽象出蛋白质地貌停滞的三大核心归因特征量：残差自相关度、变体汉明距离分布与方差信噪比；
3. 设计反事实因果归因状态机（Causal Attribution State Machine）；
4. 定义外环在影子沙箱中检索特征库、生成模型代码补丁并执行自动化测试套件的流水线规范；
5. 撰写工程蓝图并落盘。

## Deliverable Contract
- 交付物：`harness/tasks/task_ad43836db4be99ab3e3b1cebd5-research-causal-attribution-engine/artifacts/causal-attribution-engine-blueprint.md`

## Evidence Protocol
产物文件存在，包含 Mermaid 状态机流程图、Schema 定义及伪代码协议。

## Verification
- 检查状态转移完备性，验证无死锁状态与孤立节点；
- 确认沙箱安全协议完全符合防自毁（Goodhart-proof）约束。
