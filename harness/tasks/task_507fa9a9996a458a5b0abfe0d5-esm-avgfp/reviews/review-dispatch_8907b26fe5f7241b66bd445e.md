# Review review-dispatch_8907b26fe5f7241b66bd445e

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_507fa9a9996a458a5b0abfe0d5
- Execution: exe_e1eee94f119d4b4a1dcd748366
- Verdict: changes_requested
- Commit: a3a979adcc478eca7f8fe1f444fa9c5fc121fd5b
- Iteration: 0
- Content digest: sha256:5bac31ba7a3c6d3758a5e6ea7b6f14ca64db5f76cd7af4561ff0898b2812f3eb
- Submission digest: sha256:8baac074ef1b759c8a57bd0a5dc2659acd6f3e2c964b2b0b32e5d586ec305583
- Reviewed at: 2026-09-12T12:28:36.843Z
- Consent: pending
- Consent actor: pending
- Consent source: pending

## Reason

打回：冻结提交只证明了合成数据上的 bootstrap 方差、avGFP WT loader guard 与 ESM 全长输入接口；任务契约要求的 AAV-ESM 和 avGFP 四策略 metrics/事件流/曲线及跨数据集 harder-findings 均未交付，submission 也明确承认这些工作被延期。另有主路径缺陷：ESM 标准化只在 postmortem 中启用，pool_campaign 的 predictor 仍无条件使用未标准化 Ridge。需完成原契约实验产物、诚实策略对比并补齐 campaign 级测试后再审。

## Evidence checked

- ha task show 与 executions/exe_e1eee94f119d4b4a1dcd748366.md：状态 submitted/in_review、iteration 0、commit a3a979adcc478eca7f8fe1f444fa9c5fc121fd5b，与 dispatch 冻结内容一致
- 逐路径 git cat-file 检查冻结提交：AAV-ESM pool metrics/events/curve、avGFP metrics、task artifacts/harder-findings.md 均 absent
- 冻结提交 clean archive 定向测试：python -m pytest tests/test_pool_campaign.py -q => 3 passed in 1.22s
- bootstrap 对照：5 members variance min/mean/max=0.0003810905/0.0030525604/0.0131031318；1 member control 全零
- 源码检查：analysis/agentic_postmortem.py 为 ESM 传 standardize=True, alpha=10；evolution/pool_campaign.py::_predictor 仅 RidgePredictor(seeds=5)
- reports/agentic_postmortem_aav_esm.json 可解析，但内容是 predictor/variance postmortem，不是四策略 pool campaign
- task_plan.md 与 AI4S-assignment.md：要求真实四策略迭代比较、失败分析及 AAV/avGFP 交付；closeout 明确将核心输出延期
