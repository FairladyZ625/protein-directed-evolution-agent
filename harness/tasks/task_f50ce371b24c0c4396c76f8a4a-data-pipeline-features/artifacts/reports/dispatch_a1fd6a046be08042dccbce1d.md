Verdict：打回（`changes_requested`）

已登记独立评审：

- Task：`task_f50ce371b24c0c4396c76f8a4a`
- Execution：`exe_bb872d2f8353788765c6f695fd`
- Review：`rev_t2a`
- Harness 回执：`task-review-execution: applied`
- 当前状态：Task `active`，Execution `changes_requested`

证据：

- submitted commit 中四类交付物均存在，且相关文件至当前 HEAD 无差异。
- `closeout.md` 四段齐全。
- 三池实测为 5,000 / 50,000 / 94,361，互不相交、并集 149,361，WT 在 train。
- one-hot 缓存为 `(149361, 80)`。
- 已提交 train ESM 缓存可直接命中，输出 `(5000, 1280)`。
- `F-997BBF50` 与上述事实及 completionClaim 的较窄含义一致。
- 定向测试实际为 `6 passed in 1.38s`，无法支持“43 项单测通过”。
- 真实 ESM 提取 `use_cache=False` 尝试下载权重，因 `CERTIFICATE_VERIFY_FAILED` 失败，无法支持“权重已本地缓存”及实时提取已验证的表述。
- 阳性对照确认错误维度 backend 会触发 `ValueError`，检测器有效。

修复方向：

1. 将 43 项改为可复现的 6/6，或提供产生 43 passed 的确切命令。
2. 修正“2.6GB 权重已本地缓存”表述。
3. 提供干净评审环境下的真实 ESM-2 冒烟证据；否则明确交付边界仅为已提交批次缓存和 one-hot CPU 兜底。