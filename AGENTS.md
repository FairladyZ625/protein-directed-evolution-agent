# Harness Agent Entry

This file contains stable repository operating rules. Current milestone state and task-specific context belong in the active task package.

## Context Loading

- Read `harness/harness.yaml`.
- When a task is assigned, read its `task_plan.md` and only the files it names.
- Route from the task to the smallest relevant context or standard document; do not preload the whole authored tree.

## Worktree Discipline

- Use an isolated worktree and task branch for implementation work.
- Preserve unrelated changes in every checkout and stage only task-owned paths.
- Follow the task's declared base, merge, cleanup, and publication instructions.

## Kernel Workflow

- A task is the work unit and status timeline.
- A fact is an explicit, append-only promotion of a load-bearing observation; the default `code-doc-reconciliation` completion gate requires at least one fact and rejects its absence with `fact_missing`.
- A decision records the load-bearing why: choices, reversals, long-lived boundaries, and downstream work-spawning judgments.
- Prose mentions do not replace canonical facts, decisions, or relations.

## Relation Rules

- Write relations with canonical IDs.
- Use `derives` when a decision directly spawned a task and `relates` when a connection was identified later.
- Use `refines` only for decision-to-decision revision.

## Write Coordination

- Use Harness commands for machine-read fields, lifecycle changes, and relations.
- Follow repository doc-sync policy for registered authored prose; `ha doc sync --submit --path` resolves paths from the configured authored root (normally `harness/`) and rejects repository-root-prefixed paths with `document_not_found`.
- Generated state under `.harness/` is local-only and must not be committed.

## Harness CLI (software/coding)

- Use `ha <command>` or `npx harness-anything <command>` and inspect command help before composing writes.
- Create task packages with `ha task create --title "<title>"`; do not hand-scaffold task directories, and replace every required `task_plan.md` placeholder before dispatch or `runtime run` rejects it with `plan_placeholder`.
- Select from the effective catalog with `ha preset list`. Packages reported unavailable must not be used to publish guidance or create a task.
- Milestone creation requires an explicit `--task-class milestone`; the preset ID does not infer task class.
- Both `--opt value` and `--opt=value` are accepted for value options; an unsupported option is rejected with `unknown_field`.
- `runtime run --mission` takes a synced mission name, not a file path; submit the mission with `ha doc sync --submit` first or dispatch rejects it with `mission_not_found`.
- Closeout order is start → submit → independent `review-execution` → `review-consent` → complete; an out-of-order lifecycle action is `invalid_transition`, and self-review is `actor_unauthorized`.
- `ha task complete --path` resolves paths from the project repository root and rejects paths absent from the submitted commit with `invalid_proof`.
- Before completion, replace `closeout.md` with the exact sections `## Summary`, `## Verification`, `## Residual Risk`, and `## Same Mechanism Elsewhere`, or completion rejects it with `closeout_placeholder`.

## Repository Scaffolds

- Context lives under `harness/context/`.
- Standards live only under `harness/governance/standards/`.
- Artifact source documents are located through generic entity descriptors; milestone documents and canonical decision packages remain under the configured authored root.
- Read each folder's README instead of duplicating its rules here.

## Architecture-aware Changes

- Before broad source search, check for `harness/context/architecture/architecture-manifest.json`.
- If present, read the architecture README and only the relevant stable view or flow before choosing an implementation layer.
- If absent, architecture remains opt-in and ordinary coding work continues without a fabricated model.

## Governance Routing

- Repository workflow and preservation: `harness/governance/standards/repository-governance.md`.
- Decision writing: `harness/governance/standards/decision-writing.md`.
- Load only standards applicable to the current task.

## Script Discovery

- Use `ha script list` and `ha script inspect <id>` to inspect vertical script declarations.
- A declaration is not proof of execution support. Run a script only when inspection explicitly reports execution as available.

## 生命周期纪律(2026-09-14 立,针对 23 个在飞任务积压的根因)

在飞线一度积压 23 个 `status=active` 的任务,其中 **17 个 Iteration 0**——产物早已落进仓库,
但 `ha task start` / `submit` 压根没跑过。根因不是评审太严,是**开工与销账两头都没挂进生命周期**。

**先记一条会误导人的机制**:`ha agenda` 的在飞线只看 `status`,**不看 `packageDisposition`**。
实测 23 条里已有 8 条是 `archived` 却仍在在飞线;而不带 `--json` 的 `ha task show`
只打印三行、**不显示 disposition**。所以「归档」不会让任务离开在飞线——
要离开只有走完礼到 `done`,或 `ha task transition <id> cancelled`。

