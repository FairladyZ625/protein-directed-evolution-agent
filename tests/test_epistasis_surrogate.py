"""EpistasisRidgePredictor:pairwise 交互 surrogate 应能抓加性模型抓不到的上位。

用一个纯二阶(XOR 式)合成适应度:fitness 只由两个位点的交互决定,单点边际为 0。
加性 Ridge 的 Spearman 应塌到 ~0,pairwise 应显著为正。同时验接口(fit/predict 形状、
方差非负)。
"""
from __future__ import annotations

import numpy as np
from scipy.stats import spearmanr

from models.train_ladder import EpistasisRidgePredictor, RidgePredictor

AA = "ACDEFGHIKLMNPQRSTVWY"
L = 6


def _onehot(seqs):
    lut = {c: i for i, c in enumerate(AA)}
    x = np.zeros((len(seqs), L * 20))
    for r, s in enumerate(seqs):
        for p, c in enumerate(s):
            x[r, p * 20 + lut[c]] = 1.0
    return x


def _xor_dataset(n=600, seed=0):
    rng = np.random.default_rng(seed)
    wt = "AAAAAA"
    seqs, ys = [], []
    for _ in range(n):
        s = list(wt)
        # positions 0 and 1 each independently A or S; fitness = +1 iff exactly one of them is S
        b0 = rng.random() < 0.5
        b1 = rng.random() < 0.5
        if b0:
            s[0] = "S"
        if b1:
            s[1] = "S"
        # add noise mutations elsewhere with no effect
        if rng.random() < 0.3:
            s[rng.integers(2, L)] = AA[rng.integers(1, 20)]
        seqs.append("".join(s))
        ys.append(1.0 if (b0 ^ b1) else 0.0)
    return seqs, np.array(ys, dtype=float)


def test_interface_shapes_and_nonneg_variance():
    seqs, y = _xor_dataset(200)
    X = _onehot(seqs)
    m = EpistasisRidgePredictor(min_count=2, var_seeds=3).fit(X, y)
    mean, var = m.predict(X)
    assert mean.shape == (len(seqs),)
    assert var.shape == (len(seqs),)
    assert np.all(var >= -1e-9)
    assert m.val_spearman is not None
    assert m.val_spearman > 0.6


def test_pairwise_beats_additive_on_pure_epistasis():
    seqs, y = _xor_dataset(600)
    X = _onehot(seqs)
    n = len(seqs)
    tr, te = np.arange(0, int(n * 0.7)), np.arange(int(n * 0.7), n)
    add = RidgePredictor(seeds=3).fit(X[tr], y[tr])
    epi = EpistasisRidgePredictor(min_count=2, var_seeds=3).fit(X[tr], y[tr])
    sp_add = spearmanr(add.predict(X[te])[0], y[te]).correlation
    sp_epi = spearmanr(epi.predict(X[te])[0], y[te]).correlation
    # additive cannot express XOR -> ~0; pairwise should clearly capture it
    assert abs(sp_add) < 0.3, f"additive unexpectedly captured XOR: {sp_add}"
    assert sp_epi > 0.6, f"pairwise failed to capture XOR: {sp_epi}"
    assert sp_epi > sp_add + 0.3


def test_shuffled_label_negative_control_collapses_validation_spearman():
    seqs, y = _xor_dataset(600)
    shuffled = np.random.default_rng(42).permutation(y)
    model = EpistasisRidgePredictor(min_count=2, var_seeds=3).fit(_onehot(seqs), shuffled)
    assert model.val_spearman is not None
    assert abs(model.val_spearman) < 0.2
