# Closeout

## Summary

建成首个真自主 agentic AutoResearch agent（`agent/auto_researcher.py`），由 SOL（`gpt-5.6-sol`）
经 pydantic-ai 工具调用驱动：6 个工具（analyze_measured / predict / list_pool / check_knowledge
/ test / best_so_far）+ 逐轮有界自主循环 + 确定性兜底。在 AAV 池（288 预算）跑通：agent 做出
25 次自主工具调用、预算全花，是真 tool-calling 决策而非写死流水线；但**诚实地输给了朴素 greedy**
（cum_top10_max 5.96 vs 7.53、strong 命中 15 vs 85）。随后用可复现的机制尸检
（`analysis/agentic_postmortem.py`）定位了失败根因（方差有毒）。附带修复了 EventStore 并发竞态
（使 agentic 多工具并发可靠落盘），并把产物迁入 `harness/reports/` 版本化树、登记为 ReportEntity。

## Verification

- 43 项单测通过，含新增 200 并发 append 回归测试（`tests/test_events.py::test_concurrent_appends_keep_chain_intact`）。
- 事件链 SHA-256 校验通过：`harness/reports/agentic-v0.1/aav/agentic.events.jsonl`（25 事件，`store.verify()` OK）。
- 独立评审 + consent：由泽宇经 GUI 裁决（本 agent 不自审）。
- 已促成的 Facts：`F-327D08B4`（方差∝突变阶数∝负fitness,故 agent 输 greedy）、`F-3169EBC2`
  （25 次自主工具调用,真 tool-calling）、`F-8FA12407`（ESM-2 公平对照下未救回真峰）。
- 产物实体：`REP-3e2a7fefcc2563d440a93f27565c566a`（agentic-v0.1 整文件夹,内容 SHA256 锁定）。

## Residual Risk

- 该失败结论目前只在 AAV one_hot/esm2 两表征上证实；跨地形（avGFP 等）普适性待补（avGFP 数据尚缺）。
- ESM-2 mean-pooled 在 AAV 定长替换任务上劣于 one-hot，完整 ESM campaign 暂缓。
- `report → task` 关系待决策 `dec_561738967E6C5014C6C17A924A` 独立接受后接线（泽宇 GUI 裁决中）。
- 下一版 v0.2（强制 Knowledge 门禁流:HD≤4 截断 + BLOSUM62 硬过滤）用于检验结构化约束能否消除探索惩罚——非本任务阻塞项。

## Same Mechanism Elsewhere

机制句（去掉调用方/资源/症状）：**"按模型不确定性给候选打分的选择策略，会优先选中模型未训练过的区域，
而该区域在此类地形上恰好与非功能/高阶突变尾部重合。"**

仓库内搜索该机制：命中 `evolution/pool_campaign.py::_rank` 里 knowledge_agent 的 UCB 项
`LAMBDA_UCB * sqrt(var)`——它同样把不确定性加进 acquisition，但**已有 `BETA_BLOSUM` 保守性先验作为守卫**
压制"选中死蛋白"；以及 agent 自己的 `list_pool(by="uncertainty"/"diverse")` 轴（无守卫）。
结论:凡"用不确定性驱动选择"处都需同一守卫,v0.2 的门禁流正是把该守卫前移为硬约束。
