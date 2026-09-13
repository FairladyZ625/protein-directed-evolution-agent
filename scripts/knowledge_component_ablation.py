#!/usr/bin/env python3
"""Separate the two components of the GB1 "knowledge" treatment.

The knowledge arm's acquisition score is

    acq = predicted_mean + LAMBDA_UCB * sqrt(variance) + BETA_BLOSUM * blosum_prior

so "knowledge on/off" bundles two independent terms: an *exploration* term (UCB on the
bootstrap ensemble's disagreement) and a *conservativeness prior* (mean BLOSUM62 score of
the variant's substitutions). The published ablation only ever compared the bundle against
neither term, so neither component's contribution is identified. This script runs the 2x2:

    neither      lambda=0,    beta=0      (== the agent_no_knowledge arm)
    ucb_only     lambda=0.75, beta=0
    blosum_only  lambda=0,    beta=0.30
    both         lambda=0.75, beta=0.30   (== the published knowledge_agent arm)

The two corner cells are controls: they must reproduce the published arms exactly, which is
what makes the two middle cells readable. Nothing in evolution/campaign.py is modified —
the constants are rebound on the module object for the duration of one run, so the default
code path that produced every existing result is untouched.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from evolution import campaign as C
from evolution.random_baseline import load_landscape
from knowledge.validators import load_rules


CELLS = (
    ("neither", 0.0, 0.0),
    ("ucb_only", C.LAMBDA_UCB, 0.0),
    ("blosum_only", 0.0, C.BETA_BLOSUM),
    ("both", C.LAMBDA_UCB, C.BETA_BLOSUM),
)


def run_cell(df, *, lambda_ucb: float, beta_blosum: float, seed: int, n_rounds: int,
             budget: int, cold_start: str, max_cold_hd: int, blosum_score,
             stream: Path) -> tuple[dict, list[list[str]]]:
    """Run one knowledge_agent campaign with the two acquisition weights rebound.

    Returns the run record and the per-round nominated batches, read back from the event
    stream — the campaign does not return them, and the batches are what decide whether a
    term changed the experiment or only the score.
    """
    from events.store import EventStore

    if stream.exists():
        stream.unlink()
    store = EventStore(stream)
    saved = (C.LAMBDA_UCB, C.BETA_BLOSUM)
    C.LAMBDA_UCB, C.BETA_BLOSUM = float(lambda_ucb), float(beta_blosum)
    try:
        run = C._run_strategy("knowledge_agent", df, seed=seed, n_rounds=n_rounds,
                              budget=budget, pool_size=C.POOL_SIZE, event_store=store,
                              use_llm=False, cold_start=cold_start,
                              max_cold_hd=max_cold_hd, blosum_score=blosum_score)
    finally:
        C.LAMBDA_UCB, C.BETA_BLOSUM = saved
    batches = []
    for line in stream.read_text().splitlines():
        event = json.loads(line)
        if event["event_type"] == "campaign.propose.completed":
            batches.append(sorted(event["payload"]["variants"]))
    return run, batches


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--rounds", type=int, default=C.N_ROUNDS)
    parser.add_argument("--budget", type=int, default=C.BUDGET)
    parser.add_argument("--cold-start", default="low_hd", choices=("low_hd", "random"))
    parser.add_argument("--max-cold-hd", type=int, default=2)
    parser.add_argument("--output", default="reports/knowledge_component_ablation.json")
    args = parser.parse_args()

    df = load_landscape()
    if "HD" not in df.columns:
        df["HD"] = [sum(a != b for a, b in zip(v, C.WT)) for v in df.Variants]
    blosum_score = C._blosum_lookup(load_rules())

    stream_dir = Path(args.output).resolve().parent / "_component_ablation_streams"
    stream_dir.mkdir(parents=True, exist_ok=True)
    cells: dict[str, dict] = {}
    for name, lam, beta in CELLS:
        run, batches = run_cell(df, lambda_ucb=lam, beta_blosum=beta, seed=args.seed,
                                n_rounds=args.rounds, budget=args.budget,
                                cold_start=args.cold_start, max_cold_hd=args.max_cold_hd,
                                blosum_score=blosum_score,
                                stream=stream_dir / f"{name}.jsonl")
        last = run["rounds"][-1]
        sizes = [r["n_nominated"] for r in run["rounds"]]
        cells[name] = {
            "lambda_ucb": lam,
            "beta_blosum": beta,
            "final_cum_top10_max": last["cum_top10_max"],
            "final_cum_n_strong": last["cum_n_strong"],
            "total_beneficial_hits": sum(r["n_hit_beneficial"] for r in run["rounds"]),
            "n_nominated": sum(sizes),
            "peak_round": next((r["round"] for r in run["rounds"]
                                if r["cum_top10_max"] >= max(x["cum_top10_max"]
                                                             for x in run["rounds"])), None),
            "rounds": [{k: r[k] for k in ("round", "top10_max", "cum_top10_max",
                                          "cum_n_strong", "n_hit_beneficial")}
                       for r in run["rounds"]],
            "batches": batches,
        }
        print(name, "strong", cells[name]["final_cum_n_strong"],
              "max", cells[name]["final_cum_top10_max"], flush=True)

    # Batch overlap between cells: whether a term changed *what was measured*, not only
    # the end score. Two cells with equal strong counts but disjoint batches are not the
    # same treatment, and a term that leaves the batch byte-identical bought nothing.
    overlap = {}
    names = [n for n, _, _ in CELLS]
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            per_round = [len(set(x) & set(y)) for x, y in zip(cells[a]["batches"], cells[b]["batches"])]
            overlap[f"{a}__vs__{b}"] = per_round

    result = {
        "schema_version": "knowledge-component-ablation/v1",
        "question": "Which part of the GB1 knowledge treatment produced its effect: the UCB "
                    "exploration term, the BLOSUM62 conservativeness prior, or their interaction?",
        "protocol": {"dataset": "GB1", "seed": args.seed, "n_rounds": args.rounds,
                     "budget_per_round": args.budget, "cold_start": args.cold_start,
                     "max_cold_hd": args.max_cold_hd,
                     "strong_threshold": 4.0, "beneficial_threshold": 1.0,
                     "selector": "reads all scored candidates; the knowledge rule gate is "
                                 "audit-only on this frozen GB1 path"},
        "cells": cells,
        "batch_overlap_per_round": overlap,
        "deltas": {
            "ucb_only_minus_neither": cells["ucb_only"]["final_cum_n_strong"] - cells["neither"]["final_cum_n_strong"],
            "blosum_only_minus_neither": cells["blosum_only"]["final_cum_n_strong"] - cells["neither"]["final_cum_n_strong"],
            "both_minus_neither": cells["both"]["final_cum_n_strong"] - cells["neither"]["final_cum_n_strong"],
            "interaction": (cells["both"]["final_cum_n_strong"] - cells["ucb_only"]["final_cum_n_strong"]
                            - cells["blosum_only"]["final_cum_n_strong"] + cells["neither"]["final_cum_n_strong"]),
        },
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print("written", out)


if __name__ == "__main__":
    main()
