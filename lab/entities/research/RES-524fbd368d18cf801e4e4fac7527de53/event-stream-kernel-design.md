# AI4S 笔试 · 精简事件流内核设计（file-by-file 实现清单）

> 定稿 2026-09-10（周四）· 对应《AI4S笔试-技术方案》§1.5 / §4.3 周六上午 ~3h 预算
> 结论先行：**「~150 行」是内核 happy path 的数字；诚实可用版 = 内核 200–240 行 + 测试 60–80 行 + demo 集成 30–40 行，总计 ~300–360 行。周六 3h 预算够核心+测试+基本集成，前提是照本文件抄，不现场发明。**

---

## 0. 依据：我核对过 Harness Anything 真实内核

本节不是类比，是我打开 `packages/kernel/src` 逐文件看过的结论（移植时保留什么、砍什么，有据可依；面试被追问也能答）：

| Harness 内核真实机制（TS） | 本笔试版 | 取舍理由 |
|---|---|---|
| `integrity/stable-hash.ts`：`stableStringify`（递归排序 key）+ sha256 | **保留**（~15 行 Python 复刻） | 内容寻址哈希的确定性全靠它；已验证实现等价 |
| `store/sqlite-event-store.ts`：`event(revision, op_id, event_json, digest, occurred_at, recorded_at)` 表 + `ledger_meta` 表 | **保留精简**：`events` 单表 + `meta` 表，去掉 `command_outcome` | 后者记录命令级幂等，单 agent 笔试不需要 |
| `writer_lease` / `lease_cas` / `lease_interval` 三表（单写者围栏） | **砍**，换成文档约定"单进程单写者" | 我们是单进程 loop，多写者围栏是给自己挖坑 |
| `PRAGMA busy_timeout; journal_mode=WAL; synchronous=FULL` | **保留** WAL + busy_timeout；synchronous 用默认 FULL 之于 jsonl 侧由显式 fsync 承担 | Streamlit 读 + campaign 写跨进程，WAL 必开 |
| `projection/rebuildable-task-projection-*.ts`（~1600 行：投影可重建运行时） | **压扁成 1 个 `rebuild()` + SQL 视图** | "投影是衍生物，删库可重建"这个**理念**保留，实现 30 倍精简 |
| 事件形态迁移 / generation 切换 | **砍** | 4 天工期不存在 schema 演进问题 |

---

## 1. 「150 行」现实吗 —— 逐模块诚实估算

| 模块 | 文件 | 乐观（裸 happy path） | 诚实（含 docstring/异常路径） | 说明 |
|---|---|---|---|---|
| 事件存储 | `events/store.py` | 60 | **90–110** | append(链式哈希+fsync) / iterate / verify / 容忍截断尾行。砍 verify 可省 ~20 行，但 verify 是面试演示点，不砍 |
| SQLite 投影 | `events/project.py` | 35 | **50–60** | 建表(2张)+视图(2个)+rebuild 全量回填+只读连接。json_extract 单表+视图，不做三实体表 |
| 回放 | `events/replay.py` | 30 | **50–60** | timeline 过滤+render_text+argparse CLI（--round/--strategy/--json） |
| 包导出 | `events/__init__.py` | 3 | 5 | |
| 测试 | `tests/test_events.py` | 40 | **60–80** | 5 组断言（见 §5），pytest 风格 |
| demo 集成 | `app/` 内一节 | 25 | 30–40 | expander 时间线 + dataframe 提案表 + 缓存读取 |

**汇总口径**：

- **内核三件套（store+project+replay）**：乐观 ~130 行 / 诚实 **190–230 行**
- **内核+测试**：诚实 **250–310 行**
- **全套（含 demo 集成）**：**280–350 行**

所以：技术方案里写"~150 行"要改成 **"~200 行内核 / 全套 ~300 行"**——报告里如实写 200 行反而更可信（150 像拍脑袋，300 带测试像工程师）。

