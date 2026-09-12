本轮按第 3 项检查点停线，未使用未跟踪 ESM 大文件，也未提交 44MB 级产物。

- 第 2 项完成：PydanticAI `output_type=Pydantic schema`，移除裸 JSON 手工解析；失败显式记录 fallback、错误和调用数。受控 API 共 2 次：Critic 成功，响应模型 `claude-sonnet-5`；Hypothesis schema 解析失败并显式报错。
- 第 3 项阻塞：已提交 1280 维缓存仅覆盖 5000、2168、两个 2000 样本块；无 149,361 全空间覆盖。Fact：`F-54695D51`。
- 第 4 项选择：收窄为“GB1 四位点 demo”，不申领通用 WT 加分。因强制停线尚未改 `app/demo.py`。
- 点名测试：`23 passed in 45.11s`。
- 本地提交：`1bcf2e9b05f594f6323e83bd3e02d057a58ea298`，作者 ZeyuLi；未 push、未开 PR。
- `origin/main` 与当前历史无共同 merge-base；rebase 会重放 56 个无关提交并立即产生冲突，已安全中止。

明确回答：重跑后 GB1 四策略数值有变化。最显著的是 `knowledge_agent` 最终 max 从 `8.761966` 降至 `3.738620`；没有回退实现以对齐旧数字，叙事交 CEO 裁决。

完整证据见 [report.md](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/harness/reports/pkgA-mainline-truth/report.md)。下一步需决定补齐全空间 ESM 缓存，还是修订 D2 为可交付的分层表征口径。