# V0.5:LLM 池式主动学习 agent 的 explore/exploit 优化 —— 文献调研 + 落地方案

> 承接 `plateau-breaking-methods.md`(V0.3 轮:结论"天花板 = 加性 surrogate 表达上限",已由 V0.4 上位感知 surrogate 解决)。本轮回答新问题:**surrogate 已经很好(CV Spearman ≈0.90,确定性 greedy 288 预算直达真峰 8.416)时,为什么 LLM agent 768 预算都追不上,以及怎么改**。
>
> 证据等级:标 ✔本仓已验证 的来自 `lab/facts/` 与 `lab/reports/agentic-v0.4/`;标(文献主张)的是外部论文结论,本会话未在本仓复现;引用核实状态见文末。检索由本 Agent 完成,综合判断供 CEO 裁定。

## 0. 问题画像(✔本仓已验证,不重复上轮)

V0.4 事件流诊断(F-07B08C97,证据 `agentic.metrics.json` / `agentic.events.jsonl`):

1. **过度探索**:28 次 `list_pool` 调用中 exploit(`predicted_mean`)仅 9 次,explore(`diverse`/`uncertainty`/`random`)19 次;LLM batch 峰值大起大落 `[7.39, 5.13, 5.99, 7.83, 5.83, 6.46, 3.78]`,而确定性 greedy 纯 exploit 稳步 `[7.39, 6.53, 7.83, 8.42]`(第 4 批 192 预算即达真峰)。
2. **不感知 surrogate 质量**:代码根源在 `agent/auto_researcher.py:34-51` —— system prompt 硬编码"surrogate rank correlation only **~0.6** and it systematically underrates high-order epistatic peaks. Do NOT blindly test its top predictions",且换上 0.90 的 `EpistasisRidgePredictor` 后一字未改;user prompt(:296-301)与 gate_note(:268-275)还每轮强制 "**Deliberately** mix exploitation with exploration"。即:**agent 不是自主选择探索,是被过时信念 + 三处指令推着探索**。
3. **工具调用脆弱**:6 轮中 2 轮在 LLM 调用层抛 `string index out of range`(未归因到具体工具/参数),触发 `no_test` → harness 代打 exploit 批,浪费整轮 agent 决策;12 轮版再犯 1 次,16 轮版 0 次(偶发)。
4. **加预算无效**:12 轮/576 于 round 5 达 7.829 后 7 轮全平;16 轮/768 反降至 7.5301(report.md:45:"LLM 的短板不是 budget/rounds 不足,是自主 explore/exploit 决策的利用效率确实不如纯 greedy")。

笼子约束(落地映射的坐标系):6 工具(`analyze_measured`/`predict`/`list_pool(n, by)`/`check_knowledge`/`test`/`best_so_far`);`list_pool.by ∈ {predicted_mean(exploit), uncertainty(explore=bootstrap 方差), diverse(UCB式+扰动), random}`;每轮 batch=48、每轮模型请求上限 20 次;`test` 预算截断;知识门只塑形(`list_pool` 已预过滤)不代选;探索分 = 3-seed bootstrap Ridge 方差。

---

## 1. 重点(1):surrogate-quality-aware / adaptive acquisition

### 核心思想
探索的边际价值是 **surrogate 质量与所处阶段的函数**:模型差/早期(不确定度校准差)时探索(甚至纯随机)有益;模型好/后期时,不确定度引导的探索不再有增益,纯利用(greedy)是极强 baseline。自适应采集 = 显式或隐式地随质量/轮次把 explore 权重降下来。