**写入路径已实测验证**（本机 Python 3.11.14 + sqlite 3.53.4）：`json_extract` 可用；WAL 可开；fsync 见 §3.3。

---

## 2. 具体设计

### 2.1 事件 schema（单行 JSON，append 到 `events.jsonl`）

```json
{
  "seq": 42,
  "ts": "2026-09-12T14:03:21.487Z",
  "event_type": "proposal.validated",
  "round_id": 2,
  "strategy": "knowledge_agent",
  "actor": "mutation_designer",
  "payload": {"variant": "V39I/D40N", "score": 0.83, "rule_refs": ["R3"]},
  "prev_hash": "ab12…",
  "hash": "cd34…"
}
```

设计规则：

- **`seq` 从 1 递增**，文件行号即序号，读侧校验"第 n 行 seq==n"（防重排/防删行，比纯哈希链多一层数字级防篡改，0 成本）。
- **`ts` 强制 UTC ISO8601 带 `Z`**。生成：`datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z")`。禁止 naive local time（排序会错，面试官一眼看穿）。
- **`event_type` 枚举**（与主方案 §1.5 一致）：`round.started / agent.thought / tool.called / tool.result / proposal.validated / proposal.rejected / oracle.queried / decision.made / round.completed`。
- `payload` 是自由 dict，但**关键事件有必备键**（proposal 类必有 `variant`；decision 必有 `chose/rejected/reasons`），测试里断言（§5.5）。
- **链式哈希：要。** 计算方式：`hash = sha256(canonical({seq, ts, event_type, round_id, strategy, actor, payload, prev_hash}))`，canonical = 递归排序 key 的紧凑 JSON（`ensure_ascii=False, separators=(",",":")`）——等价复刻内核 `stableStringify`。
  - **取舍（报告照抄这段）**：链式哈希给的是**防篡改可检测（tamper-evident），不是防篡改（tamper-proof）**——攻击者可重算整条链。真防篡改需要链头签名/外部公证；笔试版把**链头哈希写进 git commit message**（"campaign@head=cd34…"），git 的不可变性当公证。面试话术："审计链的可信度上限取决于链头锚定在哪，我锚在 git；医药生产会锚在时间戳服务。"
- **哈希冻结提案**（主方案"牌 1"）不单独做机制：`proposal.validated` 事件的 `hash` **就是**提案内容哈希——每条提名落流即冻结，零额外代码。

### 2.2 SQLite 投影：单表 + 视图（明确否决三实体表）

```sql
CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY, value TEXT NOT NULL);          -- schema_version / head_hash / built_at
CREATE TABLE IF NOT EXISTS events (
  seq INTEGER PRIMARY KEY, ts TEXT NOT NULL, event_type TEXT NOT NULL,
  round_id INTEGER, strategy TEXT, actor TEXT,
  payload_json TEXT NOT NULL, prev_hash TEXT, hash TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_events_type_round ON events(event_type, round_id);

-- 视图即"投影"：查询第2轮为什么推荐 39V→I，一句 SQL
CREATE VIEW IF NOT EXISTS v_proposals AS
  SELECT seq, round_id, strategy, actor, ts,
         json_extract(payload_json,'$.variant')  AS variant,
         json_extract(payload_json,'$.score')    AS score,
         json_extract(payload_json,'$.rule_refs')AS rule_refs, hash
  FROM events WHERE event_type IN ('proposal.validated','proposal.rejected');
CREATE VIEW IF NOT EXISTS v_decisions AS
  SELECT seq, round_id, strategy, ts, payload_json, hash
  FROM events WHERE event_type = 'decision.made';
```

