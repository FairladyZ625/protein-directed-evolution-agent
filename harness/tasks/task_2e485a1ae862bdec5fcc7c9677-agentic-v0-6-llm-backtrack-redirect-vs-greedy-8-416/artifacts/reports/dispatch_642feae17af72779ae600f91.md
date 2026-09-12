## 任务完成汇报：agentic v0.6 元层 backtrack(full vs semi)

**终态：两个变体 cum_top10_max 均 7.829、strong 命中 166(全版本最高)，未追平 8.416——但负结果的机制被完全钉死，并包含一个对任务前提的 evidence-backed 修正。** 本地 commit `471536b`,fact `F-72B1D940`,报告落 `harness/reports/agentic-v0.6/`。

### 实测结果(runner 原始输出)

```
full: llm_used=True model=gpt-5.6-sol budget_spent=288 tool_calls=25 backtrack=full redirects=[5] cum_top10_max=7.829 strong=166
semi: llm_used=True model=gpt-5.6-sol budget_spent=288 tool_calls=27 backtrack=semi redirects=[5] stall_flags=[5,6] cum_top10_max=7.829 strong=166
```

曲线均为 `[7.391, 7.829, 7.829, 7.829, 7.829, 7.829]`;28/28 定向测试绿；两 run 事件链哈希校验通过，0 工具错误、0 门禁拒绝。模型说明：端点无 GLM 系列，按 task_plan 注记用与 v0.4/v0.5 相同的 `gpt-5.6-sol`(保持唯一变量=决策层)，已在 report/manifest 如实记录。

### 三个承重发现

1. **纯利用默认修复了 v0.5 退化**：6/6 批 48/0(`v06_pure_exploit_default`),首轮 batch max 7.391 精确命中 v0.5 反事实预测——rank-45 教训在真实 run 中验证。
2. **停滞检测有效，LLM 自主判断 = 2 行硬规则**：full(LLM 从轨迹自判)与 semi(硬规则 rsi≥2)同在第 5 轮触发 redirect;semi 第 6 轮旗标再触发时 LLM 正确选择回 exploitation。检测半边赢了。
3. **redirect 无处可跳 + 8.416 前提被 artifact 证伪**：已测最优簇签名空(最高共享替换 T20E 仅 4/10)→ redirect 退化为同一批 greedy top-48。campaign 后只读反事实：纯 PM greedy 六轮回放与 v0.6 批次**逐批一致**、真峰从未被测(7.829 = mean 决策面上限)；而 v0.4 的 8.4162 出自其 **r4 diverse(mean+3√var) 批**(tool_trace 直接记录，r3 状态真峰 UCB 排名 #15 / mean #2930)——**“确定性 greedy 纯利用直达 8.416”不成立，8.416 参照线含被调度的 UCB 探索**。逃逸机制的缺口不是“何时”，是“往哪”：redirect 只按 mean 重排，永远缺方差信号。

### Blocker(需 CEO 处理)

`ha task submit` 被 daemon CI 钩子拒(`service_rejected`:远端 `FairladyZ625/protein-directed-evolution-agent` 默认分支无 `rewrite-ci.yml`,`gh run list` 404)。按 CI/Gate 停手条款未建 workflow、未绕门，已记入台账；closeout.md 四节已写好，fact/report/commit 均就位，workflow 补上后 submit 即可重放。

### 残余风险与下一步

单 dataset/seed/model;full=semi 等价性仅一次停滞事件；分支与 origin/main 无 merge-base(v0.5 同款，rebase 不可行);`experiment_log.jsonl` 被 run 追加但未暂存(超出声明文件面，归 CEO)。下一步需预注册：① redirect 排序改 mean+κ√var(停滞轮启用，κ 不按测试峰调)；② 最终报告把 v0.4 baseline 正名为 "PM/diverse(UCB) alternation" 并同步修正 F-F7BC7554 等文档表述；③ GB1 复验空签名是否 AAV 特有。