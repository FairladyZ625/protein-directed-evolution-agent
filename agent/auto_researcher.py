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
from collections import Counter
import contextlib
import functools
import json
import math
import os
from pathlib import Path
import signal
import threading
import re

import numpy as np
import pandas as pd

from evolution.pool_campaign import DatasetSpec, _stats
from models.train_ladder import RidgePredictor
from knowledge.validators import build_knowledge_graph, query_mutation_context, validate_candidate

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
{acquisition_paragraph}

Workflow for each agent turn: call `analyze_measured` and `best_so_far`, call `compose_batch` for
one full batch, optionally inspect its preview, then call `test_composed_batch` with no arguments.
Never copy the long sequence list into `test`: transcription can corrupt candidates. After that
single successful test, immediately return control to the campaign harness; never start another
cycle in the same turn. The harness will invoke the next round with updated evidence. When the
budget is exhausted, briefly summarise the strategy."""

# v0.5 wording kept verbatim so the v0.5 prompt is byte-identical when backtrack is off.
_V05_ACQUISITION_PARAGRAPH = """Use `compose_batch` as the primary acquisition tool. Its answer-agnostic default computes the
exploit ratio from held-out CV quality and campaign round, then combines predicted-mean and
diverse candidates without duplicates. Prefer that default unless measured evidence justifies an
explicit ratio; do not hand-pick dozens of sequence strings."""

# v0.6 wording: the rank-45 lesson — with a high-CV surrogate, forced early exploration only
# truncates the greedy head; the default becomes pure predicted-mean exploitation and the only
# sanctioned escape is the meta-layer `redirect_batch` basin hop.
_V06_ACQUISITION_PARAGRAPH = """Use `compose_batch` as the primary acquisition tool. In this campaign its default is PURE
predicted-mean exploitation: the top-n candidates by predicted mean, with no forced exploration
tax. Prefer that default while the CV evidence is high; do not dilute batches with diverse or
uncertainty picks unless the CV evidence itself demands it."""

SYSTEM_PROMPT = SYSTEM_PROMPT.format(acquisition_paragraph=_V05_ACQUISITION_PARAGRAPH)

_BACKTRACK_FULL_NOTE = """

META-LAYER AUTONOMY (v0.6, you own the campaign strategy): each round `analyze_measured` also
reports the campaign trajectory — the cumulative top-10-max history, the number of rounds since
it last improved, the mutation signature of the best measured cluster, and which rounds already
used a redirect. If YOU judge that your own strategy has stalled (e.g. the top-10 max no longer
improves across consecutive rounds — a self-made local trap), you may stage `redirect_batch(n=...)`
instead of `compose_batch`: a gate-safe batch of high predicted-mean candidates whose mutation
composition differs from the best measured cluster (a basin hop; lower `max_overlap` = a harder
hop). When to judge a stall, whether to redirect, and how far to hop are entirely YOUR decisions,
based only on measured fitness and surrogate predictions. After a redirect, judge freshly: return
to pure exploitation when the evidence says the new basin is no better."""

_BACKTRACK_SEMI_NOTE = """

META-LAYER WITH HARD STALL DETECTOR (v0.6): a fixed rule monitors the campaign — if the cumulative
top-10 max fails to improve for 2 consecutive rounds, your round prompt carries STALLED=true and
`analyze_measured` shows `campaign.stalled`. The flag states the detected fact; whether to act on
it is your decision. The escape tool is `redirect_batch(n=...)`: a gate-safe batch of high
predicted-mean candidates whose mutation composition differs from the best measured cluster (a
basin hop; lower `max_overlap` = a harder hop). The default acquisition stays pure predicted-mean
exploitation. Where to redirect — and whether to redirect at all — is your judgment, based only on
measured fitness and surrogate predictions."""

_MUTATION_NOTATION = re.compile(r"^[A-Z]\d+[A-Z]$")
_AMINO_ACIDS = frozenset("ACDEFGHIKLMNPQRSTVWY")

# v0.6 meta-layer backtrack: hard stall rule shared by the semi-autonomous variant.
STALL_THRESHOLD = 2  # consecutive rounds without a new cumulative top-10 max

def _clean_seq(value: object) -> str:
    """Normalise an untrusted tool-supplied full sequence without guessing its meaning."""
    if not isinstance(value, str):
        return ""
    return "".join(value.split()).upper()


@contextlib.contextmanager
def _wall_clock_timeout(seconds: float):
    """Bound a synchronous LLM round on Unix; always restore the prior alarm state."""
    if seconds <= 0 or threading.current_thread() is not threading.main_thread():
        yield
        return
    previous_handler = signal.getsignal(signal.SIGALRM)

    def _raise_timeout(_signum, _frame):
        raise TimeoutError(f"LLM round exceeded {seconds:g}s wall-clock limit")

    signal.signal(signal.SIGALRM, _raise_timeout)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, float(seconds))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, *previous_timer)
        signal.signal(signal.SIGALRM, previous_handler)


def _mutation_codes(sequence: str, wild_type: str) -> list[str]:
    """Represent full-sequence substitutions with the campaign's zero-based positions."""
    return [f"{wild}{position}{mutant}"
            for position, (wild, mutant) in enumerate(zip(wild_type, sequence))
            if wild != mutant]


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


