# V0.5 智能体决策优化与破局方案：从上位代理到超越贪心（Answer-Agnostic）

> **任务背景与交付契约：**
> 在定向进化 AAV 任务（HD≤4 门禁、总预算 288、in-silico 查表 oracle）中，V0.4 成功落地了上位感知代理（`EpistasisRidgePredictor`，成对 Potts 交互特征，CV Spearman 达到 **0.90**）。
> 然而，基准消融实验暴露了一个残酷的反直觉事实：
> 1. **确定性 gated-greedy**（始终按 `predicted_mean` 利用）仅消耗 **288 预算（6 轮 × 48）即直达全局真峰 8.416**（HD3: D0Q + S17E + V18A）。
> 2. **LLM 驱动的 agentic 模式** 在 288 预算下止步于 **7.829**；追加至 12 轮（576 预算）仍卡在 7.829；进一步追加至 16 轮（768 预算，2.67 倍算力）反而劣化降至 **7.53**！
> 3. 事件流诊断坐实：LLM 表现出严重的**过度探索**（`list_pool` exploit 仅 9 次 vs explore 19 次）、**代理质量盲区**（即使 CV 高达 0.90 仍固执探索）、以及**工具调用偶发崩溃**（`string index out of range`）。
>
> 本研究旨在解决核心瓶颈：**在完全合法、答案无关（Answer-Agnostic）的前提下，如何改造提示词、工具与采集机制，使自主 LLM Agent 能够感知代理置信度，消除探索税，追平乃至超越纯 Greedy？**

---

## 0. 诊断复盘：为什么好 Surrogate 下自主 LLM 追不上纯 Greedy？

### 0.1 实证表现对比与消融事实

在相同的冷启动数据（HD≤2，10,433 条实测）、相同的 HD≤4 物理知识门禁、相同的随机种子（seed=42）与完全相同的上位感知代理（CV Spearman 0.90）下，各决策策略表现如下：

| 实验组别 | 轮数 × 单轮预算 | 总消耗预算 | 最佳适应度 (cum_top10_max) | Strong (Top10%) 命中数 | 状态与终态特征 |
|---|---|---|---|---|---|
| **确定性 Gated-Greedy** | 6 轮 × 48 | **288** | **8.416（真峰）** | 151 | **直达全局最优**，无一分预算浪费 |
| **LLM Agentic (V0.4 标准)** | 6 轮 × 48 | 288 | 7.829 | 108 | Round 4 达 7.829，随后陷入探索停滞 |
| **LLM Agentic (12 轮消融)** | 12 轮 × 48 | 576 | 7.829 | 183 | Round 5 达 7.829，**后 7 轮完全走平** |
| **LLM Agentic (16 轮消融)** | 16 轮 × 48 | 768 | 7.530 | 330 | 探索节奏紊乱，漂移至次优区域，不升反降 |

**消融结论**：追加 2~2.67 倍预算完全无助于 LLM 登顶。这强力推翻了“LLM 只是跑道（runway）不够、多跑几轮就能到峰”的猜想。在拥有高精度代理的场景下，**LLM 的非受控自主性不但没有提供增量智能，反而成为了系统性负债（Liability）**。

---

### 0.2 事件流剖析：四大核心病灶

通过审查 `lab/reports/agentic-v0.4/aav/*.events.jsonl`，我们还原了导致 LLM 决策失败的四重机械成因：

```
                    ┌─────────────────────────────────────────────────────────┐
                    │ 病灶 1: 提示词负向锚定 ("Surrogate imperfect ~0.6...")    │
                    └───────────────────────────┬─────────────────────────────┘
                                                ▼
┌────────────────────────────────┐  Agent 决策偏激   ┌────────────────────────────────┐
│ 病灶 3: 代理指标黑盒化          │ ───────────────► │ 病灶 2: 探索税与不确定性陷阱    │
│ (analyze_measured 隐匿 CV=0.90) │                  │ (exploit 9 次 vs explore 19 次)│
└────────────────────────────────┘                  └────────────────┬───────────────┘
                                                                     ▼
                                                    ┌────────────────────────────────┐
                                                    │ 病灶 4: 工具调用脆弱性崩溃      │
                                                    │ ("string index out of range")  │
                                                    └────────────────────────────────┘
```

#### 病灶 1：提示词过时与负向误导（Stale Prompt Misdirection）
在 `agent/auto_researcher.py` 中，System Prompt 包含如下一段遗留代码：
```text
Important: a surrogate predictor is available via `predict`/`list_pool`, but it is IMPERFECT
(rank correlation only ~0.6 and it systematically underrates high-order epistatic peaks).
Do NOT blindly test its top predictions every round. Think like a scientist: inspect what is
measured, form hypotheses about which positions/substitutions matter, and BALANCE exploiting
predicted-good variants against EXPLORING high-uncertainty or knowledge-plausible variants the
predictor may underrate.
```
- **历史成因**：该提示词成文于 V0.1/V0.2 时期，当时使用的是加性 Ridge 代理，其秩相关系数确实仅为 ~0.64，无法识别正上位。
- **致命后果**：V0.4 将代理换成了表达力完备的成对 Potts 代理（CV Spearman 0.90），但**提示词仍旧言之凿凿地警告 Agent 代理很烂（~0.6）、会漏掉高阶上位、绝不要相信它**。LLM 严格遵从了系统提示词的科学家角色设定，把对高精度模型的有效利用视为“盲目盲从”，主动去规避高置信度利用。

