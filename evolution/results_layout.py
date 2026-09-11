"""Single source of truth for where experiment records live.

One research cycle = one report = one folder directly under `harness/reports/`, named
`<line>-v<version>` (`agentic-v0.1`, `workflow-v1.0`, ...). The folder is self-contained:
its `report.md` plus all the data behind it (metrics / events / figures / post-mortems).
Each iteration of a method line bumps its version into a NEW folder — a past cycle's
folder is never overwritten, so the exact data behind any result stays reproducible, and
`harness/reports/experiment_log.jsonl` is the append-only spine recording the git commit
and SHA-256 of every artifact. Each folder is imported into Harness as one Report entity.

    harness/reports/
      experiment_log.jsonl          # version spine (git commit + artifact sha per run)
      <line>-v<version>/            # one cycle = one report = one entity
        report.md                   # the cycle's markdown report (the entity's document)
        <dataset>/                  # metrics / events / figures for each landscape
      cache/                        # gitignored embeddings etc.

The final multi-chapter report is authored separately (harness/final-report/), not here.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "harness" / "reports"

LEDGER = REPORTS / "experiment_log.jsonl"
CACHE = REPORTS / "cache"

# Current version of each method line. Bump on every iteration; past folders are kept.
VERSIONS = {"workflow": "v1.0", "agentic": "v0.1"}


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
