# 试题逐项覆盖核对(2026-09-13)

> 对照 `lab/context/research/AI4S-assignment.md` 逐条打钩。
> **规则:每一项都要给证据路径,找不到就写「没找到」,不为好看打钩。**
> 图例:✅ 有且有证据 · ⚠️ 有但有保留 · ❌ 没有。
> 路径相对仓库根 `ai4s-directed-evolution-agent/`。

---

## 结论先行:五处需要处理

| # | 问题 | 严重度 | 处理成本 |
|---|---|---|---|
| 1 | **报告 PDF 25 页,试题要求 3–5 页** | **高** | 需要重新裁剪,不是小改 |
| 2 | **强化学习(加分项①后半)未做**,且是明确决定不做 | 中(加分项) | 要么做,要么在报告里写清为何不做 |
| 3 | **3D 结构信息未做**(加分项④只做了保守位点一半) | 中(加分项) | 同上 |
| 4 | README 首页 PDF 链接仍指向 v0.5 | 低 | 一行 |
| 5 | 理化性质只有数据块,无独立门禁规则 | 低 | 一条 rule |

除此之外,**试题正文要求的每一条都有实现且有证据**。

---

## 二、项目任务

### 1 数据选择与处理

| 条目 | 状态 | 证据 |
|---|---|---|
| a. 使用公开数据集 | ✅ | GB1(Wu et al. 2016)+ AAV 双数据集 |
| b. 选择具体蛋白任务 | ✅ | GB1 四位点结合能力;AAV 28 aa 衣壳适应度 |
| c. 整理野生型/突变序列/位点/fitness | ✅ | `evolution/datasets.py`;GB1 WT `VDGV`(V39/D40/G41/V54),AAV WT `DEEEIRTTNPVATEQYGSVSTNLQRGNR` |
| 划分训练/验证/测试,模拟「已完成实验」与「未知候选」 | ✅ | 冷启动 HD≤2 = 已完成实验(GB1/AAV);候选池 HD>2 = 未知候选。AAV:冷启动 10,433 / 候选池 27,832 |

### 2 适应度预测模型

| 条目 | 状态 | 证据 |
|---|---|---|
| baseline 模型 | ✅ | 三级梯队:one-hot / ESM-2 × Ridge / GradientBoosting / MLP,Ridge 为 5-seed bootstrap 集成 — `models/train_ladder.py:55-215`,入口 `models/train_predictor.py`、`models/evaluate_all.py:33-79` |
| **Spearman** | ✅ | `models/train_ladder.py:178-186` |
| **Pearson** | ✅ | 同上 |
| **MSE** | ✅ | 同上 |
| **Top-k 命中率** | ✅ | 同上(默认前 1%) |
| 结果落盘 | ✅ | `reports/predictor_metrics.json`(train/validation/test 三段)、`lab/reports/workflow-v1.1/gb1/predictor_ladder_scaling_ablation.json`、`reports/final-report-v0.6/evidence/predictors.json` |
| 能否识别高 fitness 变体 | ✅ | `models/train_ladder.py:324-332`,字段 `high_fitness_analysis.top_1pct_recall` + `conclusion`;闭环侧另有 `hit_rate_beneficial` — `evolution/campaign.py:205-213` |

### 3 科学智能体设计

仓库有**两条独立的 agent 线**,六项功能在两条线上都有落点。

**五角色 workflow 线**(`agent/pipeline.py` + `evolution/campaign.py`,主用 GB1):

| 试题要求 | 状态 | 证据 |
|---|---|---|
| i. 读取当前实验数据和 top variants | ✅ | `DataAnalyst.run` `agent/pipeline.py:85-98`;top variants `evolution/campaign.py:110-135,205` |
| ii. 总结哪些突变位点可能有益 | ✅ | `HypothesisGenerator.run` `agent/pipeline.py:100-112` |
| iii. 提出下一轮候选突变序列 | ✅ | `MutationDesigner.run` `agent/pipeline.py:114-161` |
| iv. 调用预测模型打分 | ✅ | `FitnessEvaluator.run` `agent/pipeline.py:163-168`;`evolution/campaign.py:232` |
| v. 选择 Top-k 推荐 | ✅ | `evolution/campaign.py:225-267` |
| vi. **给出推荐理由** | ✅ | `CombinationRationale.deterministic_summary` `agent/pipeline.py:147-156`;`ScientificCritic` `:184-204` |

**自主 agent 线**(`agent/auto_researcher.py`,主用 AAV):

