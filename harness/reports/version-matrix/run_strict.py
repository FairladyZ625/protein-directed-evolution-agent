"""Strict 48x6 replay runner for the historical agentic variants.

The production runner is intentionally not modified.  This task-owned runner preserves
each version's tools, surrogate, and gate while enforcing a per-round experiment quota
and writing a complete pre-test nomination ledger.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.model_selection import train_test_split

from agent.auto_researcher import SYSTEM_PROMPT
from events.store import EventStore
from evolution.datasets import load
from evolution.pool_campaign import _stats
from knowledge.validators import load_rules, validate_candidate
from models.train_ladder import EpistasisRidgePredictor, RidgePredictor


VERSIONS = {
    "v0.1": {"guardrail": False, "surrogate": "ridge"},
    "v0.2": {"guardrail": True, "surrogate": "ridge"},
    "v0.4-llm": {"guardrail": True, "surrogate": "epistasis"},
}


def _surrogate(name: str):
    if name == "epistasis":
        return EpistasisRidgePredictor()
    return RidgePredictor(seeds=3)


def _finite_spearman(actual: np.ndarray, predicted: np.ndarray) -> float:
    value = spearmanr(actual, predicted).statistic
    return float(value) if value is not None and np.isfinite(value) else 0.0


def controls(spec, surrogate: str, seed: int) -> dict[str, Any]:
    """Fixed held-out positive control and train-label shuffle negative control."""
    cold = spec.df[spec.df.hd <= 2]
    X = spec.feature_fn(cold.seq.tolist())
    y = cold[spec.fitness_col].to_numpy()
    train, valid = train_test_split(np.arange(len(y)), test_size=0.2, random_state=0)
    positive = _surrogate(surrogate).fit(X[train], y[train])
    positive_mean, _ = positive.predict(X[valid])
    shuffled = y[train].copy()
    np.random.default_rng(seed).shuffle(shuffled)
    negative = _surrogate(surrogate).fit(X[train], shuffled)
    negative_mean, _ = negative.predict(X[valid])
    return {
        "protocol": "80/20 split random_state=0; shuffle training labels only",
        "positive_heldout_spearman": _finite_spearman(y[valid], positive_mean),
        "shuffle_heldout_spearman": _finite_spearman(y[valid], negative_mean),
        "shuffle_abs_below_0_1": abs(_finite_spearman(y[valid], negative_mean)) < 0.1,
        "shuffle_seed": seed,
        "n_train": int(len(train)),
        "n_valid": int(len(valid)),
    }


def run_strict(version: str, seed: int, out_dir: Path) -> dict[str, Any]:
    cfg = VERSIONS[version]
    spec = load("aav", "one_hot")
    fit_col = spec.fitness_col
    budget = 48
    n_rounds = 6
    total_budget = budget * n_rounds
    strong_threshold = float(np.quantile(spec.df[fit_col], 0.9))
    rng = np.random.default_rng(seed)
    rules = load_rules()["blosum62"]

    out_dir.mkdir(parents=True, exist_ok=False)
    store = EventStore(out_dir / "events.jsonl")
    state: dict[str, Any] = {
        "measured": spec.df[spec.df.hd <= 2].copy(),
        "pool": spec.df[spec.df.hd > 2].copy(),
        "spent": 0,
        "trace": [],
        "pred_cache": None,
        "round": 0,
        "round_nominations": [],
        "round_rejections": [],
        "round_quota_remaining": 0,
        "driver": "live_llm",
        "request_id": 0,
        "llm_tool_calls": 0,
        "llm_round_errors": 0,
        "live_llm_rounds": 0,
        "harness_fill_rounds": 0,
        "harness_fill_nominations": 0,
        "fallback_count": 0,
    }

    def blosum(a: str, b: str) -> int:
        if a == b:
            return 4
        return rules.get(a, {}).get(b, rules.get(b, {}).get(a, 0))

    def gate(variants: list[str]) -> tuple[list[str], dict[str, list[str]]]:
        allowed: list[str] = []
        rejected: dict[str, list[str]] = {}
        for variant in variants:
            substitutions = [
                (spec.wt[i], aa) for i, aa in enumerate(variant) if aa != spec.wt[i]
            ]
            reasons: list[str] = []
            if len(substitutions) > 4:
                reasons.append(f"HD {len(substitutions)} > 4")
            if substitutions:
                score = float(np.mean([blosum(wt, aa) for wt, aa in substitutions]))
                if score < 0.0:
                    reasons.append(f"mean BLOSUM62 {score:.1f} < 0.0")
            if reasons:
                rejected[variant] = reasons
            else:
                allowed.append(variant)
        return allowed, rejected

    gate_pass: set[str] | None = None
    if cfg["guardrail"]:
        gate_pass = set(gate(state["pool"].seq.tolist())[0])

    def emit(kind: str, actor: str, payload: dict[str, Any]) -> None:
        entry = {"event_type": kind, "actor": actor, "payload": payload}
        state["trace"].append(entry)
        store.append(
            kind,
            round_id=max(1, state["round"]),
            strategy=version,
            actor=actor,
            payload=payload,
        )

    def count_tool_call() -> None:
        if state["driver"] == "live_llm":
            state["llm_tool_calls"] += 1

    def make_surrogate():
        return _surrogate(cfg["surrogate"])

    def pool_scores() -> tuple[np.ndarray, np.ndarray] | None:
        if state["pool"].empty:
            return None
        if state["pred_cache"] is None:
            model = make_surrogate().fit(
                spec.feature_fn(state["measured"].seq.tolist()),
                state["measured"][fit_col].to_numpy(),
            )
            mean, variance = model.predict(spec.feature_fn(state["pool"].seq.tolist()))
            state["pred_cache"] = (np.asarray(mean), np.asarray(variance))
        return state["pred_cache"]

    def analyze_measured() -> dict[str, Any]:
        """Summarise measured fitness and substitution enrichments."""
        count_tool_call()
        measured = state["measured"]
        top = measured.nlargest(8, fit_col)
        tally: dict[str, list[float]] = {}
        for sequence, fitness in zip(measured.seq, measured[fit_col]):
            for i, (aa, wt) in enumerate(zip(sequence, spec.wt)):
                if aa != wt:
                    tally.setdefault(f"{wt}{i}{aa}", []).append(float(fitness))
        enriched = sorted(
            ((key, float(np.mean(values))) for key, values in tally.items() if len(values) >= 3),
            key=lambda pair: -pair[1],
        )[:12]
        result = {
            "n_measured": len(measured),
            "n_pool_unmeasured": len(state["pool"]),
            "round_budget_remaining": state["round_quota_remaining"],
            "campaign_budget_remaining": total_budget - state["spent"],
            "best_measured": [
                [str(sequence), round(float(fitness), 3)]
                for sequence, fitness in zip(top.seq, top[fit_col])
            ],
            "top_enriched_substitutions": [
                [key, round(value, 3)] for key, value in enriched
            ],
        }
        emit("agent.tool.analyze_measured", "data_analyst", result)
        return result

    def predict(variants: list[str]) -> list[list[float]]:
        """Return surrogate [mean, variance] for unmeasured pool variants."""
        count_tool_call()
        scores = pool_scores()
        if scores is None:
            return []
        mean, variance = scores
        index = {sequence: i for i, sequence in enumerate(state["pool"].seq)}
        result = [
            [round(float(mean[index[v]]), 3), round(float(variance[index[v]]), 6)]
            if v in index
            else [0.0, 0.0]
            for v in variants
        ]
        emit("agent.tool.predict", "fitness_evaluator", {"n": len(variants)})
        return result

    def list_pool(n: int = 20, by: str = "predicted_mean") -> list[str]:
        """List up to 60 pool variants by predicted_mean, uncertainty, diverse, or random."""
        count_tool_call()
        if state["pool"].empty:
            return []
        n = int(max(1, min(n, 60)))
        scores = pool_scores()
        assert scores is not None
        mean, variance = scores
        if by == "predicted_mean":
            order: Any = np.argsort(-mean)
        elif by == "uncertainty":
            order = np.argsort(-variance)
        elif by == "diverse":
            order = np.argsort(
                -(mean + 3.0 * np.sqrt(np.maximum(variance, 0)) + rng.random(len(mean)))
            )
        else:
            order = rng.permutation(len(state["pool"]))
        if gate_pass is not None:
            sequences = state["pool"].seq.to_numpy()
            order = [i for i in order if sequences[i] in gate_pass]
        picks = state["pool"].iloc[order[:n]].seq.tolist()
        emit(
            "agent.tool.list_pool",
            "hypothesis_generator",
            {"by": by, "n": len(picks), "gated": gate_pass is not None},
        )
        return picks

    def check_knowledge(variants: list[str]) -> dict[str, Any]:
        """Apply the historical mutation-rule and BLOSUM62 checks."""
        count_tool_call()
        result: dict[str, Any] = {}
        for variant in variants[:40]:
            mutations = [
                f"{wt}{i}{aa}"
                for i, (aa, wt) in enumerate(zip(variant, spec.wt))
                if aa != wt
            ]
            checks = validate_candidate(mutations)
            result[variant] = {
                "ok": all(check["pass"] for check in checks),
                "fail": [check["rule_id"] for check in checks if not check["pass"]],
            }
        emit("agent.tool.check_knowledge", "scientific_critic", {"n": len(result)})
        return result

    def test(variants: list[str]) -> dict[str, Any]:
        """Measure valid pool variants within this round's fixed 48-candidate quota."""
        count_tool_call()
        state["request_id"] += 1
        request_id = state["request_id"]
        requested = list(dict.fromkeys(variants))
        duplicates = len(variants) - len(requested)
        pool_sequences = set(state["pool"].seq)
        invalid = [variant for variant in requested if variant not in pool_sequences]
        candidates = [variant for variant in requested if variant in pool_sequences]
        rejected: dict[str, list[str]] = {}
        if cfg["guardrail"]:
            candidates, rejected = gate(candidates)
        quota = min(state["round_quota_remaining"], total_budget - state["spent"])
        chosen = candidates[:quota]
        overflow = candidates[quota:]
        rejection_rows = [
            {"sequence": variant, "reasons": ["not_in_unmeasured_pool"], "request_id": request_id}
            for variant in invalid
        ]
        rejection_rows.extend(
            {"sequence": variant, "reasons": reasons, "request_id": request_id}
            for variant, reasons in rejected.items()
        )
        rejection_rows.extend(
            {"sequence": variant, "reasons": ["round_quota_exceeded"], "request_id": request_id}
            for variant in overflow
        )
        state["round_rejections"].extend(rejection_rows)
        if quota <= 0:
            return {
                "status": "round_budget_exhausted",
                "round_budget_remaining": 0,
                "campaign_budget_remaining": total_budget - state["spent"],
            }
        scores = pool_scores()
        assert scores is not None
        mean, variance = scores
        score_by_sequence = {
            sequence: (float(mean[i]), float(variance[i]))
            for i, sequence in enumerate(state["pool"].seq)
        }
        request_position = {sequence: i for i, sequence in enumerate(chosen, 1)}
        chosen_set = set(chosen)
        rows = state["pool"][state["pool"].seq.isin(chosen_set)].copy()
        for measurement_position, row in enumerate(rows.itertuples(), 1):
            predicted_mean, predicted_variance = score_by_sequence[row.seq]
            state["round_nominations"].append(
                {
                    "sequence": str(row.seq),
                    "hd": int(row.hd),
                    "predicted_mean": predicted_mean,
                    "predicted_variance": predicted_variance,
                    "gate_allowed": True,
                    "gate_reasons": [],
                    "driver": state["driver"],
                    "request_id": request_id,
                    "request_position": request_position[str(row.seq)],
                    "measurement_position_in_request": measurement_position,
                    "fitness": float(getattr(row, fit_col)),
                }
            )
        state["measured"] = pd.concat([state["measured"], rows], ignore_index=True)
        state["pool"] = state["pool"].drop(rows.index)
        state["pred_cache"] = None
        state["spent"] += len(rows)
        state["round_quota_remaining"] -= len(rows)
        best = state["measured"].nlargest(1, fit_col).iloc[0]
        results = [
            [str(sequence), round(float(fitness), 3)]
            for sequence, fitness in zip(rows.seq, rows[fit_col])
        ]
        emit(
            "agent.tool.test",
            "experiment",
            {
                "driver": state["driver"],
                "request_id": request_id,
                "requested": len(variants),
                "deduplicated": len(requested),
                "duplicates": duplicates,
                "measured": len(rows),
                "round_spent": budget - state["round_quota_remaining"],
                "campaign_spent": state["spent"],
                "n_rejected": len(rejection_rows),
            },
        )
        return {
            "status": "ok",
            "n_measured_now": len(rows),
            "results": results,
            "round_budget_remaining": state["round_quota_remaining"],
            "campaign_budget_remaining": total_budget - state["spent"],
            "running_best": [str(best.seq), round(float(best[fit_col]), 3)],
            "rejected": rejection_rows[:8],
        }

    def best_so_far() -> list[Any]:
        """Return the best measured variant, including the fixed cold start."""
        count_tool_call()
        best = state["measured"].nlargest(1, fit_col).iloc[0]
        return [str(best.seq), round(float(best[fit_col]), 3)]

    from pydantic_ai import Agent
    try:
        from pydantic_ai.models.openai import OpenAIChatModel as OpenAIModel
    except ImportError:
        from pydantic_ai.models.openai import OpenAIModel
    from pydantic_ai.providers.openai import OpenAIProvider
    from agent.llm import llm_config

    llm = llm_config()
    if llm is None:
        raise RuntimeError("no LLM credentials; strict LLM replay cannot proceed")
    resolved_model = str(llm["model"])
    model = OpenAIModel(
        resolved_model,
        provider=OpenAIProvider(base_url=llm["base_url"], api_key=llm["api_key"]),
    )
    gate_note = ""
    if cfg["guardrail"]:
        gate_note = (
            "\n\nKNOWLEDGE GATE (unbypassable): candidates must pass HD<=4 and mean "
            "BLOSUM62>=0. list_pool already returns only gate-passing candidates."
        )
    agent = Agent(model, system_prompt=SYSTEM_PROMPT + gate_note)
    for function in (analyze_measured, predict, list_pool, check_knowledge, test, best_so_far):
        agent.tool_plain(function)
    kwargs: dict[str, Any] = {}
    try:
        from pydantic_ai.usage import UsageLimits

        kwargs["usage_limits"] = UsageLimits(request_limit=20)
    except Exception:
        pass

    history = None
    rounds: list[dict[str, Any]] = []
    cumulative_batches: list[pd.DataFrame] = []
    llm_summaries: list[str] = []
    for round_id in range(1, n_rounds + 1):
        state["round"] = round_id
        state["round_quota_remaining"] = budget
        state["round_nominations"] = []
        state["round_rejections"] = []
        state["driver"] = "live_llm"
        prompt = (
            f"Round {round_id} of {n_rounds}. This round has exactly {budget} experiment slots. "
            "Analyse with the tools, then call test on candidates you choose. You may split the "
            "48 nominations across calls, but this round cannot borrow from another round. "
            "Deliberately balance exploitation and exploration, then note what you learned."
        )
        try:
            result = agent.run_sync(prompt, message_history=history, **kwargs)
            history = result.all_messages()
            llm_summaries.append(str(getattr(result, "output", ""))[:800])
            state["live_llm_rounds"] += 1
        except Exception as exc:  # preserve the failure, then apply preregistered fill
            state["llm_round_errors"] += 1
            emit(
                "agent.llm.round_error",
                "agent",
                {"round": round_id, "error": str(exc)[:400]},
            )
        if state["round_quota_remaining"]:
            missing = state["round_quota_remaining"]
            state["driver"] = "harness_fill"
            state["harness_fill_rounds"] += 1
            state["harness_fill_nominations"] += missing
            emit(
                "agent.llm.underfilled_round",
                "agent",
                {"round": round_id, "missing": missing, "policy": "predicted_mean"},
            )
            fill = list_pool(missing, "predicted_mean")
            test(fill)
        if state["round_quota_remaining"] != 0 or len(state["round_nominations"]) != budget:
            raise RuntimeError(
                f"round {round_id} could not be filled: "
                f"remaining={state['round_quota_remaining']} nominations={len(state['round_nominations'])}"
            )
        batch = pd.DataFrame(
            {
                "seq": [row["sequence"] for row in state["round_nominations"]],
                "fitness": [row["fitness"] for row in state["round_nominations"]],
            }
        )
        cumulative_batches.append(batch)
        cumulative = pd.concat(cumulative_batches, ignore_index=True)
        round_report = {
            "round": round_id,
            **_stats(batch, cumulative, "fitness", strong_threshold),
            "spent_after": state["spent"],
            "n_live_llm": sum(
                row["driver"] == "live_llm" for row in state["round_nominations"]
            ),
            "n_harness_fill": sum(
                row["driver"] == "harness_fill" for row in state["round_nominations"]
            ),
            "nominations": state["round_nominations"],
            "rejections": state["round_rejections"],
        }
        rounds.append(round_report)
        emit("campaign.round.completed", "campaign", round_report)

    control_results = controls(spec, cfg["surrogate"], seed)
    report = {
        "schema_version": "version-matrix.v1",
        "record_type": "unified_rerun",
        "version": version,
        "dataset": spec.name,
        "feature": "one_hot",
        "wild_type": spec.wt,
        "candidate_pool_size": int((spec.df.hd > 2).sum()),
        "cold_start_size": int((spec.df.hd <= 2).sum()),
        "gate_pass_pool_size": len(gate_pass) if gate_pass is not None else None,
        "guardrail": cfg["guardrail"],
        "surrogate": cfg["surrogate"],
        "oracle": "post-nomination measured-table lookup",
        "seed": seed,
        "budget_per_round": budget,
        "n_rounds": n_rounds,
        "total_budget": total_budget,
        "budget_spent": state["spent"],
        "round_counts": [round_["n_nominated"] for round_ in rounds],
        "strong_threshold": strong_threshold,
        "model": {
            "resolved_request_id": resolved_model,
            "gateway_identity_independently_verified": False,
        },
        "execution": {
            "live_llm_rounds": state["live_llm_rounds"],
            "live_llm_tool_calls": state["llm_tool_calls"],
            "llm_round_errors": state["llm_round_errors"],
            "harness_fill_rounds": state["harness_fill_rounds"],
            "harness_fill_nominations": state["harness_fill_nominations"],
            "fallback_count": state["fallback_count"],
        },
        "controls": control_results,
        "summary": {
            "final_cum_top10_max": rounds[-1]["cum_top10_max"],
            "final_cum_top10_mean": rounds[-1]["cum_top10_mean"],
            "final_cum_n_strong": rounds[-1]["cum_n_strong"],
            "cum_top10_max_curve": [round_["cum_top10_max"] for round_ in rounds],
        },
        "rounds": rounds,
        "tool_trace": state["trace"],
        "llm_summaries": llm_summaries,
    }
    (out_dir / "metrics.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    store.verify()
    summary = {
        "version": version,
        "seed": seed,
        "round_counts": report["round_counts"],
        "budget_spent": report["budget_spent"],
        "cum_top10_max": report["summary"]["final_cum_top10_max"],
        "strong": report["summary"]["final_cum_n_strong"],
        "model": resolved_model,
        **report["execution"],
        "positive_heldout_spearman": control_results["positive_heldout_spearman"],
        "shuffle_heldout_spearman": control_results["shuffle_heldout_spearman"],
        "shuffle_abs_below_0_1": control_results["shuffle_abs_below_0_1"],
        "event_count": sum(1 for _ in store.iter_events()),
        "event_chain_verified": True,
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(summary, ensure_ascii=False))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", choices=tuple(VERSIONS), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    run_strict(args.version, args.seed, args.out_dir)


if __name__ == "__main__":
    main()
