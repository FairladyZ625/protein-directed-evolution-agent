"""Agentic AutoResearch agent — the LLM autonomously runs the directed-evolution loop.

Unlike the fixed five-role workflow (evolution/campaign.py, evolution/pool_campaign.py),
here the LLM is the researcher. It is given a set of tools and a finite experiment
budget and *decides for itself* what to analyse, what to predict, whether to exploit
the surrogate's top picks or explore uncertain / knowledge-plausible regions, when to
spend budget on real measurements, and how to adapt after seeing results. This is a
genuine pydantic-ai tool-calling agent, not a hardcoded schedule.

The oracle is still a measured-table lookup, so the agent can only *test* variants that
exist in the withheld pool — the campaign is pool-based active learning; the agent's
freedom is which pool variants to measure, guided by its own reasoning.

Fair comparison: same total budget (budget × n_rounds), same pool, same oracle as
greedy / workflow. If the pool LLM is unavailable, a deterministic exploit/explore
fallback runs instead (recorded as llm_used=False), so the module never hard-fails.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from evolution.pool_campaign import DatasetSpec, _stats
from models.train_ladder import RidgePredictor
from knowledge.validators import validate_candidate

ROOT = Path(__file__).resolve().parents[1]

SYSTEM_PROMPT = """You are an autonomous protein-engineering researcher running a directed-evolution campaign.

Goal: within a FIXED budget of real experiments, discover variants with the highest possible
fitness. You start with a set of already-measured low-order variants; a large pool of
higher-order variants is UNMEASURED and can only be evaluated by spending budget via the
`test` tool (that is the real experiment; its result is ground truth).

Important: a surrogate predictor is available via `predict`/`list_pool`, but it is IMPERFECT
(rank correlation only ~0.6 and it systematically underrates high-order epistatic peaks).
Do NOT blindly test its top predictions every round. Think like a scientist: inspect what is
measured, form hypotheses about which positions/substitutions matter, and BALANCE exploiting
predicted-good variants against EXPLORING high-uncertainty or knowledge-plausible variants the
predictor may underrate. Adapt after each batch of results.

