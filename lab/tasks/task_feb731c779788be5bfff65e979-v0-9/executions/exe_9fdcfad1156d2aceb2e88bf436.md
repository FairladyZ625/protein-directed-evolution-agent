# Execution exe_9fdcfad1156d2aceb2e88bf436

Managed by `ha task start/submit`; hand edits are rejected.

- Task: task_feb731c779788be5bfff65e979
- Iteration: 1
- State: changes_requested
- Claimed: 2026-09-14T09:54:14.498Z
- Submitted: 2026-09-14T09:55:47.708Z
- Closed: 2026-09-14T10:01:19.293Z
- Commit: 359154195e9b4cc18154bae9f740051b64fcb7b1
- Completion claim: 交付提交 `359154195e9b4cc18154bae9f740051b64fcb7b1`(结果与文档)。实现先落在同一执行的前一个
提交 `377a614b`,其变更已全部包含在上述交付切面内——一个 execution 只有一个交付 cut,故此处
只命名被交付的那个提交。

v0.8 的 2×2 测到强制注入残差对 agent 提名零影响(四臂批次逐位相同)。本任务先定位根因:
不是模型缺陷,是**工具契约的形状**——`exploit_ratio` 是标量,没有任何取值能表达
「别选带 N21D 的候选」;而唯一那个标量入口被提示词的「Prefer that default」劝退,
并被利用比地板在 campaign 后半程压成空集(实测第 4 轮起可行区间为空)。

`--contract v09` 一次性改三处(它们互相封锁,单改一处等于没改):
1. `compose_batch` 增加 `exclude_motifs`,按 `W<0-based pos>M` 剔除候选;剔除后不足 n 时
   返回 `exclusion_too_strict`,不静默缩批;
2. 新采集段落删去「Prefer that default」并点名新入口,round prompt 模板暴露参数位;
3. 释放利用比地板,使因变量不再被压成常数;
4. 反思卡片在契约开启时指向 `compose_batch(exclude_motifs=...)`,并要求说明故意保留了哪些。

两个契约的差异落在**工具 schema** 上而不只在提示词:v08 臂根本看不到 `exclude_motifs`,
否则对照臂不再是对照。

重跑同一 2×2(AAV,seed 42,288 预算,固定 `--backtrack semi --acquisition v05`):
v08 契约下批次仍未分叉;**v09 契约下批次分叉并逐轮发散**(r1 46/48 → r6 8/48)。
- Reviews: review_de_reviewer_20260914_v09_r2/changes_requested
- Selected review: pending
- Consent: pending
- Checker witnesses: ci/op_1d02ba52a64c74ef20294520a49aece9f12a520e2ad9bc8b39fd037a752c415b
- Code-doc witness: code-doc-8a5e198d966bd044

## Deliverables

- lab/facts/F-2CBCCC90.md
- lab/facts/F-CB49BF0D.md
- lab/reports/REPORT-HANDOFF.md
- lab/reports/v09-contract/contract-v08_reflexion-off_seed-42/agentic.events.jsonl.gz
- lab/reports/v09-contract/contract-v08_reflexion-off_seed-42/agentic.metrics.json
- lab/reports/v09-contract/contract-v08_reflexion-on_seed-42/agentic.events.jsonl.gz
- lab/reports/v09-contract/contract-v08_reflexion-on_seed-42/agentic.metrics.json
- lab/reports/v09-contract/contract-v09_reflexion-off_seed-42/agentic.events.jsonl.gz
- lab/reports/v09-contract/contract-v09_reflexion-off_seed-42/agentic.metrics.json
- lab/reports/v09-contract/contract-v09_reflexion-on_seed-42/agentic.events.jsonl.gz
- lab/reports/v09-contract/contract-v09_reflexion-on_seed-42/agentic.metrics.json
- lab/tasks/task_feb731c779788be5bfff65e979-v0-9/artifacts/contract-2x2-seed42.md

## Outputs

- none

## Verification

