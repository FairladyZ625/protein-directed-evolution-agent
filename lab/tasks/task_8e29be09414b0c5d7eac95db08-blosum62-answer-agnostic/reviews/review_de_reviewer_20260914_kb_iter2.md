# Review review_de_reviewer_20260914_kb_iter2

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_8e29be09414b0c5d7eac95db08
- Execution: exe_f0e3aa7dd2b354ba7a49a4ba4f
- Verdict: changes_requested
- Commit: null
- Iteration: 2
- Content digest: sha256:316123e59da77d536586c69657ad1c52301a87a7e1817707123c31f7e848ddb8
- Submission digest: sha256:7e407ab0ba8eb2f577fddc50efbc2b782ff3fa1734bd6dceca1d6f9fb656b778
- Reviewed at: 2026-09-14T10:01:19.544Z
- Consent: pending
- Consent actor: pending
- Consent source: pending

## Reason

打回：当前 execution 的 artifact 仍不能作为 CEO 的现状与优先级依据。第一，文档第25行称指定 v07-peak-mechanism.md 不存在，但当前磁盘该路径存在且已读取；这使 read-set/证据边界陈旧。第二，文档第9、18、121、160-161行仍把 gate=9533、具体残基对=11130、未见=7937、相关候选=6852及矩阵缺136/190作为当前或承重结论，仅用勘误文字无法消除附录和结论中的冲突。按交付文档自身 runner 的 pair 定义、当前代码和同一无标签输入重跑，真实输出为 rows=38265,cold=10433,pool=27832,gate=2515,gate_residue_pairs=3878,unseen_residue_pairs=2323,gate_candidates_with_unseen_pair=1770；当前 rules.yaml 缺失无序 BLOSUM 对为0，_score(A,T/E,N/G,S/V,T)均保留显式0。第三，文档仍把 build_knowledge_graph 描述为历史上未消费/仅二元门禁，虽然表格勘误提到已接线；当前 agent/auto_researcher.py:488-508 已构建 measured-only graph 并生成 rationale，需统一现状语义。请基于当前磁盘重写现状、覆盖统计、read-set与附录输出；旧基线只能明确标注为历史且不能继续支撑当前结论。保留收益未证明、answer-agnostic 边界和 ESM zero-shot 负例的谨慎表述。

## Evidence checked

- lab/tasks/task_8e29be09414b0c5d7eac95db08-blosum62-answer-agnostic/artifacts/kb-iteration-research.md (171 lines; artifact and canonical document byte-identical)
- lab/context/research/v07-peak-mechanism.md (exists; read current root)
- knowledge/rules.yaml and knowledge/validators.py: current complete matrix; missing unordered pairs=0; _score(A,T), _score(E,N), _score(G,S), _score(V,T)=0
- agent/auto_researcher.py:488-508: measured-only build_knowledge_graph and query_mutation_context rationale path
- current-code no-fitness audit using the artifact runner definition: rows=38265,cold=10433,pool=27832,gate=2515,gate_residue_pairs=3878,unseen_residue_pairs=2323,gate_candidates_with_unseen_pair=1770
- ha task show task_8e29be09414b0c5d7eac95db08: status=in_review; execution exe_f0e3aa7dd2b354ba7a49a4ba4f submitted/open