| 试题要求 | 状态 | 证据 |
|---|---|---|
| i | ✅ | `analyze_measured`(`best_measured` top-8) |
| ii | ✅ | 同函数 `top_enriched_substitutions` |
| iii | ✅ | `list_pool` / `compose_batch` / `redirect_batch` |
| iv | ✅ | `predict` |
| v | ✅ | `_compose_batch_indices` + compose_batch 取 top-n |
| vi | ✅ | `_graph_rationale` → `knowledge_graph_rationales`;`check_knowledge` |

试题说「可采用简单模块化设计,不要求复杂框架」——五角色线正是它点名的那五个角色,
自主线是 pydantic-ai 的真工具调用 + `message_history` 跨轮连续。

### 4 知识增强设计

规则库 `knowledge/rules.yaml`,试题点名的六条逐个核:

| 试题点名的知识 | 状态 | 证据 |
|---|---|---|
| i. 氨基酸理化性质(疏水/电荷/大小/极性) | ⚠️ | **只有数据块** `rules.yaml:2-22`(charge/size/polarity),**没有对应的门禁 rule**,仅供知识图谱 `has_property` 使用 |
| ii. 保守替换与激进替换 | ✅ | `R-BLOSUM-CONSERVATIVE` / `R-BLOSUM-AGGRESSIVE` `rules.yaml:49-50` |
| iii. 突变数量限制 | ✅ | `R-MAX-MUTATIONS` `rules.yaml:47` |
| iv. 避免终止密码子或异常氨基酸 | ✅ | `R-NO-STOP` `rules.yaml:48` |
| v. 避免一次引入过多突变 | ⚠️ | 与 iii 同一条规则(limit 4),无独立规则 |
| vi. 优先组合历史表现好的单点突变 | ✅ | `R-PRIORITIZE-HISTORICAL` `rules.yaml:52`(advisory),实现 `knowledge/validators.py:91-96` |

知识图谱四种关系:

| 关系 | 状态 | 证据 |
|---|---|---|
| Amino Acid — has_property — Hydrophobic | ✅ | `knowledge/validators.py:124` |
| Mutation — occurs_at — Position | ✅ | `:134` |
| Mutation — improves — Fitness | ✅ | `:139` |
| Variant — contains — Mutation | ✅ | `:135` |

(另有第五种 `changes_to`。查询接口 `knowledge/validators.py:143-209`。)

**比较有无知识增强** ✅ — `knowledge/ablation.py:204-260`(四臂含 `agent_no_knowledge`
vs `knowledge_agent`,配对比较);产物 `lab/reports/knowledge-ablation/metrics.json`、
`rejected_candidates.json`、`knowledge_ablation.png`;图
`reports/final-report-v0.6/figures/f05_knowledge.png`、`f08_aav_ablation.png`。

### 5 虚拟定向进化实验

| 条目 | 状态 | 证据 |
|---|---|---|
| a. 已有训练数据作第一轮结果 | ✅ | 冷启动 HD≤2 |
| b. Agent 提出下一轮候选 | ✅ | 见上 |
| c. 用测试集真实 fitness 作虚拟评估器 | ✅ | oracle = 真值表查表(`measured table lookup`),非预测模型自评 |
| d. **至少 2–3 轮迭代** | ✅ | GB1 3 轮;AAV **6 轮**,远超要求 |
| 观察 fitness 是否逐轮提升 | ✅ | `top10_max_history` 逐轮累计;看板模块① 曲线 |

### 6 结果分析与展示

| 条目 | 状态 | 证据 |
|---|---|---|
| a. 每轮 Top-k 推荐 | ✅ | `reports/campaign_metrics.json` 各 `strategies.*.rounds[].top10`;看板 `app/demo.py:270-283` |
| b. 推荐是否集中在关键位点 | ✅ | 看板 ④-a `app/demo.py:868-922`;`_topk_concentration` `evolution/campaign.py:305-322` |
| c. 四方法比较(随机 / 模型直推 / LLM Agent / 知识增强 Agent) | ✅ | 四策略齐全:`random` / `greedy` / `agent_no_knowledge` / `knowledge_agent`;看板模块① |
| d. **成功案例与失败案例** | ✅ | 逐变体残差 `evolution/campaign.py:282-302`,事件 `campaign.oracle.residuals` `:379-388`;文字分析 `reports/final-report-v0.6/report.md:209-213`(§7.3) |
| 讨论「是否真学到科学家思维」 | ✅ | 报告第七章 + 续页;**最新证据是 v0.8/v0.9 契约实验**(见下「本轮新增」) |

---

## 三、详细要求

### 实验报告

