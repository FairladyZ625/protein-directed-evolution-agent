# 包1:四策略主链真实性(最高优先,这是笔试题⑤的核心)

你在修一个**已被独立评审打回的任务**。评审意见全文在任务包的 `reviews/` 下最新一份 .md,
**先读它**,它给的是工具证据不是猜测。本 prompt 只补充 CEO 的验收口径。

## 缺口(评审实测,已由 CEO 复核)

1. **策略③④是假的四方法比较**:`evolution/campaign.py` 里 `agent_no_knowledge` 与
   `knowledge_agent` 都**没有调用 `agent.pipeline.run_pipeline`**,也没注入 `llm_hypothesis`/
   `llm_critic`。三种非随机策略实际共用同一个 Ridge 排序,只有 `knowledge_agent` 多加 UCB。
   题面要求的是「随机 / 模型直推 / LLM Agent / 知识增强 Agent」四个**机制不同**的方法。
   → 策略③④必须真的走 `run_pipeline`,分别传 `no_knowledge=True` / `False`,
     保持相同候选空间与预算。LLM 用不上时**明确标注 fallback**(现有 `_llm_hypothesis` 的
     `state["source"]` 机制就是对的,沿用它),不要假装调了。
2. **契约指定测试真实失败**:`tests/test_campaign.py` 在隔离快照里 2 failed——首轮 cumulative
   的 `Fitness` 列保持 object dtype,`nlargest` 抛 TypeError。先修这个 dtype,让点名测试真绿。
3. **随机基线只有 seed=42 单次**:metrics 无跨 seed 均值/方差。跑多个**明确写死的** seeds,
   产出 mean/std;`plot_campaign` 现在只有 `ax.plot`,要加 `fill_between` 误差带。
4. **事件流不完整**:只有 started / round.completed / completed 三类共 20 条。计划要求逐步
   提名、oracle 查表、回填、重训各自可审计 → 为 propose / oracle / refill / retrain 各补事件。
5. **缺关键位点集中分析**:metrics 要加 Top-k 位点/残基集中统计,并配相应测试。

## 验收口径(CEO 亲验,达不到就是没做完)

- `pytest tests/test_campaign.py` 在**干净 clone 的冻结提交树上**全绿。不是在你的工作区绿。
- 四策略的**机制差异必须可从代码读出**:③④ 的调用栈里有 `run_pipeline`,且 `no_knowledge`
  取值不同。我会自己 grep 验证,不看你的汇报。
- 跨 seed 的 mean/std 必须来自真的多次运行,不是同一次运行的抖动。seeds 写死在代码里。
- 事件条数和类型我会用 `EventStore.verify` 加篡改阳性对照复核。

## 边界

- **只动** `evolution/campaign.py`、`tests/test_campaign.py`、campaign 的绘图与 metrics 产出路径。
- **不要动** `agent/pipeline.py`(另一个 worker 正在改它的内部实现,但 `run_pipeline` 的签名
  保持不变:`run_pipeline(pool, predictor, *, event_store, llm_hypothesis, llm_critic, budget,
  round_id, no_knowledge)`)、`models/`、`knowledge/`、`events/`。
- 不要为了达分改 oracle、改门禁、改 seed 选择。**负结果是合法交付**,造假不是。
- 独立 worktree,不占仓库根。停止点 = 点名测试绿 + commit,**不 push、不发 PR**。

## 停手与异议

任何一步发现 CEO 的判断错了(比如 ③④ 其实已经接了而评审看错了),**带证据回报并停手**,
不要按错的 mission 往下做。预算:一条语义线做完即止,不要顺手重构无关代码。
