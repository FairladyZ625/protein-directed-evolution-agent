---
schema: decision-package/v1
decision_id: dec_956152B50EA1B4EC050D9C7FAF
workspaceRevision: 995
title: "因果归因外环先隔离证据与评测，再开放单一模型插件变异面"
state: in_effect
riskTier: low
urgency: medium
vertical: "software/coding"
preset: "decision-conformance"
decisionClass: ordinary
applies_to: {"modules":[],"productLines":[]}
proposer: {"executor":{"id":"runtime-session:runtime_40c7e26ecf2d9df4345b5eeb","kind":"agent"},"principal":{"personId":"person-ai4s"}}
arbiter: {"executor":null,"principal":{"personId":"person-ai4s"}}
proposedAt: "2026-09-12T06:00:41.013Z"
decidedAt: "2026-09-12T09:09:31.261Z"
provenance: [{"boundAt":"2026-09-12T06:00:41.013Z","runtime":"codex","sessionId":"01a09429-dc55-73f1-9473-f7e79c98ccd8","transcriptReachability":"dispatch_stream_only"}]
question: "下游如何在不泄漏答案、不自改评价规则的前提下实现因果归因与自动模型补丁？"
chosen: [{"id":"CH1","rationale":"让归因、补丁效用与恢复行为可分别验证，失败时保留历史已验证版本。","text":"采用清洁证据视图、直接/总效应分离、独立 Verifier 与有界事务，先实现单一模型插件修改面。"}]
rejected: [{"id":"RJ1","text":"向自主研究者直接提供含已知峰的事后研究笔记，并允许修改评测与多种优化面。","whyNot":"答案泄漏使自主发现评价失真；多面同时改写无法隔离因果，评价器自改不能证明真实收益。"}]
claims: [{"fulfillment":"evidenced","id":"C1","loadBearing":true,"text":"指定平台期笔记含真实峰身份、分数和排名；后续自主研究输入需要剔除这些事后答案。"},{"fulfillment":"evidenced","id":"C2","loadBearing":true,"text":"蓝图的 13 状态、13 Pydantic 契约与 13 负例静态验证通过，但未提供运行期或生物学有效性证据。"}]
judgmentConsents: [{"action":"accept","actor":{"executor":null,"principal":{"personId":"person-ai4s"}},"consentId":"djc_7df773b14f23699e5dee45a3c6","consentedAt":"2026-09-12T09:09:31.261Z","decisionId":"dec_956152B50EA1B4EC050D9C7FAF","machineDigest":"sha256:644f9d10c44e38c022fad07b274a672b0998a60a61a85cd6c00c118729caa276","schema":"decision-judgment-consent/v1","source":"local","targetState":"in_effect"}]
contentPins: [{"action":"accept","actor":{"executor":null,"principal":{"personId":"person-ai4s"}},"digest":"sha256:644f9d10c44e38c022fad07b274a672b0998a60a61a85cd6c00c118729caa276","evidence":"同意","pinId":"dcp_7df773b14f23699e5dee45a3c6","pinnedAt":"2026-09-12T09:09:31.261Z","schema":"decision-content-pin/v1","state":"in_effect"}]
---
## 背景
因果归因蓝图已提供模型与采集分离的试验协议、13 状态机、独立 Verifier、恢复事务及静态验收。指定平台期研究笔记包含真实峰答案，不能原样进入未来 answer-agnostic 自主研究者。来源清单与字节 pin 位于本任务 artifacts/source-manifest.json。

## 裁定
建议下游实现先采用清洁证据视图、固定预算和独立评测，开放单一模型插件修改面；区分冻结数据预测效应与闭环总效应。未识别或未通过晋级门时保留 champion。该决策为待接受提案，不授权部署，不宣称真实景观因果结论或沙箱安全已验证。

## 影响
实施顺序为证据/检测、受控干预、沙箱与事务、经验编译验证。根评价器、权限、隐藏标签和预算不在候选变异面。未来开发任务由接受后的裁定正式派生；当前不自动创建实施任务。

## 反证与残余风险
若固定数据下模型效应不能迁移到同预算闭环、静态契约无法通过运行期越权与崩溃注入、或清洁视图仍有答案泄漏，应保持 champion 并修订方案。静态通过仅表示设计结构自洽；尚无真实实验/运行期安全证据。独立接受必须按此证据边界审查。
