# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-A64AE06A

- Statement: AGENTS.md 里一条过期的仓规在本会话造成两次误判,已更正(提交 35f8384)。旧条目称「本仓 standard-task 的 ci 门结构性不可满足,submit/complete 必返 service_rejected,依据 gh run list --workflow rewrite-ci.yml HTTP 404」。实测该条已失效:rewrite-ci 在全局 CLI dist 里 grep 零命中,上游缺陷已修;那个 404 源于拿错 workflow 名——harness.yaml:13-14 配置的是 workflows: [ci]。真实判据见 fact F-B0148E72:见证只为 headBranch=='main' 且 status=='completed' 的运行发布,且 workflowName 须在 settings.ci.workflows 内,与被审任务自身 commit 无关。两次误判的具体形态:①对 task_2e485a1ae 事前判定 complete 必被 service_rejected 拒,实际 applied 并自动铸出 Checker witnesses: ci/op_5bcd5086…;②据此又推断「其余带 git 锚的停摆任务本来就能收」,该推论当时无证据,已撤回。真实原因是本会话修 CI 的三个提交(1ebfeba/d1e38b9/646ad49)把 main 的 ci 跑绿,使门的取证面成立,task_2e485a1ae 与 task_6a18b55b9 因此得以 approved→consent→complete 收口。
- Evidence source: AGENTS.md:130(改前); 提交 35f8384; fact F-B0148E72; gh run list --workflow ci --branch main; harness/harness.yaml:13-14
- Observed at: 2026-09-14T13:49:06.063Z
- Confidence: high
- State: standing

