verdict：打回（未能写入 Harness 台账；因 `reviewReturnBudget=4`，CLI 返回 `manual_intervention_required`）。

证据：

- 事实勘验通过：AAV clean 38,265 条；目标峰 `8.416205` 在池内；`D0Q+S17E` 全表缺测。
- artifact 与 canonical 文档 SHA256 一致：`cfd742...1df38b`。
- 文档第 87–93、196–204 行明确承认多数引用缺完整标题、DOI/稳定链接且未逐篇核验，不满足任务要求的“真实可核引用”。
- 文档把单独实测的 UCB β=3 结果延伸为“信任域 + viability-gated 联用”效果，但现有证据未运行该组合，属于未经验证的外推。

修复方向：

1. 为每条方法补齐可定位书目，或删除待核文献并仅作为背景。
2. 明确区分“UCB/现有门禁已实测”和“TuRBO、viability-gating 联用待验证”。
3. owner 执行 `ha task submit ... --amend` 后重新提交复审。