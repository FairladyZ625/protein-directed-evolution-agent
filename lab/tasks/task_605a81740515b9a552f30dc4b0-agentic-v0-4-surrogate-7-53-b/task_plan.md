# 实验三/agentic v0.4:上位感知 surrogate 能否让真峰进可达区、破 7.53(提名B先行)

Task Contract: harness-task v1

## Brief

实验二证明 7.53 天花板既非决策问题(v0.2)也非表征×代理问题(v0.3:one_hot/ESM×Ridge/kNN/GBM + ESM zero-shot 全不破),真峰 8.42 因**正上位效应**对加性/自然度先验双重隐形。研究(plateau-breaking-methods.md)与本仓自证指出:**cold-start(HD≤2)本就含单/双突变实测,瓶颈是加性 surrogate 的表达力**。本任务做提名 B:把加性 surrogate 换成**上位感知模型**(显式含 pairwise 交互项),在同一 cold-start 上先做确定性诊断——真峰门内预测排名能否从 #1283 掉进可达区(≤288)。这是最省、最决定性地验证"天花板 = 加性表达上限"这一假设。

## Goal

在 AAV 池、同 cold-start(HD≤2)、同门内定义(HD≤4 且平均 BLOSUM62≥0,9533)下,产出**上位感知 surrogate 的确定性诊断**:真峰门内排名 + pool/gate Spearman,与实验二加性基线(esm2×knn #1283、one_hot×ridge #2776)对照。判据:是否有上位感知 surrogate 把真峰排进 ≤288 可达区。若诊断为正,再接**闭环跑分**(同 288 预算、同门禁、同采集,仅换 surrogate)产出 agentic v0.4 的 cum_top10_max,看是否突破 7.53。全程 answer-agnostic(不看测试峰成分;位点/特征选择不用峰信息)。交付:`lab/reports/agentic-v0.4/aav/` 诊断 JSON(+ 若跑闭环则 metrics/events/figure)+ 报告 report.md。

## Context

- 关键自证(F-851790B5 / 本仓数据):cold-start 含 D0Q 单点 Δ+1.22(共现富集 −0.01 被加性拉平)、S17E×V18A 上位藏在已有 doubles 里 → 加性 surrogate 看不见,交互项 surrogate 有望看见。
- 上位感知候选(族 2,answer-agnostic):pairwise 交互(Potts/EVmutation 式)、因子分解机(FM,高效捕获二阶交互)、ECNet-style、ProteinNPT。**优先实现 FM 或 pairwise-one-hot+正则**(轻、快、二阶交互显式)。
- 风险(研究已预登记):若峰的构成上位是纯高阶/sign-epistasis、成对投影不显,pairwise surrogate 仍可能漏 → 诊断会如实显示排名不降,则转提名 A(主动双突变扫描)。
- 区分三原语:task=换 surrogate 加诊断(+可选闭环),fact=真峰排名是否进可达区的观察,decision=若诊断改变"天花板成因"结论则记裁定。

## Required Reading

1. `analysis/representation_surrogate_scan.py`(实验二诊断脚手架,复用其门内排名/Spearman 口径)。
2. `models/train_ladder.py`(RidgePredictor 与 standardize;新 surrogate 加此,保持 .fit(X,y).predict->(mean,var) 接口)。
3. `lab/reports/agentic-v0.3/report.md` + `aav/surrogate_scan.json`(加性基线数字)。
4. `lab/context/research/plateau-breaking-methods.md`(族 2 方法与提名 B/A 依据)。
5. `agent/auto_researcher.py` 的 `_pool_scores`/`--surrogate` 注入点(若接闭环)。

## Entry Conditions

AAV one_hot/esm2 特征可加载;cold-start(HD≤2)含 doubles(实测已确认);sklearn 可用(FM 可用 pairwise 特征 + 线性,或轻量实现)。任一不满足停下报告,不伪造。

## Dependencies

上游:实验二诊断(v0.3)、cold-start 数据、门禁定义。下游:若破顶,反哺最终报告"agent 跨到上位感知表征才破顶"章节;若不破,转提名 A(主动双突变扫描)。无并发改 train_ladder.py / auto_researcher.py。

## Execution Surface

仓库根。写范围:`models/train_ladder.py`(加上位感知 surrogate)、`analysis/`(诊断脚本,可扩展 representation_surrogate_scan 或新建 epistasis_surrogate_scan.py)、可补 `tests/`(surrogate 接口单测)、`agent/auto_researcher.py`(仅当接闭环:扩 `--surrogate` 选项);产物落 `lab/reports/agentic-v0.4/`。不改 workflow 线、不动 v0.1–v0.3 产物。

## Constraints

- **answer-agnostic 硬约束**:surrogate 的特征/位点选择不得使用测试峰成分;训练只用 cold-start 实测标签 + 序列。
- 公平对照:与实验二诊断同 cold-start、同门内池、同真峰口径;唯一变量是 surrogate 的表达力(加性 → 上位感知)。
- 保留既有行为:RidgePredictor 及 `--surrogate ridge` 不变,新 surrogate 默认关。
- 诚实:诊断为负(真峰仍不进可达区)如实记录,并据研究转提名 A;不调门/调 seed/挑特征凑赢。
- 先诊断后闭环:确定性诊断为正(真峰进可达区)才跑 LLM/闭环,不盲跑。
- 不做外部/破坏性动作。

## Checkpoint

- **诊断出来先报一次**:贴"上位感知 surrogate vs 加性基线 → 真峰门内排名 + Spearman"表,明确真峰是否进可达区(≤288);再决定是否接闭环。
- 若诊断为负,停下报 CEO:说明是"成对投影不显(需高阶/主动测双突变→提名 A)"还是"cold-start 缺关键 doubles",给转向建议,不擅自反复换模型。
- 闭环跑通后再报:v0.4 cum_top10_max vs 7.53 + 是否实际测到真峰/>7.53 门内针。

## CI/Gate Authority Stop Condition

不改 CI/gate/治理面。定向测试(surrogate 单测 + 回归)本地绿即可;完成 CI witness 依基线 closeout 批次的 ci.yml artifact 方案(settings.ci.workflows 已配)。

## Implementation Plan

1. `models/train_ladder.py` 加上位感知 surrogate:优先 **FM(因子分解机)** 或 **pairwise-one-hot + 岭正则**(显式二阶交互),统一 `.fit(X,y).predict(X)->(mean,var)`(var 用 bootstrap/集成方差)。
2. 诊断脚本(扩 `analysis/representation_surrogate_scan.py` 或新建):对 {加性基线, 上位感知} 各算门内真峰排名 + pool/gate Spearman + top-288 命中,输出 JSON 到 `lab/reports/agentic-v0.4/aav/`。
3. **Checkpoint 1 报 CEO**(诊断表 + 真峰是否进可达区)。
4. 若为正:`auto_researcher.py` 扩 `--surrogate` 支持新模型,跑 v0.4 闭环(--dataset aav --guardrail --surrogate <epistasis> --budget 48 --n-rounds 6 --seed 42 --model gpt-5.6-sol),入 ledger,写 report.md 五方对比(v0.1/v0.2/greedy/v0.3诊断/v0.4)。
5. surrogate 接口单测 + 门禁回归绿。
6. `ha fact record --task task_605a81740515b9a552f30dc4b0` 记真峰排名结论。

## Deliverable Contract

- `models/train_ladder.py`:上位感知 surrogate(接口统一,ridge 不变)。
- 诊断脚本 + `lab/reports/agentic-v0.4/aav/epistasis_surrogate_scan.json`。
- `tests/` surrogate 单测 + 门禁回归通过。
- 若接闭环:`agentic-v0.4/aav/` metrics/events(链校验)/figure + `report.md`(多方对比)+ manifest.json。
- ≥1 条 `ha fact record --task task_605a81740515b9a552f30dc4b0`。

## Evidence Protocol

- 诊断证据:上位感知 vs 加性 的门内真峰排名表(同 cold-start、同门内池),明确 ≤288 与否。
- 若闭环:事件流含 knowledge_gate、measured 全在门内、budget 花满、store.verify() 通过。
- 破顶判据:真峰(或 >7.53 门内针)被实际测到且 cum_top10_max>7.531 才算破;否则如实记 null + 排名上界。
- 单测 clean-env 可复现。

## Verification

- 通过判据:诊断 JSON 落库、真峰排名结论有数据支撑(进/不进可达区)、surrogate+门禁单测绿;若闭环则 metrics 落库 + 事件链校验 + 多方对比可复现。
- 收尾自检:v0.1–v0.3 产物未被覆盖;`--surrogate ridge` 仍复现旧行为。
- 诚实性:诊断/闭环为负如实写明并按研究转提名 A,不美化。