- - `PYTHONPATH=. .venv/bin/python -m pytest -q` → 当时 **152 passed**。**该数字此后一度无法复现,原因与本任务无关**:`fbfd5c6`(2026-09-13 14:41)交付 v0.7 证据包时,把 `reports/final-report-v0.7/evidence/code-v09/tests/` 下三个与 `tests/` 完全同名的文件(`test_auto_researcher_backtrack.py`、`test_auto_researcher_contract.py`、`test_reflexion.py`)带进了收集范围;两边都无 `__init__.py`,pytest 按 basename 导入撞名,把**两边**都判成 collection error,于是全量变成 4 errors 起不来,而 CI 只点名跑 8 个自包含文件,没有任何门发现它(fact `F-89963893` 那条机制的第四次发作)。已于 2026-09-14 加 `pytest.ini` 把收集范围钉在 `tests/`(证据副本是交付物,不动它),全量恢复为 **166 passed in 28.62s**。
- 新增 `tests/test_auto_researcher_contract.py` 守护测试,**四项改造各自反向验证**
  (地板开关、排除入口、提示词切换、卡片开关分别打回原状,确认对应测试变红后还原)。
  该文件当时 15 条(按 pytest 参数化计),2026-09-14 补入 `exclusion_too_strict` 的覆盖后为 **16 条**——
  独立评审指出原文件虽实现了该分支却无用例覆盖,成立。新用例钉住两件事:排除后候选不足 `n`
  的前提可被 `_exclude_motif_indices` 算出;以及若省掉那个 early return,`_compose_batch_indices`
  确实会交出一个短批次(阳性对照),因此 `auto_researcher.py:662-670` 的闸不可省。
  `_compose_batch_core` 是依赖九个自由变量的闭包,无法直接 import,故未为可测性改动生产代码。
- **对照臂在真实 LLM 跑批下逐位复现 v0.8**:`contract-v08_reflexion-off_seed-42` 六轮批次哈希
  与 v0.8 `acq-v05_reflexion-off_seed-42` 完全相同,证明改动对默认路径惰性。
- **排除的 motif 全部有据**:被 `exclude_motifs` 排除的替换 ⊆ 累积注入证据集,零凭空;
  全程卡片标记 34 个,agent 只排 20 个(有选择),排除集单调增长 0→2→4→8→13→20。
- 四臂均 288/288 花满预算、6/6 LLM 成功、0 超时、0 工具错误。
- `python3 scripts/check_references.py` → 本任务新增章节未带入死链;`REPORT-HANDOFF.md` 当时全部可达。
  **但"全仓引用全部可达"不成立,原文案偏强**:2026-09-14 实跑全仓为 **5 处失效引用**,均在本任务交付面之外——
  `lab/reports/migration-audit.md` 两处(`reports/experiment_log.jsonl`、`reports/report_standalone.html`)、
  `lab/reports/agentic-v0.1/report.md` 一处(`reports/agentic_postmortem_aav.json`)、
  `lab/reports/agentic-v0.4/report.md` 一处(`agentic-v0.4/aav/agentic.metrics.json`)、
  `lab/reports/final-report-v0.3/report.md` 一处(`figures/fig2_gb1_convergence.png`)。
  独立评审报的是 7 处并点名 `REPORT-HANDOFF.md` 的 `data/aav/full_data.csv`,与本次实跑不符(它在基准 checkout 上跑的);
  以本条的实跑清单为准,该 5 处的修复不属本任务交付面。
- 促成事实:`F-2CBCCC90`(根因)、`F-378F2B8D`(结果)。

- **交付路径与契约声明不一致(须按实际登记)**:`task_plan.md` 的 Deliverable Contract 写「数据:`tmp/v09-contract/` 四臂 metrics + 事件流」,而 `tmp/` 在本仓是 gitignored,**因此该路径在任何提交树里都不存在**,独立评审据此指出交付缺失是对的。正式产物实际落在 `lab/reports/v09-contract/` 下,四臂齐全:`contract-v08_reflexion-off_seed-42`、`contract-v08_reflexion-on_seed-42`、`contract-v09_reflexion-off_seed-42`、`contract-v09_reflexion-on_seed-42`。本 closeout 以后者为交付路径;契约里那处 `tmp/` 写法是当时的工作目录习惯,不应作为交付声明。

