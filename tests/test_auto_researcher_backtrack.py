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


def test_acquisition_flag_decouples_policy_from_backtrack_without_moving_v05_or_v06():
    """v0.8 解耦:采集档位与 backtrack 各管各的,但历史配对必须逐字节不变。

    v0.8 之前这两件事是一个旋钮:传 --backtrack 会**顺带**把 v0.5 的质量感知采集段落
    换成 v0.6 的纯利用段落。于是「去掉 --backtrack」同时改了采集策略、stall 注入
    和可用工具三样,任何差异都归因不到具体哪一样——这样的对照没法解释。

    解耦之后仍必须保证:acquisition=None 时的输出与解耦前完全一致,
    否则 v0.5/v0.6 两个已发布版本的数据就不可复现了。
    """
    from agent.auto_researcher import (SYSTEM_PROMPT, _BACKTRACK_FULL_NOTE,
                                       _BACKTRACK_SEMI_NOTE, _V05_ACQUISITION_PARAGRAPH,
                                       _V06_ACQUISITION_PARAGRAPH, compose_system_prompt)

    v06_body = SYSTEM_PROMPT.replace(_V05_ACQUISITION_PARAGRAPH, _V06_ACQUISITION_PARAGRAPH)

    # 历史配对:三条都必须逐字节等于解耦前的产物
    assert compose_system_prompt(None) == SYSTEM_PROMPT
    assert compose_system_prompt("semi") == v06_body + _BACKTRACK_SEMI_NOTE
    assert compose_system_prompt("full") == v06_body + _BACKTRACK_FULL_NOTE

    # 新增的两个格子:backtrack 固定为 semi,只换采集档位
    v05_semi = compose_system_prompt("semi", "v05")
    v06_semi = compose_system_prompt("semi", "v06")
    assert v05_semi == SYSTEM_PROMPT + _BACKTRACK_SEMI_NOTE
    assert v06_semi == v06_body + _BACKTRACK_SEMI_NOTE
    # 两格之间唯一的差别就是采集段落本身
    assert _V05_ACQUISITION_PARAGRAPH in v05_semi and _V06_ACQUISITION_PARAGRAPH not in v05_semi
    assert _V06_ACQUISITION_PARAGRAPH in v06_semi and _V05_ACQUISITION_PARAGRAPH not in v06_semi
    # stall note 在两格里都在 —— 这正是解耦要保住的「其余条件不变」
    assert v05_semi.endswith(_BACKTRACK_SEMI_NOTE) and v06_semi.endswith(_BACKTRACK_SEMI_NOTE)


def test_acquisition_switch_moves_both_layers_not_just_the_prompt():
    """采集档位有两层:系统提示词段落,和 compose_batch 的工具级默认。两层必须一起动。

    第一次 v0.8 的 2x2 就栽在这里:只解耦了提示词层,工具层的默认仍挂在 backtrack 上。
    结果四个臂全部返回 allocation_source='v06_pure_exploit_default'、批次逐位相同——
    提示词告诉 agent「用自适应规则」,而 compose_batch 照样给纯利用。
    **只修一层比两层都不修更危险**,因为实验看起来是受控的,其实不是。
    """
    from agent.auto_researcher import (_V05_ACQUISITION_PARAGRAPH, _V06_ACQUISITION_PARAGRAPH,
                                       _default_exploit_ratio, compose_system_prompt)

    # 工具层:同样固定 backtrack='semi',只切 acquisition
    v05_ratio, v05_src = _default_exploit_ratio("semi", 0.90, 1, 6, "v05")
    v06_ratio, v06_src = _default_exploit_ratio("semi", 0.90, 1, 6, "v06")
    assert v06_src == "v06_pure_exploit_default" and v06_ratio == 1.0
    assert v05_src == "adaptive_default", "工具层没跟着切——这正是第一次 2x2 失败的原因"
    assert v05_ratio < 1.0, "自适应档位不应等于纯利用"

    # 提示词层:同一组参数下也必须切
    assert _V05_ACQUISITION_PARAGRAPH in compose_system_prompt("semi", "v05")
    assert _V06_ACQUISITION_PARAGRAPH in compose_system_prompt("semi", "v06")

    # 历史配对(acquisition=None)两层都必须保持原样,否则 v0.5/v0.6 不可复现
    assert _default_exploit_ratio("semi", 0.90, 1, 6)[1] == "v06_pure_exploit_default"
    assert _default_exploit_ratio(None, 0.90, 1, 6)[1] == "adaptive_default"
