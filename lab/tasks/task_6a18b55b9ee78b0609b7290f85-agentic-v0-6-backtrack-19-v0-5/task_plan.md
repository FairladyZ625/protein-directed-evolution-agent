# 把 agentic v0.6 的 backtrack 实现合进主线

## Brief

`lab/reports/agentic-v0.6/` 的实验数据在主线上,**但产生它的代码不在**。
分支 `t-v06` 的 commit `471536b`(meta-layer backtrack autonomy)从未合入 main:
`redirect_batch` / `top10_max_history` / `rounds_since_improvement` 三个关键机制在
`origin/main:agent/auto_researcher.py` 里出现 **0 次**,而在 `471536b` 上分别出现
10 / 9 / 6 次。`lab/reports/agentic-v0.6/report.md` 引用的
`tests/test_auto_researcher_backtrack.py` 在主线上根本不存在。

这是本仓同一形态的**第二例**。第一例是 `knowledge-ablation`(fact `F-94CBEC61`,
已修 `b78bac5`),当时 CEO 得出「这是唯一缺口」的结论 —— 那个结论是错的,
人工检查只覆盖了 metrics 类产物到生产脚本的映射。现在有脚本了:
`python3 scripts/check_data_has_code.py`,它正是抓出本任务的那个检查。

## Goal

`agentic-v0.6` 的数据变得可复现:代码在主线、测试在主线、报告里的复现命令能跑,
**同时 v0.5 的行为一个字节都不变**。

跑 `python3 scripts/check_data_has_code.py`,`agentic-v0.6` 那一行从 ❌ 变 ✅。

## Context

**这不是一次普通的落后分支合并,它有语义风险,先读懂再动手。**

v0.5 与 v0.6 是**并列变体,不是递进版本**(同类判断已记在 fact `F-84AE8976`:
agentic v0.6/v0.7 是 siblings 而非 progressive)。v0.6 刻意把默认采集策略从
「质量感知的 exploit/diverse 混合」改成了**纯预测均值利用**(报告里叫 rank-45 lesson),
并把唯一的逃逸手段收敛到 meta-layer 的 `redirect_batch` basin hop。

**如果把 v0.6 的默认行为直接合成主线默认,v0.5 的数据就不再可复现了** ——
那等于用修一个复现洞的方式制造另一个复现洞。

好消息:`471536b` 的作者已经预留了正确的形状。分支里有
`_V05_ACQUISITION_PARAGRAPH`(注释写明「v0.5 wording kept verbatim so the v0.5 prompt
is byte-identical when backtrack is off」)与 `_V06_ACQUISITION_PARAGRAPH`,
并且 `SYSTEM_PROMPT` 默认用 v0.5 那份。**沿用这个设计,不要自己另起一套。**

另一个复杂度来源:主线的 `agent/auto_researcher.py` 在 `471536b` 之后又前进了 ——
`b78bac5` 合入了 quality-aware adaptive acquisition(来自 `t-knowledge-ablation`)。
所以冲突是**两条真实演进线**的合并,不是简单的落后分支。`git merge master` 到
`t-v06` 上实测 19 处冲突,集中在 `agent/auto_researcher.py`。

## Required Reading

| 来源 | 为什么 |
|---|---|
| `git show 471536b` | v0.6 到底改了什么(提交信息本身写得很清楚) |
| `git diff master...t-v06 -- agent/auto_researcher.py` | 要合的那条线 |
| `lab/reports/agentic-v0.6/report.md` | v0.6 声称的结果与复现命令,合完要能跑 |
| `lab/reports/agentic-v0.5/report.md` | v0.5 的结果,合完**必须仍然可复现** |
| `agent/auto_researcher.py`(主线当前) | quality-aware acquisition 那条线 |
| `scripts/check_data_has_code.py` | 本任务的验收判据就是它 |

## Entry Conditions

worktree 与分支由 CEO 备好(见 Execution Surface),基于最新 master。
`.venv`、GB1 真值表、AAV 数据与 `features/cache` 已链接进去。

## Dependencies

无阻塞。CEO 正在并行跑 `workflow-v1.1` 的 llm regime,只写
`lab/reports/workflow-v1.1/gb1/campaign_llm.*`,与本任务文件面不重叠。

## Execution Surface

**可写**:`agent/auto_researcher.py`、`tests/test_auto_researcher_*.py`、
`lab/reports/agentic-v0.6/report.md`(只改其中失效的路径引用)。

