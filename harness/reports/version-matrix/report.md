# AAV agentic 版本矩阵：严格 48×6 统一复跑

## 预注册（实验启动前冻结）

- 数据与候选空间：`data/aav/full_data.csv`；clean 38,265，cold-start 固定为 HD≤2 的 10,433 条，未测池固定为 HD>2 的 27,832 条。v0.2/v0.4 使用历史门禁 HD≤4 且 mean BLOSUM62≥0（门内 9,533）；v0.1 不使用门禁。
- oracle：只在提名冻结后用本地 CSV 真值查表；峰身份、峰排名和未测标签不得进入采集、补批、早停或选参。
- 统一预算：每条轨迹严格 6 轮，每轮恰好 48 个互不重复的有效池内提名，总预算 288；不允许少花、跨轮挪用或第 7 轮。
- seeds：主矩阵预注册采集 seed 为 `[0, 7, 42]`。先以 seed 42 做协议 pilot；三 seed 终点 `cum_top10_max` 的样本标准差若超过 0.5，则按 `[1, 2, 3, 4, 5, 6, 8]` 依次补到 10 seed，且不按结果挑 seed。
- shortlist：候选工具单次最多返回 60 条；LLM 可在该上限内查看 predicted-mean、uncertainty、diverse 或 random 候选。
- 版本语义：v0.1 = 无门禁 + Ridge；v0.2 = Knowledge 门禁 + Ridge；v0.4-LLM = Knowledge 门禁 + EpistasisRidge。除此之外不统一 surrogate、门禁或 LLM 决策语义。
- 第一轮模型记录：当时端点实际解析值为 `claude-sonnet-5`；第一轮 checkpoint 同时记录 live LLM 轮数、LLM tool calls、round errors、harness 补批次数与 fallback 次数。
- 第一轮严格批次补齐：每轮 LLM 获得独立的 48 条额度；其多次 `test` 合计最多消费 48。若该轮有效提名不足 48，先保留 LLM 已测试候选，再由 harness 使用该版本当轮 surrogate 的 `predicted_mean` 排名从相同合法池补足；补批逐条标记 `driver=harness_fill`，不得伪装成 live LLM 提名。该规则只适用于已经归档的第一轮 checkpoint，不进入正式矩阵。
- 新 schema：每轮保存全部 48 条提名的 sequence、HD、当时 predicted mean/variance、gate 判定与原因、driver、精确 oracle fitness；保存请求、拒绝与去重账本，使 288 条提名可逐条审计。
- 指标：主指标为新增测量的 `cum_top10_max`；同时报告 strong（fitness≥2.6159）与逐轮数量。shuffle-label cold-start held-out Spearman 是每个版本配置必跑的阴性对照，期望绝对值 <0.1；未达阈值必须如实标记。
- 锚点：正式 LLM pilot 前先复现 v0.4 deterministic 的历史调度（predicted_mean/diverse 交替）；只有 `cum_top10_max=8.4162` 且六轮各 48 才继续。

### 第二轮预注册修订（模型路由恢复后、正式矩阵开跑前）

- 端点于 2026-09-12 下架 `claude-sonnet-5`，现配置实际解析值为 `gpt-5.6-sol`；正式统一复跑的模型字段必须写 `gpt-5.6-sol`。历史 v0.1–v0.7 原始记录来自 `claude-sonnet-5` 时代。因此“原始记录”与“统一复跑”的差同时包含预算协议差异与 LLM 模型差异，**不得把差值单独归因给协议**。
- 正式矩阵仍用 seeds `[0, 7, 42]`、48×6、同池、同 cold-start、同 shortlist 上限与各版本原 surrogate/门禁。第一轮 v0.1 seed42 混合点不复用，三个版本的三个 seed 全部从空输出目录重跑。
- “全 live”接纳门：每条轨迹必须 `live_llm_rounds=6`、`llm_round_errors=0`、`harness_fill_nominations=0`、`fallback_count=0`，且 288 条 ledger 的 driver 全为 `live_llm`。若一次 live 响应未花满当轮额度，最多在同一消息历史内追加 3 次 live 请求要求补足；仍欠额或任一请求报错则该轨迹失败并停下，不用确定性策略补批。
- 已验收锚点 `anchor-v0.4-deterministic-seed42` 保留，不重跑；它是无 LLM 的 mean/diverse 交替复现点，不受模型路由变更影响。

## 版本矩阵

> **可比性边界（必须先读）**：历史“原始记录”产生于 `claude-sonnet-5` 时代；第二轮“统一复跑”请求的是 `gpt-5.6-sol`。两列之差同时混入预算协议变化与模型变化，不能把 delta 单独归因给预算协议，也不能据此声称某一 LLM 的普适优劣。

第二轮在已验收锚点上继续，完成 v0.1 的三个预注册主 seed；其终点方差触发扩展到 10 seed，但第一个扩展 seed 即无法满足全 live 的单轮固定预算，按异议型停点停止。因此下表是**中止时的证据矩阵**，不是七版本最终矩阵。

