from knowledge.validators import (
    build_knowledge_graph,
    load_rules,
    query_amino_acid_properties,
    query_mutation_context,
    query_position_mutations,
    validate_candidate,
    validate_mutations,
)


def test_conservative_and_aggressive_rules():
    conservative = validate_candidate("V39I")
    assert any(r["rule_id"] == "R-BLOSUM-CONSERVATIVE" and r["pass"] for r in conservative)
    aggressive = validate_candidate("V39W")
    assert any(r["rule_id"] == "R-BLOSUM-AGGRESSIVE" and not r["pass"] for r in aggressive)


def test_blosum62_is_complete_and_classifies_zero_score_as_neutral():
    matrix = load_rules()["blosum62"]
    amino_acids = set("ACDEFGHIKLMNPQRSTVWY")
    assert set(matrix) == amino_acids
    assert all(set(row) == amino_acids for row in matrix.values())
    assert sum(len(row) for row in matrix.values()) == 400
    assert all(matrix[a][b] == matrix[b][a] for a in amino_acids for b in amino_acids)

    assert matrix["C"]["W"] == -2
    c39w = validate_candidate("C39W")
    assert any(r["rule_id"] == "R-BLOSUM-AGGRESSIVE" for r in c39w)

    # This asymmetric fixture exercises the reverse-only zero-score lookup.
    neutral_rules = load_rules()
    neutral_rules["blosum62"] = {"A": {}, "G": {"A": 0}}
    neutral = validate_mutations(["A39G"], rules=neutral_rules)
    assert any(r["rule_id"] == "R-BLOSUM-CONSERVATIVE" and not r["pass"] for r in neutral)
    assert any(r["rule_id"] == "R-BLOSUM-AGGRESSIVE" and r["pass"] for r in neutral)


def test_historical_single_mutant_priority_hit_and_miss():
    hit = validate_candidate(["V39I", "D40E"], historical_good=["V39I", "G41A"])
    hit_result = next(r for r in hit if r["rule_id"] == "R-PRIORITIZE-HISTORICAL")
    assert hit_result["pass"] is True
    assert "V39I" in hit_result["note"]

    miss = validate_candidate("V39W", historical_good=["V39I", "G41A"])
    miss_result = next(r for r in miss if r["rule_id"] == "R-PRIORITIZE-HISTORICAL")
    assert miss_result["pass"] is False


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
