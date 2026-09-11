"""Append-only master experiment ledger for the whole project.

Every experiment run — campaign, predictor evaluation, ablation, diagnostic —
appends ONE immutable entry here recording what was run, from which code, and
what it produced (content hashes of the output artifacts). The log is never
overwritten: re-running an experiment adds a new entry, so the ledger is a
complete, tamper-evident history from project start to submission.

It reuses the T4 hash-chained EventStore, so the whole ledger can be verified
with ``EventStore(LEDGER).verify()``.
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any, Mapping

from events.store import EventStore

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "reports" / "experiment_log.jsonl"


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _git_head() -> str:
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                              capture_output=True, text=True, timeout=10).stdout.strip() or "unknown"
    except Exception:  # noqa: BLE001
        return "unknown"


def log_run(kind: str, *, command: str, params: Mapping[str, Any],
            artifacts: list[str] | None = None, summary: Mapping[str, Any] | None = None,
            ledger: Path = LEDGER) -> dict[str, Any]:
    """Append one experiment entry and return the stored event.

    kind      short label, e.g. "campaign" / "predictor_eval" / "diagnostic".
    command   the exact command (or call) that produced the result.
    params    machine-readable parameters (seed, cold_start, ...).
    artifacts repo-relative paths whose SHA-256 is recorded for provenance.
    summary   key results worth keeping inline (numbers, not full dumps).
    """
    store = EventStore(ledger)
    payload = {
        "kind": kind,
        "command": command,
        "params": dict(params),
        "git_commit": _git_head(),
        "artifacts": {a: _sha256(ROOT / a) for a in (artifacts or [])},
        "summary": dict(summary or {}),
    }
    return store.append("experiment.run", round_id=None, strategy=kind,
                        actor="experiment-runner", payload=payload)


def verify(ledger: Path = LEDGER) -> int:
    """Verify the ledger hash chain and return the entry count."""
    store = EventStore(ledger)
    store.verify()
    return sum(1 for _ in store.iter_events())
