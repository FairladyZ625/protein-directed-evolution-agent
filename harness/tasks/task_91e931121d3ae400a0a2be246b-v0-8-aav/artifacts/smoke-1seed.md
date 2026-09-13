# v0.8 第一轮冒烟(AAV,seed 42,单 seed)

> **给写报告的人:先读本文件最后一节「引用时必须带的话」。这一轮是 n=1,
> 而且构型本身限制了结论的适用范围——直接引数字会说过头。**

## 跑了什么

单因子对照,除「LLM 看不看得到残差」外一切相同。

| 项 | 值 |
|---|---|
| 数据集 | AAV(28 残基变异窗口) |
| 协议 | budget 48 × 6 轮 = 288,seed 42 |
| 特征 / 代理模型 | one_hot / epistasis(成对交互) |
| 采集 | `--backtrack semi`(v0.6 纯预测均值利用) |
| 知识门禁 | `--guardrail` 开 |
| LLM | `gpt-5.6-sol`,`LLM_TIMEOUT=240` |
| 复现命令 | `scripts/run_v08_arms.sh` |

**两臂都记录残差事件,只有 reflexion 臂把残差注入下一轮 prompt。**
所以唯一的变量是「LLM 看不看得到」,不是「有没有算残差」。

## 结果

| | control | reflexion |
|---|---|---|
| 工具调用 | 38 | 44 |
| `redirect_batch` 触发轮次 | `[5]` | **`[2, 5]`** |
| 停滞旗标轮次 | `[5, 6]` | `[5, 6]` |
| cum_top10_max | 8.4162 | 8.4162 |
| strong | 157 | 157 |
| 墙钟 | 221 s | 268 s |
| LLM 成功率 | **6/6** | **6/6** |
| 超时次数 | 0 | 0 |

### 核心观察:注入改变了 LLM 的动作,却没改变任何一个提名

逐轮比对两臂**实际被 oracle 测过**的批次(按序列集合取 SHA-256):

| 轮次 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| 批次是否相同 | 同 | 同 | 同 | 同 | 同 | 同 |
| 重叠 | 48/48 | 48/48 | 48/48 | 48/48 | 48/48 | 48/48 |

288 个变体,一个不差。`motif_recurrence` 因此两臂逐位相同(不是指标失灵,是行为真的没分叉)。

**但注入确实起作用了**:reflexion 臂在**第 2 轮**就触发了 basin hop,control 到**第 5 轮**才触发。
这正是 RFC-008 §4 预测的「停滞时盆地跳跃提前 1~2 轮」。

**那次提前的 hop 是空转的**:第 2 轮尚未形成可供「跳离」的最优簇,
`redirect_batch` 退化成与纯利用相同的挑法,所以动作变了、批次没变。

### 为什么行为空间这么窄

两臂**每一轮**的采集参数都是:

```
src=v06_pure_exploit_default   requested_exploit_ratio=1.0 -> effective=1.0
```

LLM 从头到尾**没有对采集比例行使过任何裁量**——v0.6 的纯利用默认把它的选择权吃光了。
它唯一的杠杆是 `redirect_batch`,而那个杠杆在早期是空的。

**所以本轮测到的不是「反思没用」,而是「在这个构型下反思无处着力」。**

### 一条适合写进报告的观察

reflexion 臂的 LLM 在收尾总结里写:

> "Residual reflexion excluded the two strongly lethal round-5 contexts and
> prioritized measured-supported motifs without assuming additive effects."

而它实际测的 288 个变体与对照臂**逐字节相同**。
**模型声称自己据此做了取舍,可它做的事一件没变。**
这条直接对应试题「讨论 LLM Agent 是否真正学到了『科学家思维』,还是只是调用预测模型」。

## 注入内容长什么样(第 2 轮实际发给 LLM 的原文)

```
MANDATORY RESIDUAL REFLEXION (observed round 1):
Residual definition: measured_fitness - nomination-time predicted_mean.
Lethal threshold fixed before the run: measured_fitness < 0.2.
Overestimated lethal variants (largest absolute residual first):
- DEEEISQTNPVATEQYGSVSTDLQRGNQ: predicted=8.331898, variance=3.283166,
  measured=-0.223544, residual=-8.555442
- KEQEIRTTNPVATEQYGSVSTDLQRGNM: predicted=7.756840, variance=5.156062,
  measured=-0.149848, residual=-7.906688
Underestimated variants: none observed in the recorded batch.
Observed substitution motifs: N21D (over=2, under=0), D0K (over=1, under=0), ...
ACTION CONSTRAINT: before selecting this round, explicitly account for the lethal
motifs above and avoid carrying them forward unless current measured evidence justifies it.
```

注意它诚实地写了 `Underestimated variants: none observed`——没有为了凑格式编内容。

## 工程侧的两个副产品

1. **LLM 端口成功率从 54% 升到 100%**。此前 GB1 `llm` 档实测 Critic 54% / Hypothesis 50%,
   主因是 90 秒超时零重试(fact `F-ABD9B83F`)。本轮 `LLM_TIMEOUT=240`,
   两臂各 6/6 成功、0 次超时。**报告里凡引用「LLM 成功率」必须写清对应的超时设置**,
   90 秒和 240 秒是两个不同的实验条件。
2. **残差记录本身是新增能力**。此前事件流里逐变体真值只存在于 `campaign.round.completed`
   的 top10 字段,而失败的提名(尤其预测高、实测致死的)按定义进不了 top-10,
   **失败案例结构性地一条都没被记下来**。现在两条线都记了。

## 引用时必须带的话

1. **这是 n=1。** 单 seed,而且底下是一个有随机性的 LLM。
   本仓已有前车之鉴:随机基线的单 seed 值看起来有趋势,5 seed 一算三者在 ±1σ 内完全重叠
   (fact `F-6394AB50`)。**不得据此说「反思有效/无效」。**
2. **「批次逐位相同」这个事实是硬的,可独立复核**(事件流里 `agent.tool.test.residuals`
   的 `records[].seq` 取集合哈希);但**它的成因与构型强绑定**——
   v0.6 纯利用默认 + 策略下限让 LLM 无裁量空间。换构型结论可能不同,后续 2×2 会测。
3. **不要把「redirect 提前 3 轮」写成正面结果。** 动作提前了,但那次 hop 是空转的,
   净效果为零。诚实的说法是「注入改变了 agent 的动作选择,但在本构型下该动作无效”。
4. **两臂 strong 都是 157、峰都是 8.4162**;而 cold-start 已含 incumbent **9.536457**,
   高于池内峰。所以「达峰」不等于「超越已知最优」——这条边界(「9.536 悖论」)
   在既有报告里已经自曝过,本轮不改变它。

## 下一步(在跑)

2×2 因子实验:采集构型 {v0.6 纯利用, v0.5 质量感知混合} × 反思 {关, 开}。
加 v0.5 那一档是因为本轮证明了:**LLM 的选择权被纯利用默认吃光时,反思无处着力**;
只有在它的 `exploit_ratio` 真能影响批次的构型下,才谈得上检验反思有没有用。
批次若开始分叉,再上多 seed。
