"""v0.2 Knowledge Gate behavior: HD + BLOSUM62 filter before budget is spent.

Uses a tiny synthetic pool so the tests are fast and deterministic (no LLM). The gate
must (1) do nothing when off, (2) reject high-order / non-conservative candidates when
on, without spending budget on the rejected ones, and (3) only ever measure gate-passing
variants when on.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from evolution.pool_campaign import DatasetSpec
from agent.auto_researcher import _gate_variants, run_autoresearch

WT = "AAAAAAAA"  # 8-residue toy wild type


def _spec():
    # measured cold start (HD<=2) + a pool (HD>2) mixing low-order conservative and
    # high-order / non-conservative variants.
    rows = []
    # cold start: WT and single/double conservative mutants (A->S/G are mild)
    for s, f in [("AAAAAAAA", 1.0), ("SAAAAAAA", 1.1), ("ASAAAAAA", 1.2),
                 ("SSAAAAAA", 1.3), ("GAAAAAAA", 0.9), ("AGAAAAAA", 1.0)]:
        rows.append((s, f, sum(a != b for a, b in zip(s, WT))))
    # pool HD>2: some low-order conservative (should pass), some high-order (fail HD),
    # some non-conservative (fail BLOSUM: A->P/W are disruptive)
    pool = [
        ("SSSAAAAA", 2.0),   # HD3 conservative -> pass
        ("SGSAAAAA", 2.2),   # HD3 conservative -> pass
        ("SSSSAAAA", 2.5),   # HD4 conservative -> pass
        ("SSSSSAAA", 2.7),   # HD5 -> fail HD
        ("SSSSSSAA", 3.0),   # HD6 -> fail HD
        ("PPPAAAAA", 3.5),   # HD3 but A->P non-conservative -> fail BLOSUM
        ("WWWAAAAA", 4.0),   # HD3 but A->W non-conservative -> fail BLOSUM
    ]
    for s, f in pool:
        rows.append((s, f, sum(a != b for a, b in zip(s, WT))))
    df = pd.DataFrame(rows, columns=["seq", "fitness", "hd"])

    def feat(seqs):
        aa = "ACDEFGHIKLMNPQRSTVWY"
        lut = {c: i for i, c in enumerate(aa)}
        x = np.zeros((len(seqs), len(WT) * 20))
        for r, s in enumerate(seqs):
            for p, c in enumerate(s):
                x[r, p * 20 + lut[c]] = 1.0
        return x

    return DatasetSpec(name="toy", df=df, wt=WT, feature_fn=feat)


def test_gate_off_spends_budget_and_rejects_nothing():
    rep = run_autoresearch(_spec(), budget=4, n_rounds=1, seed=0, llm=False, guardrail=False)
    assert rep["guardrail"] is False
    assert rep["n_gate_rejected"] == 0
    assert rep["budget_spent"] > 0  # deterministic driver measured something


def test_gate_on_rejects_and_never_measures_disallowed():
    spec = _spec()
    rep = run_autoresearch(spec, budget=7, n_rounds=2, seed=0, llm=False,
                           guardrail=True, max_hd=4, blosum_min=0.0)
    assert rep["guardrail"] is True
    assert rep["max_hd"] == 4
    # every variant actually measured must satisfy the gate
    wt = spec.wt
    bl = _blosum()
    for rnd in rep["rounds"]:
        for seq, _f in rnd["top10"]:
            subs = [(wt[i], c) for i, c in enumerate(seq) if c != wt[i]]
            assert len(subs) <= 4, f"measured {seq} has HD {len(subs)} > 4"
            if subs:
                assert np.mean([bl(w, c) for w, c in subs]) >= 0.0, f"measured {seq} non-conservative"


def test_relaxed_gate_lets_everything_through():
    # max_hd huge + very low blosum floor -> gate rejects nothing, behaves like off
    rep = run_autoresearch(_spec(), budget=7, n_rounds=1, seed=0, llm=False,
                           guardrail=True, max_hd=99, blosum_min=-99.0)
    assert rep["n_gate_rejected"] == 0
    assert rep["budget_spent"] > 0


def _big_gated_spec():
    """A pool with MANY gate-passing variants (HD<=4 conservative A->S/G) plus some
    gate-failing ones, so we can prove the gate does not starve the budget: candidate
    generation must surface the valid region and spend the full budget inside it."""
    import itertools
    rows = [("AAAAAAAA", 1.0, 0)]
    for i in range(8):  # cold-start singles
        s = "A" * i + "S" + "A" * (7 - i)
        rows.append((s, 1.0 + 0.01 * i, 1))
    # pool: 20 gate-passing (HD3-4, A->S/G conservative) at varied positions
    gated = []
    combos = list(itertools.combinations(range(8), 3))
    for k, pos in enumerate(combos[:20]):
        s = list("AAAAAAAA")
        for j, p in enumerate(pos):
            s[p] = "S" if (j + k) % 2 == 0 else "G"
        gated.append(("".join(s), 2.0 + 0.05 * k))
    for s, f in gated:
        rows.append((s, f, sum(a != b for a, b in zip(s, "AAAAAAAA"))))
    # pool: gate-failing (high HD or non-conservative A->P/W)
    for s, f in [("SSSSSSAA", 3.0), ("SSSSSSSA", 3.1), ("PPPAAAAA", 3.5), ("WWWWAAAA", 4.0)]:
        rows.append((s, f, sum(a != b for a, b in zip(s, "AAAAAAAA"))))
    df = pd.DataFrame(rows, columns=["seq", "fitness", "hd"]).drop_duplicates("seq")

    def feat(seqs):
        aa = "ACDEFGHIKLMNPQRSTVWY"
        lut = {c: i for i, c in enumerate(aa)}
        x = np.zeros((len(seqs), 8 * 20))
        for r, s in enumerate(seqs):
            for p, c in enumerate(s):
                x[r, p * 20 + lut[c]] = 1.0
        return x

    return DatasetSpec(name="toybig", df=df, wt="AAAAAAAA", feature_fn=feat)


def test_gate_on_does_not_starve_budget():
    # Regression for the v0.2 budget-starvation bug: a reject-only gate let candidate
    # generation keep surfacing gate-failing variants, so budget went unspent. The fix
    # makes list_pool (and the exploit-fill that calls it) draw from the gate-passing
    # region, so the full budget is spent inside the valid region.
    spec = _big_gated_spec()
    rep = run_autoresearch(spec, budget=5, n_rounds=2, seed=0, llm=False,
                           guardrail=True, max_hd=4, blosum_min=0.0)
    assert rep["budget_spent"] == 10, f"gate starved the budget: only {rep['budget_spent']} spent"
    assert rep["gate_pass_pool_size"] >= 10
    wt = spec.wt
    bl = _blosum()
    for rnd in rep["rounds"]:
        for seq, _f in rnd["top10"]:
            subs = [(wt[i], c) for i, c in enumerate(seq) if c != wt[i]]
            assert len(subs) <= 4
            if subs:
                assert np.mean([bl(w, c) for w, c in subs]) >= 0.0


def _blosum():
    from knowledge.validators import load_rules
    m = load_rules()["blosum62"]
    def score(a, b):
        if a == b:
            return 4
        return m.get(a, {}).get(b, m.get(b, {}).get(a, 0))
    return score


def test_gate_cleans_whitespace_and_case_without_rejecting_valid_sequence():
    allowed, rejected = _gate_variants(
        [" sssa\n aaaa "], wt=WT, max_hd=4, blosum_min=0.0, blosum_fn=_blosum(),
    )
    assert allowed == ["SSSAAAAA"]
    assert rejected == {}


def test_gate_rejects_wrong_length_and_empty_as_structured_errors():
    wt_28 = "A" * 28
    too_long = wt_28 + "A"  # regression: the observed LLM failure supplied 29 aa for AAV's 28 aa
    allowed, rejected = _gate_variants(
        [too_long, "  \n"], wt=wt_28, max_hd=4, blosum_min=0.0, blosum_fn=_blosum(),
    )
    assert allowed == []
    assert "length_mismatch" in rejected[too_long][0]
    assert "length_mismatch" in rejected["  \n"][0]


def test_gate_rejects_mutation_notation_with_actionable_hint():
    allowed, rejected = _gate_variants(
        ["D0Q"], wt=WT, max_hd=4, blosum_min=0.0, blosum_fn=_blosum(),
    )
    assert allowed == []
    assert "mutation_notation" in rejected["D0Q"][0]
    assert "compose_batch" in rejected["D0Q"][0]
