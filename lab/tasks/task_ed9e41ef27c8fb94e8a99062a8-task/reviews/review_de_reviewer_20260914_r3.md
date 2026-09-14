# Review review_de_reviewer_20260914_r3

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_ed9e41ef27c8fb94e8a99062a8
- Execution: exe_a1307d0ec99228851659bb0a4f
- Verdict: changes_requested
- Commit: null
- Iteration: 3
- Content digest: sha256:cdb05eda5e3a69012043f5589c03ae5e8f16367a09ea1955badefa96575fe827
- Submission digest: sha256:e9514852125a6b98353c1c05177485a53db672662f1dcb68a171442fbc1466dd
- Reviewed at: 2026-09-14T10:41:12.044Z
- Consent: pending
- Consent actor: pending
- Consent source: pending

## Reason

打回：最新 artifact 已修正 AAV 的 38,265 条、真实字段、等长 substitution-only 清洗和固定池数字，但仍未达到任务要求的可供 CEO 拍板的 ground-truth 调研标准。关键缺陷：(1) AAV 仍以“病毒组装约束极强/上位效应陡峭/低阶无法线性外推”直接打 5 分，报告没有 Bryant/FLIP 的可追溯论文或数据链接，也没有本地 epistasis/HD 外推统计支撑；仅有 GitHub 根链接不足。(2) AAV 推荐与硬目标不自洽：本地 metrics 明确 candidate_pool=27,832、cold_start=10,433，cold-start incumbent=9.536457 高于 candidate max=8.416205，且 greedy/no-knowledge/knowledge 的 final_cum_top10_max 均为 7.5301（strong 85/85/86）；报告虽承认局限，却仍把 AAV 的“更难/策略分化”作为首选结论，没有重定义为受限池发现或更换可藏峰 split，也没有把 Agent/知识差异的独立实验限制为非 LLM harness 证据。(3) avGFP、ProteinGym 高难 DMS、TEM-1、Meltome、GB1 split 的表格和方案仍用未核实或泛化数字/判断（如“通常数万”“约 5000”“跨物种全长”“存在阈值型上位效应”），未逐项标 [需核实]，未给具体 assay、直接下载 URL、字段、WT/fitness 定义和可核查统计；ProteinGym 仍写“TrpB / Pab1”泛称，不能作为一个可执行候选。(4) avGFP 仅说明仓内落点与 loader 的嗅探字段，不是外部数据源核验；报告明确说“ProteinGym 原始列名大概率”，这仍是推测，且 WT 行要求/补行会改变原始 oracle，应给可复现转换规则和证据。(5) 表中 Meltome 的判据 b 使用“−”而非 1–5 分或明确 N/A 及理由，未完整满足逐项评分/标注；“能直接插入”对 avGFP/ProteinGym 也超出已核实证据。(6) 执行 closeout/claim 声称报告已交付，但报告中大量更正叙述和 `后由 decision 锁定` 不是对候选调研的来源引用；应只把本 artifact 的实际检查列为 verification。修复方向：为每个候选选定具体 assay，附论文/官方仓库/直接文件 URL和许可，统计与字段逐项标实测/文献/[需核实]；把 AAV 的 fixed-pool 实测结果与预测分栏并重新判断是否仍是 Top-1，明确不能超越已知 incumbent；若保留推荐，改成可验证的评测定义和验收指标。

## Evidence checked

- harness/harness.yaml
- lab/tasks/task_ed9e41ef27c8fb94e8a99062a8-task/task_plan.md
- lab/context/development/ai4s-worker-handbook.md
- lab/context/research/AI4S-assignment.md
- lab/context/research/AI4S-revision-report.md
- README.md
- lab/tasks/task_ed9e41ef27c8fb94e8a99062a8-task/artifacts/harder-dataset-survey.md (sha256 696fc4cc749b0efc94e55894e4b237079a7153beab5bfa13a733ab69c0fd6f59; 87 lines)
- evolution/datasets.py (load_aav source and loader contract)
- lab/reports/workflow-v1.0/aav/pool_one_hot.metrics.json
- python load_aav('one_hot'): rows=38265, seq_len=28, columns=seq/fitness/hd, max_fitness=9.53645667061
- local metrics summary: candidate_pool=27832, cold_start=10433, cold_start_hd=2; random=5.9092/35, greedy=7.5301/85, agent_no_knowledge=7.5301/85, knowledge_agent=7.5301/86
