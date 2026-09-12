"""Audit completed strict reruns and any preregistered abort evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path

from events.store import EventStore
from evolution.datasets import load


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_success(path: Path, truth: dict[str, tuple[int, float]]) -> dict:
    metrics_path = path / "metrics.json"
    events_path = path / "events.jsonl"
    report = json.loads(metrics_path.read_text())
    rows = [row for round_ in report["rounds"] for row in round_["nominations"]]
    sequences = [row["sequence"] for row in rows]
    EventStore(events_path).verify()

    assert report["round_counts"] == [48] * 6
    assert report["budget_spent"] == 288
    assert len(rows) == len(set(sequences)) == 288
    assert all(row["driver"] == "live_llm" for row in rows)
    assert all(sequence in truth for sequence in sequences)
    assert all(row["hd"] == truth[row["sequence"]][0] > 2 for row in rows)
    assert all(
        math.isclose(row["fitness"], truth[row["sequence"]][1], rel_tol=0, abs_tol=1e-12)
        for row in rows
    )
    assert all(
        math.isfinite(row["predicted_mean"])
        and math.isfinite(row["predicted_variance"])
        for row in rows
    )
    fitness = [row["fitness"] for row in rows]
    assert round(max(fitness), 4) == report["summary"]["final_cum_top10_max"]
    assert (
        sum(value >= report["strong_threshold"] for value in fitness)
        == report["summary"]["final_cum_n_strong"]
    )
    execution = report["execution"]
    assert execution["live_llm_rounds"] == 6
    assert execution["llm_round_errors"] == 0
    assert execution["harness_fill_nominations"] == 0
    assert execution["fallback_count"] == 0
    assert report["model"]["resolved_request_id"] == "gpt-5.6-sol"
    assert report["controls"]["shuffle_abs_below_0_1"] is True

    return {
        "version": report["version"],
        "seed": report["seed"],
        "round_counts": report["round_counts"],
        "nominations": len(rows),
        "unique_nominations": len(set(sequences)),
        "all_live": True,
        "oracle_hd_fitness_exact": True,
        "predictions_finite": True,
        "cum_top10_max_recomputed": round(max(fitness), 4),
        "strong_recomputed": sum(
            value >= report["strong_threshold"] for value in fitness
        ),
        "model": report["model"]["resolved_request_id"],
        "live_llm_requests": execution["live_llm_requests"],
        "shuffle_heldout_spearman": report["controls"]["shuffle_heldout_spearman"],
        "event_chain_verified": True,
        "metrics_sha256": sha256(metrics_path),
        "events_sha256": sha256(events_path),
    }


def audit_failure(path: Path) -> dict:
    failure_path = path / "failure.json"
    events_path = path / "events.jsonl"
    failure = json.loads(failure_path.read_text())
    store = EventStore(events_path)
    store.verify()
    events = list(store.iter_events())
    tests = [event for event in events if event["event_type"] == "agent.tool.test"]
    underfills = [
        event for event in events if event["event_type"] == "agent.llm.underfilled_round"
    ]
    assert len(tests) == len(underfills) == 1
    assert tests[0]["payload"]["measured"] == 46
    assert underfills[0]["payload"]["missing"] == 2
    assert underfills[0]["payload"]["policy"] == "abort_without_fallback"
    assert len(events) == failure["event_count"]
    assert sha256(events_path) == failure["events_sha256"]
    return {
        "version": failure["version"],
        "seed": failure["seed"],
        "status": failure["status"],
        "failed_round": failure["failed_round"],
        "live_nominations_measured": tests[0]["payload"]["measured"],
        "round_quota_remaining": underfills[0]["payload"]["missing"],
        "harness_fill_nominations": 0,
        "fallback_count": 0,
        "event_chain_verified": True,
        "events_sha256": sha256(events_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    spec = load("aav", "one_hot")
    truth = {
        str(row.seq): (int(row.hd), float(getattr(row, spec.fitness_col)))
        for row in spec.df.itertuples()
    }
    successes = [
        audit_success(args.root / f"v0.1-seed{seed}", truth) for seed in (0, 7, 42)
    ]
    maxima = [row["cum_top10_max_recomputed"] for row in successes]
    strong = [row["strong_recomputed"] for row in successes]
    output = {
        "schema_version": "version-matrix.audit.v1",
        "status": "stopped_on_preregistered_v0.1_seed_expansion_failure",
        "successful_runs": successes,
        "v0.1_three_seed": {
            "seeds": [0, 7, 42],
            "cum_top10_max": maxima,
            "cum_top10_max_mean": statistics.mean(maxima),
            "cum_top10_max_sample_sd": statistics.stdev(maxima),
            "strong": strong,
            "strong_mean": statistics.mean(strong),
            "strong_sample_sd": statistics.stdev(strong),
            "expanded_by_preregistered_sd_gate": statistics.stdev(maxima) > 0.5,
        },
        "failed_run": audit_failure(args.root / "v0.1-seed1"),
        "unverified": [
            "v0.1 ten-seed endpoint distribution",
            "v0.2 unified reruns",
            "v0.4-LLM unified reruns",
            "seven-version consolidated matrix",
            "post-unification version ranking",
        ],
    }
    args.out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
