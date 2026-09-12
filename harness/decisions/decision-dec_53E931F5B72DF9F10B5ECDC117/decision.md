---
schema: decision-package/v1
decision_id: dec_53E931F5B72DF9F10B5ECDC117
workspaceRevision: 231
title: "提名/评估空间统一限定为 149,361 个有真值 GB1 变体"
state: in_effect
riskTier: medium
urgency: high
vertical: "software/coding"
preset: "decision-conformance"
decisionClass: ordinary
applies_to: {"modules":[],"productLines":[]}
proposer: {"executor":{"id":"claude-session:8ba3077b-039d-4045-8dda-cee28d3a3986","kind":"agent"},"principal":{"personId":"person-ai4s"}}
arbiter: {"executor":{"id":"codex-session:01a08ed8-d616-7081-b1e1-ef413ec6f93b","kind":"agent"},"principal":{"personId":"person-ai4s"}}
proposedAt: "2026-09-11T03:27:30.467Z"
decidedAt: "2026-09-11T05:09:06.161Z"
provenance: [{"boundAt":"2026-09-11T03:27:30.467Z","runtime":"claude","sessionId":"8ba3077b-039d-4045-8dda-cee28d3a3986","transcriptReachability":"by_session_id"}]
question: "四策略候选提名空间覆盖全部 20^4=160,000 组合,还是只限有真值的 149,361 个?"
chosen: [{"id":"CH1","rationale":"同口径才可比,且避免缺真值键查表失败","text":"四策略统一只在 149,361 个有真值变体内提名与评估"},{"id":"CH2","rationale":"如实披露数据边界","text":"缺失的 10,639 组合记为已知局限并改掉 README 组合完备措辞"}]
rejected: [{"id":"RJ1","text":"允许提名到全部 160,000 组合","whyNot":"缺真值键查表会 KeyError 或被隐式当 0,四策略口径不一致、对比不可信"}]
claims: [{"fulfillment":null,"id":"C1","loadBearing":true,"text":"四策略必须共享同一提名空间与同一 oracle 才能公平对比"},{"fulfillment":null,"id":"C2","loadBearing":true,"text":"缺失的 10,639 个组合是真实缺数据、找不着、不可补"}]
judgmentConsents: [{"action":"accept","actor":{"executor":{"id":"codex-session:01a08ed8-d616-7081-b1e1-ef413ec6f93b","kind":"agent"},"principal":{"personId":"person-ai4s"}},"consentId":"djc_d6f5f376d646ae8306395fa0a9","consentedAt":"2026-09-11T05:09:06.161Z","decisionId":"dec_53E931F5B72DF9F10B5ECDC117","machineDigest":"sha256:68e7545e36c3a9324712e4bb9e15ccce0ef4e2efa67d04690573316ee028283f","schema":"decision-judgment-consent/v1","source":"local","targetState":"in_effect"}]
amendments: [{"actor":{"executor":{"id":"claude-session:8ba3077b-039d-4045-8dda-cee28d3a3986","kind":"agent"},"principal":{"personId":"person-ai4s"}},"amendedAt":"2026-09-11T04:56:08.830Z","amendmentId":"dam_4e7c6b0df50c3f8ad3596f2c64","fields":["body"],"schema":"decision-amendment/v1"}]
contentPins: [{"action":"amend","actor":{"executor":{"id":"claude-session:8ba3077b-039d-4045-8dda-cee28d3a3986","kind":"agent"},"principal":{"personId":"person-ai4s"}},"digest":"sha256:68e7545e36c3a9324712e4bb9e15ccce0ef4e2efa67d04690573316ee028283f","evidence":"fields:body","pinId":"dcp_4e7c6b0df50c3f8ad3596f2c64","pinnedAt":"2026-09-11T04:56:08.830Z","schema":"decision-content-pin/v1","state":"proposed"},{"action":"accept","actor":{"executor":{"id":"codex-session:01a08ed8-d616-7081-b1e1-ef413ec6f93b","kind":"agent"},"principal":{"personId":"person-ai4s"}},"digest":"sha256:68e7545e36c3a9324712e4bb9e15ccce0ef4e2efa67d04690573316ee028283f","evidence":"独立核对手册与题面，CSV实测149,361条变体（含表头149,362行）；统一有真值空间可避免oracle KeyError并如实披露缺失，裁定成立。","pinId":"dcp_d6f5f376d646ae8306395fa0a9","pinnedAt":"2026-09-11T05:09:06.161Z","schema":"decision-content-pin/v1","state":"in_effect"}]
---
## 背景
GB1 组合空间为 20^4=160,000,但本地真值表(Wu 2016/FLIP)只覆盖 149,361 个变体,缺失 10,639 个是真实无数据、找不着。四策略对比中,LLM Agent 会提出任意 4 位点组合,若允许提名到缺真值组合,虚拟 oracle 查表会 KeyError 或被隐式当 0。

## 裁定
四策略(随机/模型贪心/Agent/知识增强)统一只在 149,361 个有真值变体内提名与评估,共享同一 oracle。缺失的 10,639 记为"已知数据局限"写入报告,并把 README 中"组合完备/完美 oracle"措辞改为"149,361/160,000"。

## 影响
- T7 campaign 的提名空间与 T1 一致(表内可测变体),四策略同口径。
- T6 Agent 的 Mutation Designer 输出须过滤到可测空间。
- T9 报告如实披露该边界,不宣称"完美 oracle"。

## Judgment-only acceptance

独立核对手册与题面，CSV实测149,361条变体（含表头149,362行）；统一有真值空间可避免oracle KeyError并如实披露缺失，裁定成立。
