# Review review_de_reviewer_20260914_r2

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_ed9e41ef27c8fb94e8a99062a8
- Execution: exe_0ff109b77b6541e6ba80f8a467
- Verdict: changes_requested
- Commit: null
- Iteration: 2
- Content digest: sha256:0d073d0cc2ec38fa030f404e682752cad2f928d3c14cd23914436be912143c0c
- Submission digest: sha256:008133e806fa7d6e4ef9dcda1dba8b5e436ceb66ebe27759d4effd1764a8e542
- Reviewed at: 2026-09-14T09:54:07.221Z
- Consent: pending
- Consent actor: pending
- Consent source: pending

## Reason

打回：最新 submitted execution 的唯一交付物仍未完成修订，回执中声称“事实层与推荐结论被逐条推翻”，但 artifact 磁盘内容仍是旧版（SHA-256 2f8cf97b77efe71786d82d7ee83cbbbc09d3a0833c107c6276f008d6a9ca33fc，85 行）。具体缺陷：1) AAV 仍写约8.4万条、sequence/viral_viability、约10MB模糊下载源，并声称含Indel且必须放弃one-hot；本地 evolution/datasets.py + load_aav 实测清洗后为38,265条、28 aa substitution-only，字段映射为 mutated_region/score/number_of_mutations -> seq/fitness/hd，下载对象为 splits/aav/full_data.csv.zip，one-hot可用。2) AAV 推荐仍预测 random 收益为0、greedy卡死、Agent/knowledge显著分化；本地 pool_one_hot.metrics.json 显示固定 measured pool 下 greedy/no-knowledge/knowledge 的 final_cum_top10_max 均为7.5301，strong分别85/85/86，random为5.9092、35，故这些必须与“已实测”分栏，不能作为结论。3) AAV 的难度/上位效应和低阶不可外推仍无可追溯论文或本地定量证据。4) 报告仍保留 avGFP、TEM-1、ProteinGym 的未充分核实精确数字/字段/获取位置；必须逐项标[需核实]或给直接可核查来源。5) 报告的低阶冷启动方案仍未落实固定池口径；应明确 HD≤2 cold start=10,433、HD>2 candidate pool=27,832，并说明 candidate max=8.416205、cold-start incumbent=9.536457、候选池零条超过 incumbent，不能把候选池峰值与全表/全局峰混称。6) execution Verification/Completion claim 的表述应只证明本任务声明的唯一交付物 artifacts/harder-dataset-survey.md；不能以 loader、workflow 或 agentic 产物替代报告修订本身。修复方向：直接重写并重新提交 artifact，以本地 loader/metrics 和 revision-report/题面为真源；为每个候选补直接论文/官方数据源链接、字段和统计核验状态；分离已实测结果、预测与待验证项；修正执行验证范围。

## Evidence checked

- harness/harness.yaml
- lab/tasks/task_ed9e41ef27c8fb94e8a99062a8-task/task_plan.md
- lab/context/development/ai4s-worker-handbook.md
- lab/context/research/AI4S-assignment.md
- lab/context/research/AI4S-revision-report.md
- README.md
- reports/report.pdf (pdftotext sections 6-7)
- lab/tasks/task_ed9e41ef27c8fb94e8a99062a8-task/artifacts/harder-dataset-survey.md (sha256 2f8cf97b77efe71786d82d7ee83cbbbc09d3a0833c107c6276f008d6a9ca33fc)
- evolution/datasets.py
- data/aav/full_data.csv (header audit; 284010 lines including header)
- python load_aav('one_hot'): rows=38265, seq_len=28, columns=seq/fitness/hd, max_fitness=9.53645667061
- lab/reports/workflow-v1.0/aav/pool_one_hot.metrics.json
- lab/reports/agentic-v0.1/aav/agentic.metrics.json
- lab/tasks/task_ed9e41ef27c8fb94e8a99062a8-task/executions/exe_0ff109b77b6541e6ba80f8a467.md
