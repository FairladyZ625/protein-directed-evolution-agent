# 更难数据集接入:真实不确定性 + ESM + avGFP + 跨数据集诚实对比

Task Contract: harness-task v1

## Brief

CEO 已把流程扩展到更难数据集并跑通池式主动学习引擎(`evolution/pool_campaign.py`)+ 多数据集 registry(`evolution/datasets.py`),AAV(FLIP)one-hot 基线已出:random 明显垫底(strong 35)≪ greedy/agent/knowledge(strong 85-86)。但**三个模型类策略几乎重合**,诚实根因是 Ridge 5-seed 集成方差≈0 → UCB 探索项形同虚设,agent 的假设重叠项相对预测器 mean 权重太小。本任务:给预测器真实不确定性、补 ESM 特征、接入 avGFP,产出**跨数据集的诚实四策略对比**。

## Goal

在池式引擎上,让四策略对比在"更难数据集 + 校准的不确定性"下如实呈现。产出:AAV(ESM-2)与 avGFP(≥1 特征)的 `reports/pool_metrics_*.json` + 事件流 + 曲线,以及一份 `lab/tasks/<本任务>/artifacts/harder-findings.md` 记录跨数据集结论(诚实:agent/知识到底比 greedy 强不强)。

## Context

- 已就绪(master,worktree 已建 `.worktrees/t-harder`,AAV 数据已 symlink,勿重建):
  - `evolution/pool_campaign.py`:`run_pool_campaign(spec, cold_start_hd, budget, n_rounds, seed, event_store)`,四策略 random/greedy/agent_no_knowledge/knowledge_agent;agent 采集 = mean + α·analyst-overlap,knowledge += λ·√var(UCB) + β·BLOSUM。CLI:`python -m evolution.pool_campaign --dataset aav --feature esm2`。
  - `evolution/datasets.py`:`load_aav(feature)`(干净替换子集已跑通 one-hot;`esm_encoder` 会调 `features/esm2.py` 并缓存到 `reports/cache/esm_<name>.npz`)、`load_avgfp(feature)`(**stub,WT/列名是占位,需按真实 ProteinGym 列修正**)、`one_hot_encoder(length)`。
  - `models/train_ladder.py`:`RidgePredictor / MLPPredictor`,`fit(X,y)` + `predict(X)->(mean,var)`。
  - AAV 真实事实:干净替换子集 38,265;冷启动 HD≤2=10,433;外推池 HD>2=27,832;fitness=`score`(-9.54~9.54);one-hot Ridge 外推 Spearman≈0.64;峰在 HD=2,外推池 max 8.42,strong(score>3)6.5%。
- **不确定性是关键**:UCB 只有在预测器有真实 epistemic 方差时才有意义。

## Required Reading

1. `evolution/pool_campaign.py`、`evolution/datasets.py`、`models/train_ladder.py` — 现有接口。
2. `reports/report.pdf` §6-7 或 `reports/report.html` — GB1 上"预测器主导、知识仅轻先验"的诚实定调(跨数据集要延续同样诚实标准)。
3. `lab/context/development/ai4s-worker-handbook.md`(若存在)+ 本仓 CLAUDE.md/AGENTS.md 纪律。

## Entry Conditions

- 池式引擎与 AAV one-hot 基线已就绪(已满足)。avGFP 需联网获取;若无联网能力则停在此步记 blocker 并把 AAV(ESM)做完。

## Dependencies

- 上游:池式引擎(CEO 已交)。下游:CEO 汇入报告/demo 的多数据集章节。

## Execution Surface

- worktree `.worktrees/t-harder`(已建,勿重建)。允许写:`models/`(加不确定性)、`evolution/datasets.py`(修 avGFP loader)、`evolution/pool_campaign.py`(仅必要微调)、`reports/`(pool 产出)、`tests/`、`data/avgfp/`(放数据,gitignore)、本任务 `artifacts/`。绝对 cwd 已注入。

## Constraints

- **红线·不许造假拉差距**:不得为了让 agent/knowledge 赢 greedy 而调参数堆权重;差距要来自机制(真实不确定性下的探索、知识规则的真实过滤),不来自把 α/λ/β 调爆。若如实测下来 agent≈greedy,就如实报告(这本身是有价值的结论,答题目68"是否真学到科学家思维")。
- oracle=真值查表;池式口径(四策略共用同一外推池、同预算、只在排序上不同);提名不越出已测集。
- **真实不确定性**:给 Ridge 加 bootstrap(每个 seed 在 measured 的 bootstrap 重采样上训练 → 真 var),或改用 MLP 集成;确保 `predict` 返回的 var 在 pool 上有非平凡分布(打印 var 分布自证)。
- 外部/破坏性动作禁止;避免触碰 CI/门禁面。commit 作者 ZeyuLi、不提 AI;停在本地 commit,不 push/不 PR。

## Checkpoint

- 命中即停并回报:avGFP 无法联网获取;若加了真实不确定性后 agent/knowledge 仍≈greedy(如实报告,不要强凑)。计划回报点:(1) 真实不确定性接好、AAV(ESM)四策略跑出后;(2) avGFP 跑出后。

## CI/Gate Authority Stop Condition

- 需改门禁面则停记 blocker。

## Implementation Plan

1. **真实不确定性**:`models/train_ladder.py` 给 Ridge 加 bootstrap 集成(或用 MLP),使 pool 上 var 非平凡;pool_campaign 的 knowledge_agent UCB 生效。自证:打印/记录 var 的 min/mean/max。
2. **AAV ESM-2**:`python -m evolution.pool_campaign --dataset aav --feature esm2`(esm_encoder 自动抽取+缓存 38k×28aa)。对比 one-hot vs ESM 的四策略与外推。
3. **avGFP**:从 ProteinGym 获取 Sarkisyan avGFP DMS(如 `GFP_AEQVI_Sarkisyan_2016`),放 `data/avgfp/avgfp.csv`;按真实列名修 `load_avgfp`(mutated_sequence / DMS_score,WT 取 DMS 元数据或 HD=0 行,勿用"最长序列"占位);跑池式四策略(ESM-2,238 位长序列)。
4. **跨数据集诚实对比**:整理 GB1(已有)/AAV/avGFP 的四策略结果,写 `artifacts/harder-findings.md`:每数据集 random vs model 差距、agent/knowledge 是否真比 greedy 强、one-hot vs ESM 外推差异;结论要诚实。
5. `ha fact record` 记跨数据集结论。

## Deliverable Contract

- `reports/pool_metrics_aav_esm2.json`(+事件流+曲线);`reports/pool_metrics_avgfp_*.json`(+事件流+曲线);`artifacts/harder-findings.md`;`models/` 的不确定性改动 + 定向测试。回报:四策略逐数据集指标、var 分布自证、agent-vs-greedy 结论(诚实)、avGFP 获取方式与来源。

## Evidence Protocol

- 阴性对照:random 应在每个数据集明显最弱(已见 AAV)。var 必须自证非平凡(否则 UCB 无意义)。凡"更强"论断贴真实数字;凑不出就如实说 agent≈greedy。reviewer 拒收:调爆权重制造差距、oracle 用模型自评、var 恒零还报 UCB 有效。收口记一条 fact。

## Verification

- 停止点 = 定向测试绿 + 本地 commit;贴真实四策略输出 + var 分布。
- 定向测试:`tests/test_pool_campaign.py`(池式口径、四策略同池、随机最弱、var 非平凡、复现性)。
- 至少记录一条 fact。
