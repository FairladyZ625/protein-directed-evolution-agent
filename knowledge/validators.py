"""Deterministic mutation validators and a lightweight NetworkX triple graph."""
from functools import lru_cache
from pathlib import Path
import re
from typing import Any, Iterable
import argparse
import json

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None
import networkx as nx

ROOT = Path(__file__).with_name("rules.yaml")
AA = set("ACDEFGHIKLMNPQRSTVWY")

@lru_cache(maxsize=8)
def _parse_rules(path: str, _stamp: tuple[float, int]) -> dict:
    if yaml is None:
        raise RuntimeError("PyYAML is required to read knowledge/rules.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_rules(path: str | Path = ROOT) -> dict:
    """Load the rule set, parsing the YAML at most once per (path, mtime, size).

    ``validate_mutations`` calls this on every candidate, and one campaign round now
    gates a library of up to 6,561 candidates. Re-parsing the YAML each time cost
    14 ms/call — 94 s per knowledge_agent round, which is where the demo's
    "auto-recommend" button appeared to hang and why every knowledge run was slow.
    Keying on (mtime, size) rather than the path alone keeps tests that write a
    modified rules file to the same path honest.

    The returned dict is shared between callers; treat it as read-only.
    """
    resolved = Path(path)
    stat = resolved.stat()
    return _parse_rules(str(resolved), (stat.st_mtime, stat.st_size))

def _parse(item: Any) -> tuple[str, int, str]:
    if isinstance(item, dict):
        return str(item["from"]), int(item["position"]), str(item["to"])
    m = re.fullmatch(r"([A-Za-z])(\d+)([A-Za-z*])", str(item).strip())
    if not m:
        raise ValueError(f"invalid mutation notation: {item!r}")
    return m.group(1).upper(), int(m.group(2)), m.group(3).upper()

def _score(a: str, b: str, matrix: dict) -> int | None:
    direct = matrix.get(a, {})
    if b in direct:
        return direct[b]
    reverse = matrix.get(b, {})
    if a in reverse:
        return reverse[a]
    return None

def _mutation_key(item: Any) -> tuple[str, int, str]:
    """Normalize mutation notation for exact historical-single matching."""
    return _parse(item)

def validate_mutations(mutations: Iterable[Any], *, no_knowledge: bool = False,
                       rules: dict | None = None,
                       historical_good: Iterable[Any] | None = None) -> list[dict]:
    """Return one result per applicable rule (or [] for the ablation)."""
    if no_knowledge:
        return []
    cfg = rules or load_rules()
    muts = [_parse(m) for m in mutations]
    historical = {_mutation_key(m) for m in (historical_good or [])}
    enforcement = {rule["id"]: rule.get("enforcement", "gate") for rule in cfg["rules"]}
    out = []
    def add(rule_id, passed, note):
        out.append({
            "rule_id": rule_id,
            "enforcement": enforcement[rule_id],
            "pass": bool(passed),
            "note": note,
        })
    add("R-MAX-MUTATIONS", len(muts) <= 4, f"{len(muts)} substitutions (limit 4)")
    add("R-NO-STOP", all(a in AA and b in AA for a, _, b in muts), "standard amino-acid alphabet")
    for a, pos, b in muts:
        score = _score(a, b, cfg["blosum62"])
        if score is not None:
            add("R-BLOSUM-CONSERVATIVE", score >= 1, f"{a}{pos}{b}: BLOSUM62={score}")
            add("R-BLOSUM-AGGRESSIVE", score > -1, f"{a}{pos}{b}: BLOSUM62={score}")
        add("R-GB1-SITES", pos in {39, 40, 41, 54}, f"position {pos}")
    matched = [f"{a}{pos}{b}" for a, pos, b in muts if (a, pos, b) in historical]
    add(
        "R-PRIORITIZE-HISTORICAL",
        bool(matched),
        "historically high-fitness single mutants: " + (", ".join(matched) if matched else "none"),
    )
    return out

def validate_candidate(candidate: Any, *, no_knowledge: bool = False,
                       historical_good: Iterable[Any] | None = None) -> list[dict]:
    if isinstance(candidate, str): candidate = [candidate]
    return validate_mutations(
        candidate,
        no_knowledge=no_knowledge,
        historical_good=historical_good,
    )

def main(argv: list[str] | None = None) -> int:
    """CLI used by agents and demos: ``python -m knowledge.validators V39I``."""
    parser = argparse.ArgumentParser(description="Validate GB1 mutation candidates")
    parser.add_argument("mutations", nargs="*", help="mutation notation, e.g. V39I")
    parser.add_argument("--no-knowledge", action="store_true", help="disable all knowledge constraints")
    args = parser.parse_args(argv)
    print(json.dumps(validate_candidate(args.mutations, no_knowledge=args.no_knowledge), ensure_ascii=False))
    return 0

def build_knowledge_graph(variants: Iterable[dict] | None = None, *, rules: dict | None = None) -> nx.MultiDiGraph:
    cfg = rules or load_rules(); g = nx.MultiDiGraph()
    for aa, props in cfg["amino_acids"].items():
        g.add_node(f"AminoAcid:{aa}", kind="AminoAcid")
        for key, value in props.items():
            if key != "name":
                p = f"Property:{key}:{value}"; g.add_node(p, kind="Property", value=value)
                g.add_edge(f"AminoAcid:{aa}", p, relation="has_property")
    for v in variants or []:
        vid = str(v.get("id", v.get("variant", "variant")))
        fitness = None if v.get("fitness") is None else float(v["fitness"])
        g.add_node(f"Variant:{vid}", kind="Variant", fitness=fitness)
        muts = v.get("mutations", v.get("mutation", [])); muts = [muts] if isinstance(muts, str) else muts
        for raw in muts:
            a, pos, b = _parse(raw); mid = f"Mutation:{a}{pos}{b}"
            g.add_node(mid, kind="Mutation", from_aa=a, position=pos, to_aa=b)
            g.add_node(f"Position:{pos}", kind="Position")
            g.add_edge(mid, f"Position:{pos}", relation="occurs_at")
            g.add_edge(f"Variant:{vid}", mid, relation="contains")
            g.add_edge(mid, f"AminoAcid:{b}", relation="changes_to")
            if fitness is not None and fitness > 1:
                fid = f"Fitness:{fitness}"; g.add_node(fid, kind="Fitness", value=fitness)
                g.add_edge(mid, fid, relation="improves")
    return g


def query_amino_acid_properties(graph: nx.MultiDiGraph, amino_acid: str) -> dict:
    """Return property nodes connected to an amino acid in a graph snapshot."""
    aa = str(amino_acid).upper()
    node = f"AminoAcid:{aa}"
    if node not in graph:
        return {"amino_acid": aa, "properties": {}}
    properties = {}
    for _, target, edge in graph.out_edges(node, data=True):
        if edge.get("relation") != "has_property":
            continue
        _, key, value = target.split(":", 2)
        properties[key] = graph.nodes[target].get("value", value)
    return {"amino_acid": aa, "properties": properties}


def query_position_mutations(graph: nx.MultiDiGraph, position: int, *, limit: int = 5) -> list[dict]:
    """Summarise measured mutation/fitness associations at one position.

    The graph must be built from already-measured variants.  Fitness values are
    aggregated as associations, never interpreted as single-mutation causal effects.
    """
    position = int(position)
    rows = []
    for node, attrs in graph.nodes(data=True):
        if attrs.get("kind") != "Mutation" or attrs.get("position") != position:
            continue
        observed = []
        for variant, _, edge in graph.in_edges(node, data=True):
            if edge.get("relation") != "contains":
                continue
            fitness = graph.nodes[variant].get("fitness")
            if fitness is not None:
                observed.append(float(fitness))
        if observed:
            rows.append({
                "mutation": node.removeprefix("Mutation:"),
                "n_measured": len(observed),
                "fitness_mean": float(sum(observed) / len(observed)),
                "fitness_max": float(max(observed)),
            })
    rows.sort(key=lambda row: (-row["fitness_mean"], -row["n_measured"], row["mutation"]))
    return rows[:max(0, int(limit))]


def query_mutation_context(graph: nx.MultiDiGraph, mutation: Any) -> dict:
    """Query exact-mutation history plus the mutant amino acid's properties."""
    source, position, target = _parse(mutation)
    mid = f"Mutation:{source}{position}{target}"
    observed = []
    if mid in graph:
        for variant, _, edge in graph.in_edges(mid, data=True):
            if edge.get("relation") != "contains":
                continue
            fitness = graph.nodes[variant].get("fitness")
            if fitness is not None:
                observed.append(float(fitness))
    return {
        "mutation": f"{source}{position}{target}",
        "position": position,
        "n_measured": len(observed),
        "fitness_mean": None if not observed else float(sum(observed) / len(observed)),
        "fitness_max": None if not observed else float(max(observed)),
        "mutant_properties": query_amino_acid_properties(graph, target)["properties"],
        "position_leaders": query_position_mutations(graph, position),
        "interpretation": "measured association; not a causal single-mutation effect",
    }

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
