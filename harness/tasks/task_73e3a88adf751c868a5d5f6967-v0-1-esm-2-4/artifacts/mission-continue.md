# 续跑:保守位点分析(上轮只写了代码,没跑出产物)

上轮你在 worktree `.worktrees/t-conservation` 写了 `features/conservation.py` 与
`tests/test_conservation.py`,但**没提交、也没产出任何交付物**(无 JSON、无图、无报告),
会话就退出了。CEO 已把那两个文件提交保住:`4da15ac`。

**本轮从那个提交继续,不要重写已有代码。** 先 `git fetch && git rebase origin/main`
(现在是 `3d241f7`),然后把交付跑完。

## 上轮缺的部分(task_plan.md 的 Deliverable Contract 全文仍然有效)

1. `harness/reports/analysis-v0.1/{gb1,aav}/conservation.json`(全精度)—— **没有**
2. `harness/reports/analysis-v0.1/{gb1,aav}/figures/conservation.png` —— **没有**
3. `harness/reports/analysis-v0.1/conservation-report.md` —— **没有**
4. `pytest tests/test_conservation.py` 跑绿 —— 未验证

## 复述两条不可妥协的口径(task_plan 的 Constraints)

- **保守性只能用于分析与解释,绝不能进入采集或筛选路径。** ESM-2 的熵是自然度先验,
  而本项目真峰是反自然的(zero-shot 片段排 #3743、全长 #4782)。把它接进 `evolution/`
  任何采集路径 = 整轮作废。
- **首要产出是真峰三个位点(AAV 28aa 序列的第 0、17、18 位)在保守性排序里的位次。**
  若真峰位点落在高保守区,那正是「保守性先验会拒绝真峰」的直接证据 ——
  **这个负结果比一张漂亮的保守性图有价值得多。**

## 新增可用的上下文(上轮之后才有的)

同属 analysis-v0.1 的突变阶数分析已合入主线,产物在
`harness/reports/analysis-v0.1/{gb1,aav}/mutation_order.json`。其中有每个位置的效应信息
可供你的「保守性 vs 实测效应」对照复用,**只读它,不要改它,也不要改它的 report.md**
(你写自己的 `conservation-report.md`)。

## 边界不变

只动 `features/conservation.py`、`tests/test_conservation.py`、
`harness/reports/analysis-v0.1/{gb1,aav}/conservation.*` 与 figures、`conservation-report.md`。
ESM 后端跑不起来就按 blocker 回报停手,**不许用随机数或近似值顶替熵值交差**。
停止点 = 点名测试绿 + commit,不 push、不发 PR。
