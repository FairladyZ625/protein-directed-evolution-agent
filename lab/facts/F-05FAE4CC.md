# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-05FAE4CC

- Statement: kb 审计 runner 的阳性对照断言从不可能通过,导致 controls 段从未产出。audit.py 原第28行写 assert all(x['pass'] for x in validate_candidate(['V39I'])),把 advisory 级 R-PRIORITIZE-HISTORICAL 也当必过;该规则的 historical_good 是 validate_mutations 的函数参数(默认 None,load_rules() 无此键),validate_candidate 从不传它,故 matched 恒空、该行恒判 False,脚本每次在 controls emit 前 AssertionError 中断。这违反 knowledge/rules.yaml:53-57 自述的 every consumer filters on enforcement == gate 契约。改为只断言 gate 级规则后重跑,六项控制全过。
- Evidence source: knowledge/rules.yaml:53-57
- Observed at: 2026-09-14T10:33:05.963Z
- Confidence: high
- State: standing

