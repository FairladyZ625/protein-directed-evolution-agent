# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-3CCEF26F

- Statement: AAV 门内(HD≤4且平均BLOSUM62≥0,9533候选)真峰 8.416(HD3)的代理预测排名:one_hot+Ridge #2418、标准化ESM-2+Ridge #2140(全池分别 #5257/#5351);pool Spearman one_hot 0.641 > ESM 0.602。即朴素 mean-pool ESM-2+线性Ridge 几乎不改善真峰可达性(仍 ≫288 预算),真瓶颈是代理模型排不动那根针而非表征信息量——故实验二的破顶希望在 ESM 语义嵌入配更强(非线性/近邻)代理,而非单纯换 one_hot→ESM。
- Evidence source: lab/reports/agentic-v0.1/aav/postmortem_esm.json
- Observed at: 2026-09-11T15:30:50.818Z
- Confidence: high
- State: standing

