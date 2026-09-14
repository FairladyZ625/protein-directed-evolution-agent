# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-ABD9B83F

- Statement: 修好端口契约后,LLM Critic 在 workflow-v1.1 llm regime 的真实成功率是 10 次尝试中 5 次返回实质内容、5 次在 90 秒超时后回退(第 2 轮实测)。成功的评审是有科学实质的,例如引用候选 V54C 的实测单位点增益 +0.345 并给出「promising but not fully auditable」的判断,不是套话。这说明:①LLM 确实接进了五角色链路(此前 F-363846B5 证明它一次都没成功过);②池端点在 90 秒超时下约半数请求不返回,报告必须写明这个成功率而不能笼统说「由 LLM 评审」;③每轮 10 次调用里约 5 次要等满 90 秒,单个 critic 因此要花 7-8 分钟,这是 llm regime 比确定性 regime 慢一个数量级的直接原因。llm_critique_budget 上限是必需的:第 2 轮有 6508 个候选通过确定性门禁,无上限则需约 34 小时。
- Evidence source: lab/reports/workflow-v1.1/gb1/campaign_llm.events.jsonl 第2轮 scientific_critic 事件;agent/llm.py:54 LLM_TIMEOUT 默认 90
- Observed at: 2026-09-12T16:04:06.710Z
- Confidence: high
- State: standing

