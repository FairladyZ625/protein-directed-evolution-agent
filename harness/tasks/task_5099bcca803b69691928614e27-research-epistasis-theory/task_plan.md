# Research: 高阶上位相互作用与自旋玻璃地貌理论深化

Task Contract: harness-task v1

## Brief
系统性研究蛋白质序列-适应度景观中的高阶上位相互作用（Higher-Order Epistasis）与自旋玻璃（Spin-Glass）能量地貌理论，针对 AAV VR-IV 高变区，提出从二阶 Potts 势能向稀疏高阶特征扩展的理论方案与数学表达。

## Goal
输出一份前沿理论研究报告：`artifacts/higher-order-epistasis-theory.md`，形式化推导成对残基交互至 $K$ 阶张量投影的低秩稀疏化解法，解决 AAV $20^{28}$ 空间下的特征组合爆炸问题。

## Context
在 v0.4 实验中，成对 Potts 模型（EpistasisRidgePredictor）成功将 AAV 全局真峰（8.416，三突变 `D0Q+S17E+V18A`）从排名 #2776 提升至 #429，突破了加性天花板。然而，真峰本身由三位点协同产生（$1+1+1 \gg 3$），涉及三阶相互作用；若盲目将多项式扩展至 3 阶，特征维度将从数千膨胀至上千万。需从统计物理学与自旋玻璃自洽场理论寻找稀疏化与正则化解析解。

## Required Reading
1. `reports/scientific_report_v1.0.md` 第 3 章、第 7 章
2. `harness/context/research/plateau-breaking-methods.md`
3. 文献 [1] Wu et al., 2016 (*eLife*); 文献 [11] Hopf et al., 2017 (*Nat Biotech*); 文献 [12] Poelwijk et al., 2019 (*Nat Commun*); 文献 [13] Tran et al., 2026 (*Science*)

## Entry Conditions
1. 仓库既有特征代码（`features/one_hot.py`、`models/train_ladder.py`）可读；
2. 实验数据（AAV 冷启动池与实测池）结构清晰。

## Dependencies
- 下游接收：AI4S 模型梯队升级（L5 高阶上位模型）、学术报告附录。

## Execution Surface
- 工作区：`/Users/lizeyu/Projects/ai4s-directed-evolution-agent`
- 产物写入：`harness/tasks/task_5099bcca803b69691928614e27-research-epistasis-theory/artifacts/`

## Constraints
1. 严禁使用纯概念玄学，必须给出明确的数学公式（Hamiltonian 展开、稀疏惩罚、核方法或张量分解）；
2. 算法必须具备计算可行性，时间复杂度严格控制在 $O(N \cdot L^2)$ 或低秩截断内。

## Checkpoint
- 推导 Potts 模型向 3-way/4-way 扩展的低秩张量分解方程时；
- 形成针对 AAV 28aa 的工程特征选择策略时；
- 最终文档落盘验收时。

## CI/Gate Authority Stop Condition
纯学术研究任务，无需修改 CI 权限。

## Implementation Plan
1. 梳理统计物理自旋玻璃模型（Ising/Potts Hamiltonian）在蛋白质序列共变异分析中的数学表达；
2. 分析三阶及更高阶上位效应的稀疏性假设（Sparse Epistasis Hypothesis）；
3. 提出基于残基物理接触图先验（Contact Map Prior）与低秩张量 Tucker 分解的高阶交互降维方案；
4. 撰写《蛋白质适应度景观高阶上位相互作用理论与低秩稀疏化解法》；
5. 提交并落盘产物。

## Deliverable Contract
- 产物：`harness/tasks/task_5099bcca803b69691928614e27-research-epistasis-theory/artifacts/higher-order-epistasis-theory.md`

## Evidence Protocol
产物文件存在，字数不低于 3,500 字，包含完备的数学推导、特征维度量化表与伪代码。

## Verification
- 检查公式形式化完整性；
- 验证 AAV 28aa 空间在所提算法下的参数量估算合理性。
