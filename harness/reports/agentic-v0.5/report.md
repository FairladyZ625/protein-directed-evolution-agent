# 中期报告 05（实验四）：质量感知 agent 消除了工具崩溃，但自适应探索仍伤害极值发现

> 一句话：在与 v0.4 完全相同的 AAV pool/cold-start/oracle/门禁/预算/seed/上位 surrogate 下，v0.5 把 CV Spearman `0.9002–0.9059` 显式交给 agent，并用 `compose_batch` 将 288 个名额配成 276 exploit + 12 explore；工具错误从 v0.4 的 2 次降为 0、strong 命中从 108 升到 163，但 `cum_top10_max` 从 **7.829 降到 6.5309**。这是未达 Goal 的诚实负结果：对极值发现而言，即使只有 4.2% 的早期探索税，也足以把高质量 surrogate 带离纯 greedy 路径。

## 1. 唯一变量与 answer-agnostic 边界

- 固定不变：AAV 候选池 27,832、HD≤2 cold-start 10,433、查表 oracle、48×6=288 预算、HD≤4 且 mean BLOSUM62≥0 门禁、seed 42、one-hot degree-2 `EpistasisRidgePredictor`。
- C（鲁棒性）：全序列清洗、长度/字符校验、突变代号友好拒绝、工具异常结构化；`compose_batch` 暂存候选后由无参数 `test_composed_batch` 原样测试，避免 LLM 转抄 28-aa 字符串。
- A（质量透传）：`EpistasisRidgePredictor.val_spearman` 暴露 held-out Spearman；`analyze_measured.surrogate_status` 每轮返回架构、CV、置信级别和建议。删除旧 prompt 的“~0.6 且系统性低估峰”静态锚定。
- B（配比采集）：缺省 `min(1, max(0.4, val_spearman² + round/n_rounds×0.3))`，并保证高 CV 至少 80%、最后两轮至少 90% exploit。探索端只从门内 diverse 排名取样。
- 所有训练与采集只读取已测标签；下面的真值反事实诊断在 campaign 结束后运行，未回灌模型或阈值。

## 2. v0.1 → v0.5 对照

| 方法 | 预算 | cum_top10_max | strong 命中 | 结论 |
|---|---:|---:|---:|---|
| agentic v0.1（自由） | 288 | 5.96 | 15 | 无约束探索有毒 |
| workflow greedy | 288 | 7.53 | 85 | 加性 surrogate 天花板 |
| agentic v0.2（门禁） | 288 | 7.53 | 93 | 门禁修复预算浪费，但不破表征上限 |
| v0.3 加性诊断 | 288 可达线 | 峰预测排名 #1283 | — | 峰不在射程 |
| agentic v0.4（上位 surrogate） | 288 | **7.829** | 108 | 破 7.53，但仍弱于 greedy |
| v0.4 deterministic gated-greedy | 288 | **8.4162** | 151 | 同 surrogate 直达真峰 |
| **agentic v0.5（质量感知 adaptive）** | **288** | **6.5309** | **163** | 头部覆盖变宽，极值发现反而退化 |

v0.5 的累计峰曲线为 `[5.9988, 5.9988, 6.5309, 6.5309, 6.5309, 6.5309]`；累计 top-10 mean 为 6.1922。相对 v0.4 agentic，峰值下降 1.2981，但 strong 命中增加 55，说明该采集规则优化了“多找强变体”，没有优化本任务的主目标“找到最高峰”。

## 3. agent 是否真的感知并执行了质量信号

每轮 `analyze_measured` 均报告 `VERY_HIGH`，CV Spearman 依次为 `[0.9059, 0.9003, 0.9027, 0.9002, 0.9043, 0.9057]`。agent 六轮均选择 answer-agnostic 缺省，没有绕过工具或手改比例：

| round | exploit | explore | exploit ratio | batch max |
|---:|---:|---:|---:|---:|
| 1 | 42 | 6 | 0.8707 | 5.9988 |
| 2 | 44 | 4 | 0.9105 | 5.7677 |
| 3 | 46 | 2 | 0.9648 | 6.5309 |
| 4 | 48 | 0 | 1.0000 | 6.4392 |
| 5 | 48 | 0 | 1.0000 | 5.6437 |
| 6 | 48 | 0 | 1.0000 | 6.2620 |

