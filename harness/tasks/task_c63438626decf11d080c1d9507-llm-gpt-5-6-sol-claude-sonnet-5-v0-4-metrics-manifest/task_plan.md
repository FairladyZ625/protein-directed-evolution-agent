# 数据卫生修正:LLM 归属从 gpt-5.6-sol 改为实际解析模型 claude-sonnet-5

Task Contract: harness-task v1

## Brief

v0.7 红队线在审计中发现:`agent/llm.py` 实际解析到的网关模型 ID 是 `claude-sonnet-5`,而自 v0.4 起所有 metrics、manifest 与报告正文都标注为 `gpt-5.6-sol`。这是标签与实现不一致,属于必须修正的数据卫生问题——对外报告里说错自己用了哪个模型,是最容易被抓的一类硬伤。

## Goal

把所有 LLM 归属声明改为实际解析值,并在改动处留下可核的证据链(实际解析路径的代码位置 + 一次实跑的解析结果)。范围覆盖 v0.4 起的 metrics JSON、manifest、报告正文与图注。对已归档的历史报告采用**加勘误说明**而非改写原文,保留错误发生过的痕迹。

## Context

- 发现来源:v0.7 红队/多seed 批次的审计,记在 `harness/reports/agentic-v0.7/report.md` 与 `harness/context/research/v07-redteam-critique.md`。
- 本仓已有勘误横幅的先例:`harness/context/research/frontier-landscape-synthesis.md` 与 `harness/reports/agentic-v0.4/report.md` 顶部各有一条,照该格式写。
- 受影响面至少包括 `harness/reports/agentic-v0.4/`~`v0.7/` 下的 metrics 与 report,以及最终报告 v1.0/v2.0 的模型声明。

## Required Reading

1. `agent/llm.py`(**权威**:实际解析逻辑与返回的模型 ID)。
2. `harness/reports/agentic-v0.7/report.md`(**权威**:发现记录与影响面描述)。
3. `harness/reports/agentic-v0.4/report.md` 顶部勘误横幅(**格式范本**)。
4. 各版本 `*/aav/agentic.metrics.json` 与 manifest。

## Entry Conditions

能实跑一次 `agent/llm.py` 的模型解析并打印实际 ID。跑不出来就停下报——不得凭推断改标签。

## Dependencies

上游:v0.7 审计发现。下游:报告 v2.0(`task_db4ace109f72a92847c7349fe1`)必须用修正后的归属。并发:与报告 v2.0 有交集,**本任务先做**。

## Execution Surface

仓库根或独立 worktree;允许写 `harness/reports/**` 的勘误段与 manifest、`agent/llm.py` 的标签写入处(若确有写死)。禁区:实验数值本身(只改模型标签,不动任何 fitness/指标数)、CI/oracle。

## Constraints

- **只改标签,不改数据**。任何实验数值被动到即为越界。
- 历史报告加勘误,不覆盖原结论文字。
- 若发现某几轮确实用的是另一个模型,如实分版本标注,不做统一化简。

## Checkpoint

实跑解析拿到实际 ID 后即停并报(贴出解析输出),确认后再批量改。**异议型停**:若发现不同版本实际用了不同模型,停下来报清单再动手。

## CI/Gate Authority Stop Condition

非 CI/gate 任务。本仓 standard-task 的 ci 门结构性不可满足(`F-8ED77039`);不绕门、不改 CI。

## Implementation Plan

- 实跑解析,记录实际模型 ID 与解析代码路径。
- grep 全仓 `gpt-5.6-sol` 出现点,逐处判定是"标签写错"还是"确实指派了该 agent"(agent 声明里的 `de-ml` 用 sol 是对的,不要误改)。
- 改标签 + 给历史报告加勘误段。
- `ha fact record --task task_c63438626decf11d080c1d9507` 记实际模型与影响面。

## Deliverable Contract

修正后的 metrics/manifest/报告 + 历史报告勘误段;≥1 fact 记录实际模型 ID 与解析证据;回报:实际模型、改了几处、哪些 `gpt-5.6-sol` 是正确的不该改。

## Evidence Protocol

实际模型 ID 必须来自一次真实解析输出,不得来自推断或文档。区分"标签错"与"指派对"。

## Verification

停手点 = 改动落盘 + ≥1 fact + 实跑证据。CEO 语义验收:是否只动标签没动数据。
