结论：打回（`changes_requested`）。本次无法执行 `ha` 审核/consent/complete，因为本地 daemon 未注册成功；同时交付物存在实质性缺口。

工具证据：

- `ha task show task_f50ce371b24c0c4396c76f8a4a`：真实输出为 `daemon_unavailable … workspace is not registered`。
- 尝试注册/启动 daemon：
  - `ha daemon repo register ...` → `EINVAL` / `invalid_field`
  - `ha daemon start --service` → `daemon_start_runtime_forbidden`
- 定向测试：`pytest -q tests/test_data_pipeline.py` → `6 passed in 1.53s`。
- 磁盘核验：
  - `features/cache/gb1-all-one-hot.npz` 为 `(149361, 80)`。
  - ESM 缓存存在多个分片，维度为 `(N, 1280)`，合计覆盖约 51k 条变体，并非完整 149,361 条缓存。
  - execution 文档自身记录：“Actual 650M embedding cache is not built because no local weights exist”，且 dispatch 报告明确写明真实 ESM 缓存未生成。

具体缺陷：

1. Required deliverable 声称 ESM-2 650M 缓存交付，但当前仅有分片缓存，未证明覆盖完整提名空间或任务要求的缓存交付。
2. execution 的 `Residual risks` 写“已本地缓存”，与 dispatch/progress 中“未构建真实缓存”矛盾。
3. 因 daemon 不可用，未能提交独立 review、owner consent，也未能验证 `done` 状态。

可操作修复：

- 在 daemon 恢复并注册后，重新执行 `ha task show` 获取 execution-id。
- 补齐并核验完整 ESM-2 缓存（或明确将任务降级为 one-hot 可复现、ESM 运行时提取并获得治理批准），更新 execution 的 known gaps/residual risks。
- 由独立 reviewer 提交：
  `{"verdict":"approved|changes_requested","reason":"...","evidenceChecked":[...]}`
  然后执行 `review-consent`，最后 `ha task complete`。
- 在当前条件下不应批量处理其余任务。