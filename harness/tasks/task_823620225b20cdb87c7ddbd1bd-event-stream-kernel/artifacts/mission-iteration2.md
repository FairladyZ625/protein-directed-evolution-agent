# 包4:事件流内核的截断尾行恢复 + 诚实边界

你在修一个**已被独立评审打回的任务**。评审全文在任务包 `reviews/` 下最新 .md,**先读它**。

## 缺口(评审做了故障恢复阳性对照,复现步骤在评审正文里)

1. **截断尾行不可恢复(合同级缺陷)。** master-plan 明写要「容忍截断尾行」。评审实测:
   写入完整的 `seq=1` 后追加不完整字节 `{"seq":2`,重启 `EventStore` 再 `append`,
   随后 `iter_events` / `verify` 抛 `JSONDecodeError`,**而不是保留完整前缀并形成可验证的新链**。
   → 在 append 之前检测并截除不完整尾行,或明确拒绝追加并给出恢复动作(选哪个你判断,
     但必须有一条确定的、被测试覆盖的行为)。
   → **必须补 restart-after-truncated-tail 回归测试**,复现评审那条路径并断言修复后的行为。
2. **回执里的并发边界是假的。** closeout 与 Execution 仍称「跨进程靠文件锁串行化」,
   而实现里**没有文件锁**;实例级 `threading.Lock` 只保证同一个 `EventStore` 实例内的线程安全,
   **不提供跨实例/跨进程保证**。
   → 把边界改写成准确表述:「同一 EventStore 实例内线程安全;跨实例/跨进程不保证」。
     这是诚实性问题,不是措辞问题——写错了就是在承诺一个不存在的保证。
3. **冻结提交与回执不一致。** 提交 pin 在 `d9a92049`,而该树的 `tests/test_events.py` 只有 6 个
   测试,**不含回执声称的 200 并发 append 回归测试**;那个测试与 `threading.Lock` 只存在于后续提交。
   → submission 要冻结到**实际欲交付且已测试**的 commit。

## 验收口径

- `pytest tests/test_events.py` 在冻结提交树上全绿,且包含新的截断尾行回归测试。
- 我会自己跑评审那条阳性对照复现路径。
- 篡改阳性对照必须仍能报 chain broken(现在是对的,不要弄坏)。

## 边界

- **只动** `events/`、`tests/test_events.py`,以及本任务的 closeout 边界表述。
- **不要动** `agent/`、`evolution/`、`models/`、`knowledge/`——都有其他 worker 在飞。
- 独立 worktree。停止点 = 点名测试绿 + commit,不 push、不发 PR。
- 发现 CEO 判断有误就带证据回报并停手。
