# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-7445CEDD

- Statement: 随机基线阴性对照 PASS:三轮最高 top10_mean 0.814 远低于全表 top-1% 均值 3.304;make test 5 passed;跨 numpy/pandas 环境指标 JSON 逐字节一致;数据契约 149,361 行校验通过。随机策略作为四方法对比地板线成立。
- Evidence source: T1 reports/random_baseline_metrics.json + make test 输出 + de-reviewer 独立复核
- Observed at: 2026-09-11T05:03:44.422Z
- Confidence: high
- State: standing

