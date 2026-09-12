# 中期报告 01：真·Agentic Agent 在 AAV 上诚实输给 greedy —— 以及为什么

**日期**：2026-09-11 · **状态**：迭代研究进行中，非最终结论 · **数据全部留存、可复现**

> 一句话：我们做出了一个**真正自主的** LLM 工具调用 agent（SOL 驱动），它在 AAV 定向进化任务上**输给了朴素 greedy**（5.96 vs 7.53）。这不是 bug，是一个有价值的科学发现——"探索模型不确定的地方"这条主动学习教科书启发式，在蛋白地形上会**主动筛选出非功能蛋白**。

---

## 1. 我们做了什么（真 agentic，不是伪装的工作流）

`agent/auto_researcher.py`：一个 **pydantic-ai** 工具调用 agent，大脑是 **`gpt-5.6-sol`**（用户指定，走自有池子 OpenAI 兼容端点）。给它 6 个工具和固定实验预算，让它**自己决定**分析什么、探索还是利用、何时花预算做真实测量、每轮如何根据结果调整：

| 工具 | 作用 |
|---|---|
| `analyze_measured` | 看已测集：最佳变体、各位点富集的有益突变 |
| `predict` | 代理模型对池中变体的 [均值, 不确定性]（不完美，Spearman≈0.6） |
| `list_pool` | 从未测池取候选，可选 `predicted_mean`(利用)/`uncertainty`(探索)/`diverse`/`random` |
| `check_knowledge` | 知识库（突变规则 + BLOSUM62）评估 |
| `test` | **花预算**做真实测量（oracle = 已测表查询）——这是唯一的"真实验" |
| `best_so_far` | 当前最佳 |

**这是真自主性的铁证**——SOL 的完整工具调用轨迹（25 次调用，来自 `reports/pool_events_aav_agentic.jsonl`，事件链 SHA-256 校验通过）：

```
轮1: analyze → list_pool[uncertainty,diverse,predicted_mean,random,predicted_mean,uncertainty]
     → test(80个,batch_max1.87) → test(16个,batch_max4.51)
轮2: analyze → list_pool[uncertainty,predicted_mean,diverse] → test(75个,4.82)
     → list_pool[predicted_mean,random] → test(21个,5.79)
轮3: analyze → list_pool[predicted_mean,uncertainty,diverse] → test(95个,5.96)
     → list_pool[predicted_mean,n=1] → test(1个) 补满288
```

SOL 每轮自主混用多种排序轴探池、自定批大小、轮间重新分析——**不是写死的流程**。它花满了全部 288 预算。

---

## 2. 结果：五策略同预算(288)、同池、同 oracle

| 策略 | cum_top10_max | cum_mean | strong 命中 |
|---|---|---|---|
| random | 5.91 | 4.96 | 35 |
| **agentic SOL** | **5.96** | **4.73** | **15** |
| greedy | **7.53** | 6.09 | 85 |
| agent_no_knowledge | 7.53 | 6.09 | 85 |
| knowledge_agent | 7.53 | 6.09 | 86 |
| *（池子真实峰）* | *8.42* | — | — |

**agentic SOL 只和 random 持平，strong 命中(15)甚至比 random(35)还少。** 结构化的 knowledge workflow(7.53) 完胜自由 agent(5.96)。

---

## 3. 为什么输？机制分析（策略无关、可复现）

脚本 `analysis/agentic_postmortem.py`，数据 `reports/agentic_postmortem_aav.json`。用 cold-start(HD≤2) 拟合 Ridge(5 seed bootstrap)，对池(HD>2)预测均值+方差，再对照真实 fitness：

**① 预测器的"不确定性"= 高阶突变 = 死蛋白**

- Spearman(方差, HD) = **+0.47** —— 方差高的就是突变多的
- Spearman(方差, 真实fitness) = **−0.31** —— 方差高的就是 fitness 低的
- 按预测方差四分位（explorer 爬的就是这个轴）：

| 方差四分位 | 均 HD | 均 fitness | 强变体占比 |
|---|---|---|---|
| Q1(最低方差) | 4.33 | +0.22 | 13.3% |
| Q2 | 4.82 | −0.13 | 11.5% |
| Q3 | 5.60 | −0.57 | 9.1% |
| Q4(最高方差) | **8.61** | **−2.14** | **4.4%** |

**② 两极策略各挑 288 个的真实画像（最锋利的一刀）**

| 策略 | 均 HD | 均 fitness | 最高 fitness | 强命中/288 |
|---|---|---|---|---|
| greedy(按预测均值) | 6.08 | +0.90 | 7.53 | 41 |
| explorer(按预测方差) | **16.98** | **−4.60** | 0.82 | **0** |

纯"探索高不确定性"挑出的是**平均 17 个突变的死蛋白，0 个强命中**。SOL 在这两极之间平衡，被探索从 greedy 的水平拖到了 5.96。

**③ 真峰在双盲区，谁都够不着**

真峰 fitness=8.42、**HD 仅 3**（低阶变体）：

- 预测均值排名 **#5763 / 27832** → **exploit 够不着**（被系统性低估）
- 预测方差排名 **#17586 / 27832** → **explore 也够不着**（方差太低，探索会绕过它）

**所以 AAV 上"greedy 可证明达不到峰"和"agent 能赢"是两回事**：8.42 对**所有** mean/方差 引导的策略都不可见。这个地形能证明贪心失败，但不给 agent 赢的空间。

---

## 4. 这意味着什么（贡献重新定位）

我们的价值不是"造了个很强的 agent"，而是**建了一个诚实的试验台，能量化揭示 agentic 探索在蛋白地形上何时、为何失效**：

1. **主动学习的 uncertainty 启发式在蛋白地形上有毒**：因为 epistemic 方差 tracks 突变阶数，而高阶突变多为非功能。这在 ML 圈是反直觉的、值得写的结论。
2. **结构化知识 > 原始自主**：knowledge_agent 的 BLOSUM 保守性先验正是压制"探索选中死蛋白"而设计的，所以它 ≥ greedy ≥ 自由 agent。
3. **不作弊的证据**：greedy 可证明够不着真峰（真峰对预测器不可见），agent 也真输了——全是硬碰硬。

---

## 5. 待研究 / 下一轮迭代（与用户一起定）

- [ ] **中性 prompt 对照**：不鼓励探索、让 SOL 完全自由（甚至可纯 exploit）。看 agent 能否自主选择贪心而追平 7.53 → 区分"探索代价"vs"agent 无能"。
- [ ] **给 agent 一个能赢的地形**：找/造一个 greedy 卡局部最优、高区域可达但被预测器低估的实验（avGFP 阈值上位？人为 deceptive 池？）。
- [ ] **AAV-ESM 版**：ESM-2 650M 嵌入缓存已建好(173MB/38265 条)；ESM 泛化更好(HD-extrap Spearman 0.49 vs one-hot 0.36)，预测器更强时 agent 表现是否不同？
- [ ] **sample-efficiency 口径**：换"达到某 fitness 所需实验数"曲线，agent 的探索也许在低预算早期更快。
- [ ] **avGFP 数据接入**（用户确认要做）。

---

*来源(本报告文件夹自包含)*：`aav/agentic.metrics.json`、`aav/agentic.events.jsonl`(链校验通过)、`aav/postmortem_one_hot.json`、`aav/postmortem_esm.json`、`../workflow-v1.0/aav/pool_one_hot.metrics.json`(四策略基线对照)、`../experiment_log.jsonl`(版本脊柱)。全部可复现。
