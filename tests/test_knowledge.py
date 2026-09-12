from knowledge.validators import (
    build_knowledge_graph,
    query_amino_acid_properties,
    query_mutation_context,
    query_position_mutations,
    validate_candidate,
)


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


def test_graph_queries_use_measured_associations_and_properties():
    graph = build_knowledge_graph([
        {"id": "measured-1", "mutations": ["A0S", "A2G"], "fitness": 2.0},
        {"id": "measured-2", "mutations": ["A0S"], "fitness": 4.0},
        {"id": "measured-3", "mutations": ["A0G"], "fitness": -1.0},
    ])

    serine = query_amino_acid_properties(graph, "S")
    assert serine["properties"]["size"] == "small"
    context = query_mutation_context(graph, "A0S")
    assert context["n_measured"] == 2
    assert context["fitness_mean"] == 3.0
    assert context["fitness_max"] == 4.0
    assert "not a causal" in context["interpretation"]
    leaders = query_position_mutations(graph, 0)
    assert [row["mutation"] for row in leaders] == ["A0S", "A0G"]
