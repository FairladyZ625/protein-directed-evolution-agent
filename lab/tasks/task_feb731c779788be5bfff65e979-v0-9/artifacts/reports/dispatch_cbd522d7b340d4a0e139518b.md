Verdict：打回（`changes_requested`）。已记录独立评审 `review_de_reviewer_20260914_v09_r3`。

证据：

- 定向测试：`16 passed`。
- 四臂事件流均可解压；v08 未分叉，v09 已分叉，反思臂 `excluded_motifs` 非空 5/6。
- 提交 `3591541` 不含 `tmp/v09-contract/`，但任务契约仍指定该路径。
- `exclusion_too_strict` 测试位于后续提交 `646ad49`，不属于本次 submitted execution。
- 全仓引用检查仍报告 5 处失效引用。

修复方向：用新的 execution 提交纳入测试修复；统一任务声明、脚本与正式产物路径（或经治理正式修订契约并提供映射）；如实限定 closeout 的引用检查范围后重新提交。