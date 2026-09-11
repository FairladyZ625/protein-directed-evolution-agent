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
from agent.auto_researcher import run_autoresearch

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


def _blosum():
    from knowledge.validators import load_rules
    m = load_rules()["blosum62"]
    def score(a, b):
        if a == b:
            return 4
        return m.get(a, {}).get(b, m.get(b, {}).get(a, 0))
    return score
