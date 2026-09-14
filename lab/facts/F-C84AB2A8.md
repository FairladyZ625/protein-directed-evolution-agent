# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-C84AB2A8

- Statement: ESM-2 650M zero-shot 突变效应打分(掩码边际,answer-agnostic,题目点名的蛋白语言模型正解)在AAV上重测:片段上下文 门内真峰排名#3743 Spearman(pool0.356/gate0.097) 真峰z-0.43;全长VP1上下文 门内#4782 Spearman(pool0.410/gate0.154) 真峰z-1.31。全上下文整体Spearman升(0.36→0.41,证实现正确)但真峰排更后、z更负——ESM zero-shot打的是进化自然度,AAV真峰突变功能有益却进化罕见,上下文越全越看衰它。zero-shot(#3743/#4782)甚至不如embedding+监督(esm2×knn #1283)。结论:ESM两种用法(embedding+回归、zero-shot)均不破7.53;真峰对数据先验(上位效应)与进化先验(反自然)双重隐形,是地形根本难度而非方法缺陷。
- Evidence source: lab/reports/agentic-v0.3/aav/esm_zeroshot.json
- Observed at: 2026-09-11T15:54:18.896Z
- Confidence: high
- State: standing

