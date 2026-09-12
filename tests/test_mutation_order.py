from __future__ import annotations

import pandas as pd
import pytest

from analysis.mutation_order import (
    AAV_PEAK,
    additive_prediction,
    epistasis_rows,
    lower_order_coverage,
    normalize_aav,
)


def landscape(interaction: float = 0.0) -> tuple[pd.DataFrame, str]:
    wt = "AAA"
    effects = {0: 1.0, 1: 2.0, 2: -0.5}
    rows = []
    for mask in range(8):
        seq = "".join("C" if mask & (1 << i) else "A" for i in range(3))
        hd = seq.count("C")
        fitness = 3.0 + sum(effects[i] for i in range(3) if mask & (1 << i))
        if mask == 0b111:
            fitness += interaction
        rows.append({"seq": seq, "hd": hd, "fitness": fitness})
    return pd.DataFrame(rows), wt


def test_pure_additive_landscape_has_zero_epistasis():
    df, wt = landscape()
    residual = epistasis_rows(df, wt).epistasis_residual
    assert len(residual) == 4  # three doubles plus the triple: not an empty-pass control
    assert residual.abs().max() == pytest.approx(0.0)


def test_known_interaction_is_detected():
    df, wt = landscape(interaction=4.25)
    row = epistasis_rows(df, wt).query("sequence == 'CCC'").iloc[0]
    assert row.epistasis_residual == pytest.approx(4.25)


def test_additive_prediction_requires_measured_singles():
    df, wt = landscape()
    fitness = dict(zip(df.seq, df.fitness))
    assert additive_prediction("CCC", wt, fitness) == pytest.approx(5.5)
    fitness.pop("CAA")
    assert additive_prediction("CCC", wt, fitness) is None


def test_lower_order_coverage_counts_all_immediate_constituents():
    df, wt = landscape()
    measured = set(df.seq) - {"CCA"}
    result = lower_order_coverage("CCC", wt, measured)
    assert result["n_required"] == 3
    assert result["n_measured"] == 2
    assert result["fraction"] == pytest.approx(2 / 3)
    assert result["complete"] is False
    assert result["missing_sequences"] == ["CCA"]


def test_aav_peak_residual_and_missing_double_are_observed():
    df, wt = normalize_aav()
    fitness = dict(zip(df.seq, df.fitness))
    predicted = additive_prediction(AAV_PEAK, wt, fitness)
    coverage = lower_order_coverage(AAV_PEAK, wt, set(fitness))
    assert fitness[AAV_PEAK] == pytest.approx(8.41620513056)
    assert predicted == pytest.approx(6.31542751074)
    assert fitness[AAV_PEAK] - predicted == pytest.approx(2.10077761982)
    assert coverage["n_measured"] == 2
    assert coverage["n_required"] == 3
    assert coverage["missing_sequences"] == ["QEEEIRTTNPVATEQYGEVSTNLQRGNR"]
