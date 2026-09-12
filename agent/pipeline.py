"""Auditable five-role GB1 pipeline. LLM calls are confined to two roles."""
from __future__ import annotations

from itertools import product
from typing import Any, Callable, Iterable, Sequence
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import UsageLimits

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

class CriticReview(BaseModel):
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

def _structured_call(port: Callable[..., Any], output_type: type[BaseModel], *args: Any) -> BaseModel:
    """Run an injected provider port behind PydanticAI's schema boundary.

    The function model is the adapter between the existing commercial-API port
    and PydanticAI.  The port cannot bypass validation: only an instance (or a
    mapping accepted by) ``output_type`` is returned by the Agent.
    """
    def invoke(_messages: list[Any], info: AgentInfo) -> ModelResponse:
        value = output_type.model_validate(port(*args))
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, value.model_dump())])

    agent = Agent(FunctionModel(invoke), output_type=output_type, retries=0)
    return agent.run_sync("Return the structured result for this pipeline role.", usage_limits=UsageLimits(request_limit=1)).output

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
        # Provider/schema failures stay inside this role and deterministically degrade.
        fallback = Hypothesis(mutations=report.substitutions[:2], rationale="Prioritize observed substitutions under R-GB1-SITES and R-MAX-MUTATIONS.", rule_ids=["R-GB1-SITES", "R-MAX-MUTATIONS"])
        try:
            out = _structured_call(self.llm, Hypothesis, report) if self.llm else fallback
        except Exception:  # provider and schema failures share the same auditable fallback
            out = fallback
        if not any(r.startswith("R-") for r in out.rule_ids) or not any("R-" in out.rationale for _ in [0]):
            out = out.model_copy(update={"rationale": out.rationale + " (R-GB1-SITES; R-MAX-MUTATIONS)", "rule_ids": [*out.rule_ids, "R-GB1-SITES"]})
        _event(event_store, "agent.role.completed", "hypothesis_generator", out.model_dump(), round_id)
        return out

class MutationDesigner:
    """Designs a combinatorial mutation library: at most one substitution per
    site (WT kept otherwise), so every candidate is a well-formed GB1 variant.
    This replaces the earlier ``combinations``-based generator, which capped the
    hypothesis at four substitutions and could place two residues at one site."""
    def run(self, hypothesis: Hypothesis, *, measured_variants: set[str], budget=10, event_store=None, round_id=1) -> list[Candidate]:
        # Group WT-anchored substitutions by site; silently drop malformed or off-site notation.
        by_site: dict[int, list[str]] = {}
        for m in dict.fromkeys(hypothesis.mutations):
            try:
                frm, pos, to = m[0], int(m[1:-1]), m[-1]
            except (ValueError, IndexError):
                continue
            if pos in SITES and frm == WT[pos] and to != WT[pos] and to not in by_site.get(pos, []):
                by_site.setdefault(pos, []).append(to)
        active = [p for p in SITES if p in by_site]
        choices = [[WT[p], *by_site[p]] for p in active]  # WT first => single mutants precede higher-order combos
        out: list[Candidate] = []
        for combo in product(*choices) if active else []:
            chosen = dict(zip(active, combo))
            muts = [f"{WT[p]}{p}{aa}" for p, aa in chosen.items() if aa != WT[p]]
            if not muts:
                continue  # skip the all-WT sequence
            seq = "".join(chosen.get(p, WT[p]) for p in SITES)
            if seq not in measured_variants:
                continue
            out.append(Candidate(mutations=muts, sequence=seq))
            if len(out) >= budget:
                break
        _event(event_store, "agent.role.completed", "mutation_designer", {"candidates": [c.model_dump() for c in out]}, round_id)
        return out

