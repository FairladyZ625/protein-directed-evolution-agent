# 实验二/agentic v0.3:ESM-2 表征 + 强代理模型能否把真峰排进可达区、突破 7.53

Task Contract: harness-task v1

## Brief

v0.2 证明门禁消除了探索惩罚、追平 greedy 的 7.53,但破不了顶——因为 one_hot+Ridge 代理把真峰 8.42 排在门内 #2418,288 预算够不着。本任务换表征(ESM-2 语义嵌入)并配更强的代理模型,验证"表征×代理"这个真瓶颈能否被撬动:把真峰的门内预测排名从 ~#2000 拉进可达区(≤ 约 288),从而让门禁流 agent 真正突破 7.53。

## Goal

在 AAV 池、同预算(288=48×6)、同门禁(HD≤4 且平均 BLOSUM62≥0)、同 oracle、seed 42 下,产出 agentic v0.3(ESM-2 表征)跑分,并回答一个可证伪的核心问题:**是否存在 表征×代理模型 组合,把真峰 8.416 的门内预测排名拉进 288 可达区、使 cum_top10_max 突破 7.53?** 交付物:`lab/reports/agentic-v0.3/aav/` 下 metrics/events(链校验)/figure + 中期报告 report.md(四方对比:v0.1 5.96 / v0.2-onehot 7.53 / greedy 7.53 / v0.3-esm ?),以及一张"表征×代理 → 门内真峰排名"的决定性诊断表。收件人 CEO 与泽宇;首个使用者是最终报告的"表征是否是破顶杠杆"章节。

## Context