## Known gaps

- - **n=1(seed 42)。** 批次哈希类断言是确定性事实;行为类断言(v09 反思臂是四臂中
  唯一未触发 basin hop)是单次观察,不可信。
- **契约是复合处理**,本轮未拆开测提示词/地板/排除入口各自的贡献。不得声称
  「是排除入口起的作用」。拆分需要 2×2×2,是下一个实验。
- strong 计数差(158 / 153 / 160)只有 5–7,**不可当效应量**;峰值四臂同为池内峰 8.4162,
  「9.536 悖论」照旧成立。
- **v09 臂慢一倍**(527/573s vs 238/266s),论成本时是真实代价。
- 待裁决 `dec_016C25D18F5C1C17F9A7173E75`(「LLM 自主在优化内核是负担」)现有新证据:
  单给自主权略差(153),自主权配上证据才变好(160)。该决策的措辞可能需要重写,
  但裁决权归 CEO,本任务不代裁。
- - **同一机制在 `agent/pipeline.py` 的 workflow 线上未被检查过**:那条线没有会话连续性,
  也没有反思注入,其五个角色同样只能通过固定参数与外界交互。若要对该线下同类结论,
  必须先核它的工具契约能否承载证据,不能直接搬运本轮结论。
- **「只修一层」的模式在本仓复发过两次**:v0.8 首次 2×2 只解耦提示词层而工具层仍耦合;
  本轮的四层根因里同样有三层互相封锁。凡「策略挂在某个开关上」的地方,
  都应先 grep 该开关的全部读取点再动手。
- **「静默缩批伪装成策略变化」**与 v1.2 里 llm 档静默终止(退出码 0)是同一类缺陷:
  数量变化被读成质量变化。`exclusion_too_strict` 是对该类缺陷的针对性防护。

## Residual risks

- - **n=1(seed 42)。** 批次哈希类断言是确定性事实;行为类断言(v09 反思臂是四臂中
  唯一未触发 basin hop)是单次观察,不可信。
- **契约是复合处理**,本轮未拆开测提示词/地板/排除入口各自的贡献。不得声称
  「是排除入口起的作用」。拆分需要 2×2×2,是下一个实验。
- strong 计数差(158 / 153 / 160)只有 5–7,**不可当效应量**;峰值四臂同为池内峰 8.4162,
  「9.536 悖论」照旧成立。
- **v09 臂慢一倍**(527/573s vs 238/266s),论成本时是真实代价。
- 待裁决 `dec_016C25D18F5C1C17F9A7173E75`(「LLM 自主在优化内核是负担」)现有新证据:
  单给自主权略差(153),自主权配上证据才变好(160)。该决策的措辞可能需要重写,
  但裁决权归 CEO,本任务不代裁。
- - **同一机制在 `agent/pipeline.py` 的 workflow 线上未被检查过**:那条线没有会话连续性,
  也没有反思注入,其五个角色同样只能通过固定参数与外界交互。若要对该线下同类结论,
  必须先核它的工具契约能否承载证据,不能直接搬运本轮结论。
- **「只修一层」的模式在本仓复发过两次**:v0.8 首次 2×2 只解耦提示词层而工具层仍耦合;
  本轮的四层根因里同样有三层互相封锁。凡「策略挂在某个开关上」的地方,
  都应先 grep 该开关的全部读取点再动手。
- **「静默缩批伪装成策略变化」**与 v1.2 里 llm 档静默终止(退出码 0)是同一类缺陷:
  数量变化被读成质量变化。`exclusion_too_strict` 是对该类缺陷的针对性防护。
