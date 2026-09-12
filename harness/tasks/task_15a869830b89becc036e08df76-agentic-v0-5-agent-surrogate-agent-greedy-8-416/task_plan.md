# 实验四/agentic v0.5:优化 agent 决策(surrogate 质量感知采集/修工具脆弱)让自主 agent 追平 greedy 8.416

Task Contract: harness-task v1

## Brief

在 v0.4 的上位感知 surrogate(EpistasisRidgePredictor,CV Spearman 0.90)之上,改造 LLM agent 的决策接口与提示词,缩小"LLM 自主 7.829 → 确定性 gated-greedy 8.416"的差距,并把差距的机械成因钉死。全程 answer-agnostic。

## Goal

**可验证结果**:在同池(27832)/同 cold-start(10433,HD≤2)/同 288 预算(48×6)/同门禁(HD≤4,BLOSUM62≥0)/seed 42/同 EpistasisRidge surrogate 下,跑 v0.5 LLM agentic,cum_top10_max **显著高于 v0.4 的 7.829**(理想追平 8.416,退而求其次是有据可查的缩小),并给出事件流证据说明改法为何生效/为何仍差。

**交付形态与落点**:
- 代码改动落 `agent/auto_researcher.py` + `models/train_ladder.py`(暴露 val_spearman);新单测落 `tests/`。
- 结果落 `harness/reports/agentic-v0.5/`(自包含 Report 文件夹:report.md + manifest.json + aav/ metrics/events/figures),沿用 v0.4 的极简 Report 结构。
- **首个消费者**:CEO(泽宇)验收 + 最终笔试报告的"v0.5 收敛"一节。

## Context

