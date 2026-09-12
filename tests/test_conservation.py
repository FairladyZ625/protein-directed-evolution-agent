import builtins

import numpy as np
import pandas as pd
import pytest

from features.conservation import (
    ESM2ConservationAnalyzer,
    _experimental_effects,
    conservation_ranks,
    shannon_entropy,
)


def test_entropy_positive_controls() -> None:
    uniform = np.full((2, 20), 1 / 20)
    one_hot = np.eye(20)[[0, 7]]
    np.testing.assert_allclose(shannon_entropy(uniform), np.log(20))
    np.testing.assert_allclose(shannon_entropy(one_hot), 0.0)


def test_conservation_rank_low_entropy_first() -> None:
    np.testing.assert_array_equal(conservation_ranks(np.array([2.0, 0.1, 1.0])), [3, 1, 2])


def test_backend_result_is_cached(tmp_path) -> None:
    calls = 0

    def backend(sequence: str) -> np.ndarray:
        nonlocal calls
        calls += 1
        return np.full((len(sequence), 20), 1 / 20)

    analyzer = ESM2ConservationAnalyzer(cache_dir=tmp_path, backend=backend)
    first = analyzer.probabilities("ACD")
    second = analyzer.probabilities("ACD")
    np.testing.assert_allclose(first, second)
    assert calls == 1


def test_missing_esm_backend_fails_explicitly(tmp_path, monkeypatch) -> None:
    real_import = builtins.__import__

    def missing_esm(name, *args, **kwargs):
        if name in {"esm", "torch"}:
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing_esm)
    analyzer = ESM2ConservationAnalyzer(cache_dir=tmp_path)
    with pytest.raises(RuntimeError, match="no conservation fallback is allowed"):
        analyzer.probabilities("ACD", use_cache=False)


def test_rejects_invalid_probability_distribution(tmp_path) -> None:
    analyzer = ESM2ConservationAnalyzer(
        cache_dir=tmp_path, backend=lambda sequence: np.zeros((len(sequence), 20))
    )
    with pytest.raises(ValueError, match="sum to one"):
        analyzer.probabilities("ACD")


def test_experimental_effects_use_only_single_mutants() -> None:
    effects = _experimental_effects(
        pd.Series(["AAA", "CAA", "ACA", "CCA"]),
        pd.Series([1.0, 2.0, 3.0, 99.0]),
        "AAA",
    )
    assert effects[0]["n_mutated_observations"] == 1
    assert effects[0]["max_fitness_gain"] == 1.0
    assert effects[1]["n_mutated_observations"] == 1
    assert effects[1]["max_fitness_gain"] == 2.0
