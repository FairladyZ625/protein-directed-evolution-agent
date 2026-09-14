# 突变阶数效果比较(单点 / 双点 / 多点)

产物版本:`lab/reports/analysis-v0.1/`。分析线首版——**只读分析**,不跑新的虚拟进化实验,
只在已测数据上做分析。加数据集或加分析维度时 bump。

## Brief

笔试题加分项第三条明写「比较单点突变、双点突变和多点突变的优化效果」,本仓至今没做
(全仓 grep 无任何按突变数分组的指标或分析,只有 v0.4 报告散文里提过一句 doubles)。
本任务在 GB1 与 AAV 两个数据集上把它补齐,并顺带给本项目的中心论点(上位效应)提供定量支撑。

## Goal

产出一张可引用的定量表,回答:**加性可预测性如何随突变阶数衰减,以及缺测覆盖在其中占多少。**
成功判据是四层结果齐全(分布 / 可预测性 / 上位 / 缺测覆盖)且能由一条命令复现。

## Context

已确立的承重事实,直接决定本任务的解读口径:

- AAV 真峰 `QEEEIRTTNPVATEQYGEASTNLQRGNR` = {D0Q, S17E, V18A},HD3,**正上位**
  (实测 8.416205 ≫ 加性预测 ~6.3);WT `DEEEIRTTNPVATEQYGSVSTNLQRGNR` = −0.918194。
- 三个单突变**单独都有益**:D0Q +1.220 / S17E +4.206 / V18A +1.808。
- 二阶只有两对有实测:D0Q+V18A=2.087894、S17E+V18A=5.770209;
  **D0Q+S17E 在数据表里根本没有测量**(fact F-E9C38438 supersedes F-5A4B6556)。
  这一条是承重的,**不要写回旧版本的说法**(旧说法「cold-start 已含全部 doubles」为假)。
- GB1:149,361 个有真值变体,WT `VDGV` = 1.0,全局最优 `FWAA` = 8.761966。

## Required Reading

- `lab/context/research/plateau-breaking-methods.md` §0(双因素机制,已按上述事实改写)
- `models/alpha_sweep.py`(answer-agnostic 的 alpha 选法,本任务直接复用)
- `features/pools.py`、`evolution/mutations.py`、`evolution/datasets.py`(数据接口,只读)

## Entry Conditions

worktree `.worktrees/t-mutation-order` 已建好,`.venv` 与 `data/aav/full_data.csv` 已符号链接。
基线 `origin/main`。

## Dependencies

无阻塞依赖。与 `task_73e3a88adf751c868a5d5f6967`(保守位点)同写 `analysis-v0.1/`,
但各写自己的文件,互不重叠。

## Execution Surface

**只动**:`analysis/mutation_order.py`、`tests/test_mutation_order.py`、
`lab/reports/analysis-v0.1/{gb1,aav}/mutation_order.*` 与其 figures、
`lab/reports/analysis-v0.1/report.md`。

**不要动**:`evolution/`、`agent/`、`models/`、`knowledge/`、`events/`、`app/`——都有其他
worker 在飞;只读它们没问题。也不要动另一个 worker 的 conservation 文件。

## Constraints

- **alpha 不许固定**(fact F-5CC3FABA)。任何回归比较里 alpha 必须在训练集内 answer-agnostic
  地选;直接复用 `models/alpha_sweep.py` 的选法。固定 alpha 的比较不是特征比较,是在报告
  alpha 恰好贴合谁的尺度。
- 不得用真峰成分做任何模型选择或特征筛选。真峰只能出现在**事后**的上位分析里。
- 数值全精度进 JSON,报告里再取舍。图要有轴标签和图例。

## Checkpoint

四层里任一层做不出来(例如某数据集的阶数信息拿不到),**带证据回报并停手**,
不要降级成三层就交。发现 plan 里的判断错了同样回报,别按错的 mission 往下做。

## CI/Gate Authority Stop Condition

停止点 = `pytest tests/test_mutation_order.py` 绿 + commit。**不 push、不发 PR、不打 tag。**
不要跑全量测试矩阵(同机有多个 worker,会把机器拖死)。

## Implementation Plan

按阶数分组,每个数据集给四层:

1. **分布层**:每阶的变体数、fitness 分布(中位数/分位数/最大值)、有益比例(相对各自 WT)。
2. **可预测性层**:低阶训高阶测的外推设定(≤1 训 → 2 测;≤2 训 → 3 测),报 Spearman。
   这是「加性表达力随阶数衰减」的核心表。
3. **上位层**:对低阶实测完整的高阶变体,算 观测 − 加性预测 的残差(上位量);
   给每阶的上位量分布,并列出正上位最强的若干变体。**AAV 真峰必须在这张表里**,
   并明确标注它第三对二阶组合缺测。
4. **缺测覆盖层**:每阶「构成它的所有低阶组合是否都有实测」的覆盖率。
   这是上面那条承重事实的一般化,**是本任务最有价值的产出**。

## Deliverable Contract

- `analysis/mutation_order.py` —— 可执行入口,一条命令产出全部指标。
- `lab/reports/analysis-v0.1/gb1/mutation_order.json` 与 `.../aav/mutation_order.json`。
- `lab/reports/analysis-v0.1/{gb1,aav}/figures/` 下的阶数对比图。
- `lab/reports/analysis-v0.1/report.md` —— 方法、四层结果、定量结论。
- `tests/test_mutation_order.py`。

## Evidence Protocol

- 每个数字标明实测还是估算。
- **阳性对照必做**:构造一个已知纯加性的合成地形,断言上位量近零;再构造一个已知有交互的,
  断言上位量显著非零。把上位量计算改坏后测试必须变红——空结果不算通过。
- 缺测覆盖率要给出计算口径(分母是什么)。

## Verification

- `pytest tests/test_mutation_order.py` 在冻结提交树上全绿。
- CEO 会自己跑入口命令核对 JSON,并抽查 AAV 真峰那一行的数值。
- CEO 会验阳性对照真的能红。
