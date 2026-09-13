"""Measured mutation-order analysis for the GB1 and AAV landscapes.

Run with::

    PYTHONPATH=. python analysis/mutation_order.py

The analysis never queries an oracle outside the two supplied measured tables.
"""
from __future__ import annotations

import argparse
from itertools import combinations
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split

from evolution.datasets import AAV_WT, load_aav, one_hot_encoder
from evolution.random_baseline import load_landscape
from models.alpha_sweep import ALPHAS

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "harness" / "reports" / "analysis-v0.1"
AAV_PEAK = "QEEEIRTTNPVATEQYGEASTNLQRGNR"


def mutation_positions(sequence: str, wt: str) -> tuple[int, ...]:
    return tuple(i for i, (a, b) in enumerate(zip(sequence, wt)) if a != b)


def subset_sequence(sequence: str, wt: str, positions: Iterable[int]) -> str:
    keep = set(positions)
    return "".join(aa if i in keep else wt[i] for i, aa in enumerate(sequence))


def lower_order_coverage(sequence: str, wt: str, measured: set[str]) -> dict:
    """Coverage of all immediate (k-1)-order constituents of ``sequence``."""
    positions = mutation_positions(sequence, wt)
    subsets = [
        subset_sequence(sequence, wt, chosen)
        for chosen in combinations(positions, len(positions) - 1)
    ]
    present = [s for s in subsets if s in measured]
    missing = [s for s in subsets if s not in measured]
    return {
        "n_required": len(subsets),
        "n_measured": len(present),
        "fraction": float(len(present) / len(subsets)) if subsets else 1.0,
        "complete": not missing,
        "missing_sequences": missing,
    }


def additive_prediction(sequence: str, wt: str, fitness: dict[str, float]) -> float | None:
    """WT plus measured single-mutant effects; None if a constituent is missing."""
    if wt not in fitness:
        return None
    singles = [subset_sequence(sequence, wt, [p]) for p in mutation_positions(sequence, wt)]
    if any(single not in fitness for single in singles):
        return None
    baseline = fitness[wt]
    return float(baseline + sum(fitness[single] - baseline for single in singles))


def epistasis_rows(df: pd.DataFrame, wt: str) -> pd.DataFrame:
    fitness = dict(zip(df.seq, df.fitness))
    measured = set(fitness)
    rows = []
    for row in df.loc[df.hd >= 2].itertuples(index=False):
        additive = additive_prediction(row.seq, wt, fitness)
        if additive is None:
            continue
        coverage = lower_order_coverage(row.seq, wt, measured)
        rows.append({
            "sequence": row.seq,
            "order": int(row.hd),
            "observed_fitness": float(row.fitness),
            "additive_prediction": additive,
            "epistasis_residual": float(row.fitness - additive),
            "lower_order_coverage": coverage,
        })
    return pd.DataFrame(rows)


def _safe_spearman(actual: np.ndarray, predicted: np.ndarray) -> float | None:
    score = spearmanr(actual, predicted).statistic
    return None if score is None or np.isnan(score) else float(score)


def extrapolation(df: pd.DataFrame, wt: str, train_max: int, test_order: int) -> dict:
    train = df.loc[df.hd <= train_max]
    test = df.loc[df.hd == test_order]
    if train.empty or test.empty:
        raise ValueError(f"empty extrapolation split <= {train_max} -> {test_order}")
    encode = one_hot_encoder(len(wt))
    x_train, y_train = encode(train.seq.tolist()), train.fitness.to_numpy(dtype=float)
    x_test, y_test = encode(test.seq.tolist()), test.fitness.to_numpy(dtype=float)
    tr, va = train_test_split(np.arange(len(train)), test_size=0.2, random_state=0)
    validation = {}
    for alpha in ALPHAS:
        pred = Ridge(alpha=alpha).fit(x_train[tr], y_train[tr]).predict(x_train[va])
        validation[alpha] = _safe_spearman(y_train[va], pred)
    selected = max(ALPHAS, key=lambda a: -2.0 if validation[a] is None else validation[a])
    prediction = Ridge(alpha=selected).fit(x_train, y_train).predict(x_test)
    return {
        "train_orders": f"0..{train_max}",
        "test_order": test_order,
        "n_train": int(len(train)),
        "n_test": int(len(test)),
        "feature": "position-wise one-hot",
        "model": "Ridge",
        "alpha_selection": "80/20 training-only holdout, random_state=0",
        "alpha_selected": float(selected),
        "validation_spearman_by_alpha": {str(a): validation[a] for a in ALPHAS},
        "test_spearman": _safe_spearman(y_test, prediction),
    }


def normalize_gb1() -> tuple[pd.DataFrame, str]:
    raw = load_landscape()
    return raw.rename(columns={"Variants": "seq", "Fitness": "fitness", "HD": "hd"}), "VDGV"


def normalize_aav() -> tuple[pd.DataFrame, str]:
    spec = load_aav(feature="one_hot")
    return spec.df[["seq", "fitness", "hd"]].copy(), spec.wt


