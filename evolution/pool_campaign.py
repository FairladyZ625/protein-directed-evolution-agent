"""Pool-based active-learning campaign — dataset-agnostic.

GB1's four-site landscape is dense enough that an agent can *design* a combinatorial
library and expect most candidates to be measured (see evolution/campaign.py). Harder
landscapes (AAV, avGFP) are astronomically sparse: an enumerated library almost never
hits a measured variant, so free design breaks the oracle-lookup loop.

Here every strategy instead selects from a **fixed candidate pool** — the measured
variants withheld from the cold start. All four strategies share the same pool, the
same budget and the same measured-table oracle, and differ only in how they *rank* the
pool. This is a cleaner, harder test of whether the agent's reasoning / knowledge adds
value: any advantage comes from ranking, not from a different search space.

Strategies (all rank the unmeasured pool, take the top `budget`):
  ① random             — uniform random.
  ② greedy             — predicted mean only.
  ③ agent_no_knowledge — predicted mean + α · (fraction of the candidate's substitutions
                          that the Data Analyst found beneficial in the measured set);
                          i.e. focus on hypothesis-consistent variants.
  ④ knowledge_agent    — ③ plus UCB exploration (λ·√var) and a BLOSUM62 conservativeness
                          prior (β); ablating both recovers ③.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from knowledge.validators import load_rules

ROOT = Path(__file__).resolve().parents[1]
STRATEGIES = ("random", "greedy", "agent_no_knowledge", "knowledge_agent")
TOP_K = 10
ALPHA_HYP = 2.0     # weight of Data-Analyst hypothesis overlap in the agent acquisition
LAMBDA_UCB = 0.75   # exploration weight (knowledge agent)
BETA_BLOSUM = 0.30  # BLOSUM62 conservativeness prior weight (knowledge agent)


@dataclass
class DatasetSpec:
    """One protein landscape as a fixed labelled pool.

    df columns: `seq` (fixed-length substitution string), `fitness` (float), `hd`
    (Hamming distance to `wt`). feature_fn maps a list of seqs to a feature matrix.
    """
    name: str
    df: pd.DataFrame
    wt: str
    feature_fn: Callable[[list[str]], np.ndarray]
    fitness_col: str = "fitness"


def _blosum_lookup():
    matrix = load_rules()["blosum62"]
    def score(a: str, b: str) -> int:
        if a == b:
            return 4
        return matrix.get(a, {}).get(b, matrix.get(b, {}).get(a, 0))
    return score


def _subs(seq: str, wt: str) -> list[tuple[int, str]]:
    return [(i, c) for i, (c, w) in enumerate(zip(seq, wt)) if c != w]


def _analyst_beneficial(measured: pd.DataFrame, wt: str, fit_col: str, top_frac: float = 0.5) -> set[tuple[int, str]]:
    """Data Analyst: single substitutions whose mean observed fitness beats the pool
    median — the 'hypothesis' the agent focuses on."""
    tally: dict[tuple[int, str], list[float]] = {}
    for seq, f in zip(measured.seq, measured[fit_col]):
        for pos, aa in _subs(seq, wt):
            tally.setdefault((pos, aa), []).append(float(f))
    if not tally:
        return set()
    means = {k: float(np.mean(v)) for k, v in tally.items()}
    cutoff = np.quantile(list(means.values()), top_frac)
    return {k for k, m in means.items() if m >= cutoff}


def _predictor():
    from models.train_ladder import RidgePredictor
    return RidgePredictor(seeds=5)


def _event(store, name, actor, payload, round_id, strategy):
    if store is not None:
        store.append(name, round_id=round_id, strategy=strategy, actor=actor, payload=payload)


def _stats(batch: pd.DataFrame, cumulative: pd.DataFrame, fit_col: str, strong_thr: float) -> dict:
    top = batch.nlargest(TOP_K, fit_col, keep="first")
    ctop = cumulative.nlargest(TOP_K, fit_col, keep="first")
    return {"n_nominated": len(batch),
            "top10_max": round(float(top[fit_col].max()), 4),
            "top10_mean": round(float(top[fit_col].mean()), 4),
            "cum_top10_max": round(float(ctop[fit_col].max()), 4),
            "cum_top10_mean": round(float(ctop[fit_col].mean()), 4),
            "n_hit_strong": int((batch[fit_col] >= strong_thr).sum()),
            "cum_n_strong": int((cumulative[fit_col] >= strong_thr).sum()),
            "top10": [[str(s), round(float(f), 4)] for s, f in zip(top.seq, top[fit_col])]}


def _rank(strategy, pool, measured, spec, blosum, budget, rng, event_store, round_id):
    fit_col = spec.fitness_col
    if strategy == "random":
        idx = rng.permutation(len(pool))[:budget]
        return pool.iloc[np.sort(idx)]
    pred = _predictor()
    pred.fit(spec.feature_fn(measured.seq.tolist()), measured[fit_col].to_numpy())
    mean, var = pred.predict(spec.feature_fn(pool.seq.tolist()))
    _event(event_store, "agent.role.completed", "fitness_evaluator",
           {"n_scored": len(pool), "mean_max": round(float(mean.max()), 4),
            "variance_min": float(var.min()), "variance_mean": float(var.mean()),
            "variance_max": float(var.max())}, round_id, strategy)
    if strategy == "greedy":
        acq = mean
    else:
        beneficial = _analyst_beneficial(measured, spec.wt, fit_col)
        _event(event_store, "agent.role.completed", "data_analyst",
               {"n_beneficial_subs": len(beneficial)}, round_id, strategy)
        overlap = np.array([
            (sum((p, a) in beneficial for p, a in _subs(s, spec.wt)) / max(1, len(_subs(s, spec.wt))))
            for s in pool.seq])
        _event(event_store, "agent.role.completed", "hypothesis_generator",
               {"rule_ids": ["R-ANALYST-BENEFICIAL"], "mean_overlap": round(float(overlap.mean()), 3)}, round_id, strategy)
        acq = mean + ALPHA_HYP * overlap
        if strategy == "knowledge_agent":
            blosum_prior = np.array([
                (np.mean([blosum(spec.wt[p], a) for p, a in _subs(s, spec.wt)]) / 4.0) if _subs(s, spec.wt) else 0.0
                for s in pool.seq])
            acq = acq + LAMBDA_UCB * np.sqrt(np.maximum(var, 0.0)) + BETA_BLOSUM * blosum_prior
            _event(event_store, "agent.role.completed", "scientific_critic",
                   {"knowledge": "UCB + BLOSUM62 prior applied", "blosum_mean": round(float(blosum_prior.mean()), 3)}, round_id, strategy)
    order = np.lexsort((pool.seq.to_numpy(), -acq))
    return pool.iloc[order[:budget]]


def run_pool_campaign(spec: DatasetSpec, *, cold_start_hd: int = 2, budget: int = 96,
                      n_rounds: int = 3, seed: int = 42, strong_thr: float | None = None,
                      event_store=None) -> dict:
    df = spec.df
    fit_col = spec.fitness_col
    if strong_thr is None:
        strong_thr = float(np.quantile(df[fit_col], 0.9))  # top-decile fitness = "strong"
    blosum = _blosum_lookup()
    results: dict[str, dict] = {}
    for strategy in STRATEGIES:
        rng = np.random.default_rng(seed)
        measured = df[df.hd <= cold_start_hd].copy()
        pool = df[df.hd > cold_start_hd].copy()
        rounds, batches = [], []
        _event(event_store, "campaign.started", "campaign",
               {"budget": budget, "cold_start_n": len(measured), "pool_n": len(pool)}, 0, strategy)
        for round_id in range(1, n_rounds + 1):
            if pool.empty:
                break
            picks = _rank(strategy, pool, measured, spec, blosum, budget, rng, event_store, round_id)
            measured = pd.concat([measured, picks], ignore_index=True)
            pool = pool.drop(picks.index)
            batches.append(picks)
            cumulative = pd.concat(batches, ignore_index=True)
            row = {"round": round_id, **_stats(picks, cumulative, fit_col, strong_thr),
                   "measured_after": len(measured), "pool_remaining": len(pool)}
            rounds.append(row)
            _event(event_store, "campaign.round.completed", "campaign", row, round_id, strategy)
        results[strategy] = {
            "strategy": strategy, "seed": seed, "n_rounds": len(rounds),
            "budget_per_round": budget,
            "acquisition": {"random": "uniform random",
                            "greedy": "predicted mean",
                            "agent_no_knowledge": f"mean + {ALPHA_HYP}·analyst-overlap",
                            "knowledge_agent": f"mean + {ALPHA_HYP}·analyst-overlap + {LAMBDA_UCB}·√var + {BETA_BLOSUM}·BLOSUM62"}[strategy],
            "rounds": rounds}
        _event(event_store, "campaign.completed", "campaign", {"rounds": rounds}, len(rounds), strategy)
    return {"schema_version": "pool.v1", "dataset": spec.name,
            "nomination": "pool-based active learning (fixed measured pool, strategies differ by ranking)",
            "oracle": "measured table lookup", "wild_type": spec.wt,
            "candidate_pool_size": int((df.hd > cold_start_hd).sum()),
            "cold_start_size": int((df.hd <= cold_start_hd).sum()),
            "cold_start_hd": cold_start_hd, "budget_per_round": budget, "n_rounds": n_rounds,
            "strong_threshold": round(strong_thr, 4),
            "summary": {k: {"final_cum_top10_max": v["rounds"][-1]["cum_top10_max"] if v["rounds"] else None,
                            "final_cum_top10_mean": v["rounds"][-1]["cum_top10_mean"] if v["rounds"] else None,
                            "final_cum_n_strong": v["rounds"][-1]["cum_n_strong"] if v["rounds"] else None,
                            "cum_top10_max_curve": [r["cum_top10_max"] for r in v["rounds"]]}
                        for k, v in results.items()},
            "strategies": results}


def plot(report: dict, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for name, r in report["strategies"].items():
        rounds = r["rounds"]
        if rounds:
            ax.plot([x["round"] for x in rounds], [x["cum_top10_max"] for x in rounds], marker="o", label=name)
    ax.set(xlabel="round", ylabel="cumulative top-10 max true fitness",
           title=f"{report['dataset']} pool-based campaign (budget={report['budget_per_round']}/round)")
    ax.grid(axis="y", alpha=.25); ax.legend(frameon=False); fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True); fig.savefig(path, dpi=150); plt.close(fig)


def main(argv: list[str] | None = None) -> dict:
    import argparse
    from evolution.datasets import load
    p = argparse.ArgumentParser(description="Pool-based active-learning campaign on a harder landscape")
    p.add_argument("--dataset", required=True, choices=("aav", "avgfp"))
    p.add_argument("--feature", default="one_hot", choices=("one_hot", "esm2"))
    p.add_argument("--cold-start-hd", type=int, default=2)
    p.add_argument("--budget", type=int, default=96)
    p.add_argument("--n-rounds", type=int, default=3)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out-dir", type=Path, default=None,
                   help="default: harness/reports/runs/workflow@<v>/<dataset>/")
    args = p.parse_args(argv)

    from events.store import EventStore
    from evolution.results_layout import run_dir
    out_dir = args.out_dir or run_dir("workflow", args.dataset)
    (out_dir / "figures").mkdir(parents=True, exist_ok=True)
    ev = out_dir / f"pool_{args.feature}.events.jsonl"
    if ev.exists():
        ev.unlink()
    store = EventStore(ev)
    spec = load(args.dataset, args.feature)
    report = run_pool_campaign(spec, cold_start_hd=args.cold_start_hd, budget=args.budget,
                               n_rounds=args.n_rounds, seed=args.seed, event_store=store)
    store.verify()
    out_json = out_dir / f"pool_{args.feature}.metrics.json"
    out_fig = out_dir / "figures" / f"pool_{args.feature}.png"
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    plot(report, out_fig)
    n_events = sum(1 for _ in store.iter_events())
    print(f"[out] {out_json}\n[out] {out_fig}\n[out] {ev} ({n_events} events, head {store.head_hash[:12]})")
    print(f"dataset={report['dataset']} pool={report['candidate_pool_size']} "
          f"cold_start={report['cold_start_size']} strong_thr={report['strong_threshold']}")
    for name, s in report["summary"].items():
        print(f"  {name:20s} cum_top10_max={s['final_cum_top10_max']} "
              f"mean={s['final_cum_top10_mean']} strong={s['final_cum_n_strong']} "
              f"curve={[round(x, 2) for x in s['cum_top10_max_curve']]}")
    from evolution.experiment_log import log_run
    rel = lambda q: str(Path(q).resolve().relative_to(ROOT))  # noqa: E731
    log_run("pool_campaign",
            command=f"python -m evolution.pool_campaign --dataset {args.dataset} --feature {args.feature} --cold-start-hd {args.cold_start_hd}",
            params={"dataset": args.dataset, "feature": args.feature, "cold_start_hd": args.cold_start_hd,
                    "budget": args.budget, "n_rounds": args.n_rounds, "seed": args.seed},
            artifacts=[rel(out_json), rel(ev), rel(out_fig)],
            summary=report["summary"])
    return report


if __name__ == "__main__":
    main()
