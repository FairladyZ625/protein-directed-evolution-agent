"""Controlled, equal-budget GB1 comparison by mutation order.

Historical campaign artifacts retain aggregate round metrics and Top-10 rows,
not every nomination.  This analysis therefore runs one preregistered,
oracle-safe diagnostic on query-test: one validation-selected Ridge model ranks
each HD stratum, and labels are joined only after the top budget is frozen.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge

from features.one_hot import encode_one_hot
from features.pools import build_evaluation_protocol, load_three_pools
from models.train_ladder import RidgePredictor, select_ridge_alpha

ROOT = Path(__file__).resolve().parents[1]
WT = "VDGV"
WT_FITNESS = 1.0
DEFAULT_BUDGET = 24  # query-test contains exactly 24 HD=1 variants
GROUPS = (
    ("HD=1", lambda hd: hd == 1),
    ("HD=2", lambda hd: hd == 2),
    ("HD>=3", lambda hd: hd >= 3),
)


def summarize_group(picks: pd.DataFrame, *, pool_size: int, budget: int) -> dict:
    fitness = picks["Fitness"].to_numpy(dtype=float)
    gains = fitness - WT_FITNESS
    return {
        "candidate_pool_size": int(pool_size),
        "budget": int(budget),
        "n_hits_above_wt": int((gains > 0).sum()),
        "hit_rate_above_wt": float((gains > 0).mean()),
        "mean_fitness": float(fitness.mean()),
        "best_fitness": float(fitness.max()),
        "mean_gain_over_wt": float(gains.mean()),
        "best_gain_over_wt": float(gains.max()),
        "positive_gain_per_assay": float(np.maximum(gains, 0).sum() / budget),
        "nominations": [
            {"variant": str(row.Variants), "hd": int(row.HD), "fitness": float(row.Fitness)}
            for row in picks.itertuples(index=False)
        ],
    }


def run(*, budget: int = DEFAULT_BUDGET, seed: int = 42) -> dict:
    pools = load_three_pools()
    protocol = build_evaluation_protocol(pools, seed=seed)
    X_train = encode_one_hot(protocol.train.Variants.tolist())
    X_validation = encode_one_hot(protocol.validation.Variants.tolist())
    y_train = protocol.train.Fitness.to_numpy()
    y_validation = protocol.validation.Fitness.to_numpy()
    selection = select_ridge_alpha(
        X_train, y_train, X_validation, y_validation
    )

    X_development = np.concatenate((X_train, X_validation), axis=0)
    y_development = np.concatenate((y_train, y_validation), axis=0)
    model = RidgePredictor(alpha=selection["selected_alpha"], seeds=5).fit(
        X_development, y_development
    )

    query = protocol.query_test.copy()
    predicted_mean, _ = model.predict(encode_one_hot(query.Variants.tolist()))
    query["predicted_mean"] = predicted_mean
    groups = {}
    for name, predicate in GROUPS:
        candidates = query.loc[predicate(query.HD)].copy()
        if len(candidates) < budget:
            raise ValueError(f"{name} has {len(candidates)} candidates, below budget={budget}")
        # Freeze the model-ranked batch before reading its true Fitness values.
        ranked = candidates.sort_values(
            ["predicted_mean", "Variants"], ascending=[False, True], kind="stable"
        )
        picks = ranked.head(budget).drop(columns="predicted_mean")
        groups[name] = summarize_group(picks, pool_size=len(candidates), budget=budget)

    shuffled_y = np.random.default_rng(123).permutation(y_train)
    shuffled_pred = Ridge(alpha=selection["selected_alpha"]).fit(X_train, shuffled_y).predict(X_validation)
    negative_spearman = float(spearmanr(y_validation, shuffled_pred).statistic)
    return {
        "schema_version": "mutation-order.v1",
        "dataset": "GB1 Wu 2016",
        "wild_type": WT,
        "wild_type_fitness": WT_FITNESS,
        "source": {
            "outer_pools": "data/pools/{train_pool,query_pool,holdout}.csv",
            "historical_trajectory_audit": "harness/reports/agentic-v0.*/aav/*metrics.json",
            "historical_trajectory_limitation": "round aggregates and Top-10 only; full nominations/HD unavailable",
        },
        "protocol": {
            "feature": "one_hot_80d",
            "model": "5-seed Ridge ensemble",
            "seed": seed,
            "selection_metric": "validation Spearman",
            "selected_alpha": selection["selected_alpha"],
            "equal_budget_per_group": budget,
            "nomination_space": "query-test only; holdout untouched",
            "hit_definition": "true fitness > WT fitness (1.0)",
            "gain_definition": "true fitness - WT fitness",
            "budget_efficiency_definition": "sum(max(gain, 0)) / assays",
        },
        "negative_control": {
            "shuffle_seed": 123,
            "validation_spearman": negative_spearman,
        },
        "groups": groups,
    }


def plot(report: dict, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = list(report["groups"])
    metrics = (
        ("hit_rate_above_wt", "hit rate (>WT)"),
        ("best_gain_over_wt", "best gain over WT"),
        ("positive_gain_per_assay", "positive gain / assay"),
    )
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.4))
    for ax, (key, title) in zip(axes, metrics):
        values = [report["groups"][label][key] for label in labels]
        ax.bar(labels, values, color=("#4c78a8", "#f58518", "#54a24b"))
        ax.set_title(title)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle(f"GB1 equal-budget mutation-order comparison (n={report['protocol']['equal_budget_per_group']}/group)")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--out-dir", type=Path, default=ROOT / "harness" / "reports" / "pkgB-eval-protocol"
    )
    args = parser.parse_args(argv)
    report = run(budget=args.budget, seed=args.seed)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "mutation_order.json"
    figure_path = args.out_dir / "mutation_order.png"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    plot(report, figure_path)
    print(f"[out] {json_path}")
    print(f"[out] {figure_path}")
    print(
        "selected_alpha=",
        report["protocol"]["selected_alpha"],
        "shuffle_spearman=",
        round(report["negative_control"]["validation_spearman"], 6),
    )
    for name, values in report["groups"].items():
        print(
            name,
            f"pool={values['candidate_pool_size']}",
            f"budget={values['budget']}",
            f"hit_rate={values['hit_rate_above_wt']:.3f}",
            f"best_gain={values['best_gain_over_wt']:.4f}",
            f"gain_per_assay={values['positive_gain_per_assay']:.4f}",
        )
    return report


if __name__ == "__main__":
    main()
