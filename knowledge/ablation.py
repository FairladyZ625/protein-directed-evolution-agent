"""Reproducible AAV knowledge-ablation and four-strategy comparison.

Oracle fitness is exposed only after a batch has been frozen.  The knowledge graph is
built from the measured set inside ``run_autoresearch``; rejected-candidate fitness is
joined only here, after the paired campaigns finish, for failure analysis.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from agent.auto_researcher import _gate_variants, run_autoresearch
from events.store import EventStore
from evolution.datasets import load
from evolution.pool_campaign import _stats
from knowledge.validators import load_rules
from models.train_ladder import EpistasisRidgePredictor


DEFAULT_SEEDS = (0, 1, 2)


def _blosum_score(matrix: dict, source: str, target: str) -> int:
    if source == target:
        return 4
    return int(matrix.get(source, {}).get(target, matrix.get(target, {}).get(source, 0)))


def _mean_blosum(sequence: str, wild_type: str, matrix: dict) -> float:
    scores = [_blosum_score(matrix, wild, mutant)
              for wild, mutant in zip(wild_type, sequence) if wild != mutant]
    return float(np.mean(scores)) if scores else 4.0


def _nominated_sequences(report: dict) -> list[str]:
    return [sequence for batch in report["nominations"] for sequence, _ in batch["variants"]]


def _run_baseline(spec, strategy: str, *, budget: int, n_rounds: int,
                  seed: int, store: EventStore) -> dict:
    """Run random or mean-greedy with the same cold start, pool, model, and oracle."""
    if strategy not in {"random", "greedy"}:
        raise ValueError(f"unsupported baseline: {strategy}")
    fit_col = spec.fitness_col
    measured = spec.df[spec.df.hd <= 2].copy()
    pool = spec.df[spec.df.hd > 2].copy()
    strong_threshold = float(np.quantile(spec.df[fit_col], 0.9))
    rng = np.random.default_rng(seed)
    batches = []
    rounds = []
    store.append("ablation.campaign.started", round_id=0, strategy=strategy,
                 actor="campaign", payload={"seed": seed, "budget": budget,
                                             "candidate_pool_size": len(pool)})
    for round_id in range(1, n_rounds + 1):
        if strategy == "random":
            selected = pool.iloc[rng.permutation(len(pool))[:budget]].seq.tolist()
            cv_spearman = None
        else:
            model = EpistasisRidgePredictor().fit(
                spec.feature_fn(measured.seq.tolist()), measured[fit_col].to_numpy())
            mean, _ = model.predict(spec.feature_fn(pool.seq.tolist()))
            selected = pool.iloc[np.argsort(-mean)[:budget]].seq.tolist()
            cv_spearman = model.val_spearman
        # Preserve original pool row order: bootstrap membership in later rounds depends
        # on training-row order, matching the product test() path and the v0.7 anchor.
        batch = pool[pool.seq.isin(selected)].copy()
        measured = pd.concat([measured, batch], ignore_index=True)
        pool = pool.drop(batch.index)
        batches.append(batch)
        cumulative = pd.concat(batches, ignore_index=True)
        row = {"round": round_id,
               **_stats(batch, cumulative, fit_col, strong_threshold),
               "cv_spearman": cv_spearman,
               "spent_after": len(cumulative)}
        rounds.append(row)
        store.append("ablation.round.completed", round_id=round_id, strategy=strategy,
                     actor="campaign", payload={"seed": seed, **row})
    summary = {
        "final_cum_top10_max": rounds[-1]["cum_top10_max"],
        "final_cum_top10_mean": rounds[-1]["cum_top10_mean"],
        "final_cum_n_strong": rounds[-1]["cum_n_strong"],
        "cum_top10_max_curve": [row["cum_top10_max"] for row in rounds],
    }
    store.append("ablation.campaign.completed", round_id=n_rounds, strategy=strategy,
                 actor="campaign", payload={"seed": seed, **summary})
    return {
        "strategy": strategy,
        "seed": seed,
        "llm_used": False,
        "budget_spent": sum(len(batch) for batch in batches),
        "strong_threshold": strong_threshold,
        "rounds": rounds,
        "nominations": [
            {"round": round_id,
             "variants": [[str(sequence), float(fitness)]
                          for sequence, fitness in zip(batch.seq, batch[fit_col])]}
            for round_id, batch in enumerate(batches, 1)
        ],
        "summary": summary,
    }


def _run_negative_control(spec, seed: int = 20260912) -> dict:
    """Fit the registered surrogate after label shuffling; its CV rank signal must collapse."""
    cold = spec.df[spec.df.hd <= 2]
    x = spec.feature_fn(cold.seq.tolist())
    y = cold.fitness.to_numpy()
    observed = EpistasisRidgePredictor().fit(x, y).val_spearman
    shuffled_y = np.random.default_rng(seed).permutation(y)
    shuffled = EpistasisRidgePredictor().fit(x, shuffled_y).val_spearman
    return {
        "seed": seed,
        "observed_cv_spearman": float(observed),
        "shuffle_label_cv_spearman": float(shuffled),
        "pass": bool(abs(shuffled) < 0.1 and observed > 0.8),
        "criterion": "observed > 0.8 and abs(shuffle) < 0.1",
    }


def _run_v07_anchor(spec, matrix: dict, *, budget: int, n_rounds: int) -> dict:
    """Re-run the registered gated greedy and UCB-beta=3 trajectories."""
    source_pool = spec.df[spec.df.hd > 2].copy()
    allowed, _ = _gate_variants(
        source_pool.seq.tolist(), wt=spec.wt, max_hd=4, blosum_min=0.0,
        blosum_fn=lambda a, b: _blosum_score(matrix, a, b),
    )
    gate_pool = source_pool[source_pool.seq.isin(allowed)].copy()
    strong_threshold = float(np.quantile(spec.df.fitness, 0.9))
    anchors = {}
    for name, beta in (("greedy", 0.0), ("ucb_beta_3", 3.0)):
        measured = spec.df[spec.df.hd <= 2].copy()
        pool = gate_pool.copy()
        batches = []
        for _round_id in range(1, n_rounds + 1):
            model = EpistasisRidgePredictor().fit(
                spec.feature_fn(measured.seq.tolist()), measured.fitness.to_numpy())
            mean, var = model.predict(spec.feature_fn(pool.seq.tolist()))
            acquisition = mean + beta * np.sqrt(np.maximum(var, 0.0))
            selected = pool.iloc[np.argsort(-acquisition)[:budget]].seq.tolist()
            batch = pool[pool.seq.isin(selected)].copy()
            measured = pd.concat([measured, batch], ignore_index=True)
            pool = pool.drop(batch.index)
            batches.append(batch)
        cumulative = pd.concat(batches, ignore_index=True)
        anchors[name] = {
            "cum_top10_max": float(cumulative.fitness.max()),
            "cum_n_strong": int((cumulative.fitness >= strong_threshold).sum()),
            "n_nominated": int(len(cumulative)),
        }
    anchors["pass"] = bool(
        np.isclose(anchors["greedy"]["cum_top10_max"], 7.82896802739)
        and anchors["greedy"]["cum_n_strong"] == 166
        and np.isclose(anchors["ucb_beta_3"]["cum_top10_max"], 8.416205130560002)
        and anchors["ucb_beta_3"]["cum_n_strong"] == 128
    )
    if not anchors["pass"]:
        raise RuntimeError(f"v0.7 entry anchor mismatch: {anchors}")
    return anchors


def _append_agent_trace(store: EventStore, report: dict, *, seed: int) -> None:
    """Replay one completed agent trace into the campaign-owned event chain.

    Pydantic may copy tool callables while dispatching concurrent calls.  Keeping the
    durable writer outside that boundary ensures this file has exactly one sequence/hash
    owner while retaining the full, observed tool trace.
    """
    for event in report["tool_trace"]:
        store.append(event["event_type"], round_id=event["round_id"],
                     strategy=event["strategy"], actor=event["actor"],
                     payload={"seed": seed, **event["payload"]})


def _distribution(sequences: Iterable[str], spec, matrix: dict) -> dict:
    sequences = list(sequences)
    hd = np.asarray([sum(a != b for a, b in zip(sequence, spec.wt))
                     for sequence in sequences], dtype=float)
    blosum = np.asarray([_mean_blosum(sequence, spec.wt, matrix)
                         for sequence in sequences], dtype=float)
    return {
        "n": len(sequences),
        "hd_mean": None if not len(hd) else float(hd.mean()),
        "hd_counts": {str(value): int((hd == value).sum())
                      for value in sorted(set(hd.astype(int)))},
        "mean_blosum_mean": None if not len(blosum) else float(blosum.mean()),
        "mean_blosum_min": None if not len(blosum) else float(blosum.min()),
        "mean_blosum_max": None if not len(blosum) else float(blosum.max()),
    }


def _summarise(spec, trials: list[dict], matrix: dict, *, max_hd: int,
               blosum_min: float) -> tuple[dict, list[dict]]:
    by_key = {(trial["strategy"], trial["seed"]): trial for trial in trials}
    seeds = sorted({trial["seed"] for trial in trials})
    pool = spec.df[spec.df.hd > 2]
    pool_peak = float(pool.fitness.max())
    strong_threshold = float(np.quantile(spec.df.fitness, 0.9))
    strategies = {}
    for strategy in ("random", "greedy", "agent_no_knowledge", "knowledge_agent"):
        selected = [by_key[(strategy, seed)] for seed in seeds]
        maxima = [trial["summary"]["final_cum_top10_max"] for trial in selected]
        strong = [trial["summary"]["final_cum_n_strong"] for trial in selected]
        strategies[strategy] = {
            "n_seeds": len(selected),
            "cum_top10_max_mean": float(np.mean(maxima)),
            "cum_top10_max_values": maxima,
            "strong_mean": float(np.mean(strong)),
            "strong_values": strong,
            "peak_hits": int(sum(np.isclose(value, pool_peak) for value in maxima)),
            "peak_hit_rate": float(np.mean([np.isclose(value, pool_peak) for value in maxima])),
            "mean_curve": np.mean(
                [trial["summary"]["cum_top10_max_curve"] for trial in selected], axis=0
            ).tolist(),
        }

    paired = []
    rejected_rows = []
    fitness_lookup = spec.df.set_index("seq").fitness.to_dict()
    for seed in seeds:
        no_knowledge = _nominated_sequences(by_key[("agent_no_knowledge", seed)])
        knowledge = _nominated_sequences(by_key[("knowledge_agent", seed)])
        no_set, knowledge_set = set(no_knowledge), set(knowledge)
        _, rejected = _gate_variants(no_knowledge, wt=spec.wt, max_hd=max_hd,
                                     blosum_min=blosum_min,
                                     blosum_fn=lambda a, b: _blosum_score(matrix, a, b))
        for sequence, reasons in rejected.items():
            fitness = float(fitness_lookup[sequence])
            rejected_rows.append({
                "seed": seed,
                "sequence": sequence,
                "fitness": fitness,
                "is_strong": fitness >= strong_threshold,
                "reasons": reasons,
            })
        paired.append({
            "seed": seed,
            "intersection": len(no_set & knowledge_set),
            "union": len(no_set | knowledge_set),
            "jaccard": len(no_set & knowledge_set) / max(1, len(no_set | knowledge_set)),
            "knowledge_share_of_no_knowledge": len(no_set & knowledge_set) / max(1, len(no_set)),
            "no_knowledge": _distribution(no_knowledge, spec, matrix),
            "knowledge": _distribution(knowledge, spec, matrix),
            "n_no_knowledge_rejected_posthoc": len(rejected),
            "n_rejected_strong": sum(row["is_strong"] for row in rejected_rows if row["seed"] == seed),
            "max_rejected_fitness": max(
                (row["fitness"] for row in rejected_rows if row["seed"] == seed), default=None),
        })
    return {
        "candidate_pool_peak": pool_peak,
        "strong_threshold": strong_threshold,
        "strategies": strategies,
        "paired_knowledge_ablation": paired,
        "paired_deltas": {
            "strong_knowledge_minus_no_knowledge": [
                by_key[("knowledge_agent", seed)]["summary"]["final_cum_n_strong"]
                - by_key[("agent_no_knowledge", seed)]["summary"]["final_cum_n_strong"]
                for seed in seeds
            ],
            "max_knowledge_minus_no_knowledge": [
                by_key[("knowledge_agent", seed)]["summary"]["final_cum_top10_max"]
                - by_key[("agent_no_knowledge", seed)]["summary"]["final_cum_top10_max"]
                for seed in seeds
            ],
        },
    }, rejected_rows


def _plot(summary: dict, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    palette = {"random": "#777777", "greedy": "#2878b5",
               "agent_no_knowledge": "#e07a36", "knowledge_agent": "#2a9d67"}
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    for strategy, row in summary["strategies"].items():
        curve = row["mean_curve"]
        ax.plot(range(1, len(curve) + 1), curve, marker="o", linewidth=2,
                label=strategy, color=palette[strategy])
    ax.set(xlabel="Round (48 measured variants)", ylabel="Cumulative maximum true fitness",
           title="AAV four-strategy comparison (paired seeds)")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def run(*, out_dir: Path, seeds: tuple[int, ...] = DEFAULT_SEEDS, budget: int = 48,
        n_rounds: int = 6, llm: bool = True, model: str | None = None,
        max_hd: int = 4, blosum_min: float = 0.0,
        resume_from: Path | None = None) -> dict:
    if len(seeds) < 1:
        raise ValueError("at least one seed is required")
    out_dir.mkdir(parents=True, exist_ok=True)
    event_path = out_dir / "events.jsonl"
    event_path.unlink(missing_ok=True)
    store = EventStore(event_path)
    spec = load("aav", "one_hot")
    matrix = load_rules()["blosum62"]
    trials = []
    if resume_from is not None:
        resumed = json.loads((resume_from / "metrics.json").read_text(encoding="utf-8"))
        protocol = resumed["protocol"]
        expected = (budget, n_rounds, llm, max_hd, blosum_min)
        observed = (protocol["budget_per_round"], protocol["n_rounds"],
                    protocol["llm_requested"], protocol["max_hd"], protocol["blosum_min"])
        if observed != expected:
            raise ValueError(f"resume protocol mismatch: expected {expected}, observed {observed}")
        trials = [trial for trial in resumed["trials"] if int(trial["seed"]) in seeds]
        for trial in trials:
            store.append("ablation.trial.reused", round_id=0, strategy=trial["strategy"],
                         actor="campaign", payload={"seed": trial["seed"],
                                                     "source": str(resume_from)})
    for seed in seeds:
        completed = {trial["strategy"] for trial in trials if trial["seed"] == seed}
        if completed == {"random", "greedy", "agent_no_knowledge", "knowledge_agent"}:
            continue
        if completed:
            raise ValueError(f"resume source has a partial strategy set for seed {seed}: {completed}")
        for strategy in ("random", "greedy"):
            trials.append(_run_baseline(spec, strategy, budget=budget, n_rounds=n_rounds,
                                        seed=seed, store=store))
        no_knowledge = run_autoresearch(
            spec, budget=budget, n_rounds=n_rounds, seed=seed, event_store=None,
            llm=llm, model=model, surrogate="epistasis", no_knowledge=True,
        )
        _append_agent_trace(store, no_knowledge, seed=seed)
        trials.append({**no_knowledge, "seed": seed})
        knowledge = run_autoresearch(
            spec, budget=budget, n_rounds=n_rounds, seed=seed, event_store=None,
            llm=llm, model=model, surrogate="epistasis", guardrail=True,
            max_hd=max_hd, blosum_min=blosum_min,
        )
        _append_agent_trace(store, knowledge, seed=seed)
        trials.append({**knowledge, "seed": seed})
    summary, rejected = _summarise(spec, trials, matrix, max_hd=max_hd,
                                   blosum_min=blosum_min)
    negative_control = _run_negative_control(spec)
    v07_anchor = _run_v07_anchor(spec, matrix, budget=budget, n_rounds=n_rounds)
    result = {
        "schema_version": "knowledge-ablation.v1",
        "dataset": "AAV FLIP clean substitution subset",
        "protocol": {
            "seeds": list(seeds), "budget_per_round": budget, "n_rounds": n_rounds,
            "total_budget": budget * n_rounds, "cold_start": "HD <= 2",
            "candidate_pool": "same source pool HD > 2; only the knowledge treatment applies HD/BLOSUM filtering",
            "surrogate": "EpistasisRidgePredictor",
            "oracle": "measured-table lookup after nomination",
            "llm_requested": llm, "model": model,
            "max_hd": max_hd, "blosum_min": blosum_min,
            "resume_from": None if resume_from is None else str(resume_from),
        },
        "v07_entry_anchor": v07_anchor,
        "negative_control": negative_control,
        "summary": summary,
        "trials": trials,
        "artifacts": {"events": event_path.name, "rejected_candidates": "rejected_candidates.json",
                      "figure": "knowledge_ablation.png"},
    }
    metrics_path = out_dir / "metrics.json"
    rejected_path = out_dir / "rejected_candidates.json"
    figure_path = out_dir / "knowledge_ablation.png"
    metrics_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rejected_path.write_text(json.dumps(rejected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _plot(summary, figure_path)
    store.verify()
    print(f"[out] {metrics_path}")
    print(f"[out] {event_path} events={sum(1 for _ in store.iter_events())} head={store.head_hash}")
    print(f"[out] {rejected_path} n={len(rejected)}")
    print(f"[out] {figure_path}")
    print(json.dumps({"negative_control": negative_control, "summary": summary}, ensure_ascii=False))
    return result


def _parse_seeds(raw: str) -> tuple[int, ...]:
    return tuple(int(value.strip()) for value in raw.split(",") if value.strip())


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser(description="AAV knowledge ablation and four-strategy runner")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seeds", default="0,1,2")
    parser.add_argument("--budget", type=int, default=48)
    parser.add_argument("--n-rounds", type=int, default=6)
    parser.add_argument("--no-llm", action="store_true",
                        help="use the deterministic AutoResearch fallback and record llm_requested=false")
    parser.add_argument("--model", default=None)
    parser.add_argument("--resume-from", type=Path, default=None,
                        help="reuse completed seed trials from a compatible checkpoint directory")
    args = parser.parse_args(argv)
    return run(out_dir=args.out_dir, seeds=_parse_seeds(args.seeds), budget=args.budget,
               n_rounds=args.n_rounds, llm=not args.no_llm, model=args.model,
               resume_from=args.resume_from)


if __name__ == "__main__":
    main()