**已测清的地基(F-待记录 + 下列实测):**
- one_hot:门内真峰排名 **#2418**/9533,pool Spearman **0.641**。
- ESM-2(mean-pool 1280 维 + 标准化 Ridge):门内真峰排名 **#2140**/9533,pool Spearman **0.602**(见 `lab/reports/agentic-v0.1/aav/postmortem_esm.json`:全池 rank_by_mean #5759、Spearman 0.605)。
- **结论**:朴素 ESM+Ridge 几乎不改善(#2418→#2140,仍远不可达),Spearman 甚至略降。真瓶颈是**线性代理排不动那根针**,不是表征本身的信息量。
- 故本任务的破顶希望在**更强的代理模型**(kNN/GP/MLP/GBM 等)吃 ESM 语义嵌入——ESM 的价值常在非线性/近邻模型上才显现;线性 Ridge 埋没了它。
- **诚实预期**:naive `--feature esm2 --guardrail` 大概率复现 ~7.53(null);真正的实验是"表征固定为 ESM,扫代理模型,看门内真峰排名能否进可达区"。若都进不去,则得出"288 预算下 AAV 真峰对当前 表征×代理 族不可达"的诚实上界结论。

区分三原语:task=换表征+扫代理并跑对比,fact=门内真峰排名/突破与否的观察,decision=若某代理模型显著改变可达性结论则记裁定。

## Required Reading

1. `agent/auto_researcher.py`(权威:agentic 流 + 门禁,`--feature` 已支持 esm2;predict/list_pool 依赖 `RidgePredictor`——换代理要动这里的代理注入点)。
2. `models/train_ladder.py`(权威:`RidgePredictor` 及 `standardize` 选项;新代理模型加在此,保持 `.fit(X,y).predict(X)->(mean,var)` 接口)。
3. `lab/reports/agentic-v0.1/aav/postmortem_esm.json`(权威:ESM 预测器技能 + 真峰全池排名 #5759)。
4. `lab/reports/agentic-v0.2/report.md`(权威:v0.2 结论与 7.53 天花板机制)。
5. `evolution/datasets.py` 的 `esm_encoder`/`load_aav`(参考:ESM 缓存机制,`lab/reports/cache/esm_aav.npz` 已覆盖全 38265 序列)。
6. `features/esm2.py`(参考:ESM2Embedder,权重机器本地 650M)。

## Entry Conditions

- `lab/reports/cache/esm_aav.npz` 存在且覆盖全池(实测:38265×1280,已满足)——首跑为缓存命中的快跑,不需 650M 重提。
- v0.2 门禁代码正常(commit 6c7b31a 及之后,门禁单测 4 passed)。
- 至少一个候选强代理模型可用(sklearn 已在依赖内:KNeighborsRegressor/GaussianProcess/MLP/GradientBoosting)。
- 任一不满足则停下报告,不伪造跑分。

## Dependencies

上游:v0.2 门禁(commit 6c7b31a,已合 master)、ESM 全池缓存(esm_aav.npz)、knowledge 规则库(BLOSUM62)。下游:最终报告"表征/代理是否是破顶杠杆"章节;若破顶成功,反哺 avGFP-ESM 线。无并发改 auto_researcher.py / train_ladder.py。

## Execution Surface

仓库根(dispatcher 注入 cwd)。写范围:`models/train_ladder.py`(加代理模型,不动 RidgePredictor 现有行为)、`agent/auto_researcher.py`(加 `--surrogate` 选项选代理,默认 ridge 保持 v0.1/v0.2 行为)、可补 `analysis/`(表征×代理 排名诊断脚本)+ `tests/`(新代理接口单测);产物落 `lab/reports/agentic-v0.3/`。不改 workflow 线、不动 v0.1/v0.2 产物。

## Constraints

- 公平对照:v0.3 与 v0.1/v0.2/greedy 同池、同预算、同 oracle、同 seed、同门禁;唯一变量是 表征(→ESM-2)与代理模型(→扫描)。
- 保留既有行为:`--surrogate ridge --feature one_hot` 必须复现 v0.2;新代理默认关。
- 门禁语义不变:HD≤4 且平均 BLOSUM62≥0,入口塑形 + 出口硬门;拒收不扣预算。
- 诚实:若无组合突破 7.53,如实记录"当前 表征×代理 族在 288 预算下够不着真峰"这一上界结论(这是有价值的负结果),不调门/调 seed 凑赢。
- 先诊断后跑:先算各 表征×代理 的门内真峰排名(便宜、确定性),再只对"排名进可达区"的组合跑完整 LLM campaign,不盲目跑一堆 LLM。
- 不做外部/破坏性动作;ESM 权重机器本地,不入库。

## Checkpoint

- 诊断表出来后**先报一次**:贴"表征×代理 → 门内真峰排名 + pool Spearman"表,标出哪些组合把真峰拉进可达区(若有);再决定跑哪些 LLM campaign。
- 若无任何组合把真峰拉进可达区(排名仍 ≫288),停下报 CEO:这基本预示 null,问是否仍要跑一版 esm2 LLM 作完整对照、还是转向别的杠杆(如 fine-tune / 更大预算 / 不同 oracle)。
- LLM 版跑通后**再报一次**:四方对比 + 是否突破 7.53 + 门内真峰是否被实际测到。

## CI/Gate Authority Stop Condition

本任务不改 CI/gate/治理面。定向测试(新代理单测 + 门禁回归)本地绿即可;完成的 CI witness 依仓库现状(witness 机制由 task_217ab535/Phase 0 修复中,见 HARNESS-UX-FEEDBACK.md)。

## Implementation Plan

1. **诊断先行(确定性、便宜)**:写 `analysis/representation_surrogate_scan.py`——对 {one_hot, esm2} × {ridge, knn, gp?, mlp, gbm} 各组合,用 cold-start(HD≤2)拟合、预测门内池,算真峰门内排名 + pool Spearman + top-k 命中,输出诊断表 JSON。
2. **加代理模型**:`models/train_ladder.py` 加 1–3 个强代理(先 KNeighborsRegressor + 一个非线性,如 MLP 或 GradientBoosting),统一 `.fit(X,y).predict(X)->(mean,var)` 接口(var 可用邻居方差/集成方差)。
3. **接线**:`auto_researcher.py` 加 `--surrogate {ridge,knn,mlp,gbm}`,`_pool_scores`/predict 用所选代理;默认 ridge。
4. **单测**:新代理接口单测(fit/predict 形状 + var 非负)+ 门禁回归仍绿。
5. **诊断报 CEO**(Checkpoint 1),按结果只跑"有希望"的 LLM campaign:`--dataset aav --feature esm2 --guardrail --surrogate <best> --budget 48 --n-rounds 6 --seed 42 --model gpt-5.6-sol`。
6. 入 ledger,写 `lab/reports/agentic-v0.3/report.md`(四方对比 + 诊断表)+ manifest.json + figure。
7. `ha fact record --task task_d2771aa9372d26af9f81c9e9eb` 记门内真峰排名与突破与否结论。

## Deliverable Contract

- `models/train_ladder.py`:≥1 个新强代理(接口统一,ridge 行为不变)。
- `agent/auto_researcher.py`:`--surrogate` 选项(默认 ridge,复现 v0.2)。
- `analysis/representation_surrogate_scan.py` + 输出诊断表。
- `tests/` 新代理单测 + 门禁回归通过。
- `lab/reports/agentic-v0.3/aav/`:agentic.metrics.json + events.jsonl(链校验)+ figure;`lab/reports/agentic-v0.3/report.md`(四方对比)+ manifest.json。
- ≥1 条 `ha fact record --task task_d2771aa9372d26af9f81c9e9eb`;experiment_log 入库 v0.3 跑。

## Evidence Protocol

- 诊断证据:表征×代理 的门内真峰排名表(数据取自确定性拟合),明确标出是否有组合 ≤ 可达阈值(~288)。
- 对比证据:四方 cum_top10_max/strong 命中 + 曲线,数据取自各自 metrics.json。
- 门禁生效证据:事件流含 knowledge_gate、measured 变体全在门内、budget 花满、事件链 store.verify() 通过。
- 突破判据:cum_top10_max > 7.531 且真峰(或 >7.53 的门内针)被实际测到,才算突破;否则如实记 null + 门内真峰排名上界。
- 单测 clean-env 可复现(定向 test 文件 + 通过数)。

## Verification

- 通过判据:v0.3 metrics 落库、事件链校验通过、新代理+门禁单测绿、四方对比表 + 诊断表可复现;突破/未突破结论有排名数据支撑。
- 收尾自检:v0.1/v0.2 产物未被覆盖;v0.3 在独立目录;`--surrogate ridge --feature one_hot` 仍复现 v0.2。
- 诚实性:若未突破,report 如实写明"当前 表征×代理 族在 288 预算下够不着真峰"并给排名上界,不美化。