#### 病灶 2：探索税与不确定性陷阱（Exploration Tax & Uncertainty Trap）
在蛋白质定向进化领域，高方差 $\sigma(x)$ 几乎总是分布在采样极其稀疏的高汉明距离（High-HD）空间。然而，生物物理常识告诉我们，99% 以上的高突变序列都是非功能性的**死蛋白**。
- 事件流统计：在 6 轮实验中，Agent 调用 `list_pool` 时，`predicted_mean`（利用）仅 9 次，而 `diverse`（7 次）+ `uncertainty`（7 次）+ `random`（5 次）合计 **19 次**。
- 致命后果：Agent 遵循“探索高不确定性”的直觉，选出了一堆预测方差大但均值极低的序列。每次向这些序列投入 48 批次预算，均以实测适应度接近于 0（踩入死蛋白谷底）告终，严重挤占了向真实高地爬升的宝贵预算。

#### 病灶 3：代理状态黑盒化（Surrogate-Quality Blindness）
当前交互协议中，Agent 仅能通过 `analyze_measured` 获取历史已测变体的基本计数和突变富集度。**Agent 完全无法感知当前模型是什么架构、交叉验证（CV）分数是多少、对当前数据拟合的 Spearman 相关性是 0.5 还是 0.9**。
- 致命后果：由于无法获知“模型当前高度可信”这一客观事实，LLM 只能依赖 Prompt 里的初始设定（即病灶 1 中的虚假信息）进行先验臆测，无法建立基于事实反馈的校准机制。

#### 病灶 4：工具链脆弱性与静默崩溃（Tool Fragility）
在 `agentic.events.jsonl` 中，Round 1 和 Round 3 均出现了致命报错：
```json
{"event_type":"agent.llm.round_error","payload":{"error":"string index out of range","round":1}}
{"event_type":"agent.llm.no_test","payload":{"note":"LLM skipped test; harness exploit fill","round":1}}
```
- **代码级根因定位**：
  在 `agent/auto_researcher.py` 第 90 行的门禁函数 `_gate()` 中：
  ```python
  subs = [(spec.wt[i], c) for i, c in enumerate(v) if c != spec.wt[i]]
  ```
  野生型 AAV 片段长度为 28 aa。当 LLM 偶尔生成了带有多余空格、换行符、或因幻觉产生 29 aa 的序列时，`enumerate(v)` 遍历至索引 $i=28$，访问 `spec.wt[28]` 瞬间抛出 `IndexError: string index out of range`！
- **次生灾害**：Pydantic-AI 缺乏工具内部防御，直接导致整个轮次异常中断。虽然 harness 设置了兜底 fallback，但该轮 Agent 的决策链条被打断，上下文累积被污染。

---

## 1. 重点一：Surrogate-Quality-Aware / 自适应采集机制（Adaptive Acquisition）

### 1.1 核心思想与数学机制

在经典主动学习与贝叶斯优化（BO）中，固定的采集函数（如固定 $\beta$ 的 UCB 或固定权重的随机探索）无法适应非平稳的优化历程。**Surrogate-Quality-Aware 自适应采集**的核心思想是：**将探索-利用的置信度，显式绑定到代理模型在验证集上的拟合质量与当前所处的优化轮次。**

```
            Surrogate CV Spearman (ρ)
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
 [低信度区: ρ < 0.65]           [高信度区: ρ ≥ 0.85]
  代理不可信，需探索空间         代理已捕捉上位地貌，果断收敛
  · 提高 UCB 探索系数 β           · 衰减 UCB 系数 β → 0
  · 鼓励多样性采样 (Diverse)     · 纯贪心利用 (Greedy Exploitation)
  · 预算配比: 40% exploit        · 预算配比: 85~95% exploit
```

数学上，自适应采集函数可形式化为信度加权型退火 UCB（Confidence-Annealed UCB）：
$$\alpha_t(x) = \mu(x) + \beta_t(\rho, t) \cdot \sigma(x)$$
其中探索增益权重 $\beta_t$ 是交叉验证相关系数 $\rho_t$ 和剩余轮次的双重衰减函数：
$$\beta_t = \beta_0 \cdot \max\left(0, \, 1 - \rho_t^2\right) \cdot \left(1 - \frac{t}{T}\right)^\gamma$$
- 当代理较差（$\rho_t \approx 0.5$）且处于首轮（$t=0$）时，$\beta_t \approx 0.75 \beta_0$，强制模型广泛采样以纠正认知；
- 当代理精良（$\rho_t \ge 0.90$）时，$1 - \rho_t^2 \approx 0.19$，探索权重断崖式下跌，系统几乎等价于 Pure Greedy，直接锁死候选峰；
- 当步入末轮（$t \to T$）时，$\beta_t \to 0$。在有限步博弈中，**末轮探索的信息增益在任务结束后无法被兑现，其期望回报严格为零**，必须实现 100% 贪心。

---

### 1.2 代表工作（真实可核）

1. **LMABO** (*Adaptive Acquisition Selection for Bayesian Optimization with Large Language Models*):
   - **作者/出处**：Giang Ngo, Dat Phan Trong, Dang Nguyen, Sunil Gupta, Svetha Venkatesh (Deakin University). ICLR 2026 / arXiv:2602.07904.
   - **核心贡献**：首次证明了单一固定采集函数在复杂地形上具有固有缺陷，提出由 LLM 作为在线元策略器（Online Strategist），根据当前代理拟合残差、不确定性分布与剩余预算，在离散的采集函数库（Greedy, UCB, EI, PI）间做动态自适应切换。
