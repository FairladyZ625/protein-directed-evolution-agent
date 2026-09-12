Smoke checkpoint reached; stopping here pending your confirmation.

Command run:

```bash
make help && make smoke
```

Output tail:

```text
smoke         CPU-only 16-variant end-to-end campaign smoke; no source CSV
test          事件流内核测试
python -m pytest tests/test_campaign.py -q
.....                                                                    [100%]
5 passed in 2.85s
```

It is clean-clone scoped: the test reads the newly committed-intended synthetic 16-variant fixture and requires no raw GB1/AAV CSV, model download, network, or LLM credentials.

Changes are only local and uncommitted. Please confirm this qualifies as the requested clean-clone smoke, and I’ll complete the Harness report/fact/sync and local commit.