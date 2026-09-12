# 中期报告 06(实验五):元层自主 backtrack 修好了停滞检测,但 redirect 无处可跳——8.416 参照线本身含 UCB 探索

> 一句话:在与 v0.4/v0.5 完全相同的 AAV pool/cold-start/oracle/门禁/预算/seed/上位 surrogate 下,v0.6 给 agent 加了元层自主(停滞检测 + `redirect_batch` 换区),full(LLM 自判停滞)与 semi(硬规则判停滞)两变体同 seed 运行。纯利用默认把 v0.5 的 6.5309 修复回 **7.829**(strong 命中 **166**,全版本最高),两变体都在第 5 轮正确触发 backtrack(full 是 LLM 自主判定,semi 是硬规则,同一轮),但 redirect 因最优簇签名为空而退化为同一批 greedy top-48,**终态 7.829 = 纯利用天花板**。campaign 后只读反事实进一步钉死机制:**v0.4 的"确定性 greedy 8.416"实为 PM/diverse(UCB)交替驱动,真峰出自 r4 的 diverse 批(r3 状态真峰 UCB 排名 #15、mean 排名 #2930)**——纯 predicted-mean 贪心在本地形/seed 上 288 预算的上限就是 7.829。LLM 元层自主没有输在"何时检测",输在"逃逸动作里没有方差信号";这是对任务前提的一个 evidence-backed 修正,如实记录。

## 1. 唯一变量与 answer-agnostic 边界

- 固定不变:AAV 候选池 27,832、HD≤2 cold-start 10,433、查表 oracle、48×6=288 预算、HD≤4 且 mean BLOSUM62≥0 门禁、seed 42、one-hot degree-2 `EpistasisRidgePredictor`。
- 唯一变量 = 决策层:v0.5 保留 C(工具鲁棒)+ A(CV 透传);B 的自适应配比(探索税)按裁定移除,v0.6 默认采集 = **纯 predicted-mean top-n**(`allocation_source=v06_pure_exploit_default`,两 run 全部 6 批 48/0);backtrack 只作为停滞逃逸机制。
- 停滞检测只用已测 fitness 轨迹(`top10_max_history`、`rounds_since_improvement`);redirect 候选只用 surrogate 预测均值 + 已测 top-10 最优簇的替换签名(`_best_cluster_signature`,≥50% 共有);真值 oracle 只在 `test` 花预算时查表。§5/§6 的反事实全部是 campaign 结束后的只读诊断,未回灌任何模型、阈值或 prompt。
- **模型后端如实记录**:dispatch 建议 GLM-5.3,但本端点(token.qianbaner.top)模型列表无 GLM 系列;按 task_plan 注记改用端点实际可用、且与 v0.4/v0.5 相同的 **gpt-5.6-sol**,使 v0.1→v0.6 的唯一变量仍是决策层。核心是决策机制,不是后端。

## 2. v0.1 → v0.6 对照

| 方法 | 预算 | cum_top10_max | strong 命中 | 结论 |
|---|---:|---:|---:|---|
| agentic v0.1(自由) | 288 | 5.96 | 15 | 无约束探索有毒 |
| workflow greedy(加性) | 288 | 7.53 | 85 | 加性 surrogate 天花板 |
| agentic v0.2(门禁) | 288 | 7.53 | 93 | 门禁治预算浪费 |
| agentic v0.4(上位 surrogate) | 288 | 7.829 | 108 | 破 7.53,弱于"8.416 参照线" |
| v0.4 deterministic PM/diverse 交替 | 288 | **8.4162** | 151 | 真峰出自 r4 **diverse(UCB)批**(§6) |
| agentic v0.5(自适应配比) | 288 | 6.5309 | 163 | 4.2% 探索税毁掉 greedy 头部 |
| **v0.6 FULL(元层全自主)** | **288** | **7.829** | **166** | 纯利用+自判停滞+redirect,停在纯利用天花板 |
| **v0.6 SEMI(硬规则旗标)** | **288** | **7.829** | **166** | 同上,停滞由 2 行硬规则判定 |

两变体曲线完全一致:`[7.391, 7.829, 7.829, 7.829, 7.829, 7.829]`;cum top-10 mean 6.5317。相对 v0.5 修复 +1.298(rank-45 教训的默认强利用生效),strong 命中 166 为全版本最高;但未追平 8.4162。

## 3. agent 是否真的执行了元层协议(事件流证据)

两 run 各 25/27 个事件、哈希链校验通过、`agent.tool.error`/`agent.llm.round_error`/`agent.llm.no_test` 全部为 0、`n_gate_rejected=0`、288/288 预算。逐轮(批次 max / 累计):

| 轮 | 动作(full) | 动作(semi) | batch max | cum |
|---:|---|---|---:|---:|
| 1 | compose 48/0(纯利用默认) | compose 48/0 | 7.391 | 7.391 |
| 2 | compose 48/0 | compose 48/0 | **7.829** | 7.829 |
| 3 | compose 48/0 | compose 48/0 | 5.991 | 7.829 |
| 4 | compose 48/0 | compose 48/0 | 6.531 | 7.829 |
| 5 | **redirect(LLM 自判停滞)** | **stall_flag(rsi=2)→ redirect** | 5.250 | 7.829 |
| 6 | compose 48/0(回 exploitation) | stall_flag(rsi=3)→ compose(LLM 选择不 redirect) | 6.262 | 7.829 |

- **首轮 7.391 精确命中 v0.5 反事实预测**(纯 top-48 的 batch max 7.3910)——rank-45 修复在真实 run 中验证,不是只有事后推演。
- **停滞检测两变体同一轮触发**:semi 的硬规则(cum_top10_max 连续 ≥2 轮不涨)在 r5 置 `stalled=true`;full 没有任何规则提示,LLM 从 `campaign.top10_max_history=[7.391,7.829,7.829,7.829]` 自主判定停滞,同样在 r5 调用 `redirect_batch`。**在"何时判停滞"上,LLM 元层判断 = 2 行硬规则**,且都判断对了(此后确实再无新高)。
- semi r6 旗标再次触发时,LLM 选择回纯利用而非二次 redirect(prompt 赋予的"是否 redirect"判断权被真实使用,且方向正确:该轮 redirect 同样不会有效,见 §4)。
- CV 透传(A)持续工作:6 轮 CV Spearman 均在 0.90 上下,agent 据此全程采用纯利用默认,没有手改比例、没有绕过工具。

## 4. redirect 为什么没有形成换区:空签名退化

r5 的 `redirect_batch` 事件 payload:`signature_size=0, n_hop_eligible=9341, picks_overlap_mean=0.0, predicted_mean_top=6.0053`。机制分解:

1. **签名构造规则**:取已测 top-10(cold-start 含 9.536/8.645/8.438…),收集 ≥50% 共有的替换。实测最高共享替换仅 `T20E` 4/10 < 5/10,**签名为空**——本地形的最优已测簇不共享一条主导替换(上位性强、context-dependent),"当前盆地"没有可指认的突变指纹。
2. **空签名 → redirect 全池合格 → 按 mean 排序取 top-48 = 与 compose 纯利用默认完全相同的一批**(r5 批次 max 5.2504,与 §5 纯 PM 回放的 r5 批 5.2504 逐位一致)。换区动作名存实亡:redirect 没有 redirect 到任何不同的地方。
3. 这不是 LLM 的判断失误——两个变体、两种自主度,拿到的 redirect 工具都只能按 mean 重排。**逃逸机制缺的不是"何时逃",是"往哪逃"的信号**:它没有任何方差/不确定性项。

## 5. 承重反事实一(campaign 后只读):纯利用的真实天花板是 7.829

用相同 cold-start、门禁、EpistasisRidge,离线回放 6 轮纯 predicted-mean top-48(每轮重拟合):

```
PURE-PM greedy curve: [7.391, 7.829, 5.9907, 6.5309, 5.2504, 6.262]  真峰从未被测
```

该曲线与 v0.6 两变体的 6 个实际批次 max **逐批完全一致**——v0.6 agent(两变体)就是精确执行了纯 greedy。在 r5 状态(4 批之后),真峰在剩余 9,341 个门内候选中 mean 排名 **#1658**、UCB(mean+3sd) 排名 **#1986**:任何只按 mean 重排的决策层(redirect 包括在内)都够不到它。**7.829 是"rank by mean"这一决策面的上限,与 agent 自主度无关。**

## 6. 承重反事实二(artifact 证据):8.416 参照线本身含调度的 UCB 探索

v0.4 `deterministic.metrics.json` 的 tool_trace 逐轮记录:采集交替 `by=predicted_mean / by=diverse`,batch max `[7.391, 6.5309, 7.829, 8.4162, 7.0807, 4.9355]`——**8.4162 出现在 r4 的 diverse 批**(diverse = mean + 3√var + rng)。离线回放同一交替序列,r3 状态(即 r4 diverse 批的决策点)真峰的排名:mean **#2930**/9,437,UCB **#15**/9,437。也就是说:

- 把真峰从"mean 排名 #2930"抬进 48 名射程的,是**不确定性项(3√var)**,不是更纯的利用,也不是任何换区逻辑;
- 任务前提"确定性 greedy 纯利用能直达 8.416,说明 surrogate 没把 greedy 带进陷阱"在 artifact 层面**不成立**:该参照线是一个 exploit/UCB-explore 交替驱动,其制胜手恰是 v0.6 按裁定移除的那类探索(只是它是被调度的、结构化的 mean+3√var,而非 v0.1/v0.5 那种离散极端探索)。
- 这构成对 task Context 的 evidence-backed 修正(正中 checkpoint 的异议型条款):v0.6 的负结果不是"backtrack 没用"这么简单,而是**"纯利用天花板 7.829 + 逃逸动作无方差信号"双重锁死**。backtrack 的检测半边(何时)被验证有效,动作半边(往哪)从构造上就不可能突破 mean 决策面。

## 7. 工具鲁棒性与阴性对照

- 正式 run:full/semi 各 288/288 预算、6 次 compose/redirect + 6 次原样 `test_composed_batch`、0 工具错误、0 门禁拒绝、0 no_test fallback;C(鲁棒)无退化。
- 阴性对照(单测,`tests/test_auto_researcher_backtrack.py`,28/28 绿):
  - 停滞规则在**持续上升**序列上全程不触发(`test_rising_curve_never_counts_stagnation`);
  - redirect 选择对池内**真值 fitness 打乱不变**(组批器输入只有 surrogate 均值与已测簇签名,`test_redirect_picks_are_blind_to_true_fitness`);
  - v0.6 默认配比从 r1 即 1.0(`test_v06_backtrack_default_is_pure_exploitation_from_round_one`),v0.5 路径默认不变(`test_v05_mode_keeps_the_adaptive_default_unchanged`);
  - v0.5 SYSTEM_PROMPT 在 backtrack 关闭时**字节级不变**(与 git HEAD 对比)。
- 已知口径:cold-start 已含 9.536 incumbent,LLM 末尾摘要再次把它称为"best measured"(与 v0.5 同款口径混淆);主指标 cum_top10_max 只统计本轮 288 个 tested variants,报告数字不受影响。

## 8. 复现与产物

```bash
# FULL(全自主)
PYTHONPATH=. .venv/bin/python -m agent.auto_researcher --dataset aav --feature one_hot \
  --guardrail --surrogate epistasis --budget 48 --n-rounds 6 --seed 42 --model gpt-5.6-sol --backtrack full
# SEMI(硬规则旗标)
PYTHONPATH=. .venv/bin/python -m agent.auto_researcher --dataset aav --feature one_hot \
  --guardrail --surrogate epistasis --budget 48 --n-rounds 6 --seed 42 --model gpt-5.6-sol --backtrack semi
# 定向测试
PYTHONPATH=. .venv/bin/python -m pytest tests/test_auto_researcher_backtrack.py \
  tests/test_auto_researcher_compose.py tests/test_auto_researcher_gate.py \
  tests/test_epistasis_surrogate.py -q          # -> 28 passed
```

产物:`aav/full/`、`aav/semi/`(各含 metrics/events/figures,事件链校验通过)、合并对照图 `aav/figures/curves.png`;SHA-256 见 `manifest.json`。承重观察已晋升 canonical fact(见任务 Execution outputs)。

## 9. 结论、风险与下一步

**结论**:v0.6 达成了两个正结果与一个钉死的负结果。(1) 移除探索税 + 默认强利用,把 v0.5 的 6.5309 修复回 7.829,strong 166 为全版本最高——v0.5 报告"rank-45 离散截断"的机制解释在真实 run 中被证实。(2) 元层停滞检测有效且稳健:硬规则与 LLM 自主判断在同一轮触发、均无假阳性(上升期不触发有单测保证)。(3) 负结果:redirect 无法突破 7.829——空签名使换区退化为原批,且纯 mean 排序的决策面天花板就是 7.829;而 8.416 参照线的制胜手是被调度的 UCB 探索(r3 状态真峰 UCB #15)。"LLM 元层判断有价值"在"检测"半边成立(=硬规则),"任何绕路都是税"在本地形上需修正为:**无方差信号的绕路都是税;带 mean+3√var 的被调度探索不是**。两种自主度(full/semi)在同决策面上给出同一结果,互为对照。

**风险**:单 dataset/seed/model;full 与 semi 的等价性来自同 seed 同决策面,LLM 判断与硬规则的等价只在这一次停滞事件上验证;8.416 反事实依赖 v0.4 artifact 的 tool_trace 与确定性回放(rng 噪声使 r2+ 批次无法逐位复现,但不影响"8.416 出自 diverse 批"这一由 tool_trace 直接记录的事实);cold-start 9.536 incumbent 的口径问题延续。

**下一步(需 CEO 预注册,不在本 run 内调)**:
1. 把 redirect 的组批排序从 pure mean 改为 **mean + κ√var(不确定感知 basin-hop)**,仅在停滞旗标轮启用——这是唯一同时满足"答对何时"与"答对往哪"的候选,且 κ 不按测试峰调;
2. 把 v0.4 的 PM/diverse 交替作为正式 baseline 命名(如"deterministic UCB-alternation")写进最终报告的对照表,修正"greedy 纯利用 8.416"的表述;
3. 多 seed/多数据集复验"空签名"是否为 AAV 特有(GB1 top 簇可能存在主导替换,redirect 或可生效)。
