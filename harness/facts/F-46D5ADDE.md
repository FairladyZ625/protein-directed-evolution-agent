# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-46D5ADDE

- Statement: 交付面重大缺陷:本地开发史与公开 GitHub 仓完全分叉,无 merge-base。本地 master HEAD=cee742a 领先 62 个提交,origin/main=be62937(2026-09-11)另有 3 个本地没有的提交,git merge-base HEAD origin/main 返回空。试题三·代码 a 要求提交 GitHub 链接,评委 clone 到的是 origin/main 的 09-11 状态——不含 v0.5/v0.6/v0.7 全部工作、不含知识增强对照、不含任何本轮修复。另:约 20 个 standard-task 的 ci 完成门在缺陷A修复后仍报 ci_missing,根因是其执行切点 commit 91d9a17 虽有成功 CI 运行(run 34608614686)但位于 closeout-baseline 分支而非 main,而 CI 观测只对 headBranch==main 的运行发布见证——这是设计正确的行为,不是缺陷,真正的阻塞是分支从未合入 main。
- Evidence source: git rev-list --left-right --count HEAD...origin/main = 62 3; git merge-base HEAD origin/main 为空; gh run list --workflow ci.yml
- Observed at: 2026-09-12T11:22:17.361Z
- Confidence: high
- State: standing

