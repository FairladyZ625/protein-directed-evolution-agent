# 试题逐条覆盖度审计:AI4S-assignment.md 的每一条要求 vs 仓库现状

Task Contract: harness-task v1

## Brief

我们在 v0.1→v0.7 的科学深挖上走得很远,但**没有系统核对过试题原文的每一条要求是否都交付了**。CEO 抽查已发现至少一处硬缺口(题目明写"比较有无知识增强时 Agent 推荐序列的差异",而 AAV 主线七个版本里没有做这个对照)。本任务把整份试题拆成可勾核的条目,逐条 ground-truth,给出差距清单。

## Goal

产出 `harness/context/research/assignment-coverage-audit.md`:一张**逐条对照表**,试题里每一个可验收的要求一行,列:

| 试题条目(原文摘要) | 出处(二/三/四/五章第几条) | 状态(已交付/部分/未做) | 证据(具体文件路径 + 行/命令,或"无") | 差距与最小补齐动作 |

**判定必须 ground-truth**:`ls`/`grep`/实跑,不许凭报告里的声称。报告里写了但代码里没有 = 未做;代码里有但没有调用点 = 未接线(单列一类,不能算已交付)。

最后给一个**优先级排序的补齐清单**:哪些是硬要求缺口(必须补)、哪些是加分项缺口(可选)、每项的最小工作量估计。首个消费者:CEO 排期 + 最终报告的自检。

## Context

- 试题原文镜像:`harness/context/research/AI4S-assignment.md`(权威原件是明度数智的 docx)。
- 试题结构:二、项目任务(数据处理 / 适应度预测模型 / 科学智能体设计 / **知识增强设计** / 虚拟定向进化实验 / 结果分析与展示);三、详细要求(实验报告 8 节 / 代码 / 结果展示 4 类);四、考核重点 7 条;五、加分项 7 条。
- **CEO 已抽查确认的两处缺口,审计时直接采信并继续找别的**:
  1. `knowledge/validators.py` 的 `build_knowledge_graph`(networkx MultiDiGraph)**只在 `tests/test_knowledge.py` 被调用**,未接进 `agent/auto_researcher.py` 主链路——即"知识图谱"是存在但未接线。
  2. `no_knowledge` 开关只在 GB1 的四策略 campaign(`agent_no_knowledge` vs `knowledge_agent`)用过,**AAV 主线 v0.1–v0.7 没有做有/无知识增强的对照**。
- 主要交付面:`evolution/`、`models/`、`features/`、`knowledge/`、`agent/`、`app/demo.py`、`analysis/`、`reports/`、`harness/reports/agentic-v0.*/`。
- 注意版本时效:最终科学定性以 fact `F-885537A3` 为准(两目标两策略),早期报告的结论已被取代——但**本任务审的是"要求有没有做",不是"结论对不对"**,别混。

## Required Reading

1. `harness/context/research/AI4S-assignment.md`(**最高权威**:被审标尺,逐字读完)。
2. 仓库根 `README.md`(声称了什么)。
3. `agent/auto_researcher.py`、`app/demo.py`、`knowledge/validators.py`、`models/train_ladder.py`、`evolution/datasets.py`(**主要被审主体**)。
4. `harness/context/research/v07-consolidated-summary.md`(已有成果全貌,避免把做过的判成没做)。
5. `reports/scientific_report_v1.0.md`(报告章节 vs 试题要求的 8 节对照)。

## Entry Conditions

- 上述文件可读;`.venv` 可用(需要实跑验证时)。
- 若发现试题镜像与某处描述矛盾,以镜像为准并记下矛盾点。

## Dependencies

- 上游:无(纯审计)。
- 下游:CEO 排期、最终报告 v2.0(`task_db4ace109f72a92847c7349fe1`)、知识增强对照实验(`task_25092f640504bf3b040f6adfb5`)。
- 并发:只写一份新研究文档,与所有在飞任务无文件面冲突。

## Execution Surface

- 仓库根或独立 worktree(建议 `t-audit`);dispatcher 注入 cwd。
- **允许写**:仅 `harness/context/research/assignment-coverage-audit.md`(+ 自己 worktree 内的临时核查脚本,不进产品树)。
- 禁区:所有产品代码、所有已有 report、CI/oracle。本任务只看不改。

## Constraints

- **不许凭声称判定**:每个"已交付"必须附可复核证据(文件路径 + 关键行,或一条能跑出结果的命令)。存在 ≠ 被接线——躺在仓库里没有调用者的模块,单列"未接线",不算已交付。
- **不许粉饰**:缺口就写缺口。这份审计的价值全在它的诚实度上,写成"基本都做了"等于没做。
- 不做补齐实现(那是下游任务),只审计 + 给最小补齐动作。
- 加分项(第五章)单独成表,不要和硬要求混在一起,以免把可选项当缺口吓人。

## Checkpoint

- 审完试题"二、项目任务"六个小节即停并报第一版对照表 + 已发现的硬缺口数,CEO 确认标尺理解无误后再审三/四/五章。
- **异议型停**:若发现某条要求我们其实用另一种更强的方式满足了(例如题目要的"2—3 轮迭代"我们做了 6 轮),按"已交付(超出)"标注并说明,不要机械判不符;但若是**换了个东西交差**(题目要 A 我们做了 B),必须判未做并说清。

## CI/Gate Authority Stop Condition

非 CI/gate 任务(docs-task 无 CI 门)。不碰 CI/门禁/oracle。若 `ha` 生命周期命令报错,记录后继续,不绕门。

## Implementation Plan

- 把试题拆成编号条目(建议 40–60 条),每条写清"可验收的判据是什么"。
- 逐条 `ls`/`grep`/实跑核查,填证据列。
- 对"存在但未接线"的,贴出 grep 调用点的两侧证据。
- 汇总三张表:硬要求缺口 / 加分项缺口 / 已交付(带证据)。
- 出优先级排序的补齐清单,每项给最小工作量估计。
- `ha fact record --task task_d5e9455a1235d1554b1967c708` 记承重结论(缺口总数 + 最关键的 2–3 个)。

## Deliverable Contract

- `harness/context/research/assignment-coverage-audit.md`:逐条对照表 + 三张汇总表 + 优先级补齐清单。
- ≥1 条 fact。
- 回报:硬要求缺口几条、分别是什么、最该先补哪一条、为什么。
- 不改产品代码、不 push、不开 PR。

## Evidence Protocol

- 每个状态判定附证据(路径+行,或命令+输出摘要);无证据的判定一律标 `[未核实]`。
- 区分"已交付 / 部分交付 / 存在但未接线 / 未做"四态,不要只用二态。
- 实跑与静态阅读要分开标注。

## Verification

- 停手点 = 文档写完 + ≥1 fact + 摘要回报。无产品代码改动。
- CEO 语义验收(标尺是否理解正确、诚实度是否达标)不可下放。
