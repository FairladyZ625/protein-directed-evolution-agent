# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-DBD8B878

- Statement: AAV 行数的 38,293 与 38,265 两个口径都正确,差值恰为 28。mutated_region 长度为 28 的唯一取值为 38293;再加 ^[A-Z]+$ 且无 * 过滤后为 38265,即 load_aav().df 的实际行数;差的 28 条含 * 或非纯大写字符。此前多份文档只写 38293 而未声明口径,评审据此报「与实测不一致」,实为口径未声明而非数字错误。
- Evidence source: evolution/datasets.py:76; data/aav/full_data.csv
- Observed at: 2026-09-14T14:25:22.130Z
- Confidence: high
- State: standing

