"""Logic-only checks for the input-WT path in the Streamlit demo."""
from __future__ import annotations

import numpy as np
import pytest

from app.demo import (recommend_from_wild_type, recommendation_disclaimer,
                      relative_mutations, single_mutant_candidates)


class _Predictor:
    """Small deterministic Ridge-shaped stand-in: predict(X) -> mean, variance."""

    def predict(self, X):
        weights = np.arange(X.shape[1], dtype=float)
        return X @ weights, np.zeros(len(X))


def test_recommendations_change_with_wild_type_positive_control():
    predictor = _Predictor()
    vdgv = recommend_from_wild_type("VDGV", predictor, top_k=10)
    aaaa = recommend_from_wild_type("AAAA", predictor, top_k=10)

    assert {row["variant"] for row in vdgv} != {row["variant"] for row in aaaa}
    assert {mutation[0] for row in vdgv for mutation in row["mutations"]} <= set("VDGV")
    assert {mutation[0] for row in aaaa for mutation in row["mutations"]} == {"A"}


def test_invalid_wild_type_is_rejected_not_silently_reset():
    with pytest.raises(ValueError, match="exactly four standard amino acids"):
        single_mutant_candidates("VDG*")


def test_unmeasured_wild_type_disclaimer_says_prediction_not_measurement():
    message = recommendation_disclaimer("AAAA", {"VDGV"})
    assert "模型预测值而非实测值" in message


def test_mutation_labels_are_relative_to_entered_wild_type():
    assert relative_mutations("FAGV", "VDGV") == ("V39F", "D40A")
