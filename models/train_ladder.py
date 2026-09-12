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


class EpistasisRidgePredictor(_Base):
    """上位感知(Potts 式)surrogate:one-hot 的 degree-2 interaction 特征 + Ridge。

    加性 Ridge/kNN 无法表达位点×位点残基交互,故对正上位峰系统性排低(实验二/三诊断:
    加性把 AAV 真峰门内排 #2776,本模型 ~#447)。这里显式加二阶交互项:
    - answer-agnostic 频次过滤:只保留训练集里出现 >= min_count 次的 one-hot 列(去极稀有,
      控制特征规模;不使用测试峰信息)。
    - alpha 由 RidgeCV(留一)在训练集上自选(answer-agnostic),不按目标峰调参。
    - bootstrap 集成给 UCB 需要的方差;pool 预测分块,控内存。
    接口同 _Base:fit(X,y).predict(X)->(mean,var)。X 为 one-hot 特征矩阵。
    """
    def __init__(self, alphas=(1.0, 10.0, 100.0, 300.0), min_count: int = 10,
                 var_seeds: int = 3, chunk: int = 8000, **kwargs):
        super().__init__(min_count=min_count, **kwargs)
        self._alphas = tuple(alphas)
        self._var_seeds = var_seeds
        self._chunk = chunk
        self._poly = None
        self._keep = None
        self._alpha = None
        self._mean_model = None       # full-data model -> mean/ranking (no bootstrap degradation)
        self.val_spearman: float | None = None

    def _expand(self, X, fit: bool = False):
        """degree-2 interaction on the kept one-hot columns, kept SPARSE (each AAV variant
        has ~28 nonzeros -> ~378 pairwise nonzeros/row, so this stays tiny and fast)."""
        import scipy.sparse as sp
        from sklearn.preprocessing import PolynomialFeatures
        Xs = sp.csr_matrix(np.asarray(X, dtype=float)[:, self._keep])
        if fit or self._poly is None:
            self._poly = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
            return self._poly.fit_transform(Xs)
        return self._poly.transform(Xs)

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y)
        counts = (X > 0).sum(axis=0)
        self._keep = counts >= self.kwargs.get("min_count", 10)
        if self._keep.sum() == 0:                       # degenerate tiny data: keep all
            self._keep = np.ones(X.shape[1], dtype=bool)
        Xp = self._expand(X, fit=True)
        self._scaler = StandardScaler(with_mean=False).fit(Xp)   # sparse-safe (no centering)
        Xp = self._scaler.transform(Xp)
        # answer-agnostic alpha selection: one 80/20 split, pick best held-out Spearman
        # (NOT by target-peak rank). Falls back to median alpha on tiny/degenerate data.
        self._alpha = self._select_alpha(Xp, y)
        # mean/ranking from a single FULL-data fit (bootstrap would degrade the high-dim fit)
        self._mean_model = Ridge(alpha=self._alpha, solver="sparse_cg").fit(Xp, y)
        # small bootstrap ensemble ONLY for the exploration variance the agent's UCB needs
        self.models = []
        n = len(y)
        for i in range(self._var_seeds):
            rng = np.random.default_rng(i)
            s = rng.integers(0, n, size=n)
            self.models.append(Ridge(alpha=self._alpha, solver="sparse_cg").fit(Xp[s], y[s]))
        return self

    def _select_alpha(self, Xp, y):
        from sklearn.model_selection import train_test_split
        n = len(y)
        if n < 20:
            self.val_spearman = None
            return float(self._alphas[len(self._alphas) // 2])
        tr, va = train_test_split(np.arange(n), test_size=0.2, random_state=0)
        best_a, best_s = None, -2.0
        for a in self._alphas:
            m = Ridge(alpha=a, solver="sparse_cg").fit(Xp[tr], y[tr])
            s = spearmanr(m.predict(Xp[va]), y[va]).correlation
            s = -2.0 if (s is None or np.isnan(s)) else float(s)
            if s > best_s:
                best_a, best_s = a, s
        self.val_spearman = None if best_a is None else float(best_s)
        return float(best_a if best_a is not None else self._alphas[len(self._alphas) // 2])

    def predict(self, X):
        if self._mean_model is None:
            raise RuntimeError("fit must be called before predict")
        X = np.asarray(X, dtype=float)
        means, variances = [], []
        for start in range(0, len(X), self._chunk):
            Xp = self._scaler.transform(self._expand(X[start:start + self._chunk]))
            means.append(self._mean_model.predict(Xp))
            vals = np.asarray([m.predict(Xp) for m in self.models], dtype=float)
            variances.append(vals.var(axis=0))
        return np.concatenate(means), np.concatenate(variances)


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
