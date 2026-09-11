"""Tests for the four-strategy campaign engine (evolution/campaign.py).

Uses a small but *complete* 2^4 = 16-variant landscape (each of the four GB1
sites toggles between its WT residue and one alternative), so every candidate
the agent designs is guaranteed to be measurable by the oracle.
"""
from itertools import product

import pandas as pd

from evolution.campaign import run_campaign

_ALT = {0: "F", 1: "A", 2: "W", 3: "I"}  # one alternative residue per site (WT = "VDGV")
_WT = "VDGV"


def landscape() -> pd.DataFrame:
    rows = []
    for combo in product(*([wt, alt] for wt, alt in zip(_WT, _ALT.values()))):
        seq = "".join(combo)
        # Deterministic additive fitness with a mild pairwise interaction.
        f = 1.0
        f += 1.5 if seq[0] == "F" else 0.0
        f += -0.3 if seq[1] == "A" else 0.0
        f += 0.8 if seq[2] == "W" else 0.0
        f += 0.5 if seq[3] == "I" else 0.0
        f += 0.4 if (seq[0] == "F" and seq[2] == "W") else 0.0
        rows.append({"Variants": seq, "HD": sum(a != b for a, b in zip(seq, _WT)), "Fitness": round(f, 3)})
    return pd.DataFrame(rows)


class _EventProbe:
    def __init__(self):
        self.events = []

    def append(self, name, *, round_id=1, strategy="agent", actor=None, payload=None):
        self.events.append({"name": name, "round_id": round_id, "strategy": strategy, "actor": actor})


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


def test_knowledge_agent_differs_from_no_knowledge_acquisition():
    report = run_campaign(landscape(), seed=5, n_rounds=1, budget=2, pool_size=8)
    acq_no = report["strategies"]["agent_no_knowledge"]["acquisition"]
    acq_kn = report["strategies"]["knowledge_agent"]["acquisition"]
    assert acq_no != acq_kn
    assert "BLOSUM62" in acq_kn and "var" in acq_kn


def test_summary_reports_sample_efficiency():
    report = run_campaign(landscape(), seed=7, n_rounds=2, budget=2, pool_size=8)
    for name in ("random", "greedy", "agent_no_knowledge", "knowledge_agent"):
        s = report["summary"][name]
        assert len(s["cum_top10_max_curve"]) == 2
        assert s["final_cum_top10_max"] >= 1.0
