"""Four-strategy GB1 active-learning campaign (T7 — 题目⑤⑥核心).

Four strategies share one budget, one oracle and one nomination space:

  ① random             — multi-seed random nomination (baseline, reuses T1).
  ② greedy             — Ridge ladder scores the *entire* unmeasured space,
                          take top-budget by predicted mean (brute force).
  ③ agent_no_knowledge — the five-role agent pipeline (agent.pipeline.run_pipeline)
                          proposes a *focused* combinatorial library from the
                          best observed substitutions, ranked by predicted mean.
                          Knowledge base OFF (--no-knowledge ablation).
  ④ knowledge_agent    — same pipeline, plus domain knowledge: UCB exploration
                          (mean + λ·√var) and a BLOSUM62 conservativeness prior
                          from the T5 knowledge base. Ablating both recovers ③.

The oracle is always a lookup in the measured GB1 table — never a model score.
The LLM hypothesis port is injected only in --use-llm mode (backed by our
OpenAI-compatible pool, see agent/llm.py); the headline run is deterministic and
reproducible, and every round records which source it used so a reader can tell
a live LLM apart from the deterministic fallback.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from evolution.random_baseline import (BUDGET, N_ROUNDS, POOL_SIZE, TOP_K, WT,
                                        build_cold_start_pool, load_landscape, propose_random)
from agent.pipeline import Hypothesis, run_pipeline
from agent.llm import chat_json, llm_config
from knowledge.validators import load_rules

from evolution.results_layout import run_dir

ROOT = Path(__file__).resolve().parents[1]
# GB1 four-strategy campaign lives on the workflow line; the four regimes
# (easy/hard/llm/sparse) are produced by passing --out-json/--out-fig/--out-events
# explicitly. Default is the easy (random-pool) regime.
_GB1 = run_dir("workflow", "gb1")
OUT_JSON = _GB1 / "campaign_easy.metrics.json"
OUT_FIG = _GB1 / "figures" / "campaign_easy.png"
STRATEGIES = ("random", "greedy", "agent_no_knowledge", "knowledge_agent")
SITES = (39, 40, 41, 54)              # GB1 mutable positions, aligned to WT="VDGV"
AA = "ACDEFGHIKLMNPQRSTVWY"
K_PER_SITE = 8                        # top observed substitutions per site fed to the designer
LIBRARY_CAP = 10000                   # designer enumerates the full hypothesis combinatorial (≤ (K+1)^4 = 6561);
                                      # high enough to avoid truncating the library before the predictor can rank it
LAMBDA_UCB = 0.75                     # exploration weight for the knowledge agent
BETA_BLOSUM = 0.30                    # BLOSUM62 conservativeness prior weight
RANDOM_SEEDS = (11, 23, 42, 67, 89)  # fixed independent baseline repetitions


def _features(variants: list[str]) -> np.ndarray:
    lut = {c: i for i, c in enumerate(AA)}
    x = np.zeros((len(variants), 80), dtype=float)
    for row, seq in enumerate(variants):
        for pos, char in enumerate(seq):
            x[row, pos * 20 + lut[char]] = 1.0
    return x


def _variant_to_muts(variant: str) -> list[str]:
    """A 4-char variant string -> WT-anchored mutation notation, e.g. 'FDGV' -> ['V39F']."""
    return [f"{WT[i]}{SITES[i]}{c}" for i, c in enumerate(variant) if c != WT[i]]


def _pool_records(train: pd.DataFrame) -> list[dict]:
    return [{"mutations": _variant_to_muts(v), "fitness": float(f)}
            for v, f in zip(train.Variants, train.Fitness)]


def _blosum_lookup(rules: dict):
    matrix = rules["blosum62"]
    def score(a: str, b: str) -> int:
        if a == b:
            return 4
        return matrix.get(a, {}).get(b, matrix.get(b, {}).get(a, 0))
    return score


def _blosum_prior(variant: str, score) -> float:
    """Mean BLOSUM62 score of a variant's substitutions vs WT, scaled to ~[-1, 1].

    Higher = more conservative substitutions = the knowledge base's soft preference.
    """
    subs = [(WT[i], c) for i, c in enumerate(variant) if c != WT[i]]
    if not subs:
        return 0.0
    return float(np.mean([score(a, b) for a, b in subs])) / 4.0


def _predictor_factory(seeds: int = 5):
    from models.train_ladder import RidgePredictor
    return RidgePredictor(seeds=seeds)


def _deterministic_hypothesis(train: pd.DataFrame, k_per_site: int = K_PER_SITE):
    """Rank substitutions per site by observed mean fitness; return a hypothesis fn.

    This is the deterministic stand-in for the LLM Hypothesis Generator: it reads
    the Data Analyst's evidence (the training pool) and proposes the substitutions
    most worth combining. The agent pipeline turns them into a combinatorial library.
    """
    tally: dict[tuple[int, str], list[float]] = {}
    for v, f in zip(train.Variants, train.Fitness):
        for i, c in enumerate(v):
            if c != WT[i]:
                tally.setdefault((SITES[i], c), []).append(float(f))
    ranked: dict[int, list[str]] = {}
    for (site, aa), fits in tally.items():
        ranked.setdefault(site, []).append((aa, float(np.mean(fits))))
    muts: list[str] = []
    for idx, site in enumerate(SITES):
        for aa, _ in sorted(ranked.get(site, []), key=lambda t: -t[1])[:k_per_site]:
            muts.append(f"{WT[idx]}{site}{aa}")

    def fn(report):  # noqa: ARG001 — report is available but evidence already summarised here
        return Hypothesis(mutations=muts,
                          rationale="Top observed substitutions per site under R-GB1-SITES / R-MAX-MUTATIONS.",
                          rule_ids=["R-GB1-SITES", "R-MAX-MUTATIONS"])
    return fn, muts


def _llm_hypothesis(fallback_fn, fallback_muts, state: dict):
    """LLM Hypothesis Generator (our pool) with deterministic fallback.

    Calls the pool once with the per-site substitution menu and asks which
    substitutions to prioritise. On any error (no key, network, malformed reply)
    it falls back to the deterministic ranking and records the source in ``state``
    for honest reporting — the headline comparison never depends on the network.
    """
    menu = sorted(set(fallback_muts))
    allowed = set(fallback_muts)

    def fn(report):
        try:
            prompt = ("You are the Hypothesis Generator of a GB1 directed-evolution agent. "
                      "GB1 has four mutable sites V39/D40/G41/V54 (wild type VDGV). "
                      f"Observed candidate substitutions: {menu}. "
                      "Pick the most promising substitutions to combine into a mutant library. "
                      "Reply with a JSON array of substitution strings (e.g. [\"V39F\", \"D40A\"]) and nothing else.")
            text = chat_json(prompt).strip()
            text = text[text.find("["): text.rfind("]") + 1]
            picks = [str(m) for m in json.loads(text) if str(m) in allowed]
            if not picks:
                raise ValueError("LLM returned no usable substitutions")
            state["source"] = f"llm:{(llm_config() or {}).get('model', '?')}"
            return Hypothesis(mutations=picks,
                              rationale="LLM-proposed substitutions grounded in R-GB1-SITES.",
                              rule_ids=["R-GB1-SITES", "R-MAX-MUTATIONS"])
        except Exception as exc:  # noqa: BLE001 — any failure degrades to the offline generator
            state["source"] = "fallback"
            state["error"] = str(exc)[:200]
            return fallback_fn(report)
    return fn


def _llm_critic(state: dict):
    """Optional live critic port; failures remain an explicit deterministic fallback."""
    def fn(candidate, rules):
        try:
            prompt = ("Act as a GB1 scientific critic. Briefly assess this candidate and "
                      f"its rule checks: candidate={candidate.model_dump()}, rules={rules}")
            note = chat_json(prompt).strip()
            state["critic_source"] = f"llm:{(llm_config() or {}).get('model', '?')}"
            return note
        except Exception as exc:  # noqa: BLE001 — campaign must remain runnable offline
            state["critic_source"] = "fallback"
            state["critic_error"] = str(exc)[:200]
            return "accepted by deterministic rule checks (LLM critic fallback)"
    return fn


def _stats(batch: pd.DataFrame, cumulative: pd.DataFrame) -> dict:
    top = batch.nlargest(TOP_K, "Fitness", keep="first")
    ctop = cumulative.nlargest(TOP_K, "Fitness", keep="first")
    hits = int((batch["Fitness"] > 1.0).sum())          # beneficial vs wild type (fitness > 1)
    strong = int((cumulative["Fitness"] >= 4.0).sum())  # cumulative strong binders
    return {"n_nominated": len(batch),
            "top10_max": round(float(top.Fitness.max()), 6),
            "top10_mean": round(float(top.Fitness.mean()), 6),
            "n_hit_beneficial": hits,
            "hit_rate_beneficial": round(hits / len(batch), 6),
            "cum_top10_max": round(float(ctop.Fitness.max()), 6),
            "cum_top10_mean": round(float(ctop.Fitness.mean()), 6),
            "cum_n_strong": strong,
            "top10": [[str(v), round(float(f), 6)] for v, f in zip(top.Variants, top.Fitness)]}


def _event(store, event_type, strategy, round_id, payload):
    if store is not None:
        store.append(event_type, round_id=round_id, strategy=strategy, actor="campaign", payload=payload)


def _agent_propose(strategy, df, measured, train, budget, event_store, round_id,
                   blosum_score, use_llm, llm_state):
    """Strategies ③④: propose through the five-role agent pipeline, then select
    top-budget by the acquisition function among measurable, unmeasured candidates."""
    predictor = _predictor_factory()
    predictor.fit(_features(train.Variants.tolist()), train.Fitness.to_numpy())

    def agent_predictor(seqs):
        return predictor.predict(_features(list(seqs)))

    det_fn, det_muts = _deterministic_hypothesis(train)
    hyp_fn = _llm_hypothesis(det_fn, det_muts, llm_state) if use_llm else det_fn

    result = run_pipeline(_pool_records(train), agent_predictor,
                          llm_hypothesis=hyp_fn,
                          llm_critic=_llm_critic(llm_state) if use_llm else None,
                          budget=LIBRARY_CAP, event_store=event_store,
                          round_id=round_id,
                          no_knowledge=(strategy == "agent_no_knowledge"))

    known = set(df.Variants)
    rows = []
    for c in result.candidates:
        seq = c.sequence
        if seq in measured or seq not in known:
            continue
        acq = c.mean
        if strategy == "knowledge_agent":
            acq = c.mean + LAMBDA_UCB * float(np.sqrt(max(c.variance, 0.0))) + BETA_BLOSUM * _blosum_prior(seq, blosum_score)
        rows.append((acq, seq))
    if not rows:
        return np.array([], dtype=object)
    # Deterministic ordering: acquisition desc, then sequence for stable tie-breaking.
    rows.sort(key=lambda t: (-t[0], t[1]))
    return np.array([seq for _, seq in rows[:budget]], dtype=object)


def _greedy_propose(df, measured, train, budget):
    predictor = _predictor_factory()
    predictor.fit(_features(train.Variants.tolist()), train.Fitness.to_numpy())
    cand = df.loc[~df.Variants.isin(measured), "Variants"].to_numpy()
    mean, _ = predictor.predict(_features(cand.tolist()))
    order = np.lexsort((cand, -mean))  # mean desc, sequence tie-break
    return cand[order[:budget]]


def _topk_concentration(rounds: list[dict]) -> dict:
    """Residue concentration among all reported per-round Top-k nominations."""
    variants = [variant for row in rounds for variant, _ in row["top10"]]
    positions = {}
    for index, site in enumerate(SITES):
        counts: dict[str, int] = {}
        for variant in variants:
            counts[variant[index]] = counts.get(variant[index], 0) + 1
        total = len(variants)
        ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        positions[str(site)] = {
            "residue_counts": dict(ordered),
            "dominant_residue": ordered[0][0] if ordered else None,
            "dominant_fraction": round(ordered[0][1] / total, 6) if total else 0.0,
            "mutation_fraction": round(sum(n for aa, n in ordered if aa != WT[index]) / total, 6)
                                 if total else 0.0,
        }
    return {"n_topk_observations": len(variants), "positions": positions}


def _aggregate_random_runs(runs: list[dict]) -> dict:
    """Attach across-seed mean/std curves computed from genuinely independent runs."""
    metrics = ("top10_max", "top10_mean", "hit_rate_beneficial",
               "cum_top10_max", "cum_top10_mean", "cum_n_strong")
    aggregate = []
    for index in range(len(runs[0]["rounds"])):
        row = {"round": index + 1}
        for metric in metrics:
            values = np.asarray([run["rounds"][index][metric] for run in runs], dtype=float)
            row[f"{metric}_mean"] = round(float(values.mean()), 6)
            row[f"{metric}_std"] = round(float(values.std(ddof=0)), 6)
        aggregate.append(row)
    return {"seeds": [run["seed"] for run in runs], "n_runs": len(runs), "rounds": aggregate}


def _run_strategy(strategy, df, *, seed, n_rounds, budget, pool_size, event_store,
                  use_llm, cold_start, max_cold_hd, blosum_score):
    rng = np.random.default_rng(seed)
    if cold_start == "low_hd":
        pool = df[df.HD <= max_cold_hd][["Variants", "HD", "Fitness"]].copy()
    else:
        pool = build_cold_start_pool(df, rng, pool_size)
    measured = set(pool.Variants)
    train = pool[["Variants", "Fitness"]].copy()
    rounds, batches, sources = [], [], []
    _event(event_store, "campaign.started", strategy, 0,
           {"budget": budget, "pool_size": len(pool), "seed": seed})
    oracle = df.set_index("Variants")
    for round_id in range(1, n_rounds + 1):
        llm_state: dict = {"source": "fallback"}
        if strategy == "random":
            cand = df.loc[~df.Variants.isin(measured), "Variants"].to_numpy()
            picks = propose_random(cand, budget, rng)
        elif strategy == "greedy":
            picks = _greedy_propose(df, measured, train, budget)
        else:
            picks = _agent_propose(strategy, df, measured, train, budget,
                                   event_store, round_id, blosum_score, use_llm, llm_state)
        if len(picks) == 0:
            break
        _event(event_store, "campaign.propose.completed", strategy, round_id,
               {"seed": seed, "n_candidates": len(picks), "variants": picks.tolist()})
        batch = oracle.loc[picks].reset_index()
        batch["Fitness"] = pd.to_numeric(batch["Fitness"], errors="raise").astype(float)
        _event(event_store, "campaign.oracle.completed", strategy, round_id,
               {"seed": seed, "oracle": "measured table lookup", "n_lookups": len(batch)})
        measured.update(picks.tolist())
        train = pd.concat([train, batch[["Variants", "Fitness"]]], ignore_index=True)
        train["Fitness"] = pd.to_numeric(train["Fitness"], errors="raise").astype(float)
        _event(event_store, "campaign.refill.completed", strategy, round_id,
               {"seed": seed, "added": len(batch), "pool_size_after": len(train)})
        if strategy != "random":
            refreshed = _predictor_factory()
            refreshed.fit(_features(train.Variants.tolist()), train.Fitness.to_numpy())
        _event(event_store, "campaign.retrain.completed", strategy, round_id,
               {"seed": seed, "training_rows": len(train),
                "status": "not applicable" if strategy == "random" else "fitted",
                "predictor": "none (random baseline)" if strategy == "random" else "5-seed Ridge ensemble"})
        batches.append(batch)
        cumulative = pd.concat(batches, ignore_index=True)
        cumulative["Fitness"] = pd.to_numeric(cumulative["Fitness"], errors="raise").astype(float)
        row = {"round": round_id, **_stats(batch, cumulative), "pool_size_after": len(train)}
        if strategy in ("agent_no_knowledge", "knowledge_agent"):
            row["llm_source"] = llm_state.get("source", "fallback")
            row["llm_critic_source"] = llm_state.get("critic_source", "fallback")
            sources.append(row["llm_source"])
        rounds.append(row)
        _event(event_store, "campaign.round.completed", strategy, round_id, row)
    result = {
        "strategy": strategy, "seed": seed, "n_rounds": len(rounds),
        "budget_per_round": budget, "cold_start_pool_size": len(pool),
        "acquisition": {"random": "uniform random",
                        "greedy": "predicted mean over full unmeasured space",
                        "agent_no_knowledge": "agent library, predicted mean",
                        "knowledge_agent": f"agent library, mean + {LAMBDA_UCB}·√var + {BETA_BLOSUM}·BLOSUM62 prior"}[strategy],
        "llm_sources": sources or None, "rounds": rounds,
        "topk_concentration": _topk_concentration(rounds),
    }
    _event(event_store, "campaign.completed", strategy, len(rounds),
           {"seed": seed, "rounds": rounds})
    return result


def run_campaign(df: pd.DataFrame | None = None, *, seed: int = 42, n_rounds: int = N_ROUNDS,
                 budget: int = BUDGET, pool_size: int = POOL_SIZE, event_store=None,
                 use_llm: bool = False, cold_start: str = "random", max_cold_hd: int = 2) -> dict:
    """Run all four strategies.

    cold_start:
      "random"  — seed pool = ``pool_size`` uniformly random measured variants.
                  Because random 4-site variants are almost all HD=4, this pool
                  already densely samples the high-order space near the peak, so
                  the predictor is strong from round 0 (the "easy" regime).
      "low_hd"  — seed pool = every measured variant with Hamming distance
                  ≤ ``max_cold_hd`` from wild type. The nomination space is then
                  the higher-order mutants (HD > max_cold_hd), so the campaign must
                  EXTRAPOLATE outward to reach the HD=4 peak — the realistic and
                  much harder directed-evolution regime.
    """
    df = load_landscape() if df is None else df.copy()
    if df.empty:
        raise ValueError("measured landscape cannot be empty")
    if "HD" not in df.columns:
        df["HD"] = [sum(a != b for a, b in zip(v, WT)) for v in df.Variants]
    blosum_score = _blosum_lookup(load_rules())
    all_results: dict[str, dict] = {}
    for strategy in STRATEGIES:
        strategy_seeds = RANDOM_SEEDS if strategy == "random" else (seed,)
        runs = [_run_strategy(strategy, df, seed=run_seed, n_rounds=n_rounds,
                              budget=budget, pool_size=pool_size, event_store=event_store,
                              use_llm=use_llm, cold_start=cold_start,
                              max_cold_hd=max_cold_hd, blosum_score=blosum_score)
                for run_seed in strategy_seeds]
        all_results[strategy] = runs[RANDOM_SEEDS.index(42)] if strategy == "random" else runs[0]
        if strategy == "random":
            all_results[strategy]["multi_seed"] = _aggregate_random_runs(runs)
    return {"schema_version": "t7.v2",
            "candidate_space_size": len(df),
            "missing_combinations": max(0, 160000 - len(df)),
            "oracle": "measured table lookup",
            "budget_per_round": budget, "n_rounds": n_rounds,
            "cold_start": (f"low_hd (seed pool = all HD<={max_cold_hd}, nominate HD>{max_cold_hd}: extrapolation regime)"
                           if cold_start == "low_hd"
                           else f"random ({pool_size} uniform variants; ~98% HD>=3: easy regime)"),
            "llm": (f"pool {(llm_config() or {}).get('model', '?')} via injectable hypothesis port"
                    if use_llm else "deterministic (pool LLM port available via --use-llm)"),
            "summary": _summary(all_results),
            "strategies": all_results}


def _summary(results: dict) -> dict:
    """Sample-efficiency view: what each strategy reaches under the same budget."""
    out = {}
    for name, r in results.items():
        rounds = r["rounds"]
        if not rounds:
            continue
        out[name] = {
            "final_cum_top10_max": rounds[-1]["cum_top10_max"],
            "final_cum_top10_mean": rounds[-1]["cum_top10_mean"],
            "final_cum_n_strong": rounds[-1]["cum_n_strong"],
            "total_beneficial_hits": sum(x["n_hit_beneficial"] for x in rounds),
            "cum_top10_max_curve": [x["cum_top10_max"] for x in rounds]}
    return out


def plot_campaign(report: dict, path: Path = OUT_FIG) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for strategy, result in report["strategies"].items():
        rounds = result["rounds"]
        if rounds:
            ax.plot([r["round"] for r in rounds], [r["cum_top10_max"] for r in rounds],
                    marker="o", label=strategy)
            if strategy == "random":
                aggregate = result["multi_seed"]["rounds"]
                x = np.asarray([r["round"] for r in aggregate])
                mean = np.asarray([r["cum_top10_max_mean"] for r in aggregate])
                std = np.asarray([r["cum_top10_max_std"] for r in aggregate])
                ax.fill_between(x, mean - std, mean + std, alpha=.2, label="random ±1 std")
    ax.set(xlabel="round", ylabel="cumulative top-10 max true fitness",
           title=f"GB1 four-strategy campaign (budget={report.get('budget_per_round')}/round)")
    ax.grid(axis="y", alpha=.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main(argv: list[str] | None = None) -> dict:
    p = argparse.ArgumentParser(description="GB1 four-strategy active-learning campaign")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--cold-start", choices=("random", "low_hd"), default="random",
                   help="'random' = dense random seed pool (easy); 'low_hd' = seed from HD<=max-cold-hd only, extrapolate outward (hard)")
    p.add_argument("--max-cold-hd", type=int, default=2, help="for --cold-start low_hd: max Hamming distance in the seed pool")
    p.add_argument("--use-llm", action="store_true", help="inject the pool LLM into the agent hypothesis port")
    p.add_argument("--out-json", type=Path, default=OUT_JSON)
    p.add_argument("--out-fig", type=Path, default=OUT_FIG)
    p.add_argument("--out-events", type=Path, default=_GB1 / "campaign_easy.events.jsonl")
    args = p.parse_args(argv)

    from events.store import EventStore
    if args.out_events.exists():
        args.out_events.unlink()  # fresh hash chain; never append onto a stale stream
    store = EventStore(args.out_events)
    report = run_campaign(seed=args.seed, use_llm=args.use_llm, event_store=store,
                          cold_start=args.cold_start, max_cold_hd=args.max_cold_hd)
    store.verify()  # the audit chain must be intact before we publish it
    n_events = sum(1 for _ in store.iter_events())

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    plot_campaign(report, args.out_fig)
    print(f"[out] {args.out_json}\n[out] {args.out_fig}\n[out] {args.out_events} "
          f"({n_events} events, head {store.head_hash[:12]})")
    for name, s in report["summary"].items():
        print(f"  {name:20s} cum_top10_max={s['final_cum_top10_max']} "
              f"cum_top10_mean={s['final_cum_top10_mean']} strong={s['final_cum_n_strong']} "
              f"hits={s['total_beneficial_hits']}")

    # Every run appends an immutable entry to the master experiment ledger (never overwritten).
    from evolution.experiment_log import log_run
    rel = lambda pth: str(Path(pth).resolve().relative_to(ROOT))  # noqa: E731
    entry = log_run("campaign",
                    command=f"python -m evolution.campaign --seed {args.seed} --cold-start {args.cold_start}"
                            + (f" --max-cold-hd {args.max_cold_hd}" if args.cold_start == "low_hd" else "")
                            + (" --use-llm" if args.use_llm else ""),
                    params={"seed": args.seed, "cold_start": args.cold_start,
                            "max_cold_hd": args.max_cold_hd, "use_llm": args.use_llm,
                            "budget": report["budget_per_round"], "n_rounds": report["n_rounds"]},
                    artifacts=[rel(args.out_json), rel(args.out_events), rel(args.out_fig)],
                    summary={k: {"cum_top10_max": v["final_cum_top10_max"],
                                 "cum_n_strong": v["final_cum_n_strong"],
                                 "total_beneficial_hits": v["total_beneficial_hits"]}
                             for k, v in report["summary"].items()})
    print(f"[ledger] experiment_log.jsonl <- seq {entry['seq']} ({report['cold_start'].split(' ')[0]})")
    return report


if __name__ == "__main__":
    main()
