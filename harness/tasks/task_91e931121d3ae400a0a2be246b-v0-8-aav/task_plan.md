# v0.8 残差反思(AAV 主战场)

## Brief

RFC-008(`reports/v0.8-proposal-event-stream-reflexion.md`)提出给 agent 加两个机制:
跨轮次会话延续、事件流残差强制注入。**核查后这份 RFC 的前提有一半是错的**,
本任务按核准后的事实执行,不按 RFC 原文执行。

核准结论(证据见 Required Reading):

| RFC 主张 | 实际 | 本任务怎么办 |
|---|---|---|
| §2.1 需新增跨轮会话延续 | **已实现**,`agent/auto_researcher.py:842-843` 就是 RFC 伪代码本身 | **不动** |
| §2.2 需新增强制注入范式 | **已实现**,`auto_researcher.py:823-831` 每轮硬拼 `HARD STALL DETECTOR: STALLED=…` | **复用,只加内容** |
| §1.1「v0.5–v0.7 都无状态失忆」 | **对 agentic 线不成立**;只对 GB1 workflow 线成立 | 本任务不碰 GB1 |
| 第 1 步写 `events/reflexion.py` | **无米下炊**——残差数据在事件流里根本不存在 | **第 1 步改为扩 payload** |
| §4「致死变体重复提名率下降 80%」 | **结构性恒为 0**,测过的变体不可能被再提名 | **改 motif 级** |

**所以 v0.8 真正的增量只有一个:预测残差。** 在一个已经有状态、已经在强制注入的
agent 上,往注入内容里加一项「上一轮预测 vs 实测的打脸清单」。单变量,对照干净。

## Goal

AAV agentic 线具备一条闭合的认知反馈回路:上一轮的预测残差被记录进事件流、
被确定性地注入下一轮 prompt、并且**能用行为指标证明 agent 的提名确实因此改变**。

判据是三条可执行的检查,全部在 Verification 里写死。

## Context

**为什么这件事值得做**(三条,都不是修辞):

1. 试题考核重点第 4 条原文:「是否能把 LLM Agent 设计成『假设生成—突变设计—模型评估—
   **反馈迭代**』的科研流程」。当前系统的「迭代」是**环境在迭代**(预测器每轮重训、
   池子在长),**LLM 本身拿不到任何关于自己上一轮对错的反馈**。这是功能缺失,不是加分项。
2. 覆盖度审计把 H52「通过实验比较证明 Agent 作用」判为**部分交付**,缺口原话是
   「补同协议**多 seed 因子消融**」。
3. `reports/final-report-v0.6/report.md` §7.2 已把 v0.8 写成 future work,做了才算兑现。

**这件事的对立面也要写清**:本仓已有两条独立证据说 LLM 在优化内核里是负担 ——
AAV 30 seed 矩阵(greedy strong=166 达峰 0/30;UCB β=3 达峰 30/30 strong=128;
LLM-agentic 两个指标都没匹配上)与 GB1 `llm` vs `hard` 的阴性对照(agent 策略
strong −36% / 有益命中 −52%,而 random/greedy 两行逐位相同证明唯一变量就是 LLM)。

v0.8 是对「它输是因为它失忆」这个**具体机制假说**的检验,不是对 LLM 的翻案运动。
**两种结局都是好结果**:回路闭上且产出改善 → 机制假说成立;回路闭上但产出没改善 →
「给了记忆和残差反馈仍然不行」比「没给过」强得多。禁止为了让前者发生而调指标。

**治理约束**:决策 `dec_016C25D18F5C1C17F9A7173E75`(「LLM 自主在优化内核是负担」)
当前 `state=proposed`,**CEO 已明确在本实验出结果前不裁**。不要在任务里引用它作为既定结论,
也不要试图推动它 accept。

## Required Reading

| 来源 | 为什么 |
|---|---|
| `agent/auto_researcher.py:798,842-843` | 会话延续已实现的铁证,不要重复造 |
| `agent/auto_researcher.py:823-831` | 强制注入点,新内容拼在这里 |
| `agent/auto_researcher.py:518-545` | `compose_batch`:预测均值在这里算出,`state["pending_batch"]` 只存了序列 |
| `agent/auto_researcher.py:645-688` | `test()`:池子在 663 行被 drop,**提名时刻的预测在这之后就没了** |
| `agent/auto_researcher.py:555-566` | `emit` 把 `candidates` 排除在 payload 外 |
| `agent/auto_researcher.py:439-470` | `analyze_measured`,RSI / best / cluster 已在这里注入 |
| `events/store.py:26-57` | `resolve_stream_path` / `iter_stream`,只读消费用这两个,不要构造 EventStore |
| `harness/reports/workflow-v1.1/report.md` §④ | LLM 接入后变差的阴性对照,本任务的对立证据 |
| `reports/v0.8-proposal-event-stream-reflexion.md` | 原始 RFC。**读它是为了知道要改什么,不是照抄** |

## Entry Conditions

