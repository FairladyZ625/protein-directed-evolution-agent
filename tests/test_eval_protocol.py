from __future__ import annotations

import numpy as np
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge

from features.one_hot import encode_one_hot
from features.pools import build_evaluation_protocol, load_three_pools
from models.train_ladder import select_ridge_alpha


def _selection(seed: int):
    protocol = build_evaluation_protocol(load_three_pools(), seed=seed)
    return protocol, select_ridge_alpha(
        encode_one_hot(protocol.train.Variants.tolist()),
        protocol.train.Fitness.to_numpy(),
        encode_one_hot(protocol.validation.Variants.tolist()),
        protocol.validation.Fitness.to_numpy(),
    )


def test_four_roles_preserve_outer_pool_contract():
    pools = load_three_pools()
    protocol = build_evaluation_protocol(pools)
    assert protocol.sizes() == {
        "train": 4_000,
        "validation": 1_000,
        "query_test": 50_000,
        "holdout": 94_361,
    }
    assert len(protocol.train) + len(protocol.validation) == 5_000
    assert "VDGV" in set(protocol.train.Variants)
    role_sets = [
        set(protocol.train.Variants),
        set(protocol.validation.Variants),
        set(protocol.query_test.Variants),
        set(protocol.holdout.Variants),
    ]
    assert all(not role_sets[i] & role_sets[j] for i in range(4) for j in range(i + 1, 4))
    assert len(set.union(*role_sets)) == 149_361


def test_changing_validation_changes_selected_alpha():
    first, first_selection = _selection(seed=42)
    changed, changed_selection = _selection(seed=44)
    assert set(first.validation.Variants) != set(changed.validation.Variants)
    assert first_selection["selected_alpha"] == 0.01
    assert changed_selection["selected_alpha"] == 10.0
    print(
        "validation sensitivity:",
        f"seed=42 alpha={first_selection['selected_alpha']} score={first_selection['selected_score']:.6f};",
        f"seed=44 alpha={changed_selection['selected_alpha']} score={changed_selection['selected_score']:.6f}",
    )


def test_shuffled_training_labels_destroy_validation_rank_signal():
    protocol, selection = _selection(seed=42)
    X_train = encode_one_hot(protocol.train.Variants.tolist())
    X_validation = encode_one_hot(protocol.validation.Variants.tolist())
    y_train = protocol.train.Fitness.to_numpy()
    y_validation = protocol.validation.Fitness.to_numpy()
    alpha = selection["selected_alpha"]
    signal = spearmanr(
        y_validation, Ridge(alpha=alpha).fit(X_train, y_train).predict(X_validation)
    ).statistic
    shuffled = np.random.default_rng(123).permutation(y_train)
    negative = spearmanr(
        y_validation, Ridge(alpha=alpha).fit(X_train, shuffled).predict(X_validation)
    ).statistic
    assert signal > 0.45
    assert abs(negative) < 0.1
    print(f"label control: signal_spearman={signal:.6f}; shuffled_spearman={negative:.6f}")