Workflow each cycle: call `analyze_measured` and `best_so_far` to see the state; use
`list_pool` (try different `by` strategies) and `predict`/`check_knowledge` to choose
candidates; then `test` a batch to spend budget and learn. Repeat until the budget is
exhausted, then briefly summarise the best variants you found and your strategy."""


def run_autoresearch(spec: DatasetSpec, *, budget: int = 96, n_rounds: int = 3,
                     seed: int = 42, event_store=None, llm: bool = True,
                     request_limit: int = 60, model: str | None = None) -> dict:
    fit_col = spec.fitness_col
    total_budget = budget * n_rounds
    strong_thr = float(np.quantile(spec.df[fit_col], 0.9))
    rng = np.random.default_rng(seed)

    state = {
        "measured": spec.df[spec.df.hd <= 2].copy(),
        "pool": spec.df[spec.df.hd > 2].copy(),
        "spent": 0,
        "batches": [],            # each test() batch as a DataFrame(seq, fitness)
        "trace": [],
        "pred_cache": None,       # (model, mean, var) valid until measured changes
    }

    def emit(kind, actor, payload):
        state["trace"].append({"event_type": kind, "actor": actor, "payload": payload})
        if event_store is not None:
            event_store.append(kind, round_id=len(state["batches"]) + 1,
                               strategy="agentic", actor=actor, payload=payload)

    def _pool_scores():
        """Fit predictor on current measured set and score the whole pool; cached."""
        if state["pred_cache"] is None and not state["pool"].empty:
            model = RidgePredictor(seeds=3).fit(
                spec.feature_fn(state["measured"].seq.tolist()),
                state["measured"][fit_col].to_numpy())
            mean, var = model.predict(spec.feature_fn(state["pool"].seq.tolist()))
            state["pred_cache"] = (np.asarray(mean), np.asarray(var))
        return state["pred_cache"]

    # ---- tools ---------------------------------------------------------------
    def analyze_measured() -> dict:
        """Summarise the measured set: count, best variants so far, and the substitutions
        most enriched among high-fitness measured variants (the 'hypothesis' material)."""
        m = state["measured"]
        top = m.nlargest(8, fit_col)
        # per-(position, residue) mean fitness among measured, top few
        tally: dict[str, list[float]] = {}
        for s, f in zip(m.seq, m[fit_col]):
            for i, (c, w) in enumerate(zip(s, spec.wt)):
                if c != w:
                    tally.setdefault(f"{w}{i}{c}", []).append(float(f))
        enriched = sorted(((k, float(np.mean(v))) for k, v in tally.items() if len(v) >= 3),
                          key=lambda t: -t[1])[:12]
        out = {"n_measured": len(m), "n_pool_unmeasured": len(state["pool"]),
               "budget_remaining": total_budget - state["spent"],
               "best_measured": [[str(s), round(float(f), 3)] for s, f in zip(top.seq, top[fit_col])],
               "top_enriched_substitutions": [[k, round(v, 3)] for k, v in enriched]}
        emit("agent.tool.analyze_measured", "data_analyst", out)
        return out

    def predict(variants: list[str]) -> list[list[float]]:
        """Return the surrogate's [mean, uncertainty] for the given pool variants (imperfect)."""
        scores = _pool_scores()
        if scores is None:
            return []
        idx = {s: i for i, s in enumerate(state["pool"].seq)}
        mean, var = scores
        out = [[round(float(mean[idx[v]]), 3), round(float(var[idx[v]]), 6)] if v in idx else [0.0, 0.0]
               for v in variants]
        emit("agent.tool.predict", "fitness_evaluator", {"n": len(variants)})
        return out

    def list_pool(n: int = 20, by: str = "predicted_mean") -> list[str]:
        """Sample up to n candidate variants from the UNMEASURED pool.
        by: 'predicted_mean' (exploit), 'uncertainty' (explore), 'random', or 'diverse'."""
        if state["pool"].empty:
            return []
        n = int(max(1, min(n, 60)))
        scores = _pool_scores()
        mean, var = scores
        if by == "predicted_mean":
            order = np.argsort(-mean)
        elif by == "uncertainty":
            order = np.argsort(-var)
        elif by == "diverse":
            order = np.argsort(-(mean + 3.0 * np.sqrt(np.maximum(var, 0)) + rng.random(len(mean))))
        else:
            order = rng.permutation(len(state["pool"]))
        picks = state["pool"].iloc[order[:n]].seq.tolist()
        emit("agent.tool.list_pool", "hypothesis_generator", {"by": by, "n": len(picks)})
        return picks

    def check_knowledge(variants: list[str]) -> dict:
        """Knowledge-base assessment (mutation rules + BLOSUM62) for the given variants."""
        out = {}
        for v in variants[:40]:
            muts = [f"{w}{i}{c}" for i, (c, w) in enumerate(zip(v, spec.wt)) if c != w]
            checks = validate_candidate(muts)
            out[v] = {"ok": all(x["pass"] for x in checks),
                      "fail": [x["rule_id"] for x in checks if not x["pass"]]}
        emit("agent.tool.check_knowledge", "scientific_critic", {"n": len(out)})
        return out

    def test(variants: list[str]) -> dict:
        """Spend budget: measure the true fitness of these pool variants (real experiment).
        Only variants present in the unmeasured pool can be measured. Returns results,
        remaining budget, and the running best. When budget is exhausted, stop."""
        remaining = total_budget - state["spent"]
        if remaining <= 0:
            return {"status": "budget_exhausted", "budget_remaining": 0}
        chosen = list(dict.fromkeys(variants))[:remaining]
        rows = state["pool"][state["pool"].seq.isin(chosen)].copy()
        state["measured"] = pd.concat([state["measured"], rows], ignore_index=True)
        state["pool"] = state["pool"].drop(rows.index)
        state["pred_cache"] = None  # measured changed -> refit next time
        state["spent"] += len(rows)
        if len(rows):
            state["batches"].append(rows[["seq", fit_col]].rename(columns={fit_col: "fitness"}))
        best = state["measured"].nlargest(1, fit_col).iloc[0]
        results = [[str(s), round(float(f), 3)] for s, f in zip(rows.seq, rows[fit_col])]
        out = {"status": "ok", "n_measured_now": len(rows),
               "results": results, "budget_remaining": total_budget - state["spent"],
               "running_best": [str(best.seq), round(float(best[fit_col]), 3)]}
        emit("agent.tool.test", "experiment", {"requested": len(chosen), "measured": len(rows),
                                               "spent": state["spent"],
                                               "batch_max": round(float(rows[fit_col].max()), 3) if len(rows) else None})
        return out

    def best_so_far() -> list:
        """Return the single best variant measured so far as [sequence, fitness]."""
        best = state["measured"].nlargest(1, fit_col).iloc[0]
        return [str(best.seq), round(float(best[fit_col]), 3)]

    # ---- run: LLM-driven, with deterministic fallback ------------------------
    llm_used = False
    llm_summary = None
    agent_model = None
    if llm:
        try:
            from pydantic_ai import Agent
            try:
                from pydantic_ai.models.openai import OpenAIChatModel as OAModel
            except ImportError:
                from pydantic_ai.models.openai import OpenAIModel as OAModel
            from pydantic_ai.providers.openai import OpenAIProvider
            from agent.llm import llm_config
            cfg = llm_config()
            if cfg is None:
                raise RuntimeError("no LLM credentials")
            model_id = model or cfg["model"]
            oa = OAModel(model_id, provider=OpenAIProvider(base_url=cfg["base_url"], api_key=cfg["api_key"]))
            ag = Agent(oa, system_prompt=SYSTEM_PROMPT)
            agent_model = model_id
            emit("agent.llm.model", "agent", {"model": model_id, "base_url": cfg["base_url"]})
            for fn in (analyze_measured, predict, list_pool, check_knowledge, test, best_so_far):
                ag.tool_plain(fn)
            kwargs = {}
            try:
                from pydantic_ai.usage import UsageLimits
                kwargs["usage_limits"] = UsageLimits(request_limit=20)  # per-round cap
            except Exception:  # noqa: BLE001
                pass
            # Bounded autonomous loop: each round the LLM MUST spend budget via `test`
            # (analysis alone makes no progress); it chooses which variants and the
            # explore/exploit balance itself. Message history carries strategy across rounds.
            history = None
            for rnd in range(1, n_rounds + 1):
                remaining = total_budget - state["spent"]
                if remaining <= 0 or state["pool"].empty:
                    break
                this_batch = min(budget, remaining)
                spent_before = state["spent"]
                prompt = (f"Round {rnd} of {n_rounds}. Budget remaining: {remaining}. "
                          f"Analyse with the tools, then you MUST call `test` this round on a batch of about "
                          f"{this_batch} pool variants — analysis alone makes no progress and wastes the round. "
                          f"Deliberately mix exploitation (high predicted mean) with exploration "
                          f"(high uncertainty / knowledge-plausible variants the surrogate may underrate). "
                          f"After testing, note what you learned for the next round.")
                try:
                    result = ag.run_sync(prompt, message_history=history, **kwargs)
                    history = result.all_messages()
                    llm_summary = str(getattr(result, "output", ""))[:800]
                except Exception as exc:  # noqa: BLE001
                    emit("agent.llm.round_error", "agent", {"round": rnd, "error": str(exc)[:200]})
                # Guarantee progress: if the LLM analysed but did not test, the harness
                # spends this round's budget on its own exploit pick (recorded honestly).
                if state["spent"] == spent_before and not state["pool"].empty:
                    emit("agent.llm.no_test", "agent", {"round": rnd, "note": "LLM skipped test; harness exploit fill"})
                    test(list_pool(this_batch, "predicted_mean"))
            llm_used = True
        except Exception as exc:  # noqa: BLE001 — degrade to deterministic driver
            emit("agent.llm.fallback", "agent", {"error": str(exc)[:200]})

    if not llm_used:
        # Deterministic fallback: alternate exploit / explore until budget is spent.
        for rnd in range(n_rounds):
            if state["pool"].empty or state["spent"] >= total_budget:
                break
            by = "predicted_mean" if rnd % 2 == 0 else "diverse"
            analyze_measured()
            picks = list_pool(budget, by)
            check_knowledge(picks)
            test(picks)

    # ---- assemble report (cumulative over all tested batches) ----------------
    rounds = []
    seen = []
    for i, batch in enumerate(state["batches"], 1):
        seen.append(batch)
        cum = pd.concat(seen, ignore_index=True)
        rounds.append({"round": i, **_stats(batch, cum, "fitness", strong_thr),
                       "spent_after": int(cum.shape[0])})
    return {"schema_version": "pool.v1", "dataset": spec.name, "strategy": "agentic",
            "nomination": "LLM-driven tool-calling active learning (pool-based)",
            "oracle": "measured table lookup", "wild_type": spec.wt,
            "candidate_pool_size": int((spec.df.hd > 2).sum()),
            "cold_start_size": int((spec.df.hd <= 2).sum()),
            "budget_per_round": budget, "n_rounds": len(rounds), "total_budget": total_budget,
            "budget_spent": state["spent"], "strong_threshold": round(strong_thr, 4),
            "llm_used": llm_used, "llm_summary": llm_summary, "agent_model": agent_model,
            "n_tool_calls": len(state["trace"]),
            "summary": {"final_cum_top10_max": rounds[-1]["cum_top10_max"] if rounds else None,
                        "final_cum_top10_mean": rounds[-1]["cum_top10_mean"] if rounds else None,
                        "final_cum_n_strong": rounds[-1]["cum_n_strong"] if rounds else None,
                        "cum_top10_max_curve": [r["cum_top10_max"] for r in rounds]},
            "rounds": rounds, "tool_trace": state["trace"]}


