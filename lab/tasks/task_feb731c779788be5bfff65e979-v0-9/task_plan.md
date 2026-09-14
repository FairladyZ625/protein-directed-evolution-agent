# v0.9 工具契约改造:让残差证据有落点

## Brief

v0.8 2×2 证明:强制注入残差反思对 AAV agent 的提名**零影响**,四臂批次逐位相同
(48/48 × 6,两个采集档下皆然)。查代码后确认这不是模型缺陷,而是**工具契约的形状**:
agent 手上没有任何能表达「别选带 N21D 的候选」这类证据的参数。v0.9 改造契约,
让残差证据第一次有落点,然后重跑同一个 2×2,看结论是否翻转。

## Goal

把「反思是否改变提名」从一个**结构上不可能为真**的问题,变成一个**可以真的失败也可以真的成功**
的问题。判据不变:`agent.tool.test.residuals` 里 `records[].seq` 的集合哈希是否分叉。

## Context

v0.8 结论与四层根因见
`lab/tasks/task_91e931121d3ae400a0a2be246b-v0-8-aav/artifacts/factorial-2x2-seed42.md` 第 ④ 节,
以及 `lab/reports/REPORT-HANDOFF.md` §7.15(2026-09-13 二次修订版)。

四层原因,其中三层是本仓自己设的:
1. 提示词写着「Prefer that default」,round prompt 模板把 `compose_batch(n=48)` 写死、无 ratio 参数位
2. `_enforce_exploit_floor` 的地板(CV≥0.80→0.80,末两轮→0.90)恰好只禁止残差该触发的
   「调低利用比」方向;实测第 4 轮起可行区间为空集
3. **杠杆与证据不同构**:`exploit_ratio` 是标量,无法表达 motif 级排除(根因)
4. `test_composed_batch()` 无参数,连手工剔除候选都做不到

## Required Reading

- `agent/auto_researcher.py`:`SYSTEM_PROMPT`、`_V05/_V06_ACQUISITION_PARAGRAPH`、
  `compose_batch`、`_enforce_exploit_floor`、round prompt 构造(约 880–915 行)
- `events/reflexion.py`:`format_reflexion_prompt` 的 ACTION CONSTRAINT 措辞
- `scripts/run_v08_factorial.sh`、`scripts/compare_v08_arms.py`

## Entry Conditions

v0.8 四臂已完成并已推(`8df18c6`);`tmp/v08-factorial/` 下四个臂目录可作为对照基线。

## Dependencies

无外部依赖。需要 `gpt-5.6-sol` 可用、`LLM_TIMEOUT=240`。

## Execution Surface

`agent/auto_researcher.py`、`events/reflexion.py`、`tests/test_auto_researcher_contract.py`、
`scripts/run_v09_contract.sh`、`scripts/compare_v08_arms.py`(复用)。
**不动** `evolution/campaign.py` 与 `agent/pipeline.py`(另一条 workflow 线,不在本任务范围)。

## Constraints

- 不得改动 v0.8 四臂已产出的数据;新跑批落 `lab/reports/v09-contract/`(**2026-09-14 更正**:原写 `tmp/v09-contract/`,而 `tmp/` 在本仓 gitignored,该路径在任何提交树里都不存在;正式产物实际落点即 `lab/reports/v09-contract/`)
- 默认行为必须与 v0.8 逐位一致:新参数一律 opt-in,不传 = 老路径
- 每个新行为都要有守护测试,且**反向验证**(把修复打回原状确认变红)
- 不得为了让结论好看而放宽 gate 或 guardrail

## Checkpoint

契约改造 + 测试绿之后、开跑之前停一次,向 CEO 报「三处改了什么、默认路径是否 byte-identical」。

## CI/Gate Authority Stop Condition

本仓 `standard-task` 的 ci 门结构性不可满足(fact `F-8ED77039`,`rewrite-ci.yml` 404)。
**不得**新建 workflow、改 CI 配置或 `transition --force`;记录进度后停手,交 CEO。

## Implementation Plan

1. **`compose_batch` 加 `exclude_motifs: list[str] | None`** —— 让残差证据有落点。
   在 gate 过滤之后、打分之前剔除携带这些替换的候选;
   事件流记 `excluded_motifs` / `n_excluded` / `n_eligible_after_exclusion`。
   剔除后候选不足时不静默截断,回 `status="exclusion_too_strict"` 并附可用数。
2. **提示词中性化(opt-in)** —— 新增 `--prompt-neutral`:去掉「Prefer that default」,
   改为要求显式给出 `exploit_ratio` 并陈述依据;round prompt 模板暴露参数位。
   不传该开关时提示词与 v0.8 **逐字节相同**(加断言防漂移)。
3. **地板开关** —— 新增 `--no-exploit-floor`:实验臂放开 `_enforce_exploit_floor`,
   避免把因变量压成常数。默认仍启用。
4. **注入卡片指向新入口** —— `format_reflexion_prompt` 的 ACTION CONSTRAINT 改为
   点名 `exclude_motifs` 这个可用参数(仅在契约开启时)。
5. **跑 2×2**:契约(旧/新)× 反思(关/开),AAV,seed 42,288 预算,`--backtrack semi`。

## Deliverable Contract

- 代码:上述 4 处改造 + 守护测试,默认路径 byte-identical
- 数据:`lab/reports/v09-contract/` 四臂 metrics + 事件流(**2026-09-14 更正**,原写 `tmp/v09-contract/`;四臂齐全:`contract-v08_reflexion-off_seed-42`、`contract-v08_reflexion-on_seed-42`、`contract-v09_reflexion-off_seed-42`、`contract-v09_reflexion-on_seed-42`,每臂含 `agentic.metrics.json` 与 `agentic.events.jsonl.gz`)
- 文档:`artifacts/contract-2x2-seed42.md`(结果与引用纪律)+ REPORT-HANDOFF 新节

## Evidence Protocol

- 「默认路径未变」用**提示词字符串逐字节比对**与 v0.8 事件流对照证明
- 「批次是否分叉」只认 `agent.tool.test.residuals` 的 `records[].seq` 集合哈希
- 「agent 是否真的行使了新入口」看 `agent.tool.compose_batch` 的 `excluded_motifs` 非空计数
- 阴性对照保留:契约旧臂必须复现 v0.8 的「不分叉」

## Verification

`pytest tests/test_auto_researcher_contract.py -q` 全绿(2026-09-14 实测 **16 passed**);每个新测试反向验证过;
**路径更正(2026-09-14)**:本 plan 原先两处写的 `tests/test_auto_researcher.py` **从未存在过**——`tests/` 下实际是 `test_auto_researcher_backtrack.py`、`test_auto_researcher_compose.py`、`test_auto_researcher_contract.py`、`test_auto_researcher_gate.py` 四个文件,本任务的守护测试落在 `test_auto_researcher_contract.py`。独立评审指出该声明路径不存在,成立。
`python3 scripts/compare_v08_arms.py lab/reports/v09-contract` 输出四臂对照表(**2026-09-14 更正**:原写 `tmp/v09-contract`,按声明路径无法在提交树上复核;独立评审已用该更正后路径复算并确认 v08 开/关逐轮相同、v09 开/关分叉、v09 反思臂 `excluded_motifs` 非空 5/6)。
