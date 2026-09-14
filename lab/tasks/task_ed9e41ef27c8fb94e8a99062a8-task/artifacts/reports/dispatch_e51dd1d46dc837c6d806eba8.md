结论：打回（`changes_requested`）。已对 submitted execution `exe_499602fd19b231c42c6448dc7e` 提交独立评审 `review_de_reviewer_20260914_r5`，状态为 `accepted_durable / projection verified`。

已核实：

- 工件 SHA 与执行回执一致，123 行，6 个候选数据集。
- AAV 清洗后 38,265 条；冷启动 10,433、候选池 27,832；池峰值 8.416205、冷启动 incumbent 9.536457。
- 四策略指标、UCB 重复实验及知识消融数据均能从仓库报告复算。
- 未修改业务代码。

需修复：

1. [harder-dataset-survey.md:61] 中把缺失 `D0Q+S17E` 写成“不存在加性单步上升路径”过度泛化；实际存在 `WT → S17E → S17E+V18A → D0Q+S17E+V18A` 的单调路径，应限定为“特定 stepping-stone 未观测”。
2. [harder-dataset-survey.md:84] 和 `:105` 的 `238` 未标 `[需核实]`，违反任务契约；需修正并扫描全文类似外部断言。
3. 知识消融需明确无知识池为 27,832、知识过滤后有效池约 9,533，并标注强阈值 `2.615913579904`；结论应保持为 HD/BLOSUM 过滤与图机制的复合效应，不能归因于单一图机制。
4. 现存 standing facts `F-51F2E349`、`F-9649A483` 与当前实测口径冲突，应通过 Harness 追加更正事实并建立 supersedes 关系。

全量 `pytest` 未执行；本任务为文档调研任务。