### 代表工作
- **Greenman, Amini, Yang, "Benchmarking uncertainty quantification for protein engineering", PLOS Comput Biol 21(1):e1012639, 2025**(✔书目已核)。在 GB1/AAV 等数据集上系统比较 greedy vs UCB vs Thompson vs 不确定度采样 vs random:(文献主张)"the uncertainty-based methods almost always perform better than the random baseline but **never outperform greedily sampling**";"UCB sampling performs about the same as greedy sampling";"in the early stages of active learning when a model's uncertainty estimates are poorly calibrated, it may be advantageous to sample with at least some randomness"。特别扎心的一条:某些 UQ 方法(如 evidential)+ UCB **在 AAV 数据集上比 random 还差**(同上)。→ 直接适用于本题:我们正是 AAV + 高 CV surrogate + 后期阶段,explore 19/28 是系统性浪费。
- **Yang, Lal, …, Yue, Arnold, "Active learning-assisted directed evolution" (ALDE), Nat Commun 2025**(bioRxiv 2024.07.27.605457,✔书目已核)。acquisition 即 UCB 家族:greedy = UCB(β=0) 特例;湿实验最终选 **Thompson sampling**(DNN ensemble + one-hot),理由是模拟中表现最一致且 batch 内独立采样天然带来多样性;(文献主张)"performance in ALDE simulations (by max fitness achieved) is not necessarily correlated to how calibrated the uncertainties are" —— **静态校准指标不直接预测采集收益**。
- **Thompson sampling = 内在退火**(无需显式 schedule):后验(预测分布)随数据变尖,采样自动从"多样探索"过渡到"集中于最优区"。这是"自适应 explore/exploit"最优雅的免调参形态,Russo et al.《A Tutorial on Thompson Sampling》(Found. Trends Mach. Learn. 2018,书目待核实)是标准参考。
- **AdaLead, Sinai et al., arXiv:2010.02141, 2020**(正式发表 venue 待核实):**按需探索**而非固定混合——进步停滞时加大突变/随机性,找到改进立刻转贪心。与"每轮强制混合"正好相反。
- **β/ε 调度传统**:GP-UCB 理论 β_t 随信息增益演化(Srinivas et al., ICML 2010,书目待核实);工程实践中 ε-greedy 退火是 bandit 标配;近期 Candelieri et al., "When to Explore and When to Exploit: Adaptive Decisions in Bayesian Optimization", MAKE 2026(卷期待核实)把 explore/exploit 决策本身作为学习对象。
- 批内多样性(替代"整批探索"):González et al., "Batch Bayesian Optimization via Local Penalization", AISTATS 2016 —— greedy 逐点选 + 局部惩罚保多样性,exploit 主导但 batch 不塌缩。

### 笼内落地
1. **运行时滚动质量信号**(answer-agnostic,零新增测量):每轮 `test` 后,对当批算 predicted-mean vs measured-fitness 的 Spearman(数据现成)。这比静态 CV 更贴近 ALDE 的警示——静态校准≠采集收益,滚动实测直接反映"surrogate 在当前区域还有多可信"。
2. **探索配额退火**:显式 ε_t 调度(如 ε 从 round1 的 ~0.5 线性/几何退火到 round6 的 ≤0.1),并与质量信号门控:滚动 Spearman ≥0.85 时强制 ε≤0.1。对 LLM 的表述:"explore 名额每轮至多 ⌈ε_t×48⌉ 个"。
3. **给 `list_pool` 加 `by="ts"`**:用现有 (mean, var) 做逐候选高斯后验抽样(`mean + z·sqrt(var)`, z~N(0,1) 排序),模型变准时 var 缩小、采样自动收紧——Thompson 内在退火,复用现有 bootstrap 方差,改动 ~5 行。
4. 静态 CV 分(0.898, F-C08A6CF2)只作初始先验注入;注意该 3 折 CV 脚本未随仓提交,复算以 `analysis/epistasis_surrogate_scan.py` 的已提交输出口径为准。

---

## 2. 重点(2):好 surrogate 下的采集取舍 + LLM agent 的劣势与补救

