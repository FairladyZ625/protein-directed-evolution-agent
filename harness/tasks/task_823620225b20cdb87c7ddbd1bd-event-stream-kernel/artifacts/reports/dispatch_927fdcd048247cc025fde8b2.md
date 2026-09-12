已修复并本地提交：`e9c917c8fbfc7f14192ba5f5d50f479901d827b1` (`fix(events): recover truncated event tails`)。

- 重启时会丢弃无换行的截断尾行，保留完整前缀后连续追加。
- 新增评审复现路径回归测试；`python -m pytest -q tests/test_events.py`：`8 passed`。
- 篡改检测测试仍通过。
- closeout 已改为真实并发边界：仅同一实例线程安全，跨实例/进程不保证。
- 已记录事实：`F-7F5DEB5C`。

风险：完整但损坏的已换行记录不会自动删除，仍由 `verify()` 报 `chain broken`；这是刻意保留的审计边界。未 push、未发 PR。