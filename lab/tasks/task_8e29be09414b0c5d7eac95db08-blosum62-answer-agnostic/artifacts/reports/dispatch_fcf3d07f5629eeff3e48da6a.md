Verdict：打回（changes_requested），已通过 Harness 记录为独立评审 `review_de_reviewer_20260914_kb_iter1`。

关键证据：

- 当前 BLOSUM 矩阵完整，缺失 `0`；显式零分均正确保留。
- `auto_researcher.py:488–508` 已消费知识图谱并生成 rationale。
- 当前无标签审计结果为：`gate=2515`、`gate_residue_pairs=3878`、`unseen_residue_pairs=2323`、`gate_candidates_with_unseen_pair=1770`，与提交中的 `9533/11130/7937/6852` 不符。
- 指定的 `v07-peak-mechanism.md` 当前存在，提交却称其缺失。

请按当前代码重新生成覆盖率与现状盘点，删除或明确隔离过时观测，并同步修正证据边界与结论数字。未修改业务代码。