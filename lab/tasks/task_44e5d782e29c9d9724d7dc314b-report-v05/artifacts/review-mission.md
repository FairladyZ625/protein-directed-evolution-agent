先读 /Users/lizeyu/.claude/skills/fable-gpt-worker-orchestration/references/codex-worker-handbook.md；本轮是独立只读文档交付评审，不是实现。你不是代码库中唯一执行者，不得改他人文件、不得rebase或运行全量实验。

Context: 用户已完整看过17页v0.4审阅意见，授权修成v0.5、用ImageGen新作两张英文架构图，并追加“Agent应扮演使用和验证工具的研究者，而非无工具猜fitness”的学术论述。后者已在7.6节。用户授权这是扩展报告，不以原笔试3–5页作为本轮阻塞项。父报告任务task_ee0e0b26e540664dac1e6c3f29，当前被审任务task_44e5d782e29c9d9724d7dc314b，已submitted。

Request: 独立复核当前任务提交，重点发现会影响交付的数字、引用、界限或页面明显错误。审阅对象位于 /Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/report-v05/reports/final-report-v0.5；交付提交1b9fb16b775d6adba75eed9771eb79b8753e81cd。主控已逐页视觉检查全部12页并跑verify.py。你可亲自读取PDF/HTML/MD和evidence，运行同目录build/verify.py。资料源已随交付复制；不需要重新跑实验或网络搜30篇论文。重点依据用户本轮批准的校准方向，不把旧任务/手册的“全局真峰”“微积分能力”等旧断言当权威。

Output: 先把结论、证据、具体finding与风险落到本任务artifacts/reviewer-v05.md（用ha task artifact add或doc sync）；再按当前CLI帮助调用ha task review-execution给本被审任务记录你的独立verdict。不要review-consent、complete、push或合并。不能自封主控语义裁决。

Constraints: 只读交付物，不修改PDF、图片、源码、task plan。可写你自己的评审报告及review-execution。不得修改CI或其他任务。已有源快照EOF空行用于保持哈希，不是阻塞问题。

Checkpoint: 预算约3分钟，单轮，只报实质问题，不做无限文风挑刺。如果前提错误，带证据和替代建议challenge；否则完成本轮评审并返回review-id。若运行时或权限不允许记录review，只保存报告并明确阻塞，不尝试换身份。
