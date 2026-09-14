# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-7BFC6BD4

- Statement: ha task submit 成功时返回的文案是 'Worker must draft closeout.md before completion with Summary, Verification, Residual Risk, and Same Mechanism Elsewhere; the reviewer verifies and finalizes it against ground truth.' 这是完成包写作指引,不是拒绝原因:即使 closeout.md 四小节齐备且无占位符,成功提交仍返回该句。可靠判据只有执行记录本身——executions/exe_*.md 的 State=submitted 与 Closed=open,配合 ha task show 的 status=in_review/graph cursor=review,以及 artifact 行的 @revision 与 sha256 相对上一轮发生变化。ha task submit 不支持 --dry-run(unknown_field)。框架摩擦:成功路径返回指引式文案会诱导调用方判为失败并重试。
- Evidence source: ha task submit task_d3dfe26bf702928b1c3784e60f / task_d5e9455a1235d1554b1967c708 的输出; lab/tasks/*/executions/exe_d44a3176bb83f91436fa5f4888.md 与 exe_471bada619dc72466c9baf63e9.md (Iteration: 5, State: submitted, Closed: open); ha task show 两任务 status=in_review/graph cursor=review
- Observed at: 2026-09-14T11:38:29.282Z
- Confidence: high
- State: standing

