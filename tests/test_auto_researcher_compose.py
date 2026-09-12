"""Quality-aware compose_batch allocation primitives."""
from __future__ import annotations

import numpy as np
import pytest

from agent.auto_researcher import (
    _adaptive_exploit_ratio,
    _compose_batch_indices,
    _enforce_exploit_floor,
)


def test_compose_batch_honours_ratio_and_deduplicates():
    mean = np.arange(100, dtype=float)
    var = np.linspace(1.0, 0.0, 100)
    picks, n_exploit, n_explore = _compose_batch_indices(
        mean,
        var,
        eligible_indices=range(100),
        exploit_ratio=0.85,
        n=48,
        rng=np.random.default_rng(42),
    )
    assert (n_exploit, n_explore) == (41, 7)
    assert len(picks) == len(set(picks)) == 48
    assert picks[:41] == list(range(99, 58, -1))


def test_high_cv_adaptive_ratio_anneals_to_near_greedy():
    ratios = [_adaptive_exploit_ratio(0.9, rnd, 6) for rnd in range(1, 7)]
    assert ratios[0] == pytest.approx(0.86)
    assert ratios[-2:] == [1.0, 1.0]
    assert ratios == sorted(ratios)


def test_low_cv_keeps_structured_exploration_early():
    assert _adaptive_exploit_ratio(0.5, 1, 6) == 0.4


def test_final_two_rounds_force_ninety_percent_exploitation():
    assert _enforce_exploit_floor(0.4, 0.5, 5, 6) == (0.9, 0.9)
    assert _enforce_exploit_floor(0.4, 0.5, 6, 6) == (0.9, 0.9)
