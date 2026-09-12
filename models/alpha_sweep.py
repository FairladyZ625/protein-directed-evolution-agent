"""在 alpha 网格上比较 one-hot 与 ESM-2,消除"固定 alpha=1"这个混杂。

为什么需要这个脚本:predictor_ladder 固定 Ridge(alpha=1) 比较两种表征,而 alpha=1 对
两者意味着完全不同的正则化强度——one-hot 是 0/1,逐维方差 ~0.25;GB1 上的 ESM-2
逐维方差只有 ~1e-4(实测:1280 维中位数 1.06e-4,最小 3.4e-5,最大 4.5e-3)。Ridge 的
目标是 ||y-Xw||^2 + alpha*||w||^2,特征尺度小则同一个 w 需要更大的模长才能拟合,于是
alpha=1 对 ESM 是**强**正则、对 one-hot 是**弱**正则。

实测后果(GB1,random split,Spearman):
  raw          esm 0.4911 vs one-hot 0.4854   <- ESM 略胜
  standardized esm 0.2944 vs one-hot 0.4854   <- ESM 大败
同一份数据、同一个模型,只因预处理不同就结论反向。**因此固定 alpha 下的任何一侧都
不能用来支撑"某表征更好",两者都只是在报告 alpha=1 恰好多贴合谁的尺度。**

本脚本对每个 (特征 × 划分) 在训练集内用一次 80/20 留出选 alpha(answer-agnostic,
不看测试集),再在测试集上报分——这才是表征之间可比的口径。选法与仓内既有的
EpistasisRidgePredictor._select_alpha 一致。

用法:PYTHONPATH=. python models/alpha_sweep.py
"""
from __future__ import annotations

import json

import numpy as np
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from evolution.random_baseline import load_landscape
from features.pools import load_three_pools, build_hd_extrapolation_split
from features.one_hot import encode_one_hot
from features.esm2 import ESM2Embedder
from models.evaluate_all import EVAL_N, _subsample

ALPHAS = (0.01, 0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0)


def _score(alpha: float, Xtr, ytr, Xte, yte) -> float:
    pred = Ridge(alpha=alpha).fit(Xtr, ytr).predict(Xte)
    s = spearmanr(yte, pred).statistic
    return -2.0 if s is None or np.isnan(s) else float(s)


def sweep(X_train, y_train, X_test, y_test, *, standardize: bool) -> dict:
    X_train = np.asarray(X_train, dtype=float)
    X_test = np.asarray(X_test, dtype=float)
    if standardize:
        scaler = StandardScaler().fit(X_train)
        X_train, X_test = scaler.transform(X_train), scaler.transform(X_test)
    # answer-agnostic:alpha 只在训练集内部的留出split上选,绝不看 y_test
    tr, va = train_test_split(np.arange(len(y_train)), test_size=0.2, random_state=0)
    val = {a: _score(a, X_train[tr], y_train[tr], X_train[va], y_train[va]) for a in ALPHAS}
    best = max(val, key=val.get)
    return {
        "alpha_selected": best,
        "val_spearman_at_selected": round(val[best], 4),
        "test_spearman_at_selected": round(_score(best, X_train, y_train, X_test, y_test), 4),
        "test_spearman_by_alpha": {str(a): round(_score(a, X_train, y_train, X_test, y_test), 4) for a in ALPHAS},
        "val_spearman_by_alpha": {str(a): round(v, 4) for a, v in val.items()},
    }


def main() -> None:
    pools = load_three_pools()
    landscape = load_landscape()
    train_hd, test_hd_full = build_hd_extrapolation_split(landscape)
    embedder = ESM2Embedder()

    def feats(df, kind):
        v = df["Variants"].tolist()
        return encode_one_hot(v) if kind == "one_hot" else embedder.transform(v)

    splits = {
        "random": (pools.train_pool, _subsample(pools.query_pool, EVAL_N)),
        "hd_extrapolation": (train_hd, _subsample(test_hd_full, EVAL_N)),
    }

    result: dict[str, dict] = {}
    for split_name, (train, test) in splits.items():
        y_train, y_test = train["Fitness"].to_numpy(), test["Fitness"].to_numpy()
        for kind in ("one_hot", "esm2"):
            x_train, x_test = feats(train, kind), feats(test, kind)
            for scaling, std in (("raw", False), ("standardized", True)):
                key = f"{kind}__{split_name}__{scaling}"
                result[key] = sweep(x_train, y_train, x_test, y_test, standardize=std)
                r = result[key]
                print(f"{key:42s} alpha*={r['alpha_selected']:<8g} test_spearman={r['test_spearman_at_selected']}", flush=True)

    from evolution.results_layout import run_dir
    out = run_dir("workflow", "gb1") / "predictor_alpha_sweep.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print("written", out, flush=True)


if __name__ == "__main__":
    main()
