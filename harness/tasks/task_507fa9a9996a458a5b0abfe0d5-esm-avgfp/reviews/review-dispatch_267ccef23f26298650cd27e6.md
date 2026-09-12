# Review review-dispatch_267ccef23f26298650cd27e6

Managed by `ha task review-execution`; legacy `review.md` is not authoritative.

- Task: task_507fa9a9996a458a5b0abfe0d5
- Execution: exe_e1c708231c47d10d40ad509581
- Verdict: changes_requested
- Commit: fe5a1a5aa7140a8266a6d99b007a298800856c50
- Iteration: 1
- Content digest: sha256:41cd823e06a2683ae10be5b84f62291aa04fe19f69b21c92501bb4b72edfd4c3
- Submission digest: sha256:06178989262280a789032aca4560be99113fb1460080e6127c7a820ba398eda0
- Reviewed at: 2026-09-12T13:10:10.141Z
- Consent: pending
- Consent actor: pending
- Consent source: pending

## Reason

打回：iteration 1 的冻结提交 fe5a1a5 仍只交付 bootstrap/loader/ESM 输入守卫。任务契约要求的 AAV-ESM 与 avGFP 四策略 metrics、事件流、曲线以及跨数据集数值结论均未完成；closeout 也明确将这些核心目标延期。此前指出的 campaign 主路径 ESM 配置与 campaign 级语义测试缺口仍未修复。外部数据或模型下载受阻应按 checkpoint 报 blocker，而不能把未完成实验提交为完成。

## Evidence checked

- ha task show/managed execution：iteration 1 submitted，冻结 commit fe5a1a5aa7140a8266a6d99b007a298800856c50；closeout 明示 avGFP 原始 CSV、AAV-ESM 完整跑分和跨数据集对比未完成
- git cat-file 冻结提交逐路径检查：reports/pool_metrics_aav_esm2.json、pool_events_aav_esm2.jsonl、AAV 曲线及 avgfp metrics 均 absent；契约指定的 task artifacts/harder-findings.md absent
- 冻结提交 artifacts/harder-findings.md 自述 AAV ESM 下载中断、avGFP 未运行，且没有 AAV ESM/avGFP agent-vs-greedy 证据
- clean git archive 定向测试：python -m pytest tests/test_pool_campaign.py -q => 3 passed in 1.35s
- bootstrap 阳性/阴性对照：5 members variance min/mean/max=0.0003810905/0.0030525604/0.0131031318；1 member control=0/0/0
- 源码检查：evolution/pool_campaign.py::_predictor 仍固定 RidgePredictor(seeds=5)，未按 ESM 特征启用已提出的标准化/配置；测试仅覆盖 bootstrap、WT guard、ESM 全长输入，未覆盖四策略同池、random control、多轮复现与 campaign 事件方差
- git lineage：fe5a1a5 是 master 祖先但不等于 master HEAD；相较 iteration 0 冻结提交缺少多项后来文件，‘已合并 master’不能替代本 execution 的冻结交付完整性
