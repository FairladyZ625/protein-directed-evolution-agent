# 知识库消融的更细粒度实验:门禁照常执行时,让 agent 也推理知识

> **状态:留档,本轮不执行。** 交付在即,CEO 明确「这次先做到这里」。
> 本任务记录一个已定位、未验证的缺口,供后续自研继续。

## Brief

现有的知识消融 `--no-knowledge` 把**整套机制**一起关掉(校验器 + 知识图谱 + HD/BLOSUM 门禁),
所以它测的是「有没有知识」。**从未测过「门禁照常执行,但 agent 自己也推理知识」。**

这个缺口是在核对试题覆盖时发现的:自主线 7 个工具里,`check_knowledge` 在 v0.8/v0.9
共八个实验臂中**一次都没被调用**。查代码后确认 agent 是对的——我们把这个动作做成了
可证明无用的:①系统提示词的工作流只点名四个工具,不含它;②门禁说明写着
「`compose_batch` 和 `list_pool` 已经只返回过门候选」,再查必然全过;
③唯一另一处提及是 `gate_rejected` 的错误提示,八个臂从未触发。

知识增强本身 **100% 生效**(门禁在 `test()` 里无条件执行,知识图谱 rationale 由
`compose_batch` 主动推送),只是**由环境强制,而非由 agent 查询**。当前设计是自洽的,
但**没有证据说明它是最优的**。

## Goal

回答一个当前无法回答的问题:**把「为什么这个候选被拒」回灌给 agent,它下一轮的
生成方向会不会改变?** 判据仍是送测集合的集合哈希,不是它说了什么。

## Context

- 契约结论与四层根因:`harness/tasks/task_feb731c779788be5bfff65e979-v0-9/artifacts/contract-2x2-seed42.md`
- 协议复现与第八章素材:`reports/final-report-v0.6/v07-handoff-02-protocol-and-chapter8.md` §8.x-2b
- 已确立的分界:**约束的执行归环境**(不可绕过、不花预算、无裁量);
  **证据驱动的选择归 agent**(需与证据同构、分辨率足够的入口)。
  本任务测的是第三类:**约束的「理由」要不要回灌给 agent**。

## Required Reading

- `agent/auto_researcher.py`:`check_knowledge`、`_gate`、`_graph_rationale`、
  `gate_note` 构造(约 939 行)、系统提示词的 workflow 段
- `knowledge/validators.py`:`validate_mutations`、`build_knowledge_graph`、
  `query_mutation_context`;`knowledge/rules.yaml`(含 advisory 的 `R-PHYSICOCHEMICAL`)
- `knowledge/ablation.py`:现有四臂消融的形状

## Entry Conditions

v0.9 契约已合入(`377a614`),四臂数据已归档(`harness/reports/v09-contract/`)。
本任务在其之上加一个正交因子,不改动契约本身。

## Dependencies

无外部依赖。需 `gpt-5.6-sol` 与 `LLM_TIMEOUT=240`。

## Execution Surface

`agent/auto_researcher.py`(新增回灌开关与拒绝理由事件)、`tests/`、
`scripts/`(新跑批脚本)。**不动** `evolution/campaign.py` 与 `agent/pipeline.py`。

## Constraints

- 门禁**始终执行**,本实验不得让 agent 有能力绕过它——这是安全属性,不是可调项
- 新开关一律 opt-in;不传时行为与 v0.9 逐字节相同(用提示词哈希与事件流对照钉住)
- 新数据落 `tmp/` 与新的 `harness/reports/<线>-v<版本>/`,不覆盖已有四臂
- 每个新行为都要守护测试 + 反向验证

## Checkpoint

实现完成、默认路径证明惰性之后,开跑之前停一次,向 CEO 报「改了什么、
默认路径是否 byte-identical」。

## CI/Gate Authority Stop Condition

本仓 `standard-task` 的 ci 门结构性不可满足(fact `F-8ED77039`,`rewrite-ci.yml` 404)。
**不得**新建 workflow、改 CI 配置或 `transition --force`;记录进度后停手,交 CEO。

## Implementation Plan

1. **拒绝理由入事件流**:`_gate` 拒绝候选时,除现有的 `n_rejected` 计数外,
   记录逐候选的**违反了哪条规则**(复用 `validate_mutations` 的 `rule_id` + `note`,
   现已含 advisory 的 `R-PHYSICOCHEMICAL` 跨类说明)。
2. **回灌开关 `--gate-feedback`**:开启时,把上一轮被门禁拒掉的候选及其理由
   摘要注入下一轮 prompt(形态复用 `events/reflexion.py` 的注入卡片,
   保证「注入了什么」可从事件流独立复核)。
3. **提示词点名 `check_knowledge` 的增量价值**:当前它相对 `compose_batch` 无增量,
   需要先让它有——例如允许对**尚未过门**的自拟候选做预检,并明确告知这一点。
   否则 agent 不调用它仍然是理性的。
4. **2×2**:`--gate-feedback` 开/关 × `--reflexion` 开/关,固定 v0.9 契约,
   AAV,seed 42,与既有四臂同协议(48×6),使两轮可比。

## Deliverable Contract

- 代码:上述三处 + 守护测试,默认路径 byte-identical
- 数据:四臂 metrics + 事件流,归档进版本化产物树
- 文档:`artifacts/` 下一份结果与引用纪律;REPORT-HANDOFF 新节

## Evidence Protocol

- 「批次是否分叉」只认 `agent.tool.test.residuals` 的 `records[].seq` 集合哈希
- 「回灌是否真的送达」看注入事件的字符数与来源轮次
- 「agent 是否真的用了」看 `check_knowledge` 调用次数 + `compose_batch` 的
  `excluded_motifs`/`exploit_ratio` 是否随回灌内容变化
- **阴性对照**:回灌关的两臂必须复现 v0.9 已有的对应臂
- **量化陷阱**:批量必须足够大,否则标量杠杆会被量化掉
  (n=12 时 `[0.875, 0.958]` 全部映射到同一分配),见 v07-handoff-02 §三

## Verification

`pytest -q` 全绿;每条新测试反向验证过;
`scripts/compare_v08_arms.py` 输出四臂对照表且阴性对照臂复现。
