# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-7F5DEB5C

- Statement: Restarting EventStore after an unterminated JSONL tail discards that tail, appends the next contiguous event, and verifies the retained chain.
- Evidence source: tests/test_events.py::test_restart_discards_truncated_tail_before_appending
- Observed at: 2026-09-12T13:29:36.653Z
- Confidence: high
- State: standing

