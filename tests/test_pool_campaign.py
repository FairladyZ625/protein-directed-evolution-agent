from __future__ import annotations

import numpy as np
import pandas as pd

from evolution import datasets
from features.esm2 import ESM2Embedder, FEATURE_DIM
from models.train_ladder import RidgePredictor


def test_ridge_bootstrap_variance_is_nontrivial_and_reproducible():
    rng = np.random.default_rng(7)
    x = rng.normal(size=(80, 6))
    y = x[:, 0] - 0.4 * x[:, 1] + rng.normal(scale=0.3, size=80)
    pool = rng.normal(size=(30, 6))

    first = RidgePredictor(seeds=5).fit(x, y).predict(pool)
    second = RidgePredictor(seeds=5).fit(x, y).predict(pool)

    np.testing.assert_allclose(first[0], second[0])
    np.testing.assert_allclose(first[1], second[1])
    assert first[1].mean() > 0
    assert first[1].max() > first[1].min()


def test_avgfp_loader_uses_explicit_wild_type_row(tmp_path, monkeypatch):
    wt = "ACDE"
    frame = pd.DataFrame({
        "mutated_sequence": ["ACDF", wt, "ACEE"],
        "DMS_score": [0.1, 1.0, 0.4],
        "mutant": ["E4F", "WT", "D3E"],
    })
    path = tmp_path / "avgfp.csv"
    frame.to_csv(path, index=False)
    monkeypatch.setattr(datasets, "AVGFP_CSV", path)

    spec = datasets.load_avgfp(feature="one_hot")

    assert spec.wt == wt
    assert spec.df.loc[spec.df.seq.eq(wt), "hd"].item() == 0
    assert spec.feature_fn([wt]).shape == (1, 80)


def test_esm_embedder_accepts_full_sequences(tmp_path):
    seen = []

    def backend(sequences):
        seen.extend(sequences)
        return np.zeros((len(sequences), FEATURE_DIM), dtype=np.float32)

    ESM2Embedder(cache_dir=tmp_path, backend=backend).transform(["ACDEFG"])
    assert seen == ["ACDEFG"]
