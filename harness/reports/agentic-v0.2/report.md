# 中期报告 02：Knowledge 门禁流让 agentic 追平 greedy —— 探索惩罚被消除，但天花板未破

> 一句话：给自主 agent 的 `test` 前加一道**不可绕过的知识门**（HD≤4 + 平均 BLOSUM62≥0），并让门**塑造搜索空间**（`list_pool` 只出门内候选），v0.1 那个致命的探索惩罚被彻底消除——cum_top10_max 从 **5.96 → 7.53**、strong 命中 **15 → 93**，**追平 greedy**。但门禁没能让 agent **突破** 7.53：真峰 8.42 即使在门内也被代理模型排到 #5763，自主性弥补不了表征的短板。这为实验二（ESM 表征）提供了直接动机。

本报告承接 [agentic v0.1](../agentic-v0.1/report.md)（自由 agent 诚实输给 greedy）与 [workflow v1.0](../workflow-v1.0/report.md)（四策略基线）。同池、同预算、同 oracle、同 seed，唯一变量是"test 前的门"。

---

## 1. 我们做了什么：双层 Knowledge 门禁流

v0.1 证明了"自由探索高不确定性"在蛋白地形上有毒（高方差 = 高阶突变 = 死蛋白）。v0.2 把 workflow 线里那个"软 BLOSUM 先验"升级为 agent test 前的**硬门**，而且是**双层**的：

| 层 | 位置 | 作用 |
|---|---|---|
| **入口塑形** | `list_pool`（agent 找候选的检索工具） | guardrail 开时**只返回门内候选**（HD≤4 且平均 BLOSUM62≥0），把知识变成"搜索空间的形状"，agent 自然在有效区里选 |
| **出口硬门** | `test`（花预算的唯一真实验） | 任何到达 test 的候选仍逐个过门；不合格者**不扣预算**、返结构化错误让 agent 重提。防 agent 手搓门外序列，不可绕过 |

- 门定义：突变数 HD≤4 **且** 平均 BLOSUM62 替换分≥0（净保守）。
- 门内通过率：AAV 未测池 27832 个 → **9533 个通过（34.3%）**；**真峰 8.42（HD3、平均BLOSUM 0.0）在门内**，门内峰 top5 = [8.42, 7.83, 7.75, 7.53, 7.39]。门给了真实 headroom，不是过严误杀。
- agent 仍完全自主：测哪些、测多少、探索/利用配比都它自己定；门只约束"能看到什么"和"什么能被测"。**不替 agent 改 test 选择。**

---

## 2. 结果：三方同预算(288)、同池、同 oracle、seed 42

| 方法 | cum_top10_max | cum_mean | strong 命中 | budget | 备注 |
|---|---|---|---|---|---|
| agentic **v0.1**（无门禁，自由 LLM） | 5.96 | 4.73 | 15 | 288 | 自主探索有毒，输给 greedy |
| workflow greedy / agent / knowledge | 7.53 | 6.09 | 85–86 | 288 | 固定流四策略天花板 |
| **agentic v0.2（门禁，LLM SOL）** | **7.53** | 5.98 | **93** | 284 | **追平 greedy，strong 略高** |
| agentic v0.2（门禁，确定性对照） | 7.53 | 6.16 | **116** | 288 | 门内纯贪心：strong 密度最高 |
| *（池子真实峰 = 任何方法的天花板）* | *8.42* | — | — | — | 被代理模型排到 **#5763** |

v0.2 LLM 曲线：**[5.69 → 7.53 → 7.53 → 7.53 → 7.53 → 7.53]**——round 2 即够到 7.53 后进入平台。最佳变体 `DEEEIRTTNPVATEQYGEVSENLQHGNR`，fitness 7.53，**HD 3**（对比 v0.1 explorer 的均 HD 16.98）。

**三个诚实结论：**

