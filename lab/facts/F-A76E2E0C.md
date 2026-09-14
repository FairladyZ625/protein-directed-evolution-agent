# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-A76E2E0C

- Statement: reviewReturnBudget 的耗尽判据绑定 Execution 的 Iteration。ha task submit --amend 不递增 Iteration(r6 在 Iteration 4 上成功落库 changes_requested);ha task start + 普通 ha task submit 新开执行并递增 Iteration(4→5),一旦 Iteration 超过 reviewReturnBudget=4,changes_requested 即被 manual_intervention_required 拒绝、无法落库(r7 实测),但 approved 仍可记录并可继续 consent→complete(d5e9455a 即在 Iteration 5 approved 后完成)。操作结论:in_review 下继续修复一律用 --amend。附带:ha fact record --supersedes 要求 canonical ref 形式 fact/F-XXXXXXXX,传裸 id 报 invalid_command。
- Evidence source: r7 review-execution: manual_intervention_required 'return budget exhausted'; r6 经 --amend 于 Iteration 4 落库 changes_requested; exe_d44a3176bb83f91436fa5f4888 经 start+submit 升至 Iteration 5; ha settings read reviewReturnBudget=4; d5e9455a 在 Iteration 5 approved 后完成
- Observed at: 2026-09-14T11:46:51.973Z
- Confidence: high
- State: standing