def _default_exploit_ratio(backtrack, val_spearman, round_number, n_rounds) -> tuple[float, str]:
    """Default compose_batch ratio: v0.6 backtrack campaigns use pure predicted-mean
    exploitation (the v0.5 rank-45 lesson: no forced early-exploration tax); v0.5 keeps
    the CV/round adaptive rule."""
    if backtrack:
        return 1.0, "v06_pure_exploit_default"
    return _adaptive_exploit_ratio(val_spearman, round_number, n_rounds), "adaptive_default"


def _mutation_set(seq: str, wt: str) -> frozenset[str]:
    """The set of 'W<i>C' substitutions a variant carries relative to the wild type."""
    return frozenset(f"{w}{i}{c}" for i, (c, w) in enumerate(zip(seq, wt)) if c != w)


def _best_cluster_signature(measured: pd.DataFrame, fit_col: str, wt: str, k: int = 10) -> set[str]:
    """Substitutions shared by at least half of the top-k measured variants — the mutation
    signature of the basin the campaign is currently exploiting. Reads only measured labels."""
    top = measured.nlargest(min(k, len(measured)), fit_col)
    counts: Counter = Counter()
    for s in top.seq:
        counts.update(_mutation_set(str(s), wt))
    need = max(1, math.ceil(0.5 * len(top)))
    return {mut for mut, n in counts.items() if n >= need}


def _rounds_since_improvement(history: list[float]) -> int:
    """Completed batches since the cumulative top-10 max last strictly increased."""
    if len(history) <= 1:
        return 0
    best, last_improved = float("-inf"), 0
    for i, value in enumerate(history):
        if value > best + 1e-9:
            best, last_improved = value, i
    return len(history) - 1 - last_improved


