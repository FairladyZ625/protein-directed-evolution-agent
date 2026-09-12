# AI4S Research Context

本目录是 AI4S 定向进化项目的**研究上下文入口**。它不是临时资料堆，而是 Harness Anything `research` Artifact Entity 的内容载体。

## 给 CEO / Worker 的阅读顺序

1. `AI4S-assignment.md`：先理解题目、交付要求和四策略对比。
2. `AI4S-revision-report.md`：读取当前最新裁决，旧方案与它冲突时以它为准。
3. `AI4S-domain-research.md`：补齐 GB1、DMS、fitness、epistasis、主动学习领域知识。
4. `AI4S-technical-plan.md`：理解端到端工程方案与里程碑。
5. `python-agent-runtime-comparison.md`：理解为什么 Agent Runtime 选 PydanticAI。
6. `event-stream-kernel-design.md`：实现审计事件流、verify 与 replay 时阅读。
7. `pi-sdk-ui-research.md`：了解 π SDK 取舍及前端壳研究；π 不是本项目主运行时。
8. `../architecture/AI4S-master-plan.html`：面向人类的整体架构和教学版作战图。

## 已拍板边界

- 主数据集：FLIP/GB1 完备组合数据，149,361 个变体；作为虚拟实验 oracle。
- 表征：`esm2_t33_650M_UR50D` 本地实时提取，1280 维；不得退回预提取死表。
- Runtime：PydanticAI；仅策略 3/4 使用 LLM，策略 1/2 保持确定性。
- 前端：Streamlit，展示四策略曲线、五角色事件回放和任意序列试玩。
- 事件流：独立 Python 内核，必须保留 append-only、hash-chain verify、replay；只能称 tamper-evident。
- 开发治理：Harness Anything 管项目上下文、任务、CEO/Worker 派工；最终交付物不依赖 HA daemon。
- 运行方式：本机 `.venv` + Makefile 为主；Docker 仅可作为后续 CPU 复现补充，不承诺 MPS。
- 凭证：只允许环境变量；不得写入 Git、Entity 或报告，任何示例值使用 `[REDACTED]`。

## Registered Research Entities

`research` 是当前 `software/coding` vertical 已声明的 Artifact Entity kind（稳定 kind ref：`entity-kind/KND-3b7e2c9a1d5f6e8c0a4b2d3f5e7c9a16`）。本项目没有重复造第二个同名 kind，而是为每份可独立引用的研究资产注册一个 Entity instance。

- `RES-5a7b721cc78b28854f8b4d5105091b92` — 笔试题原文镜像
- `RES-89863ee83811c1a74a3d6981a02d3ec7` — 蛋白质定向进化领域 Research
- `RES-64477fdb9f6c80b62c2ab1c6f2ca099e` — 技术方案
- `RES-524fbd368d18cf801e4e4fac7527de53` — 事件流内核设计
- `RES-a9fe1c856499dc51dbdcc34dc6352933` — Python Agent Runtime 对比
- `RES-7c7c6909eb48d15ea183e04873fd3072` — π SDK 与前端壳研究
- `RES-c4b8f0315d176594f87470080b31f3ee` — 方案修订与精进报告

这些 Entity 已通过 `ha entity import --kind research` 进入 HA 账本，并以 15 条 `relates` 关系精确关联到 M1–M4，避免把所有资料全连接成噪音。

## 来源与真相边界

- 题目原件和正式求职材料仍以 ZeYu-AI-Brain 为人类侧真相源。
- 本目录是供项目 Agent 使用的、纳入 Git 的可复现快照；若 Brain 原件变化，必须重新复制并用该 Entity 的当前 version 执行 `ha entity import`，不得悄悄覆盖而不更新账本。
- `AI4S-revision-report.md` 是当前方案裁决层；早期 research 中未被明确推翻的科学事实仍可使用。
