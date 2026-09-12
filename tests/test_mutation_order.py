from __future__ import annotations

import pandas as pd

from analysis.mutation_order import summarize_group


def test_group_metrics_use_wt_referenced_gain_and_fixed_budget():
    picks = pd.DataFrame(
        {"Variants": ["AAAA", "BBBB"], "HD": [1, 1], "Fitness": [0.5, 2.5]}
    )
    result = summarize_group(picks, pool_size=20, budget=2)
    assert result["n_hits_above_wt"] == 1
    assert result["hit_rate_above_wt"] == 0.5
    assert result["mean_gain_over_wt"] == 0.5
    assert result["best_gain_over_wt"] == 1.5
    assert result["positive_gain_per_assay"] == 0.75
