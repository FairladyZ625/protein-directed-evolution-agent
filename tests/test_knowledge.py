from knowledge.validators import build_knowledge_graph, validate_candidate


def test_conservative_and_aggressive_rules():
    conservative = validate_candidate("V39I")
    assert any(r["rule_id"] == "R-BLOSUM-CONSERVATIVE" and r["pass"] for r in conservative)
    aggressive = validate_candidate("V39W")
    assert any(r["rule_id"] == "R-BLOSUM-AGGRESSIVE" and not r["pass"] for r in aggressive)


def test_constraints_and_ablation():
    assert any(not r["pass"] for r in validate_candidate(["V39I", "D40E", "G41A", "V54L", "V39A"]))
    assert validate_candidate("V39I", no_knowledge=True) == []


def test_triples():
    graph = build_knowledge_graph([{"id": "v1", "mutations": ["V39I"], "fitness": 2.0}])
    assert graph.nodes["AminoAcid:V"]["kind"] == "AminoAcid"
    relations = {(u, d["relation"]) for u, _, d in graph.edges(data=True)}
    assert ("Mutation:V39I", "occurs_at") in relations
    assert ("Variant:v1", "contains") in relations
    assert ("Mutation:V39I", "improves") in relations
