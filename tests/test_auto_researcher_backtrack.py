"""v0.6 meta-layer backtrack: stall tracking, redirect composition, answer-agnostic guards.

Covers the three primitives the full/semi variants share:
1. the hard stall rule (rising curves never flag; flat ones flag at the threshold);
2. `redirect_batch` composition (high predicted mean, mutation composition different from
   the best measured cluster, deterministic, greedy fill only when hop space is exhausted);
3. answer-agnosticism — redirect picks depend on measured labels + surrogate predictions
   only; shuffling the pool's TRUE fitness must not change a single pick.
"""
from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd
import pytest

from agent.auto_researcher import (
    STALL_THRESHOLD,
    _best_cluster_signature,
    _default_exploit_ratio,
    _mutation_set,
    _redirect_indices,
    _rounds_since_improvement,
    _V05_ACQUISITION_PARAGRAPH,
    _V06_ACQUISITION_PARAGRAPH,
    SYSTEM_PROMPT,
)

WT = "AAAAAAAA"


# ---- stall rule -------------------------------------------------------------

def test_rising_curve_never_counts_stagnation():
    # negative control required by the evidence protocol: a strictly improving campaign
    # must not trigger the stall rule at any point.
    history = []
    for v in [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]:
        history.append(v)
        assert _rounds_since_improvement(history) == 0


def test_flat_curve_flags_at_threshold():
    # v0.5-like trajectory: [5.9988, 5.9988, 6.5309, 6.5309, 6.5309, 6.5309]
    history = [5.9988, 5.9988]
    assert _rounds_since_improvement(history) == 1  # below threshold, not stalled yet
    history.append(6.5309)
    assert _rounds_since_improvement(history) == 0  # improvement resets the counter
    history += [6.5309, 6.5309]
    assert _rounds_since_improvement(history) == STALL_THRESHOLD  # fires here
    history.append(6.5309)
    assert _rounds_since_improvement(history) == STALL_THRESHOLD + 1


def test_history_of_one_round_cannot_be_stalled():
    assert _rounds_since_improvement([]) == 0
    assert _rounds_since_improvement([1.0]) == 0


# ---- best-cluster signature ---------------------------------------------------

def _measured_frame(rows):
    return pd.DataFrame(rows, columns=["seq", "fitness"])


def test_signature_collects_shared_top_mutations_only():
    # top-6 share A0S and A1G (>= half); A2P appears in only 2 of 6 -> excluded.
    rows = []
    for i, extra in enumerate(["", "", "A2P", "A2P", "", ""]):
        seq = list(WT)
        seq[0], seq[1] = "S", "G"
        if extra:
            seq[2] = "P"
        rows.append(("".join(seq), 10.0 - i))  # all six are the measured top-6
    # low-fitness noise variants so nlargest actually discriminates
    for i in range(20):
        seq = list(WT)
        seq[3], seq[4] = "S", "S"
        rows.append(("".join(seq), 0.1 * i))
    sig = _best_cluster_signature(_measured_frame(rows), "fitness", WT)
    assert "A0S" in sig and "A1G" in sig
    assert "A2P" not in sig


def test_mutation_set_matches_wt_positions():
    assert _mutation_set("SAAAAAAA", WT) == frozenset({"A0S"})
    assert _mutation_set("SGAAAAAA", WT) == frozenset({"A0S", "A1G"})
    assert _mutation_set(WT, WT) == frozenset()


# ---- redirect composition -----------------------------------------------------

def _toy_pool():
    # 8 candidates over a 3-mutation space; means chosen so mean order != hop order.
    seqs = [
        "SGSAAAAA",  # A0S,A1G,A2S
        "SGGAAAAA",  # A0S,A1G,A2G
        "GGSAAAAA",  # A0G,A1G,A2S
        "SSGAAAAA",  # A0S,A1S,A2G
        "GSGAAAAA",  # A0G,A1S,A2G
        "GSSAAAAA",  # A0G,A1S,A2S
        "SSSAAAAA",  # A0S,A1S,A2S
        "GGGAAAAA",  # A0G,A1G,A2G
    ]
    mean = np.array([9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0])
    return seqs, mean


def test_redirect_prefers_high_mean_with_low_signature_overlap():
    seqs, mean = _toy_pool()
    signature = {"A0S", "A1G"}  # the measured-best cluster lives on these substitutions
    picks, n_hop, n_fill = _redirect_indices(
        mean, np.array(seqs), WT, eligible_indices=range(8),
        signature=signature, n=3, max_overlap=0.5,
    )
    # candidates 0 (overlap 2/2) and 1 (2/2) are excluded despite the highest means;
    # the hop is led by the highest-mean candidates that stay compositionally different
    assert picks == [2, 3, 4]
    assert all(i not in (0, 1) for i in picks)
    assert n_hop == 6 and n_fill == 0


