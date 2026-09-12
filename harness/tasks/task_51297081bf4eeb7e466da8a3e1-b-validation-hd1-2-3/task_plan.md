# 包B/评测协议补全:validation 职责接入选模 + 按突变阶数分组比较优化效果

Task Contract: harness-task v1

## Brief

覆盖度审计留下两个与"评测协议"有关的缺口:(H04)试题明写"划分训练、验证、测试",我们三池隔离是真的,但**没有任何训练/选模代码实际消费 validation**——超参选择和最终评估用的是同一批数据的不同切法;(B03,加分项)试题要"比较单点、双点、多点突变的优化效果",我们只有 HD 分层的特征/池结构,**没有相同预算下按突变阶数的优化效果对照**。两者都只动评测侧,不碰 Agent 主链,适合一个包做完。

## Goal

1. **让 validation 真正承担职责**(H04):在当前协议里明确 train / validation / query-test / holdout 四者的角色,并让训练与选模代码**实际读取 validation** 来选超参(例如 Ridge 的 alpha),最终评估只看一次 holdout。产出:一条能证明"换了 validation 集合,选出的超参会变"的证据——否则等于没接。
2. **按突变阶数分组比较**(B03):在**相同预算**下,按 HD=1 / HD=2 / HD>=3 分组报告命中率、增益和预算效率,回答"多点突变到底值不值得花预算"。这不是重跑实验,是对已有轨迹做分组统计 + 必要时一次受控小跑。

首个消费者:最终报告的"适应度预测模型"节(第 1 项)与"虚拟定向进化实验结果"节(第 2 项)。

## Context

- **权威审计**:`harness/context/research/assignment-coverage-audit.md`。H04 判定:"主评测没有显式 validation 的训练/调参职责;原 CSV 虽有 legacy `*_validation` 列,但当前训练入口未消费";证据 `features/pools.py:19-26,45-60`、`models/evaluate_all.py:36-39`;E1 证明三池 5000/50000/94361 两两交集为 0、并集 149361。B03 判定:"没有相同预算下按突变阶数的优化效果对照",证据 `features/pools.py:29-42`。
- **试题原文**:`harness/context/research/AI4S-assignment.md`,二·数据(划分训练/验证/测试)、二·预测模型(Spearman/Pearson/MSE/Top-k)、五·加分项第 3 条(比较单点/双点/多点)。
- **口径不得动**:GB1 三池 5000/50000/94361;AAV 池 27832 / cold-start 10433 / 门内 9533 / 预算 288。这些是全线可比性的基础,本包**只加评测维度,不改口径**。
- 最终科学定性以 fact `F-885537A3` 为准;本包不改变科学结论。
- 相关既有事实:`F-E9C38438`(真峰隐形是"关键二阶组合缺测 + 模型表达力"双因素)——第 2 项的分组统计正好能给这条提供独立的经验支撑,留意但不要强行往上靠。

## Required Reading

1. `harness/context/research/assignment-coverage-audit.md`(**最高权威**:H04 与 B03 两行及其证据)。
2. `harness/context/research/AI4S-assignment.md`(**标尺**)。
3. `features/pools.py`、`models/evaluate_all.py`、`models/train_ladder.py`(**待改主体**:池切分与选模入口)。
4. `evolution/pool_campaign.py`(AAV 轨迹产物结构,第 2 项分组统计的数据源)。
5. `harness/reports/workflow-v1.0/gb1/predictor_ladder.json` 与 `harness/reports/agentic-v0.*/` 下的 metrics(已有轨迹,先看能不能直接分组,能就别重跑)。

## Entry Conditions

- 独立 worktree(`t-pkgB-eval-protocol`);`.venv` 与数据 symlink 就位。
- 基线:`.venv/bin/pytest -q tests/test_data_pipeline.py` 全绿。不绿先报。
- 第 2 项开工前**先确认已有轨迹里是否已记录每条提名的 HD**;若已记录,直接分组统计,不要重跑 campaign。

## Dependencies

