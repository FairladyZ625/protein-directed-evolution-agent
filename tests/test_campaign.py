"""Tests for the four-strategy campaign engine (evolution/campaign.py).

Uses a small but *complete* 2^4 = 16-variant landscape (each of the four GB1
sites toggles between its WT residue and one alternative), so every candidate
the agent designs is guaranteed to be measurable by the oracle.
"""
from itertools import product

import pandas as pd
import pytest

import evolution.campaign as campaign
from evolution.campaign import RANDOM_SEEDS, plot_campaign, run_campaign

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


@pytest.fixture(autouse=True)
def _supply_complete_measured_space(monkeypatch):
    """Give the pipeline the fixture's complete truth space independently of history.

    Production GB1 has a 149,361-variant measurable set. This synthetic analogue
    has 16 variants; bare ``_pool_records`` contains only cold-start history, so it
    must be supplemented or measured-space filtering correctly removes every new
    nomination.
    """
    original = campaign.run_pipeline
    measured_space = [{"Variants": variant} for variant in landscape()["Variants"]]

    def run_with_measured_space(pool, *args, **kwargs):
        return original([*pool, *measured_space], *args, **kwargs)

    monkeypatch.setattr(campaign, "run_pipeline", run_with_measured_space)


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


def test_agent_knowledge_ablation_reaches_pipeline(monkeypatch):
    original = campaign.run_pipeline
    observed = []

    def probe(*args, **kwargs):
        observed.append({"no_knowledge": kwargs["no_knowledge"],
                         "has_hypothesis_port": "llm_hypothesis" in kwargs,
                         "has_critic_port": "llm_critic" in kwargs})
        return original(*args, **kwargs)

    monkeypatch.setattr(campaign, "run_pipeline", probe)
    run_campaign(landscape(), seed=1, n_rounds=1, budget=2, pool_size=8)
    assert observed == [
        {"no_knowledge": True, "has_hypothesis_port": True, "has_critic_port": True},
        {"no_knowledge": False, "has_hypothesis_port": True, "has_critic_port": True},
    ]


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


def test_random_baseline_is_repeated_over_fixed_independent_seeds():
    report = run_campaign(landscape(), seed=999, n_rounds=2, budget=2, pool_size=8)
    aggregate = report["strategies"]["random"]["multi_seed"]
    assert aggregate["seeds"] == list(RANDOM_SEEDS)
    assert aggregate["n_runs"] == len(RANDOM_SEEDS)
    assert all("cum_top10_max_mean" in row and "cum_top10_max_std" in row
               for row in aggregate["rounds"])


def test_audit_events_cover_each_dbtl_step():
    probe = _EventProbe()
    run_campaign(landscape(), seed=2, n_rounds=1, budget=2, pool_size=8, event_store=probe)
    names = {event["name"] for event in probe.events}
    assert {"campaign.propose.completed", "campaign.oracle.completed",
            "campaign.refill.completed", "campaign.retrain.completed"} <= names


def test_topk_residue_concentration_is_reported():
    report = run_campaign(landscape(), seed=4, n_rounds=1, budget=2, pool_size=8)
    for result in report["strategies"].values():
        concentration = result["topk_concentration"]
        assert concentration["n_topk_observations"] == 2
        assert set(concentration["positions"]) == {"39", "40", "41", "54"}
        for position in concentration["positions"].values():
            assert 0.0 <= position["dominant_fraction"] <= 1.0
            assert 0.0 <= position["mutation_fraction"] <= 1.0


def test_object_fitness_is_coerced_and_random_band_is_drawn(tmp_path, monkeypatch):
    frame = landscape()
    frame["Fitness"] = frame["Fitness"].astype(str)
    report = run_campaign(frame, seed=6, n_rounds=1, budget=2, pool_size=8)

    import matplotlib.axes
    calls = []
    original = matplotlib.axes.Axes.fill_between

    def fill_between(self, *args, **kwargs):
        calls.append(args)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(matplotlib.axes.Axes, "fill_between", fill_between)
    plot_campaign(report, tmp_path / "curve.png")
    assert calls
    assert (tmp_path / "curve.png").is_file()
