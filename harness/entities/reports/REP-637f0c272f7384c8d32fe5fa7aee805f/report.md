# workflow-v1.0：固定工作流 + 四策略主动学习基线

**方法线**：workflow · **版本**：v1.0 · **定位**：baseline archetype（后续 agentic 线的对照基准）

> 一句话：固定五角色工作流下的四策略池式主动学习（random / greedy / agent_no_knowledge / knowledge_agent），在 GB1 与 AAV 两个地形上建立诚实基线。GB1 可达全局峰、AAV 不可达——为"greedy 何时够得着、何时够不着"提供对照。

## 1. 边界与口径
- **地形**：GB1（4 位点组合库，全局峰 8.762）、AAV（FLIP 28-aa 窗口，池真实峰 8.42）。
- **口径**：候选池 = 撤出冷启动后的已测变体；四策略共享同池、同预算、同 oracle（已测表查询），**只在候选排序上不同**。
- **冷启动**：GB1 三档（easy 随机池 / hard HD≤2 外推 / sparse 仅 77 单突变）+ LLM 注入档；AAV：HD≤2 → HD>2。

## 2. 预测器阶梯（Spearman，`gb1/predictor_ladder.json`）
| 特征 × 划分 | ridge | xgboost | mlp |
|---|---|---|---|
| one-hot · 随机划分 | 0.484 | 0.474 | 0.389 |
| esm2 · 随机划分 | 0.493 | 0.377 | 0.491 |
| one-hot · HD 外推 | 0.358 | 0.354 | 0.278 |
| **esm2 · HD 外推** | 0.404 | 0.352 | **0.493** |

要点：随机划分下 one-hot/esm2 相当；**HD 外推（真实困难场景）下 ESM-2 泛化更好**（mlp 0.493）。

## 3. 四策略跑分矩阵
**GB1 · hard（HD≤2 外推，`gb1/campaign_hard.metrics.json`）**
| 策略 | cum_top10_max | strong 命中 |
|---|---|---|
| random | 5.08 | 1 |
| greedy | **8.762** | 43 |
| agent_no_knowledge | 8.762 | 56 |
| knowledge_agent | 8.762 | 57 |

→ GB1 上 greedy **够得着全局峰 8.762**；知识增强主要体现在 strong 命中数（43→57）。

**AAV（`aav/pool_one_hot.metrics.json`）**
| 策略 | cum_top10_max | strong 命中 |
|---|---|---|
| random | 5.91 | 35 |
| greedy | 7.53 | 85 |
| agent_no_knowledge | 7.53 | 85 |
| knowledge_agent | 7.53 | 86 |

→ AAV 上四策略**都卡在 7.53**，池真实峰 8.42 被预测器排到 #5763，**greedy 可证明够不着**。

## 4. 承前启后
- GB1 太"善良"（greedy 达峰），AAV 才把"greedy 够不着峰"逼出来——这是选 AAV 作 agentic 主战场的理由。
- 四策略里 agent/knowledge 相对 greedy 增益有限（同 7.53/8.762），说明**固定工作流的排序增强在这两个地形上天花板不高**——引出下一代 `agentic` 线：让 LLM 自主决策，看自主性是否带来不同。

*事件流*：各 `*.events.jsonl` 均为 append-only SHA-256 链，可 `python -m events.replay` 回放。*脊柱*：`../experiment_log.jsonl`。
