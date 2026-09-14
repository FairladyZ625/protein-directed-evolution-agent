# Review review_de_reviewer_20260914_r4

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_ed9e41ef27c8fb94e8a99062a8
- Execution: exe_4a45ec5648195fa1f5d301cea8
- Verdict: changes_requested
- Commit: null
- Iteration: 4
- Content digest: sha256:f581d2d63176fe783351f08a398dce237c21ccc4be9393d46648ab73b2f17a07
- Submission digest: sha256:61c8547b96faa70f334aaf7cd47bbcd7c12a1d14a33e16a11b48cffa8e6312f2
- Reviewed at: 2026-09-14T12:28:07.404Z
- Consent: pending
- Consent actor: pending
- Consent source: pending

## Reason

打回：当前 submitted execution 的 artifact 已修正主要 AAV 池数字，但仍未满足窄化后的逐项诚实验收。证据核验：load_aav('one_hot') 实测 38265 行、28 aa、列 seq/fitness/hd，max fitness 9.53645667061；pool_one_hot.metrics.json 实测 candidate_pool=27832、cold_start=10433、greedy/no-knowledge/knowledge final max 均 7.5301，strong=85/85/86。残留缺陷：(1) §1 表格的 avGFP、ProteinGym、TEM-1、GB1 split、Meltome 多个判据只在总括说明中称未核实，但逐格仍写无 [需核实] 的精确分数/判断（如 avGFP b/e/f、ProteinGym b/c/e、TEM-1 b/d/e、GB1 b/c、Meltome c/e），其中“存在阈值型上位效应”“通常数万”“高阶真值缺失”等会被读成事实；任务要求是逐项标注。(2) §2 第28行仍把 avGFP/ProteinGym 写成“能直接插入（只需写 Loader）”，超出本任务明确的未核实边界；应改成未验证的工程假设。(3) §3 第57行重新写入“病毒组装约束极强、上位效应陡峭、无法轻易低阶线性外推”，没有本地统计或可追溯来源，且与前文“本次不做外部核验/仅凭本仓实测”的效力边界冲突；应删除或明确标为未核实推测。补充：§3 的 30/30 UCB 与知识消融数字在本轮未找到由该报告明确列出的直接产物路径，不能替代上述缺陷的修复。修复方向：逐格给所有非 AAV 单元加 [需核实]（或删掉精确判断），把 avGFP/ProteinGym 的接入描述降格为待验证建议，删除/标注 AAV 无来源生物学难度断言；保持受限池发现定义和“池内峰不等于超越 incumbent”边界。未发现代码或业务文件越界修改。

## Evidence checked

- harness/harness.yaml
- lab/tasks/task_ed9e41ef27c8fb94e8a99062a8-task/task_plan.md
- lab/context/development/ai4s-worker-handbook.md
- lab/context/research/AI4S-assignment.md
- README.md
- lab/tasks/task_ed9e41ef27c8fb94e8a99062a8-task/artifacts/harder-dataset-survey.md (sha256 5774f73061ccc857c3c2f16faffd7eda6b20690ead98801a18ee75ce67ec1932)
- lab/tasks/task_ed9e41ef27c8fb94e8a99062a8-task/executions/exe_4a45ec5648195fa1f5d301cea8.md
- evolution/datasets.py
- lab/reports/workflow-v1.0/aav/pool_one_hot.metrics.json
- lab/reports/knowledge-ablation/report.md
- lab/reports/analysis-v0.1/report.md
