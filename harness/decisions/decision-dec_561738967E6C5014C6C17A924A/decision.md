---
schema: decision-package/v1
decision_id: dec_561738967E6C5014C6C17A924A
workspaceRevision: 375
title: "实验报告作为一等 ReportEntity,按周期版本化并挂到产生它的任务"
state: in_effect
riskTier: low
urgency: medium
vertical: "software/coding"
preset: "decision-conformance"
decisionClass: ordinary
applies_to: {"modules":[],"productLines":[]}
proposer: {"executor":{"id":"claude-session:8ba3077b-039d-4045-8dda-cee28d3a3986","kind":"agent"},"principal":{"personId":"person-ai4s"}}
arbiter: {"executor":null,"principal":{"personId":"person-ai4s"}}
proposedAt: "2026-09-11T12:17:57.892Z"
decidedAt: "2026-09-11T12:45:34.744Z"
provenance: [{"boundAt":"2026-09-11T12:17:57.892Z","runtime":"claude","sessionId":"8ba3077b-039d-4045-8dda-cee28d3a3986","transcriptReachability":"by_session_id"}]
question: "如何以不可篡改、可审计、可回溯的方式管理每个研究周期的实验报告?"
chosen: [{"id":"CH1","rationale":"不可篡改、可审计、可回溯任意历史版本","text":"每周期一个自包含报告文件夹,report.md 经 ha entity import 登记为 report 工件实体(SHA256锁定),并用 relates 关系挂到产生它的 task"}]
rejected: [{"id":"RJ1","text":"平铺 reports/ 覆盖式文件堆","whyNot":"无版本、无防篡改、无法回溯历史版本的确切数据"}]
claims: [{"fulfillment":"evidenced","id":"C1","loadBearing":true,"text":"report 工件实体可通过 relates 关系挂到产生它的 task,建立可审计的 任务→阶段报告 拓扑"}]
judgmentConsents: [{"action":"accept","actor":{"executor":null,"principal":{"personId":"person-ai4s"}},"consentId":"djc_3184be25b4e23ff196861bc064","consentedAt":"2026-09-11T12:45:34.744Z","decisionId":"dec_561738967E6C5014C6C17A924A","machineDigest":"sha256:f98f973d22d095db81da441acb85959e6a9bfd812f1fe22e6507c7bc882828ba","schema":"decision-judgment-consent/v1","source":"local","targetState":"in_effect"}]
amendments: [{"actor":{"executor":{"id":"claude-session:a11ed5b6-6214-43b0-b577-d3e16d449705","kind":"agent"},"principal":{"personId":"person-ai4s"}},"amendedAt":"2026-09-11T12:41:07.164Z","amendmentId":"dam_2e3fb62f92eae3af141389f4bb","fields":["body"],"schema":"decision-amendment/v1"}]
contentPins: [{"action":"amend","actor":{"executor":{"id":"claude-session:a11ed5b6-6214-43b0-b577-d3e16d449705","kind":"agent"},"principal":{"personId":"person-ai4s"}},"digest":"sha256:f98f973d22d095db81da441acb85959e6a9bfd812f1fe22e6507c7bc882828ba","evidence":"fields:body","pinId":"dcp_2e3fb62f92eae3af141389f4bb","pinnedAt":"2026-09-11T12:41:07.164Z","schema":"decision-content-pin/v1","state":"proposed"},{"action":"accept","actor":{"executor":null,"principal":{"personId":"person-ai4s"}},"digest":"sha256:f98f973d22d095db81da441acb85959e6a9bfd812f1fe22e6507c7bc882828ba","evidence":"同意","pinId":"dcp_3184be25b4e23ff196861bc064","pinnedAt":"2026-09-11T12:45:34.744Z","schema":"decision-content-pin/v1","state":"in_effect"}]
---
## 背景
每个研究周期(workflow-v1.0、agentic-v0.1、后续 v0.2…)都产出一份报告 + 一批数据(metrics/events/figures)。若平铺堆在 reports/,无法回溯"历史上某版本确切是这组数据",也无防篡改。医药/科研标准要求可审计、不可篡改、可回溯。

## 裁定
每个周期 = 一个自包含文件夹 harness/reports/<line>-v<version>/(report.md + 数据),整文件夹经 ha entity import --kind report 登记为 report 工件实体,内容 SHA-256 锁定,freshness 引擎自动追踪篡改;并用 relates 关系挂到产生它的 task,建立"任务→阶段报告"可审计拓扑。新一版 = 新文件夹,旧版永不覆盖。

## 影响
- 新增 report 实体种类(KND-22c8d77f…);已导入 REP-637f0c27(workflow-v1.0)、REP-3e2a7fef(agentic-v0.1)。
- 每周期结束按此登记并 relates 挂 task;最终 8 章报告单独写(harness/final-report/)。
- reports/ 迁入 harness/ 下,最终公开快照连 harness 仓一起推。

## 证据
C1 由 F-9EC46CD1 佐证:两周期整文件夹导入成功、整树 SHA256 锁定、与仓库已在用的 research 实体(relates→task)同构。
