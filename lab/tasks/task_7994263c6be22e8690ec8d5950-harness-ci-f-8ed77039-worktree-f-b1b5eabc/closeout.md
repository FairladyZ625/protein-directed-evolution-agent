# Closeout

## Summary

本任务上报的两个 Harness 框架缺陷**均已在上游 `harness-anything` 修复**,本仓已逐条实测确认;修复由上游完成,本任务的贡献是把两个缺陷 ground-truth 到源码行并促成修复。

- **缺陷 A(`F-8ED77039`,CI 见证不可配置)**:`settings.ci.workflows` 现在有了写入入口——`ha settings update` 多出 `--ci-workflows` 选项;`DEFAULT_CI_WORKFLOWS` 由 `['rewrite-ci']` 改为 `Object.freeze([])`;`rewrite-ci` 这个字符串在整个 CLI dist 中已零命中(原先 `repo-cell-task-progress.js:28` 把它硬编码为公共交付见证的判定值)。本仓 `settings.ci.workflows` 现为 `[ci]` 并生效。
- **缺陷 B(`F-B1B5EABC`,纯文档任务 worktree 提交死锁)**:`repo-cell-submit.js:65-70` 新增 `privateDelivery` 判定——当任务的完成门既不含 `ci` 也不含 `code-doc-reconciliation` 时,空交付 diff 不再抛 `invalid_submission`,改走私有交付路径;同时 Summary 可用任务包内 artifacts/ 目录下的工件作为交付锚点,代替 40 位 commit sha。

交付锚点:artifact:artifacts/mission-integration.md

## Verification

- **缺陷 A 已修(三条独立证据)**:①`ha settings update --help` 的选项列表含 `--ci-workflows <ci-workflows>...`;②`packages/cli/dist/kernel/src/domain/settings.js:10` 为 `export const DEFAULT_CI_WORKFLOWS = Object.freeze([])`;③`grep -rn "rewrite-ci" packages/cli/dist` 零命中。
- **CI 见证链路实测可用**:本仓 `harness.yaml` 的 `settings.ci.workflows` 为 `[ci]`,`.github/workflows/ci.yml` 的 `name: ci` 与文件名 stem 一致,`gh run list --workflow ci` 返回真实运行记录(缺陷存在时该查询是 HTTP 404)。
- **缺陷 B 已修**:`repo-cell-submit.js:68` 的 `privateDelivery = !(snapshot.task?.completionGateIds ?? []).some(gate => gate === "ci" || gate === "code-doc-reconciliation")`,仅当非私有交付才抛 "Delivery cut contains no changed paths"。实测:本仓零门任务 `task_ed9e41ef27c8fb94e8a99062a8` 与 `task_d5e9455a1235d1554b1967c708` 以 artifact 锚点成功 `submit`(走 `commitSha: null` 路径),未再出现空 diff 拒绝。
- **顺带钉住了 ci 门的真实判据**(此前只知它会拒,不知判据):`kernel/src/domain/completion-evidence.js` 的 `judgeCompletionEvidence` 收尾为 `accepted: evidence.result === "pass"`,`fail` 以 "checker reported fail" 拒;`daemon/src/ci-observation-actions.js:41` 只为 `headBranch === "main"` 且 `status === "completed"` 的运行发布见证,`:172-178` 进一步要求 workflowName 落在 `settings.ci.workflows`、branch/sha/runId 全部对齐。**即 ci 门要求 main 分支上一次绿的运行,不是"有见证记录"即可。**

## Residual Risk

- 修复由上游完成,本仓未验证其在其他 workflow 命名或多 workflow 场景下的行为;`--ci-workflows` 是可重复选项,本仓只用了单值。
- **ci 门至今尚未实际通过一次**:本仓 main 分支的 CI 当前仍为红,原因与本任务无关(依赖安装:手写清单缺 xgboost,改用 `-r requirements.txt` 后又撞上 `numpy==2.5.3` 要求 Python>=3.12 而 CI 固定 3.11),已在 `1ebfeba`、后续提交中分两步处置。因此"20 个 standard-task 的 ci 门现已可满足"这一判断的最后一环有待那次绿运行确认。
- 本任务未产生产品代码变更,交付切面是任务包内的调查与验证工件;上游的修复提交不在本仓历史中,故无法用本仓 commit 作为交付锚点。

## Same Mechanism Elsewhere

机制:**一个被声明为可配置的字段,其默认值取自工具自身的开发环境,而没有任何命令入口能写它**——于是除该工具自己的仓库以外,任何使用者都必然撞上一个无法修改的错值。

按这句话搜本仓,命中的是同一机制的另一种形态:默认值取自**首个数据集(GB1)**的环境,且没有配置入口能改。

- `evolution/mutations.py:10` `MUTABLE_POSITIONS = (39, 40, 41, 54)` — 并在 `:29/:41/:50/:62/:85/:90` 六处被当作不变量使用;
- `evolution/random_baseline.py:39` `EXPECTED_ROWS = 149_361`、`:41` `WT = "VDGV"` — 加载时硬断言,不符即抛错;
- `features/one_hot.py:10` `FEATURE_DIM = 80`(= 4 位点 × 20 氨基酸);
- `features/esm2.py:65` `variant_to_sequence(variant) if len(variant) == 4 else variant` — 最隐蔽的一处:任何长度恰为 4 的新序列会被**静默展开**进 56-aa 的 GB1 骨架,不报错。

后果与缺陷 A 同形:换任何新数据集都会撞上这些取自单一环境的默认值,而它们没有配置入口。该清理由 `task_ff24b0e33edb3412f4dd070e4b` 跟踪(当前 `planned`),且它是"要不要把新数据集接到四策略 workflow 线"的前置。