| 条目 | 状态 | 说明 |
|---|---|---|
| PDF 格式 | ✅ | `reports/final-report-v0.6/scientific_report_v0.6_two_column.pdf` |
| **3–5 页** | ❌ | **实测 25 页**(正文 10 + 参考 1 + 附录 14)。v0.5 是 12 页,v0.6 反而更长 |
| 八章齐全且顺序一致 | ✅ | `reports/final-report-v0.6/verification.md` 已核对八章名与顺序 |

**这是目前最需要决定的一条。** 25 页对「3–5 页」是 5 倍。可选:
(a) 正文压到 5 页内、附录另立单独 PDF;(b) 保持现状并在开头说明为何超长;
(c) 出一个 5 页精简版 + 一个完整版。

### 代码

| 条目 | 状态 | 证据 |
|---|---|---|
| GitHub 链接 | ✅ | 公开仓 |
| 含数据处理/模型训练/Agent 推理/候选生成/评估 | ✅ | `evolution/` `models/` `agent/` `knowledge/` `analysis/` |
| README 说明运行环境 | ✅ | `README.md:153-170`(`scripts/install.sh`、Python 3.11+、`requirements.txt`) |
| README 说明数据来源 | ✅ | `README.md:25-34`(Wu et al. 2016,DOI 10.7554/eLife.16965.024,明确不自动下载) |
| README 说明运行命令 | ✅ | `README.md:171-186` |
| README 说明主要结果 | ✅ | `README.md:36-50`(预测器 Spearman 表)+ `:70-95` |
| README 链接是否最新 | ⚠️ | **首页 PDF 链接仍指向 v0.5** — `README.md:11` |
| 小规模数据集可复现 | ✅ | `scripts/smoke.py:1-106`(16 变体合成景观,无需 CSV / ESM / API key),`make smoke` |

### 结果展示

| 条目 | 状态 | 证据 |
|---|---|---|
| a. 野生型 + 若干突变序列 | ✅ | 看板模块③ `app/demo.py:623-730`(含 `VDGV` / `FWAA` 预置);`report.md:35-40` |
| b. 每轮 Top-k 方案 | ✅ | 见上 |
| c. 表格或曲线展示 fitness 提升 | ✅ | `app/demo.py:286-345`(累计 top-10 曲线 + 随机 ±1σ 带);图 `f06_regimes.png` |
| d-i. 发现哪些位点重要 | ✅ | 看板 ④-a |
| d-ii. 为什么选某些替换 | ✅ | `agent/pipeline.py:100-112`;看板②回放 |
| d-iii. 为什么组合某些突变 | ✅ | 看板 ④-b,读 `lab/reports/workflow-v1.1/agent_combination_rationales.json` |
| d-iv. **哪些推荐失败,原因** | ✅ | 逐变体残差事件;`report.md:209-213`。⚠️ 看板里没有独立的失败面板,失败信息散在 ⑥ 与报告里 |

### 资源使用标注

✅ 报告标注了数据来源与 DOI;ESM-2 来源已注明。

---

## 五、加分项(7 条)

| # | 加分项 | 状态 | 证据 |
|---|---|---|---|
| 1 | 主动学习 **/ 强化学习** 策略选下一轮 | ⚠️ | **主动学习 ✅**:UCB 采集 `evolution/campaign.py:258`(λ=0.75)、自适应 exploit 比例 `agent/auto_researcher.py`、停滞回溯 redirect。**强化学习 ❌**,明确决定不做(`reports/final-report-v0.6/evidence/handoff.md:397`) |
| 2 | 不确定性估计(GP 或模型集成) | ✅ | **bootstrap 集成方差**(非 GP)— `models/train_ladder.py:55-157`,`predict` 返回 mean/var;用于 UCB `evolution/campaign.py:258`、`evolution/pool_campaign.py:135` |
| 3 | 比较单点 / 双点 / 多点突变 | ✅ | `analysis/mutation_order.py:1-257`,产物 `gb1_mutation_order.json`(`distribution_by_order` 1–4 阶 + `additive_extrapolation` + `epistasis_by_order`);看板 ⑤-a;图 `f10_order.png` / `f11_epistasis.png` |
| 4 | 蛋白结构信息 **或** 保守位点分析 | ⚠️ | **保守位点 ✅**:ESM-2 逐位熵 `features/conservation.py:1-251`、`analysis/esm_zeroshot_scan.py`,产物 `gb1_conservation.json` / `aav_conservation.json`,负结果如实展示 `app/demo.py:1073-1155`。**3D 结构 ❌ 未实现**,只在未来规划文案里出现 |
| 5 | 知识图谱表示「位点—突变—性质—fitness」 | ✅ | 四类节点齐备 `knowledge/validators.py:117-140`;查询接口 `:143-209` |
| 6 | 可交互 demo(输入野生型自动推荐) | ✅ | `app/demo.py:623-830`,`make demo`;现已并入统一看板 |
| 7 | 讨论连接真实自动化实验平台 | ✅ | `report.md:265-269`(§8.4);更详版含 SiLA 2 在 `reports/final-report-v0.3/report.md:514-525` |