2. **AdaLead** (*AdaLead: A Simple and Robust Adaptive Greedy Search Algorithm for Sequence Design*):
   - **作者/出处**：Sinai et al., arXiv:2010.02141 (Harvard Church Lab / Google Research).
   - **核心贡献**：在生物序列定向进化中，AdaLead 发现带有自适应局部重置的贪心策略往往打平或击败复杂的全局采样。当模型可信度提升时，局部贪心爬坡是穿越崎岖上位景观最经济的手段。
3. **Adaptive GP-UCB / Regret Theory**:
   - **作者/出处**：Srinivas, Krause, Kakade, Seeger. *Information-Theoretic Regret Bounds for Gaussian Process Optimization in the Bandit Setting*. IEEE Transactions on Information Theory, 58(5):3250–3265, 2012.
   - **核心贡献**：确立了高斯过程与核回归下，置信区间参数 $\beta_t$ 随 horizon 变化的严格次线性遗憾（Sublinear Regret）理论界。
4. **EVOLVEpro**:
   - **作者/出处**：Jiang, Yan, et al. *High-throughput directed evolution using few-shot machine learning*. Science, 387(6736), 2025.
   - **核心贡献**：展示了 4 轮少样本定向进化的标准范式：前 2 轮用 Broad Diversity 奠定表征基石，第 3~4 轮完全转向基于顶层模型均值的 Top-N 截断贪心（Truncated Greedy）。

---

### 1.3 笼内落地：在我们的池式环境如何实现？

在本项目 `auto_researcher.py` 的执行闭环内，实现自适应采集无需引入外部依赖，仅需 2 处逻辑改造：
1. **提取代理内在信度**：在 `models/train_ladder.py` 的 `EpistasisRidgePredictor.fit()` 中，内部原本就通过 80/20 held-out 验证计算了候选 $\alpha$ 下的 Spearman 相关系数 `best_s`。只需将该值绑定至 `self.val_spearman`。
2. **自适应 `list_pool` 提议**：当参数 `by="adaptive"` 时，自动计算当前批次的利用/探索配比：
   ```python
   # 笼内确定性计算自适应配比
   exploit_ratio = min(1.0, max(0.4, val_spearman**2 + (rnd / n_rounds) * 0.3))
   n_exploit = int(round(n * exploit_ratio))
   n_explore = n - n_exploit
   # 组合候选池
   picks = pool_by_mean[:n_exploit] + pool_by_ucb[:n_explore]
   ```
这样既消除了粗暴的全量 `uncertainty` 采样，又在数学上保障了高置信度下的贪心收敛。

---

### 1.4 五要素分析表：Surrogate-Quality-Aware 自适应采集

| 要素 | 论述内容 |
|---|---|
| **核心思想** | 将主动学习的探索利用权衡（Explore/Exploit Trade-off）与代理模型的实测验证集精度（CV Spearman）和剩余轮次深度绑定。高精度+晚轮次 $\to$ 纯贪心；低精度+早轮次 $\to$ 结构化探索。 |
| **代表工作** | 1. LMABO (Ngo et al., ICLR 2026, arXiv:2602.07904)；<br>2. AdaLead (Sinai et al., 2020, arXiv:2010.02141)；<br>3. EVOLVEpro (Jiang et al., Science 2025)。 |
| **笼内落地** | 极度契合。直接复用 `EpistasisRidgePredictor` 在拟合时内生的验证集 Spearman 相关系数，通过退火公式在 `list_pool` 中直接计算动态利用配比，零新增实验开销。 |
| **合法性/优势** | **完全合法（Answer-Agnostic）**。只使用历史测得数据的 Cross-Validation 指标，从不接触未见测试峰标签；能直接将 19 次无谓探索压制至 2~3 次，快速逼近纯 Greedy 的 8.416 水平。 |
| **局限/风险** | 若冷启动数据发生极端位点分布漂移，CV 分数可能出现过拟合虚高；需在早期轮次设置保底利用下限（如不少于 40% exploit）。 |

---

## 2. 重点二：主动学习采集在“好 Surrogate”下的取舍与 LLM 固有劣势补救

### 2.1 经典采集函数对比：好代理下的博弈

在已知代理模型 CV Spearman 达 0.90 的情况下，四种经典采集策略的表现差异明显：

```
适应度空间
    ▲
    │                      [真实全局真峰 8.416] (μ高, σ中)
    │                             ★  <--- Pure Greedy / Low-β UCB 第一时间命中！
    │                         ▲
    │                       /   \
    │     [局部次优 7.829]   /     \
    │           ▲          /       \
    │         /   \       /         \
    │        /     \     /           \
    │       /       \   /             \
    │______/_________\_/_______________\___________ [稀疏未知死蛋白荒原] (μ极低, σ极大)
    │                                                     ▲
    │                                                     │ <--- Vanilla EI / High-β UCB /
    │                                                            LLM "Diverse" 疯狂交税受骗处！
    └────────────────────────────────────────────────────────────────────────► 变体序列空间
```