- **为什么否决 events/proposals/decisions 三表**：三表 = 每表一套回填+同步逻辑（行数×2.5，还引入"投影与流不一致"这个自找的 bug 面）。单表+视图在 2.4k 事件量级查询即时完成，且**投影"可丢弃可重建"的故事更纯粹**：删掉 .db，`rebuild()` 一遍 jsonl 即恢复——这本身就是内核 `rebuildable-*` 的理念复刻。
- `rebuild()` = 逐行读 jsonl → `INSERT OR REPLACE` → 写 `meta.head_hash`。幂等，跑 N 次结果相同（测试断言）。
- 连接姿势：**写侧**（campaign 进程）`journal_mode=WAL`（一次性）+ `busy_timeout=5000`；**读侧**（Streamlit）只读 URI `sqlite:file:...?mode=ro`，杜绝 demo 里误写。

### 2.3 replay 输出形态：文本时间线为主，JSON 为机读接口

- `render_text()`：按轮分组的时间线，`[14:03:21] #42 proposal.validated knowledge_agent ▸ V39I/D40N score=0.83 refs=[R3]`——终端可跑、README 可贴、demo 可嵌，一种输出三处用。
- `--json`：吐结构化数组给 Streamlit / 报告脚本复用。**不做 HTML 渲染**（Streamlit 已是 HTML，重复）。
- CLI：`python -m events.replay --round 2 --strategy knowledge_agent`；不带参数 = 全量摘要。

### 2.4 Streamlit 集成（拒绝自定义组件）

- `st.expander(f"Round {r} · {strategy}")` 内逐事件渲染文本行（`st.code(text)` 保等宽）；`st.dataframe(v_proposals 查询结果)` 展示提案表，**点击行无法联动到事件**——够用，不追求。
- 回放交互降级方案：`st.slider("回放位置", 0, len(timeline))` 切片显示前 k 步——10 行实现"逐步回放"效果，面试演示点保住。
- **缓存（rerun 语义坑，见 §3.6）**：`@st.cache_data` 包 `load_events()`，cache key 用 `(path, mtime_ns, size)`——jsonl 是 append-only，文件不变则缓存命中；append 后 mtime/size 变，自动失效。

---

## 3. 坑清单（每条给处刑方式）

1. **jsonl 并发写**：单进程单 agent loop = 非问题；Streamlit 只读。**不做文件锁**（内核用 writer_lease 三张表解决的事，我用"架构上只允许一个写进程"解决，报告里明说这是有意识的取舍）。POSIX `O_APPEND` 单 write ≤4096B 原子，我们事件行常超 4K，**不依赖它**，靠单写者假设。
2. **SQLite WAL**：Streamlit（读）与 campaign（写）是两个进程，不开 WAL 会 `database is locked`。写进程启动时 `PRAGMA journal_mode=WAL` 一次；两个连接都设 `busy_timeout`。**WAL 产生 -wal/-shm 文件，加入 .gitignore**（否则仓库里出现二进制垃圾）。
3. **fsync 性能：实测不是问题**。本机实测 2000 次 append+flush+fsync = **0.09s（0.05ms/条）**；整个 campaign 预估 ~2400 事件 → fsync 总开销 **~0.12s**。结论：**逐事件 fsync，一步不省**——成本为零的审计卖点。
4. **哈希链的意义边界**：防篡改可检测≠防篡改（§2.1）。演示价值真实存在：现场用文本编辑器改一个字符 → `verify()` 报 `chain broken at seq=k`——这个 15 秒演示比一页报告有说服力。**报告里必须诚实写边界**，否则面试官反问"重算全链怎么办"就塌了（答：链头锚定 git commit）。
5. **datetime 时区**：一律 UTC 带 Z（§2.1）。两处必炸点：LLM 返回的时间字符串（不信任，自己生成 ts）；报告里"冻结时间"展示本地时区（渲染层转换，存储层不动）。
6. **Streamlit rerun**：每个控件交互整脚本重跑。①**严禁在模块顶层 append 事件**（rerun 一次写一次，事件流被 rerun 污染成垃圾场）——写入只发生在 campaign 进程，app 永远只读；②读取必须缓存（§2.4），否则每次拖 slider 全量读文件；③回放游标放 `st.session_state`。
7. **canonical JSON 细节**：`json.dumps` 默认 `ensure_ascii=True` + 不排序 → 同一 payload 两次算出不同哈希。必须 `sort_keys=True, ensure_ascii=False, separators=(",",":")`，浮点数先 `round()`（score 保留 6 位，防浮点重渲染漂移）。
8. **崩溃截断尾行**：写侧单次 `write(line+"\n")`+flush+fsync，行内不会半截；但进程被杀仍可能留无换行尾行 → 读侧容忍：最后一行无 `\n` 则跳过并 warning，不 raise（内核同款 fail-soft 策略）。
9. **sqlite3 隐式事务**：Python 默认 `isolation_level=''` 会悄悄开事务。rebuild 里显式 `isolation_level=None`（autocommit）+ 手动 `BEGIN/COMMIT` 包批量插入，避免"写了但投影读不到"的假象。
10. **events/ 样例要入库**：主方案 §2 已定 `events/` 目录进 git——**别顺手 gitignore**（.gitignore 只排 `*.db`、`*-wal`、`*-shm`）；样例 jsonl 是给面试官直接翻看的展品。

