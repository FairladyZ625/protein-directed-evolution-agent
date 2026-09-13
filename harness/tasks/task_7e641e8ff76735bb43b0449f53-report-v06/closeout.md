## Summary

完成报告 v0.6：交付提交 e007fc1a8dfe30ef0052f39f8171c065525b4453，分支 codex/report-v06，worktree .worktrees/report-v06。基于本会话 v0.5 重写八章，18 页双栏 PDF/离线 HTML、12 张主图+1张附图，纳入用户新交付的 V0.8 首轮 n=1 冒烟，第二轮保持进行中。仅 reports/final-report-v0.6 文件面。

## Verification

python3 reports/final-report-v0.6/build/verify.py 通过：41 个输入快照哈希、13 图、18 页、无元素溢出、V0.8 六轮序列集合一致、残差恒等式与 GB1 实际预算。主控已看全部 18 页。证据在 reports/final-report-v0.6/evidence/verification.json、layout-check.json、visual-qa/ 与 verification.md。关联 fact F-873ED21D、F-9A20141E。

## Residual Risk

不重跑历史实验；非随机 GB1、AAV 消融与 V0.8 首轮均按真实重复数表述。V0.8 第二轮运行中，结果未填。原参考稿保存在 reference_received，基础代码锚点与新增冒烟快照分别记录。等待独立报告复核；主线集成后提供最终文件。

## Same Mechanism Elsewhere

统一核对所有图表的查询分母、重复定义、阈值与实际消费者接线；尤其区分 GB1 Critic 记录与 AAV 门禁、语言自述与送测序列、发现组合与识别上位机制。V0.7 接收约定延续相同核对规则。
