# 独立评审并完成 baseline milestone 的 10 个 in_review 任务

Task Contract: harness-task v1

## Brief

作为独立评审(与提交者 claude-session 不同 actor),真审并 review-consent→complete 掉 baseline milestone 的 10 个已 submit 的 in_review 任务。

## Goal

10 个任务全部走完 review-execution → review-consent → complete 到达 `done`;对每个任务先按 ground truth 核实其 closeout 真实成立,再同意。产出:一份评审小结(每任务一行:通过/打回 + 依据),落在本任务 artifacts/review-summary.md;任何 closeout 不成立的任务**打回不 complete**,并记录原因。收件人:CEO(claude-session)与泽宇。

## Context

CEO(claude-session)本轮把 baseline milestone 的 T2–T8、调研、ESM+avGFP 基础设施、agentic 共 10 个任务 start+submit 到 in_review,每个都写了 closeout.md(四小节)+ 完成包 + 至少一条 fact。因 Harness GUI 目前没有人工 Task review 入口(见仓库根 HARNESS-UX-FEEDBACK.md),且 self-review 被 `actor_unauthorized` 拒,故派你(de-reviewer,codex 不同 actor)代为独立评审。区分三原语:task=做了什么,fact=观察到什么,decision=为什么。

待评审的 10 个任务:
- task_41142b2ccb60a72acfe70d133a(agentic:真自主SOL agent,诚实输greedy)
- task_f50ce371b24c0c4396c76f8a4a(T2 数据管线+特征)
- task_84fd80d36f4b5a871d7478a8ff(T3 预测器阶梯)
- task_823620225b20cdb87c7ddbd1bd(T4 事件流内核)
- task_cea947b5025412586587d1e4b1(T5 知识库)
- task_d72b24d5452f2e96e6a94769b1(T6 五角色Agent)
- task_afc2590161f244b08a0ce9216e(T7 campaign引擎)
- task_17056dd3fd8bb06bd69b91d499(T8 Streamlit demo)
- task_ed9e41ef27c8fb94e8a99062a8(调研更难数据集)
- task_507fa9a9996a458a5b0abfe0d5(ESM+avGFP 基础设施,注:avGFP完整跑分诚实延到优化阶段)

## Required Reading

1. `AGENTS.md` 的「治理配方」节(权威:命令序列与坑)。
2. 每个任务的 `harness/tasks/<task-dir>/closeout.md`(权威:该任务完成断言)。
3. `ha task show <id>`(权威:已 submit 的完成包 completionClaim/deliverables/outputs/…)。
4. 交付物真源:各任务 deliverables 指向的代码/产物路径(用 ls/grep 核实存在)。

## Entry Conditions

10 个任务均处于 `in_review`(已 submit)。若某任务不在 in_review,跳过并在小结记明。

## Dependencies

上游:CEO 已 submit 各任务(完成包 + closeout.md 就位)。无并发写同一任务。下游:任务转 done 后 CEO 据此宣告 baseline milestone 收口。

## Execution Surface

仓库根(dispatcher 注入绝对 cwd);只读代码/产物 + 通过 `ha` 写任务生命周期。不改任何源码、不动 reports 产物、不碰其他任务文件面。

## Constraints

- **真审,不橡皮图章**:每个任务先 ground-truth(ls/grep 交付物存在、fact 存在、closeout 四小节齐全、断言与产物一致),成立才 consent。
- 不成立的任务**不要 complete**,用 `ha task transition <id> active --reason "打回:<原因>"` 或在小结记录打回,交回 CEO。
- 不改源码、不做外部/破坏性动作。
- `complete` 若因 closeout.md 是 daemon 管理(gitignore)而报 invalid_proof/路径问题,**停下记录到小结**(这是新的 Harness 缺陷证据),不要强解。

## Checkpoint

- 跑通**第一个**任务的完整 review-execution→review-consent→complete 后**先停下报一次**:贴命令与结果,确认生命周期走得通,再批量做其余 9 个。
- 遇任何 complete 门(fact-holds / --path / ci)拦截,停下报 CEO,不自行削门。

## CI/Gate Authority Stop Condition

本任务不修改任何 CI/gate/治理授权面。若 complete 需要触碰门禁配置,停下记录 blocker 并请 CEO 裁决。

## Implementation Plan

- **review 的 JSON schema 不是 submit 那套!** 正确 schema:`{"verdict":"approved|changes_requested|dismissed","reason":"<ground-truth核实结论>","evidenceChecked":["<路径/测试/fact>"]}`。verdict 必须是 approved 才能过。
- 逐任务确切命令(照抄):
  ```
  ha task show <id>                     # 取 execution-id(exe_...)与完成包供核实
  # ground-truth:ls/grep deliverables 存在、closeout 四段齐、fact 存在
  ha task review-execution <id> --review-id rev-<短id> --json-input @- <<'J'
  {"verdict":"approved","reason":"<核实结论>","evidenceChecked":["<证据1>","<证据2>"]}
  J
  ha task review-consent <id> --review-id rev-<短id> --consent-id con-<短id> --json-input @- <<'J'
  {"verdict":"approved","reason":"同意完成","evidenceChecked":["<证据>"]}
  J
  ha task complete <id> --execution-id <exe_从 ha task show 或 review_missing 提示取>
  ```
