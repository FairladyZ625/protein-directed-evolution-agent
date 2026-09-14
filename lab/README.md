# `lab/` — 冻结的研究台账文档树

本目录是 2026-09-14 从嵌套的 harness 台账仓中搬出的**文档树快照**。它现在是本仓库里的**普通文件**：
不再由任何工具驱动，也不再有机器写入者。报告与看板引用的实验产物、研究文稿、任务包、事实与决策都在这里。

## 目录构成

| 子目录 | 内容 |
|---|---|
| `reports/` | 实验产物树，每个研究周期一个自包含文件夹（`workflow-v1.x`、`agentic-v0.x`、`v09-contract`、`analysis-v0.1` 等）；`REPORT-HANDOFF.md` 是给报告作者的修订摘要；`experiment_log.jsonl` 是追加式实验台账 |
| `context/` | 研究文稿与架构文档（试题原文、领域调研、技术方案、平台期破局、多种子稳健性等） |
| `tasks/` | 78 个任务包：`task_plan.md`、`closeout.md`、执行记录、评审记录、`artifacts/` 产物 |
| `facts/` | 163 条追加式事实记录（`F-XXXXXXXX.md`） |
| `decisions/` | 9 个决策包 |
| `agents/` | 10 个 agent 声明（`de-reviewer`、`de-research`、`de-ml` 等） |
| `governance/` | 治理标准与 walls 配置 |
| `entities/` | 登记的报告与研究实体（图表、报告正文、manifest） |
| `events/`、`milestones/`、`schedules/` | 事件流投影、里程碑、排期 |

## 未一起搬入的东西，以及依据

| 未搬 | 体积 | 依据（均为实测） |
|---|---|---|
| 台账仓自身的 `.git` | 229M | 无 remote、1968 个提交（2026-09-10 → 09-14）。已冷存为 `~/harness-ledger-20260914.tgz`（240M，HEAD `ac0e139`）。其中截至 09-13 的部分另存于伴生仓 `protein-directed-evolution-agent-harness`（`main` 1,458 个提交） |
| `final-report/report.html` + `report.pdf` | 18M | 与 `reports/final-report-v0.7/scientific_report_v0.7_two_column.{html,pdf}` **md5 完全相同**（`faae21a2…` / `c21e3354…`），属重复件 |
| `entities/reports/REP-637f…/gb1/campaign_{easy,hard,sparse,llm}.events.jsonl` | 33M | 与 `lab/reports/workflow-v1.0/gb1/campaign_*.events.jsonl` **md5 完全相同**，删除前已逐个复核副本存在 |
| `.harness/` | 0B | daemon 本地运行态，上游明令不得提交 |

`lab/reports/cache/`（173M，`esm_aav.npz`）**在版本控制之外**：它可由 `evolution/datasets.py` 重新生成。

## 路径重写

搬迁把 3,687 处 `harness/<目录>/` 改写为 `lab/<目录>/`，覆盖 628 个文件；另外补齐了两类前缀替换漏掉的形态：
`ROOT / "harness" / "reports"` 这种 Path 分段拼接，以及 `ROOT / "harness/reports"` 这种不带尾斜杠的字符串。

**故意未改动**的三类（实测计数在搬迁前后完全一致）：`.harness/…`（153 处，daemon 本地态）、
`harness/harness.yaml`（15 处，台账仓配置，重建后路径依旧成立）、
`~/Projects/coding-agent-harness/harness-anything`（5 处，另一个仓库）。

历史文档里出现的 `.harness/runtime/…` 等派工运行态路径不再存在，它们是当时的真实记录，未作改写。

## 哈希台账的三类账（重要，勿误记）

7 个哈希台账共 **263 条**记录（`app/timeline_evidence/provenance.json`、v0.3/v0.5/v0.6/v0.7 的
`evidence/sources.json`、v0.3 的 `evidence/delivery-manifest.json`、`research/rsi-cybernetic/source-manifest.json`）：

| 类别 | 条数 | 说明 |
|---|---|---|
| 记录值与当前内容一致 | 197 | — |
| **仅因本次路径重定位而变** | **20** | 内容实质未变。记录值可精确复现，见下方命令 |
| 在本次搬迁之前就已对不上 | 44 | 其中 18 条所在文件本次也被改过（记录在更早就过期了），26 条所在文件本次完全未碰。**未作改动**：这些是历史漂移，把它们改成"看起来对"等于造假 |
| 指向不存在的文件 | 2 | `lab/reports/workflow-v1.2/gb1/campaign_llm.events.jsonl`——该目录下只有 `.gz`，无未压缩版本 |

**冻结版本的证据台账（`sources.json`、`delivery-manifest.json`）一律未被改写**：它们记录的是"本版报告由哪些输入、
在什么哈希下构建"，改成搬迁后的值等于声称 v0.3 是用含 `lab/` 的内容构建的，而 `lab/` 当时并不存在。

那 20 条的记录值可这样独立复核——把文件内容里的 `lab/` 反向替换回 `harness/`，哈希即与记录值精确相等：

```bash
python3 - <<'PY'
import hashlib, re, sys, pathlib
DIRS = 'reports|context|tasks|facts|decisions|agents|governance|entities|milestones|schedules'
b = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'lab/context/research/v07-multiseed-robustness.md').read_bytes()
s = b.decode('utf-8', 'surrogateescape')
s = re.sub(r'(?<!\.)lab/(' + DIRS + r')', r'harness/\1', s)
s = re.sub(r'"lab"(\s*/\s*)"reports"', r'"harness"\1"reports"', s)
print(hashlib.sha256(s.encode('utf-8', 'surrogateescape')).hexdigest())
PY
```

唯一被更新了记录值的台账是 `app/timeline_evidence/provenance.json` 的 2 条 whitepaper 记录：它由
`app/build_timeline_snapshot.py` 生成（而非人工维护），并由 `tests/test_timeline.py` 强制校验字节一致。
该 bundle 内的两份 whitepaper 与上游 `reports/theoretical_foundations/` 的对应文件当前**字节完全相同**，
即记录值只是旧了；填入的值正是生成器会算出的值。该生成器本身此刻跑不起来（它需要
`.worktrees/t-v05`、`t-v07`，而那些旧 worktree 里只有当年的 `harness/`、没有 `lab/`）。
