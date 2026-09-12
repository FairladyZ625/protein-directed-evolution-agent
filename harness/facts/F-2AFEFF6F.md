# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-2AFEFF6F

- Statement: v0.4 更多轮次消融(same seed42/门禁/上位surrogate,per-round48):6轮288→7.829、12轮576→7.829(round5达峰后7轮全平)、16轮768→7.53(更差)。加到12/16轮(2-2.67×预算)LLM均未达真峰8.416,而确定性gated-greedy同surrogate仅288就直达8.416。反驳'来不及跑'假设:LLM在v0.4的短板不是budget/rounds不足,是自主explore/exploit决策的利用效率确实不如纯greedy——给足runway仍达不到峰,16轮因不同pacing反而更差(LLM决策变异)。坐实:破顶来自表征(surrogate),自主性在利用上位surrogate这步是liability非asset。
- Evidence source: harness/reports/agentic-v0.4/aav/agentic_16rounds.metrics.json
- Observed at: 2026-09-12T03:15:43.214Z
- Confidence: high
- State: standing

