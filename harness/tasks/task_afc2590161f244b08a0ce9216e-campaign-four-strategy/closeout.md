# Closeout

## Summary

campaign 对比引擎:四策略(随机/模型贪心/Agent/知识增强 UCB)×3 轮闭环,149,361 提名口径,三档冷启动(easy/hard/sparse)+ LLM 注入档;GB1 与 AAV 双地形。

交付提交:`ebf5e17afc7cf1556ba240977d2276ba841ae27b`(四策略 campaign 引擎)。

## Verification

GB1 hard:greedy 达全局峰 8.762、knowledge strong 57;AAV:四策略卡 7.53、真峰 8.42 greedy 可证明够不着。事件链校验通过。促成 Fact F-A97B5159、F-45DD053A、F-A0F3187E。

## Residual Risk

LIBRARY_CAP 曾截断组合库致漏峰(已修至 10000);稀疏地形组合库设计会失效,故 AAV 改用池式(pool_campaign)。

## Same Mechanism Elsewhere

四策略的候选排序 acquisition 机制被 pool_campaign(池式)与 agentic 的 list_pool 多轴复用;UCB 的不确定性项风险见 agentic-v0.1 尸检。
