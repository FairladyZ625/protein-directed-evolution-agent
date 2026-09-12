# Review review-dispatch_46046dfe7df1b74f4fdddaaf

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_afc2590161f244b08a0ce9216e
- Execution: exe_9049aa1c5cdc1f324f5fbc3014
- Verdict: changes_requested
- Commit: ebf5e17afc7cf1556ba240977d2276ba841ae27b
- Iteration: 1
- Content digest: sha256:5f3abbb453c1936b010fa4805ef9f8dad613f3ca303939e526f41e154ab2b3e0
- Submission digest: sha256:19ce352833ad60126819a8127e8219673e59bcf4aedc93dce17d14594c5edeb9
- Reviewed at: 2026-09-12T13:10:24.503Z
- Consent: pending
- Consent actor: pending
- Consent source: pending

## Reason

打回。固定提交 ebf5e17afc7cf1556ba240977d2276ba841ae27b 未修复上一轮核心缺陷，且契约指定测试在隔离快照中真实失败：tests/test_campaign.py 为 2 failed（首轮 cumulative 的 Fitness 列保持 object dtype，nlargest 抛 TypeError）。evolution/campaign.py 中 agent_no_knowledge 与 knowledge_agent 均未调用 agent.pipeline.run_pipeline，也无 llm_hypothesis/llm_critic 注入；三种非随机策略实际共用同一 Ridge 排序，仅 knowledge_agent 加 UCB，不能构成题面要求的模型直推/LLM Agent/知识增强 Agent 四方法比较。随机仍仅 seed=42 单次运行，metrics 无跨 seed 均值/方差，plot_campaign 仅 ax.plot、无误差带。事件样例虽通过 EventStore.verify 且篡改阳性对照能报 chain broken，但只有 started/round.completed/completed 三类共 20 条，未记录计划要求的逐步提名、oracle 查表、回填和重训事件。metrics 正确声明 candidate_space_size=149361、missing_combinations=10639、oracle=measured table lookup，四策略各 3 轮同预算 96，但缺少关键位点集中分析。修复方向：先修 cumulative 数值 dtype 并让定向测试真实全绿；随机运行多个明确 seeds 并产出 mean/std 与 fill_between；策略③④按任务接口实际调用 run_pipeline（商业 LLM 或明确标注 fallback），分别传 no_knowledge=True/False，保留相同候选空间与预算；为 propose/oracle/refill/retrain 各追加可审计事件；在 metrics 加 Top-k 位点/残基集中统计及相应测试。

## Evidence checked

- 隔离 git archive 快照 ebf5e17afc7cf1556ba240977d2276ba841ae27b；.venv/bin/python -m pytest -q tests/test_campaign.py => 2 failed in 1.68s，均为 pandas nlargest 对 object dtype 抛 TypeError
- git show 固定提交 evolution/campaign.py 与 tests/test_campaign.py；_propose 对 greedy/agent_no_knowledge 使用相同 mean 排序，knowledge_agent 仅 mean+0.75*sqrt(var)，无 run_pipeline/LLM 端口调用
- git grep 固定提交未命中 run_pipeline、llm_hypothesis、llm_critic、fill_between、随机多-seed/std 聚合；metrics 四策略 seed 均为 42
- 固定提交 reports/campaign_metrics.json：candidate_space_size=149361、missing_combinations=10639、oracle=measured table lookup，四策略各 3 轮且每轮 96；agent 两策略 fallback=true
- 固定提交 reports/campaign_events.jsonl：EventStore.verify 通过，共 20 条，仅 campaign.started/campaign.round.completed/campaign.completed；人工篡改第 2 条 payload 后 verify 报 chain broken at seq=2（检测器阳性对照）
- 固定提交 reports/figures/campaign_curve.png 经 file 识别为 1200x675 PNG；代码仅 ax.plot，无随机误差带
- 任务计划、AI4S worker handbook、AI4S-assignment.md、AI4S-master-plan.html，以及实际 random_baseline/T3 predictor/T6 pipeline/T4 EventStore 接口
