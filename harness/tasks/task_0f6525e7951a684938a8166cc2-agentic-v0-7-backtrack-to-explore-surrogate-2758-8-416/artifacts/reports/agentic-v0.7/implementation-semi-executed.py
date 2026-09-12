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
import functools
import json
import os
from pathlib import Path
import re
import threading

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

SURROGATE EVIDENCE CALIBRATION: never rely on a static belief about predictor quality. Call
`analyze_measured` each round and use its `surrogate_status.cv_spearman` evidence:
- CV Spearman >= 0.80: allocate at least 80% of the batch to predicted-mean exploitation.
- CV Spearman < 0.65: the surrogate is struggling, so allocate 40-50% to structured exploration.
- In the final two rounds, allocate at least 90% to exploitation because late exploration cannot
  be harvested within this campaign.
Use `compose_batch` as the primary acquisition tool. Its answer-agnostic default computes the
exploit ratio from held-out CV quality and campaign round, then combines predicted-mean and
diverse candidates without duplicates. Prefer that default unless measured evidence justifies an
explicit ratio; do not hand-pick dozens of sequence strings.

Workflow for each agent turn: call `analyze_measured` and `best_so_far`, call `compose_batch` for
one full batch, optionally inspect its preview, then call `test_composed_batch` with no arguments.
Never copy the long sequence list into `test`: transcription can corrupt candidates. After that
single successful test, immediately return control to the campaign harness; never start another
cycle in the same turn. The harness will invoke the next round with updated evidence. When the
budget is exhausted, briefly summarise the strategy."""


_MUTATION_NOTATION = re.compile(r"^[A-Z]\d+[A-Z]$")
_AMINO_ACIDS = frozenset("ACDEFGHIKLMNPQRSTVWY")

BACKTRACK_PROMPT = """You are an autonomous protein-engineering researcher with a fixed experiment budget.
Each turn is ONE round: analyze_measured, choose a full batch, test_composed_batch, then return.
Default to strong exploitation using compose_batch (all predicted-mean by default).
Aggregate held-out CV can be high while the surrogate severely underestimates rare high-fitness
variants. Watch top10_max_history and rounds_since_improvement, which include ONLY newly tested
variants, not cold-start incumbents. On stagnation consider switching acquisition to exploration.
explore_batch stages a full exploratory batch: diverse = mean + 3*sqrt(var) + seeded uniform
jitter; uncertainty = highest bootstrap variance; spread = UCB shortlist with soft sequence
diversity. No mode sees unmeasured fitness. compose_batch accepts exploit_ratio in [0,1] and
exploration to mix either amount. No high-CV or late-round exploitation floor applies here.
Use evidence from measured outcomes to choose; do not invent unseen fitness or assume a known
numeric ceiling. best_so_far includes cold-start and is NOT a discovery metric.
Never transcribe sequences: test_composed_batch tests the staged batch exactly.
"""


def _rounds_since_improvement(history) -> int:
    """Consecutive non-improving batches, excluding the initial cold-start incumbent."""
    count, best = 0, -np.inf
    for value in history:
        if value > best:
            best, count = float(value), 0
        else:
            count += 1
    return count


def _explore_batch_indices(mean, var, *, eligible_indices, n, rng,
                           method="diverse", seqs=None, anchors=()):
    """Acquisition uses predictions and sequence geometry only; never pool labels.

    Diverse preserves the reference's UCB+jitter definition. Spread applies a soft
    Hamming-distance bonus in a 10*n UCB shortlist, with no sequence exclusion rule.
    """
    if method not in ("diverse", "uncertainty", "spread"):
        raise ValueError("exploration must be diverse, uncertainty, or spread")
    mean, var = np.asarray(mean), np.asarray(var)
    eligible = np.asarray(list(dict.fromkeys(eligible_indices)), dtype=int)
    n = min(max(0, int(n)), len(eligible))
    if not n:
        return []
    ucb = mean + 3.0 * np.sqrt(np.maximum(var, 0.0))
    score = var if method == "uncertainty" else ucb
    if method == "diverse":
        score = score + rng.random(len(mean))
    order = eligible[np.argsort(-score[eligible], kind="stable")]
    if method != "spread":
        return order[:n].tolist()
    if seqs is None:
        raise ValueError("spread requires pool sequences")
    shortlist = order[:max(n, 10 * n)]
    chars = np.asarray([list(seqs[i]) for i in shortlist])
    distances = np.ones(len(shortlist))
    for anchor in anchors:
        distances = np.minimum(distances, np.mean(chars != np.asarray(list(anchor)), axis=1))
    quality = ucb[shortlist]
    quality = (quality - quality.min()) / max(float(np.ptp(quality)), 1e-12)
    chosen = []
    for _ in range(n):
        utility = quality + distances
        utility[chosen] = -np.inf
        j = int(np.argmax(utility))
        chosen.append(j)
        distances = np.minimum(distances, np.mean(chars != chars[j], axis=1))
    return shortlist[chosen].tolist()


def _clean_seq(value: object) -> str:
    """Normalise an untrusted tool-supplied full sequence without guessing its meaning."""
    if not isinstance(value, str):
        return ""
    return "".join(value.split()).upper()


def _gate_variants(variants, *, wt: str, max_hd: int, blosum_min: float, blosum_fn):
    """Validate untrusted full sequences and apply the knowledge gate without indexing risk."""
    allowed: list[str] = []
    rejected: dict[str, list[str]] = {}
    for raw in variants:
        key = raw if isinstance(raw, str) else repr(raw)
        variant = _clean_seq(raw)
        reasons: list[str] = []
        if _MUTATION_NOTATION.fullmatch(variant):
            reasons.append(
                f"mutation_notation: {variant!r} is a mutation code, not a full {len(wt)}-aa "
                "sequence; retrieve full candidates with compose_batch or list_pool"
            )
        elif len(variant) != len(wt):
            reasons.append(
                f"length_mismatch: sequence has {len(variant)} aa; wild type requires exactly "
                f"{len(wt)} aa"
            )
        else:
            invalid = sorted(set(variant) - _AMINO_ACIDS)
            if invalid:
                reasons.append(f"invalid_residue: unsupported characters {''.join(invalid)!r}")

        if reasons:
            rejected[key] = reasons
            continue

        # zip makes the comparison safe even if validation changes in a future refactor.
        substitutions = [(wild, mutant) for wild, mutant in zip(wt, variant) if mutant != wild]
        if len(substitutions) > max_hd:
            reasons.append(f"HD {len(substitutions)} > {max_hd}")
        if substitutions:
            mean_blosum = float(np.mean([blosum_fn(wild, mutant)
                                        for wild, mutant in substitutions]))
            if mean_blosum < blosum_min:
                reasons.append(
                    f"mean BLOSUM62 {mean_blosum:.1f} < {blosum_min} (non-conservative)"
                )
        if reasons:
            rejected[key] = reasons
        else:
            allowed.append(variant)
    return allowed, rejected


def _adaptive_exploit_ratio(val_spearman: float | None, round_number: int,
                            n_rounds: int) -> float:
    """Answer-agnostic CV-quality/round annealing rule used by ``compose_batch``."""
    rho = 0.0 if val_spearman is None or not np.isfinite(val_spearman) else float(val_spearman)
    progress = max(0.0, min(1.0, float(round_number) / max(1, int(n_rounds))))
    return min(1.0, max(0.4, rho ** 2 + progress * 0.3))


def _enforce_exploit_floor(ratio: float, val_spearman: float | None, round_number: int,
                           n_rounds: int) -> tuple[float, float]:
    """Apply the prompt's high-CV and final-two-round allocation invariants."""
    cv = None if val_spearman is None or not np.isfinite(val_spearman) else float(val_spearman)
    floor = 0.0
    if cv is not None and cv >= 0.80:
        floor = 0.80
    if int(round_number) >= max(1, int(n_rounds) - 1):
        floor = max(floor, 0.90)
    return max(float(ratio), floor), floor


