# 收口已完成的 harness 任务:零门任务销账 + 4 个 in_review 独立评审

Task Contract: harness-task v1

## Brief

把"实质已完成、但生命周期状态没销"的任务走完门链:6 个零门 docs-task 收到终态,4 个 in_review 任务做独立评审。standard-task(ci + code-doc-reconciliation 双门)那一批**不在本次范围**——它们的 ci 门当前被 origin/main 上一次红的 CI run 卡住,修法涉及 CI 配置,属 CEO 裁定面。

## Goal

A 组 6 个任务各自到达 **submitted** 状态,或给出带证据的打回理由(打回=不 submit,并说明缺什么)。交付物=一份提交结果清单,通过 `ha task progress append` 落在本任务上。第一个读者是 CEO,他据此派独立评审收尾。

**A 组 · 零门 docs-task(completionGates=[]),closeout 已写实,可直接走门链:**

| task id | 标题要点 |
|---|---|
| task_ed9e41ef27c8fb94e8a99062a8 | 调研更难的定向进化基准数据集 |
| task_d3dfe26bf702928b1c3784e60f | Research:平台期破局手段 |
| task_8e29be09414b0c5d7eac95db08 | 知识库迭代研究(BLOSUM62 二元门禁→更丰富先验) |
| task_e2eab881832291e8f8f73f30a4 | V0.6 对抗分析(LLM 停滞机制 / backtrack) |
| task_d5e9455a1235d1554b1967c708 | 试题逐条覆盖度审计 |
| task_7994263c6be22e8690ec8d5950 | 上报并修复 Harness 两个框架缺陷 |

`task_7994263c…` 的 closeout 仍是脚手架占位符,且它的主题(CI 见证不可配置)**上游已修掉**(见 Context),所以它需要先按现状写实 closeout 再收;若你判断它应改为 supersede 而非 complete,把理由报回,不要自行 supersede。

**B 组 · in_review,需要独立 review-execution + review-consent:**

| task id | 标题要点 | 注意 |
|---|---|---|
| task_2e485a1ae862bdec5fcc7c9677 | agentic v0.6 元层 backtrack | 包内已有 `reviews/rev-de-reviewer-v06-20260912.md`,先读它,别重复评审 |
| task_6a18b55b9ee78b0609b7290f85 | 合并 v0.6 backtrack 进主线 | 交付 sha 80c9bce7 |
| task_f50ce371b24c0c4396c76f8a4a | T2 数据管线+特征 | closeout 有一处锚点更正(曾被打回),核实更正后的锚点 149f69be 是否真含契约面 |
| task_feb731c779788be5bfff65e979 | v0.9 工具契约改造 | **无 dispatch 记录**,execution 由 CEO 提交;你评审它是合法的独立评审 |

B 组四个都是 standard-task 双门。它们的独立评审由 CEO 另派身份处理(一个被审任务派一次),**不在本次范围**;且即便评审通过,`complete` 仍会被 `ci` 门拒(原因见 Context)。你对 B 组只做状态核实,不做任何写入。

## 身份分工(本次派工的硬边界)

本次派工**只做提交侧**:A 组的 lease 接回 + closeout 核实 + submit。

