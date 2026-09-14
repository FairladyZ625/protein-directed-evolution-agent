# Review review_de_reviewer_20260914_r5

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_ed9e41ef27c8fb94e8a99062a8
- Execution: exe_499602fd19b231c42c6448dc7e
- Verdict: changes_requested
- Commit: null
- Iteration: 5
- Content digest: sha256:3540dd1953f38739c8ccf75a9aedc46a03a3df4afc7359641790b71d5b125409
- Submission digest: sha256:c067fdc962cb811d4df05c43cf2d0dd7f8d1387ed37c8c746eb8170533fda3c4
- Reviewed at: 2026-09-14T14:04:12.164Z
- Consent: pending
- Consent actor: pending
- Consent source: pending

## Reason

打回：当前提交已修正主要 AAV 池数字、池内峰边界、非 AAV 表格逐格标记与产物路径，但仍有三处必须修正。

1. 中心科学表述过宽且被本地真值反驳。artifact:61 写 `D0Q+S17E` 缺测后称“加性单步上升路径确实不存在”。对当前三突变峰，实际存在严格递增的已测路径 WT(-0.9181937107) → S17E(3.2874179974) → S17E+V18A(5.7702087392) → D0Q+S17E+V18A(8.4162051306)；缺的是特定的 `D0Q+S17E` 二阶垫脚石/该分支路径，不是所有单步上升路径。请改成特定路径不可观测，并保留“正式三阶系数不可算”的边界。

2. 诚实标注仍有正文泄漏。artifact:84 再次写模型记忆数字“全长 238”，artifact:105 的结构建议又写“238 位点”，两处没有 `[需核实]`；任务 plan:58 要求模型知识给出的规模/数字明确标注。表格六个非 AAV 行的六个判据单元格已逐格带 `[需核实]`，但不能替代正文重复出现处的标注。请在两处加标记或删去精确数字，并检查同类重复。

3. 副指标的消融解释缺少关键混杂条件。artifact:54/71 使用 `lab/reports/knowledge-ablation/metrics.json` 的 54.0→162.333 strong、平均 HD、Jaccard，但该产物 protocol 明确写明 no-knowledge 可访问源池 27,832，而 knowledge treatment 应用 HD/BLOSUM 门禁、有效门内池为 9,533；`strong_threshold` 也应明确为 2.615913579904（或引用字段）。当前措辞“知识臂确实显出价值”容易被读成知识/图谱单因素优势。请把结论改成复合 HD/BLOSUM 门禁+图谱处理效应，列出两侧候选空间/阈值，并保留其“36/36 LLM 轮次超时、不能证明 LLM 因果增益”的限制。

治理残留：`ha fact show` 显示 standing Fact F-51F2E349 仍声称“greedy 可证明够不着”且 Fact F-9649A483 仍保留“约 8.4 万/强上位/外部核实”等已被当前 ground truth 推翻的内容。当前 artifact 的更正 prose 不能替代 append-only fact supersession；请通过 Harness 追加更正 Fact 并 supersede/建立关系，或在任务收口前明确移交责任。

修复后重新提交同一 execution；无需修改业务代码。

## Evidence checked

- lab/tasks/task_ed9e41ef27c8fb94e8a99062a8-task/task_plan.md:13-18,58,77-89
- lab/tasks/task_ed9e41ef27c8fb94e8a99062a8-task/artifacts/harder-dataset-survey.md (sha256 997b876ec542fe282d96fb545d25063bd6a4f64a18fb7bebd12f09c13ce65929; wc -l=123; table=6 candidates x 6 criteria)
- evolution/datasets.py:61-86 and .venv load_aav(one_hot) audit: rows=38265, columns=seq/fitness/hd, cold=10433, pool=27832, pool_max=8.416205130560002, cold_max=9.53645667061, pool_gt_incumbent=0
- AAV raw-data path audit: category=designed 30932/38265; pool peak and cold incumbent both category=designed
- AAV path audit: WT=-0.9181937107, S17E=3.2874179974, S17E+V18A=5.7702087392, triple=8.4162051306; specific D0Q+S17E is missing; strictly_increasing=True
- lab/reports/workflow-v1.0/aav/pool_one_hot.metrics.json: random=5.9092/35, greedy=7.5301/85, agent_no_knowledge=7.5301/85, knowledge_agent=7.5301/86
- lab/reports/knowledge-ablation/metrics.json: source protocol 27,832 with knowledge HD/BLOSUM filtering, strong_threshold=2.615913579904, agent_no_knowledge strong_mean=54.0, knowledge_agent strong_mean=162.3333333333
- lab/context/research/v07-multiseed-evidence/summary.json and protocol.md: ucb3 30/30, mean 0/30, deterministic duplicate caveat
- ha fact show --id F-51F2E349 and --id F-9649A483: both state=standing with superseded claims
