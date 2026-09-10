# AI4S Directed Evolution Agent

面向蛋白质定向进化的科学智能体 —— 明度数智 AI4S 笔试项目。

## 数据
- GB1（蛋白 G B1 结构域，56aa，4 可变位点 V39/D40/G41/V54）
- 全量 149,361 变体（four_mutations_full_data.csv，Wu et al. 2016 eLife, via FLIP benchmark）
- 建模切分：FLIP two_vs_rest（train 424 / test 8,309，下采样版）
- 虚拟实验 oracle：全量表查表（组合完备 149,361/160,000）

来源声明：数据来自 FLIP benchmark (J-SNACKKB/FLIP, Dallago et al. 2021)；
GB1 原始论文 Wu et al. 2016 eLife（https://elifesciences.org/articles/16965）。

## 结构（开发中）
data/ 管线 · models/ 适应度模型 · agent/ 五角色 · knowledge/ 规则库
evolution/ DBTL 虚拟实验 · events/ 事件流内核 · app/ demo

## 运行
（随开发补全）