**不要执行任何 `review-execution` / `review-consent` / `complete`。** 自己提交的 execution 由自己评审返回 `actor_unauthorized`;而按本仓实测(`AGENTS.md` 坑 #2),用"一个身份统管提交与评审"的形态派工,worker 会把活全干完、直到写入时才报 `executor_binding_invalid`,**整轮作废**。评审侧由 CEO 另派独立身份,一个被审任务派一次。

B 组四个 in_review 任务**也不在本次范围**(它们只缺独立评审)。你只需核实它们当前确实停在 review 节点并把结论写进报告。

## Context

- **`ci` 完成门的真实判据**(已 ground-truth,别再从记忆里取):见证事件要求 `summary.headBranch === "main"` 且 `artifact.run.branch === "main"` 且 sha/runId 对齐(`packages/cli/dist/daemon/src/ci-observation-actions.js:41,172-178`);随后 `judgeCompletionEvidence` 收尾是 `accepted: evidence.result === "pass"`,`fail` 明确以 "checker reported fail" 拒(`packages/cli/dist/kernel/src/domain/completion-evidence.js`)。**所以 ci 门要求 main 分支上一次绿的 run,不是"有见证记录"就行。**
- **fact `F-8ED77039` 描述的框架缺陷已被上游修掉**:`rewrite-ci` 在整个 CLI dist 里 grep 零命中,`DEFAULT_CI_WORKFLOWS` 现在是 `[]`,本仓 `harness.yaml` 的 `settings.ci.workflows` 已是 `[ci]`,`.github/workflows/ci.yml` 的 `name: ci` 与文件名 stem 一致。**现在卡住 ci 门的不再是框架,而是一次红的 run**:`origin/main` HEAD `af60187` 的 CI run 失败,原因是 CI 那一步手写依赖清单缺 `xgboost`,`tests/test_predictor.py` 两条 ImportError。本地装了 `xgboost==3.4.1` 时该文件 6 passed(阳性对照已做)。修 CI 属 CEO 面,不在本任务范围。
- B 组四个交付 sha(`471536b1` / `80c9bce7` / `149f69be` / `35915419`)均已 ground-truth 确认在 `origin/main` 上,所以"交付未落 main"不是阻塞项。
- **零门的含义**:`completionGates=[]` ⇒ 不需要 `code-doc reconcile` 见证、不需要 fact。但生命周期顺序仍然是 start → submit → 独立 review-execution → review-consent → complete;自审返回 `actor_unauthorized`。
- WIP 上限 30,当前 active 25 —— 逐个收、别一次 start 一大批把自己顶到上限。

## Required Reading

按序:
1. `AGENTS.md` 的「治理配方」节 —— 配方 3(closeout)是本任务的主线命令序列;注意它自己标注的四个实测坑(lease 接回、评审独立性、纯文档任务 worktree 死锁、ci 门)。**权威级别最高**,与本 plan 冲突时以本 plan 的 Context 为准(因为上游刚改过)。
2. 每个待收任务自己的 `closeout.md` 与 `task_plan.md`(在其包目录内)。
3. `lab/context/development/ai4s-worker-handbook.md` —— 仓库口径与数据事实。

## Entry Conditions

- A 组 6 个 + B 组 4 个已逐个 `ha task start --dry-run` 探过:A 组全部 `admissible=true`;`task_feb731c7…` 返回 `invalid_transition`(已在 review 节点、无活跃 lease),说明它不需要也不能重新 start,直接走 review-execution。
- 不需要网络、不需要下数据、不需要跑实验。

## Dependencies

- 无上游依赖。
- 下游:CI 修绿后,B 组的 complete 与 standard-task 那一批的收口由 CEO 另行安排。

## Execution Surface

- 仓库:`/Users/lizeyu/Projects/ai4s-directed-evolution-agent`,直接在仓库根工作。
- **不要建 worktree**:本任务产出全在 `harness/` 台账内,纯文档任务绑 worktree 会造成空交付提交死锁(fact `F-B1B5EABC`)。
- 写入面:只通过 `ha` 命令写台账;`lab/tasks/<待收任务>/closeout.md` 在需要写实时可直接编辑(它是脚手架文件)。

## Constraints

- **绝不 `git commit` / `git add` `harness/` 下任何文件**——该目录由 daemon 单写,自提交会破坏台账。你的产出靠 `ha` 命令落库。
- 禁止 `ha task transition --force`、禁止削门、禁止新建或修改任何 CI workflow、禁止改 `harness.yaml`。
- 禁止自审:你提交的 execution 不能由你 review。A 组任务若 execution 的 executor 就是你这次的身份,报回让 CEO 换人评审。
- `task_ee0e0b26e540664dac1e6c3f29` 是 milestone 类,**不在范围**(milestone 收口归 CEO)。
- `task_5455e0628aa237d1553e69befb` closeout 仍是占位符且父任务已 done,**不在范围**,只需在报告里提一句这处漂移。
- 不放宽验收标准:closeout 四小节(`## Summary` / `## Verification` / `## Residual Risk` / `## Same Mechanism Elsewhere`)必须写实才可 submit。

## Checkpoint

命中即停并上报:
- 同一个错误码(`service_rejected` / `invalid_transition` / `actor_unauthorized` / `closeout_placeholder`)在同一任务上连续出现两次且你不知道为什么;
- 需要改 CI、门禁配置或 `harness.yaml` 才能推进;
- 发现某个任务的 closeout 与仓库现状不符(即它实质没做完)——这类要打回,不要替它补内容再收;
- 任何需要 `--force` 的念头出现时。

计划性回报点:A 组做完后先 `ha task progress append` 报一次中间结果,再动 B 组。

## CI/Gate Authority Stop Condition

本任务不是 CI/gate/governance 任务。如果推进需要修改 CI 或门禁权威面,停止实现、记录 blocker、报回 CEO。不得以"为了让门过"为理由改动任何门禁配置。

## Implementation Plan

对 A 组每个任务,逐个(不要批量并发):
1. `ha task start <id> --dry-run` 取回 `executionId`;
2. `ha task start <id> --execution-id <exe_id>` 接回该执行(坑 #1:worker 跑完后执行留在 active 且无 lease,必须带 `--execution-id` 接回,否则报 `lease_conflict`);
3. 读 `closeout.md`,核四小节是否写实,并**抽查至少一条它的断言**(它声称的产物文件是否真存在、行数/数字是否对得上、若有 40 位 sha 则 `git merge-base --is-ancestor <sha> origin/main`);
4. 断言不成立 ⇒ **不要替它补内容**,记为打回并写清缺什么;
5. 断言成立 ⇒ `ha task submit <id>`;
6. `ha task show <id>` 核实已进 review 节点 —— **回执不是证据,projection 才是**;
7. 若 submit 被 `closeout_placeholder` 拒(预期只会发生在 `task_7994263c…`),按仓库现状写实那四小节再 submit;它的主题(CI 见证不可配置)上游已修掉,写实时必须反映这一点,不要照抄旧结论。

B 组:只做第 6 步式的状态核实,不做任何写入。

## Deliverable Contract

- 形态:`ha task progress append task_8cca79cbf42be758e0610e04d3 --text "<收口结果清单>"`,可分多次 append。
- 内容:每个任务一行 —— task id / 结果(submitted / 打回) / 依据(命令 + 关键回显) / 抽查了它哪一条断言、怎么验的 / 若打回则缺什么。另附 B 组四个任务的当前节点核实结果。
- 交给谁:CEO。放哪:本任务的 progress。

## Evidence Protocol

- 每个状态变更后用 `ha task show <id>` 复核 projection,不以命令退出码为准。
- 声称"closeout 写实"前,至少抽查一条它的断言(产物文件存在 / 测试文件存在 / sha 在 origin/main 上:`git merge-base --is-ancestor <sha> origin/main`)。
- 最终用 `ha task list --status in_review --limit 500` 和 `--status active --limit 500` 给出收口前后的对比计数。
- 没验证的断言一律标 `unverified`。

## Verification

- A 组 6 个:`ha task show <id>` 显示已离开 implementation 节点进入 review(或带证据的打回记录)。
- B 组 4 个:确认仍停在 review 节点,未被本次派工改动。
- `git status --porcelain harness/` 不得出现由你手工 `git add`/`git commit` 造成的变化(daemon 自己的写入不算)。
- 报告里每条断言标明是实测还是推断;没验证的标 `unverified`。