- 上游:覆盖度审计(`task_d5e9455a1235d1554b1967c708`)。
- 下游:最终报告 v2.0(`task_db4ace109f72a92847c7349fe1`)。
- **并发(硬约束)**:包A(`task_0bc2d4d678eea24c4930b60a0e`,动 `evolution/campaign.py`/`agent/pipeline.py`/`agent/llm.py`/`app/demo.py`)、包C(`task_6d1dc285d32628ed317b9bb4da`,动 `README.md`/`Makefile`/`harness/reports/**`/`reports/**`)、知识增强实验(`task_25092f640504bf3b040f6adfb5`,动 `knowledge/**`/`agent/auto_researcher.py`)。**全部是禁区。**

## Execution Surface

- 分支 `t-pkgB-eval-protocol`;dispatcher 注入 cwd。
- **允许写**:`features/pools.py`、`models/evaluate_all.py`、`models/train_ladder.py`、`analysis/**`(新增分组统计脚本)、对应测试,以及 `harness/reports/pkgB-eval-protocol/**`。
- **禁区**:上面"并发"里列出的所有路径;`evolution/datasets.py` 与 `evolution/campaign.py` 的口径;CI/oracle。
- 禁区之外自行判断,事后汇报动了哪些我没预见的面。

## Constraints

- **不改池口径**。任何会让 5000/50000/94361 或 27832/10433/9533/288 变化的改动即为越界,停手报告。
- **validation 要真接上**:只在文档里声明角色不算。必须有代码路径读它,且有证据显示它影响了选参结果。
- 第 2 项**优先用已有轨迹做分组统计**;确需补跑时,只补最小的一次受控跑并预注册参数。
- 加分项结论要诚实:如果分组统计显示多点突变在本题不划算,如实写,不要为了"加分项看起来完成"而粉饰。
- 新产物的模型字段(若有)写实际解析值,不抄 `gpt-5.6-sol`。

## Checkpoint

- 第 1 项做完即停并报:贴出"换 validation 集合 → 选出的 alpha 变化"的实际输出。没有这条证据就等于没接上。
- 第 2 项开工前报一句:已有轨迹够不够做分组(够就不重跑)。
- **异议型停**:若发现当前协议下 validation 无法在不破坏可比性的前提下接入(例如接入会改变历史结果),停下来报设计问题与替代方案,不要硬改。

## CI/Gate Authority Stop Condition

非 CI/gate 任务。已知本仓 standard-task 的 ci 完成门结构性不可满足(fact `F-8ED77039`,上游修复在飞);submit/complete 必被拒。不绕门、不改 CI、不 `transition --force`;失败即记录进度并停手。

## Implementation Plan

- 盘清现有三池/四池角色与当前选参实际用了什么。
- 接入 validation:选参只看 validation,最终一次看 holdout;补一条"换 validation → 选参变化"的断言测试。
- 读已有轨迹,按 HD=1/2/>=3 分组算命中率、增益、预算效率;出一张可直接进报告的表 + 一张图。
- 写 `harness/reports/pkgB-eval-protocol/report.md`。
- `ha task progress append` 留痕;`ha fact record --task task_51297081bf4eeb7e466da8a3e1` 记承重结论。

## Deliverable Contract

- validation 接入的代码 + 证据(选参随 validation 变化的实际输出)。
- `harness/reports/pkgB-eval-protocol/report.md`:四池角色定义、validation 接入证据、按突变阶数分组的表与图、诚实判定(多点突变值不值)。
- 点名测试绿(`tests/test_data_pipeline.py` + 新增;**不要跑全量矩阵**)。
- ≥1 条 fact;本地 commit,不 push、不开 PR。
- 回报:validation 接上没有(附证据)+ 分组结论一句话。

## Evidence Protocol

- "validation 真接上"是结构断言,要 grep 调用点两侧 + 一条行为证据(选参变化)。
- 分组统计要说明数据来自哪些轨迹文件、样本量多少;样本量不足的分组要标注而不是硬给结论。
- 区分实测与估算。

## Verification

- 停手点 = 代码 + report + 点名测试绿 + ≥1 fact + 本地 commit。
- CEO 语义验收(validation 是否真承担职责、分组结论是否诚实)不可下放。
