任务已完成并停在本地提交 `9e90575ff59a69d26ca92ac69ca50953abc26e9f`，未 push/PR。

核心结论：

- GB1 Spearman：≤1→2 为 `0.657990`，≤2→3 降至 `0.558856`
- AAV Spearman：≤1→2 为 `0.874888`，≤2→3 降至 `0.615519`
- AAV 真峰实测 `8.416205`，加性预测 `6.315428`，正上位残差 `+2.100778`
- 真峰三个直接二阶构件仅实测 `2/3`，缺少 D0Q+S17E
- AAV 三阶完整低阶覆盖率仅 `31.17%`，四阶降至 `2.24%`

交付：

- [分析入口](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-mutation-order/analysis/mutation_order.py)
- [定量报告](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-mutation-order/harness/reports/analysis-v0.1/report.md)
- [测试](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-mutation-order/tests/test_mutation_order.py)
- GB1/AAV 全精度 JSON 与图已写入 `harness/reports/analysis-v0.1/{gb1,aav}/`

验证证据：

```text
gb1 {"n": 149361, "spearman": [0.6579902547119055, 0.5588564275111084]}
aav {"n": 38265, "spearman": [0.8748881725761463, 0.6155193550463083]}
5 passed in 3.84s
```

已记录承重事实 `F-31A132DA`。风险是 AAV loader 实际保留 38,265 条，与旧研究文字的 38,293 条不一致；报告已明确披露。另因 AAV 库设计存在阶数选择偏差，阶间分布不可解释为突变数的因果效应。