- 若某命令报 invalid_command,**读错误提示里列出的字段要求**照改(schema 以 CLI 报错为准,别硬套)。complete 若报 invalid_proof/路径门(closeout.md 是 gitignore),停下记到小结,别强解。
- 每完成一个,`ha task progress append <此任务id> --text "..." --evidence task:<被审id>:通过/打回`。
- 全部做完,把每任务一行的结果写进 `artifacts/review-summary.md`。
- 用 `ha fact record --task <此任务id>` 记一条承重观察(如"10 个 baseline 任务独立评审通过并 complete,milestone 收口"或实际结果)。

## Deliverable Contract

- 10 个任务各自到达 `done`(或被打回并记录原因)。
- `artifacts/review-summary.md`:每任务一行(id + 通过/打回 + ground-truth 依据 + complete 结果)。
- 本任务至少一条 `ha fact record --task task_195067be4dc452a5b1b050c1dd ...` 记评审结论。
- 形态:Harness 任务生命周期状态变更 + 一份 markdown 小结;收件人 CEO 与泽宇。

## Evidence Protocol

- 每任务核实证据:`ls`/`grep` 确认 deliverables 路径存在;`ha task show <id>` 取完成包;确认 closeout.md 四小节齐全;确认该任务有 ≥1 fact(produces 关系)。
- 每步用 `ha task progress append task_195067be4dc452a5b1b050c1dd --text "..." --evidence task:<被审id>:结果` 留痕。
- 断言与产物不一致 = 打回,不 consent。

## Verification

- 通过判据:被审任务 state=`done`,且其 deliverables 经 ls/grep 实证存在、fact 存在、closeout 四小节齐全、completionClaim 与产物一致。
- 收尾自检:`ha task list --status in_review` 应不再含这 10 个(除被打回者);review-summary.md 行数 = 处理任务数。
- 第一个任务走通后先停报 CEO(见 Checkpoint),确认生命周期可行再批量。

---

## 本轮范围更新(2026-09-12,CEO 重新下发)

CEO 本轮已亲自完成能做的部分,你的范围缩小为下面 8 个——它们的 submit actor 与 CEO 同一身份,`review-execution` 被 `actor_unauthorized` 拒,必须由你(不同 actor)来做。

**你要评审的 8 个**:
1. `task_84fd80d36f4b5a871d7478a8ff` T3 预测模型阶梯+指标表
2. `task_823620225b20cdb87c7ddbd1bd` T4 事件流内核
3. `task_cea947b5025412586587d1e4b1` T5 知识库/规则库
4. `task_d72b24d5452f2e96e6a94769b1` T6 五角色 Agent 流水线
5. `task_afc2590161f244b08a0ce9216e` T7 campaign 对比引擎
6. `task_17056dd3fd8bb06bd69b91d499` T8 Streamlit 看板+demo
7. `task_507fa9a9996a458a5b0abfe0d5` 更难数据集接入(ESM+avGFP)
8. `task_ed9e41ef27c8fb94e8a99062a8` 调研更难的定向进化基准数据集

**CEO 已自行处理、你不要碰**:`task_41142b2ccb60a72acfe70d133a`、`task_f50ce371b24c0c4396c76f8a4a`、`T1-random-baseline`(均已 review+consent 完毕)。

### 已知阻塞(先读,别浪费轮次去撞)

上面第 1–7 个是 `standard-task` preset,`completionGates` 含 `ci`。本仓的 CI 见证**结构性不可满足**,`ha task complete` 必然返回:

```
error code=service_rejected hint=Command failed: gh run list --workflow rewrite-ci.yml ... HTTP 404
```

根因(CEO 已 ground-truth,勿重复调查):`packages/cli/dist/kernel/src/domain/settings.js` 的 `DEFAULT_CI_WORKFLOWS = ["rewrite-ci"]` 是 harness-anything 自己仓库的 workflow 名;`ci` 是 repository-owned settings 字段,但 `ha settings update` **没有任何写入该字段的选项**,手改 `harness.yaml` 无效(该文件是 canonical writer 的产物,不是输入)。

因此:
- 第 1–7 个 **只做到 `review-execution` + `review-consent` 为止**,`complete` 预期失败,失败即记录、不要尝试任何绕门(不得 `transition --force`、不得新建 workflow、不得改 CI 配置)。
- 第 8 个是 `docs-task`(`completionGates` 为空),**应当能一路 complete 到 `done`**,请走完整链路。

### 评审质量要求(不变,且是本轮重点)

不橡皮图章。每个任务先 ground-truth:`ls`/`grep` 确认 deliverables 真实存在、fact 存在、closeout.md 四小节齐全、completionClaim 与产物一致。断言与产物不一致就 `changes_requested`,写清哪一条对不上。

**评审时必须带上的时效背景**(这些任务写于 v0.1–v0.4 叙事之下,此后结论被推翻了四次):最终定性以 fact `F-885537A3` 为准——两个目标两套相反策略,纯利用/greedy 赢"大量强变体"(strong=166),重不确定性探索 UCB β=3 赢"单个全局峰"(30/30 达峰 8.4162),LLM 自主决策两个都没匹配上。若某任务的 closeout 里写着"greedy 直达真峰 8.416"这类旧结论,**不要因此打回**(它在当时是按当时证据写的),但要在 `reason` 里明确标注"该结论已被 F-885537A3 取代",让台账自带时效。

### 交付

- `artifacts/review-summary.md`:8 行,每行 = 任务 id + verdict + ground-truth 依据 + complete 结果(done / CI 门阻塞)。
- ≥1 条 `ha fact record --task task_195067be4dc452a5b1b050c1dd`。
- 回报:通过几个 / 打回几个 / 哪些卡在 CI 门。
