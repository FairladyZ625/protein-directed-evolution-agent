# V0.6 对抗分析:LLM 停滞机制 + backtrack 能否达峰 + redirect 判据(纯高均值 vs 换构成)

Task Contract: harness-task v1

## Brief

只读对抗式分析(不改产品代码)。独立回答三问,给 CEO 一份判据分析文档,用于验收/修正正在并行开发的 V0.6 backtrack 机制。核心争议:**既然确定性纯 greedy(不换区)就能到 8.416,LLM 的失败模式到底是"走错盆地"还是"利用不足"?若是后者,V0.6 的正确 redirect 判据应是"直奔最高预测未测区",而非 CEO 初稿里的"换不同突变构成"。**

## Goal

产出 `harness/context/research/v06-backtrack-analysis.md`,用 answer-agnostic 证据回答:
1. **停滞机制**:LLM 在 v0.4(停 7.829)/v0.5(停 6.53)时,已测集卡在什么突变构成簇?停滞时刻 surrogate 对未测高均值变体的排名/预测分布是什么样?它到底是"没去测高均值区"(利用不足)还是"高均值区被 surrogate 低估"(走错盆地)?
2. **backtrack 能否达峰**:后验诊断(可参照确定性 greedy 达 8.416 的已测轨迹作为参考,但结论不得反哺任何在线机制)——一个"停滞→redirect"的 agent,在本地形上有没有可达 8.416 的合法路径?
3. **redirect 判据对比**:对比两种 answer-agnostic 逃逸判据——(a)**纯高均值未测区**(直奔 predicted_mean 顶端、忽略构成),(b)**换构成 basin-hop**(高均值 + 突变构成远离当前最优簇)。哪个更可能在本地形达峰?预测 V0.6 full/semi 两变体的结果与失败模式。给出对 GLM 实现的明确建议(判据该用哪个/怎么组合)。

交付形态:一份分析文档(≤ ~400 行),结论优先、附实测数字与命令。首个消费者:CEO(用于 V0.6 验收与可能的判据修正)。

## Context

- **v0.4/v0.5 事实**(`harness/reports/agentic-v0.4/report.md`、`harness/reports/agentic-v0.5/report.md`,facts F-851790B5/F-C08A6CF2/F-8A58F305/F-F7BC7554):同 EpistasisRidge(CV 0.90)下,确定性 gated-greedy 288 预算直达 8.416(strong 151);LLM v0.4 停 7.829、v0.5 加自适应配比反降 6.53。v0.5 机制=rank-45 截断(4.2% 早期探索税带离纯 greedy 路径)。
- **CEO 假设(要你证伪/证实)**:本地形上 greedy 纯利用即达峰 → LLM 病是**利用不足/过度探索**,不是被 surrogate 骗进错盆地 → V0.6 的 redirect 判据应偏向"纯高均值未测",而非"换构成"。
- **V0.6 正在并行开发**(GLM,`agent/auto_researcher.py`,task_2e485a1ae862bdec5fcc7c9677):C+A 保留 + 停滞检测 + redirect_batch,full/semi 两变体。你的分析用于验收/修正它。
- **前沿定位**(`harness/context/research/frontier-landscape-synthesis.md`):元层自主(判停滞+换策略)是 LLM 可能有价值的一档;微观选点 LLM 弱。

## Required Reading

1. `harness/reports/agentic-v0.5/report.md` + `harness/reports/agentic-v0.4/report.md`(**权威**:停滞曲线、rank-45、8.416 机制)。
2. `harness/reports/agentic-v0.4/aav/agentic.events.jsonl`、`agentic.metrics.json`、`deterministic.metrics.json`(v0.4 LLM vs 确定性 greedy 的实测轨迹与已测集)。
3. `harness/reports/agentic-v0.5/aav/agentic.events.jsonl`、`agentic.metrics.json`(v0.5 停滞轨迹)。
4. `agent/auto_researcher.py`(**只读**:_pool_scores/_gate_variants/compose_batch/surrogate_status,理解已有采集与门禁)。
5. `models/train_ladder.py`(EpistasisRidgePredictor:one-hot degree-2 + val_spearman)。
6. `evolution/datasets.py`(AAV 池/cold-start/oracle 加载口径)。

## Entry Conditions