def _compose_batch_indices(mean, var, *, eligible_indices, exploit_ratio: float, n: int, rng):
    """Return de-duplicated exploit-first indices and the realised allocation counts."""
    mean = np.asarray(mean, dtype=float)
    var = np.asarray(var, dtype=float)
    eligible = np.asarray(list(eligible_indices), dtype=int)
    n = max(0, min(int(n), len(eligible)))
    n_exploit = int(round(n * float(exploit_ratio)))
    n_exploit = max(0, min(n, n_exploit))

    mean_order = eligible[np.argsort(-mean[eligible], kind="stable")]
    exploit = mean_order[:n_exploit].tolist()
    chosen = set(exploit)
    diverse_score = mean + 3.0 * np.sqrt(np.maximum(var, 0.0)) + rng.random(len(mean))
    diverse_order = eligible[np.argsort(-diverse_score[eligible], kind="stable")]
    explore = [int(i) for i in diverse_order if int(i) not in chosen][:n - n_exploit]
    chosen.update(explore)
    # If the diverse ranking is ever exhausted, fill deterministically by predicted mean.
    fill = [int(i) for i in mean_order if int(i) not in chosen][:n - len(exploit) - len(explore)]
    picks = exploit + explore + fill
    return picks, len(exploit), len(explore) + len(fill)


