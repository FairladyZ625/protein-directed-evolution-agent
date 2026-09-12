"""Deterministic mutation validators and a lightweight NetworkX triple graph."""
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

def load_rules(path: str | Path = ROOT) -> dict:
    if yaml is None:
        raise RuntimeError("PyYAML is required to read knowledge/rules.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

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
        vid = str(v.get("id", v.get("variant", "variant"))); g.add_node(f"Variant:{vid}", kind="Variant")
        muts = v.get("mutations", v.get("mutation", [])); muts = [muts] if isinstance(muts, str) else muts
        for raw in muts:
            a, pos, b = _parse(raw); mid = f"Mutation:{a}{pos}{b}"; g.add_node(mid, kind="Mutation")
            g.add_node(f"Position:{pos}", kind="Position")
            g.add_edge(mid, f"Position:{pos}", relation="occurs_at")
            g.add_edge(f"Variant:{vid}", mid, relation="contains")
            if v.get("fitness") is not None and float(v["fitness"]) > 1:
                fid = f"Fitness:{v['fitness']}"; g.add_node(fid, kind="Fitness", value=float(v["fitness"]))
                g.add_edge(mid, fid, relation="improves")
    return g

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
