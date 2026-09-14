---
schema: decision-package/v1
decision_id: dec_9C76B8C06D36F7E3BEFCA2A097
workspaceRevision: 235
title: "以 revision-report 为唯一现行方案,旧 technical-plan 废弃"
state: in_effect
riskTier: low
urgency: high
vertical: "software/coding"
preset: "decision-conformance"
decisionClass: ordinary
applies_to: {"modules":[],"productLines":[]}
proposer: {"executor":{"id":"claude-session:8ba3077b-039d-4045-8dda-cee28d3a3986","kind":"agent"},"principal":{"personId":"person-ai4s"}}
arbiter: {"executor":{"id":"codex-session:01a08ed8-d616-7081-b1e1-ef413ec6f93b","kind":"agent"},"principal":{"personId":"person-ai4s"}}
proposedAt: "2026-09-11T03:27:39.941Z"
decidedAt: "2026-09-11T05:09:07.648Z"
provenance: [{"boundAt":"2026-09-11T03:27:39.941Z","runtime":"claude","sessionId":"8ba3077b-039d-4045-8dda-cee28d3a3986","transcriptReachability":"by_session_id"}]
question: "technical-plan 与 revision-report 冲突时以哪版为准?"
chosen: [{"id":"CH1","rationale":"新版修正了旧版的关键错误","text":"以 revision-report(新版)为唯一现行方案:本地实时 ESM、商业 API、极简 Streamlit"},{"id":"CH2","rationale":"避免双真源漂移","text":"旧 technical-plan 归档为背景,不再作现行决策依据"}]
rejected: [{"id":"RJ1","text":"保留 technical-plan 的 CPU-only/预提取/GLM 默认路线并列","whyNot":"与新版直接冲突,双真源不可维护"}]
claims: [{"fulfillment":null,"id":"C1","loadBearing":true,"text":"两文档在表征路线与 LLM provider 上直接冲突,需单一现行真源"}]
judgmentConsents: [{"action":"accept","actor":{"executor":{"id":"codex-session:01a08ed8-d616-7081-b1e1-ef413ec6f93b","kind":"agent"},"principal":{"personId":"person-ai4s"}},"consentId":"djc_eba5986f7cab326c3ec55ebcc6","consentedAt":"2026-09-11T05:09:07.648Z","decisionId":"dec_9C76B8C06D36F7E3BEFCA2A097","machineDigest":"sha256:d76e1c8bf7c73aeb790e7c69307fafddac193fa0e5de77923a24369c4d282b70","schema":"decision-judgment-consent/v1","source":"local","targetState":"in_effect"}]
contentPins: [{"action":"accept","actor":{"executor":{"id":"codex-session:01a08ed8-d616-7081-b1e1-ef413ec6f93b","kind":"agent"},"principal":{"personId":"person-ai4s"}},"digest":"sha256:d76e1c8bf7c73aeb790e7c69307fafddac193fa0e5de77923a24369c4d282b70","evidence":"revision-report明确修正旧technical-plan的静态嵌入与GLM路线；手册指定新版唯一真源，避免双方案冲突，裁定成立。","pinId":"dcp_eba5986f7cab326c3ec55ebcc6","pinnedAt":"2026-09-11T05:09:07.648Z","schema":"decision-content-pin/v1","state":"in_effect"}]
---

# 以 revision-report 为唯一现行方案,旧 technical-plan 废弃

## 背景
仓库里 technical-plan(旧)与 revision-report(新)在两个关键决定上直接冲突:表征路线(预提取/CPU-only vs 本地实时 ESM)、LLM provider(GLM 默认 vs 商业 API)。双真源会持续漂移。

## 裁定
以 revision-report(新版)为唯一现行方案:本地实时 ESM、商业 API、极简 Streamlit 三模块。旧 technical-plan 归档为背景材料,不再作为现行决策依据。

## 影响
- D2/D4 的口径以本裁定为总纲。
- 后续所有 worker 的 read-set 以 revision-report 为准,冲突时不采信旧 plan。
- T9 报告的方案叙述基于新版。

## Judgment-only acceptance

revision-report明确修正旧technical-plan的静态嵌入与GLM路线；手册指定新版唯一真源，避免双方案冲突，裁定成立。