worktree `.worktrees/t-v08-reflexion`(分支 `t-v08-reflexion`,基于 master `e7fa48f`)由 CEO 备好。
AAV 数据与 `features/cache` 需链接进去(CEO 负责,缺了就回报,不要自己下载)。

## Dependencies

无阻塞。CEO 不并行改 `agent/` 下任何文件。

## Execution Surface

**可写**:`agent/auto_researcher.py`、`events/reflexion.py`(新建)、
`tests/test_reflexion*.py`(新建)、`tests/test_auto_researcher_*.py`、
跑批脚本(建议 `scripts/run_v08_arms.sh`)。

**禁区**:
- `evolution/campaign.py`、`agent/pipeline.py`、`app/demo.py` —— GB1 workflow 线本任务不碰
- `agent/llm.py` —— 改它的默认超时会让已发布的 v1.1 llm 档不可复现,见 Constraints ④
- `.env` —— worktree 里它是指向主树的软链,改它会污染主树
- `harness/reports/` 下任何既有 metrics / events / figures —— **不重跑、不覆盖**
- `reports/final-report-v0.5/`、`reports/final-report-v0.6/` —— 用户在写
- `knowledge/`、`models/`、`features/`

## Constraints

**① 残差必须取「提名时刻」的预测,不能取重训后的预测。**
这是本任务最容易出错、也最致命的一点。`test()` 在 `agent/auto_researcher.py:663`
执行 `state["pool"].drop(rows.index)` 并在 664 行把 `pred_cache` 置空。
**必须在这两行之前**从 `_pool_scores()` 取该批候选的 `mean`/`var`。
取重训后的预测算出来的不是「打脸」,是穿越。

**② 注入内容只能来自 agent 当时真的观测到的东西。**
不得把未测标签、全池分位、真峰身份以任何形式带进注入卡片。
本仓在 `harness/context/research/v07-constructive-conclusion.md` 里已明确警告过
「不能把未测标签算出的分位点透传给 agent」。**建议从事件流读残差而不是从内存 state 读**
—— 内存里什么都有,很容易顺手带进去;事件流里只有当时被记录下来的东西,是结构性防漏。

**③ 单因子。** 本任务只引入一个新变量:注入内容里多一段残差。
会话延续、强制注入范式、工具集、采集函数、预算协议、seed 全部保持不变。
**不要顺手改采集策略、不要调 STALL_THRESHOLD、不要加新工具。**

**④ 超时按 CEO 裁定放宽到 180–240 秒,但不得改全局默认值。**
当前 `agent/llm.py:54` 默认 90 秒、零重试,实测 Critic 成功率 54% / Hypothesis 50%,
主因就是 90 秒超时。CEO 原话:「超时完全可以调长,调到 3 分钟、4 分钟都可以,等着就好了」。

**但 `workflow-v1.1` 的 llm 档数据是在 90 秒下产出的**(fact `F-ABD9B83F` 记录了
27 实质 / 23 超时回退)。把默认值改成 240 秒,那份已发布数据就不可复现了。
所以:
- **不改 `agent/llm.py` 的默认值,也不改被 symlink 共享的 `.env`**
  (worktree 的 `.env` 是指向主树的软链,改它会污染主树)。
- v0.8 两臂通过**环境变量 `LLM_TIMEOUT=240` 显式设定**,并写进跑批脚本与 artifacts。
- **把生效的超时值 emit 进事件流**(`llm_timeout_s` 字段),让 provenance 自带口径,
  以后读事件流的人不必去猜当时是 90 还是 240。

**两臂必须用同一个超时值**,并逐臂记录 LLM 成功率——否则测出来的是端口差异不是认知差异。

**⑤ 指标改 motif 级。** 「同一个致死变体被重复提名」在两条线上都结构性不可能
(`auto_researcher.py:661-663` 把测过的行从池里物理移除)。
真正要防的是「同类构象重蹈覆辙」,所以指标定义为:
**第 t 轮提名中,携带「第 t−1 轮致死变体所含取代」的候选占比**。
致死阈值必须在跑之前写死进代码常量并在报告里声明,不得跑完再选。

## Checkpoint

三个停手点,命中就带证据回报,不要自己选一边:

1. **提名时刻的预测取不到**(例如 LLM 直接调 `test(variants=[...])` 传了池外序列)。
   这是语义问题:那些候选没有「提名时刻预测」。回报你的处理方案,不要静默填 0 或 NaN。
2. **放宽超时后成功率仍显著低于 90%**。那意味着端口本身不可靠,
   在它上面做的任何对照都测不出认知机制。带成功率数据回报。
3. **注入后 agent 行为完全没变**(motif 复现率两臂无差异)。
   这**不是失败,是结果**——立刻回报,不要通过加强 prompt 措辞去「修」它。
   反复改 prompt 直到出现想要的差异,那是调参调出结论,不是实验。

## CI/Gate Authority Stop Condition

停止点 = 定向测试绿 + 本地 commit。**不 push、不发 PR。**

要跑的测试(**只跑这些**,同机有其他进程,不要跑全量矩阵):

