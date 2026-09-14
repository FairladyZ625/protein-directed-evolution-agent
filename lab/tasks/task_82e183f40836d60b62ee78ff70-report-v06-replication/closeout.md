## Summary

交付提交 eb6157453d489e95d122b9b2771641ed099407bf，在前次独立通过的 e007fc1 上只补第6.3节 workflow-v1.2 查询5/5、强命中3/3的复现观察，明确不归因独立知识收益，补充3项冻结来源，保留根讨论纪要。分支codex/report-v06，worktree .worktrees/report-v06。

## Verification

/Users/lizeyu/miniforge/bin/python3 reports/final-report-v0.6/build/verify.py 通过：44项哈希、18页、13图、六轮V0.8集合相同及两轮GB1预算。第9页重渲染后已查看，无溢出。未重跑实验。

## Residual Risk

两次LLM运行只作分开观察，不合并效应；独立定向评审待做。前次评审的fitz依赖问题已通过明确的miniforge运行时补跑。

## Same Mechanism Elsewhere

所有LLM数字同时给实际查询分母；保留版本、超时条件与回退路径，避免绝对产量被误读为质量。