- **开工即 `start`**:动手写第一行产物之前先 `ha task start <id>` 拿租约。事后补不回来——
  执行记录只从 `closeout.md` 派生,而 lease 释放后 `progress append` 没有恢复路径。
- **产物落盘当天就 `submit`**:不要等"做得更完整些"。`submit` 之后仍可 `--amend`,
  但没 submit 就没有可评审对象,任务会无声停在 active。
- **一个被审任务派一次评审**:`ha agent run de-reviewer --task <被审任务> --instance <inst>
  --role reviewer --cwd <仓库根> --detach`。用「一个评审任务统管 N 个被审任务」的形态派工,
  worker 会把活全干完、写入时才报 `executor_binding_invalid`,整轮作废。
- **走完 consent 才算完**:`review-execution` → `review-consent` → `complete`。停在
  `review-execution` 之后 = 前面几轮评审的成本全部沉没(本次归档的 5 个 Iteration 2 就是这样)。
- **积压上限**:`ha agenda` 的在飞线超过 8 条就停止开新任务,先收口。23 条时单个任务的
  关闭成本已经高到只能批量归档——那等于承认前面的流程记录作废。

## Repository Specifics

Repository-specific rules may be added here after explicit diagnosis; the deterministic base and vertical overlay above remain unchanged.

## 治理配方(本仓实测·抄命令别撞墙)

Fact → Decision → Task 是一个闭环:**观察**促成 **Fact**,Fact 催生 **Decision**(裁定),Decision 派生 **Task**(工作),Task 完成又产出新 **Fact**。下面是每个动作的确切命令序列 + 已踩过的坑,照抄即可,别再逐个报错反向发现。

**通用坑**:
- `decisions/`、`tasks/`、`entities/` 下的 .md 由 daemon 管理(gitignore),**别直接编辑**,一律走 `ha ... amend/--body-file`;`--body-file` 的文件**必须在仓库根内**(scratchpad 在外会被拒)。
- 提交类 packet 的多值字段(verificationNotes/deliverables/…)**是数组**,不是字符串。
- 关系必须是**已声明的三元组**;`relation_triple_undeclared` 时别硬试,先看下面已知可用的三元组。

### 配方 1:记录 Fact
```
ha fact record --statement "<观察>" --source "<证据路径>" --confidence high [--task <task-id>]
```
带 `--task` 会自动建 `task --produces--> fact`(满足任务完成门的 fact 要求)。`ha fact` **没有 list 命令**。

### 配方 2:建决策并让它可被接受(接受由他人/GUI 做,自己不能自审)
```
# ① 提议(chosen/rejected/claims 必填;rejected 每条必带 whyNot)
ha decision propose --json-input @- <<'J'
{"title":"…","question":"…","riskTier":"low","urgency":"medium","decisionClass":"ordinary",
 "chosen":[{"id":"CH1","text":"…","rationale":"…"}],
 "rejected":[{"id":"RJ1","text":"…","whyNot":"…"}],
 "claims":[{"id":"C1","loadBearing":true,"text":"…"}]}
J
# ② 填 body(否则 accept 报 body_placeholder)——四小节
printf '## 背景\n…\n## 裁定\n…\n## 影响\n…\n' > .body.md
ha decision amend <id> --body-file .body.md && rm .body.md
# ③ 让 load-bearing claim 被证据覆盖(否则 accept 报 coverageRows 0/N):两步,缺一不可
ha fact record --statement "<支撑该claim的实测观察>" --source "…" --confidence high   # 得到 F-xxxx
ha relation relate --source-ref decision/<id>/C1 --target-ref fact/F-xxxx --type evidenced-by --rationale "…" --expected-version 0
ha decision claim fulfill <id> --id C1 --mode evidenced
# ④ 校验干净后交 GUI/他人 accept(applies_to 空只是软警告,不阻塞)
ha decision validate <id>
```
> 若无实测证据,accept 可走 `--judgment-only "<理由>"` 兜底(样板决策即如此),但有证据优先。

