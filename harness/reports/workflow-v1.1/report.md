# workflow-v1.1:四策略闭环重跑(measurable_variants 修复后)

## 这一版为什么存在

v1.0 的 agent 策略是**静默失效**的。`agent/pipeline.py` 的 `run_pipeline` 把「已测池」
当成了「可测空间」:提名按定义就是还没测过的变体,拿它去和池子求交集,结果必然是空集,
于是两个 agent 策略每轮提名 0 个候选,却不报错、不告警,曲线照样画出来。
v1.0 的 agent 数字因此**不能代表 agent 的能力**。

修复是给 `run_pipeline` 加 `measurable_variants` 参数(oracle 能回答的全部 149,361 个变体),
调用方 `evolution/campaign.py` 显式传 `set(df.Variants)`。本版是修复后的重跑。

同批修好的还有两处:
- `no_knowledge` 此前在 campaign 里被硬编码为 `True`,导致「知识增强」策略的 Critic 门禁
  实际没开;现在按策略传 `no_knowledge=(strategy == "agent_no_knowledge")`。
- LLM Critic 端口返回类型与 `CriticReview` 不匹配,每次调用都被静默吞掉降级
  (fact `F-363846B5`),`llm` 档因此从未真正用过 LLM。

## 口径

四个策略共享同一个预算、同一个 oracle、同一个提名空间,唯一变量是提名方式。

| 项 | 值 |
|---|---|
| 候选空间 | 149,361 个实测变体(160,000 个四位点组合中 10,639 个无真值,不进候选) |
| oracle | 实测真值表查表,**从不是模型打分** |
| 预算 | 每轮 96 个提名 × 3 轮 |
| 野生型 | `VDGV` = 1.0;全局最优 `FWAA` = 8.761966 |
| 强命中 | 累计 fitness ≥ 4.0 的变体数 |
| 有益命中 | 当轮 fitness > 1.0(优于野生型)的提名数 |
| 随机基线 | 5 个独立 seed(11/23/42/67/89)取平均 |

四个 regime 的区别只在冷启动池:

- **easy** — 5,000 个均匀随机变体(约 98% 是 HD≥3),预测器从第 0 轮就很强
- **hard** — 种子池 = 全部 HD≤2 的变体,只提名 HD>2(外推)
- **sparse** — 种子池 = 全部 HD≤1 的变体,只提名 HD>1(更强的外推)
- **llm** — 与 hard 同冷启动,但把池内商用 LLM 接进假设生成与 Critic 两个端口

## 结果

`cum_top10_max` = 三轮累计提名里 top-10 的最高真实 fitness。

| regime | random(5 seed 均值 ± σ) | greedy | agent 无知识 | 知识增强 |
|---|---:|---:|---:|---:|
| easy | 3.674 ± 0.820 | **8.761966** | **8.761966** | **8.761966** |
| hard | 4.611 ± 1.850 | **8.761966** | **8.761966** | **8.761966** |
| sparse | 4.046 ± 0.720 | 5.772032 | 5.772032 | **8.761966** |
| llm | 4.611 ± 1.850 | **8.761966** | **8.761966** | **8.761966** |

> **随机基线必须引 5 seed 的均值 ± σ,不要引 `summary.random.final_cum_top10_max`。**
> 后者只是 seed 42 那一次(easy 2.374 / hard 5.081 / sparse 3.993),
> 三个 regime 之间看起来有大小关系,而 5 seed 统计显示**三者在 ±1σ 内完全重叠、
> 并无差异**。用单 seed 值会读出一个不存在的趋势。
> 其余三个策略目前是单 seed(42),见「已知限制」。

强命中数 / 有益命中数(random 为 5 seed 强命中均值):

| regime | random | greedy | agent 无知识 | 知识增强 |
|---|---:|---:|---:|---:|
| easy | 0.4 / 6 | 81 / 239 | **95** / 244 | 86 / **250** |
| hard | 0.6 / 7 | 43 / 178 | 50 / 182 | **65** / **204** |
| sparse | 0.4 / 9 | 29 / 180 | 27 / **213** | **33** / 202 |
| llm | 0.6 / 7 | 43 / 178 | 32 / 88 | 59 / 140 |

`llm` 档与 `hard` 档只差一个变量(接不接 LLM),对照见下面第 ④ 条。

## 读法(五条,包括对我们不利的那几条)

**① sparse 是唯一分出高下的 regime,而且分在知识库这一侧。**
种子池收紧到 HD≤1 时,greedy 与无知识 agent 都停在 5.772032,只有知识增强
(UCB λ=0.75 + BLOSUM62 先验 β=0.30)走到全局最优 8.761966。
种子越稀疏,领域知识的边际价值越大。这是本仓知识库第一次拿到可量化的正证据,
而不只是「加了没坏」。(fact `F-61A84D3B`)

**② 但知识库不是普遍有效——easy regime 下它没有可测增益。**
信息充足时三个模型策略并列命中全局最优,分不出高下。
**任何把知识增强写成普遍优势的表述都不成立**,它的价值条件性地依赖于信息稀疏度。

**③ 两个指标会给出相反的排序,必须同时报。**
easy regime 下无知识 agent 的强命中数(95)高于知识增强(86),
而知识增强的有益命中数最多(250)。两者问的是不同问题:
强命中问「找到多少个高适应度变体」,有益命中问「多少提名优于野生型」。
只报对自己有利的那个是选择性汇报。

**④ 接入真 LLM 之后,两个 agent 策略都变差了——而且这个对比自带阴性对照。**

`llm` 档与 `hard` 档的冷启动、预算、轮数、候选空间、oracle **完全相同**,
唯一变量是假设生成与 Critic 两个端口接不接池内 LLM(`gpt-5.6-sol`)。

