结论：T4 事件流内核已完成并本地提交。

实现内容：

- `events/store.py`：append-only JSONL、链式 SHA-256、`flush + fsync`、`verify()` 篡改检测、链头哈希。
- `events/project.py`：SQLite 单表与 `v_proposals` 视图，可幂等 rebuild，并提供只读连接。
- `events/replay.py`：按 `--round` / `--strategy` 过滤并输出文本时间线。
- `tests/test_events.py`：6 项定向测试，覆盖 fsync、链校验、篡改阳性对照、投影、只读和 CLI。

工具证据：

- `pytest -q tests/test_events.py`：`6 passed`
- 篡改验证：`chain broken at seq=1`
- 正常链验证：`verify() -> None`
- Fact：`F-3379A413`
- Commit：`d9a9204 feat: add auditable event stream kernel`

工作树干净，未 push/创建 PR。