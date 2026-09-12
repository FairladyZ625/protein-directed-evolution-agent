from __future__ import annotations

import json
import argparse
from pathlib import Path
from typing import Any

import joblib
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
    """Bootstrap Ridge ensemble with optional train-only alpha selection."""

    def __init__(self, alpha: float | str = 1.0, **kwargs):
        super().__init__(alpha=alpha, **kwargs)
        self.alpha_: float | None = None

    def fit(self, X, y):
        if self.kwargs["alpha"] == "auto":
            self.alpha_ = select_ridge_alpha(X, y, standardize=self.kwargs.get("standardize", False))
        else:
            self.alpha_ = float(self.kwargs["alpha"])
        return super().fit(X, y)

    def _make(self, seed):
        return Ridge(alpha=self.alpha_)


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


RIDGE_ALPHAS = (0.01, 0.1, 1.0, 10.0, 100.0, 1000.0)


def select_ridge_alpha(X, y, *, standardize: bool = False,
                       alphas=RIDGE_ALPHAS) -> float:
    """Select alpha on a deterministic split of the training data only."""
    from sklearn.model_selection import train_test_split

    X, y = np.asarray(X, dtype=float), np.asarray(y, dtype=float)
    train, validation = train_test_split(np.arange(len(y)), test_size=.2, random_state=0)
    if standardize:
        scaler = StandardScaler().fit(X[train])
        x_train, x_validation = scaler.transform(X[train]), scaler.transform(X[validation])
    else:
        x_train, x_validation = X[train], X[validation]
    scores = []
    for alpha in alphas:
        prediction = Ridge(alpha=alpha).fit(x_train, y[train]).predict(x_validation)
        score = spearmanr(y[validation], prediction).statistic
        scores.append(-np.inf if score is None or np.isnan(score) else float(score))
    return float(alphas[int(np.argmax(scores))])


def save_predictor(model: _Base, path: str | Path) -> Path:
    """Persist a fitted predictor, including its scaler and ensemble members."""
    if not model.models:
        raise RuntimeError("only a fitted predictor can be saved")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path


def load_predictor(path: str | Path) -> _Base:
    """Load a predictor persisted by :func:`save_predictor`."""
    model = joblib.load(Path(path))
    if not isinstance(model, _Base):
        raise TypeError("artifact is not a predictor")
    return model


def evaluate_ladder(X_train, y_train, X_test, y_test, *, standardize: bool = False) -> dict[str, dict[str, float]]:
    """Fit the three standard predictors and score an explicit split.

    ``standardize`` is forwarded to every rung. It defaults to False so existing one-hot
    numbers stay byte-identical, but a *comparison* between one-hot and ESM-2 must pass the
    same value on both sides: leaving it off silently compares a scaled feature (one-hot is
    already 0/1) against an unscaled one (ESM-2), which is a feature-quality claim resting on
    a preprocessing artefact. See the note on `_Base.__init__`.
    """
    result = {}
    for name, cls in (("ridge", RidgePredictor), ("xgboost", XGBoostPredictor), ("mlp", MLPPredictor)):
        model = cls(standardize=standardize).fit(X_train, y_train)
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


def _subsample(frame, n: int, seed: int):
    if len(frame) <= n:
        return frame.reset_index(drop=True)
    return frame.sample(n=n, random_state=seed).reset_index(drop=True)


def train_from_t2(*, feature: str = "one_hot", eval_n: int = 2000,
                  output: str | Path = "reports/predictor_metrics.json") -> dict[str, Any]:
    """Train from T2's three pools and emit reproducible val/test metrics and a figure.

    The query and holdout pools are disjoint validation and test sets.  Ridge alpha is
    selected inside the training pool; neither validation nor test labels tune it.
    """
    from features.esm2 import ESM2Embedder
    from features.one_hot import encode_one_hot
    from features.pools import load_three_pools
    from evolution.results_layout import run_dir

    pools = load_three_pools()
    frames = {
        "train": pools.train_pool.reset_index(drop=True),
        "validation": _subsample(pools.query_pool, eval_n, 43),
        "test": _subsample(pools.holdout, eval_n, 44),
    }
    if feature == "one_hot":
        transform = lambda frame: encode_one_hot(frame["Variants"].tolist())
    elif feature == "esm2":
        embedder = ESM2Embedder()
        transform = lambda frame: embedder.transform(frame["Variants"].tolist())
    else:
        raise ValueError("feature must be 'one_hot' or 'esm2'")
    X = {name: transform(frame) for name, frame in frames.items()}
    y = {name: frame["Fitness"].to_numpy() for name, frame in frames.items()}

    version_dir = run_dir("workflow", "gb1")
    model_dir = version_dir / "models"
    result: dict[str, Any] = {
        "schema_version": "predictor-metrics/v1",
        "workflow_version": "workflow-v1.1",
        "feature": feature,
        "split": {name: int(len(frame)) for name, frame in frames.items()},
        "alpha_policy": "train-only deterministic holdout; independently selected per representation",
        "models": {},
    }
    ladder = (
        ("ridge", RidgePredictor(alpha="auto")),
        ("xgboost", XGBoostPredictor()),
        ("mlp", MLPPredictor()),
    )
    for name, model in ladder:
        model.fit(X["train"], y["train"])
        artifact = save_predictor(model, model_dir / f"{feature}-{name}.joblib")
        # Exercise the public loading path used by downstream consumers.
        restored = load_predictor(artifact)
        entry: dict[str, Any] = {}
        for split in ("train", "validation", "test"):
            prediction, variance = restored.predict(X[split])
            entry[split] = {
                **metrics(y[split], prediction),
                "variance_min": float(variance.min()),
                "variance_max": float(variance.max()),
            }
        entry["artifact"] = str(artifact.relative_to(Path.cwd()))
        if isinstance(restored, RidgePredictor):
            entry["alpha_selected"] = restored.alpha_
        result["models"][name] = entry

    best = max(result["models"], key=lambda name: result["models"][name]["test"]["spearman"])
    best_test = result["models"][best]["test"]
    result["high_fitness_analysis"] = {
        "best_model": best,
        "top_1pct_recall": best_test["top_k"],
        "conclusion": ("detects high-fitness variants above random expectation"
                       if best_test["top_k"] > .01 else
                       "does not detect high-fitness variants above random expectation"),
    }

    import matplotlib.pyplot as plt
    names = list(result["models"])
    figure_path = version_dir / "figures" / "predictor_comparison.png"
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.5))
    axes[0].bar(names, [result["models"][n]["test"]["spearman"] for n in names])
    axes[0].set(title="Test ranking", ylabel="Spearman rho")
    axes[1].bar(names, [result["models"][n]["test"]["top_k"] for n in names])
    axes[1].axhline(.01, color="black", linestyle="--", linewidth=1, label="random")
    axes[1].set(title="High-fitness retrieval", ylabel="Top-1% recall")
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(figure_path, dpi=160)
    plt.close(fig)
    result["figure"] = str(figure_path.relative_to(Path.cwd()))

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    version_metrics = version_dir / "predictor_metrics.json"
    version_metrics.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the predictor ladder from T2 pools")
    parser.add_argument("--feature", choices=("one_hot", "esm2"), default="one_hot")
    parser.add_argument("--eval-n", type=int, default=2000)
    parser.add_argument("--output", default="reports/predictor_metrics.json")
    args = parser.parse_args()
    result = train_from_t2(feature=args.feature, eval_n=args.eval_n, output=args.output)
    print(json.dumps({name: values["test"] for name, values in result["models"].items()}, indent=2))


if __name__ == "__main__":
    main()
