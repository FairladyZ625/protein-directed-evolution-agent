# workflow-v1.2:逐变体预测残差入事件流 + llm 档复现检验

## 这一版为什么存在

两件事,一件是新能力,一件是把上一版的一个结论推翻了。

**新能力**:事件流开始记录**逐变体的预测残差**(`campaign.oracle.residuals`)。
在此之前,逐变体真值只存在于 `campaign.round.completed` 的 `top10` 字段,
而失败的提名——尤其「预测很高、实测致死」那种——按定义进不了 top-10,
**失败案例结构性地一条都没被记录过**。试题「结果展示 d-iv:哪些推荐失败,
原因可能是什么」此前答不上来,根因不是没写,是没数据。

**推翻的结论**:v1.1 报告 §④ 写「接入真 LLM 之后,两个 agent 策略都变差了」。
按 CEO 裁定「真实性最重要」对 llm 档做了一次独立复现,发现那个比较**根本不是同预算比较**。
详见下面第 ③ 条。

## 与 v1.1 的关系

三个确定性档(easy / hard / sparse)是**逐位复现**,不是新实验:

| regime | random(5 seed 均值 ± σ) | greedy | agent 无知识 | 知识增强 | 与 v1.1 |
|---|---:|---:|---:|---:|---|
| easy | 3.674 ± 0.820 | 81 / 239 | 95 / 244 | 86 / 250 | **逐位相同** |
| hard | 4.611 ± 1.850 | 43 / 178 | 50 / 182 | 65 / 204 | **逐位相同** |
| sparse | 4.046 ± 0.720 | 29 / 180 | 27 / 213 | 33 / 202 | **逐位相同** |

(格式为 `strong / 有益命中`;三档的 `cum_top10_max` 与 v1.1 亦相同,sparse 下只有
知识增强达到 8.761966,其余两条停在 5.772032。)

**这个「逐位相同」本身就是结论**:它证明加入残差记录对实验结果完全惰性。
每档墙钟从 v1.1 的 4.3 分钟降到约 7 秒——那是同期修掉的 `load_rules` 重复解析
(每次调用重新 yaml.safe_load 一遍 `knowledge/rules.yaml`,14.32 ms × 6,539 候选 ≈ 94 秒/轮)。

## ① 残差数据长什么样(hard 档,knowledge_agent)

| 类型 | 变体 | 预测 | 实测 |
|---|---|---:|---:|
| 高估(致死) | `FYFC` `FYYC` `IYYC` `IYQC` `IYLC` | 2.93–3.07 | **0.01–0.15** |
| 低估(真峰) | `FYAA` `FWAA` `FWCA` | 1.40–3.06 | **8.05–8.76** |

第 4 位是 `A` 还是 `C` 决定生死,而模型给两边的分几乎一样:
**给全局最优 `FWAA` 打 3.061,给致死变体 `FYFC` 打 3.069——给峰的分比给死的还低。**
这不是「模型不够准」,是它在这个 motif 上系统性地分不清方向。

## ② 残差取的是「提名时刻」的预测,不是重训后的

`_run_strategy` 在 oracle 回填后会用 `train + batch` 重新 fit 预测器。
拿重训后的模型算残差,是在跟一个**已经看过这批标签**的预测器比——那不是「看走眼」,
是穿越,而且穿越出来的残差会小得多。所以 emit 发生在重训之前,
`_greedy_propose` / `_agent_propose` 改为连同提名时刻的预测一起返回。

`random` 策略记 `None` 而非 `0.0`:它根本不查模型,填 0.0 会被读成
「模型预测它是死的而且猜对了」,是凭空捏造一条模型行为。

守护测试:`tests/test_campaign.py::test_residuals_record_the_nomination_time_prediction_not_the_refit_one`
(独立复现第 1 轮 greedy 的提名时刻预测逐位比对,自带阴性对照证明重训后的预测确实是另一组数)。

## ③ llm 档:v1.1 §④ 的结论不成立

**llm 档与 hard 档不是同预算比较。** 名义预算 96 提名/轮 × 3 轮 = 288:

| 策略 | hard 档 | llm 档(v1.1) | llm 档(v1.2) |
|---|---:|---:|---:|
| greedy | 288 | 288 | 288 |
| agent_no_knowledge | 288 | **105** | **5** |
| knowledge_agent | 288 | **197** | **5** |

