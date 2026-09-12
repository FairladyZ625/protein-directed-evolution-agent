---
schema: decision-package/v1
decision_id: dec_D054AAF358178C453FA1A4CEA8
workspaceRevision: 233
title: "事件流内核属交付层(前端回放底座+可审计链),不进砍单序列"
state: in_effect
riskTier: low
urgency: medium
vertical: "software/coding"
preset: "decision-conformance"
decisionClass: ordinary
applies_to: {"modules":[],"productLines":[]}
proposer: {"executor":{"id":"claude-session:8ba3077b-039d-4045-8dda-cee28d3a3986","kind":"agent"},"principal":{"personId":"person-ai4s"}}
arbiter: {"executor":{"id":"codex-session:01a08ed8-d616-7081-b1e1-ef413ec6f93b","kind":"agent"},"principal":{"personId":"person-ai4s"}}
proposedAt: "2026-09-11T03:27:39.185Z"
decidedAt: "2026-09-11T05:09:06.897Z"
provenance: [{"boundAt":"2026-09-11T03:27:39.185Z","runtime":"claude","sessionId":"8ba3077b-039d-4045-8dda-cee28d3a3986","transcriptReachability":"by_session_id"}]
question: "事件流/审计内核是可选可砍的差异化层,还是交付层的一部分?"
chosen: [{"id":"CH1","rationale":"回放与审计都以事件流为底座","text":"事件流内核作为交付层组成部分:前端回放依赖它,并提供可审计防篡改链"}]
rejected: [{"id":"RJ1","text":"把事件流当可砍的差异化彩蛋","whyNot":"会导致前端无法回放 Agent 过程"}]
claims: [{"fulfillment":null,"id":"C1","loadBearing":true,"text":"前端要展示整个过程必须先记录事件,event-stream 是回放的数据底座"},{"fulfillment":null,"id":"C2","loadBearing":true,"text":"一面对方明确重视可审计/可控,二面拿出为差异化"}]
judgmentConsents: [{"action":"accept","actor":{"executor":{"id":"codex-session:01a08ed8-d616-7081-b1e1-ef413ec6f93b","kind":"agent"},"principal":{"personId":"person-ai4s"}},"consentId":"djc_63032c54ea0cdfc5d01a93c6a4","consentedAt":"2026-09-11T05:09:06.897Z","decisionId":"dec_D054AAF358178C453FA1A4CEA8","machineDigest":"sha256:f3eeed55de0638d7d6d96f6816509ef821f29223e4b806ad6c5784c2d6f0ad4b","schema":"decision-judgment-consent/v1","source":"local","targetState":"in_effect"}]
contentPins: [{"action":"accept","actor":{"executor":{"id":"codex-session:01a08ed8-d616-7081-b1e1-ef413ec6f93b","kind":"agent"},"principal":{"personId":"person-ai4s"}},"digest":"sha256:f3eeed55de0638d7d6d96f6816509ef821f29223e4b806ad6c5784c2d6f0ad4b","evidence":"题面要求展示Agent推理过程与可交互演示；事件流提供回放和审计底座，且手册列为交付层必做，裁定成立。","pinId":"dcp_63032c54ea0cdfc5d01a93c6a4","pinnedAt":"2026-09-11T05:09:06.897Z","schema":"decision-content-pin/v1","state":"in_effect"}]
---

# 事件流内核属交付层(前端回放底座+可审计链),不进砍单序列

## 背景
一面时对方明确重视"可控、可审计、会失败"的 Agent 系统;二面把可审计事件流作为差异化。更关键:前端要回放 Agent 的整个推理过程,必须先把每步事件记录下来——事件流是回放的数据底座,不是可选彩蛋。

## 裁定
事件流内核(append-only + 链式 sha256 + SQLite 投影 + replay CLI)属于交付层的必做组成部分,进入砍单序列的"永不砍"档。它同时承担两个职责:前端过程回放的数据源,以及可审计防篡改链。

## 影响
- T4 已交付内核(store/project/replay,6 测试绿)。
- T6 五角色每步 append 事件;T8 前端读事件流做回放。
- 时间紧张时优先砍知识图谱可视化、demo 降录屏,不砍事件流。

## Judgment-only acceptance

题面要求展示Agent推理过程与可交互演示；事件流提供回放和审计底座，且手册列为交付层必做，裁定成立。