- v0.4 实测(权威,`harness/reports/agentic-v0.4/report.md` + manifest.json):同 surrogate 下确定性 gated-greedy 288 预算直达真峰 8.416(strong 151);LLM agentic 止步 7.829(strong 108);12 轮(576)仍 7.829、16 轮(768)反降 7.53。**更多轮次/预算无助 LLM 达峰,证短板是利用效率非 runway。**
- 三大前沿共识(权威,`harness/context/research/frontier-landscape-synthesis.md`,fact F-EE89324D):LLM 增益在上游/外围;利用步自主决策 ≤ 固定采集函数(2509.21403 对反馈不敏感、2502.00225 利用弱于线性回归);救 LLM 的办法一律是"去自主化/套 BO 不确定性框架"(2504.06265)。
- **V0.5 的诚实目标不是"证明 LLM 超 greedy"(共识说大概率不能),而是缩小差距 + 钉死机械成因。** 这是一个对齐前沿裂缝的、有价值的实验。
- 两份互不透题的独立研究(GLM + Gemini)收敛到同一套 3 条改法 C→A→B(见下 Required Reading)。
- **三条 fact 基线**:F-851790B5(上位假设)、F-C08A6CF2(诊断 #2776→#447)、F-8A58F305(破顶 7.829/8.416)。

## Required Reading

按顺序读,标注权威级:
1. `harness/context/research/v05-agent-optimization-gemini.md`(**权威·实现级**:四病灶事件流诊断 + 精确代码 diff:`_gate()` 越界修法用 `zip(spec.wt,v)`+长度检查、`_clean_seq`、四层防御、compose_batch 签名、退火配比公式、prompt 重构草案、surrogate_status 字段规格)。
2. `harness/context/research/v05-agent-optimization-glm.md`(**权威·佐证**:独立收敛的同 3 提名,交叉印证)。
3. `agent/auto_researcher.py`(**待改主体**:现有 `_gate()`(~line 90 索引越界)、SYSTEM prompt 中"surrogate IMPERFECT ~0.6"负向锚定、`analyze_measured`/`list_pool` 工具、`_make_surrogate`/`_pool_scores`)。
4. `models/train_ladder.py`(**待改**:`EpistasisRidgePredictor.fit()` 内部已算 held-out best_s,需绑 `self.val_spearman` 暴露)。
5. `harness/reports/agentic-v0.4/report.md` + `harness/reports/agentic-v0.4/aav/*.events.jsonl`(**权威·基线**:复现 7.829/8.416 与事件流诊断,新结果对照)。
6. `harness/reports/agentic-v0.4/manifest.json` 与 `agentic-v0.4/report.md` 的复现命令块(**权威**:v0.5 沿用同池/同预算/同 seed,只改 agent 决策层)。

冲突解决:Gemini 文件为实现级权威(diff 更细),GLM 为佐证;两者一致处即定稿,不一致处以事件流实测 + answer-agnostic 纪律裁。

## Entry Conditions

- v0.4 代码在仓库主线可复现(`--surrogate epistasis --guardrail`)。
- EpistasisRidgePredictor 在 `models/train_ladder.py`,fit ~6s。
- 独立 worktree 已由 dispatcher 注入 cwd。
- 未满足即停并报,不要自造缺失上游。

## Dependencies

- 上游:v0.4 实现(已合入主线)、两份 V0.5 研究文档(已落 research/)、frontier synthesis(已落)。
- 下游:CEO 语义验收 + 最终笔试报告。
- 并发所有权:无其他 worker 在改 `agent/auto_researcher.py` 或 `models/train_ladder.py`。

## Execution Surface

- 仓库:ai4s-directed-evolution-agent;base=main;独立 worktree + 任务分支(dispatcher 注入绝对 cwd)。
- **允许写范围**:`agent/auto_researcher.py`、`models/train_ladder.py`、`tests/`(新增测试)、`harness/reports/agentic-v0.5/`(新结果树)。
- 禁区:v0.1-v0.4 的既有 report 文件夹(只读对照,不覆盖);CI/门禁配置(protected surface);其他任何文件面。
- **运行时已预置(别重建)**:本 worktree 的 `.venv`(→ 主仓 .venv)与 `data/aav/full_data.csv`(→ 主仓 oracle 查表)已 symlink 好,直接 `PYTHONPATH=. .venv/bin/python -m ...` 即可跑;V0.5 用 epistasis one-hot surrogate,不需要 ESM 缓存。已冒烟验证 `load('aav','one_hot')` + `EpistasisRidgePredictor` import 通过。

## Constraints

- **answer-agnostic 是硬红线**:surrogate 特征只用 one-hot(位点×残基),训练标签只用已测(cold-start + 逐轮所测);CV/val_spearman 由 held-out 预测精度算,**绝不按目标峰排名调参、绝不看测试峰成分**。任何"上帝视角"手段一律禁止(这是刷分/过拟合,不是解决问题)。
- **保留上一轮结果**:v0.4 及更早 report 全保留,v0.5 落新文件夹,不覆盖。
- 不改 oracle、不改池/cold-start/预算/门禁/seed(唯一变量是 agent 决策层:prompt + 采集接口 + 工具鲁棒性)。
- 不做外部/破坏性动作;未分配文件面不写。

## Checkpoint

- 停手上报点:(1) C+A+B 三改法实现完 + 单测绿 + v0.5 LLM campaign 跑完拿到 cum_top10_max 后,先落盘再报,**不 push、不开 PR**(PR 面归 CEO);(2) 若发现改法与 answer-agnostic 纪律冲突,立即停并报,不自行放宽。
- 异议型停:若实测发现 C→A→B 某条无效或有害(如 compose_batch 反而降分),带事件流证据 challenge,不硬套。
- 越界即停:任何需要改门禁/CI/oracle 才能提分的路径,停并报——那是刷分信号。

## CI/Gate Authority Stop Condition

本任务非 CI/gate/governance 任务。若发现必须改 CI/gate authority surface 才能过,停实现、记 blocker、请 CEO 建治理任务。不得削门、绕 check、调 oracle。

## Implementation Plan

按 **C→A→B** 顺序(C 零风险底座先合,A 拨乱反正,B 建数学护栏):

**C 工具鲁棒性(先做,~15-20 行)**:
- 修 `_gate()` 越界:加 `_clean_seq(s)`(strip/upper/去空格换行);长度 `!=len(spec.wt)` 优雅拒(结构化理由),不抛异常;用 `zip(spec.wt, v)` 替代 `spec.wt[i]` 索引。
- 突变代号混淆(如传入 "D0Q")友好提示;关键工具入口(test/predict/list_pool)顶级 try-except 兜底返回结构化错误。
- 单测:29aa/空格/换行/突变代号 输入不再 `string index out of range`,返回结构化拒。

**A 认知纠偏 + CV 透传**:
- 删 SYSTEM prompt 里"surrogate IMPERFECT (~0.6)...systematically underrates...Do NOT blindly test its top predictions"整段负向锚定;换入证据校准准则:CV≥0.80 时重点利用 predicted_mean(≥80% batch),CV<0.65 时才分配探索,最后 2 轮强制 ≥90% 利用。
- `models/train_ladder.py`:`EpistasisRidgePredictor.fit()` 把 held-out best_s 绑 `self.val_spearman`。
- `analyze_measured()` 输出加 `surrogate_status` 节点(architecture / cv_spearman / confidence_level / recommendation),显式透传给 agent。

**B 自适应配比采集**:
- 新增 `compose_batch(exploit_ratio, n=48)` 工具(或 `list_pool(by="adaptive")`):底层按 exploit_ratio 分配——前 n×ratio 给 predicted_mean 降序,余额给门禁内 diverse/uncertainty;去重后返回预览。
- 自适应缺省:`exploit_ratio = min(1.0, max(0.4, val_spearman**2 + (rnd/n_rounds)*0.3))`(answer-agnostic,只用 CV + 轮次);prompt 引导 agent 用 compose_batch 定 ratio 而非逐条选。
- 单测:XOR/合成场景验 compose_batch 配比正确、高 CV 退火到近纯贪心。

**跑 v0.5 campaign**:同 v0.4 复现命令,`--surrogate epistasis --guardrail --budget 48 --n-rounds 6 --seed 42 --model gpt-5.6-sol`(version 逻辑加 v0.5);拿 cum_top10_max + 事件链校验 + explore/exploit 计数对照 v0.4。落 `harness/reports/agentic-v0.5/`。
- 台账:`ha task progress append` 记关键进展;`ha fact record --task task_15a869830b89becc036e08df76` 记 v0.5 实测结果(≥1 fact,满足完成门)。

## Deliverable Contract

- 代码:`agent/auto_researcher.py`(C+A+B)、`models/train_ladder.py`(val_spearman)、`tests/test_*`(gate 鲁棒性 + compose_batch)。
- 结果:`harness/reports/agentic-v0.5/report.md`(破/追平叙事,含 v0.1→v0.5 对照表 + explore/exploit 计数对比 + 事件流机制)+ manifest.json + aav/ 产物。
- 完成提交(submit)带:completionClaim、deliverables、outputs(fact id + report)、verificationNotes(实测命令 + 真实 runner 输出)、commitSha。
- 本地 commit 为止,**不 push 不开 PR**。

## Evidence Protocol

- 证据粒度:cum_top10_max 曲线 + strong 命中 + 事件链校验(50+ 事件)+ explore/exploit 计数(对照 v0.4 的 exploit 9/explore 19)。
- 阴性对照:C 前后各跑一次证 0 崩溃;A 前后对比 explore 比例下降;B 的 exploit_ratio 在高 CV 下退火到近 1.0。
- 诚实纪律:若 v0.5 仍不达 8.416,如实写负结果 + 机械成因(这本身有价值,共识预期 LLM 难超 greedy)。不得为凑分改 oracle/门禁/seed。
- reviewer 拒收条件:任何 answer-agnostic 违规、覆盖旧 report、削门凑分。
- 闭环:`ha fact record --task task_15a869830b89becc036e08df76 ...` 记实测,收据存 Execution outputs。

## Verification

- 停手点 = 触碰面定向测试绿 + 本地 commit(不 push/不 PR)。
- 定向测试集:(1) `tests/test_auto_researcher_gate.py`(gate 鲁棒性,含新 29aa/突变代号用例)、`tests/test_epistasis_surrogate.py`(surrogate 接口不回归)、新增 compose_batch 测试;(2) `git grep` 改动的工具名/错误码/字段名(surrogate_status、compose_batch、val_spearman),跑到的消费者测试。
- 贴真实 runner 输出,不写"all green"。
- 完成门:`code-doc-reconciliation` 要求 ≥1 fact,已在 Implementation Plan 用 `--task` 记 fact 满足。
- 附加人评:CEO 语义验收(v0.5 是否 answer-agnostic、结果是否诚实、机制是否钉死)不可下放。