逐轮拆开,机制没有例外(v1.1):

| 策略 | r1 | r2 | r3 |
|---|---|---|---|
| agent_no_knowledge | **5**(llm) | **96**(fallback) | **4**(llm) |
| knowledge_agent | **5**(llm) | **96**(fallback) | **96**(fallback) |

**凡 LLM 真正跑通的轮次,提名从 96 塌到 ~5;凡回退到确定性的轮次,提名满额 96。**
v1.2 复现时两条策略唯一的 LLM 轮都只提名 5 个,第 2 轮已无候选可提,
campaign 在 `if len(picks) == 0: break` 处**静默终止,退出码 0**。

按每次提名归一化(v1.1 hard vs v1.1 llm):

| 策略 | hard:strong/提名 | llm:strong/提名 | hard:有益率 | llm:有益率 |
|---|---:|---:|---:|---:|
| agent_no_knowledge | 0.174 | **0.305** | 0.632 | **0.838** |
| knowledge_agent | 0.226 | **0.299** | 0.708 | 0.711 |

**质量指标是升的。** §④ 的「−36% / −52%」是预算差,不是质量差;
§④ 里「knowledge_agent 优于 agent_no_knowledge」也只是它多拿了一个满额回退轮次。

机制在 `evolution/campaign.py::_llm_hypothesis`:LLM 只是从确定性菜单里**挑子集**,
挑得少组合库就塌,而**没有任何下限**。确定性档给每位点 top-8 共 32 个替换、库 6,539;
LLM 每次只给寥寥几个,库塌到个位数。

**刻意不补这个下限**——补了就把刚发现的效应掩盖掉。改为让它可见:
`summary` 现在每个臂都带 `budget_planned` / `budget_spent` / `budget_complete` 与
`strong_per_nomination`,CLI 对未花满的臂逐行标注并在表尾打整体告警。

## 产物

| 文件 | 内容 |
|---|---|
| `harness/reports/workflow-v1.2/gb1/campaign_{easy,hard,sparse,llm}.metrics.json` | 四 regime 四策略逐轮指标,含预算完成度与归一化指标 |
| `harness/reports/workflow-v1.2/gb1/campaign_{easy,hard,sparse}.events.jsonl.gz` | 链式 SHA-256 事件流(gzip 归档),各 190 事件、24 条 `campaign.oracle.residuals` |
| `harness/reports/workflow-v1.2/gb1/campaign_llm.events.jsonl` | llm 档事件流(156 事件,该档提前终止) |
| `harness/reports/workflow-v1.2/gb1/figures/campaign_*.png` | 四条累计曲线 |

## 复现

```bash
./scripts/install.sh
# 需要 data/four_mutations_full_data.csv,见 data/README.md

python -m evolution.campaign \
  --out-json harness/reports/workflow-v1.2/gb1/campaign_easy.metrics.json \
  --out-fig  harness/reports/workflow-v1.2/gb1/figures/campaign_easy.png \
  --out-events harness/reports/workflow-v1.2/gb1/campaign_easy.events.jsonl

python -m evolution.campaign --cold-start low_hd --max-cold-hd 2 ...   # hard
python -m evolution.campaign --cold-start low_hd --max-cold-hd 1 ...   # sparse
LLM_TIMEOUT=90 python -m evolution.campaign --cold-start low_hd --max-cold-hd 2 --use-llm ...  # llm
```

确定性三档可逐位复现;**llm 档不可复现**——它依赖商业 LLM 的当次输出,
v1.1 与 v1.2 两次运行的提名数分别是 105/197 与 5/5。

## 已知限制

1. **llm 档两次运行都未花满预算**,其计数型指标(strong / 有益命中)与确定性档不可比。
   引用该档任何数字时必须同时给出实际提名数。
2. **确定性三档仍是单 seed(42)**,只有随机基线做了 5 seed。策略之间的差值没有误差棒。
3. **10,639 个组合在真值表里没有数据**,既不进候选也不计入分母;
   全局最优是「实测 149,361 个里的最优」,不是理论最优。
4. **残差只对查了模型的策略有意义**;`random` 策略的残差字段是 `None`,不是 0。
5. v1.1 与 v1.2 的 llm 档是**同条件**(`LLM_TIMEOUT=90`)的两次独立运行,
   可并列作为「不稳定性」的证据,**但不得取平均当作一个效应量**。
