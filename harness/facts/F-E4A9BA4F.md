# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-E4A9BA4F

- Statement: AAV 池同预算288同oracle下,给自主 agent 加双层 Knowledge 门禁流(list_pool 入口只出门内候选 HD≤4且平均BLOSUM62≥0 + test 出口硬门)后:cum_top10_max 由 v0.1 的 5.96 升至 7.53(追平 greedy),strong 命中 15→93,budget 花满 284/288,n_gate_rejected=1(手搓门外候选被出口门抓),事件链43事件校验通过。探索惩罚被消除(测的全是HD3-4保守变体,对比 v0.1 explorer 均HD17),但未突破 7.53:真峰8.42在门内仍被 one_hot 代理排到#5763,天花板是表征问题非决策问题。
- Evidence source: harness/reports/agentic-v0.2/report.md
- Observed at: 2026-09-11T15:20:00.546Z
- Confidence: high
- State: standing

