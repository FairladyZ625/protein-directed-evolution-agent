# AAV agentic 版本矩阵：严格 48×6 统一复跑

## 预注册（实验启动前冻结）

- 数据与候选空间：`data/aav/full_data.csv`；clean 38,265，cold-start 固定为 HD≤2 的 10,433 条，未测池固定为 HD>2 的 27,832 条。v0.2/v0.4 使用历史门禁 HD≤4 且 mean BLOSUM62≥0（门内 9,533）；v0.1 不使用门禁。
- oracle：只在提名冻结后用本地 CSV 真值查表；峰身份、峰排名和未测标签不得进入采集、补批、早停或选参。
- 统一预算：每条轨迹严格 6 轮，每轮恰好 48 个互不重复的有效池内提名，总预算 288；不允许少花、跨轮挪用或第 7 轮。
- seeds：主矩阵预注册采集 seed 为 `[0, 7, 42]`。先以 seed 42 做协议 pilot；三 seed 终点 `cum_top10_max` 的样本标准差若超过 0.5，则按 `[1, 2, 3, 4, 5, 6, 8]` 依次补到 10 seed，且不按结果挑 seed。
- shortlist：候选工具单次最多返回 60 条；LLM 可在该上限内查看 predicted-mean、uncertainty、diverse 或 random 候选。
- 版本语义：v0.1 = 无门禁 + Ridge；v0.2 = Knowledge 门禁 + Ridge；v0.4-LLM = Knowledge 门禁 + EpistasisRidge。除此之外不统一 surrogate、门禁或 LLM 决策语义。
- 实际模型：请求模型字段固定记录端点实际解析值 `claude-sonnet-5`；同时记录 live LLM 轮数、LLM tool calls、round errors、harness 补批次数与 fallback 次数。
- 严格批次补齐：每轮 LLM 获得独立的 48 条额度；其多次 `test` 合计最多消费 48。若该轮有效提名不足 48，先保留 LLM 已测试候选，再由 harness 使用该版本当轮 surrogate 的 `predicted_mean` 排名从相同合法池补足；补批逐条标记 `driver=harness_fill`，不得伪装成 live LLM 提名。该规则只修复预算执行，不回退或删除已测标签。
- 新 schema：每轮保存全部 48 条提名的 sequence、HD、当时 predicted mean/variance、gate 判定与原因、driver、精确 oracle fitness；保存请求、拒绝与去重账本，使 288 条提名可逐条审计。
- 指标：主指标为新增测量的 `cum_top10_max`；同时报告 strong（fitness≥2.6159）与逐轮数量。shuffle-label cold-start held-out Spearman 是每个版本配置必跑的阴性对照，期望绝对值 <0.1；未达阈值必须如实标记。
- 锚点：正式 LLM pilot 前先复现 v0.4 deterministic 的历史调度（predicted_mean/diverse 交替）；只有 `cum_top10_max=8.4162` 且六轮各 48 才继续。

## 版本矩阵

第一次 checkpoint 只完成锚点与 v0.1 seed 42 pilot；由于实际解析模型在第 3–6 轮连续返回 `model_not_found`，按任务的异议型停点暂停，未铺开其余 seed/版本。

| 版本/记录 | 协议 | 实花 | surrogate | 门禁 | LLM | cum_top10_max | strong | 状态 |
|---|---|---:|---|---|---|---:|---:|---|
| v0.1 原始记录 | 声称 96×3；实际 test 批 `80/16/75/21/95/1` | 288 | Ridge | 无 | 历史模型标签不可信，待包 C 勘误 | 5.961 | 15 | 原始记录 |
| v0.1 seed 42 本次统一 pilot | 严格 `48/48/48/48/48/48` | 288 | Ridge | 无 | `claude-sonnet-5`：前 2 轮 live，后 4 轮 404 后补批 | **7.5301** | **57** | 本次复跑；不等于六轮全 live LLM |
| v0.4 deterministic 锚点 | 严格 `48/48/48/48/48/48` | 288 | EpistasisRidge | HD≤4 + BLOSUM62≥0 | 否；mean/diverse 交替 | **8.4162** | **151** | 本次复现锚点 |

v0.1 pilot 相对原始记录：`cum_top10_max +1.5691`，strong `+42`。变化同时包含严格轮协议和 192/288 个 harness predicted-mean 补批的影响，不能归因于 LLM 自主策略改善。

## Seed 方差与排序判定

未计算。只有 v0.1 seed 42 一个 pilot，且其中 4/6 轮不是 live LLM；在恢复稳定模型路由前继续跑 seed 0/7 会产生不可比混合点。版本排序是否翻转仍未验证。

## 证据与限制

- 锚点真实 runner：`round_counts=[48,48,48,48,48,48]`、`budget_spent=288`、`cum_top10_max=8.4162`、strong=151、24 events，哈希链通过。metrics SHA-256 `41ae9945a401c0d047c7b6bd81738f96e953fa638bc55c5b22d1cae7e0e144b0`。
- v0.1 真实 runner：`round_counts=[48,48,48,48,48,48]`、`budget_spent=288`、`cum_top10_max=7.5301`、strong=57、57 events，哈希链通过。metrics SHA-256 `fabf64a71eede9fa17696e1b1f5187fe5ce9c0671879a1a55ea4d8af6c4ec709`。
- v0.1 驱动归因：live LLM 96 条，harness fill 192 条；成功 live 轮数 2，round error 4，fallback campaign 0。第 2 轮另有 24 条无效/超额请求被拒且不扣预算。
- 四次错误均为网关 404：`Model "claude-sonnet-5" is not supported by any configured account in this group`。配置解析值和前两轮实际请求 ID 均为 `claude-sonnet-5`；网关背后的物理模型身份未独立验证。
- 阴性对照：Ridge cold-start 固定 80/20 held-out 正常标签 Spearman=0.908743；仅打乱训练标签后 held-out Spearman=0.054191，满足预注册的 `abs(rho)<0.1`。
- 独立账本审计：288 条提名唯一、全部属于 oracle 的 HD>2 池；HD 与 fitness 逐条精确匹配；预测均值/方差均为有限数；strong 和 max 可从全量账本重算；事件链验证通过。
- 治理阻塞：运行时注入的 `HARNESS_DAEMON_ENDPOINT` socket 不存在；`ha task show`/`ha task dispatches` 均返回 `daemon_start_runtime_forbidden`，因此本 checkpoint 无法写入 canonical fact 或 progress。未在 task-bound worker 内自行启动 daemon。
- 基线阻塞：已成功 `git fetch origin main`；当前 HEAD `cee742a3c57e53f803db41ff96f934054124c8a2` 与 `origin/main=be62937a8b7a7bc3e6e9e7d67fba33e67e8f3bc2` 无共同 merge-base，故无法安全 rebase，未强拼无关历史。
- 尚未完成：v0.1 的另外 seeds、v0.2/v0.4-LLM 统一复跑、seed 方差、v0.5/v0.6/v0.7 汇总、七版本总表与最终排序判断。