---

## 4. 周六 3h 预算判定与 MVP 边界

**判定：3h 够，但只够"照单施工"，不够"现场设计"。** 分箱：

| 时段 | 产出 | 验收 |
|---|---|---|
| 0:00–0:50 | `store.py` + `test_events.py` 前 3 个测试 | 追加→读回全等；tamper 被 verify 抓到 |
| 0:50–1:40 | `project.py`（建表/视图/rebuild） | rebuild 后行数/seq/head_hash == jsonl |
| 1:40–2:20 | `replay.py` + CLI | `--round 2` 时间线输出；同输入两次输出 diff 为空 |
| 2:20–3:00 | `loop.py` 埋点接入 + Streamlit 时间线节 | 单轮 campaign 事件落流可在 demo 页展开 |

风险缓冲：如果 0:50 检查点 store 还没过测试 → **立即触发 MVP 砍单**，不恋战。

**MVP 边界（21:00 检查点未达 M-Sat 时执行）**：

- **MVP = store.py 完整版（含 verify）+ replay.py 文本版 + loop 埋点。约 150–170 行。** SQLite 投影整体砍掉——查询需求降级为 `replay --json | jq`（README 里给三条 jq 示例照常能查"第2轮为什么推荐 X"）。
- 砍单顺序（从先砍到后砍）：①SQLite 投影（-60 行）→ ②Streamlit 时间线组件（用静态 `st.code(open(replay输出))` 替代）→ ③CLI 参数化（写死默认全量）→ ④测试缩到 3 个断言（round-trip / tamper / replay 确定性）。
- **永不砍**（与主方案 §4.5 对齐）：append-only 落流、链式哈希+verify、按轮文本回放——这三个是"可回放"卖点的最小闭包，砍掉任何一个，差异化叙事就没了。

---

## 5. 验证方式（写进报告的证据链）

1. **写读全等**：随机 200 事件（含中文/嵌套 dict/空串）append → iterate → `assert deep_equal`。证明流无损。
2. **链完整性**：①完好文件 `verify() → ok`，返回链头哈希；②对第 k 行改 1 字节 → `verify()` 精确报 `chain broken at seq=k`；③删掉第 k 行 → `seq gap at k`。**截图进报告**（失败案例分析章节的信任基石）。
3. **投影一致性（= 回放重建状态 == 最终状态）**：campaign 跑完 → `rebuild()` → 断言 `COUNT(*)==len(jsonl)`、`MAX(seq)==流尾 seq`、`meta.head_hash==流尾事件.hash`。**每次 campaign 结束自动跑**（loop.py 里 campaign 收尾钩子调一次），报告写"投影与事件流每轮自动对账"。
4. **回放确定性**：同 `--round --strategy` 跑两次，输出按字节 diff 为空。
5. **语义不变量**（每轮结构完整性）：每 `round.started` 恰配一个 `round.completed`；每个 `proposal.validated` 的 variant 在同轮 `oracle.queried` 中出现；`decision.made.chose` ⊆ 该轮 validated 集合。这是"状态机健康"级的检查，~15 行测试。
6. **演示动线**：README 放 tamper→verify 报错的 asciinema/gif；现场版本 = 终端里 `sed -i '' 's/0.83/0.99/'` 改一行 → verify 立刻红。15 秒，记忆点拉满。

