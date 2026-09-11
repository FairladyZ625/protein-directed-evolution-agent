"""Unit tests for the five-role agent pipeline (agent/pipeline.py).

Pure unit tests: no torch, no ESM, no GB1 data on disk. The fitness predictor
and both LLM ports are injected as fakes, so the deterministic skeleton and the
injectable-port contract are exercised in isolation.
"""
from __future__ import annotations

import pytest

from agent.pipeline import (
    AnalystReport,
    Hypothesis,
    PipelineResult,
    ScoredCandidate,
    run_pipeline,
)


class _EventProbe:
    """Minimal event sink matching the store.append contract used by the pipeline."""

    def __init__(self) -> None:
        self.events: list[dict] = []

    def append(self, name, *, round_id=1, strategy="agent", actor=None, payload=None):
        self.events.append(
            {"name": name, "round_id": round_id, "strategy": strategy, "actor": actor, "payload": payload}
        )


def _fake_predictor(sequences):
    """Deterministic stand-in for the trained ladder: mean rises with non-WT content."""
    means = [1.0 + 0.5 * sum(1 for ch in seq if ch not in "VDGV") for seq in sequences]
    variances = [0.1] * len(sequences)
    return means, variances


# Conservative substitutions (BLOSUM62 >= 1) at the four GB1 sites, so the
# knowledge rules accept them: V39I=3, D40E=2, V54I=3.
_CONSERVATIVE_POOL = [
    {"mutations": ["V39I"], "fitness": 2.0},
    {"mutations": ["D40E"], "fitness": 1.8},
    {"mutations": ["V54I"], "fitness": 1.5},
]


def test_deterministic_fallback_produces_valid_result():
    result = run_pipeline(_CONSERVATIVE_POOL, _fake_predictor, budget=10)
    assert isinstance(result, PipelineResult)
    # DataAnalyst saw all three observations at the four canonical sites.
    assert result.report.n_observations == 3
    assert set(result.report.position_gains) == {39, 40, 41, 54}
    # Fallback hypothesis always cites the locked rule ids.
    assert "R-GB1-SITES" in result.hypothesis.rule_ids
    # Candidates are scored and every accepted one passed all knowledge rules.
    assert result.candidates, "expected at least one scored candidate"
    assert all(isinstance(c, ScoredCandidate) for c in result.candidates)
    assert len(result.critiques) == len(result.candidates)
    for acc in result.accepted:
        assert acc in result.candidates


def test_injectable_llm_ports_are_invoked():
    hypo_calls: list[AnalystReport] = []
    critic_calls: list = []

    def fake_hypothesis(report: AnalystReport) -> Hypothesis:
        hypo_calls.append(report)
        return Hypothesis(
            mutations=["V39I", "D40E"],
            rationale="LLM proposal grounded in R-GB1-SITES.",
            rule_ids=["R-GB1-SITES", "R-MAX-MUTATIONS"],
        )

    def fake_critic(candidate: ScoredCandidate, rules: list[dict]) -> str:
        critic_calls.append((candidate, rules))
        return "LLM critic: accepted"

    result = run_pipeline(
        _CONSERVATIVE_POOL,
        _fake_predictor,
        llm_hypothesis=fake_hypothesis,
        llm_critic=fake_critic,
        budget=10,
    )
    # Hypothesis port received exactly one AnalystReport.
    assert len(hypo_calls) == 1 and isinstance(hypo_calls[0], AnalystReport)
    # The LLM hypothesis mutations flowed into the designed candidates.
    assert result.hypothesis.mutations == ["V39I", "D40E"]
    # Critic port is invoked only for rule-passing candidates; note is its output.
    assert critic_calls, "critic port should be invoked for accepted candidates"
    assert any(c.note == "LLM critic: accepted" for c in result.critiques)


def test_events_emitted_for_all_five_roles():
    probe = _EventProbe()
    run_pipeline(_CONSERVATIVE_POOL, _fake_predictor, event_store=probe, budget=10, round_id=7)
    actors = {e["actor"] for e in probe.events}
    assert actors == {
        "data_analyst",
        "hypothesis_generator",
        "mutation_designer",
        "fitness_evaluator",
        "scientific_critic",
    }
    # Round id threads through every event.
    assert all(e["round_id"] == 7 for e in probe.events)


def test_designer_filters_off_site_mutation():
    """An off-site hypothesis is dropped structurally: no candidate is ever built."""

    def off_site_hypothesis(report: AnalystReport) -> Hypothesis:
        # Position 10 is not in {39,40,41,54}; the designer's structural guard
        # (site membership + WT-residue match) rejects it before scoring.
        return Hypothesis(mutations=["A10G"], rationale="off-site probe", rule_ids=["R-GB1-SITES"])

    result = run_pipeline(
        _CONSERVATIVE_POOL,
        _fake_predictor,
        llm_hypothesis=off_site_hypothesis,
        budget=10,
    )
    assert result.candidates == []
    assert result.accepted == []
    assert result.critiques == []


def test_critic_rejects_non_conservative_substitution():
    """An on-site but non-conservative substitution passes the designer yet the
    Scientific Critic rejects it on the BLOSUM62 rule."""

    def aggressive_hypothesis(report: AnalystReport) -> Hypothesis:
        # V39D is on-site (V is WT at 39) so the designer builds it, but
        # BLOSUM62(V,D) = -3 fails both the conservative and aggressive rules.
        return Hypothesis(mutations=["V39D"], rationale="aggressive probe", rule_ids=["R-GB1-SITES"])

    result = run_pipeline(
        _CONSERVATIVE_POOL,
        _fake_predictor,
        llm_hypothesis=aggressive_hypothesis,
        budget=10,
    )
    # Designer built the candidate, but the critic could not accept it.
    assert result.candidates, "on-site candidate should be designed"
    assert result.accepted == []
    assert all(not c.accepted for c in result.critiques)
    # The failing BLOSUM rule is surfaced in the rule_check trail.
    failed_rules = {r["rule_id"] for c in result.critiques for r in c.rule_check if not r["pass"]}
    assert "R-BLOSUM-CONSERVATIVE" in failed_rules


def test_budget_caps_candidate_count():
    result = run_pipeline(_CONSERVATIVE_POOL, _fake_predictor, budget=2)
    assert len(result.candidates) <= 2