### 核心思想(文献主张汇总)
- **采集函数层面**:好 surrogate 上 greedy 几乎不可击败(Greenman 2025;ALDE 湿实验选 TS 也是"最不坏"而非"碾压 greedy");UCB≈greedy;TS 居中;qEI 计算贵且无增益(ALDE)。EI 在噪声/大 batch 下与 UCB 表现相近,不赘。
- **LLM agent 层面的系统性劣势**:
  - **LLAMBO**(Liu et al., "Large Language Models to Enhance Bayesian Optimization", ICML 2024, arXiv:2402.03721→**2402.03921**,✔已核):LLM 当 surrogate/采集器在**低数据早期**有增益,"especially in the early stage";言下之意(及消融)数据充足后增益消退——与我们"surrogate 已好、LLM 仍插手采集反而亏"同构。
  - **LLM 直接做序贯决策不可靠**:"Emergent Exploitation Bias in Meta-Bandit LLM Training"(arXiv:2509.24923,ICLR 2026 poster,作者待核实)证明 SFT/RL 训练会系统性塑形 LLM 的探索行为(且偏差方向取决于训练);PNAS 2025(PMC12207438,书目待核实)报告 LLM 决策偏差较人类放大。方向虽与我们的"过度探索"相反,但共同结论一致:**LLM 的 explore/exploit 校准不可依赖,需要外部机制约束或替代**。
  - **PSRL-LLM**(Arumugam, "Toward Efficient Exploration by Large Language Model Agents", arXiv:2504.20997,ICLR 2026 投稿,✔已核):处方不是让 LLM 自己探索,而是 **LLM 提供结构化先验、采样决策交给经典算法(Posterior Sampling)** —— "LLM 提议、算法决策"的分工。
  - **BioDesignBench**(Kim & Romero, "Benchmarking and behavioral characterization of LLM agents for protein design", bioRxiv 2026.05.06.723381,✔已核):76 个蛋白设计任务上,强 LLM agent(DeepSeek V3、GPT-5)**可以**超过确定性 pipeline(54.5 分),但 (文献主张)"the underlying tools, rather than the orchestrating agent, primarily determine output quality"——工具链决定质量下限,agent 决定编排;行为瓶颈是"evaluation depth"(把随机工具当确定性 oracle、从不淘汰候选),且"the gap is **behavioral rather than a fundamental capability constraint**"。**结构化行为干预**(强制多候选→跨互补指标评估→排序提交)使 DeepSeek +9.3、GPT-5 +15.9(p<0.01)。反例警示:Gemini 2.5 Pro 因系统性 MCP 工具调用失败只得 8.8 分——工具失败可整链摧毁(见重点 4)。

### 笼内落地(LLM 相对固定采集的补救 = 角色重划)
LLM 的比较优势在**提议、解释、跨轮假设**(BioDesignBench 的骨架生成段 130–185% 人类水平 vs 打分段 14%);explore/exploit 配比是**统计决策**,不是 LLM 的强项。三个梯度:
- **梯度 A(软)**:保留 LLM 全权,但 prompt 注入真实质量信号 + 探索配额上限(重点 1+3 落地),行为引导而非权限剥夺。
- **梯度 B(硬)**:**exploit-default 内核 + LLM 提名权**:每轮 harness 预生成 exploit 批(如 36/48 = `list_pool(36,"predicted_mean")`),LLM 只支配剩余 12 个名额(自由 explore/知识提名/组合假设)并输出科学理由。对齐 PSRL-LLM 的分工与 BioDesignBench 的"强制结构"哲学;LLM 的探索冲动被限制在不会拖垮主干的份额里。
- **梯度 C(极简)**:LLM 完全退出采集,只做 round 间的假设总结与下一轮位点建议(写作/分析角色),采集 = greedy 或 TS。这是"确定性 greedy 已 8.416"路线的保守上限,可作为 V0.5 消融的对照臂。

---

## 3. 重点(3):让 agent 感知 surrogate 质量的 prompt / 工具设计

### 核心思想
LLM 对自身与外部工具的可信度没有内省通道,但**能消费显式给出的置信/质量信号**:(文献主张)Kadavath et al., "Language Models (Mostly) Know What They Know"(arXiv:2207.05221, 2022,书目待核实)显示 LLM 可被引导表达并利用校准的置信;LLAMBO 的做法是把历史观测与配置作为上下文注入;CRITIC(Gou et al., ICLR 2024,书目待核实)证明工具反馈可校正 LLM 判断。**关键:注入"事实信号"优于注入"死命令"** —— BioDesignBench 的 guided 模式给强 agent(DeepSeek)反而 -2.0 分(约束过死),给弱 agent +9.1;而"强制评估深度"类干预对所有强模型显著为正。

