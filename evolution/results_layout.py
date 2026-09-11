"""Single source of truth for where experiment records live.

Everything an experiment produces is versioned by **method line** (`workflow`,
`agentic`, ...) and a semantic version that bumps every iteration of that line
(`agentic@v0.1`, `agentic@v0.2`, ...). A run never overwrites an earlier version: a
new version is a new directory, so the exact data behind any past result stays
reproducible forever, and the append-only ledger (`ledger/experiment_log.jsonl`)
records the git commit + SHA-256 of every artifact as the immutable version spine.

Layout (all under harness/ so Harness can import reports as first-class entities and
the public snapshot carries the whole audit trail):

    harness/reports/
      ledger/experiment_log.jsonl          # version spine (git commit + artifact sha per run)
      runs/<line>@<version>/<dataset>/      # metrics/events/figures, frozen per version
      interim/                              # markdown interim reports (ReportEntity sources)
      final/                                # the final multi-chapter report
      cache/                                # gitignored embeddings etc.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "harness" / "reports"

LEDGER = REPORTS / "ledger" / "experiment_log.jsonl"
RUNS = REPORTS / "runs"
INTERIM = REPORTS / "interim"
FINAL = REPORTS / "final"
CACHE = REPORTS / "cache"

# Current method-line versions. Bump on every iteration of a line; past dirs are kept.
VERSIONS = {"workflow": "v1.0", "agentic": "v0.1"}


def run_dir(line: str, dataset: str, *, version: str | None = None, create: bool = True) -> Path:
    """Directory holding one (line, version, dataset)'s metrics / events / figures."""
    version = version or VERSIONS[line]
    d = RUNS / f"{line}@{version}" / dataset
    if create:
        (d / "figures").mkdir(parents=True, exist_ok=True)
    return d


def figures_dir(line: str, dataset: str, *, version: str | None = None) -> Path:
    return run_dir(line, dataset, version=version) / "figures"