def main(argv=None):
    from evolution.datasets import load
    from events.store import EventStore
    from evolution.experiment_log import log_run
    p = argparse.ArgumentParser(description="Agentic AutoResearch campaign")
    p.add_argument("--dataset", default="aav", choices=("aav", "avgfp"))
    p.add_argument("--feature", default="one_hot", choices=("one_hot", "esm2"))
    p.add_argument("--budget", type=int, default=96)
    p.add_argument("--n-rounds", type=int, default=3)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--no-llm", action="store_true", help="force the deterministic fallback")
    p.add_argument("--model", default=os.environ.get("AGENTIC_LLM_MODEL", "gpt-5.6-sol"),
                   help="LLM that drives the agent (default gpt-5.6-sol); workflow modes are unaffected")
    p.add_argument("--out-dir", type=Path, default=ROOT / "reports")
    a = p.parse_args(argv)

    ev = a.out_dir / f"pool_events_{a.dataset}_agentic.jsonl"
    ev.unlink(missing_ok=True)
    store = EventStore(ev)
    spec = load(a.dataset, a.feature)
    rep = run_autoresearch(spec, budget=a.budget, n_rounds=a.n_rounds, seed=a.seed,
                           event_store=store, llm=not a.no_llm, model=a.model)
    store.verify()
    out = a.out_dir / f"pool_metrics_{a.dataset}_agentic.json"
    fig = a.out_dir / "figures" / f"pool_curve_{a.dataset}_agentic.png"
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n")
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        r = rep["rounds"]
        if r:
            fig.parent.mkdir(parents=True, exist_ok=True)
            f, ax = plt.subplots(figsize=(8, 4.5))
            ax.plot([x["round"] for x in r], [x["cum_top10_max"] for x in r], marker="o", color="#a05252", label="agentic")
            ax.set(xlabel="test batch", ylabel="cumulative top-10 max fitness", title=f"{rep['dataset']} agentic AutoResearch")
            ax.grid(axis="y", alpha=.25); ax.legend(frameon=False); f.tight_layout(); f.savefig(fig, dpi=150); plt.close(f)
    except Exception:  # noqa: BLE001
        pass
    print(f"[out] {out}\n[out] {ev} ({sum(1 for _ in store.iter_events())} events)")
    print(f"llm_used={rep['llm_used']} model={rep.get('agent_model')} budget_spent={rep['budget_spent']} "
          f"tool_calls={rep['n_tool_calls']} "
          f"cum_top10_max={rep['summary']['final_cum_top10_max']} strong={rep['summary']['final_cum_n_strong']}")
    log_run("agentic", command=f"python -m agent.auto_researcher --dataset {a.dataset} --feature {a.feature} --model {a.model}",
            params={"dataset": a.dataset, "feature": a.feature, "budget": a.budget, "n_rounds": a.n_rounds,
                    "seed": a.seed, "llm": not a.no_llm, "model": a.model},
            artifacts=[str(out.relative_to(ROOT)), str(ev.relative_to(ROOT))],
            summary={**rep["summary"], "llm_used": rep["llm_used"], "budget_spent": rep["budget_spent"]})
    return rep


if __name__ == "__main__":
    main()