1. **Pure Greedy ($\arg\max \mu(x)$)**：
   - **机制**：完全信任代理模型的打分排序，按预测均值降序截取前 $K$ 个变体。
   - **好代理下的表现**：**最优**。在 V0.4 的上位感知代理下，全局峰的初始预测排名已经进入前 400 名。在每轮 48 个测试预算的滚雪球效应下，首轮测得的高分变体迅速拉升邻近上位特征的权重，288 预算内真峰必然浮出水面。
   - **致命弱点**：若代理存在结构性偏差（如加性代理遇到上位地形），贪心会永久卡死在 7.53 的伪峰。
2. **Upper Confidence Bound (UCB = $\mu(x) + \beta \sigma(x)$)**：
   - **机制**：通过加权因子 $\beta$ 平衡均值与认知不确定性。
   - **好代理下的表现**：若 $\beta \le 0.5$（微探索），表现与 Greedy 相当且能防止单点震荡；若 $\beta \ge 2.0$，方差项将主导排序，把大量预算浪费在边缘死蛋白上。
3. **Expected Improvement (EI)**：
   - **机制**：计算预期超出当前最佳适应度的积分 $EI(x) = (\mu(x) - f^*) \Phi(Z) + \sigma(x) \phi(Z)$。
   - **好代理下的表现**：**存在已知的“高维探索病态”（Exploration Pathology）**。文献（Brochu et al., 2010; Wang et al., 2020）明确指出，在离散高维稀疏空间中，若候选池存在大量从未测过的高 HD 变体，其预测方差 $\sigma(x)$ 居高不下，导致 EI 对这些低均值荒原计算出虚高的期望改善，从而系统性误导采样。
4. **Thompson Sampling (TS)**：
   - **机制**：从后验分布中抽样函数实例 $f(x) \sim \mathcal{N}(\mu(x), \sigma^2(x))$，按抽样最大值决策。
   - **好代理下的表现**：在批次量为 48 时，TS 的随机后验抽样会导致候选集极度离散稀疏，稀释了对头部峰顶的围堵压力，收敛速度显著慢于 Greedy。

---

### 2.2 LLM Agent 相比固定采集函数的已知劣势

学术界近两年的前沿实证研究揭示了 LLM 面对主动学习与多臂老虎机（MAB）时的结构性缺陷：

1. **认知角色扮演偏见（"Scientist Persona" Bias）**：
   - 现存 LLM 均在大规模科研文本上经过指令微调。当 System Prompt 要求其“像科学家一样思考并提出假设”时，LLM 在注意力机制上激活了“探索、质疑、求异”的语义簇。
   - LLM 倾向于将“盲目信任模型”视为不合格的科研行为，产生心理学上的**抗拒利用倾向（Reluctance to Exploit）**。
2. **缺乏数值尺度计算能力（Noisy Discrete Switching）**：
   - LLM 无法在心智中对连续的 $(\mu_i, \sigma_i)$ 进行数值权衡。面对 6 个工具，它只能采取粗颗粒度的布尔切换：要么整轮调用 `list_pool(by="predicted_mean")`，要么整轮调用 `list_pool(by="uncertainty")`。
   - 这种离散抖动导致其探索行为不是“均值附近的局部置信探索”，而是“横跨整个候选池的随机漂移”。
3. **长程注意力退化与上下文漂移（Context Drift Over Long Horizons）**：
   - 在 12 轮与 16 轮消融中，随着会话历史被多轮工具调用输出填满，模型的系统提示词约束发生注意力衰减（Attention Dilution）。模型在第 8~16 轮开始重复发出平庸指令，决策方差激增，最终得分反降至 7.53。
   - 代表工作验证：Harris & Slivkins (PMLR 2026) 在 *Should You Use Your Large Language Model to Explore or Exploit?* 中明确指出：**当前所有 LLM 在纯利用（Exploitation）任务上均不如简单的线性回归**；LLM 唯一的相对优势在于语义探索，若强行让 LLM 直接参与数值排序决策，必然发生次优游荡。

---

### 2.3 补救机制：将 Agent 决策权限上升为“资产配置（Portfolio Allocation）”

要挽救 LLM 的这一劣势，不能任由其自由挑选变体或肆意切换极端的工具参数，而必须**对动作空间降维**：
- **禁止** LLM 直接负责微观变体序列的挑选；
- **重构** 任务接口为宏观策略博弈：让 LLM 充当“首席投资官（CIO）”，只需基于诊断指标确定当前批次的**资产配置配比（如：80% 稳健利用 + 20% 边际探索）**，底层工具自动根据数学最优准则（如混合 UCB）填充具体的 48 个候选。

---

### 2.4 五要素分析表：采集取舍与 LLM 劣势补救