- worktree(t-analysis)从 v0.5 HEAD 分叉,`.venv`+`data/aav/full_data.csv` 已 symlink(可跑 `PYTHONPATH=. .venv/bin/python`)。
- 未满足即停并报。

## Dependencies

- 上游:v0.4/v0.5 report + metrics + events。
- 下游:CEO(V0.6 验收/判据修正);GLM 的 V0.6 实现(你的建议可能改它)。
- 并发所有权:**GLM 正在 t-v06 改 `agent/auto_researcher.py`——你禁止改任何产品代码,只写分析文档;你的 worktree 是独立 checkout,天然无冲突,但结论落文档不落代码。**

## Execution Surface

- 分支 t-analysis(base=v0.5 HEAD);dispatcher 注入 cwd。
- **允许写范围**:仅 `harness/context/research/v06-backtrack-analysis.md`(+ 你自己在 `.worktrees/t-analysis` 内的临时分析脚本,不进产品树)。
- 禁区:`agent/`、`models/`、`tests/`、任何 report 树、CI/oracle——**全只读**。
- 运行时已预置:`.venv`、`data/aav/full_data.csv` symlink 好。

## Constraints

- **answer-agnostic 硬红线**:任何"在线机制建议"只能依据已测标签 + surrogate 预测 + held-out CV;可用确定性 greedy 的已测轨迹作**后验诊断参照**(它本身是 answer-agnostic 跑出来的),但**不得把测试峰坐标直接当作机制输入**去建议。区分清楚"诊断用了什么"和"你建议的在线机制用什么"。
- 不改任何产品代码/测试/oracle;只写分析文档。
- 不做外部/破坏性动作。
- 诚实:若证据表明 CEO 假设错了(其实是走错盆地),如实说,别迎合。

## Checkpoint

- 写完分析文档即停并报,回结论摘要(3 问的答案 + 对 GLM redirect 判据的明确建议)。
- 异议型停:若你发现 V0.6 整个方向有更好替代(不是 backtrack),带证据 challenge。

## CI/Gate Authority Stop Condition

非 CI/gate 任务(docs-task 无 CI 门)。不碰 CI/门禁/oracle。

## Implementation Plan

- 读 v0.4/v0.5 的 events + metrics,重建 LLM 停滞时刻的已测集与 surrogate 状态(可在 t-analysis 内写只读脚本,用同 cold-start 重拟 surrogate 复现每轮预测)。
- 诊断 1(利用不足 vs 错盆地):停滞轮次,LLM 已测集 vs 该轮 surrogate 的 predicted_mean top-N;统计"LLM 有没有测过高均值区"、"真值达 8.416 的变体在该轮 surrogate 的预测排名"(参照 v0.4 诊断 #2776→#447 口径)。
- 诊断 2(jud据对比):对停滞态,模拟两种 redirect——(a)纯 predicted_mean 未测 top-48,(b)高均值+构成远离最优簇 top-48——各自 batch 真值 max 与是否包含达峰路径变体。只读、后验、不反哺。
- 阴性对照:在"持续上升"的合成轨迹上验证停滞检测不误触发(若涉及)。
- 写 `harness/context/research/v06-backtrack-analysis.md`:结论优先 + 每个数字附命令 + 对 GLM 的建议(判据 a/b/组合)。
- 台账:`ha fact record --task task_e2eab881832291e8f8f73f30a4 ...` 记承重诊断结论(≥1 fact)。

## Deliverable Contract

- `harness/context/research/v06-backtrack-analysis.md`(结论优先,≤~400 行,附实测数字与复现命令)。
- 完成回报:3 问答案摘要 + 对 GLM redirect 判据的明确建议 + 预测 V0.6 full/semi 结果。
- 只写文档,不动产品代码;不 push 不 PR。

## Evidence Protocol

- 每个结论附实测数字 + 命令;区分"实测/复现"与"推断"。
- 后验诊断可参照 greedy 轨迹,但建议的在线机制必须 answer-agnostic,明确标注边界。
- ≥1 fact 记承重结论。

## Verification

- 停手点 = 分析文档写完 + ≥1 fact + 回结论摘要。无代码改动,无需定向测试;若写了分析脚本,贴其真实输出。
- CEO 语义验收(结论是否 answer-agnostic、判据建议是否有实测支撑)不可下放。
