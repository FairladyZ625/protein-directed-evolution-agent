# Review de-reviewer-20260912-plateau

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_d3dfe26bf702928b1c3784e60f
- Execution: exe_a41f6335621459a841dbcdc3ff
- Verdict: changes_requested
- Commit: ec3f6d56b96723f4c6d10ce9e431f94a6ac68295
- Iteration: 0
- Content digest: sha256:13ce300cdd779de7c4bbef5a7a943df7ec6d137b2002b47297edf496fac5c70d
- Submission digest: sha256:a30d377d54e73fc2536e36cc467756af81d344628aaa90c4c916464aebc6ec26
- Reviewed at: 2026-09-12T09:41:22.771Z
- Consent: pending
- Consent actor: pending
- Consent source: pending

## Reason

打回：交付文档的承重机制事实与本轮 oracle 复算矛盾。真峰三组二阶子组合中 D0Q+S17E 不在数据表，不能声称 cold-start 已含构成真峰的全部 doubles，也不能据此排除数据覆盖并把瓶颈唯一归因于 surrogate 表达力。该错误已进入正文、两条 task fact、排序清单和首选实验论证。文献条目也未满足逐条五要素与可核书目契约，多数仅列作者/刊物/年份且正文承认未逐篇核验；提交 Deliverables/commit 又指向无关 rsi-cybernetic 工件，而非本任务研究文档。需修正文档和事实、重新给出 answer-agnostic 排序依据、补齐可核引用与五要素映射，并 amend submission 到正确 deliverable/content pin 后再审。

## Evidence checked

- task_plan.md、AI4S-assignment.md、ai4s-worker-handbook.md 与提交 execution exe_a41f6335621459a841dbcdc3ff
- 磁盘及提交 pin 的 plateau-breaking-methods.md，SHA256=428095b1e3045e2f197acadcdf74eb56b56916f76088f14af8750946048ee255
- 使用 evolution.datasets.load_aav() 对 data/aav oracle 复算：38265 行；WT=-0.9181937107；峰=8.41620513056；D0Q+S17E double 缺失，D0Q+V18A=2.08789430573，S17E+V18A=5.77020873916
- lab/context/research/v07-peak-mechanism.md：独立后续审计同样认定关键二阶组合缺测、低阶随机验证不能代表 HD3-4 头部排序
- ha fact search --task：F-5A4B6556 与 F-851790B5 均仍声称全部单/双突变已测，和 oracle 不符
- git show ec3f6d5：提交只变更 research/rsi-cybernetic 三个文件；execution Deliverables 同样列出这三个无关路径
- 结构检查：7 个方法族、10 项排序、3 个实验提名存在；但各方法未逐条提供原理/文献/破峰原因/工具新增/answer-agnostic 五要素
- Crossref/OpenAlex 阳性对照可返回 EVmutation、Epistatic Net、ECNet、MULTI-evolve 等规范书目；交付正文除 MULTI-evolve 外多数无标题/DOI且自标未逐篇核实
