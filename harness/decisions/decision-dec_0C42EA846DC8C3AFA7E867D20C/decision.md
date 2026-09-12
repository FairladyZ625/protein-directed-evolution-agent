---
schema: decision-package/v1
decision_id: dec_0C42EA846DC8C3AFA7E867D20C
workspaceRevision: 234
title: "LLM 走商业 API(Claude/GPT-4o/DeepSeek),不用本地量化默认"
state: in_effect
riskTier: low
urgency: medium
vertical: "software/coding"
preset: "decision-conformance"
decisionClass: ordinary
applies_to: {"modules":[],"productLines":[]}
proposer: {"executor":{"id":"claude-session:8ba3077b-039d-4045-8dda-cee28d3a3986","kind":"agent"},"principal":{"personId":"person-ai4s"}}
arbiter: {"executor":{"id":"codex-session:01a08ed8-d616-7081-b1e1-ef413ec6f93b","kind":"agent"},"principal":{"personId":"person-ai4s"}}
proposedAt: "2026-09-11T03:27:39.560Z"
decidedAt: "2026-09-11T05:09:07.279Z"
provenance: [{"boundAt":"2026-09-11T03:27:39.560Z","runtime":"claude","sessionId":"8ba3077b-039d-4045-8dda-cee28d3a3986","transcriptReachability":"by_session_id"}]
question: "Agent 的 LLM 用本地/GLM 还是商业 API?"
chosen: [{"id":"CH1","rationale":"JSON schema 遵循率高、推理更深","text":"用商业 LLM API(Claude 3.5 Sonnet / GPT-4o / DeepSeek-V3)"}]
rejected: [{"id":"RJ1","text":"本地量化模型/pi SDK 微调","whyNot":"schema 遵循不稳、推理弱"},{"id":"RJ2","text":"默认 GLM","whyNot":"作为离线兜底保留但非主线"}]
claims: [{"fulfillment":null,"id":"C1","loadBearing":true,"text":"五角色流水线要求 LLM 严格产出 Pydantic schema,商业 API 遵循率近 100%"}]
judgmentConsents: [{"action":"accept","actor":{"executor":{"id":"codex-session:01a08ed8-d616-7081-b1e1-ef413ec6f93b","kind":"agent"},"principal":{"personId":"person-ai4s"}},"consentId":"djc_c4241b96be687a33a135d85172","consentedAt":"2026-09-11T05:09:07.279Z","decisionId":"dec_0C42EA846DC8C3AFA7E867D20C","machineDigest":"sha256:2eb1b371abfca66e1968231274f205e2110ff6969b484f33006b801f8cb5f7b4","schema":"decision-judgment-consent/v1","source":"local","targetState":"in_effect"}]
contentPins: [{"action":"accept","actor":{"executor":{"id":"codex-session:01a08ed8-d616-7081-b1e1-ef413ec6f93b","kind":"agent"},"principal":{"personId":"person-ai4s"}},"digest":"sha256:2eb1b371abfca66e1968231274f205e2110ff6969b484f33006b801f8cb5f7b4","evidence":"题面允许OpenAI等外部API；手册要求商业API及Pydantic结构化输出，revision-report同口径，默认商业API裁定成立。","pinId":"dcp_c4241b96be687a33a135d85172","pinnedAt":"2026-09-11T05:09:07.279Z","schema":"decision-content-pin/v1","state":"in_effect"}]
---

# LLM 走商业 API(Claude/GPT-4o/DeepSeek),不用本地量化默认

## 背景
五角色流水线要求 LLM 严格产出 Pydantic schema(Hypothesis Generator、Scientific Critic 两处);本地量化模型/pi SDK 微调的 schema 遵循率不稳、推理弱。

## 裁定
Agent 的 LLM 默认走商业 API(Claude 3.5 Sonnet / GPT-4o / DeepSeek-V3),JSON schema 遵循率近 100%、推理更深。GLM 作为离线兜底保留但非主线。

## 影响
- T6 的 output_type=Pydantic schema 依赖商业 API 的高遵循率。
- 需在报告与 README 声明外部 LLM 资源及使用方式(题目要求)。
- 失败要有降级链;所有外部调用记入事件流可审计。

## Judgment-only acceptance

题面允许OpenAI等外部API；手册要求商业API及Pydantic结构化输出，revision-report同口径，默认商业API裁定成立。