def test_redirect_fills_greedily_only_when_hop_space_exhausted():
    seqs, mean = _toy_pool()
    signature = {"A0S", "A1G"}
    picks, n_hop, n_fill = _redirect_indices(
        mean, np.array(seqs), WT, eligible_indices=range(8),
        signature=signature, n=7, max_overlap=0.5,
    )
    assert len(picks) == 7
    assert n_hop == 6 and n_fill == 1
    assert picks[6] in (0, 1)  # greedy fill = the highest-mean excluded candidate first
    assert picks[6] == 0


def test_redirect_with_empty_signature_degrades_to_pure_mean_order():
    # degenerate basin (no shared signature): redirect == greedy top-n, still deterministic
    seqs, mean = _toy_pool()
    picks, n_hop, n_fill = _redirect_indices(
        mean, np.array(seqs), WT, eligible_indices=range(8),
        signature=set(), n=4, max_overlap=0.5,
    )
    assert picks == [0, 1, 2, 3]
    assert n_hop == 8 and n_fill == 0


def test_redirect_max_overlap_zero_demands_fully_different_composition():
    seqs, mean = _toy_pool()
    signature = {"A1G"}  # only one signature mutation anywhere in position 1
    picks, n_hop, _ = _redirect_indices(
        mean, np.array(seqs), WT, eligible_indices=range(8),
        signature=signature, n=4, max_overlap=0.0,
    )
    for i in picks:
        assert "A1G" not in _mutation_set(seqs[i], WT)


def test_redirect_picks_are_blind_to_true_fitness():
    # answer-agnostic negative control: shuffling the pool's TRUE fitness column must not
    # change a single pick — the composer sees only surrogate means and the measured
    # cluster signature, never pool labels.
    seqs, mean = _toy_pool()
    signature = {"A0S", "A1G"}
    rng = np.random.default_rng(0)
    for _ in range(5):
        _shuffled_fitness = rng.permutation(np.linspace(0, 9, 8))  # never passed in
        picks, _, _ = _redirect_indices(
            mean, np.array(seqs), WT, eligible_indices=range(8),
            signature=signature, n=5, max_overlap=0.5,
        )
        assert picks == [2, 3, 4, 5, 6]


def test_redirect_n_is_clamped_to_eligible_pool():
    seqs, mean = _toy_pool()
    picks, _, _ = _redirect_indices(
        mean, np.array(seqs), WT, eligible_indices=[0, 2, 4],
        signature={"A0S"}, n=48, max_overlap=0.5,
    )
    assert sorted(picks) == [0, 2, 4]


# ---- v0.6 default acquisition ---------------------------------------------------

def test_v06_backtrack_default_is_pure_exploitation_from_round_one():
    # the rank-45 lesson: no forced early-exploration tax in backtrack campaigns
    ratio, source = _default_exploit_ratio("full", 0.90, 1, 6)
    assert (ratio, source) == (1.0, "v06_pure_exploit_default")
    ratio, source = _default_exploit_ratio("semi", 0.5, 1, 6)  # even a weak surrogate
    assert (ratio, source) == (1.0, "v06_pure_exploit_default")


def test_v05_mode_keeps_the_adaptive_default_unchanged():
    ratio, source = _default_exploit_ratio(None, 0.9, 1, 6)
    assert (ratio, source) == (pytest.approx(0.86), "adaptive_default")


def test_v05_default_system_prompt_is_byte_identical():
    assert hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest() == (
        "191ae4c066f2441a455cbedd127e518f18778bb49c5477e1609add028bed0409"
    )


def test_v06_prompt_swaps_acquisition_paragraph_and_keeps_v05_wording():
    v06 = SYSTEM_PROMPT.replace(_V05_ACQUISITION_PARAGRAPH, _V06_ACQUISITION_PARAGRAPH)
    assert v06 != SYSTEM_PROMPT  # the swap must actually apply when v0.6 runs
    assert _V06_ACQUISITION_PARAGRAPH in v06
    assert "PURE" in v06
    # the published v0.5 prompt keeps its adaptive-default wording byte-for-byte
    assert _V05_ACQUISITION_PARAGRAPH in SYSTEM_PROMPT
