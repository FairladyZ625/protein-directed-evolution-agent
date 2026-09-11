"""Four-strategy GB1 active-learning campaign (T7).

The campaign deliberately keeps the oracle separate from predictors: every reported
fitness is looked up in the measured GB1 table, never taken from a model.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from evolution.random_baseline import (DATA_PATH, EXPECTED_ROWS, BUDGET, N_ROUNDS,
                                       POOL_SIZE, TOP_K, load_landscape, propose_random,
                                       build_cold_start_pool)
from models.train_ladder import RidgePredictor

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "reports" / "campaign_metrics.json"
OUT_FIG = ROOT / "reports" / "figures" / "campaign_curve.png"
STRATEGIES = ("random", "greedy", "agent_no_knowledge", "knowledge_agent")


def _features(variants: list[str]) -> np.ndarray:
    aa = "ACDEFGHIKLMNPQRSTVWY"
    lut = {c: i for i, c in enumerate(aa)}
    x = np.zeros((len(variants), 80), dtype=float)
    for row, seq in enumerate(variants):
        for pos, char in enumerate(seq):
            x[row, pos * 20 + lut[char]] = 1.0
    return x


def _stats(batch: pd.DataFrame, cumulative: pd.DataFrame) -> dict:
    top = batch.nlargest(TOP_K, "Fitness", keep="first")
    ctop = cumulative.nlargest(TOP_K, "Fitness", keep="first")
    hits = int((batch["Fitness"] > 0.01).sum())
    return {"n_nominated": len(batch), "top10_max": round(float(top.Fitness.max()), 6),
            "top10_mean": round(float(top.Fitness.mean()), 6), "n_hit_nonzero": hits,
            "hit_rate_nonzero": round(hits / len(batch), 6),
            "cum_top10_max": round(float(ctop.Fitness.max()), 6),
            "cum_top10_mean": round(float(ctop.Fitness.mean()), 6),
            "top10": [[str(v), round(float(f), 6)] for v, f in zip(top.Variants, top.Fitness)]}


def _event(store, event_type, strategy, round_id, payload):
    if store is not None:
        store.append(event_type, round_id=round_id, strategy=strategy, actor="campaign", payload=payload)


def _propose(strategy: str, candidates: np.ndarray, budget: int, rng: np.random.Generator,
             train: pd.DataFrame, predictor: RidgePredictor | None) -> np.ndarray:
    if strategy == "random" or predictor is None or len(train) < 2:
        return propose_random(candidates, budget, rng)
    predictor.fit(_features(train.Variants.tolist()), train.Fitness.to_numpy())
    mean, var = predictor.predict(_features(candidates.tolist()))
    score = mean + (0.75 * np.sqrt(np.maximum(var, 0)) if strategy == "knowledge_agent" else 0)
    # Stable tie-breaking makes reruns independent of pandas ordering.
    order = np.lexsort((candidates, -score))
    picks = candidates[order[:budget]]
    if strategy in ("agent_no_knowledge", "knowledge_agent") and len(picks) < budget:
        extra = candidates[~np.isin(candidates, picks)]
        picks = np.concatenate([picks, propose_random(extra, budget - len(picks), rng)])
    return picks


def run_campaign(df: pd.DataFrame | None = None, *, seed: int = 42, n_rounds: int = N_ROUNDS,
                 budget: int = BUDGET, pool_size: int = POOL_SIZE, event_store=None) -> dict:
    df = load_landscape() if df is None else df.copy()
    if df.empty:
        raise ValueError("measured landscape cannot be empty")
    oracle = df.set_index("Variants")["Fitness"]
    all_results = {}
    for strategy in STRATEGIES:
        rng = np.random.default_rng(seed)
        pool = build_cold_start_pool(df, rng, pool_size)
        measured = set(pool.Variants)
        train = pool[["Variants", "Fitness"]].copy()
        predictor = RidgePredictor(seeds=5) if strategy != "random" else None
        rounds, cumulative = [], pd.DataFrame(columns=df.columns)
        _event(event_store, "campaign.started", strategy, 0, {"budget": budget, "pool_size": pool_size})
        for round_id in range(1, n_rounds + 1):
            candidates = df.loc[~df.Variants.isin(measured), "Variants"].to_numpy()
            picks = _propose(strategy, candidates, budget, rng, train, predictor)
            batch = df.set_index("Variants").loc[picks].reset_index()
            measured.update(picks.tolist()); train = pd.concat([train, batch[["Variants", "Fitness"]]], ignore_index=True)
            cumulative = pd.concat([cumulative, batch], ignore_index=True)
            row = {"round": round_id, **_stats(batch, cumulative), "pool_size_after": len(train)}
            rounds.append(row)
            _event(event_store, "campaign.round.completed", strategy, round_id, row)
        all_results[strategy] = {"strategy": strategy, "seed": seed, "n_rounds": n_rounds,
                                 "budget_per_round": budget, "cold_start_pool_size": pool_size,
                                 "rounds": rounds, "fallback": strategy in ("agent_no_knowledge", "knowledge_agent")}
        _event(event_store, "campaign.completed", strategy, n_rounds, {"rounds": rounds})
    return {"schema_version": "t7.v1", "candidate_space_size": len(df),
            "missing_combinations": max(0, 160000 - len(df)), "oracle": "measured table lookup",
            "strategies": all_results}


def plot_campaign(report: dict, path: Path = OUT_FIG) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for strategy, result in report["strategies"].items():
        ax.plot([r["round"] for r in result["rounds"]], [r["cum_top10_max"] for r in result["rounds"]], marker="o", label=strategy)
    ax.set(xlabel="round", ylabel="cumulative top-10 max true fitness", title="GB1 four-strategy campaign")
    ax.grid(axis="y", alpha=.25); ax.legend(frameon=False); fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True); fig.savefig(path, dpi=150); plt.close(fig)


def main(argv: list[str] | None = None) -> dict:
    p = argparse.ArgumentParser(); p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out-json", type=Path, default=OUT_JSON); p.add_argument("--out-fig", type=Path, default=OUT_FIG)
    args = p.parse_args(argv); report = run_campaign(seed=args.seed)
    args.out_json.parent.mkdir(parents=True, exist_ok=True); args.out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    plot_campaign(report, args.out_fig); print(f"[out] {args.out_json}\n[out] {args.out_fig}"); return report


if __name__ == "__main__":
    main()
