# Closeout

## Summary

调研更难的定向进化基准数据集:确认 GB1 对 greedy 太易(可达全局峰),选定 AAV(FLIP,真峰 greedy 够不着)+ avGFP 作边界数据集;确立池式主动学习口径(固定已测池=候选池,策略只在排序上不同)。

## Verification

AAV/avGFP 数据源与口径写入 evolution/datasets.py loader 文档;池式口径在 workflow-v1.0/aav 与 agentic-v0.1 对照结果中验证。促成 Fact F-51F2E349。

## Residual Risk

avGFP 原始数据(ProteinGym)尚未获取,其完整跑分延到优化阶段。

## Same Mechanism Elsewhere

'greedy 可证明够不着峰'的地形选择判据,后续为 agentic 优化(找 agent 能赢的地形)复用。
