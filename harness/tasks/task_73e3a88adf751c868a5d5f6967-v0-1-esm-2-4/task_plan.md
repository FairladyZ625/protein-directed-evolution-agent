# 保守位点分析(ESM-2 逐位置熵作保守性代理)

产物版本:`harness/reports/analysis-v0.1/`。与突变阶数分析同属分析线首版,各写自己的文件。

## Brief

笔试题加分项第四条是「引入蛋白质结构信息**或**保守位点分析」。本仓两样都没做:全仓
`conserv` 的命中全是 BLOSUM 保守性**替换规则**(`R-BLOSUM-CONSERVATIVE`)——那是氨基酸替换
的保守性,不是**序列位置**的保守性;无 PDB / 结构 / ddG。

## Goal

补齐保守位点分析这一条,并回答一个真问题:**保守位点上的突变是否真的更有害?**
首要产出不是一张保守性图,而是「保守性先验会不会拒绝真峰」的定量答案(见 Constraints)。

## Context

**范围已由 CEO 裁定,不要扩。** 走保守位点,不碰结构。理由:结构路线要 PDB + FoldX/Rosetta
ddG,新增工具链成本高,而 AAV 可变区多为柔性环、结构杠杆本就弱、AlphaFold 置信度低。
保守位点可以便宜且诚实地做——仓内已有 ESM-2 650M(`features/esm2.py`),用它的**逐位置氨基酸
分布熵**当保守性代理,不需要 MSA、不需要新工具。

已确立的承重事实:AAV 真峰是**反自然**的——ESM zero-shot 给它的 z 分为负,片段排 #3743、
全长 #4782。真峰三个位点是 AAV 28aa 序列的第 0、17、18 位(D0Q / S17E / V18A)。

## Required Reading

- `features/esm2.py`(ESM 后端与 npz 缓存机制,**只读复用,不要改**)
- `harness/context/research/plateau-breaking-methods.md` 族 1(为什么 zero-shot 对本题是反指标)

## Entry Conditions

worktree `.worktrees/t-conservation` 已建好,`.venv`、`data/aav/full_data.csv`、
`features/cache` 已符号链接。基线 `origin/main`。

## Dependencies

无阻塞依赖。与 `task_2c7cd062c0ed0006932cee1c88`(突变阶数)同写 `analysis-v0.1/`,
但各写自己的文件。

## Execution Surface

**只动**:`features/conservation.py`、`tests/test_conservation.py`、
`harness/reports/analysis-v0.1/{gb1,aav}/conservation.*` 与其 figures、
`harness/reports/analysis-v0.1/conservation-report.md`。

**不要动**:`features/esm2.py`、`evolution/`、`agent/`、`models/`、`knowledge/`、`events/`、
`app/`,以及另一个 worker 的 `analysis/mutation_order.py` 与 `report.md`。

## Constraints

**这条最重要,违反即整轮作废。** ESM-2 的熵是**自然度先验**的一种。本项目已实测确立:
任何用自然度/PLM 先验去筛候选、缩候选集或挑训练集的流程,**都会把反自然的真峰重新藏起来**,
在本题里是违规的。

所以:**保守性只能作为「分析与解释」的维度,绝不能进入采集或筛选路径。**
- 报告里要显式写出这条边界。
- 并给出证据:把真峰三个位点在保守性排序里的**位次**报出来。如果真峰位点落在高保守区,
  那正是「保守性先验会拒绝真峰」的直接证据。**这个负结果比一张漂亮的保守性图有价值得多。**
- 不接受把保守性接进 `evolution/` 任何采集路径的改动。

## Checkpoint

ESM 后端跑不起来(缓存缺失、显存不足等)→ **按 blocker 回报并停手**,不要用随机数或
近似值顶替熵值交差。发现 plan 判断有误同样回报。

## CI/Gate Authority Stop Condition

停止点 = `pytest tests/test_conservation.py` 绿 + commit。**不 push、不发 PR、不打 tag。**
不要跑全量测试矩阵(同机多 worker)。

## Implementation Plan

1. `features/conservation.py`:用 ESM-2 取逐位置 token 概率分布,算每位置 Shannon 熵
   (低熵 = 高保守)。GB1(56 残基全长,四个可变位点 V39/D40/G41/V54)与 AAV(28aa 可变段)
   各一份。缓存沿用 `features/esm2.py` 既有 npz 机制,**别另造一套**。
2. 保守性排序:每个位置给熵值与保守性名次。
3. **与实测效应对照**:每位置「实测有益突变比例 / 最大 fitness 增益」对保守性名次作图,
   并报 Spearman 相关。
4. **真峰位点定位**:真峰三个位点的保守性位次单独报出(见 Constraints)。

## Deliverable Contract

- `features/conservation.py` —— 可执行入口。
- `harness/reports/analysis-v0.1/{gb1,aav}/conservation.json`(全精度)。
- `harness/reports/analysis-v0.1/{gb1,aav}/figures/conservation.png`。
- `harness/reports/analysis-v0.1/conservation-report.md` —— 方法、结果、**边界声明**。
- `tests/test_conservation.py`。

## Evidence Protocol

- **阳性对照必做**:人工均匀分布(熵应达最大)与 one-hot 分布(熵应为 0),断言熵计算正确。
- ESM 后端缺失时必须明确报错,**不许静默降级**;为此补一条断言。
- 每个数字标明实测还是模型产出。

## Verification

- `pytest tests/test_conservation.py` 在冻结提交树上全绿,阳性对照真的能红。
- CEO 会自己核真峰三个位点的位次,以及那条边界声明在不在报告里。
- CEO 会 grep 确认保守性没有出现在 `evolution/` 的采集路径上。
