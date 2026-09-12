"""Evaluate the predictor ladder across [one-hot, ESM-2] x [random, HD-extrapolation] splits.

Produces reports/predictor_metrics.json with an honest feature x split comparison.
ESM test sets are subsampled (fixed seed) to keep 650M extraction tractable; one-hot
uses the same subsample so the two features are compared on identical rows.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from evolution.random_baseline import load_landscape
from features.pools import load_three_pools, build_hd_extrapolation_split
from features.one_hot import encode_one_hot
from features.esm2 import ESM2Embedder
from models.train_ladder import evaluate_ladder

SEED = 42
EVAL_N = 2000


def _subsample(df, n: int, seed: int = SEED):
    if len(df) <= n:
        return df.reset_index(drop=True)
    rng = np.random.default_rng(seed)
    idx = np.sort(rng.choice(len(df), size=n, replace=False))
    return df.iloc[idx].reset_index(drop=True)


def main() -> None:
    pools = load_three_pools()
    landscape = load_landscape()

    train_random = pools.train_pool
    test_random = _subsample(pools.query_pool, EVAL_N)
    train_hd, test_hd_full = build_hd_extrapolation_split(landscape)
    test_hd = _subsample(test_hd_full, EVAL_N)

    embedder = ESM2Embedder()

    def features(df, kind: str):
        variants = df["Variants"].tolist()
        return encode_one_hot(variants) if kind == "one_hot" else embedder.transform(variants)

    combos = {
        "one_hot__random": (train_random, test_random, "one_hot"),
        "esm2__random": (train_random, test_random, "esm2"),
        "one_hot__hd_extrapolation": (train_hd, test_hd, "one_hot"),
        "esm2__hd_extrapolation": (train_hd, test_hd, "esm2"),
    }

    # 每个组合跑两遍,唯一变量是特征是否标准化。不跑这个对照就不能说「ESM 不如 one-hot」:
    # one-hot 是 0/1、本身已是单位尺度,ESM-2 是连续非单位尺度的 1280 维,同一个 Ridge(alpha=1)
    # 对两者的正则化强度实际上不同,单跑 raw 一档等于把预处理伪影读成了特征质量差异。
    result: dict[str, dict] = {}
    for name, (train, test, kind) in combos.items():
        x_train = features(train, kind)
        x_test = features(test, kind)
        y_train = train["Fitness"].to_numpy()
        y_test = test["Fitness"].to_numpy()
        entry: dict[str, dict] = {}
        for scaling, standardize in (("raw", False), ("standardized", True)):
            entry[scaling] = evaluate_ladder(x_train, y_train, x_test, y_test, standardize=standardize)
            spearmans = {m: round(entry[scaling][m]["spearman"], 4) for m in ("ridge", "xgboost", "mlp")}
            print(name, scaling, "n_train", len(train), "n_test", len(test), "spearman", spearmans, flush=True)
        entry["_meta"] = {"n_train": int(len(train)), "n_test": int(len(test)), "feature": kind}
        result[name] = entry

    from evolution.results_layout import run_dir
    out = run_dir("workflow", "gb1") / "predictor_ladder_scaling_ablation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print("written", out, flush=True)


if __name__ == "__main__":
    main()
