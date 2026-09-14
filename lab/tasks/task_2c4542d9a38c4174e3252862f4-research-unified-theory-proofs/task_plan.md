# Research: RSI-AI4S 统一定理与形式化证明集

Task Contract: harness-task v1

## Brief
统合高阶上位自旋玻璃地貌、有限视界探索税贝尔曼泛函与五机双循环状态转移系统，推导并证明《RSI-AI4S 统一定理与收敛性证明集》。

## Goal
输出一份顶级数学物理理论白皮书：`artifacts/unified-rsi-ai4s-theorems.md`，形式化证明在何种地貌特征与信噪比下，受控自演进双环系统相对经典静态贪心及标准贝叶斯优化具备严格的 Pareto 样本效率占优性。

## Context
本仓前置工作已分别证明了：1. 成对至高阶 Potts 势能地貌在参考态下的代数规范（Paper 1）；2. 探索税在极小预算下的贝尔曼分解与机会成本凸性（Paper 2）；3. 五机状态机马尔可夫决策过程与绝对不变量准则（Paper 3）。当前缺乏将三者结合的统一定理体系。

## Required Reading
1. `reports/theoretical_foundations/01_higher_order_epistasis_theory.md`
2. `reports/theoretical_foundations/02_exploration_tax_and_voi_formalization.md`
3. `reports/theoretical_foundations/03_rsi_cybernetic_ai4s_system_spec.md`

## Entry Conditions
1. 三篇理论基础文档存在且可访问；
2. 独立 worktree `.worktrees/t-unified-theory` 已建立并关联。

## Dependencies
- 下游接收：AI4S 理论白皮书正文、学术论文预印本核心理论章节。

## Execution Surface
- 执行 Worktree: `/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-unified-theory`
- 产物写入：`lab/tasks/task_2c4542d9a38c4174e3252862f4-research-unified-theory-proofs/artifacts/`

## Constraints
1. 恪守测度论、泛函分析与现代控制论严谨符号体系；
2. 所有定理必须包含明确的前提假设（Assumptions）、引理（Lemmas）与完整数学证明（Proofs）；
3. 严格在指定 worktree 内工作，严禁越界修改主分支代码。

## Checkpoint
- 完成统一定理核心命题陈述时；
- 完成贝尔曼收敛性与 Pareto 占优不等式证明时；
- 最终产物落盘验收时。

## CI/Gate Authority Stop Condition
纯数学理论任务，无需修改 CI 权限。

## Implementation Plan
1. 建立包含适应度地貌、有限预算测定与外环代码变异的统一状态空间（Unified State Space）；
2. 提出并证明定理一：表征秩赤字下的渐近停滞定理（Inductive Asphyxiation Theorem）；
3. 提出并证明定理二：信息价值驱动采样的严格非负探索增益定理（VoI Non-Negative Advantage Theorem）；
4. 提出并证明定理三：受控双环 RSI 在有限步下的超线性收敛与 Pareto 占优定理（Controlled Dual-Loop Superlinear Dominance Theorem）；
5. 撰写理论白皮书并落盘。

## Deliverable Contract
- 交付物：`lab/tasks/task_2c4542d9a38c4174e3252862f4-research-unified-theory-proofs/artifacts/unified-rsi-ai4s-theorems.md`

## Evidence Protocol
产物文件存在，包含 3 个核心定理的严密符号化证明，并附带数值边界验证脚本。

## Verification
- 检查公式逻辑链条闭环；
- 运行验证脚本确认定理边界在极端条件下的自洽性。