def run_autoresearch(spec: DatasetSpec, *, budget: int = 96, n_rounds: int = 3,
                     seed: int = 42, event_store=None, llm: bool = True,
                     request_limit: int = 60, model: str | None = None,
                     guardrail: bool = False, max_hd: int = 4, blosum_min: float = 0.0,
                     surrogate: str = "ridge", backtrack: str | None = None,
                     reference: str = "alternating") -> dict:
    if backtrack not in (None, "full", "semi"):
        raise ValueError("backtrack must be full, semi, or None")
    if reference not in ("alternating", "mean"):
        raise ValueError("reference must be alternating or mean")
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
        "current_round": 0,
        "last_test_round": None,
        "pending_batch": None,
        "surrogate_status": None,
        "n_gate_rejected": 0,     # v0.2 Knowledge Gate: candidates blocked before spending budget
        "top10_max_history": [],
        "rounds_since_improvement": 0,
        "pending_action": None,
        "authorized_exploration": None,
    }

    # v0.2 Knowledge Guardrail: an unbypassable gate BEFORE budget is spent, rejecting
    # biophysically implausible candidates (too high-order, or net non-conservative).
    # Rejected candidates cost no budget and are returned to the agent as structured errors.
    _blosum_matrix = None
    def _blosum(a: str, b: str) -> int:
        nonlocal _blosum_matrix
        if _blosum_matrix is None:
            from knowledge.validators import load_rules
            _blosum_matrix = load_rules()["blosum62"]
        if a == b:
            return 4
        return _blosum_matrix.get(a, {}).get(b, _blosum_matrix.get(b, {}).get(a, 0))

    def _gate(variants: list[str]):
        """Return (allowed, rejected{seq: [reasons]}). Reject HD>max_hd or mean BLOSUM62<blosum_min."""
        return _gate_variants(variants, wt=spec.wt, max_hd=max_hd,
                              blosum_min=blosum_min, blosum_fn=_blosum)

    # v0.2: precompute which unmeasured-pool variants pass the gate, so candidate
    # GENERATION (list_pool, and the harness exploit-fill that calls it) surfaces only
    # the valid region. The gate then SHAPES the search space rather than merely
    # rejecting at test() time — a reject-only wall starves the budget because the
    # surrogate ranks high-HD variants first and the agent keeps proposing gate-fails.
    # test()'s reject-gate is still kept as the unbypassable guarantee (defence in depth).
    gate_pass = None
    if guardrail:
        _allowed, _ = _gate(state["pool"].seq.tolist())
        gate_pass = set(_allowed)

    def emit(kind, actor, payload):
        state["trace"].append({"event_type": kind, "actor": actor, "payload": payload})
        if event_store is not None:
            event_store.append(kind, round_id=state["current_round"] or 1,
                               strategy="agentic", actor=actor, payload=payload)

    def _make_surrogate():
        # v0.4: 'epistasis' = pairwise-interaction (Potts-like) surrogate; captures the
        # position×position epistasis the additive 'ridge' cannot express (see v0.3/v0.4 diagnostic).
        if surrogate == "epistasis":
            from models.train_ladder import EpistasisRidgePredictor
            return EpistasisRidgePredictor()
        return RidgePredictor(seeds=3)

    def _pool_scores():
        """Fit predictor on current measured set and score the whole pool; cached."""
        if state["pred_cache"] is None and not state["pool"].empty:
            model = _make_surrogate().fit(
                spec.feature_fn(state["measured"].seq.tolist()),
                state["measured"][fit_col].to_numpy())
            mean, var = model.predict(spec.feature_fn(state["pool"].seq.tolist()))
            state["pred_cache"] = (model, np.asarray(mean), np.asarray(var))
        return state["pred_cache"]

    def _surrogate_status() -> dict:
        cached = _pool_scores()
        model_obj = cached[0] if cached is not None else None
        cv = getattr(model_obj, "val_spearman", None)
        cv = None if cv is None or not np.isfinite(cv) else float(cv)
        if cv is None:
            confidence = "UNKNOWN"
            recommendation = "No held-out CV score is exposed; use the conservative adaptive default."
        elif cv >= 0.80:
            confidence = "VERY_HIGH" if cv >= 0.90 else "HIGH"
            recommendation = "Prioritise predicted_mean exploitation (>=80% of the batch)."
        elif cv < 0.65:
            confidence = "LOW"
            recommendation = "Allocate 40-50% to structured diverse exploration."
        else:
            confidence = "MODERATE"
            recommendation = "Use the CV/round adaptive allocation and monitor measured results."
        out = {
            "architecture": type(model_obj).__name__ if model_obj is not None else None,
            "cv_spearman": None if cv is None else round(cv, 4),
            "confidence_level": confidence,
            "recommendation": recommendation,
        }
        if backtrack:
            out["recommendation"] = (
                "Stagnation: explore underestimated regions; global CV does not calibrate the tail."
                if state["rounds_since_improvement"] >= 2 else
                "Default to predicted-mean exploitation; monitor newly measured progress."
            )
        state["surrogate_status"] = out
        return out

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
               "current_round": f"{state['current_round']} / {n_rounds}",
               "best_measured": [[str(s), round(float(f), 3)] for s, f in zip(top.seq, top[fit_col])],
               "top_enriched_substitutions": [[k, round(v, 3)] for k, v in enriched],
               "surrogate_status": _surrogate_status(),
               "top10_max_history": list(state["top10_max_history"]),
               "rounds_since_improvement": state["rounds_since_improvement"],
               "stalled": state["rounds_since_improvement"] >= 2,
               "exploration_required": _exploration_required()}
        emit("agent.tool.analyze_measured", "data_analyst", out)
        return out

    def predict(variants: list[str]) -> list[list[float]]:
        """Return the surrogate's [mean, uncertainty] for the given pool variants (imperfect)."""
        scores = _pool_scores()
        if scores is None:
            return []
        idx = {s: i for i, s in enumerate(state["pool"].seq)}
        _model, mean, var = scores
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
        _model, mean, var = scores
        if by == "predicted_mean":
            order = np.argsort(-mean)
        elif by == "uncertainty":
            order = np.argsort(-var)
        elif by == "diverse":
            order = np.argsort(-(mean + 3.0 * np.sqrt(np.maximum(var, 0)) + rng.random(len(mean))))
        else:
            order = rng.permutation(len(state["pool"]))
        if gate_pass is not None:  # v0.2: restrict the candidate view to the gate-passing region
            seqs = state["pool"].seq.to_numpy()
            order = [i for i in order if seqs[i] in gate_pass]
        picks = state["pool"].iloc[order[:n]].seq.tolist()
        emit("agent.tool.list_pool", "hypothesis_generator",
             {"by": by, "n": len(picks), "gated": gate_pass is not None})
        return picks

    def _exploration_required():
        return backtrack == "semi" and state["rounds_since_improvement"] >= 2

    def explore_batch(n: int = 48, method: str = "diverse") -> dict:
        """Stage a gate-safe exploration batch using diverse, uncertainty, or spread."""
        if backtrack == "semi" and not _exploration_required():
            return {"status": "exploitation_required",
                    "hint": "SEMI exploits until two non-improving batches; call compose_batch."}
        if method not in ("diverse", "uncertainty", "spread"):
            return {"status": "invalid_argument", "error": "unknown exploration method"}
        if state["pool"].empty:
            return {"status": "pool_exhausted", "candidates": []}
        n = max(1, min(int(n), budget, total_budget - state["spent"]))
        if backtrack == "semi":
            n = min(budget, total_budget - state["spent"])
        _, mean, var = _pool_scores()
        seqs = state["pool"].seq.to_numpy()
        eligible = [i for i, seq in enumerate(seqs) if gate_pass is None or seq in gate_pass]
        picks = _explore_batch_indices(
            mean, var, eligible_indices=eligible, n=n, rng=rng, method=method,
            seqs=seqs, anchors=state["measured"].nlargest(10, fit_col).seq.tolist(),
        )
        candidates = [str(seqs[i]) for i in picks]
        state["pending_batch"] = candidates
        state["pending_action"] = {"mode": method, "n_exploit": 0, "n_explore": len(picks)}
        state["authorized_exploration"] = candidates
        out = {"status": "ok", "n": len(picks), "method": method,
               "forced": _exploration_required(), "candidates": candidates}
        emit("agent.tool.explore_batch", "hypothesis_generator",
             {k: v for k, v in out.items() if k != "candidates"})
        return out

    def compose_batch(exploit_ratio: float | None = None, n: int = 48,
                      exploration: str = "diverse") -> dict:
        """Compose a gate-safe batch from predicted-mean exploit and diverse explore picks.

        Omit exploit_ratio to use the answer-agnostic CV-quality/round annealing rule.
        """
        if state["pool"].empty:
            return {"status": "pool_exhausted", "candidates": []}
        if backtrack and exploration not in ("diverse", "uncertainty", "spread"):
            return {"status": "invalid_argument", "error": "unknown exploration method"}
        if _exploration_required():
            return explore_batch(n=n, method=exploration)
        n = int(max(1, min(int(n), 60)))
        if backtrack:
            n = min(n, budget, total_budget - state["spent"])
        if backtrack == "semi":
            n = min(budget, total_budget - state["spent"])
        model_obj, mean, var = _pool_scores()
        cv = getattr(model_obj, "val_spearman", None)
        adaptive_ratio = _adaptive_exploit_ratio(cv, state["current_round"], n_rounds)
        if exploit_ratio is None:
            requested_ratio = 1.0 if backtrack else adaptive_ratio
            source = "mean_default" if backtrack else "adaptive_default"
        else:
            requested_ratio = float(exploit_ratio)
            if not np.isfinite(requested_ratio) or not 0.0 <= requested_ratio <= 1.0:
                return {"status": "invalid_argument", "error": "exploit_ratio must be within [0, 1]"}
            source = "agent_requested"
        ratio, policy_floor = _enforce_exploit_floor(
            requested_ratio, cv, state["current_round"], n_rounds,
        )
        if backtrack:
            ratio, policy_floor = requested_ratio, 0.0
        if backtrack == "semi":
            ratio, policy_floor, source = 1.0, 1.0, "semi_exploitation_phase"
        seqs = state["pool"].seq.to_numpy()
        eligible = np.arange(len(seqs))
        if gate_pass is not None:
            eligible = np.asarray([i for i in eligible if seqs[i] in gate_pass], dtype=int)
        if backtrack:
            count = min(n, len(eligible))
            n_exploit = int(round(count * ratio))
            exploit = eligible[np.argsort(-mean[eligible], kind="stable")][:n_exploit].tolist()
            chosen = set(exploit)
            explore = _explore_batch_indices(
                mean, var, eligible_indices=[i for i in eligible if i not in chosen],
                n=count - n_exploit, rng=rng, method=exploration, seqs=seqs,
                anchors=state["measured"].nlargest(10, fit_col).seq.tolist(),
            )
            picks, n_explore = exploit + explore, len(explore)
        else:
            picks, n_exploit, n_explore = _compose_batch_indices(
                mean, var, eligible_indices=eligible, exploit_ratio=ratio, n=n, rng=rng,
            )
        candidates = [str(seqs[i]) for i in picks]
        state["pending_batch"] = candidates
        state["authorized_exploration"] = None
        state["pending_action"] = {"mode": exploration if n_explore else "predicted_mean",
                                   "n_exploit": n_exploit, "n_explore": n_explore}
        out = {
            "status": "ok",
            "allocation_source": source,
            "requested_exploit_ratio": round(float(requested_ratio), 4),
            "exploit_ratio": round(float(ratio), 4),
            "adaptive_default_ratio": round(float(adaptive_ratio), 4),
            "policy_min_ratio": round(float(policy_floor), 4),
            "n_exploit": n_exploit,
            "n_explore": n_explore,
            "n": len(candidates),
            "candidates": candidates,
        }
        emit("agent.tool.compose_batch", "hypothesis_generator",
             {k: v for k, v in out.items() if k != "candidates"})
        return out

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
        if state["current_round"] > 0 and state["last_test_round"] == state["current_round"]:
            return {"status": "round_test_complete", "budget_remaining": total_budget - state["spent"],
                    "hint": "One successful test is allowed per round; return control to the harness now."}
        if state["pending_batch"] is not None:
            return {"status": "composed_batch_pending", "budget_remaining": total_budget - state["spent"],
                    "hint": "Call test_composed_batch() without copying sequence strings."}
        remaining = total_budget - state["spent"]
        if remaining <= 0:
            return {"status": "budget_exhausted", "budget_remaining": 0}
        if _exploration_required() and variants != state["authorized_exploration"]:
            return {"status": "exploration_required", "hint": "Stage explore_batch, then test_composed_batch."}
        if backtrack == "semi" and not _exploration_required():
            _, phase_mean, _ = _pool_scores()
            phase_seqs = state["pool"].seq.to_numpy()
            eligible = np.asarray([i for i, seq in enumerate(phase_seqs)
                                   if gate_pass is None or seq in gate_pass], dtype=int)
            order = eligible[np.argsort(-phase_mean[eligible], kind="stable")]
            expected = set(phase_seqs[order[:min(budget, remaining)]])
            if set(variants) != expected:
                return {"status": "exploitation_required",
                        "hint": "SEMI requires the full predicted-mean batch before stagnation; use compose_batch."}
        requested = list(dict.fromkeys(variants))
        if guardrail:
            allowed, rejected = _gate(requested)
            if rejected:
                state["n_gate_rejected"] += len(rejected)
                emit("agent.tool.knowledge_gate", "scientific_critic",
                     {"n_rejected": len(rejected), "n_allowed": len(allowed),
                      "max_hd": max_hd, "blosum_min": blosum_min})
            if not allowed:
                return {"status": "gate_rejected", "budget_remaining": remaining,
                        "rejected": dict(list(rejected.items())[:8]),
                        "hint": (f"All candidates blocked by the Knowledge Gate (require HD<={max_hd} "
                                 f"and mean BLOSUM62>={blosum_min}). No budget spent. Propose lower-order, "
                                 f"conservative variants (e.g. from list_pool then check_knowledge).")}
            requested = allowed
        chosen = requested[:min(remaining, budget) if backtrack else remaining]
        rows = state["pool"][state["pool"].seq.isin(chosen)].copy()
        # Freeze predictions/ranks BEFORE oracle lookup is consumed by training. The audit
        # records every tested candidate, so post-hoc peak analysis cannot steer acquisition.
        if len(rows):
            _, mean, var = _pool_scores()
            seqs = state["pool"].seq.tolist()
            eligible = [i for i, seq in enumerate(seqs) if gate_pass is None or seq in gate_pass]
            order = np.asarray(eligible)[np.argsort(-mean[eligible], kind="stable")]
            ranks = {seqs[i]: rank for rank, i in enumerate(order, 1)}
            idx = {seq: i for i, seq in enumerate(seqs)}
            emit("agent.acquisition", "hypothesis_generator", {
                "round": state["current_round"], "action": state["pending_action"],
                "forced": _exploration_required(),
                "candidates": [{"seq": seq, "mean_rank": ranks.get(seq),
                                "mean": float(mean[idx[seq]]), "var": float(var[idx[seq]])}
                               for seq in rows.seq],
            })
        state["measured"] = pd.concat([state["measured"], rows], ignore_index=True)
        state["pool"] = state["pool"].drop(rows.index)
        state["pred_cache"] = None  # measured changed -> refit next time
        state["spent"] += len(rows)
        if len(rows):
            state["last_test_round"] = state["current_round"]
            state["batches"].append(rows[["seq", fit_col]].rename(columns={fit_col: "fitness"}))
            previous = state["top10_max_history"][-1] if state["top10_max_history"] else -np.inf
            state["top10_max_history"].append(max(previous, float(rows[fit_col].max())))
            state["rounds_since_improvement"] = _rounds_since_improvement(state["top10_max_history"])
            emit("agent.measurements", "experiment", {
                "round": state["current_round"],
                "results": [[str(s), float(f)] for s, f in zip(rows.seq, rows[fit_col])],
                "top10_max_history": list(state["top10_max_history"]),
                "rounds_since_improvement": state["rounds_since_improvement"],
            })
        state["pending_action"] = None
        state["authorized_exploration"] = None
        best = state["measured"].nlargest(1, fit_col).iloc[0]
        results = [[str(s), round(float(f), 3)] for s, f in zip(rows.seq, rows[fit_col])]
        out = {"status": "ok", "n_measured_now": len(rows),
               "results": results, "budget_remaining": total_budget - state["spent"],
               "running_best": [str(best.seq), round(float(best[fit_col]), 3)]}
        emit("agent.tool.test", "experiment", {"requested": len(chosen), "measured": len(rows),
                                               "spent": state["spent"],
                                               "batch_max": round(float(rows[fit_col].max()), 3) if len(rows) else None})
        return out

    def test_composed_batch() -> dict:
        """Test the exact batch staged by compose_batch, avoiding LLM sequence transcription."""
        if state["pending_batch"] is None:
            return {"status": "no_composed_batch", "budget_remaining": total_budget - state["spent"],
                    "hint": "Call compose_batch first."}
        variants = state["pending_batch"]
        state["pending_batch"] = None
        out = test(variants)
        emit("agent.tool.test_composed_batch", "experiment",
             {"n": len(variants), "status": out.get("status")})
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
            gate_note = ("" if not guardrail else
                         f"\n\nKNOWLEDGE GATE (unbypassable): before `test` spends budget, every candidate must pass "
                         f"HD<={max_hd} substitutions AND mean BLOSUM62>={blosum_min} (net-conservative). To help you, "
                         f"`compose_batch` and `list_pool` ALREADY return only gate-passing candidates. Test a full "
                         f"composed batch each round; do not hand-craft high-order variants (they are rejected without "
                         f"spending budget). Use the reported CV evidence and round annealing to set allocation.")
            if backtrack and guardrail:
                gate_note = (f"\nKnowledge gate: HD<={max_hd}, mean BLOSUM62>={blosum_min}. "
                             "Candidate tools prefilter it; measurement validates it again.")
            policy_note = ("\nFULL: You decide when to explore and how much; no automatic redirect."
                           if backtrack == "full" else
                           "\nSEMI: Before two consecutive non-improving batches, the entire batch MUST be "
                           "predicted-mean exploitation. After that, an entire exploration batch is required "
                           "each round until improvement. You choose its method, not the phase or amount."
                           if backtrack == "semi" else "")
            ag = Agent(oa, system_prompt=(BACKTRACK_PROMPT if backtrack else SYSTEM_PROMPT)
                       + gate_note + policy_note)
            agent_model = model_id
            emit("agent.llm.model", "agent", {"model": model_id, "base_url": cfg["base_url"]})
            tool_lock = threading.RLock()
            def safe_tool(fn):
                @functools.wraps(fn)
                def wrapped(*args, **kwargs):
                    try:
                        with tool_lock:
                            return fn(*args, **kwargs)
                    except Exception as exc:  # noqa: BLE001 - tool boundary must be recoverable
                        out = {"status": "tool_execution_error", "tool": fn.__name__,
                               "error_type": type(exc).__name__, "message": str(exc)[:200],
                               "hint": "Verify the tool arguments and retry in this round."}
                        emit("agent.tool.error", "agent", out)
                        return out
                return wrapped

            for fn in (analyze_measured, predict, list_pool, compose_batch,
                       check_knowledge, test, test_composed_batch, best_so_far,
                       *((explore_batch,) if backtrack else ())):
                ag.tool_plain(safe_tool(fn))
            kwargs = {}
            try:
                from pydantic_ai.usage import UsageLimits
                kwargs["usage_limits"] = UsageLimits(request_limit=min(request_limit, 20))
            except Exception:  # noqa: BLE001
                pass
            # Bounded autonomous loop: each round the LLM MUST spend budget via `test`
            # (analysis alone makes no progress); it chooses which variants and the
            # explore/exploit balance itself. Message history carries strategy across rounds.
            history = None
            for rnd in range(1, n_rounds + 1):
                state["current_round"] = rnd
                remaining = total_budget - state["spent"]
                if remaining <= 0 or state["pool"].empty:
                    break
                this_batch = min(budget, remaining)
                spent_before = state["spent"]
                prompt = (f"Round {rnd} of {n_rounds}. Budget remaining: {remaining}. "
                          f"Call `analyze_measured`, then call `compose_batch(n={this_batch})` (prefer its "
                          f"CV/round adaptive default), then MUST call `test_composed_batch()` without "
                          f"copying any sequences. "
                          f"Analysis alone makes no progress. Follow the >=80% high-CV exploitation rule and "
                          f">=90% exploitation rule in the final two rounds. "
                          f"After testing, note what you learned for the next round.")
                if backtrack:
                    prompt = (f"Round {rnd}/{n_rounds}; batch {this_batch}; remaining {remaining}. "
                              f"Analyze measured evidence, then stage and test one full batch. "
                              f"Default compose_batch(n={this_batch}) exploits; explore_batch or an explicit "
                              f"compose ratio explores. Mode={backtrack}; exploration_required={_exploration_required()}. "
                              f"Choose exploration method and allocation from evidence; return after testing.")
                try:
                    result = ag.run_sync(prompt, message_history=history, **kwargs)
                    history = result.all_messages()
                    llm_summary = str(getattr(result, "output", ""))[:800]
                    emit("agent.llm.round_summary", "agent", {"round": rnd, "summary": llm_summary})
                except Exception as exc:  # noqa: BLE001
                    emit("agent.llm.round_error", "agent", {"round": rnd, "error": str(exc)[:200]})
                # Guarantee progress: if the LLM analysed but did not test, the harness
                # spends this round's budget on its own exploit pick (recorded honestly).
                if state["spent"] == spent_before and not state["pool"].empty:
                    emit("agent.llm.no_test", "agent", {"round": rnd,
                         "note": "LLM skipped test; harness completes staged batch or policy fill"})
                    if state["pending_batch"] is not None:
                        test_composed_batch()
                    elif _exploration_required():
                        explore_batch(this_batch)
                        test_composed_batch()
                    else:
                        test(list_pool(this_batch, "predicted_mean"))
            llm_used = True
        except Exception as exc:  # noqa: BLE001 — degrade to deterministic driver
            emit("agent.llm.fallback", "agent", {"error": str(exc)[:200]})

    if not llm_used:
        # Deterministic fallback: alternate exploit / explore until budget is spent.
        for rnd in range(n_rounds):
            state["current_round"] = rnd + 1
            if state["pool"].empty or state["spent"] >= total_budget:
                break
            by = "predicted_mean" if reference == "mean" or rnd % 2 == 0 else "diverse"
            analyze_measured()
            if _exploration_required():
                explore_batch(budget)
                test_composed_batch()
            else:
                picks = list_pool(budget, by)
                state["pending_action"] = {"mode": by, "driver": "deterministic"}
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
            "guardrail": guardrail, "max_hd": max_hd if guardrail else None,
            "blosum_min": blosum_min if guardrail else None,
            "n_gate_rejected": state["n_gate_rejected"],
            "gate_pass_pool_size": len(gate_pass) if gate_pass is not None else None,
            "surrogate": surrogate,
            "seed": seed, "backtrack": backtrack, "reference": reference,
            "top10_max_history": state["top10_max_history"],
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
    p.add_argument("--model", default=os.environ.get("AGENTIC_LLM_MODEL"),
                   help="LLM model override; otherwise resolve through agent.llm.llm_config")
    p.add_argument("--backtrack", choices=("full", "semi"))
    p.add_argument("--reference", choices=("alternating", "mean"), default="alternating")
    p.add_argument("--guardrail", action="store_true",
                   help="v0.2: unbypassable Knowledge Gate before test (HD<=max-hd + mean BLOSUM62>=0)")
    p.add_argument("--max-hd", type=int, default=4)
    p.add_argument("--blosum-min", type=float, default=0.0)
    p.add_argument("--surrogate", default="ridge", choices=("ridge", "epistasis"),
                   help="v0.4: 'epistasis' = pairwise-interaction (Potts-like) surrogate; use with --feature one_hot")
    p.add_argument("--out-dir", type=Path, default=None,
                   help="default: harness/reports/<agentic-version>/<dataset>/")
    a = p.parse_args(argv)

    from evolution.results_layout import run_dir
    # folder by method generation: v0.5 = quality-aware agent + gate + epistasis surrogate.
    version = ("v0.5" if a.surrogate == "epistasis" else "v0.2") if a.guardrail else None
    if a.backtrack:
        version = "v0.7"
    out_dir = a.out_dir or run_dir("agentic", a.dataset, version=version)
    (out_dir / "figures").mkdir(parents=True, exist_ok=True)
    ev = out_dir / "agentic.events.jsonl"
    ev.unlink(missing_ok=True)
    store = EventStore(ev)
    spec = load(a.dataset, a.feature)
    rep = run_autoresearch(spec, budget=a.budget, n_rounds=a.n_rounds, seed=a.seed,
                           event_store=store, llm=not a.no_llm, model=a.model,
                           guardrail=a.guardrail, max_hd=a.max_hd, blosum_min=a.blosum_min,
                           surrogate=a.surrogate, backtrack=a.backtrack, reference=a.reference)
    store.verify()
    out = out_dir / "agentic.metrics.json"
    fig = out_dir / "figures" / "agentic.png"
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
    _gflag = (f" --guardrail --max-hd {a.max_hd} --blosum-min {a.blosum_min}" if a.guardrail else "")
    _sflag = (f" --surrogate {a.surrogate}" if a.surrogate != "ridge" else "")
    log_run("agentic",
            command=(f"python -m agent.auto_researcher --dataset {a.dataset} --feature {a.feature} "
                     f"--budget {a.budget} --n-rounds {a.n_rounds} --seed {a.seed} --model {a.model}{_gflag}{_sflag}"),
            params={"dataset": a.dataset, "feature": a.feature, "budget": a.budget, "n_rounds": a.n_rounds,
                    "seed": a.seed, "llm": not a.no_llm, "model": a.model,
                    "guardrail": a.guardrail, "max_hd": a.max_hd if a.guardrail else None,
                    "blosum_min": a.blosum_min if a.guardrail else None, "surrogate": a.surrogate},
            artifacts=[str(out.relative_to(ROOT)), str(ev.relative_to(ROOT))],
            summary={**rep["summary"], "llm_used": rep["llm_used"], "budget_spent": rep["budget_spent"]})
    return rep


if __name__ == "__main__":
    main()