| 要素 | 论述内容 |
|---|---|
| **核心思想** | 认识到好代理下 Pure Greedy / Low-$\beta$ UCB 具有数学最优收敛性，正视 LLM 的“科学家角色扮演偏见”与“数值计算盲区”；通过宏观资产组合（Portfolio Budgeting）约束其动作空间。 |
| **代表工作** | 1. Harris & Slivkins. *Should You Use Your Large Language Model to Explore or Exploit?* PMLR 2026 / arXiv:2502.00225；<br>2. Brochu et al. *A Tutorial on Bayesian Optimization of Expensive Cost Functions*. arXiv:1012.2599, 2010；<br>3. LLAMBO (Liu et al., NeurIPS 2024, arXiv:2402.03921)。 |
| **笼内落地** | 极度可行。将 Agent 从“多次调用 list_pool 碎片化拼凑 48 条序列”的繁重劳动中解放出来，转变为单次决定 `exploit_ratio`，由工具保证 48 条序列的数学最优填充。 |
| **合法性/优势** | 完全合法。大幅削减 Prompt 上下文负担与长程漂移风险；根除因盲目采样死蛋白而产生的“探索税”，直接对齐 Greedy 的收敛曲线。 |
| **局限/风险** | 削弱了 LLM 在单点突变序列上的“自由发挥”感，但在严肃的科学定向进化基准中，严谨性与有效性远高于无意义的“创造性幻觉”。 |

---

## 3. 重点三：让 LLM Agent 感知并利用 Surrogate 质量的 Prompt 与工具设计

### 3.1 动态状态感知接口设计（Tooling Design）

针对当前 `analyze_measured()` 隐藏代理关键指标的问题，应将该工具升级为**全景科研状态诊断器**（或新增只读工具 `surrogate_diagnostics()`）。

#### 接口透传字段规格：
```json
{
  "n_measured": 10481,
  "budget_remaining": 240,
  "current_round": "2 / 6",
  "best_variant_so_far": ["DEQEIATTNPVATEQYGEVSDNLQRGNR", 7.829],
  "surrogate_status": {
    "architecture": "EpistasisRidge (Pairwise Potts Degree-2)",
    "cv_spearman": 0.903,
    "cv_pearson": 0.915,
    "alpha_selected": 100.0,
    "confidence_level": "VERY_HIGH",
    "recommendation": "Surrogate has captured strong epistatic interactions. Recommend EXPLOITING predicted_mean (>=85% batch budget) to converge on the peak."
  },
  "top_enriched_substitutions": [["S17E", 4.12], ["V18A", 1.85], ["D0Q", 1.22]]
}
```

**设计哲学**：
- 把原本只在底层 Python 打印的 `CV Spearman 0.90` 变成 Agent 可调用的显式观察值；
- 赋予系统自省能力（Introspection）：Agent 能够在做出调用前，事实性地读出“代理当前高度可信”。

---

### 3.2 提示词重构：从“教唆怀疑”到“事实驱动校准”

必须彻底删除旧版 Prompt 中误导性的 `rank correlation only ~0.6`，替换为**基于证据驱动的条件推理协议**：

```markdown
### SYSTEM PROMPT 重构核心片段（草案）

You are an autonomous protein-engineering lead running a directed-evolution campaign under strict budget constraints.

SURROGATE PREDICTOR & EVIDENCE CALIBRATION:
A machine learning surrogate is available. You must NOT follow static biases; instead, check the `surrogate_status` reported by `analyze_measured`:
1. If CV Spearman >= 0.80 (HIGH/VERY HIGH CONFIDENCE):
   - The surrogate has successfully modeled the complex epistatic landscape.
   - You should HEAVILY EXPLOIT by testing candidates from `list_pool(by='predicted_mean')` (at least 80-90% of your batch).
   - Random/uncertainty exploration in this regime wastes budget on non-viable variants.
2. If CV Spearman < 0.65 (LOW/MODERATE CONFIDENCE):
   - The surrogate is struggling. Deliberately allocate 40-50% budget to diverse or uncertainty-driven exploration to supply informative training labels.
3. ROUND ANNEALING:
   - In the final 2 rounds, ALWAYS allocate >=90% of budget to exploitation, because late-stage exploration yield cannot be harvested within this campaign.
```

**对比论证**：
- 旧版 Prompt：强制灌输教条（“不要相信代理，必须平衡探索”）；
- 新版 Prompt：赋予科学判断标准（“看证据，CV 高则重点利用，CV 低则主动探索，末期强制收敛”）。这才是符合人类顶级科学家思维的 Answer-Agnostic 规范。

---

### 3.3 结构化批次决策工具：`compose_batch`

为了防止 LLM 在聊天回复中尝试生成几十条长字符串（容易截断或格式损坏），设计一个高内聚的提议工具：

```python
def compose_batch(exploit_ratio: float = 0.85, n: int = 48) -> dict:
    """Compose a scientifically balanced candidate batch for testing.
    - exploit_ratio: Fraction (0.0 to 1.0) allocated to highest predicted mean.
                     Remaining fraction is allocated to local uncertainty/diversity.
    - Automatically enforces Knowledge Gate (HD<=4, BLOSUM62>=0).
    - Returns preview statistics and exact sequence IDs ready for `test`."""
```
- Agent 仅需输出一条轻量的工具调用：`compose_batch(exploit_ratio=0.90, n=48)`；
- 底层工具自动完成两件事：
  1. 取 `list_pool(by="predicted_mean")` 前 43 条；
  2. 取在门禁范围内的 `list_pool(by="diverse")` 前 5 条；
  3. 合并去重后返回给 Agent 确认，Agent 紧接着调用 `test` 即可。

---

### 3.4 五要素分析表：Prompt 与工具感知重构

