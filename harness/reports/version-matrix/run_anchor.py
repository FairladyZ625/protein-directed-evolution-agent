"""Reproduce the historical v0.4 deterministic alternation anchor."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent.auto_researcher import run_autoresearch
from events.store import EventStore
from evolution.datasets import load


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=False)
    events_path = args.out_dir / "events.jsonl"
    store = EventStore(events_path)
    report = run_autoresearch(
        load("aav", "one_hot"),
        budget=48,
        n_rounds=6,
        seed=args.seed,
        event_store=store,
        llm=False,
        guardrail=True,
        max_hd=4,
        blosum_min=0.0,
        surrogate="epistasis",
    )
    store.verify()
    (args.out_dir / "metrics.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    counts = [round_["n_nominated"] for round_ in report["rounds"]]
    summary = {
        "seed": args.seed,
        "round_counts": counts,
        "budget_spent": report["budget_spent"],
        "cum_top10_max": report["summary"]["final_cum_top10_max"],
        "strong": report["summary"]["final_cum_n_strong"],
        "event_count": sum(1 for _ in store.iter_events()),
        "event_chain_verified": True,
    }
    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
