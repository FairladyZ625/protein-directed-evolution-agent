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


def test_load_rules_parses_yaml_once_but_still_notices_a_changed_file(monkeypatch, tmp_path):
    """门禁一轮要过 6,539 个候选，规则文件只能解析一次。

    改前 validate_candidate 每次调用都重新打开并 yaml.safe_load 一遍 rules.yaml：
    14.32 ms/次 × 6,539 ≈ 94 s，这就是看板「自动推荐」看起来卡死、以及每次
    knowledge_agent 跑批都慢的原因。缓存按 (路径, mtime, size) 记，所以
    测试改写规则文件后仍能读到新内容——缓存不能变成「改了规则也不生效」。
    """
    import knowledge.validators as V

    real_safe_load = V.yaml.safe_load
    calls = {"n": 0}

    def counting(stream):
        calls["n"] += 1
        return real_safe_load(stream)

    monkeypatch.setattr(V.yaml, "safe_load", counting)
    V._parse_rules.cache_clear()

    for _ in range(50):
        validate_candidate(["V39I", "D40E"], no_knowledge=False)
    assert calls["n"] == 1, f"rules.yaml 被解析了 {calls['n']} 次，缓存没生效"

    # 阴性对照：换一个文件、再改写它，必须重新解析并读到新内容
    copy = tmp_path / "rules.yaml"
    copy.write_text(V.ROOT.read_text(encoding="utf-8"), encoding="utf-8")
    assert V.load_rules(copy)["rules"], "副本应能正常解析"
    after_first_copy = calls["n"]
    assert after_first_copy == 2

    copy.write_text(copy.read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8")
    V.load_rules(copy)
    assert calls["n"] == after_first_copy + 1, "文件改了却没重新解析，缓存把更新吃掉了"


# ---- R-PHYSICOCHEMICAL:理化性质从「只喂知识图谱」升为具名规则 -----------------------
# rules.yaml 的 amino_acids 表此前只被知识图谱的 has_property 边读取,而试题把理化性质
# 列为帮助 agent 决策的知识。做成 advisory 而非 gate 是刻意的:所有消费者都按
# enforcement == "gate" 过滤,因此这一行不可能改变任何已提名的候选,历史实验无需重跑。

def test_physicochemical_rule_names_the_class_crossings():
    from knowledge.validators import validate_candidate
    rows = {r["rule_id"]: r for r in validate_candidate(["D40W"])}
    row = rows["R-PHYSICOCHEMICAL"]
    assert row["enforcement"] == "advisory"
    assert row["pass"] is False          # 跨了类 -> advisory 报 False
    for axis in ("charge -1→0", "polarity polar→nonpolar", "size medium→large"):
        assert axis in row["note"], axis


def test_physicochemical_rule_stays_quiet_within_class():
    """阴性对照:V→F 同为 large / nonpolar / charge 0,疏水差 1.4,不该报跨类。"""
    from knowledge.validators import validate_candidate
    row = {r["rule_id"]: r for r in validate_candidate(["V39F"])}["R-PHYSICOCHEMICAL"]
    assert row["pass"] is True
    assert "none" in row["note"]


def test_physicochemical_rule_cannot_gate_anything():
    """它必须对门禁完全惰性——否则所有历史实验数据都要作废重跑。"""
    from knowledge.validators import validate_candidate
    for muts in (["D40W"], ["V39F"], ["V39A", "D40E", "G41S"]):
        rows = validate_candidate(muts)
        gating = [r for r in rows if r["enforcement"] == "gate"]
        assert all(r["rule_id"] != "R-PHYSICOCHEMICAL" for r in gating)