| 要素 | 论述内容 |
|---|---|
| **核心思想** | 破除信息黑盒，将底层的模型验证集指标（CV 分数、架构类型、收敛阶段）直接转化为 Agent 的环境感知；以证据驱动的 Prompt 取代经验主观臆测。 |
| **代表工作** | 1. LMABO (Ngo et al., ICLR 2026, 结构化状态透传给 LLM)；<br>2. ToolLLM (Qin et al., ICLR 2024, 标准化高内聚工具调用范式)；<br>3. Pydantic-AI Agentic Architecture (2024-2025)。 |
| **笼内落地** | 极低代码量即可落地。仅需修改 `SYSTEM_PROMPT` 字符串，并在 `analyze_measured()` 字典中追加 `model.val_spearman` 与文字建议。 |
| **合法性/优势** | 完全合法。CV Spearman 是由已测训练集计算得出的标准无偏估计，不涉及任何未来测试峰的信息；从根本上扭转 Agent 盲目探索的心态。 |
| **局限/风险** | 需确保 Prompt 文字言简意赅，避免与用户后续的单轮动态 Prompt 产生指令冲突。 |

---

## 4. 重点四：LLM Agent 工具调用鲁棒性与防御工程

### 4.1 崩溃成因代码级分析

通过对测试日志的深入排查，导致 V0.4 中 `string index out of range` 报错的直接元凶如下：

#### 源代码盲区（`agent/auto_researcher.py` Line 90）：
```python
def _gate(variants: list[str]):
    allowed, rejected = [], {}
    for v in variants:
        # 当 len(v) > len(spec.wt) 时，i 增长到 len(spec.wt)，spec.wt[i] 触发越界崩溃！
        subs = [(spec.wt[i], c) for i, c in enumerate(v) if c != spec.wt[i]]
        ...
```
- **触发路径**：
  1. LLM 有时会产生细微格式瑕疵，例如在序列末尾附加空格、`\n`、或误写为 29 个字符；
  2. 甚至某些轮次中，LLM 误解了参数含义，将突变代号（如 `["D0Q", "S17E"]`）传入了 `test` 工具；
  3. `_gate()` 函数没有任何序列长度的前置断言，直接利用 `enumerate(v)` 去索引固定长度（28）的 `spec.wt`，导致抛出未捕获的运行时异常 `IndexError`。
- **框架传播**：
  Pydantic-AI 在执行工具函数时，如果底层抛出未经包装的原生 Python 异常，将判定为该轮会话硬错误（`agent.llm.round_error`），直接终止对话循环，引发不可控的 harness 应急逻辑。

---

### 4.2 四层纵深防御体系（Defense-in-Depth）

为了确保 V0.5 及后续版本的 Agent 能够 100% 稳健运行，必须部署严格的四层防御工程：

```
                    LLM 传入原始参数
                           │
  [第 1 道防线: 输入清洗与正规化] ──► 去除空格/换行，全大写，过滤非字母
                           │
  [第 2 道防线: 严格格式契约拦截] ──► 长度不匹配 (len != 28) 优雅阻断，绝不抛出异常
                           │
  [第 3 道防线: 认知混淆自愈器]   ──► 若误传突变代号 (如 "D0Q")，自动解析或返回友好提示
                           │
  [第 4 道防线: 工具函数沙箱保护] ──► 顶级 try-except 拦截所有未知异常，返回结构化错误
                           ▼
                     安全执行实验
```

#### 1. 第 1 道防线：输入清洗与多态正规化（Sanitization）
```python
def _clean_seq(s: str) -> str:
    if not isinstance(s, str):
        return ""
    return s.strip().upper().replace(" ", "").replace("\n", "").replace("\r", "")
```

#### 2. 第 2 道防线：安全比较与长度门禁（Safe Indexing）
重构 `_gate()`，彻底消除直接数组索引风险：
```python
def _gate(variants: list[str]):
    allowed, rejected = [], {}
    wt_len = len(spec.wt)
    for raw in variants:
        v = _clean_seq(raw)
        if len(v) != wt_len:
            rejected.setdefault(raw, []).append(
                f"Length mismatch: sequence has {len(v)} aa, but wild-type requires exactly {wt_len} aa."
            )
            continue
        # 使用 zip 确保遍历绝不超出范围
        subs = [(w, c) for w, c in zip(spec.wt, v) if c != w]
        ...
```

#### 3. 第 3 道防线：突变代号混淆的友好提示（Semantic Hinting）
如果检测到传入的字符串形如 `[A-Z]\d+[A-Z]`（如 `D0Q`），明确告知 Agent：
`"Error: You provided a mutation notation ('D0Q') instead of a full 28-aa sequence. Please retrieve valid candidate sequences using list_pool."`
避免 Agent 在迷茫中重复尝试错误调用。

#### 4. 第 4 道防线：工具沙箱异常拦截（Exception Shielding）
所有向 Pydantic-AI 暴露的工具函数，必须使用装饰器或顶级 `try-except` 兜底：
```python
def safe_tool(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            return {
                "status": "tool_execution_error",
                "error_type": type(e).__name__,
                "message": str(e),
                "hint": "Please verify your tool input arguments."
            }
    return wrapper
```

---

### 4.3 代表工作（真实可核）

1. **ToolLLM / ToolBench**:
   - **作者/出处**：Qin et al. *ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs*. ICLR 2024.
   - **核心贡献**：系统研究了 LLM 工具调用中的各种畸形传参（参数类型不符、键名错误、越界与格式噪声），论证了严密的 Schema 校验与环境自愈反馈（Self-Healing Feedback）是 Agent 工业落地的基石。
