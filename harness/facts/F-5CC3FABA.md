# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-5CC3FABA

- Statement: alpha 一旦 answer-agnostic 地调过,标准化伪影完全消失,且 ESM-2 在困难划分上稳定优于 one-hot——这推翻了 D2 修订裁定的依据。方法:每个(特征×划分×预处理)在训练集内做一次 80/20 留出、在 alpha∈{0.01,0.1,1,10,100,1000,10000} 上按留出 Spearman 选 alpha(不看测试集),再在测试集报分;产物 harness/reports/workflow-v1.0/gb1/predictor_alpha_sweep.json。结果(GB1,Ridge,test Spearman):random 划分 one_hot raw/std 均 0.4840(alpha* 0.01/10)、esm2 raw 0.4893(alpha* 10)/std 0.4916(alpha* 10000);hd_extrapolation 划分 one_hot raw 0.3588(alpha* 10)/std 0.3530(alpha* 10000)、esm2 raw 0.4039(alpha* 1)/std 0.4090(alpha* 10000)。两点结论:(1)固定 alpha=1 时 esm2 raw 0.4911 vs std 0.2944 的 0.197 落差、以及 hd 划分上 0.4125 vs 0.1226 的 0.290 落差,调 alpha 后分别收敛到 0.4893/0.4916 与 0.4039/0.4090,证明该落差 100% 是 alpha 与特征尺度耦合的伪影,不是标准化本身的效应;(2)在 hd_extrapolation(向远端突变体外推,正是定向进化真正要的能力)上 ESM-2 比 one-hot 高约 0.05 Spearman,两种预处理下一致;random 划分上 ESM 也略高 0.005~0.008。因此'ESM-2 未稳定优于 one-hot'不成立,dec_DFC565AC114BFC6371E684FA29 把 ESM-2 从主力表征降为对照的理由被推翻,应撤回或反向。范围限制:本结论只覆盖 Ridge 这一级,xgboost/mlp 两级未做 alpha 扫描;闭环 campaign 目前实际用 one-hot 这一事实不受影响。
- Evidence source: harness/reports/workflow-v1.0/gb1/predictor_alpha_sweep.json; harness/reports/workflow-v1.0/gb1/predictor_ladder_scaling_ablation.json; models/alpha_sweep.py
- Observed at: 2026-09-12T13:15:03.357Z
- Confidence: high
- State: standing

