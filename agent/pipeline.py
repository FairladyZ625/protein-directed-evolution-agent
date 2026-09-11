"""Auditable five-role GB1 pipeline. LLM calls are confined to two roles."""
from __future__ import annotations

from itertools import combinations
from typing import Any, Callable, Iterable, Sequence
from pydantic import BaseModel, Field

from knowledge.validators import validate_candidate

WT = {39: "V", 40: "D", 41: "G", 54: "V"}
SITES = tuple(WT)

class AnalystReport(BaseModel):
    position_gains: dict[int, float] = Field(default_factory=dict)
    substitutions: list[str] = Field(default_factory=list)
    n_observations: int = 0

class Hypothesis(BaseModel):
    mutations: list[str] = Field(default_factory=list)
    rationale: str
    rule_ids: list[str] = Field(default_factory=list)

class Candidate(BaseModel):
    mutations: list[str]
    sequence: str

class ScoredCandidate(Candidate):
    mean: float
    variance: float

class CriticResult(BaseModel):
    accepted: bool
    score: float
    rule_check: list[dict[str, Any]] = Field(default_factory=list)
    note: str

class PipelineResult(BaseModel):
    report: AnalystReport
    hypothesis: Hypothesis
    candidates: list[ScoredCandidate]
    accepted: list[ScoredCandidate]
    critiques: list[CriticResult]

def _event(store, name, actor, payload, round_id=1, strategy="agent"):
    if store is not None:
        store.append(name, round_id=round_id, strategy=strategy, actor=actor, payload=payload)

class DataAnalyst:
    def run(self, pool: Iterable[dict[str, Any]], *, event_store=None, round_id=1) -> AnalystReport:
        rows = list(pool); sums: dict[int, list[float]] = {p: [] for p in SITES}; subs = []
        for row in rows:
            muts = row.get("mutations", row.get("mutation", [])); muts = [muts] if isinstance(muts, str) else muts
            fit = float(row.get("fitness", 0.0))
            for m in muts:
                if isinstance(m, str) and len(m) >= 3:
                    pos = int(m[1:-1])
                    if pos in sums: sums[pos].append(fit); subs.append(m)
        gains = {p: (sum(v) / len(v) if v else 0.0) for p, v in sums.items()}
        out = AnalystReport(position_gains=gains, substitutions=sorted(set(subs)), n_observations=len(rows))
        _event(event_store, "agent.role.completed", "data_analyst", out.model_dump(), round_id)
        return out

class HypothesisGenerator:
    def __init__(self, llm: Callable[[AnalystReport], Hypothesis] | None = None): self.llm = llm
    def run(self, report: AnalystReport, *, event_store=None, round_id=1) -> Hypothesis:
        # Optional PydanticAI/provider adapter; deterministic fallback is offline and auditable.
        out = self.llm(report) if self.llm else Hypothesis(mutations=report.substitutions[:2], rationale="Prioritize observed substitutions under R-GB1-SITES and R-MAX-MUTATIONS.", rule_ids=["R-GB1-SITES", "R-MAX-MUTATIONS"])
        if not any(r.startswith("R-") for r in out.rule_ids) or not any("R-" in out.rationale for _ in [0]):
            out = out.model_copy(update={"rationale": out.rationale + " (R-GB1-SITES; R-MAX-MUTATIONS)", "rule_ids": [*out.rule_ids, "R-GB1-SITES"]})
        _event(event_store, "agent.role.completed", "hypothesis_generator", out.model_dump(), round_id)
        return out

class MutationDesigner:
    def run(self, hypothesis: Hypothesis, *, budget=10, event_store=None, round_id=1) -> list[Candidate]:
        muts = list(dict.fromkeys(hypothesis.mutations))[:4]; out=[]
        for n in range(1, min(4, len(muts))+1):
            for combo in combinations(muts, n):
                parsed=[]
                try:
                    for m in combo: parsed.append((m[0], int(m[1:-1]), m[-1]))
                    seq = "".join(WT[p] if p not in {x[1] for x in parsed} else next(x[2] for x in parsed if x[1]==p) for p in SITES)
                    if all(x[1] in SITES and x[0] == WT[x[1]] for x in parsed): out.append(Candidate(mutations=list(combo), sequence=seq))
                except (ValueError, IndexError): continue
                if len(out) >= budget: break
            if len(out) >= budget: break
        _event(event_store, "agent.role.completed", "mutation_designer", {"candidates": [c.model_dump() for c in out]}, round_id)
        return out

class FitnessEvaluator:
    def __init__(self, predictor: Callable[[Sequence[str]], Any]): self.predictor = predictor
    def run(self, candidates: list[Candidate], *, event_store=None, round_id=1) -> list[ScoredCandidate]:
        vals = self.predictor([c.sequence for c in candidates]); means, vars_ = vals if isinstance(vals, tuple) else (vals, [0.0]*len(candidates))
        out=[ScoredCandidate(**c.model_dump(), mean=float(m), variance=float(v)) for c,m,v in zip(candidates, means, vars_)]
        _event(event_store, "agent.role.completed", "fitness_evaluator", {"candidates": [x.model_dump() for x in out]}, round_id); return out

class ScientificCritic:
    def __init__(self, llm: Callable[[ScoredCandidate, list[dict[str, Any]]], str] | None = None): self.llm=llm
    def run(self, scored: list[ScoredCandidate], *, event_store=None, round_id=1) -> tuple[list[ScoredCandidate], list[CriticResult]]:
        accepted=[]; checks=[]
        for c in scored:
            rules=validate_candidate(c.mutations); ok=all(x["pass"] for x in rules); note=self.llm(c,rules) if self.llm and ok else ("accepted" if ok else "rejected by knowledge rules")
            result=CriticResult(accepted=ok, score=c.mean, rule_check=rules, note=note); checks.append(result)
            if ok: accepted.append(c)
        _event(event_store, "agent.role.completed", "scientific_critic", {"critiques": [x.model_dump() for x in checks]}, round_id); return accepted, checks

def run_pipeline(pool, predictor, *, event_store=None, llm_hypothesis=None, llm_critic=None, budget=10, round_id=1):
    report=DataAnalyst().run(pool,event_store=event_store,round_id=round_id); hyp=HypothesisGenerator(llm_hypothesis).run(report,event_store=event_store,round_id=round_id); cand=MutationDesigner().run(hyp,budget=budget,event_store=event_store,round_id=round_id); scored=FitnessEvaluator(predictor).run(cand,event_store=event_store,round_id=round_id); accepted, critiques=ScientificCritic(llm_critic).run(scored,event_store=event_store,round_id=round_id); return PipelineResult(report=report,hypothesis=hyp,candidates=scored,accepted=accepted,critiques=critiques)