**7 条里 5 条完整、2 条一半。**

---

## 四、考核重点(7 条)自评

| 考核点 | 自评 | 依据 |
|---|---|---|
| 理解定向进化基本科学流程 | ✅ | 冷启动 → 提名 → oracle → 重训 → 再提名的六轮闭环 |
| 处理真实蛋白突变与 fitness 数据 | ✅ | GB1 149,361 / AAV 38,265 真实 DMS 数据 |
| 训练合理的适应度预测模型 | ✅ | 三级梯队 + 四指标 + 上位性代理 |
| 把 Agent 设计成「假设生成—突变设计—模型评估—反馈迭代」 | ✅ | 两条线都是闭环;自主线还有跨轮 `message_history` |
| 合理引入氨基酸性质 / 突变规则 / 知识图谱 | ✅ | 见上,唯理化性质缺独立门禁规则 |
| **通过实验比较证明 Agent 的作用** | ✅ | 四策略同预算比较 + 知识消融 + **v0.8/v0.9 契约 2×2** |
| **分析失败原因,而不是只展示成功样例** | ✅ | 这是本项目最强的一块:见下 |

---

## 本轮新增、试题里没要求但直接答「考核重点」最后两条的东西

这些不在试题字面清单里,但恰好回答「是否能通过实验比较证明 Agent 的作用」与
「是否能分析失败原因」:

1. **撤回过一个自己的错误结论。** 曾把「接入 LLM 后 agent 变差 −36%/−52%」当成主要发现,
   后来查出那不是同预算比较(LLM 臂只提名 105/197 而非 288),归一化后 LLM 臂反而更好。
   已在交接单 §7.11 打作废横幅、§7.14 给正确口径。
2. **v0.8 契约实验**:强制注入残差反思,四臂送测集合逐位相同(48/48 × 6)。
3. **根因定位**:不是模型不会用证据,是工具契约里 `exploit_ratio` 是标量,
   **没有任何取值能表达「别选带 N21D 的候选」**。
4. **v0.9 换契约后**:同模型、同 seed、同注入内容,送测集合分叉并逐轮发散(r6 只剩 8/48);
   `agent_requested` 从 0/20 → 11/11;被排除的 motif **全部**能在此前注入的证据里找到出处。
5. **指标饱和的自我揭发**:八个臂全部在第 2 轮达到候选池真实最优 8.416205,
   即 67% 预算花在答案已找到之后 → 峰值与样本效率两个指标都失去区分力。
   改用致死 motif 复现率后,后段(r4+)四臂为 13.9% / 13.9% / 20.1% / **6.2%**。
6. **一处口径更正**:「AAV 达峰 8.4162 未超越冷启动 9.536457」此前被写成局限,
   实为**数据集构造**——候选池 27,832 条里超过 9.536457 的有 **0 条**,全表最优本身落在 HD=2。
   报告应改为设定说明,不应记作 agent 的失败。

---

## 待办清单(按优先级)

1. **[高] 决定报告页数怎么办**(**2026-09-14 更新:当前受控/交付 PDF 已是 v0.7 的 44 页,README:11 入口仍是 v0.6 的 25 页,两者都远超 3–5 页**)。这是唯一一条硬性格式不符。本条与 `assignment-coverage-audit.md` 的 H33 此前互相矛盾——审计表曾据一份已被同名替换掉的 4 页旧 PDF 判「已交付」,现已改判未达标,两份文档口径统一。裁剪可行性已量:正文八章约 15.8K 字符、附录 A–L.3 共 30 节约 40K 字符。
2. **[中] 加分项①的强化学习、④的 3D 结构**:要么补,要么在报告里明写为何不做
   (「不做」写清理由也是一种交代,总比让人以为漏了强)。
3. **[低] README 首页 PDF 链接改指 v0.6**。
4. **[低] 理化性质补一条独立门禁规则**,或在报告里说明它只作为知识图谱属性使用。
5. **[可选] 看板加一个独立的「失败推荐」面板**,把 d-iv 的证据集中展示
   (现在散在模块⑥与报告里)。