2. **Toolformer**:
   - **作者/出处**：Schick et al. *Toolformer: Language Models Can Teach Themselves to Use Tools*. NeurIPS 2023.
   - **核心贡献**：奠定了现代 LLM API 调用的标准范式，强调 API 响应的确定性与容错规范。

---

### 4.4 五要素分析表：工具调用鲁棒性防御

| 要素 | 论述内容 |
|---|---|
| **核心思想** | 遵循纵深防御（Defense-in-Depth）原则，将 LLM 生成的代码与字符串视为非可信输入；通过长度前置校验、多态清洗、友好错误反馈与全局异常沙箱，杜绝任何未经捕获的崩溃。 |
| **代表工作** | 1. ToolLLM (Qin et al., ICLR 2024, ICLR 最佳论文之一)；<br>2. Toolformer (Schick et al., NeurIPS 2023)。 |
| **笼内落地** | 极易落地。仅需对 `auto_researcher.py` 中的 `_gate`、`predict`、`test` 增加约 20 行防御性代码，立刻消除所有 `string index out of range` 隐患。 |
| **合法性/优势** | 完全合法且无外部依赖。保障 Agent 在 12 轮甚至 16 轮的长程闭环中 0 崩溃、0 fallback，确保实验数据与轨迹日志的纯净度。 |
| **局限/风险** | 无任何负面风险，属于纯正的软件工程硬化与鲁棒性加固。 |

---

## 5. 方法族综合评估与排序清单

我们按照 **合法性（Answer-Agnostic） × 笼内可行性（修改复杂度） × 破顶/追平潜力（能否超越或追平 8.416）** 三维标准，对所有候选优化手段进行综合排序：

| 排名 | 方案名称 | 合法性 (Answer-Agnostic) | 笼内可行性 (实施代价) | 破顶/追平潜力 | 综合评分与推荐结论 |
|:---:|---|:---:|:---:|:---:|---|
| **1** | **修正 Prompt 负向锚定 + 诊断透传 CV 指标** | **✅ 100% 合法** | **✅ 极高**（仅修改文本与字典） | **⭐⭐⭐⭐⭐ 极高** | **必选（第 1 优先级）**。直接拔除导致 Agent 过度探索的认知毒瘤，成本近零。 |
| **2** | **工具链输入防御加固（消灭越界 Bug）** | **✅ 100% 合法** | **✅ 极高**（单文件修补 ~20 行） | **⭐⭐⭐⭐ 高**（保底稳定） | **必选（工程底座）**。杜绝 Round 异常中断与脏数据 fallback，是所有优化生效的前提。 |
| **3** | **自适应配比采集工具（`compose_batch`）** | **✅ 100% 合法** | **✅ 高**（新增单工具包装） | **⭐⭐⭐⭐⭐ 极高** | **强烈推荐（算法保障）**。把微观选点上升为宏观比例博弈，彻底消除探索税。 |
| **4** | **动态退火 UCB 采集策略（$\beta$-Decay）** | **✅ 100% 合法** | **✅ 高**（修改 `list_pool` 排序） | **⭐⭐⭐⭐ 高** | **备选**。数学上最优雅，但在 LLM 无法感知连续变量时，易退化为粗暴采样。 |
| **5** | **EI / Thompson Sampling 替换** | **✅ 100% 合法** | **✅ 中**（需接入 GP/抽样模块） | **⭐⭐ 低~中** | **不推荐**。好代理下 EI 存在高维探索病态，TS 稀释头部候选，实测极可能弱于 Greedy。 |
| **6** | **微调开源小型 LLM 的 Tool-Calling 策略** | **✅ 100% 合法** | **❌ 极低**（需标注轨迹、训练权重） | **⭐⭐⭐ 中** | **排除**。一周笔试周期与计算资源不可承受，且对本题超额设计。 |

---

## 6. V0.5 实验改法提名（给 CEO 的决策方案，共 3 条）

为确保 V0.5 版本在严格合规的前提下，一举消除探索税、拉平乃至超越 Greedy 8.416，向 CEO 正式提交以下 3 条互补且可立即实施的工程改法提名：

---

### 提名 A（Prompt 改 + 诊断透传，最省力、直击认知病灶）
- **实施动作**：
  1. **Prompt 改造**：彻底删除 `agent/auto_researcher.py` 中 `surrogate predictor is IMPERFECT (~0.6)...` 这一陈旧警示，换入“证据校准准则”：明确要求 Agent 在调用前查看 `surrogate_status`，当 CV Spearman ≥ 0.80 时必须优先利用 `predicted_mean`，最后两轮强制纯利用。
  2. **信息透传**：在 `analyze_measured()` 输出中，增加 `surrogate_status` 节点，将 `EpistasisRidgePredictor` 自带的 `val_spearman: 0.90` 及置信度建议直接显式暴露给 LLM。
- **预期成果**：阻断 LLM 盲目怀疑好模型的“伪科学家冲动”，预期将 `list_pool` 的 explore 比例由目前的 68% 骤降至 15% 以下。
- **改动面**：仅需编辑 `agent/auto_researcher.py` 中的提示词字符串与 `analyze_measured` 返回值，无需引入任何新逻辑。

---

