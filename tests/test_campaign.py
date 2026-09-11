import pandas as pd

from evolution.campaign import run_campaign


def landscape():
    rows = []
    for i, seq in enumerate(("VDGV", "FWAA", "AAAA", "VVVV", "FDGV", "VDAV", "VAGV", "VDGW", "FWWW", "WWWW")):
        rows.append({"Variants": seq, "HD": sum(a != b for a, b in zip(seq, "VDGV")), "Fitness": float(i) / 2 + 0.1})
    return pd.DataFrame(rows)


def test_four_strategies_share_oracle_and_budget():
    report = run_campaign(landscape(), seed=3, n_rounds=2, budget=2, pool_size=2)
    assert set(report["strategies"]) == {"random", "greedy", "agent_no_knowledge", "knowledge_agent"}
    assert report["oracle"] == "measured table lookup"
    for result in report["strategies"].values():
        assert [r["n_nominated"] for r in result["rounds"]] == [2, 2]
        assert all("cum_top10_max" in r for r in result["rounds"])


def test_campaign_is_reproducible():
    a = run_campaign(landscape(), seed=9, n_rounds=2, budget=2, pool_size=2)
    b = run_campaign(landscape(), seed=9, n_rounds=2, budget=2, pool_size=2)
    assert a == b
