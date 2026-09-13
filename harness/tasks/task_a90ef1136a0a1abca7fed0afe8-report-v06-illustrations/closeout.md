## Summary

交付提交 6ffdaa6fd78ada5e5ecbdabaa91f5a9ddaf98e80。隔离 worktree .worktrees/report-v06-polish，分支 codex/report-v06-polish；仅 reports/final-report-v0.6。正文8页、参考1页、附录14页。详细资料编入附录A–K，首页插入更新版总览，三张机制图使用内置ImageGen恢复用户喜爱的v0.5风格，保留提示词与输出哈希。

## Verification

/Users/lizeyu/miniforge/bin/python3 reports/final-report-v0.6/build/verify.py 通过：44项冻结来源、3张生图SHA、13张唯一正式图、23页无溢出、既有预算/残差断言。全部23页已渲染目视；生图标签、四残基示意、Hypothesis→Designer、Critic→Event log已复核。证据在evidence/visual-qa与verification.json。

## Residual Risk

生图为机制插画，统计图仍由真实数值生成。工具未暴露Image2.5版本选择，已向用户说明并在制作记录中如实记载。实验数值与输入不变；后续V0.8轮次仍由v0.7报告单独整合。

## Same Mechanism Elsewhere

所有补充表、完整参数扫描、运行条件、预算审计、阶数/保守性分析、数据交接与证据来源均已在PDF附录呈现。验证改为动态页数与正式引用图核验，避免旧固定18页/13文件的断言随着重排失效。
