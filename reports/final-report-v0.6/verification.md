# v0.6 验证记录

2026-09-13，在隔离 worktree codex/report-v06 完成。

- `python3 build/figures.py`：成功生成 13 张图的 PNG/SVG。
- `python3 build/build.py` 与 `node build/render.cjs`：18 页，全部图片加载成功；逐页检查段落、标题、表、图、公式元素，无正文框溢出。
- `python3 build/verify.py`：44 项源快照 SHA-256 一致；PDF 18 页均有文本；GB1 hard 实际查询 288/288、LLM 105/197 与表格一致。
- V0.8 两臂各六个残差事件、每轮 48 条；每条 residual = measured − nominated predicted；六轮序列集合 SHA-256 完全相同。提前跳转 signature_size=0；compose 事件均为纯利用 requested/effective=1.0。完整机器结果在 evidence/verification.json。
- 主控已查看渲染后的全部 18 页（evidence/visual-qa），并修复图 5 的 S17E 标签与标题重叠。图 12 已从旧预案四组描述改为实际 2×2 构型×反思设计。
- 收到的参考稿、讨论纪要与 v0.5 原稿保留。未改实验代码、未重跑实验，未填写第二轮结果。

验证覆盖报告重建、源证据完整性、关键数值和视觉排版；并不表示重新执行了历史模型训练或 campaign。

## 同轮复现补充

workflow-v1.2 两条 LLM 臂 rounds[].n_nominated 均只有一轮、值为5，强命中各3。补充源文件和原始事件后，44项快照、18页及原有验证重新通过；第9页重新渲染并查看。独立评审的默认 Python 缺少 fitz，主控用 `/Users/lizeyu/miniforge/bin/python3 build/verify.py` 补跑通过，定向复核使用相同明确运行时。
