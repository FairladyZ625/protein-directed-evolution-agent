# T4 事件流内核（前端回放底座 + 可审计链）

Task Contract: harness-task v1

## Brief

实现最小事件流内核：append-only jsonl + 链式 sha256 + fsync，SQLite 投影，replay CLI。它是 T8 前端「Agent 思考过程回放」的数据底座，同时提供可审计防篡改能力（二面差异化点）。

## Goal

`events/store.py`（append-only 写入 + 链式哈希 + fsync）、`events/project.py`（SQLite 单表+视图投影，可 rebuild）、`events/replay.py`（按轮/策略过滤→文本时间线 CLI）、`tests/test_events.py`。交付给 T7（写事件）与 T8（读回放）；第一个使用方：T7 campaign 进程。

## Context

- task：搭事件流内核。decision：event-stream 属交付层（前端要回放整个过程必须记录），非可砍层——泽宇裁定。fact：一面时对方明确重视可审计/可控/会失败，二面拿出为差异化。
- 事件 schema：jsonl 单行 `{seq,ts,event_type,round_id,strategy,actor,payload,prev_hash,hash}`。写侧唯一写者=campaign 进程；读侧=Streamlit 只读（严禁顶层 append）。

## Required Reading

1. `harness/context/architecture/AI4S-master-plan.html`（事件流内核节：链式哈希、投影、replay、写读分离）— 权威：设计。
2. `harness/context/research/AI4S-revision-report.md`（前端回放需求）— 权威：动机。

## Entry Conditions

- 无外部依赖，可 Day1 与 T2/T5 并行开工。

## Dependencies

- 上游：无。下游：T7（append 事件）、T8（replay 读取）。判定满足：T7 能 append 且 `verify()` 通过，replay CLI 能按轮/策略输出时间线。

## Execution Surface

独立 worktree + 任务分支，base=main。允许写入：`events/`、`tests/test_events.py`。绝对 cwd 由派工注入。文件面与 T2/T5 完全不重叠，可并行。

## Constraints

- 只做最小内核（约 200–300 行），不引入外部消息队列/数据库服务；SQLite 用标准库。
- 链式哈希 = `sha256(canonical(prev_hash + body))`；篡改任一事件后 `verify()` 必须报 `chain broken at seq=k`。
- 不承担业务语义（不懂 fitness/突变），只做通用事件流。外部/破坏性动作禁止。

## Checkpoint

命中即停：需触碰 T7/T8 文件面、或 schema 与 master-plan 冲突。计划回报点：store+verify 通过后、replay CLI 打通后。

## CI/Gate Authority Stop Condition

非 CI/gate 任务；需改门禁面则停止记 blocker。

## Implementation Plan

- `store.py`：append(event)→计算 prev_hash 链→fsync；`verify()` 全链校验。
- `project.py`：jsonl→SQLite 单表+视图，支持 rebuild（幂等）。
- `replay.py`：CLI 按 `--round/--strategy` 过滤输出人类可读时间线。
- 链头哈希预留锚进 git commit 的接口。
- `ha fact record` 晋升「链式校验可检出单字符篡改」。

## Deliverable Contract

代码 + `tests/test_events.py`（≥6 断言）。回报字段：事件 schema 字段、verify 篡改检出证据、replay CLI 用法。

## Evidence Protocol

阳性对照优先：先制造一次篡改让 `verify()` 出声，再证明正常链沉默。reviewer 拒收：verify 无篡改检出证据、写读未分离、schema 漂移。收口记一条 fact。

## Verification

- 停止点 = 便宜确定性门全绿 + 定向测试全绿 + 本地 commit。
- 定向测试：`tests/test_events.py`（append/链式哈希/fsync、投影 rebuild 幂等、replay 过滤、篡改检出阳性对照）；贴真实输出。
- 至少记录一条 fact。