---

## 6. File-by-file 实现清单（照此施工）

仓库内落点：`ai4s-directed-evolution-agent/events/`

| # | 文件 | 职责 | 预估行数 | 核心签名 |
|---|---|---|---|---|
| 1 | `events/__init__.py` | 导出公共 API | 5 | `from .store import EventStore; from .replay import replay_round` |
| 2 | `events/store.py` | append-only 事件流：追加+链哈希+fsync、迭代读、链验证、容忍截断尾行 | 90–110 | `class EventStore:`<br>`· __init__(self, path: Path)`<br>`· append(self, event_type: str, payload: dict, *, round_id: int, actor: str, strategy: str) -> dict`<br>`· iterate(self) -> Iterator[dict]`（跳过无换行尾行）<br>`· verify(self) -> VerifyReport`（`ok/first_bad_seq/reason/head_hash`）<br>`· head_hash(self) -> str \| None`（property）<br>模块级 `canonical(obj) -> str`、`content_hash(canonical_str) -> str` |
| 3 | `events/project.py` | SQLite 投影：建表+视图、全量 rebuild、只读连接 | 50–60 | `SCHEMA_SQL: str`（§2.2 全文）<br>`def rebuild(jsonl_path: Path, db_path: Path) -> int`（返回行数，幂等）<br>`def connect_ro(db_path: Path) -> sqlite3.Connection`（URI mode=ro）<br>`def connect_rw(db_path: Path) -> sqlite3.Connection`（WAL+busy_timeout=5000+isolation_level=None） |
| 4 | `events/replay.py` | 按轮/策略过滤→时间线条目→文本渲染；CLI 入口 | 50–60 | `def timeline(events: Iterable[dict], *, round_id: int \| None = None, strategy: str \| None = None) -> list[dict]`<br>`def render_text(entries: list[dict]) -> str`<br>`def main() -> None`（argparse：`--round --strategy --json --db`） |
| 5 | `tests/test_events.py` | §5 的 1/2/3/4/5 断言（pytest，tmp_path fixture） | 60–80 | `test_roundtrip / test_verify_ok / test_tamper_detected / test_rebuild_consistent / test_replay_deterministic / test_round_invariants` |
| 6 | `app/`（已有 demo 页内新增一节） | 事件时间线展示：缓存读取+expander+dataframe+slider 步进 | 30–40 | `@st.cache_data` `def load_events(path, mtime_ns, size)`；`render_timeline_section(round_id)` |
| 7 | `agent/loop.py`（埋点，非新文件） | 每步 `store.append(...)`；campaign 收尾调 `rebuild()`+对账断言 | +15–20 | 感知→假设→评估→批评→提名各阶段各 1 次 append；`decision.made` 记 chose/rejected/reasons |

**行数合计**：内核 195–230 / +测试 255–310 / +demo+埋点 **285–350**。

**施工顺序 = 清单序号顺序**，#2 完成前不开 #3（store 的 canonical/hash 被 project 和 replay 复用）。

---

## 7. 给主方案的三处修订建议

1. §1.5 "~150 行" → 改 "**~200 行内核 + 测试，全套 ~300 行**"（更诚实也更可信）。
2. §2 仓库结构 `events/` 条目补一句：*.db/-wal/-shm 进 .gitignore，**样例 jsonl 必须入库**。
3. §4.3 周六上午条目追加 MVP 触发线：**0:50 store 未过测试 → 砍 SQLite 投影**（§4 本文件）。
