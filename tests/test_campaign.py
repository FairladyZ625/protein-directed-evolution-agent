"""Tests for the four-strategy campaign engine (evolution/campaign.py).

Uses a small but *complete* 2^4 = 16-variant landscape (each of the four GB1
sites toggles between its WT residue and one alternative), so every candidate
the agent designs is guaranteed to be measurable by the oracle.
"""
from itertools import product

import pandas as pd

from evolution.campaign import run_campaign

_ALT = {0: "I", 1: "E", 2: "C", 3: "I"}  # rule-passing alternatives (WT = "VDGV")
_WT = "VDGV"


def landscape(alternatives: dict[int, str] = _ALT) -> pd.DataFrame:
    rows = []
    for combo in product(*([wt, alt] for wt, alt in zip(_WT, alternatives.values()))):
        seq = "".join(combo)
        # Deterministic additive fitness with a mild pairwise interaction.
        f = 1.0
        f += 1.5 if seq[0] != _WT[0] else 0.0
        f += -0.3 if seq[1] != _WT[1] else 0.0
        f += 0.8 if seq[2] != _WT[2] else 0.0
        f += 0.5 if seq[3] == "I" else 0.0
        f += 0.4 if (seq[0] != _WT[0] and seq[2] != _WT[2]) else 0.0
        rows.append({"Variants": seq, "HD": sum(a != b for a, b in zip(seq, _WT)), "Fitness": round(f, 3)})
    return pd.DataFrame(rows)


class _EventProbe:
    def __init__(self):
        self.events = []

    def append(self, name, *, round_id=1, strategy="agent", actor=None, payload=None):
        self.events.append({"name": name, "round_id": round_id, "strategy": strategy,
                            "actor": actor, "payload": payload})


def test_four_strategies_share_oracle_and_budget():
    report = run_campaign(landscape(), seed=3, n_rounds=2, budget=2, pool_size=8)
    assert set(report["strategies"]) == {"random", "greedy", "agent_no_knowledge", "knowledge_agent"}
    assert report["oracle"] == "measured table lookup"
    assert report["candidate_space_size"] == 16
    for result in report["strategies"].values():
        assert [r["n_nominated"] for r in result["rounds"]] == [2, 2]
        assert all("cum_top10_max" in r for r in result["rounds"])


def test_campaign_is_reproducible():
    a = run_campaign(landscape(), seed=9, n_rounds=2, budget=2, pool_size=8)
    b = run_campaign(landscape(), seed=9, n_rounds=2, budget=2, pool_size=8)
    assert a == b


def test_agent_strategies_actually_invoke_the_five_role_pipeline():
    """Regression guard: ③④ must route through agent.pipeline.run_pipeline, not a
    predictor shortcut. If they did not, no role events would be emitted."""
    probe = _EventProbe()
    run_campaign(landscape(), seed=1, n_rounds=1, budget=2, pool_size=8, event_store=probe)
    role_events = [e for e in probe.events if e["name"] == "agent.role.completed"]
    actors = {e["actor"] for e in role_events}
    assert {"data_analyst", "hypothesis_generator", "mutation_designer",
            "fitness_evaluator", "scientific_critic"} <= actors


def test_knowledge_critic_rejects_candidate_in_campaign_event():
    """Positive control: the knowledge arm must emit a concrete rejected candidate.

    V39F is designable but violates the local BLOSUM rules.  The no-knowledge
    arm remains a clean ablation and therefore has no rejected critiques.
    """
    probe = _EventProbe()
    radical = {0: "F", 1: "E", 2: "C", 3: "I"}
    run_campaign(landscape(radical), seed=1, n_rounds=1, budget=2, pool_size=8,
                 event_store=probe)
    critic_events = [e for e in probe.events
                     if e["name"] == "agent.role.completed"
                     and e["actor"] == "scientific_critic"]
    assert len(critic_events) == 2
    no_knowledge, knowledge = critic_events
    assert all(c["accepted"] for c in no_knowledge["payload"]["critiques"])
    rejected = [c for c in knowledge["payload"]["critiques"] if not c["accepted"]]
    assert rejected, "knowledge Critic must reject at least one designed candidate"
    assert all(c["sequence"] and c["mutations"] for c in rejected)
    assert any("R-BLOSUM" in c["note"] for c in rejected)


def test_knowledge_agent_differs_from_no_knowledge_acquisition():
    report = run_campaign(landscape(), seed=5, n_rounds=1, budget=2, pool_size=8)
    acq_no = report["strategies"]["agent_no_knowledge"]["acquisition"]
    acq_kn = report["strategies"]["knowledge_agent"]["acquisition"]
    assert acq_no != acq_kn
    assert "BLOSUM62" in acq_kn and "var" in acq_kn


def test_structured_llm_failure_is_explicit_fallback(monkeypatch):
    def malformed(*args, **kwargs):
        raise ValueError("invalid structured output")

    monkeypatch.setattr("evolution.campaign.chat_structured", malformed)
    report = run_campaign(landscape(), seed=5, n_rounds=1, budget=2, pool_size=8,
                          use_llm=True)
    no_knowledge = report["strategies"]["agent_no_knowledge"]["rounds"][0]
    knowledge = report["strategies"]["knowledge_agent"]["rounds"][0]
    assert no_knowledge["llm_source"] == "fallback"
    assert no_knowledge["hypothesis_llm_calls"] == 1
    assert no_knowledge["hypothesis_llm_failures"] == 1
    assert no_knowledge["critic_llm_calls"] == 0  # clean no-knowledge ablation
    assert knowledge["llm_source"] == "fallback"
    assert knowledge["hypothesis_llm_failures"] == 1
    assert knowledge["critic_llm_calls"] == 1
    assert knowledge["critic_llm_failures"] == 1
    assert knowledge["hypothesis_llm_model"] is None
    assert knowledge["critic_llm_model"] is None
    assert knowledge["hypothesis_llm_error"] == "invalid structured output"
    assert knowledge["critic_llm_error"] == "invalid structured output"


def test_summary_reports_sample_efficiency():
    report = run_campaign(landscape(), seed=7, n_rounds=2, budget=2, pool_size=8)
    for name in ("random", "greedy", "agent_no_knowledge", "knowledge_agent"):
        s = report["summary"][name]
        assert len(s["cum_top10_max_curve"]) == 2
        assert s["final_cum_top10_max"] >= 1.0