| 策略 | hard(确定性) | llm(接入 LLM) | 变化 |
|---|---|---|---|
| random | strong 1 / hits 7 | strong 1 / hits 7 | **逐位相同** |
| greedy | strong 43 / hits 178 | strong 43 / hits 178 | **逐位相同** |
| agent 无知识 | strong 50 / hits 182 | strong 32 / hits 88 | **−36% / −52%** |
| 知识增强 | strong 65 / hits 204 | strong 59 / hits 140 | **−9% / −31%** |

**random 与 greedy 两行逐位相同是天然的阴性对照**:这两个策略不经过 LLM 端口,
它们没变,证明两次运行之间除了 LLM 没有别的东西在动。所以 agent 两行的下降
不能归因于随机性或环境差异。

三个模型策略的峰值都仍是 8.761966 —— **找峰的能力没变,变差的是批次产出**。
机制上说得通:找峰靠的是 Ridge 代理模型对全空间的排序,LLM 不参与;
而 LLM 参与的是「从实测单点替换里挑哪些去组合」,它挑出的集合比确定性排序更窄,
于是每轮的有益命中显著减少。

这直接回答试题考核重点里那一问——「LLM Agent 是否真正学到了『科学家思维』,
还是只是调用预测模型」。**本仓的证据支持后者偏多**:把 LLM 放进假设生成角色,
批次质量下降而非上升;真正把峰找出来的是预测模型。
这是一个负结果,报告里应当如实写,不要绕过。

**⑤ 随机基线在三个 regime 之间没有差异,不要从单 seed 值读出趋势。**
5 seed 统计是 easy 3.674±0.820、hard 4.611±1.850、sparse 4.046±0.720,三者在 ±1σ 内
完全重叠。`summary` 字段里的单 seed 42 值(2.374 / 5.081 / 3.993)看起来像有大小关系,
那是 288 次抽样在 149,361 个变体尾部的噪声——hard 的 σ 达到 1.850,本身就说明
单次运行的最大值极不稳定。**写报告时引均值 ± σ,不要引那三个单 seed 数字。**

## 产物

| 文件 | 内容 |
|---|---|
| `gb1/campaign_{easy,hard,sparse,llm}.metrics.json` | 每 regime 四策略逐轮指标,含 `topk_concentration`(每策略每位点的 `residue_counts` / `dominant_residue` / `dominant_fraction` / `mutation_fraction`) |
| `gb1/campaign_*.events.jsonl.gz` | 链式 SHA-256 事件流(gzip 归档,`EventStore` 读侧透明回退) |
| `gb1/figures/campaign_*.png` | 四条累计曲线 |
| `gb1/predictor_metrics.json` | 预测器阶梯指标 |
| `agent_combination_rationales.json` | 组合理由快照(`evidence_source` / `narrative_source` 分列) |

`topk_concentration` 直接回答试题「结果分析与展示 b. 分析推荐突变是否集中在关键位点」:
以 easy 档的知识增强策略为例,V54 位点 30 次 top-k 观测里 100% 是 Ala
(`dominant_fraction` = 1.0),G41 位点 60% 是 Cys,而 V39 最分散(主导残基只占 20%)。

## 复现

```bash
./scripts/install.sh                 # 或手工装 requirements.txt
# 需要 data/four_mutations_full_data.csv,见 data/README.md

python evolution/campaign.py \
  --out-json harness/reports/workflow-v1.1/gb1/campaign_easy.metrics.json \
  --out-fig  harness/reports/workflow-v1.1/gb1/figures/campaign_easy.png \
  --out-events harness/reports/workflow-v1.1/gb1/campaign_easy.events.jsonl

python evolution/campaign.py --cold-start low_hd --max-cold-hd 2 \
  --out-json ... campaign_hard.metrics.json   # hard
python evolution/campaign.py --cold-start low_hd --max-cold-hd 1 \
  --out-json ... campaign_sparse.metrics.json # sparse
python evolution/campaign.py --cold-start low_hd --max-cold-hd 2 --use-llm \
  --out-json ... campaign_llm.metrics.json    # llm(需要 agent/llm.py 的端点配置)
```

每次运行会自动往 `harness/reports/experiment_log.jsonl` 追加一条带命令、git commit
与产物 SHA-256 的记录。事件链可用
`EventStore("<events 路径>").verify()` 独立校验。

## 已知限制

1. **随机基线以外的策略都是单 seed(42)**。策略之间的差值没有做重复实验,
   sparse 下那条 5.772032 → 8.761966 的分层**没有误差棒**。
2. **10,639 个组合在真值表里没有数据**,它们既不进候选也不计入分母;
   全局最优是「实测 149,361 个里的最优」,不是理论最优。
3. **`llm` 档的 LLM Critic 每轮有调用预算上限(10)**,预算外的候选记确定性注释。
   全程实测:LLM 写出实质评审 **27 条**、90 秒超时回退 **23 条**,成功率 **54%**
   (fact `F-ABD9B83F`)。其中 knowledge_agent 第 1 轮预算花了 0/10 —— 因为 15 个候选
   全被知识门禁拒了,没有候选进到「写评审」这一步,这是预期行为不是故障。
   假设生成端口的逐轮来源也记录在案:agent_no_knowledge 是
   `llm / fallback / llm`,knowledge_agent 是 `llm / fallback / fallback`。
   **报告引用时必须写明成功率与逐轮来源,不能笼统说「由 LLM 评审」。**
4. **事件流里五角色的 `strategy` 字段统一是 `agent`**,不区分是无知识还是知识增强那一路;
   要分辨得看外层 campaign 事件。回放界面据此归属时要小心。
