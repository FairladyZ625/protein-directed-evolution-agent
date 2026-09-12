# 上报并修复 Harness 两个框架缺陷(CI 见证不可配置 / 纯文档任务 worktree 提交死锁)

Task Contract: harness-task v1

## Brief

本轮 closeout 撞上两个 Harness 框架缺陷,它们不是本仓的配置错误,而是产品缺陷——都已 ground-truth 到源码行。合计阻塞本仓约 20 个 standard-task 的正式收口。按"发现问题就改造自己的系统"的纪律,这不该靠变通绕过去,而该修掉。

## Goal

在 `harness-anything` 仓(`/Users/lizeyu/Projects/coding-agent-harness/harness-anything`)提出并落地修复,或至少提出经 CEO 认可的修复方案与对应任务:

- **缺陷 A(fact `F-8ED77039`)**:`settings.ci.workflows` 被 `SETTINGS_FIELD_OWNERSHIP` 标为 repository-owned,默认 `["rewrite-ci"]`(harness-anything 自己仓库的 workflow 名),但 `ha settings update` **没有任何写入该字段的选项**,手改 `harness.yaml` 无效(它是 canonical writer 的输出不是输入)。后果:任何 workflow 不叫 `rewrite-ci` 的仓库,ci 完成门必然 `service_rejected`(HTTP 404)。另 `repo-cell-task-progress.js:28` 把 `"rewrite-ci"` 作为字符串硬编码判定公共交付见证,即便字段可配也仍会失败。
- **缺陷 B(fact `F-B1B5EABC`)**:`deriveCloseoutSubmission` 在执行被 dispatch 绑定了 cwd 时走产品仓 diff 路径,要求 `base..commitSha` 有非空变更;而纯文档任务的产出全在 gitignored 的 `/harness/` ledger 树里,worker 的提交必然为空 → `invalid_submission` → `document_invalid`。且执行处于 `active` 时无法用 `--execution-id` 另起新执行绕开绑定,形成死锁。

## Context

- 缺陷 A 证据:`packages/cli/dist/kernel/src/domain/settings.js:8`(`DEFAULT_CI_WORKFLOWS`)、`packages/cli/dist/daemon/src/ci-observation-actions.js:11`(`workflows = cell.settings.read().ci.workflows`)、`packages/cli/dist/daemon/src/repo-cell-task-progress.js:28`(硬编码字符串)。
- 缺陷 B 证据:`packages/cli/dist/daemon/src/repo-cell-submit.js:9-88`;本仓 `.gitignore:17` 忽略整个 `/harness/`。
- 复现仓:`ai4s-directed-evolution-agent`,远端 `FairladyZ625/protein-directed-evolution-agent`,其 workflow 名为 `ci.yml`(有绿色 main 运行)。
- 顺带发现的文档腐烂:本仓 `AGENTS.md` 的治理配方写着 `ha task submit <id> --json-input @-`,而现在的 CLI 已改为从 `closeout.md` 派生完成包、`submit` 不接受 `--json-input`。配方需同步更新。

## Required Reading

1. 上述四个源码位置(**权威**:缺陷本体)。
2. `packages/cli/dist/kernel/src/domain/settings.js` 的 `SETTINGS_FIELD_OWNERSHIP` 与 `ha settings update` 的选项表(对比出缺口)。
3. 本仓 `AGENTS.md` 的「治理配方」节(需同步的文档)。

## Entry Conditions

能在 harness-anything 仓正常工作(该仓有自己的治理与 CI,遵其规矩);能复现两个缺陷。复现不了先报。

## Dependencies

上游:本轮 closeout 的实测证据(facts F-8ED77039 / F-B1B5EABC)。下游:本仓全部 standard-task 的正式收口、纯文档任务 e2eab881 与 8e29be09 的提交。并发:无。

## Execution Surface

主要在 `/Users/lizeyu/Projects/coding-agent-harness/harness-anything`(独立 worktree,按该仓规矩);本仓内只允许更新 `AGENTS.md` 的治理配方节。禁区:本仓产品代码与 report;harness-anything 的 protected surface 按该仓规则走。

## Constraints

- **不得为了绕过而在本仓新建名为 `rewrite-ci` 的 workflow**——那是给公开笔试交付仓塞一个语义错误的文件,拿可读性换便利,不做。
- 不得削门、不得 `transition --force`、不得改本仓 CI 配置。
- 修改 `dist/` 不算修复;要改源码并按该仓流程走。

## Checkpoint

拿出修复方案(两个缺陷各一段:改哪、为什么、影响面)即停并报 CEO 裁定,之后再动手。**异议型停**:若判断某个缺陷其实是设计意图而非缺陷,带论证来谈。

## CI/Gate Authority Stop Condition

**本任务就是治理/CI 面任务**,是允许触碰 CI 与门禁授权面的例外。但仍须:改动落决策台账、留任务痕迹、不降低任何既有门的强度。

## Implementation Plan

- 缺陷 A:给 `ha settings update` 增加 ci workflows 的写入选项(或等价的 canonical 写路径);把 `repo-cell-task-progress.js` 的硬编码换成读配置。
- 缺陷 B:让 dispatch-bound 执行在产品仓 diff 为空时回落到 privateDelivery 路径(ledger 的 artifacts 检查),或提供显式的 `--private-delivery` 声明。
- 同步更新本仓 `AGENTS.md` 治理配方(submit 已不接受 `--json-input`)。
- `ha fact record --task task_7994263c6be22e8690ec8d5950` 记修复结论。

## Deliverable Contract

修复 PR(或经 CEO 认可的方案文档 + harness-anything 侧任务)+ 本仓 `AGENTS.md` 配方更新;≥1 fact;回报两个缺陷各自的处置与本仓能否随之解锁。

## Evidence Protocol

每条断言给源码行;"修好了"必须有本仓一次真实 `ha task complete` 成功作为验证,不接受单测绿代替。

## Verification

停手点 = 方案经 CEO 认可(或修复合入)+ 本仓至少一个 standard-task 能走完 complete + ≥1 fact。
