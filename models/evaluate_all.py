"""Evaluate the predictor ladder under explicit four-role GB1 protocols.

Each feature/split combination selects Ridge alpha on validation, reports a
query-test diagnostic, then evaluates the frozen ladder once on holdout. ESM
evaluation sets are subsampled with fixed seeds to keep extraction tractable;
one-hot uses the same rows for a paired feature comparison.
"""
from __future__ import annotations

import json

import numpy as np

from evolution.random_baseline import load_landscape
from features.pools import (
    build_evaluation_protocol,
    build_hd_extrapolation_split,
    load_three_pools,
    split_train_validation,
)
from features.one_hot import encode_one_hot
from features.esm2 import ESM2Embedder
from models.train_ladder import fit_ladder, score_ladder

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
    protocol = build_evaluation_protocol(pools)
    landscape = load_landscape()

    train_random = protocol.train
    validation_random = protocol.validation
    query_random = _subsample(protocol.query_test, EVAL_N)
    holdout_random = _subsample(protocol.holdout, EVAL_N, seed=SEED + 1)
    train_hd, _ = build_hd_extrapolation_split(landscape)
    train_hd, validation_hd = split_train_validation(
        train_hd, validation_size=max(1, len(train_hd) // 5), seed=SEED
    )
    query_hd = _subsample(
        pools.query_pool.loc[pools.query_pool["HD"] >= 3], EVAL_N
    )
    holdout_hd = _subsample(
        pools.holdout.loc[pools.holdout["HD"] >= 3], EVAL_N, seed=SEED + 1
    )

    embedder = ESM2Embedder()

    def features(df, kind: str):
        variants = df["Variants"].tolist()
        return encode_one_hot(variants) if kind == "one_hot" else embedder.transform(variants)

    combos = {
        "one_hot__random": (train_random, validation_random, query_random, holdout_random, "one_hot"),
        "esm2__random": (train_random, validation_random, query_random, holdout_random, "esm2"),
        "one_hot__hd_extrapolation": (train_hd, validation_hd, query_hd, holdout_hd, "one_hot"),
        "esm2__hd_extrapolation": (train_hd, validation_hd, query_hd, holdout_hd, "esm2"),
    }

    result: dict[str, dict] = {}
    for name, (train, validation, query_test, holdout, kind) in combos.items():
        x_train = features(train, kind)
        x_validation = features(validation, kind)
        x_query = features(query_test, kind)
        x_holdout = features(holdout, kind)
        y_train = train["Fitness"].to_numpy()
        y_validation = validation["Fitness"].to_numpy()
        ladder = fit_ladder(
            x_train,
            y_train,
            x_validation,
            y_validation,
            standardize=kind == "esm2",
        )
        query_metrics = score_ladder(ladder, x_query, query_test["Fitness"].to_numpy())
        # Final evaluation: the fitted ladder sees holdout labels exactly once, here.
        holdout_metrics = score_ladder(ladder, x_holdout, holdout["Fitness"].to_numpy())
        result[name] = {
            "_meta": {
                "n_train": int(len(train)),
                "n_validation": int(len(validation)),
                "n_query_test": int(len(query_test)),
                "n_holdout": int(len(holdout)),
                "feature": kind,
                "roles": {
                    "train": "fit candidate models",
                    "validation": "select hyperparameters only",
                    "query_test": "iterative development diagnostic",
                    "holdout": "single final evaluation",
                },
            },
            "selection": ladder.selection,
            "query_test": query_metrics,
            "holdout": holdout_metrics,
        }
        spearmans = {m: round(holdout_metrics[m]["spearman"], 3) for m in ("ridge", "xgboost", "mlp")}
        print(
            name,
            "roles",
            {"train": len(train), "validation": len(validation), "query_test": len(query_test), "holdout": len(holdout)},
            "selected_alpha",
            ladder.selection["ridge"]["selected_alpha"],
            "holdout_spearman",
            spearmans,
            flush=True,
        )

    from evolution.results_layout import run_dir
    out = run_dir("workflow", "gb1") / "predictor_ladder.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print("written", out, flush=True)


if __name__ == "__main__":
    main()
