## Summary

交付 commit d2e3e767665c02d9eced8202f17973b4e6e7a3e2（task-owned commits b661c0d、d2e3e76；base ccbfce6），作者 ZeyuLi。改动仅 agent/auto_researcher.py 与 tests/test_auto_researcher_explore.py；未 push/PR/merge。

实现新增测量停滞检测、UCB/diverse/uncertainty/spread 批次、FULL 自主比例与 SEMI 强制阶段，并保留 C+A。12组 AAV 同288预算实测：mean0/3、alternating1/3、FULL0/3、SEMI1/3 达峰。SEMI 打平朴素交替的达峰次数，没有证明更稳健或 LLM 探索更优。交替seed42在R4均值排名1384命中，SEMI seed0在R6均值排名124命中。FULL/SEMI maxima 按seed42/0/7分别为7.829/6.5309/7.829与7.829/8.4162/7.829。

## Verification

- OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=. .venv/bin/python -m pytest tests/test_auto_researcher_explore.py tests/test_auto_researcher_compose.py tests/test_auto_researcher_gate.py tests/test_epistasis_surrogate.py -q：31 passed in 3.58s（tests-final.log）。
- run_matrix.py / run_single.py：12个正式结果均288/288、六批各48；summarize.py exit0，验证每批候选与预先冻结预测一致、跨批无重复、全事件链完整、SEMI 阶段与轨迹一致。真实API model id=claude-sonnet-5；tool/round errors=0，harness代测/补批共4次（FULL seed0 R5代测暂存批；FULL seed0 R6、seed42 R4和SEMI seed7 R6由harness自行选样），非fallback运行。
- AAV cold CV=0.905917215，shuffle CV=0.013438177；cold peak mean rank426，非合同2758。原始数据与三版实跑/最终源码hash见manifest和源码快照。
- 三条初始SEMI非合规预运行保留于pilot-semi-*；修正的是停滞前必须纯利用的合同违例，没有改探索分数、门禁、oracle、seed或patience。
- Facts：F-AFE22C14、F-B5AE4DDE。报告、matrix-summary、12组metrics/events、预运行、runner stdout、对比图和源码快照均位于本任务artifacts/reports/agentic-v0.7/，通过ha task artifact add及ha doc sync --submit --task提交。
- git diff --check exit0；git status --short为空。未执行全量suite/CI；独立review-execution与CEO consent待办，未自行批准或完成任务。

## Residual Risk

仅一个AAV数据集/三个采集seed，LLM随机性未控；diverse预览消耗共享RNG，不能把同seed视作同随机候选流。三个bootstrap方差不等于尾部校准，CV参与alpha选择。网关背后的物理模型身份、GB1/ESM/v0.6与全量CI均unverified。

交付前fetch成功，origin/main=be62937a8b7a7bc3e6e9e7d67fba33e67e8f3bc2，仓库非shallow，merge-base HEAD origin/main exit1：无法安全rebase，保留指定v0.5基线，请CEO裁定历史整合。

本文件是允许写范围内准备的收口收据。canonical repository root 按dispatch保持只读，未直接替换其任务closeout.md投影。当前CLI已取消submission JSON packet，要求canonical closeout正文后再submit；因此该生命周期步骤需CEO应用本收据/处理权限与独立审核。文档收据已通过任务绑定doc sync发布，不能把这等同于task complete。

## Same Mechanism Elsewhere

机制：聚合验证分数不能保证尾部排序，固定利用下限又可能在已测轨迹停滞后阻止必要的采集切换；混用历史已有最优与本次新增最优还会制造错误的停滞叙事。

使用git grep -n -E 'cum_top10_max|best_so_far|_enforce_exploit_floor|val_spearman' -- agent/auto_researcher.py evolution/pool_campaign.py models/train_ladder.py；输出见mechanism-search.log。发现auto_researcher的legacy比例下限仍保留供旧模式使用，v0.7显式分离；pool_campaign已有新增累计统计，train_ladder暴露整体CV。只读检查这些调用点，未修改其他产品面；没有扩展成全仓搜索。
