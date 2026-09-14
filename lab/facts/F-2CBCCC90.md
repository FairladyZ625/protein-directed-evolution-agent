# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-2CBCCC90

- Statement: v0.8 的 agent_requested=0/20 不是模型不用工具,而是契约形状:两个采集段落都写着 Prefer that default、round prompt 把 compose_batch(n=48) 写死无 ratio 参数位、利用比地板恰好只禁止残差该触发的调低方向(实测第4轮起可行区间为空集)、且 exploit_ratio 是标量无法表达 motif 级排除。v0.9 冒烟改契约后 agent_requested 立刻变为 2/2。
- Evidence source: agent/auto_researcher.py; lab/tasks/task_91e931121d3ae400a0a2be246b-v0-8-aav/artifacts/factorial-2x2-seed42.md
- Observed at: 2026-09-13T04:31:57.264Z
- Confidence: high
- State: standing

