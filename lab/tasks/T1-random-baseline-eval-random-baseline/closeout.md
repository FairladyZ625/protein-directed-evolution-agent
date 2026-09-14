# Closeout

## Summary

交付随机策略基线:`evolution/random_baseline.py` 实现三轮虚拟进化的随机提名与评估,`__main__` 可直接运行,并对外暴露 `propose_random` / `simulate` / `build_report` 供 M3 闭环复用。产出指标表 `reports/random_baseline_metrics.json`(三轮,每轮记录 round / top10_max / top10_mean / n_hit_nonzero,以及 hit_rate、累计指标与 top10 明细)与曲线图 `reports/figures/random_baseline_curve.png`(每轮 top-10 真实 fitness 曲线 + 非零命中率柱图)。

这条基线的价值不在它的分数,而在它是全部后续策略的下界参照:v0.1–v0.7 每一版的 `strong` 与 `cum_top10_max` 都是对着它读的。在 AAV 知识增强对照里它也继续服役,四策略中随机策略 `cum_top10_max=5.8015`、`strong=29`,是四条线里最低的一条,确认了排序信号确实来自模型而非运气。

交付提交:`3483c848a98ce8ef9ee65724b71e062b74b92388`(该提交已是公开主线 main 的祖先)。

## Verification

- 定向测试 `tests/test_random_baseline.py` 通过;`tests/conftest.py` 保证 `make test` 能从仓库根 import 包。
- 三轮指标与图表由同一次运行产出,曲线图的每轮 top-10 数值与 `random_baseline_metrics.json` 逐点一致。
- 依赖补齐(matplotlib、pytest 及传递依赖)单独提交 `cff717e`,与实现提交分离,便于审阅。
- 下游复用成立:M3 的四策略对照引用了本模块的 `propose_random`,`lab/reports/workflow-v1.0/` 下的 campaign 产物可追溯到这条基线。

## Residual Risk

- 单 seed。本任务只跑了一个随机种子,因此"随机策略最弱"这个结论在本任务范围内是单点观测;真正的多 seed 稳健性要到 v0.7 的 30 seed 矩阵才建立(`lab/context/research/v07-multiseed-robustness.md`)。
- 该基线的绝对数值绑定 GB1 的 149,361 提名空间口径(裁定 D1);换池口径后不可直接比较。
- 本任务早于 fact `F-885537A3`,closeout 中不含任何关于最优策略的结论——最终定性以该 fact 为准。

## Same Mechanism Elsewhere

"基线只跑单 seed 就用来支撑排序结论"这个模式在本项目反复出现,直到 v0.7 才被系统纠正:v0.4 用单条轨迹比较 LLM 与确定性基线,结果那条"确定性"基线本身还被错标了(fact `F-6D7255DE`);v0.1–v0.4 更是连每轮预算协议都不一致(fact `F-186DC664`)。通用纪律:任何"A 比 B 强"的断言,先问跑了几个 seed、两侧协议是否同一;单点观测只能写成观测,不能写成排序结论。
