---
schema: decision-package/v1
decision_id: dec_F08B92A50B80439AC8FD8BA0C5
workspaceRevision: 232
title: "表征路线:ESM-2 650M 本地实时(L2 主力)+ one-hot(L1),嵌入缓存进仓库"
state: in_effect
riskTier: medium
urgency: high
vertical: "software/coding"
preset: "decision-conformance"
decisionClass: ordinary
applies_to: {"modules":[],"productLines":[]}
proposer: {"executor":{"id":"claude-session:8ba3077b-039d-4045-8dda-cee28d3a3986","kind":"agent"},"principal":{"personId":"person-ai4s"}}
arbiter: {"executor":{"id":"codex-session:01a08ed8-d616-7081-b1e1-ef413ec6f93b","kind":"agent"},"principal":{"personId":"person-ai4s"}}
proposedAt: "2026-09-11T03:27:38.809Z"
decidedAt: "2026-09-11T05:09:06.532Z"
provenance: [{"boundAt":"2026-09-11T03:27:38.809Z","runtime":"claude","sessionId":"8ba3077b-039d-4045-8dda-cee28d3a3986","transcriptReachability":"by_session_id"}]
question: "特征表征用预提取死表格、纯 one-hot、还是本地实时 ESM-2?如何兼顾评委可复现?"
chosen: [{"id":"CH1","rationale":"Agent 提任意新变体都能实时取特征","text":"ESM-2 650M 本地实时提取作 L2 主力,one-hot 作 L1 阶梯"},{"id":"CH2","rationale":"满足题目可复现要求","text":"embedding 缓存进仓库,使评委无 GPU 也能复现"}]
rejected: [{"id":"RJ1","text":"FLIP 预提取死表格","whyNot":"Agent 提新变体会对不上,违背探索未知候选初衷"},{"id":"RJ2","text":"纯 one-hot 单一路线","whyNot":"丢失 ESM 语义,指标上限低"}]
claims: [{"fulfillment":null,"id":"C1","loadBearing":true,"text":"Agent 会提出任意新变体,需能对任意序列实时取特征"},{"fulfillment":null,"id":"C2","loadBearing":true,"text":"题目要求代码可复现,故嵌入须缓存且保留 one-hot CPU 兜底"}]
judgmentConsents: [{"action":"accept","actor":{"executor":{"id":"codex-session:01a08ed8-d616-7081-b1e1-ef413ec6f93b","kind":"agent"},"principal":{"personId":"person-ai4s"}},"consentId":"djc_74c91a8f114e93907c3d10826d","consentedAt":"2026-09-11T05:09:06.532Z","decisionId":"dec_F08B92A50B80439AC8FD8BA0C5","machineDigest":"sha256:559cd8b701d51013a55ada05ade42638e9a4a126248236830376827509e1770e","schema":"decision-judgment-consent/v1","source":"local","targetState":"in_effect"}]
contentPins: [{"action":"accept","actor":{"executor":{"id":"codex-session:01a08ed8-d616-7081-b1e1-ef413ec6f93b","kind":"agent"},"principal":{"personId":"person-ai4s"}},"digest":"sha256:559cd8b701d51013a55ada05ade42638e9a4a126248236830376827509e1770e","evidence":"手册锁定ESM-2 650M加one-hot；revision-report明确本地实时ESM，缓存与CPU兜底满足可复现约束，裁定成立。","pinId":"dcp_74c91a8f114e93907c3d10826d","pinnedAt":"2026-09-11T05:09:06.532Z","schema":"decision-content-pin/v1","state":"in_effect"}]
---

# 表征路线:ESM-2 650M 本地实时(L2 主力)+ one-hot(L1),嵌入缓存进仓库

## 背景
预提取"死表格"嵌入只能覆盖既有题库,Agent 提出新变体时会对不上;纯 one-hot 丢失 ESM 语义、指标上限低。而题目要求代码可在小规模数据上复现,不能硬绑特定 GPU。

## 裁定
表征走阶梯:one-hot(L1,80 维,CPU 秒级)作基线与兜底;ESM-2 650M 本地实时提取(device 优先 mps)作 L2 主力(1280 维)。ESM 嵌入缓存进仓库,使评委无 GPU 也能复现全流程。

## 影响
- T2 产出 one-hot 缓存(已完成)+ ESM 缓存(补齐中)。
- T3 三级 ladder 在 one-hot 与 ESM 上分别出指标,诚实对照。
- 复现:README 说明 ESM 缓存已随仓库提供,无 GPU 亦可跑 one-hot 全链。

## Judgment-only acceptance

手册锁定ESM-2 650M加one-hot；revision-report明确本地实时ESM，缓存与CPU兜底满足可复现约束，裁定成立。