```
PYTHONPATH=. .venv/bin/python -m pytest -q \
  tests/test_reflexion.py tests/test_auto_researcher_backtrack.py \
  tests/test_auto_researcher_gate.py tests/test_auto_researcher_compose.py
```

注:本仓 `standard-task` 的 CI 见证门结构性不可满足(fact `F-8ED77039`)。
**不要新建 workflow、不要改 `.github/workflows/`、不要 `transition --force`。**
命中就记录进度后停手,交 CEO。

## Implementation Plan

**第 1 步:扩事件 payload(前置,没有它后面全是空中楼阁)**

在 `test()` 里、池子被 drop 之前,取该批候选的提名时刻 `mean`/`var`,
emit 一条新事件(建议 `agent.tool.test.residuals`,actor `experiment`),payload 至少含:
逐变体 `seq` / `predicted_mean` / `predicted_var` / `measured_fitness` / `residual`。
`agent.tool.test` 原有 payload 保持不变(向后兼容,既有解析器不能坏)。

同时处理 `compose_batch` 路径:`state["pending_batch"]` 只存序列,
需要一并把预测暂存下来,或在 `test()` 里统一从 `_pool_scores()` 取(推荐后者,两条路径同一套逻辑)。

**第 2 步:`events/reflexion.py`**

纯函数、无 LLM、无副作用。读事件流(用 `iter_stream`,**不要构造 `EventStore`**
——它的 `__init__` 会全量走一遍流恢复链尾,只读场景是浪费),产出结构化反思对象:
- `overestimated_fails`:预测高、实测低,按 |residual| 取 Top-k
- `underestimated_hits`:预测低、实测高
- `motif_summary`:上述变体所含取代的归并统计(供第 3 步的行动约束用)

RFC 里写的 `store.events(round_id=...)` **这个 API 不存在**,正确写法是
`select_events(iter_stream(path), round_id=…)`(见 `events/replay.py:13-20`)。

**第 3 步:接进注入点**

在 `auto_researcher.py:823-831` 已有的 `HARD STALL DETECTOR` 旁边追加残差段落。
用同样的确定性拼接方式,**不要**改成让 LLM 自己调工具查——
可选工具会让「这一轮到底查没查」变成不受控变量,直接污染对照。
注入卡片本身也要 emit 成事件(这样 demo 能回放「agent 当时被告知了什么」)。

**第 4 步:行为指标 + 阳性对照**

实现 motif 复现率指标。**必须有阳性对照**:构造一个已知会重蹈覆辙的合成轨迹,
证明该指标在那种情况下确实变高——一个永远读数为 0 的指标等于没有指标。

**第 5 步:单因子对照跑批**

两臂,除注入残差段落外一切相同:

| 臂 | 会话延续 | 强制注入(stall) | 残差注入 |
|---|---|---|---|
| A(对照) | 有(现状) | 有(现状) | **无** |
| B(处理) | 有 | 有 | **有** |

先跑 **1 seed 冒烟**确认管线通、且真的有残差被注入(看 prompt 日志),
然后**报 CEO 单次墙钟耗时**再决定 seed 数——不要自作主张跑长批。

## Deliverable Contract

- `agent/auto_researcher.py`:残差事件 + 注入段落,`agent.tool.test` 原 payload 不变。
- `events/reflexion.py`:纯函数解析器。
- `tests/test_reflexion.py`:含第 4 步的阳性对照。
- 一条钉住「提名时刻预测」的测试:构造重训会改变预测的场景,
  断言记录下来的 `predicted_mean` 是提名时刻那个值而不是重训后的值。
  **这条是本任务的核心交付物**,没有它就防不住将来有人把它悄悄改成穿越。
- `harness/tasks/<本任务>/artifacts/smoke-1seed.md`:1 seed 冒烟证据 +
  实际注入的 prompt 片段 + 单次墙钟耗时 + 逐臂 LLM 成功率。

## Evidence Protocol

- **每条新测试都要反向验证**:临时把修复打回原样,测试必须变红;改回必须变绿。
  把两次的输出都贴进 artifacts。**一条永远绿的测试等于没有测试。**
- **残差数字要能手工复核**:冒烟证据里挑 2 个变体,把
  「提名时刻预测 / 实测 / 残差」三个数与事件流原始记录逐一对上。
- **注入生效要有直接证据**:贴出第 2 轮实际发给 LLM 的 prompt 里那段残差文本,
  不是「我确认注入了」。
- LLM 成功率与超时次数逐臂报告,不合并。

## Verification

CEO 会自己做,不看自报:

1. 自己解 gz 事件流,确认 `predicted_mean` 与 `measured_fitness` 逐变体在案。
2. 自己反向验证「提名时刻预测」那条测试(改成取重训后预测 → 必须红)。
3. 自己反向验证 motif 指标的阳性对照。
4. 自己 diff `harness/reports/`,确认没有任何既有产物被改动。
5. 自己核对两臂除残差注入外的配置完全一致(超时、seed、预算、采集函数)。