class FitnessEvaluator:
    def __init__(self, predictor: Callable[[Sequence[str]], Any]): self.predictor = predictor
    def run(self, candidates: list[Candidate], *, event_store=None, round_id=1) -> list[ScoredCandidate]:
        vals = self.predictor([c.sequence for c in candidates]); means, vars_ = vals if isinstance(vals, tuple) else (vals, [0.0]*len(candidates))
        out=[ScoredCandidate(**c.model_dump(), mean=float(m), variance=float(v)) for c,m,v in zip(candidates, means, vars_)]
        _event(event_store, "agent.role.completed", "fitness_evaluator", {"candidates": [x.model_dump() for x in out]}, round_id); return out

class ScientificCritic:
    def __init__(self, llm: Callable[[ScoredCandidate, list[dict[str, Any]]], CriticReview] | None = None, *, no_knowledge: bool = False):
        self.llm=llm; self.no_knowledge=no_knowledge
    def run(self, scored: list[ScoredCandidate], *, event_store=None, round_id=1) -> tuple[list[ScoredCandidate], list[CriticResult]]:
        # no_knowledge=True is the ablation: validate_candidate returns [] so all(...) is True (no gating).
        accepted=[]; checks=[]
        for c in scored:
            rules=validate_candidate(c.mutations, no_knowledge=self.no_knowledge)
            gate_rules = [rule for rule in rules if rule["enforcement"] == "gate"]
            ok=all(rule["pass"] for rule in gate_rules)
            note = "accepted" if ok else "rejected by knowledge rules"
            if self.llm and ok:
                try:
                    note = _structured_call(self.llm, CriticReview, c, rules).note
                except Exception:
                    note = "accepted (deterministic critic fallback)"
            result=CriticResult(accepted=ok, score=c.mean, rule_check=rules, note=note); checks.append(result)
            if ok: accepted.append(c)
        _event(event_store, "agent.role.completed", "scientific_critic", {"critiques": [x.model_dump() for x in checks]}, round_id); return accepted, checks

def run_pipeline(pool, predictor, *, event_store=None, llm_hypothesis=None, llm_critic=None, budget=10,
                 round_id=1, no_knowledge=False, measurable_variants=None):
    """Run the five roles for one round.

    ``pool`` is what已经 measured — rows carrying fitness labels, i.e. the training set.
    ``measurable_variants`` is what the oracle *can* answer — the full candidate space
    (GB1: 149,361 variants). The two are different sets and conflating them breaks the
    designer: nominations are by definition not yet measured, so intersecting candidates
    against the pool-derived set filters out every new nomination and the round yields
    nothing. Callers that own a candidate space MUST pass it; ``None`` falls back to the
    pool-derived set, which is only correct when the pool already spans the space
    (synthetic fixtures do, the real campaign does not).
    """
    rows = list(pool)
    measured_variants = (
        {str(v) for v in measurable_variants} if measurable_variants is not None
        else {_variant_from_row(row) for row in rows}
    )
    report=DataAnalyst().run(rows,event_store=event_store,round_id=round_id); hyp=HypothesisGenerator(llm_hypothesis).run(report,event_store=event_store,round_id=round_id); cand=MutationDesigner().run(hyp,measured_variants=measured_variants,budget=budget,event_store=event_store,round_id=round_id); scored=FitnessEvaluator(predictor).run(cand,event_store=event_store,round_id=round_id); accepted, critiques=ScientificCritic(llm_critic, no_knowledge=no_knowledge).run(scored,event_store=event_store,round_id=round_id); return PipelineResult(report=report,hypothesis=hyp,candidates=scored,accepted=accepted,critiques=critiques)

def _variant_from_row(row: dict[str, Any]) -> str:
    explicit = row.get("Variants", row.get("variant", row.get("sequence")))
    if explicit is not None and len(str(explicit)) == len(SITES):
        return str(explicit)
    residues = dict(WT)
    mutations = row.get("mutations", row.get("mutation", []))
    mutations = [mutations] if isinstance(mutations, str) else mutations
    for mutation in mutations:
        try:
            residues[int(mutation[1:-1])] = mutation[-1]
        except (TypeError, ValueError, IndexError):
            continue
    return "".join(residues[position] for position in SITES)
