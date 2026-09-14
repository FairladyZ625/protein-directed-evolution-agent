"""Single source of truth for where experiment records live.

One research cycle = one report = one folder directly under `lab/reports/`, named
`<line>-v<version>` (`agentic-v0.1`, `workflow-v1.0`, ...). The folder is self-contained:
its `report.md` plus all the data behind it (metrics / events / figures / post-mortems).
Each iteration of a method line bumps its version into a NEW folder — a past cycle's
folder is never overwritten, so the exact data behind any result stays reproducible, and
`lab/reports/experiment_log.jsonl` is the append-only spine recording the git commit
and SHA-256 of every artifact. Each folder is imported into Harness as one Report entity.

    lab/reports/
      experiment_log.jsonl          # version spine (git commit + artifact sha per run)
      <line>-v<version>/            # one cycle = one report = one entity
        report.md                   # the cycle's markdown report (the entity's document)
        <dataset>/                  # metrics / events / figures for each landscape
      cache/                        # gitignored embeddings etc.

The final multi-chapter report is authored separately (reports/final-report-v0.7/), not here.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "lab" / "reports"

LEDGER = REPORTS / "experiment_log.jsonl"
CACHE = REPORTS / "cache"

# Current version of each method line. Bump on every iteration; past folders are kept.
#
# 三条线的语义边界(2026-09-12 定,决策见 decisions/ 的版本口径裁定):
#   workflow  —— 交付主线:数据管线 → 预测器 → 五角色 Agent → 四策略 campaign → demo。跑 GB1。
#   agentic   —— 自主 agentic researcher 线,跑 AAV。每次 agent 自主性机制的改动 bump 一版。
#   analysis  —— 只读分析线:不跑新实验,只在已测数据上做分析(突变阶数、保守性等)。
#                加数据集或加分析维度时 bump。
#
# ⚠️ agentic 线的 v0.6 与 v0.7 是**兄弟不是递进**(fact F-84AE8976):两者都从 v0.5(ccbfce6)
# 分出,v0.7 不含 v0.6 的 471536b。版本号在这里不表示线性演进,报告里不得写成单调递进的
# 消融链。三版的代码分别固定在 tag agentic-v0.5 / agentic-v0.6 / agentic-v0.7 上。
VERSIONS = {"workflow": "v1.1", "agentic": "v0.7", "analysis": "v0.1"}


def report_dir(line: str, *, version: str | None = None) -> Path:
    """The self-contained folder for one cycle's report."""
    version = version or VERSIONS[line]
    return REPORTS / f"{line}-{version}"


def run_dir(line: str, dataset: str, *, version: str | None = None, create: bool = True) -> Path:
    """Directory holding one (line, version, dataset)'s metrics / events / figures."""
    d = report_dir(line, version=version) / dataset
    if create:
        (d / "figures").mkdir(parents=True, exist_ok=True)
    return d


def figures_dir(line: str, dataset: str, *, version: str | None = None) -> Path:
    return run_dir(line, dataset, version=version) / "figures"
