# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-B1B5EABC

- Statement: Harness 框架缺陷B(纯文档任务派进 worktree 后无法 submit):deriveCloseoutSubmission 在执行被 dispatch 绑定了 cwd 时(directories.length>0)走产品仓 diff 路径,要求 base..commitSha 有非空变更;而本仓 .gitignore 第17行忽略整个 /harness/ 树(研究文档走 ledger 而非产品仓),故纯文档任务的 worker 提交必然是空提交,submit 抛 invalid_submission -> document_invalid。未绑 worktree 的同类任务(privateDelivery 路径,取 ledgerRoot HEAD + artifacts 检查)可正常提交。受影响:task_e2eab881832291e8f8f73f30a4、task_8e29be09414b0c5d7eac95db08。且执行处于 active 时无法用 --execution-id 另起一个新执行来绕开绑定。
- Evidence source: packages/cli/dist/daemon/src/repo-cell-submit.js:9-88; .gitignore:17
- Observed at: 2026-09-12T09:29:10.912Z
- Confidence: high
- State: standing

