# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-3F7BAF86

- Statement: AAV 真峰存在加性单步单调上升路径,原「加性单步路径不存在」断言为假。实测 f(WT)=-0.918194 → f(S17E)=3.287418 → f(S17E+V18A)=5.770209 → f(D0Q+S17E+V18A)=8.416205,每步 HD=1 且严格单调,四个构型全部在 data/aav/full_data.csv 内;缺测的 D0Q+S17E 只阻断「先 D0Q 后 S17E」这一条路由。故 greedy 实测停在 7.5301 不能归因于地形无路,也不能推出「只有直接提名 HD3 组合的方法能到」。
- Evidence source: data/aav/full_data.csv; lab/context/research/plateau-breaking-methods.md
- Observed at: 2026-09-14T14:25:21.942Z
- Confidence: high
- State: standing

