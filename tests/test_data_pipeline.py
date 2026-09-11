from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from data.download_gb1 import validate_local_gb1
from evolution.mutations import GB1_WT_SEQUENCE, apply_mutations, parse_mutation, sequence_to_variant, variant_to_sequence
from evolution.random_baseline import EXPECTED_ROWS, load_landscape
from features.esm2 import ESM2Embedder, FEATURE_DIM as ESM_DIM
from features.one_hot import encode_one_hot
from features.pools import build_three_pools, load_three_pools


def test_data_contract_and_provenance():
    manifest = validate_local_gb1()
    assert manifest["rows"] == manifest["unique_variants"] == EXPECTED_ROWS
    assert manifest["wt_fitness"] == 1.0
    assert len(manifest["sha256"]) == 64


def test_mutation_parsing_and_domain_reconstruction():
    assert str(parse_mutation("v39i")) == "V39I"
    sequence = variant_to_sequence("IDAV")
    assert len(sequence) == 56
    assert sequence_to_variant(sequence) == "IDAV"
    assert apply_mutations([]) == GB1_WT_SEQUENCE
    with pytest.raises(ValueError, match="wild-type residue mismatch"):
        parse_mutation("A39I")
    with pytest.raises(ValueError, match="invalid GB1 mutation"):
        parse_mutation("V39*")


def test_three_pools_are_disjoint_stratified_and_seeded():
    landscape = load_landscape()
    first = build_three_pools(landscape, seed=42)
    replay = build_three_pools(landscape, seed=42)
    changed = build_three_pools(landscape, seed=43)
    assert first.sizes() == changed.sizes() == {"train_pool": 5_000, "query_pool": 50_000, "holdout": 94_361}
    assert first.train_pool.Variants.tolist() == replay.train_pool.Variants.tolist()
    assert set(first.train_pool.Variants) != set(changed.train_pool.Variants)
    assert "VDGV" in set(first.train_pool.Variants)
    sets = [set(first.train_pool.Variants), set(first.query_pool.Variants), set(first.holdout.Variants)]
    assert not (sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2])
    assert len(set.union(*sets)) == EXPECTED_ROWS
    population_share = landscape.HD.value_counts(normalize=True).sort_index()
    train_share = first.train_pool.HD.value_counts(normalize=True).sort_index()
    assert np.max(np.abs(population_share - train_share)) < 0.001


def test_one_hot_is_80_dimensional():
    encoded = encode_one_hot(["VDGV", "FWAA"])
    assert encoded.shape == (2, 80)
    assert encoded.dtype == np.uint8
    assert np.all(encoded.sum(axis=1) == 4)
    assert not np.array_equal(encoded[0], encoded[1])


def test_committed_one_hot_cache_is_safe_and_complete():
    pools = load_three_pools()
    expected = sum(pools.sizes().values())
    with np.load("features/cache/gb1-all-one-hot.npz", allow_pickle=False) as cache:
        assert cache["variants"].dtype.kind == "U"
        assert cache["variants"].shape == (expected,)
        assert cache["embeddings"].shape == (expected, 80)


def test_esm_cache_matches_live_backend_elementwise(tmp_path):
    calls = 0

    def deterministic_backend(sequences):
        nonlocal calls
        calls += 1
        return np.stack([np.full(ESM_DIM, sum(map(ord, sequence)) / 10_000, dtype=np.float32)
                         for sequence in sequences])

    embedder = ESM2Embedder(cache_dir=tmp_path, backend=deterministic_backend)
    live = embedder.transform(["VDGV", "FWAA"])
    cached = embedder.transform(["VDGV", "FWAA"])
    assert calls == 1
    np.testing.assert_allclose(cached, live, rtol=0, atol=5e-4)
    assert cached.shape == (2, 1280)