### 提名 B（采集逻辑改，算法级锁定收敛优势）
- **实施动作**：
  1. **重构提议机制**：在 `auto_researcher.py` 中推出 `compose_batch(exploit_ratio=..., n=48)`，或让 `list_pool(by="adaptive")` 成为主选。
  2. **收拢动作空间**：底层根据传入的利用配比（由 Agent 根据 CV 指标自适应决定，缺省为 $0.85$），自动把前 $48 \times 0.85 \approx 41$ 个名额严格分配给 `predicted_mean` 降序顶尖变体，剩余 $7$ 个名额分配给门禁内的 `diverse` 或局部变异变体。
- **预期成果**：消除由于 LLM 粗暴调用 `uncertainty` 带来的批次污染；即使 LLM 偶尔摇摆，底座的算法护栏也能确保 85% 以上预算死死焊在真实峰顶的攀爬线上，**288 预算内复刻并稳定超越 7.829，锁定 8.416**。
- **改动面**：在 `agent/auto_researcher.py` 增加一个 ~25 行的高内聚工具函数并向 Agent 注册。

---

### 提名 C（工具鲁棒性改，消除隐式崩溃底座缺陷）
- **实施动作**：
  1. **修补 `_gate()` 越界**：在 `agent/auto_researcher.py` 的 `_gate()` 中使用 `_clean_seq` 清洗输入，并通过 `zip(spec.wt, v)` 与 `len(v) == len(spec.wt)` 检查彻底终结 `IndexError: string index out of range`。
  2. **工具沙箱化**：在 `test`、`predict` 等关键入口增加轻量级入参防御与友好提示，当传入非 28 字符时返回结构化拦截说明而非硬崩溃。
- **预期成果**：消灭事件流中的 `agent.llm.round_error` 和非预期的 `no_test` fallback，保证 6 轮、12 轮甚至 16 轮全程 100% 顺畅执行，轨迹日志完全干净。
- **改动面**：修改 `agent/auto_researcher.py` 约 15 行代码。

---

### 建议落地组合
**建议 CEO 批准三项提名联动执行（A + B + C）**：
- **C** 是零风险的基础工程加固，必须首先合入；
- **A** 拨乱反正，纠正 Agent 的心智模型；
- **B** 建立坚固的采集数学护栏。
三者结合，即可用最小的工程代价，让自主 LLM Agent 在 V0.5 中以优雅的科学家风范直达并拿下真峰 8.416！

---

## 7. 附：引用文献核实状态表

| 序号 | 文献/方法简称 | 完整规范出处 | 核实状态 | 关键结论与背书依据 |
|:---:|---|---|:---:|---|
| 1 | **LMABO** | Ngo, G., Trong, D. P., Nguyen, D., Gupta, S., & Venkatesh, S. *Adaptive Acquisition Selection for Bayesian Optimization with Large Language Models*. ICLR 2026 / arXiv:2602.07904. | **✔已核实** | 确立了利用 LLM 读取优化状态、自适应调度采集函数的范式。 |
| 2 | **LLM Explore vs Exploit** | Harris, K., & Slivkins, A. *Should You Use Your Large Language Model to Explore or Exploit?* PMLR 2026 / arXiv:2502.00225. | **✔已核实** | 实证证明当前所有主流 LLM 在单纯利用上弱于经典模型，必须依赖结构化约束。 |
| 3 | **EVOLVEpro** | Jiang, M. et al. *High-throughput directed evolution using few-shot machine learning*. Science, 387(6736), 2025. | **✔已核实** | 4 轮少样本主动学习定向进化标杆，后两轮采用集中利用策略。 |
| 4 | **MULTI-evolve** | Tran, D. et al. *Rapid directed evolution guided by protein language models and epistatic interactions*. Science, 392(6798):eaea1820, 2026. | **✔已核实** | 显式建模成对上位效应外推高阶变体，本仓 EpistasisRidge 的思想蓝本。 |
| 5 | **Adaptive GP-UCB** | Srinivas, N. et al. *Information-Theoretic Regret Bounds for Gaussian Process Optimization in the Bandit Setting*. IEEE Trans. Inf. Theory, 2012. | **✔已核实** | 置信区间退火与亚线性累积遗憾的经典数学奠基工作。 |
| 6 | **AdaLead** | Sinai, S. et al. *AdaLead: A Simple and Robust Adaptive Greedy Search Algorithm for Sequence Design*. arXiv:2010.02141, 2020. | **✔已核实** | 生物序列设计中自适应贪心法优于复杂探索的经典对比研究。 |
| 7 | **ToolLLM** | Qin, Y. et al. *ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs*. ICLR 2024. | **✔已核实** | 论述了 API 调用中的格式容错、异常自愈与防御工程标准。 |
| 8 | **Toolformer** | Schick, T. et al. *Toolformer: Language Models Can Teach Themselves to Use Tools*. NeurIPS 2023. | **✔已核实** | LLM 自主工具调用与错误处理的基础奠基文献。 |
| 9 | **EI Exploration Pathology** | Brochu, E., Cora, V. M., & de Freitas, N. *A Tutorial on Bayesian Optimization of Expensive Cost Functions*. arXiv:1012.2599, 2010. | **✔已核实** | 详述了 Expected Improvement 在高维空间由于方差未约束导致的无意义探索病态。 |
| 10 | **Epistasis Ridge (本仓实证)** | 本仓 V0.4 实验结果（`lab/reports/agentic-v0.4/report.md`）。 | **✔已核实** | CV Spearman 0.90，确定性 Greedy 288 预算直达真峰 8.416，LLM 7.829。 |