1. **门禁消除了探索惩罚（决定性胜利）**：v0.2 相对 v0.1，cum_top10_max **+1.57**（5.96→7.53），strong 命中 **×6**（15→93）。v0.1 那个"自由 agent 把预算烧在均 HD 17 的死蛋白上"的病，被门禁根治——测的全是 HD 3–4 的保守变体。
2. **追平 greedy，但没突破 7.53**：自主性 + 知识让 agent **达到**固定工作流的同一天花板，却翻不出那 3–4 根 >7.53 的针。这是意料之中的诚实结果——one_hot 表征下代理模型把真峰 8.42 排到 #5763，**贪心排序够不着、自主探索也够不着**。自主性弥补不了表征短板。
3. **门是活的、不可绕过**：LLM 手搓了 1 个门外候选，被出口硬门抓住（n_gate_rejected=1）；284/288 预算全花在门内有效区；事件链 `store.verify()` 通过（43 事件）。

---

## 3. 机制：门为什么"治得了病、破不了顶"

- **治病**：v0.1 的病根是 `list_pool by uncertainty/diverse` 把高阶变体送到 agent 面前，agent 一探索就中毒。入口塑形后，agent 看到的候选全是门内保守变体，方差与死蛋白率被压到最低——这正是 workflow 线 knowledge_agent 达到 7.53 的同一机制，只是现在由自主 agent 在门内自行调度。
- **破不了顶**：7.53 是**代理模型在门内能排到 top 的最高真值**。真峰 8.42 虽在门内，但 one_hot + Ridge 代理对它的预测排名 #5763——288 预算无论怎么在门内挑，只要靠代理排序就够不到。门缩小了搜索空间（27832→9533）、提高了命中密度（strong 116 vs 85），但**没有改变代理模型的排序能力**，而排序能力才是 7.53 天花板的成因。

**推论（直接引出实验二）**：要破 7.53，杠杆不在"更聪明的 agent 决策"，而在"更好的表征让代理把 8.42 排上来"。→ **实验二：ESM-2 表征**，看 richer embedding 能否把真峰的预测排名从 #5763 拉进 top，从而给门禁流真正的破顶空间。

---

## 4. 过程诚实：我们跑砸过一次，并修好了

首轮 LLM v0.2 只花了 **6/288** 预算就退化了。诊断：门禁最初只做了"出口拒收墙"，但 agent 找候选的 `list_pool` 仍对全池排序、top 全是高阶变体 → 被拒 → agent 反复撞墙、放弃测量 → 预算花不出去。**这不是门太严，是知识只筑了墙、没塑造搜索空间**。修复（commit d1140a2）：guardrail 开时 `list_pool` 只出门内候选 → 预算恢复花满 284/288。补了 starvation 回归单测。此坑与修复保留在此，作为"reject-only 门禁不足以引导自主 agent"的教训。

---

## 5. 复现

```
PYTHONPATH=. .venv/bin/python -m agent.auto_researcher \
  --dataset aav --feature one_hot --guardrail \
  --budget 48 --n-rounds 6 --seed 42 --model gpt-5.6-sol
```

- 代码：`agent/auto_researcher.py`（git d1140a2 及之后）；门禁单测 `tests/test_auto_researcher_gate.py`（4 passed）。
- 产物：`harness/reports/agentic-v0.2/aav/`（agentic.metrics.json + agentic.events.jsonl 链校验 + figures/agentic.png）；ledger `harness/reports/experiment_log.jsonl` 末条（git_commit + artifacts SHA256）。
- 注：ledger 首条 v0.2 记录的 `command` 字段（d1140a2 之前的 log_run 模板）漏了 `--guardrail`，以本节命令为准；d1140a2 起 log_run 已记全门禁参数。

---

## 6. 结论与下一步

门禁流把 agentic 从"输给 greedy"救到"追平 greedy"，探索惩罚被诚实、彻底地消除——这是 v0.1→v0.2 的核心进展。但 7.53 的天花板是**表征问题**，不是决策问题：自主性已用尽 one_hot 代理的排序能力。**下一代的杠杆是表征（实验二 ESM-2），不是更复杂的 agent 策略**——这是本轮最有价值的、可指导后续投入的诚实判断。