def analyze(df: pd.DataFrame, wt: str, dataset: str) -> dict:
    values = dict(zip(df.seq, df.fitness))
    if wt not in values:
        raise ValueError(f"{dataset}: WT is not measured")
    wt_fitness = float(values[wt])
    distribution = {}
    coverage = {}
    measured = set(values)
    for order, group in df.groupby("hd", sort=True):
        fit = group.fitness.astype(float)
        distribution[str(int(order))] = {
            "source": "measured",
            "n_variants": int(len(group)),
            "fitness_median": float(fit.median()),
            "fitness_q25": float(fit.quantile(0.25)),
            "fitness_q75": float(fit.quantile(0.75)),
            "fitness_max": float(fit.max()),
            "beneficial_fraction_vs_wt": float((fit > wt_fitness).mean()),
        }
        if order >= 2:
            records = [lower_order_coverage(s, wt, measured) for s in group.seq]
            coverage[str(int(order))] = {
                "source": "measured presence/absence",
                "denominator": "measured variants at this order",
                "n_variants": int(len(records)),
                "n_complete": int(sum(r["complete"] for r in records)),
                "complete_fraction": float(np.mean([r["complete"] for r in records])),
                "mean_subset_coverage": float(np.mean([r["fraction"] for r in records])),
                "subset_denominator_per_variant": f"all {int(order)} immediate order-{int(order)-1} constituents",
            }

    epi = epistasis_rows(df, wt)
    epi_summary = {}
    for order, group in epi.groupby("order", sort=True):
        residual = group.epistasis_residual
        strongest = group.nlargest(10, "epistasis_residual").to_dict("records")
        epi_summary[str(int(order))] = {
            "source": "estimated from measured fitness: observed - (WT + sum measured single effects)",
            "n_with_all_single_mutants": int(len(group)),
            "n_with_all_lower_orders": int(sum(r["complete"] for r in group.lower_order_coverage)),
            "residual_median": float(residual.median()),
            "residual_q25": float(residual.quantile(0.25)),
            "residual_q75": float(residual.quantile(0.75)),
            "residual_mean": float(residual.mean()),
            "strongest_positive": strongest,
        }

    peak = None
    if dataset == "aav":
        matches = epi.loc[epi.sequence == AAV_PEAK]
        if len(matches) != 1:
            raise ValueError("AAV measured peak missing from epistasis rows")
        peak = matches.iloc[0].to_dict()

    predictions = [extrapolation(df, wt, 1, 2), extrapolation(df, wt, 2, 3)]
    return {
        "dataset": dataset,
        "n_measured_variants": int(len(df)),
        "wt_sequence": wt,
        "wt_fitness": wt_fitness,
        "distribution_by_order": distribution,
        "additive_extrapolation": predictions,
        "epistasis_by_order": epi_summary,
        "lower_order_coverage_by_order": coverage,
        "aav_peak_posthoc": peak,
    }


def plot_report(report: dict, output: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    orders = sorted(map(int, report["distribution_by_order"]))
    dist = report["distribution_by_order"]
    epi = report["epistasis_by_order"]
    coverage = report["lower_order_coverage_by_order"]
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    axes[0, 0].plot(orders, [dist[str(o)]["fitness_median"] for o in orders], "o-", label="median")
    axes[0, 0].plot(orders, [dist[str(o)]["fitness_max"] for o in orders], "o-", label="maximum")
    axes[0, 0].set(xlabel="Mutation order", ylabel="Measured fitness", title="Fitness by mutation order")
    axes[0, 0].legend()
    axes[0, 1].bar(["≤1→2", "≤2→3"], [x["test_spearman"] for x in report["additive_extrapolation"]], label="Ridge")
    axes[0, 1].set(xlabel="Train→test order", ylabel="Spearman ρ", title="Low-to-high extrapolation")
    axes[0, 1].legend()
    eo = sorted(map(int, epi))
    axes[1, 0].plot(eo, [epi[str(o)]["residual_median"] for o in eo], "o-", label="median residual")
    axes[1, 0].axhline(0, color="black", linewidth=0.8)
    axes[1, 0].set(xlabel="Mutation order", ylabel="Observed − additive", title="Epistasis residual")
    axes[1, 0].legend()
    co = sorted(map(int, coverage))
    axes[1, 1].plot(co, [coverage[str(o)]["complete_fraction"] for o in co], "o-", label="complete variants")
    axes[1, 1].plot(co, [coverage[str(o)]["mean_subset_coverage"] for o in co], "o-", label="mean subset coverage")
    axes[1, 1].set(xlabel="Mutation order", ylabel="Coverage fraction", ylim=(-0.03, 1.03), title="Measured lower-order coverage")
    axes[1, 1].legend()
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)


def write_report(report: dict, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "mutation_order.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    plot_report(report, directory / "figures" / "mutation_order.png")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    reports = {}
    for dataset, loader in (("gb1", normalize_gb1), ("aav", normalize_aav)):
        df, wt = loader()
        reports[dataset] = analyze(df, wt, dataset)
        write_report(reports[dataset], args.output / dataset)
        print(dataset, json.dumps({
            "n": reports[dataset]["n_measured_variants"],
            "spearman": [x["test_spearman"] for x in reports[dataset]["additive_extrapolation"]],
        }))


if __name__ == "__main__":
    main()
