# 知识库迭代研究:从 BLOSUM62 二元门禁 → 进化耦合/结构/保守性引导探索的先验(answer-agnostic)

Task Contract: harness-task v1

## Brief

我们链路里的"知识库"目前很基础:`knowledge/rules.yaml`(BLOSUM62 + 氨基酸理化属性)+ HD 距离,且只当**二元门禁**(HD≤max_hd 且 mean BLOSUM62≥min)用,没当**引导探索的先验**。研究:有哪些 answer-agnostic 的更丰富领域知识(进化耦合/结构/位点保守性/PLM 先验)能加进来,尤其能**引导探索去撞 surrogate 隐形的上位峰**;给出排序 + 对最优 1-2 项的落地设计。这是研究/设计文档,不改产品代码。

## Goal

产出 `harness/context/research/kb-iteration-research.md`(结论优先,≤300 行),回答:
1. **现状盘点**:当前 KB 到底编码了什么(BLOSUM62 保守性、理化属性、HD),在链路里怎么用(gate + check_knowledge),局限是什么(通用、非 AAV 特异、无结构/耦合、只做二元过滤)。
2. **候选知识源**:枚举可加的 answer-agnostic 知识——位点保守性(MSA/PSSM)、进化耦合(EVmutation/DCA/Potts,直接对应"哪些位点对上位")、结构约束(AAV capsid 接触图/埋藏度/二级结构,P03135 VP1)、PLM 先验(ESM,注意我们之前测过 ESM zero-shot 失败)、氨基酸理化梯度。**每项按三维打分**:(a) answer-agnostic 合法性(能否不看测试标签就获得,不泄漏测试峰);(b) 笼内可行性(考试条件下能否用现成工具/数据实现,无湿实验);(c) 帮助"surface 隐形上位峰"的潜力(与 v07 峰机制"关键二阶组合缺测"挂钩)。
3. **落地设计**:对最优 1-2 项,给出怎么从"二元门禁"升级为"探索先验/采集引导"的接口草案(如:耦合先验给候选打分、引导 explore_batch 去测高耦合位点对),明确 answer-agnostic 边界。
4. **批判性**:诚实说清哪些是"看着高级但对本题大概率没用/增复杂度"(如 ESM zero-shot 我们实测失败)。不迎合,给真判断。

首个消费者:CEO(判断知识库是否值得迭代、怎么迭代)+ 最终报告的 future-work / 方法讨论。

## Context

- **现状**:`knowledge/rules.yaml`(version 1:amino_acids 理化 + 部分 blosum62)、`knowledge/validators.py`(validate_mutations:R-BLOSUM-CONSERVATIVE score≥1 / R-BLOSUM-AGGRESSIVE score>-1;build_knowledge_graph)。链路:`agent/auto_researcher.py` 的 `_gate`(HD+mean BLOSUM 门禁)、`check_knowledge`(每突变 BLOSUM 检查)。
- **核心发现挂钩**(facts F-8514C714/F-CCF29A66,v07-peak-mechanism.md):真峰 8.4162 对 pairwise surrogate 隐形(门内均值 #426),根因是**关键二阶组合在 cold-start 缺测**+ 模型低估。所以能"指出哪些位点对值得测"的知识(进化耦合/结构接触)最可能有用。
- **already-tried 负例**:ESM-2 zero-shot(masked-marginal)在本题实测失败(analysis/esm_zeroshot_scan.py:峰 z 为负、evolutionarily atypical)——别把 ESM 当银弹。
- **前沿**:frontier-landscape-synthesis.md(EVmutation/ECNet/MULTI-evolve 一族显式建模上位;LLM 增益在先验/探索层)。
- **answer-agnostic 红线**:任何知识必须能在**不看测试 fitness 标签**下获得(MSA/结构/PLM 都可以),且不得偷偷编码测试峰身份。

## Required Reading

按序:
1. `knowledge/validators.py` + `knowledge/rules.yaml`(**待研究主体**:现有 KB)。
2. `agent/auto_researcher.py`(**只读**:`_gate`/`check_knowledge`/`validate_candidate` 如何用 KB)。
3. `harness/context/research/v07-peak-mechanism.md`(**权威**:峰为何隐形——知识该补哪)。
4. `harness/context/research/v06-backtrack-analysis.md` + `frontier-landscape-synthesis.md`(定位)。
5. `analysis/esm_zeroshot_scan.py`(**负例**:ESM zero-shot 为何失败)。
6. `evolution/datasets.py`(AAV WT/窗口/池口径)。

## Entry Conditions

- worktree(t-astra-kb)从 v0.5 HEAD 分叉;`.venv`+`data/aav/full_data.csv` symlink 好。你是 codex 本地无联网,基于代码 + 你的领域知识推理(EVmutation/DCA/结构方法你都懂),不需要抓新论文。
- 未满足即停并报。

## Dependencies

- 上游:现有 knowledge 模块、v07 峰机制、ESM 负例。
- 下游:CEO + 最终报告。
- 并发:其他 Astra 在别的 worktree 跑,互不冲突;你只读代码 + 写你这一个研究文档。

## Execution Surface

- 分支 t-astra-kb;dispatcher 注入 cwd。
- **允许写范围**:仅 `harness/context/research/kb-iteration-research.md`(+ 你自己 worktree 内的临时分析脚本,不进产品树)。
- 禁区:所有产品代码(knowledge/agent/models/evolution 只读)、其他 report、CI/oracle。
- 运行时:`.venv`、`data/aav/full_data.csv` symlink 好。

## Constraints

- **answer-agnostic 硬红线**:所有建议的知识源必须不看测试标签就能得到,不编码测试峰。
- 不改产品代码;只写研究文档。
- 无湿实验、无外部/破坏性动作。
- 诚实:看着高级但对本题没用的,直说(尤其 ESM 已是负例)。

## Checkpoint

- 写完文档即停并报,回:现状局限一句话 + 最值得加的 1-2 项知识 + 为什么它能帮到隐形峰。
- 异议型停:若结论是"知识库其实够用、迭代收益低",如实说,不硬造迭代空间。

## CI/Gate Authority Stop Condition

非 CI/gate 任务(docs-task 无 CI 门)。不碰 CI/门禁/oracle。

## Implementation Plan

- 读现有 KB + 链路用法,精确刻画"编码了什么、怎么用、局限"。
- 可写只读脚本做小实证:如统计 cold-start 里哪些位点对缺测、真峰的突变落在哪些位点对(不用测试峰身份调参,仅用于说明"知识能否指出这些对")。
- 枚举候选知识源,三维打分排序。
- 对 top 1-2 给接口草案(门禁→先验/采集引导)。
- 台账:`ha fact record --task task_8e29be09414b0c5d7eac95db08 ...` 记承重结论(≥1 fact)。

## Deliverable Contract

- `harness/context/research/kb-iteration-research.md`(结论优先,现状/候选/打分/落地/批判,≤300 行)。
- 完成回:现状局限 + top 1-2 知识源 + 落地接口一句话 + 对本题的诚实收益判断。
- 只写该文档,不改产品代码,不 push/不 PR。

## Evidence Protocol

- 每个判断给依据(代码事实/领域机制/与 v07 峰机制的挂钩);区分"实证/推断"。
- answer-agnostic 边界对每个候选明确标注。
- ≥1 fact 记承重结论。

## Verification

- 停手点 = 文档写完 + ≥1 fact + 回结论摘要。无产品代码改动;若写了分析脚本,贴真实输出。
- CEO 语义验收(answer-agnostic + 收益判断是否诚实 + 落地设计是否可行)不可下放。
