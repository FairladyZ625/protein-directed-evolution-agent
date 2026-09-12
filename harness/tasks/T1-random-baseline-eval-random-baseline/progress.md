# Progress

## Entries

### 2026-09-10T14:48:53.414Z

入口条件核验通过：four_mutations_full_data.csv 149,361 行，Fitness 0 缺失，Variants 全部为 4 位 20aa 合法组合且唯一，WT VDGV=1.0；HD 分层 {0:1,1:76,2:2091,3:26019,4:121174}；fitness>0.01 占 23.13%；全表 top-1%(1,494 条) 均值 3.304、阈值 2.153；缺失组合 10,639/160,000。.venv 缺 matplotlib/pytest。

### 2026-09-10T14:57:36.235Z

实现并提交 3483c84（依赖 cff717e）：make baseline 退出 0；三轮 top10_max/top10_mean/n_hit_nonzero = R1 1.612/0.475/22、R2 2.374/0.814/26、R3 1.456/0.439/26；阴性对照 PASS（0.814 < top-1% 均值 3.304）；make test 5 passed；指标 JSON 在 .venv(numpy2.5/pandas3.0) 与 miniforge(numpy1.26/pandas2.3) 下逐字节一致。
Evidence: file:reports/random_baseline_metrics.json:三轮指标 JSON（seed=42，rounds 3）
Evidence: file:reports/figures/random_baseline_curve.png:top-10 曲线 + 非零命中率图
Evidence: file:tests/test_random_baseline.py:5 项测试全过

