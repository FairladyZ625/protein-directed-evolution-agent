"""Post-mortem: why the autonomous agentic agent underperforms greedy on AAV.

The agentic SOL agent (agent/auto_researcher.py), given the freedom to explore, lost
to naive greedy on the AAV pool campaign (cum_top10_max 5.96 vs 7.53; 15 vs 85 strong
hits). This is a genuine, reproducible finding — not a bug. This script produces the
mechanistic evidence for *why*, entirely from the public data + the shared predictor,
so the claim is auditable.

Core result: on this landscape the surrogate's epistemic uncertainty (bootstrap
variance) tracks mutational order, and high-order mutants are mostly non-functional.
So "explore where the model is uncertain" — the textbook active-learning heuristic —
actively selects for dead proteins. The true peak is a low-order variant sitting in a
double blind spot (under-rated mean AND low variance), unreachable by any
mean/uncertainty-guided policy within budget.

Run:  PYTHONPATH=. python analysis/agentic_postmortem.py [--feature one_hot]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from evolution.datasets import load_aav
from models.train_ladder import RidgePredictor

ROOT = Path(__file__).resolve().parents[1]


def postmortem(feature: str = "one_hot", budget_total: int = 288, seeds: int = 5) -> dict:
    spec = load_aav(feature=feature)
    df = spec.df
    cold = df[df.hd <= 2]
    pool = df[df.hd > 2].reset_index(drop=True)
    strong_thr = float(np.quantile(df.fitness, 0.9))

    # ESM-2 embeddings are continuous / non-unit-scale: standardise and relax alpha or Ridge
    # is mis-regularised (raw Spearman 0.47 -> fair 0.60). one-hot needs neither.
    esm = feature != "one_hot"
    model = RidgePredictor(seeds=seeds, standardize=esm, alpha=10.0 if esm else 1.0).fit(
        spec.feature_fn(cold.seq.tolist()), cold.fitness.to_numpy())
    mean, var = model.predict(spec.feature_fn(pool.seq.tolist()))
    mean, var = np.asarray(mean), np.asarray(var)
    fit, hd = pool.fitness.to_numpy(), pool.hd.to_numpy()

    # variance quartiles: the axis an uncertainty-led explorer climbs
    q = np.quantile(var, [0, .25, .5, .75, 1.0])
    quartiles = []
    for i in range(4):
        sel = (var >= q[i]) & (var <= q[i + 1] if i == 3 else var < q[i + 1])
        quartiles.append({"quartile": i + 1, "var_lo": round(float(q[i]), 4),
                          "var_hi": round(float(q[i + 1]), 4),
                          "mean_hd": round(float(hd[sel].mean()), 2),
                          "mean_fitness": round(float(fit[sel].mean()), 3),
                          "strong_frac_pct": round(float((fit[sel] >= strong_thr).mean() * 100), 1),
                          "max_fitness": round(float(fit[sel].max()), 2)})

    poles = {}
    for name, order in [("greedy_by_mean", np.argsort(-mean)),
                        ("explorer_by_variance", np.argsort(-var))]:
        idx = order[:budget_total]
        poles[name] = {"mean_hd": round(float(hd[idx].mean()), 2),
                       "mean_fitness": round(float(fit[idx].mean()), 3),
                       "max_fitness": round(float(fit[idx].max()), 3),
                       "n_strong": int((fit[idx] >= strong_thr).sum())}

    peak_i = int(np.argmax(fit))
    peak = {"fitness": round(float(fit[peak_i]), 3), "hd": int(hd[peak_i]),
            "rank_by_mean": int((mean > mean[peak_i]).sum()) + 1,
            "rank_by_variance": int((var > var[peak_i]).sum()) + 1,
            "pool_size": int(len(pool))}

    return {
        "dataset": spec.name, "cold_start": int(len(cold)), "pool": int(len(pool)),
        "strong_threshold": round(strong_thr, 3), "pool_peak_fitness": round(float(fit.max()), 3),
        "predictor_skill_spearman_mean_fitness": round(float(spearmanr(mean, fit).correlation), 3),
        "spearman_var_hd": round(float(spearmanr(var, hd).correlation), 3),
        "spearman_var_fitness": round(float(spearmanr(var, fit).correlation), 3),
        "variance_quartiles": quartiles, "two_pole_picks": poles, "true_peak": peak,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--feature", default="one_hot", choices=("one_hot", "esm2"))
    p.add_argument("--out", type=Path, default=ROOT / "reports" / "agentic_postmortem_aav.json")
    a = p.parse_args(argv)
    rep = postmortem(feature=a.feature)
    a.out.write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    print(f"\n[out] {a.out}")
    return rep


if __name__ == "__main__":
    main()
