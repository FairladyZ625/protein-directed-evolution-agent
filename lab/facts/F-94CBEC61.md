# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-94CBEC61

- Statement: 交付前审计发现「数据在主线、生产代码不在主线」这一类复现洞,并逐产物核对收敛到唯一缺口:lab/reports/knowledge-ablation/ 的 1.5MB 产物早在主线,但产生它的 knowledge/ablation.py(404行)从未合入,报告第84节列的复现命令在 main 上必报 ModuleNotFoundError。同批遗漏 agent/auto_researcher.py 的 quality-aware 采集(agentic-v0.5 的生产代码)与两个测试文件。其余产物的生产脚本经 git grep 逐条确认均已在 main(mutation_order/conservation/alpha_sweep/scaling_ablation/agentic.metrics 各有对应脚本)。已合入 b78bac5,38 测试通过,阴阳对照完成。机制:worktree 里的数据被抢救进 lab/reports 提交了,代码却留在未合入分支——抢救数据和合并代码是两个动作,只做了前一个。同类风险在另外 23 个含未合入代码的分支上仍存在。
- Evidence source: commit b78bac5; lab/reports/knowledge-ablation/report.md:84-96; git diff master...t-knowledge-ablation
- Observed at: 2026-09-12T15:22:51.491Z
- Confidence: high
- State: standing

