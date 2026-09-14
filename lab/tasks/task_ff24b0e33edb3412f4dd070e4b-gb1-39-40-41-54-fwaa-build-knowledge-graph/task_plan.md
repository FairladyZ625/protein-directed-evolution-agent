# 清理知识库 GB1 遗留硬编码,并处置未接线的 build_knowledge_graph

Task Contract: harness-task v1

## Brief

知识库模块里残留着 GB1 时期的专用硬编码(位点 39/40/41/54、FWAA 野生型片段),而主战场早已是 AAV(WT 28 残基窗口)。这些是死代码,留在公开交付仓里会让读者以为我们的知识库是针对 GB1 调过的。同时 `build_knowledge_graph` 没有任何调用点——存在但未接线,与"没做"同形。

## Goal

产出干净的 `knowledge/` 模块:GB1 专用常量要么删除,要么显式参数化为"数据集特定配置"并由调用方注入;`build_knowledge_graph` 要么接进主链路并给出它改变了什么,要么删掉并在 closeout 说明为什么不需要。两条路都可接受,**但必须二选一,不能继续放着**。

## Context

- 发现来源:`lab/context/research/kb-iteration-research.md`(fact `F-159073F2`),该文档同时盘点了现有 KB 到底编码了什么。
- 现状:`knowledge/rules.yaml`(20 氨基酸理化属性 + 部分 BLOSUM62)、`knowledge/validators.py`(`validate_mutations` 实现 R-BLOSUM-CONSERVATIVE score≥1 与 R-BLOSUM-AGGRESSIVE score>−1;`build_knowledge_graph` 无调用点)。
- 链路消费点:`agent/auto_researcher.py` 的 `_gate`(HD + mean BLOSUM 门禁)与 `check_knowledge`。
- **门禁口径必须保持不变**:HD≤4 且 mean BLOSUM62≥0 → 门内 9533 个候选。这个数是 v0.5–v0.7 全部实验的可比性基础,清理不得改动它。

## Required Reading

1. `lab/context/research/kb-iteration-research.md`(**权威**:现状盘点与问题定位)。
2. `knowledge/validators.py` + `knowledge/rules.yaml`(**待改主体**)。
3. `agent/auto_researcher.py` 的 `_gate` / `check_knowledge`(调用面,决定哪些是真接线的)。
4. `evolution/datasets.py`(AAV WT 与窗口口径,确认 GB1 常量确实无用)。

## Entry Conditions

- 清理前先跑一次现有门禁,记录门内候选数 = 9533 作为回归基准。跑不出这个数就先停下查口径,不要在口径已漂的状态下清理。

## Dependencies

上游:KB 研究。下游:v0.8-C(`task_135d946b4d8fa566d87b063fa6`)在此之上改,**本任务应先做**;最终报告 v2.0 的知识库描述。并发:与 v0.8-C 同文件面,不得并行。

## Execution Surface

仓库根或独立 worktree;允许写 `knowledge/**`、相关测试、必要时 `agent/auto_researcher.py` 的知识库调用处。禁区:池口径、surrogate、已有 report、CI/oracle。

## Constraints

- **门内候选数必须仍为 9533**,清理后回归验证;变了即为越界,停手报告。
- 不得顺手"改进"规则阈值——本任务只做清理与接线判定,功能变更属 v0.8-C。
- 删除优于保留:留下一个机制才需要举证,删掉不需要。

## Checkpoint

清理完成、回归跑出 9533 即停并报:删了什么、`build_knowledge_graph` 选了哪条路、理由。**异议型停**:若发现某个 GB1 常量其实仍被间接消费,停下来报调用链,不要硬删。

## CI/Gate Authority Stop Condition

非 CI/gate 任务。本仓 standard-task 的 ci 门结构性不可满足(`F-8ED77039`);不绕门、不改 CI。

## Implementation Plan

- grep GB1 专用常量(39/40/41/54、FWAA)的所有出现与调用链。
- grep `build_knowledge_graph` 调用点,确认为零后二选一处置。
- 改完跑门禁回归(9533)+ 定向测试。
- `ha fact record --task task_ff24b0e33edb3412f4dd070e4b` 记清理结论。

## Deliverable Contract

清理后的 `knowledge/` + 门禁回归证据(9533)+ 定向测试绿;≥1 fact;回报删了什么、接线怎么定的。

## Evidence Protocol

"无调用点"这类结构断言必须贴 grep 两侧证据,不能只说"我看了没有"。回归数字贴真实输出。

## Verification

停手点 = 清理落盘 + 9533 回归通过 + 测试绿 + ≥1 fact。