def _redirect_indices(mean, seqs, wt, *, eligible_indices, signature, n, max_overlap: float = 0.5):
    """Basin-hop batch: highest predicted-mean candidates whose mutation composition differs
    from the measured-best cluster.

    A candidate is hop-eligible when at most `max_overlap` of its substitutions lie inside the
    best-cluster signature. Candidates are ranked by predicted mean only; if hop-eligible ones
    are exhausted the batch degrades to a greedy fill (mean order) — never by true fitness.
    Returns (pool indices, n_hop_eligible, n_fill_used).
    """
    mean = np.asarray(mean, dtype=float)
    by_mean = sorted((int(i) for i in eligible_indices), key=lambda i: -float(mean[i]))
    n = max(0, min(int(n), len(by_mean)))
    sig = set(signature)
    hop: list[int] = []
    fill: list[int] = []
    for i in by_mean:
        muts = _mutation_set(str(seqs[i]), wt)
        overlap = (len(muts & sig) / len(muts)) if muts else 0.0
        (hop if overlap <= float(max_overlap) + 1e-12 else fill).append(i)
    picks = hop[:n]
    n_fill = max(0, n - len(picks))
    if n_fill:
        picks += fill[:n_fill]
    return picks, len(hop), n_fill


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
                     surrogate: str = "ridge", no_knowledge: bool = False,
                     backtrack: str | None = None) -> dict:
    if guardrail and no_knowledge:
        raise ValueError("guardrail and no_knowledge are mutually exclusive treatment modes")
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
        "knowledge_graph": None,   # measured-only snapshot; invalidated after every test
        "n_gate_rejected": 0,     # v0.2 Knowledge Gate: candidates blocked before spending budget
        # v0.6 meta-layer backtrack: stagnation tracking + redirect bookkeeping.
        "top10_max_history": [],  # cumulative top-10 max after each completed batch
        "redirect_rounds": [],    # rounds where redirect_batch staged the tested batch
        "stall_flag_rounds": [],  # rounds where the semi hard rule fired (semi only)
    }
    knowledge_enabled = bool(guardrail and not no_knowledge)
    tool_lock = threading.RLock()

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
        strategy = "knowledge_agent" if knowledge_enabled else "agent_no_knowledge"
        state["trace"].append({"event_type": kind, "round_id": len(state["batches"]) + 1,
                               "strategy": strategy, "actor": actor, "payload": payload})
        if event_store is not None:
            event_store.append(kind, round_id=len(state["batches"]) + 1,
                               strategy=strategy,
                               actor=actor, payload=payload)

    def _knowledge_graph():
        """Build a graph exclusively from measurements available at this decision point."""
        if state["knowledge_graph"] is None:
            records = [
                {"id": str(sequence), "mutations": _mutation_codes(str(sequence), spec.wt),
                 "fitness": float(fitness)}
                for sequence, fitness in zip(state["measured"].seq, state["measured"][fit_col])
            ]
            state["knowledge_graph"] = build_knowledge_graph(records)
        return state["knowledge_graph"]

    def _graph_rationale(variant: str) -> str:
        contexts = [query_mutation_context(_knowledge_graph(), mutation)
                    for mutation in _mutation_codes(variant, spec.wt)]
        if not contexts:
            return "KG: wild type; no mutation node queried."
        clauses = []
        for item in contexts:
            mean = item["fitness_mean"]
            evidence = ("unseen in measured graph" if mean is None else
                        f"n={item['n_measured']}, measured-association mean={mean:.3f}, "
                        f"max={item['fitness_max']:.3f}")
            props = item["mutant_properties"]
            clauses.append(
                f"{item['mutation']} ({evidence}; target properties: "
                f"charge={props.get('charge')}, size={props.get('size')}, "
                f"polarity={props.get('polarity')})"
            )
        return "KG: " + "; ".join(clauses) + ". Associations are not causal effects."

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
               "surrogate_status": _surrogate_status()}
        if backtrack:
            # v0.6 meta-layer evidence: stagnation trajectory + best-cluster composition.
            # Read-only, from measured labels only. The `stalled` verdict is exposed ONLY to
            # the semi variant (its hard rule owns stall judgment); full keeps raw data.
            rsi = _rounds_since_improvement(state["top10_max_history"])
            campaign = {"top10_max_history": [round(float(v), 4) for v in state["top10_max_history"]],
                        "rounds_since_improvement": rsi,
                        "redirect_rounds_so_far": list(state["redirect_rounds"])}
            if backtrack == "semi":
                campaign["stalled"] = bool(rsi >= STALL_THRESHOLD)
            out["campaign"] = campaign
            out["best_cluster_signature"] = sorted(
                _best_cluster_signature(state["measured"], fit_col, spec.wt))
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

    def compose_batch(exploit_ratio: float | None = None, n: int = 48) -> dict:
        """Compose a gate-safe batch from predicted-mean exploit and diverse explore picks.

        Omit exploit_ratio to use the answer-agnostic CV-quality/round annealing rule.
        """
        if state["pool"].empty:
            return {"status": "pool_exhausted", "candidates": []}
        n = int(max(1, min(int(n), 60)))
        model_obj, mean, var = _pool_scores()
        cv = getattr(model_obj, "val_spearman", None)
        adaptive_ratio = _adaptive_exploit_ratio(cv, state["current_round"], n_rounds)
        if exploit_ratio is None:
            requested_ratio, source = _default_exploit_ratio(
                backtrack, cv, state["current_round"], n_rounds)
        else:
            requested_ratio = float(exploit_ratio)
            if not np.isfinite(requested_ratio) or not 0.0 <= requested_ratio <= 1.0:
                return {"status": "invalid_argument", "error": "exploit_ratio must be within [0, 1]"}
            source = "agent_requested"
        ratio, policy_floor = _enforce_exploit_floor(
            requested_ratio, cv, state["current_round"], n_rounds,
        )
        seqs = state["pool"].seq.to_numpy()
        eligible = np.arange(len(seqs))
        if gate_pass is not None:
            eligible = np.asarray([i for i in eligible if seqs[i] in gate_pass], dtype=int)
        picks, n_exploit, n_explore = _compose_batch_indices(
            mean, var, eligible_indices=eligible, exploit_ratio=ratio, n=n, rng=rng,
        )
        candidates = [str(seqs[i]) for i in picks]
        state["pending_batch"] = candidates
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
        if knowledge_enabled:
            out["knowledge_graph_rationales"] = [
                {"variant": variant, "rationale": _graph_rationale(variant)}
                for variant in candidates[:3]
            ]
            emit("agent.tool.knowledge_graph", "scientific_critic", {
                "stage": "compose_batch",
                "measured_only": True,
                "rationales": out["knowledge_graph_rationales"],
            })
        emit("agent.tool.compose_batch", "hypothesis_generator",
             {k: v for k, v in out.items()
              if k not in {"candidates", "knowledge_graph_rationales"}})
        return out

    def redirect_batch(n: int = 48, max_overlap: float = 0.5) -> dict:
        """Stage a gate-safe, predicted-mean basin hop away from the best cluster."""
        if state["pool"].empty:
            return {"status": "pool_exhausted", "candidates": []}
        n = int(max(1, min(int(n), 60)))
        if not np.isfinite(max_overlap) or not 0.0 <= float(max_overlap) <= 1.0:
            return {"status": "invalid_argument", "error": "max_overlap must be within [0, 1]"}
        _model, mean, _var = _pool_scores()
        seqs = state["pool"].seq.to_numpy()
        eligible = np.arange(len(seqs))
        if gate_pass is not None:
            eligible = np.asarray([i for i in eligible if seqs[i] in gate_pass], dtype=int)
        signature = _best_cluster_signature(state["measured"], fit_col, spec.wt)
        picks, n_hop, n_fill = _redirect_indices(
            mean, seqs, spec.wt, eligible_indices=eligible, signature=signature,
            n=n, max_overlap=float(max_overlap),
        )
        candidates = [str(seqs[i]) for i in picks]
        state["pending_batch"] = candidates
        state["redirect_rounds"].append(state["current_round"])
        overlaps = []
        for candidate in candidates:
            mutations = _mutation_set(candidate, spec.wt)
            overlaps.append((len(mutations & signature) / len(mutations)) if mutations else 0.0)
        out = {
            "status": "ok", "n": len(candidates), "max_overlap": float(max_overlap),
            "signature_size": len(signature), "n_hop_eligible": n_hop, "n_fill": n_fill,
            "picks_overlap_mean": round(float(np.mean(overlaps)), 4) if overlaps else None,
            "predicted_mean_top": round(float(np.max(mean[picks])), 4) if len(picks) else None,
            "candidates": candidates,
        }
        emit("agent.tool.redirect_batch", "hypothesis_generator",
             {key: value for key, value in out.items() if key != "candidates"})
        return out

    def check_knowledge(variants: list[str]) -> dict:
        """Knowledge-base assessment (mutation rules + BLOSUM62) for the given variants."""
        out = {}
        for index, v in enumerate(variants[:40]):
            if no_knowledge:
                out[v] = {"ok": True, "fail": [], "knowledge": "disabled", "rationale": None}
                continue
            if knowledge_enabled:
                allowed, rejected = _gate([v])
                out[v] = {"ok": bool(allowed),
                          "fail": rejected.get(v, []),
                          "knowledge": "AAV HD/BLOSUM gate + measured-only knowledge graph",
                          "rationale": _graph_rationale(v) if index < 3 else None}
            else:
                # Backwards-compatible GB1 validator path for callers that do not opt into
                # either explicit AAV treatment.  AAV experiments always choose one mode.
                muts = _mutation_codes(v, spec.wt)
                checks = validate_candidate(muts)
                out[v] = {"ok": all(x["pass"] for x in checks),
                          "fail": [x["rule_id"] for x in checks if not x["pass"]],
                          "rationale": None}
        emit("agent.tool.check_knowledge", "scientific_critic", {
            "n": len(out),
            "knowledge_enabled": knowledge_enabled,
            "rationales": [{"variant": variant, "rationale": row["rationale"]}
                           for variant, row in out.items() if row.get("rationale")],
        })
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
        chosen = requested[:remaining]
        rows = state["pool"][state["pool"].seq.isin(chosen)].copy()
        state["measured"] = pd.concat([state["measured"], rows], ignore_index=True)
        state["pool"] = state["pool"].drop(rows.index)
        state["pred_cache"] = None  # measured changed -> refit next time
        state["knowledge_graph"] = None
        state["spent"] += len(rows)
        if len(rows):
            state["last_test_round"] = state["current_round"]
            state["batches"].append(rows[["seq", fit_col]].rename(columns={fit_col: "fitness"}))
            if backtrack:
                # v0.6 stagnation tracking: running max over completed batches only.
                batch_max = float(rows[fit_col].max())
                prev = state["top10_max_history"][-1] if state["top10_max_history"] else None
                running = batch_max if prev is None else max(prev, batch_max)
                state["top10_max_history"].append(running)
        best = state["measured"].nlargest(1, fit_col).iloc[0]
        results = [[str(s), round(float(f), 3)] for s, f in zip(rows.seq, rows[fit_col])]
        out = {"status": "ok", "n_measured_now": len(rows),
               "results": results, "budget_remaining": total_budget - state["spent"],
               "running_best": [str(best.seq), round(float(best[fit_col]), 3)]}
        test_payload = {"requested": len(chosen), "measured": len(rows),
                        "spent": state["spent"],
                        "batch_max": round(float(rows[fit_col].max()), 3) if len(rows) else None}
        if backtrack and state["top10_max_history"]:
            test_payload["cum_top10_max"] = round(float(state["top10_max_history"][-1]), 4)
        emit("agent.tool.test", "experiment", test_payload)
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

    def execute_research_round(n: int = 48, exploit_ratio: float | None = None) -> dict:
        """Atomically analyse, compose, and test one batch with one LLM tool request.

        This keeps the scientific transitions identical while avoiding several network
        round trips that can exceed the bounded per-round wall-clock budget.
        """
        analysis = analyze_measured()
        composition = compose_batch(exploit_ratio=exploit_ratio, n=n)
        if composition.get("status") != "ok":
            return {"status": composition.get("status"), "analysis": analysis,
                    "composition": composition}
        experiment = test_composed_batch()
        return {
            "status": experiment.get("status"),
            "analysis": analysis,
            "composition": {key: value for key, value in composition.items()
                            if key not in {"candidates", "knowledge_graph_rationales"}},
            "experiment": experiment,
        }

    def best_so_far() -> list:
        """Return the single best variant measured so far as [sequence, fitness]."""
        best = state["measured"].nlargest(1, fit_col).iloc[0]
        return [str(best.seq), round(float(best[fit_col]), 3)]

    # ---- run: LLM-driven, with deterministic fallback ------------------------
    llm_used = False
    llm_summary = None
    agent_model = None
    llm_round_timeout_seconds = None
    if llm:
        try:
            from pydantic_ai import Agent
            try:
                from pydantic_ai.models.openai import OpenAIChatModel as OAModel
            except ImportError:
                from pydantic_ai.models.openai import OpenAIModel as OAModel
            from pydantic_ai.providers.openai import OpenAIProvider
            from openai import AsyncOpenAI
            from agent.llm import llm_config
            cfg = llm_config()
            if cfg is None:
                raise RuntimeError("no LLM credentials")
            model_id = model or cfg["model"]
            llm_round_timeout_seconds = float(cfg["timeout"])
            client = AsyncOpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"],
                                 timeout=cfg["timeout"], max_retries=0)
            oa = OAModel(model_id, provider=OpenAIProvider(openai_client=client))
            gate_note = ("" if not guardrail else
                         f"\n\nKNOWLEDGE GATE (unbypassable): before `test` spends budget, every candidate must pass "
                         f"HD<={max_hd} substitutions AND mean BLOSUM62>={blosum_min} (net-conservative). To help you, "
                         f"`compose_batch` and `list_pool` ALREADY return only gate-passing candidates. Test a full "
                         f"composed batch each round; do not hand-craft high-order variants (they are rejected without "
                         f"spending budget). Use the reported CV evidence and round annealing to set allocation.")
            if backtrack:
                base_prompt = SYSTEM_PROMPT.replace(
                    _V05_ACQUISITION_PARAGRAPH, _V06_ACQUISITION_PARAGRAPH)
                if base_prompt == SYSTEM_PROMPT:  # prompt text drifted; never mis-prompt silently
                    raise RuntimeError("v0.6 acquisition paragraph no longer matches SYSTEM_PROMPT")
                base_prompt += _BACKTRACK_FULL_NOTE if backtrack == "full" else _BACKTRACK_SEMI_NOTE
            else:
                base_prompt = SYSTEM_PROMPT
            ag = Agent(oa, system_prompt=base_prompt + gate_note)
            agent_model = model_id
            emit("agent.llm.model", "agent", {"model": model_id, "base_url": cfg["base_url"]})
            def safe_tool(fn):
                @functools.wraps(fn)
                def wrapped(*args, **kwargs):
                    # A model may request several stateful tools in one response.  Pydantic
                    # executes those calls concurrently, so serialise each complete tool
                    # transition to keep measured/pool/budget state deterministic.
                    with tool_lock:
                        try:
                            return fn(*args, **kwargs)
                        except Exception as exc:  # noqa: BLE001 - recoverable tool boundary
                            out = {"status": "tool_execution_error", "tool": fn.__name__,
                                   "error_type": type(exc).__name__, "message": str(exc)[:200],
                                   "hint": "Verify the tool arguments and retry in this round."}
                            emit("agent.tool.error", "agent", out)
                            return out
                return wrapped

            tool_fns = [execute_research_round, analyze_measured, predict, list_pool, compose_batch,
                        check_knowledge, test, test_composed_batch, best_so_far]
            if backtrack:
                tool_fns.append(redirect_batch)
            for fn in tool_fns:
                ag.tool_plain(safe_tool(fn))
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
                state["current_round"] = rnd
                remaining = total_budget - state["spent"]
                if remaining <= 0 or state["pool"].empty:
                    break
                this_batch = min(budget, remaining)
                spent_before = state["spent"]
                if backtrack:
                    prompt = (f"Round {rnd} of {n_rounds}. Budget remaining: {remaining}. "
                              f"Call `analyze_measured` (it includes the campaign trajectory), "
                              f"then stage ONE batch: `compose_batch(n={this_batch})` "
                              f"(pure-exploitation default) or, if you judge the campaign "
                              f"stagnant, `redirect_batch(n={this_batch})` (basin hop). Then "
                              f"MUST call `test_composed_batch()` without copying any "
                              f"sequences. Analysis alone makes no progress. After testing, "
                              f"note what you learned for the next round.")
                    if backtrack == "semi":
                        rsi_now = _rounds_since_improvement(state["top10_max_history"])
                        stalled_now = rsi_now >= STALL_THRESHOLD
                        if stalled_now:
                            state["stall_flag_rounds"].append(rnd)
                            emit("agent.backtrack.stall_flag", "agent",
                                 {"round": rnd, "rounds_since_improvement": rsi_now,
                                  "threshold": STALL_THRESHOLD, "mode": "semi"})
                        prompt += (f" HARD STALL DETECTOR: STALLED="
                                   f"{'true' if stalled_now else 'false'} "
                                   f"(rounds_since_improvement={rsi_now}; rule: no cum_top10_max "
                                   f"improvement for >={STALL_THRESHOLD} consecutive rounds).")
                        if stalled_now:
                            prompt += (" The pure-exploitation path has stopped yielding new "
                                       "maxima; judge whether to `redirect_batch` to a different "
                                       "high-prediction basin or to keep exploiting — the "
                                       "redirect decision is yours.")
                else:
                    prompt = (f"Round {rnd} of {n_rounds}. Budget remaining: {remaining}. "
                              f"Call `execute_research_round(n={this_batch})` exactly once; prefer its "
                              f"CV/round adaptive exploit ratio unless prior measured evidence justifies an override. "
                              f"This atomic tool performs analysis, composition, and testing without sequence copying. "
                              f"Follow the >=80% high-CV exploitation rule and "
                              f">=90% exploitation rule in the final two rounds. "
                              f"After testing, note what you learned for the next round.")
                try:
                    with _wall_clock_timeout(cfg["timeout"]):
                        result = ag.run_sync(prompt, message_history=history, **kwargs)
                    history = result.all_messages()
                    llm_summary = str(getattr(result, "output", ""))[:800]
                except Exception as exc:  # noqa: BLE001
                    emit("agent.llm.round_error", "agent", {"round": rnd, "error": str(exc)[:200]})
                # Guarantee progress: if the LLM analysed but did not test, the harness
                # spends this round's budget on its own exploit pick (recorded honestly).
                if state["spent"] == spent_before and not state["pool"].empty:
                    emit("agent.llm.no_test", "agent", {
                        "round": rnd,
                        "note": "LLM skipped test; harness composed fill",
                    })
                    if state["pending_batch"] is not None:
                        test_composed_batch()
                    else:
                        composition = compose_batch(n=this_batch)
                        if composition.get("status") == "ok":
                            test_composed_batch()
            llm_used = True
        except Exception as exc:  # noqa: BLE001 — degrade to deterministic driver
            emit("agent.llm.fallback", "agent", {"error": str(exc)[:200]})

    if not llm_used:
        # Deterministic fallback: alternate exploit / explore until budget is spent.
        for rnd in range(n_rounds):
            state["current_round"] = rnd + 1
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
    nominations = [
        {"round": round_id,
         "variants": [[str(sequence), float(fitness)]
                      for sequence, fitness in zip(batch.seq, batch.fitness)]}
        for round_id, batch in enumerate(state["batches"], 1)
    ]
    n_llm_no_test = sum(event["event_type"] == "agent.llm.no_test"
                        for event in state["trace"])
    return {"schema_version": "pool.v1", "dataset": spec.name,
            "strategy": "knowledge_agent" if knowledge_enabled else "agent_no_knowledge",
            "nomination": "LLM-driven tool-calling active learning (pool-based)",
            "oracle": "measured table lookup", "wild_type": spec.wt,
            "candidate_pool_size": int((spec.df.hd > 2).sum()),
            "cold_start_size": int((spec.df.hd <= 2).sum()),
            "budget_per_round": budget, "n_rounds": len(rounds), "total_budget": total_budget,
            "budget_spent": state["spent"], "strong_threshold": round(strong_thr, 4),
            "guardrail": knowledge_enabled, "no_knowledge": no_knowledge,
            "knowledge_graph_enabled": knowledge_enabled,
            "max_hd": max_hd if knowledge_enabled else None,
            "blosum_min": blosum_min if knowledge_enabled else None,
            "n_gate_rejected": state["n_gate_rejected"],
            "gate_pass_pool_size": len(gate_pass) if gate_pass is not None else None,
            "surrogate": surrogate,
            "backtrack": backtrack,
            "stall_threshold": STALL_THRESHOLD if backtrack else None,
            "redirect_rounds": list(state["redirect_rounds"]),
            "stall_flag_rounds": list(state["stall_flag_rounds"]),
            "top10_max_history": [round(float(v), 4) for v in state["top10_max_history"]],
            "llm_used": llm_used, "llm_summary": llm_summary, "agent_model": agent_model,
            "llm_round_timeout_seconds": llm_round_timeout_seconds,
            "llm_direct_test_rounds": max(0, len(rounds) - n_llm_no_test) if llm_used else 0,
            "llm_no_test_rounds": n_llm_no_test,
            "llm_round_errors": sum(event["event_type"] == "agent.llm.round_error"
                                    for event in state["trace"]),
            "n_tool_calls": len(state["trace"]),
            "summary": {"final_cum_top10_max": rounds[-1]["cum_top10_max"] if rounds else None,
                        "final_cum_top10_mean": rounds[-1]["cum_top10_mean"] if rounds else None,
                        "final_cum_n_strong": rounds[-1]["cum_n_strong"] if rounds else None,
                        "cum_top10_max_curve": [r["cum_top10_max"] for r in rounds]},
            "rounds": rounds, "nominations": nominations, "tool_trace": state["trace"]}


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
    p.add_argument("--guardrail", action="store_true",
                   help="v0.2: unbypassable Knowledge Gate before test (HD<=max-hd + mean BLOSUM62>=0)")
    p.add_argument("--no-knowledge", action="store_true",
                   help="explicit AAV ablation: disable validation, graph queries, and the knowledge gate")
    p.add_argument("--max-hd", type=int, default=4)
    p.add_argument("--blosum-min", type=float, default=0.0)
    p.add_argument("--surrogate", default="ridge", choices=("ridge", "epistasis"),
                   help="v0.4: 'epistasis' = pairwise-interaction (Potts-like) surrogate; use with --feature one_hot")
    p.add_argument("--backtrack", choices=("full", "semi"), default=None,
                   help="v0.6 meta-layer autonomy: 'full' = the LLM judges stagnation itself and "
                        "may redirect_batch; 'semi' = a hard rule flags stalls "
                        "(no cum_top10_max improvement for >=2 rounds) in the prompt. Default "
                        "acquisition in both modes is pure predicted-mean exploitation.")
    p.add_argument("--out-dir", type=Path, default=None,
                   help="default: harness/reports/<agentic-version>/<dataset>/")
    a = p.parse_args(argv)

    from evolution.results_layout import run_dir
    # folder by method generation: v0.6 = meta-layer backtrack agent (full/semi subfolders);
    # v0.5 = quality-aware agent + gate + epistasis surrogate.
    if a.out_dir is not None:
        out_dir = a.out_dir
    elif a.backtrack:
        out_dir = run_dir("agentic", a.dataset, version="v0.6") / a.backtrack
    else:
        version = ("v0.5" if a.surrogate == "epistasis" else "v0.2") if a.guardrail else None
        out_dir = run_dir("agentic", a.dataset, version=version)
    (out_dir / "figures").mkdir(parents=True, exist_ok=True)
    ev = out_dir / "agentic.events.jsonl"
    ev.unlink(missing_ok=True)
    store = EventStore(ev)
    spec = load(a.dataset, a.feature)
    rep = run_autoresearch(spec, budget=a.budget, n_rounds=a.n_rounds, seed=a.seed,
                           event_store=store, llm=not a.no_llm, model=a.model,
                           guardrail=a.guardrail, max_hd=a.max_hd, blosum_min=a.blosum_min,
                           surrogate=a.surrogate, no_knowledge=a.no_knowledge,
                           backtrack=a.backtrack)
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
          f"tool_calls={rep['n_tool_calls']} backtrack={rep.get('backtrack')} "
          f"redirects={rep.get('redirect_rounds')} stall_flags={rep.get('stall_flag_rounds')} "
          f"cum_top10_max={rep['summary']['final_cum_top10_max']} strong={rep['summary']['final_cum_n_strong']}")
    _gflag = (f" --guardrail --max-hd {a.max_hd} --blosum-min {a.blosum_min}" if a.guardrail else "")
    _kflag = " --no-knowledge" if a.no_knowledge else ""
    _sflag = (f" --surrogate {a.surrogate}" if a.surrogate != "ridge" else "")
    _bflag = (f" --backtrack {a.backtrack}" if a.backtrack else "")
    log_run("agentic",
            command=(f"python -m agent.auto_researcher --dataset {a.dataset} --feature {a.feature} "
                     f"--budget {a.budget} --n-rounds {a.n_rounds} --seed {a.seed} --model {a.model}"
                     f"{_gflag}{_kflag}{_sflag}{_bflag}"),
            params={"dataset": a.dataset, "feature": a.feature, "budget": a.budget, "n_rounds": a.n_rounds,
                    "seed": a.seed, "llm": not a.no_llm, "model": a.model,
                    "guardrail": a.guardrail, "max_hd": a.max_hd if a.guardrail else None,
                    "blosum_min": a.blosum_min if a.guardrail else None,
                    "no_knowledge": a.no_knowledge, "surrogate": a.surrogate,
                    "backtrack": a.backtrack},
            artifacts=[str(out.relative_to(ROOT)), str(ev.relative_to(ROOT))],
            summary={**rep["summary"], "llm_used": rep["llm_used"], "budget_spent": rep["budget_spent"]})
    return rep


if __name__ == "__main__":
    main()
