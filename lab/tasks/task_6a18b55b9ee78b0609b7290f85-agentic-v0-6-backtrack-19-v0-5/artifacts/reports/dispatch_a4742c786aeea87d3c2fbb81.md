已完成并提交本地审阅。

- 本地提交：`80c9bce79b7b34388af93b9a7ce3725b16a00ebf`
- 作者：`ZeyuLi`
- 仅相对 `origin/main` 修改：
  - `agent/auto_researcher.py`
  - `tests/test_auto_researcher_backtrack.py`
- v0.5 默认 `SYSTEM_PROMPT` 前后字节一致；SHA-256：`191ae4c…0409`
- 反向验证成功：临时切换 v0.6 默认段落后守护测试按预期失败
- 指定测试：`58 passed, 1 warning`
- `agentic-v0.6`：
  - `check_data_has_code.py`：✅
  - `check_references.py`：✅
- 已 rebase 到最新 `origin/main`
- Harness fact：`F-E34909AE`
- Harness 状态：`in_review`
- 合并证据与冲突裁决已通过 `ha doc sync --submit` 提交
- 未 push、未开 PR、未重跑或覆盖实验产物

残余风险：商业 LLM 的 AAV seed-42 实验按约束未重跑。全仓审计另有一个无关的 `pkgA-mainline-truth` 代码谱系缺口及 7 个既存失效引用，均在本任务边界之外。