总计 276 exploit / 12 explore（95.8% / 4.2%）。v0.4 的事件口径是工具调用次数：`predicted_mean` 9 次，对比 `diverse/uncertainty/random` 19 次；v0.5 将其收敛为 6 次结构化 compose，且没有再调用离散极端的 `list_pool` 策略。两版单位不同，不能把 9:19 与 276:12 直接当同一比例比较。

## 4. 为什么仍然更差：首批 rank-45 被 6 个 explore 挤掉

campaign 后用相同 cold-start surrogate 做只读反事实：若首轮取纯 predicted-mean top-48，真实 batch max 是 **7.3910**；其中最高真值候选位于预测均值排名 **#45**。自适应规则只保留 top-42，恰好将 #43–#48 全部替换为 diverse，因此实际首批 max 只有 **5.9988**。

- 被替换的 mean rank #43–#48 真值：`[2.8427, 4.0494, 7.3910, -1.5387, 2.4406, 3.2063]`。
- 换入的 6 个 diverse 真值：`[4.4412, 1.6172, 1.1961, 5.8322, -0.8568, 1.7439]`。

关键不是“探索很多”，而是有限批次的离散截断效应：仅替换 6/48，就漏掉 #45 的 7.391 标签；第一轮训练集不同后，后续 surrogate 排序路径也不同。即使 round 4–6 已纯利用，也未在剩余 144 预算追回 v0.4 的 7.829 或 greedy 的 8.4162。这直接命中任务的异议条件：当前 `compose_batch` 默认公式对该高质量 surrogate/seed 是有害的，不能继续把“近纯 greedy”当成“等价纯 greedy”。

## 5. 工具鲁棒性与事件证据

- 正式 run：288/288 预算，6 次 compose、6 次原样 test；`n_gate_rejected=0`。
- `agent.tool.error=0`、`agent.llm.round_error=0`、`agent.llm.no_test=0`；v0.4 的两次 `string index out of range` 未复现。
- 事件哈希链验证通过，共 25 个高内聚事件。数量少于原协议预期的 50+，原因是一次 compose + 一次原样 test 取代了每轮多次 `list_pool/predict/check`；事件完整覆盖 6 轮状态、配比和测量，但未人为拆分事件凑数。
- 阴性对照：XOR 合成数据打乱标签后，held-out `val_spearman=-0.119960`，置信信号塌到近 0；未把随机标签误当高质量 surrogate。

## 6. 复现与产物

```bash
PYTHONPATH=. .venv/bin/python -m agent.auto_researcher --dataset aav --feature one_hot \
  --guardrail --surrogate epistasis --budget 48 --n-rounds 6 --seed 42 --model gpt-5.6-sol

PYTHONPATH=. .venv/bin/python -m pytest \
  tests/test_auto_researcher_gate.py tests/test_epistasis_surrogate.py \
  tests/test_auto_researcher_compose.py -q
```

产物位于 `aav/agentic.metrics.json`、`aav/agentic.events.jsonl` 和 `aav/figures/agentic.png`。SHA-256 分别为 `a718c0b63bae…`, `20c16adcd13d…`, `6794ed9778da…`。
承重观察已晋升为 canonical fact `F-F7BC7554`。

## 7. 结论、风险与下一步

结论：C 与 A 达到预期——工具链零崩溃且 agent 持续读到真实 CV；B 未达到预期——自适应探索在极值指标上显著有害，v0.5 没有缩小差距，反而从 7.829 降到 6.5309。这个负结果进一步支持 v0.4 的核心判断：当 surrogate 已足够好且目标是固定预算内极值发现，纯 greedy 的截断排序不能被“近似 greedy”随意替代。

风险：这里只验证一个 dataset/seed/model run；CV 是固定 80/20 held-out Spearman，不等于 acquisition regret 的校准；25 事件低于预定 50+ 粒度；LLM 末尾摘要把 cold-start 中已有的 9.536 incumbent 称为 “discovered”，主指标则正确只统计本轮 288 个 tested variants；任务分支与远端 `origin/main` 无共同 merge-base，无法安全执行交付前 rebase。

下一步需 CEO 先裁定新的、预注册的实验，而不是依据本次 oracle 结果现场改阈值。优先消融是：保留 C+A 与原样批次工具，但在 CV≥0.90 时从 round 1 使用纯 predicted-mean；同时在多 seed 或另一数据集验证，避免把本次 rank-45 事件反向编码进规则。
