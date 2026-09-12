已完成任务并在本地提交：

- 新增 [agent/auto_researcher.py](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-agentic/agent/auto_researcher.py)
- 实现六个工具：数据分析、预测、候选池选择、实验测试、最优追踪、知识校验
- 严格预算扣减，候选仅来自外推池
- 事件流记录每次工具调用及轮次状态
- 降级路径为确定性的 exploit/explore 交替策略
- 已通过 `py_compile`
- 已记录 Harness fact：`F-1C5E5DE0`
- 本地 commit：`aaacbee feat: add autonomous autoresearch agent`

尚未运行 AAV 完整数据任务测试，因当前 worktree 缺少对应数据与点名测试文件。