### 笼内落地(直接对应诊断②的代码根源)
1. **删除/动态化 system prompt 里的硬编码信念**(`auto_researcher.py:34-51`):"~0.6 + underrates peaks" 改为每轮注入真实数据:`"surrogate 3-fold CV Spearman = {cv_spe}(训练时测);最近 {k} 批 predicted-vs-measured Spearman = {rolling_spe};exploit 批 top-10 预测命中率 = {hit_rate}"`。滚动指标在 harness 侧算好,经 user prompt 或 `analyze_measured` 输出。
2. **`analyze_measured` 扩展为 `surrogate_report`**(或新增工具):返回 CV Spearman、滚动批内 Spearman、近 K 批 exploit 命中率(预测 top-k ∩ 实测 top-k)、方差-实测误差相关(校准的粗诊断)。全部 answer-agnostic(只用已测数据)。工具化而非只放 prompt,让 agent 能**主动查询**并在推理链里引用数字。
3. **指令条件化而非命令化**:把"Deliberately mix exploitation with exploration"改为决策规则文本:"若 rolling Spearman ≥0.85:surrogate 可信,本批 ≥80% 名额用 predicted_mean,探索名额 ≤⌈ε_t×batch⌉;若 <0.6 或连续 2 批 exploit 命中率为 0:提高探索/多样性配额"。即把重点(1)的退火调度**写进 agent 可读的策略**,而不是依赖模型自觉——BioDesignBench 的教训是行为要被结构塑造,prompt 里的形容词(deliberately/balance)不构成行为约束。
4. **负结果反馈回路**:每轮把上一批"探索名额的实际收益"(explore 候选的实测 fitness vs 同批 exploit 候选)注入下一轮 prompt——让浪费可见,压制惯性探索。

---

## 4. 重点(4):工具调用鲁棒性

### 核心思想
偶发工具调用失败不是小噪声:(文献主张)τ-bench(Yao et al., arXiv:2406.12045, 2024,✔已核)以 pass^k 度量一致性,顶级模型 function calling 也随重复试验大幅掉点;BioDesignBench 中 Gemini 2.5 Pro 因系统性 MCP 调用失败全链崩溃(8.8/100)。工程共识与 PALADIN(arXiv:2509.25238, 2025,作者待核实)的自修复框架一致:**① 入口 schema/参数校验挡掉畸形调用;② 错误结构化回喂、同轮自校正;③ 区分 schema 病(高验证错误率 = 工具描述/schema 有问题)与瞬时错误(需重试)**;④ 约束解码(如 outlines, Willard & Louf, arXiv:2307.09702,书目待核实;或 API 侧 structured outputs)可从生成端消除参数畸形。

### 笼内落地(对应诊断③)
1. **工具入口校验**:所有吃序列的工具(`predict`/`check_knowledge`/`test`)先验长度、氨基酸字符集、池内性,非法即返回结构化错误对象(`{"error": "invalid_sequence", "hint": "…", "received": …}`)而非抛裸异常——`string index out of range` 的最可能来源就是畸形序列参数触发了工具内索引。
2. **同轮恢复取代整轮放弃**:现在 `ag.run_sync` 层异常 → `no_test` → harness 代打(:306-312),损失的是整轮 LLM 决策。改为 per-tool `try/except` + pydantic-ai 的 `ModelRetry`(把异常文本作为工具结果回喂,让模型当轮修正重发);只有重试额度(如 2 次)耗尽才降级代打。
3. **事件归因**:`agent.llm.round_error` 增加 tool 名、参数摘要、异常栈首行字段,使下次消融能区分"哪个工具的哪种畸形"而非黑盒失败。
4. (可选)`request_limit=20` 硬编码与未用的形参 `request_limit=60` 合一;重试额度计入限额。

---

