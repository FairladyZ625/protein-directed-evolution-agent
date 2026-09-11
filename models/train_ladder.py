from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from scipy.stats import spearmanr, pearsonr


class _Base:
    def __init__(self, **kwargs: Any):
        self.kwargs = kwargs
        self.models: list[Any] = []
        # Continuous, non-unit-scale features (ESM-2 embeddings) leave Ridge(alpha=1) badly
        # mis-regularised: on AAV, raw ESM scores Spearman 0.47 but standardised 0.60. one-hot
        # (0/1) is already scaled so this is a no-op there. Opt-in to keep existing one-hot
        # baselines byte-identical; ESM callers pass standardize=True.
        self._scaler: StandardScaler | None = None

    def fit(self, X, y):
        X, y = np.asarray(X, dtype=float), np.asarray(y)
        if self.kwargs.get("standardize", False):
            self._scaler = StandardScaler().fit(X)
            X = self._scaler.transform(X)
        self.models = [self._make(i) for i in range(self.kwargs.get("seeds", 5))]
        for i, model in enumerate(self.models):
            if hasattr(model, "random_state") and model.random_state is None:
                model.random_state = i
            rng = np.random.default_rng(i)
            sample = rng.integers(0, len(y), size=len(y))
            model.fit(X[sample], y[sample])
        return self

    def predict(self, X):
        if not self.models:
            raise RuntimeError("fit must be called before predict")
        X = np.asarray(X, dtype=float)
        if self._scaler is not None:
            X = self._scaler.transform(X)
        values = np.asarray([m.predict(X) for m in self.models], dtype=float)
        return values.mean(axis=0), values.var(axis=0)

    def _make(self, seed):
        raise NotImplementedError


class RidgePredictor(_Base):
    def __init__(self, alpha: float = 1.0, **kwargs):
        super().__init__(alpha=alpha, **kwargs)

    def _make(self, seed):
        return Ridge(alpha=self.kwargs["alpha"])


class XGBoostPredictor(_Base):
    """Gradient boosting implementation; uses XGBoost when available."""
    def _make(self, seed):
        try:
            from xgboost import XGBRegressor
            return XGBRegressor(n_estimators=200, max_depth=6, learning_rate=.05,
                                subsample=.8, colsample_bytree=.8, objective="reg:squarederror",
                                random_state=seed, n_jobs=1)
        except ImportError:
            return GradientBoostingRegressor(n_estimators=150, max_depth=3, random_state=seed)


class MLPPredictor(_Base):
    def _make(self, seed):
        return MLPRegressor(hidden_layer_sizes=(128, 64), max_iter=300,
                            early_stopping=True, random_state=seed)


def metrics(y_true, y_pred, *, top_k: float = .01) -> dict[str, float]:
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    n = max(1, int(np.ceil(len(y_true) * top_k)))
    pred_idx = np.argsort(y_pred)[-n:]
    true_idx = set(np.argsort(y_true)[-n:])
    return {"spearman": float(spearmanr(y_true, y_pred).statistic),
            "pearson": float(pearsonr(y_true, y_pred).statistic),
            "mse": float(np.mean((y_true-y_pred)**2)),
            "top_k": float(len(set(pred_idx) & true_idx) / n)}


def evaluate_ladder(X_train, y_train, X_test, y_test) -> dict[str, dict[str, float]]:
    """Fit the three standard predictors and score an explicit split."""
    result = {}
    for name, cls in (("ridge", RidgePredictor), ("xgboost", XGBoostPredictor), ("mlp", MLPPredictor)):
        model = cls().fit(X_train, y_train)
        pred, var = model.predict(X_test)
        result[name] = {**metrics(y_test, pred), "variance_min": float(var.min()), "variance_max": float(var.max())}
    return result


def train_ladder(X, y, *, out: str | Path | None = None):
    if out is None:
        from evolution.results_layout import run_dir
        out = run_dir("workflow", "gb1") / "predictor_ladder.json"
    n = len(y); cut1 = int(n * .6)
    result = evaluate_ladder(X[:cut1], y[:cut1], X[cut1:], y[cut1:])
    path = Path(out); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(result, indent=2))
    return result