| 版本/记录 | 协议 | 实花 | surrogate | 门禁 | LLM | cum_top10_max | strong | 状态 |
|---|---|---:|---|---|---|---:|---:|---|
| v0.1 原始记录 | 声称 96×3；实际 test 批 `80/16/75/21/95/1` | 288 | Ridge | 无 | `claude-sonnet-5` 时代 | 5.9610 | 15 | 原始记录；协议不严格 |
| v0.1 seed0 统一复跑 | 严格 `48/48/48/48/48/48` | 288 | Ridge | 无 | `gpt-5.6-sol`；6/6 live，0 fill/fallback | 5.9610 | 48 | 本次统一复跑 |
| v0.1 seed7 统一复跑 | 严格 `48/48/48/48/48/48` | 288 | Ridge | 无 | `gpt-5.6-sol`；6/6 live，0 fill/fallback | 5.9610 | 36 | 本次统一复跑 |
| v0.1 seed42 统一复跑 | 严格 `48/48/48/48/48/48` | 288 | Ridge | 无 | `gpt-5.6-sol`；6/6 live，0 fill/fallback | **7.7497** | **55** | 本次统一复跑 |
| v0.1 seed1 扩展轨迹 | 第 1 轮目标 48，四次 live 请求后只测 46 | 46 | Ridge | 无 | `gpt-5.6-sol`；0 模型错误，0 fill/fallback | — | — | **预注册失败；中止，不纳入矩阵** |
| v0.4 deterministic 锚点 | 严格 `48/48/48/48/48/48` | 288 | EpistasisRidge | HD≤4 + BLOSUM62≥0 | 否；mean/diverse 交替 | **8.4162** | **151** | 本次复现锚点 |

v0.1 三条成功统一复跑的 `cum_top10_max` 为 `[5.9610, 5.9610, 7.7497]`，均值 `6.5572`、样本 SD `1.0327`；strong 为 `[48, 36, 55]`，均值 `46.33`、样本 SD `9.61`。相对原始单次记录，三个 seed 的 max delta 分别是 `[0.0000, 0.0000, +1.7887]`，strong delta 是 `[+33, +21, +40]`；这些 delta 都是模型与协议混合差，不作单因子解释。

## Seed 方差与排序判定

v0.1 三 seed max 样本 SD=`1.0327`，超过预注册阈值 0.5，依法触发 seeds `[1,2,3,4,5,6,8]` 扩展。seed1 第 1 轮第一次 `test` 请求 47 条，其中 1 条重复，实际测 46；随后三个 live 响应均未调用工具补余下 2 条。四次 live 请求上限耗尽后 runner 以 `abort_without_fallback` 退出。事件链共 7 条并通过哈希校验；没有 404/round error，也没有 deterministic/harness fill。

这证明 v0.1 裸 agent 在当前模型下并非每条轨迹都能遵守固定轮预算；强行提高事后重试上限或补 2 条会改变预注册协议。v0.2/v0.4-LLM 尚未启动统一复跑，v0.5/v0.6/v0.7 尚未汇总，所以“统一协议后版本排序是否翻转”目前**未验证，不能回答为是或否**。

## 证据与限制

- 锚点真实 runner：`round_counts=[48,48,48,48,48,48]`、`budget_spent=288`、`cum_top10_max=8.4162`、strong=151、24 events，哈希链通过。metrics SHA-256 `41ae9945a401c0d047c7b6bd81738f96e953fa638bc55c5b22d1cae7e0e144b0`。
- v0.1 seed0：max=5.9610、strong=48、71 events；metrics/events SHA-256=`9a23f4fbf992…`/`9f8ac2a1e10a…`。
- v0.1 seed7：max=5.9610、strong=36、64 events；metrics/events SHA-256=`a25f1e519615…`/`cb67d6c3feef…`。
- v0.1 seed42：max=7.7497、strong=55、49 events；metrics/events SHA-256=`2ec209ceafde…`/`6469d0dd7d96…`。
- 三条成功轨迹均为 288 条唯一、全 `driver=live_llm`、全部属于 HD>2 oracle 池；HD 与 fitness 逐条匹配，预测均值/方差有限，strong 与四位小数 max 可从 ledger 重算，事件链通过。
- 阴性对照：三条 Ridge 正常标签 held-out Spearman 均为 `0.908743`；shuffle 分别为 `-0.024522 / 0.004801 / 0.054191`，均满足 `abs(rho)<0.1`。
- 第一轮混合 pilot (`claude-sonnet-5` + 192 条 harness fill) 保留在 `reruns/v0.1-seed42/`，但不进入第二轮统一复跑统计。
- 已完成交付前 rebase：两条任务 commit 已安全重放到当时最新的 `origin/main=05d6e4d`，rebase 后全量 ledger 审计再次通过。
- 尚未完成：v0.1 扩展到 10 seed、v0.2/v0.4-LLM 统一复跑、v0.5/v0.6/v0.7 汇总、七版本总表与最终排序判断。继续需要 CEO 对 v0.1 全 live 欠额轨迹给出新的预注册裁定。