### 配方 3:closeout 一个任务(2026-09-12 实测重写)
```
ha task start <id>                       # 先拿 lease,否则 submit 报 lease_required
# 写 closeout.md 四个精确小节(占位符未替换则报 closeout_placeholder):
#   ## Summary / ## Verification / ## Residual Risk / ## Same Mechanism Elsewhere
ha task submit <id>                      # 完成包从 closeout.md 派生,不接受 --json-input
ha task review-execution <id> --review-id <rev-id> --json-input @- <<'J'
{"verdict":"approved","reason":"…","evidenceChecked":["…"]}
J
ha task review-consent <id> --review-id <rev-id>
ha task complete <id>
```
**`ha task submit` 早已不接受 `--json-input`**(旧配方里那个 JSON 完成包是过期写法,会报 `unknown_field`)。完成包现在**全部从 `closeout.md` 正文派生**:交付提交由"Summary 里出现的 40 位 sha"或"该执行 dispatch 绑定的 worktree HEAD"决定,deliverables 由 `base..commitSha` 的 diff 自动算出。任务仍需 ≥1 个 fact(配方 1 带 `--task`)。

**四个实测坑**:
1. **lease 接回**:worker 跑完后执行留在 active、无 lease,`ha task start <id>` 报 `lease_conflict` 或 `progress append` 报 `progress_lease_required` —— 用 `ha task start <id> --execution-id <exe_…>` 接回那个执行。反过来,执行处于 active 时用**新的** execution-id 起一个执行会被拒(`invalid_transition`)。
2. **评审独立性**:自己提交的执行不能自审(`actor_unauthorized`)。派 reviewer 必须**一个被审任务派一次**:`ha agent run de-reviewer --task <被审任务> --instance <inst> --role reviewer --cwd <仓库根> --detach`(2026-09-14 实测:旧写法 `ha runtime run <inst> --agent …` 已被 `error code=invalid_field` 拒,CLI 自述 hint 为「Use ha agent run <agent-id> --task <task-id> for task-bound work」;派工回执形如 `runtime-run: detached dispatch_… ; next: ha runtime status runtime_… --wait`)。用"一个评审任务统管 N 个被审任务"的形态派工,worker 会把活全干完但写入时才报 `executor_binding_invalid`,整轮作废。
3. **纯文档任务 + worktree = 提交死锁**(fact `F-B1B5EABC`):产出全在 gitignored 的 `/harness/` 里 → worker 的交付提交是空提交 → `document_invalid`。未绑 worktree 的同类任务走 privateDelivery 路径可正常提交。
4. **ci 完成门的真实判据**(fact `F-B0148E72`;2026-09-14 实测更正):见证只为 **`headBranch=='main'` 且 `status=='completed'`** 的运行发布,并要求 `workflowName` 落在 `settings.ci.workflows` 里——本仓 `harness.yaml:13-14` 配的是 `workflows: [ci]`。**见证与被审任务自己的 commit 无关**:它取 main 上的 `ci` 运行,所以只要 main 的 `ci` 是绿的,`complete` 会自行铸出 `Checker witnesses: ci/op_…`。2026-09-14 有两个任务据此真过了门(`task_2e485a1ae…`、`task_6a18b55b9…`,均为 approved → consent → complete)。
   **原写「standard-task 的 ci 门结构性不可满足(`rewrite-ci.yml` HTTP 404),`submit`/`complete` 必返 `service_rejected`」已作废**——`rewrite-ci` 在全局 CLI dist 里 `grep` **零命中**,该上游缺陷已修(见 `task_8cca79cbf…/task_plan.md:48`);那个 404 是拿错 workflow 名(`rewrite-ci.yml` 而非配置里的 `ci`)的历史状态。**照旧条推断会得出错误结论,2026-09-14 本会话即因此误判两次。**
   仍然有效的红线不变:**不得**新建 workflow、改 CI 配置或 `transition --force`;门真红时记录进度后停手,交 CEO。

### 配方 4:把报告/工件登记为实体并挂到任务
```
ha vertical entity-kind upsert --from-file kind.json      # 声明种类(minimal:id/entityType/idPrefix/display/descriptorSchemaRef/store/locatorKinds)
ha entity import --kind <kind> --locator <路径> --expected-version 0 --title "…"   # locator 可是文件或整文件夹(整树 SHA256)
# 若要 <kind> --relates--> task:该三元组要先在 kind 的 relations 里声明,且每条 relation 需 decisionClaimRef+decisionContentPin(先有决策授权)
```

### 已知可用的关系三元组(省得猜)
- `task --produces--> fact`(记 fact 带 --task 时自动生成)
- `decision/<claim> --evidenced-by--> fact`(给 claim 挂证据)
- `<artifact-kind>/<ENTITY> --relates--> task`(需 kind 预声明该三元组)
- 遇 `relation_triple_undeclared`:该 (source-kind,type,target-kind) 没声明,换方向或先在 kind 上声明,别穷举 type。