**禁区**:
- `lab/reports/` 下任何 metrics / events / figures 产物 —— **不重跑、不覆盖**。
  本任务是把代码补回主线,不是重做实验。
- `lab/reports/workflow-v1.1/`(CEO 在写)
- `reports/final-report-v0.5/`(用户正在写的报告)
- `evolution/`、`knowledge/`、`models/`、`app/`

## Constraints

- **v0.5 的默认行为必须逐字节不变**。合完要能论证:不开 backtrack 时
  system prompt 与采集默认与合并前完全一致。这是本任务最硬的约束。
- **不要靠删代码来消冲突**。两侧都是有数据背书的真实演进线:
  master 侧是 quality-aware adaptive acquisition,v0.6 侧是 pure-exploitation +
  meta-layer redirect。**两者都要留下,由开关/变体参数区分。**
- **不重跑任何实验**。`agentic-v0.6/` 里的数字是 seed 42 的既有结果,不得改动;
  你的合并不需要复现它们。
- 若合并后发现 v0.6 的代码路径在当前主线上根本跑不起来(例如依赖了已被重构掉的接口),
  **带证据回报,不要为了让它跑而改产物或改数字**。

## Checkpoint

两个停手点,命中就带证据回报:

1. **发现无法同时保住 v0.5 默认行为与 v0.6 能力**(例如两侧对同一个函数有不相容的语义假设)。
   这是承重取舍,归 CEO 裁决,不要自己选一边。
2. **`471536b` 依赖的某个接口在主线上已不存在**,补回它需要动禁区文件。

## CI/Gate Authority Stop Condition

停止点 = 定向测试绿 + 本地 commit。**不 push、不发 PR。**

要跑的测试(**只跑这些**,同机还有其他进程,不要跑全量矩阵):

```
PYTHONPATH=. .venv/bin/python -m pytest -q \
  tests/test_agent.py tests/test_auto_researcher_gate.py \
  tests/test_auto_researcher_compose.py tests/test_auto_researcher_backtrack.py \
  tests/test_knowledge.py tests/test_campaign.py
```

注:本仓 `standard-task` 的 CI 见证门结构性不可满足(fact `F-8ED77039`)。
**不要新建 workflow、不要改 `.github/workflows/`、不要 `transition --force`。**

## Implementation Plan

1. `git merge master`(在 `t-v06` 基础的 worktree 里),或反向 —— 你判断哪个方向冲突更好解。
2. 逐个冲突块决定:哪一侧是承重的、能不能两侧共存。**默认答案是共存**。
3. 采集段落按分支已有的 `_V05_ACQUISITION_PARAGRAPH` / `_V06_ACQUISITION_PARAGRAPH`
   两份并存的形状收敛;默认仍是 v0.5 那份。
4. 把 `tests/test_auto_researcher_backtrack.py` 带进主线。
5. 修 `lab/reports/agentic-v0.6/report.md` 里指向不存在文件的引用
   (`python3 scripts/check_references.py` 会列出来)。

## Deliverable Contract

- 合并后的 `agent/auto_researcher.py`,两条能力并存。
- `tests/test_auto_researcher_backtrack.py` 在主线上且通过。
- 一条新测试**钉住 v0.5 默认行为不变**(例如断言默认 `SYSTEM_PROMPT` 含
  v0.5 那段 wording 而不含 v0.6 那段)。这条测试是本任务的核心交付物,
  没有它就无法防止将来有人把 v0.6 的默认悄悄变成主线默认。
- `lab/tasks/<本任务>/artifacts/merge-verification.md`:
  记录每个冲突块怎么判的、v0.5 行为不变的证据、以及你没能验证的部分。

## Evidence Protocol

- **v0.5 不变的证据要是可执行的**,不是"我看了一遍觉得一样"。
  做法:合并前后各导出一次默认 `SYSTEM_PROMPT` 到文件,`diff` 必须为空;
  把 diff 命令与输出贴进 `merge-verification.md`。
- **反向验证新测试**:临时把默认改成 v0.6 那段,新测试必须变红;改回必须变绿。
  **一条永远绿的测试等于没有测试。**
- 收尾跑 `python3 scripts/check_data_has_code.py`,`agentic-v0.6` 必须变 ✅。

## Verification

- CEO 会自己跑 `scripts/check_data_has_code.py` 与 `scripts/check_references.py`。
- CEO 会自己做一次 v0.5 默认 prompt 的 diff。
- CEO 会反向验证那条新测试(改默认 → 必须红)。
- CEO 会确认 `lab/reports/` 下没有任何产物被改动(`git diff --stat` 里不应出现)。