## 5. V0.5 改法提名(给 CEO 裁定,按证据强度 × 改动成本排序)

**提名 1(首选):质量感知 prompt + 退火探索配额(重点 1+3 的合并落地)。**
改动面:system/user prompt 三处文案 + `analyze_measured`/新工具注入 CV/滚动 Spearman/命中率 + 探索名额上限 ε_t(质量门控)。零新增测量、不动 surrogate、不动预算。预期:exploit 占比从 9/28 提到 ≥70%,LLM 曲线贴合 greedy 的稳步爬升;若 6×48 仍不达 8.416,则证明剩余差距来自提案质量而非配比(信息量大)。证据链:Greenman 2025(greedy 不可被不确定度法打败,AAV 上 UQ+UCB 可比 random 差)+ AdaLead(按需探索)+ F-07B08C97(本仓探索浪费实测)+ BioDesignBench(行为干预有效)。

**提名 2:exploit-default 内核 + LLM 提名/解释权(重点 2 梯度 B)。**
每轮 36/48 由 harness 直接下 exploit 批,LLM 支配 12 个自由名额(知识驱动组合/上位假设)+ 全部科学解释。把采集的统计决策收归算法,LLM 退到其强项(提议/解释,对应试题"科学智能体"叙事,报告里也更好写)。证据链:PSRL-LLM 分工哲学 + LLAMBO(数据充足后 LLM 增益消退)+ BioDesignBench("tools determine quality, agent determines orchestration")。与提名 1 互为消融臂:1 失败且 2 成功 ⇒ LLM 决策不可救药须剥夺;1 成功 ⇒ 软引导够用。

**提名 3:工具鲁棒性三件套(重点 4,独立于 1/2,建议无条件做)。**
入口校验+结构化错误、`ModelRetry` 同轮恢复、事件归因到工具/参数。直接消灭"2/6 轮整轮浪费"(6 轮版 round1/round3),对 12/16 轮长跑更关键(越长的 run 撞上偶发错误的期望次数越多,16 轮 145 次工具调用只侥幸 0 错)。证据链:τ-bench pass^k + PALADIN + BioDesignBench(Gemini 工具失败全链崩溃)。

**顺序建议**:3(半天级,先堵漏)→ 1(主实验)→ 2(消融/对照)。三者合计不动 surrogate、不动池、不动预算、不看任何测试标签,answer-agnostic。

---

## 附:引用核实状态
- ✔已核(本会话核对书目/原文):Greenman et al. 2025(PLOS Comput Biol 21(1):e1012639,DOI 10.1371/journal.pcbi.1012639);ALDE(Yang et al., bioRxiv 2024.07.27.605457 / Nat Commun 2025);LLAMBO(arXiv:2402.03921, ICML 2024);Arumugam PSRL-LLM(arXiv:2504.20997);BioDesignBench(Kim & Romero, bioRxiv 2026.05.06.723381,v2 2026-06-28);τ-bench(Yao et al., arXiv:2406.12045);González et al. AISTATS 2016;meta-bandit 偏差(arXiv:2509.24923, ICLR 2026 poster)。
- **待核实**:AdaLead 正式发表 venue(arXiv:2010.02141 之外);arXiv:2509.24923 作者列表;PNAS 2025 认知偏差论文(PMC12207438)完整书目;PALADIN(arXiv:2509.25238)作者与最终 venue;Kadavath et al. arXiv:2207.05221;CRITIC(Gou et al., ICLR 2024);outlines(Willard & Louf, arXiv:2307.09702);Russo et al. Thompson tutorial(2018);Srinivas et al. GP-UCB(ICML 2010);Candelieri et al. MAKE 2026 卷期;LLAMBO"后期增益消退"的原文精确表述(摘要级证据)。
- ✔本仓事实:F-07B08C97(事件流诊断)、F-C08A6CF2(CV 0.898@alpha=100;3 折 CV 计算脚本未随仓提交,复算以已提交的 `analysis/epistasis_surrogate_scan.py` 输出为准)、`lab/reports/agentic-v0.4/report.md` 及 metrics/events JSON。
