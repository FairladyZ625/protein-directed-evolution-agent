import json

import numpy as np
import pytest

from evolution import random_baseline as rb


@pytest.fixture(scope="module")
def df():
    return rb.load_landscape()


@pytest.fixture(scope="module")
def simulated(df):
    return rb.simulate(df, seed=rb.SEED)


def test_landscape_contract(df):
    assert len(df) == rb.EXPECTED_ROWS == 149_361
    assert df["Fitness"].notna().all()
    assert df.loc[df["Variants"] == rb.WT, "Fitness"].tolist() == [1.0]


def test_cold_start_pool_is_5000_hd_stratified(df):
    pool = rb.build_cold_start_pool(df, np.random.default_rng(rb.SEED))
    assert len(pool) == rb.POOL_SIZE == 5_000
    assert pool["Variants"].is_unique
    assert set(pool["HD"]) == {0, 1, 2, 3, 4}
    assert rb.WT in set(pool["Variants"])
    # 比例分层：各 HD 层占比与全表一致（每层保底 1 条只带来 < 0.1 个百分点偏差）
    share_gap = pool["HD"].value_counts(normalize=True) - df["HD"].value_counts(normalize=True)
    assert share_gap.abs().max() < 1e-3


def test_each_round_nominates_96_new_unique_variants(df, simulated):
    pool, batches = simulated
    assert len(batches) == rb.N_ROUNDS == 3
    seen = set(pool["Variants"])
    oracle = df.set_index("Variants")["Fitness"]
    for batch in batches:
        assert len(batch) == rb.BUDGET == 96
        assert batch["Variants"].is_unique
        assert seen.isdisjoint(batch["Variants"])  # 去重：不重测池内或前几轮已测变体
        seen |= set(batch["Variants"])
        assert batch["Fitness"].tolist() == oracle.loc[batch["Variants"]].tolist()  # 真值来自全表查表


def test_same_seed_reproduces_identical_metrics(tmp_path):
    runs = []
    for name in ("a", "b"):
        rb.main(["--out-json", str(tmp_path / f"{name}.json"), "--out-fig", str(tmp_path / f"{name}.png")])
        runs.append((tmp_path / f"{name}.json").read_text(encoding="utf-8"))
    assert runs[0] == runs[1]
    other = rb.main(["--seed", "7", "--out-json", str(tmp_path / "c.json"), "--out-fig", str(tmp_path / "c.png")])
    assert other["rounds"] != json.loads(runs[0])["rounds"]  # 种子确实生效


def test_metrics_schema_and_negative_control(tmp_path):
    out_json, out_fig = tmp_path / "m.json", tmp_path / "m.png"
    rb.main(["--out-json", str(out_json), "--out-fig", str(out_fig)])
    report = json.loads(out_json.read_text(encoding="utf-8"))
    assert report["seed"] == 42
    assert report["n_rounds"] == len(report["rounds"]) == 3
    assert report["budget_per_round"] == 96 and report["cold_start_pool_size"] == 5_000
    for i, r in enumerate(report["rounds"], start=1):
        assert {"round", "top10_max", "top10_mean", "n_hit_nonzero"} <= r.keys()
        assert r["round"] == i
        assert r["top10_max"] >= r["top10_mean"] >= 0
        assert 0 <= r["n_hit_nonzero"] <= 96
        assert r["top10_mean"] < report["landscape"]["top1pct_mean"]  # 阴性对照
    assert report["negative_control"]["passed"] is True
    assert out_fig.stat().st_size > 10_000
