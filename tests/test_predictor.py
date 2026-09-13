from __future__ import annotations

import numpy as np
import pytest

from models.train_ladder import (
    RidgePredictor,
    XGBoostPredictor,
    load_predictor,
    metrics,
    save_predictor,
    select_ridge_alpha,
)


def synthetic(seed: int = 7):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(240, 12))
    y = X[:, 0] - .7 * X[:, 1] + .4 * X[:, 2] * X[:, 3] + rng.normal(0, .15, 240)
    return X[:180], y[:180], X[180:], y[180:]


@pytest.mark.parametrize("predictor", [RidgePredictor(alpha="auto", seeds=5), XGBoostPredictor(seeds=5)])
def test_predict_contract_is_reproducible_and_variance_is_non_degenerate(predictor):
    X_train, y_train, X_test, _ = synthetic()
    mean, variance = predictor.fit(X_train, y_train).predict(X_test)
    mean_again, variance_again = predictor.fit(X_train, y_train).predict(X_test)

    assert mean.shape == variance.shape == (len(X_test),)
    np.testing.assert_allclose(mean, mean_again)
    np.testing.assert_allclose(variance, variance_again)
    # Positive control for UCB: replacing bootstrap members with identical full-data
    # fits makes this fail because variance_max becomes approximately zero.
    assert float(variance.max()) > 1e-8


def test_metrics_and_shuffle_negative_control():
    rng = np.random.default_rng(19)
    truth = np.linspace(-2, 2, 1000)
    perfect = metrics(truth, truth)
    shuffled = metrics(truth, rng.permutation(truth))

    assert perfect["spearman"] == pytest.approx(1.0)
    assert perfect["pearson"] == pytest.approx(1.0)
    assert perfect["mse"] == pytest.approx(0.0)
    assert perfect["top_k"] == pytest.approx(1.0)
    assert abs(shuffled["spearman"]) < .1


def test_alpha_selection_uses_training_data_and_persistence_roundtrip(tmp_path):
    X_train, y_train, X_test, _ = synthetic()
    alpha = select_ridge_alpha(X_train, y_train, alphas=(.01, 1.0, 100.0))
    assert alpha in (.01, 1.0, 100.0)

    model = RidgePredictor(alpha="auto", seeds=3, standardize=True).fit(X_train, y_train)
    before = model.predict(X_test)
    path = save_predictor(model, tmp_path / "ridge.joblib")
    after = load_predictor(path).predict(X_test)
    np.testing.assert_allclose(before[0], after[0])
    np.testing.assert_allclose(before[1], after[1])


def test_save_rejects_unfitted_predictor(tmp_path):
    with pytest.raises(RuntimeError, match="fitted"):
        save_predictor(RidgePredictor(), tmp_path / "bad.joblib")


def test_xgboost_predictor_names_its_backend_and_refuses_a_silent_substitute(monkeypatch):
    """A row labelled "XGBoost" must not be producible by a different library.

    The old ``_make`` caught ImportError and returned a sklearn GradientBoostingRegressor
    with different hyper-parameters, recording nothing; the published v0.7 ladder was in
    fact produced that way on a machine without xgboost. Two guarantees are asserted here:
    the fitted model names the implementation that ran, and a missing xgboost raises
    instead of quietly substituting one.
    """
    X_train, y_train, _, _ = synthetic()

    fitted = XGBoostPredictor(seeds=2).fit(X_train, y_train)
    assert fitted.backend is not None and fitted.backend.startswith("xgboost-")

    import builtins

    real_import = builtins.__import__

    def without_xgboost(name, *args, **kwargs):
        if name == "xgboost":
            raise ImportError("No module named 'xgboost'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_xgboost)
    with pytest.raises(ImportError, match="xgboost"):
        XGBoostPredictor(seeds=2).fit(X_train, y_train)

    # The stand-in stays available, but only on request and only while saying so.
    fallback = XGBoostPredictor(seeds=2, allow_sklearn_fallback=True).fit(X_train, y_train)
    assert fallback.backend.startswith("sklearn-gradient-boosting-")
