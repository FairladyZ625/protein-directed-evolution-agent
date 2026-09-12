"""实验三·提名B诊断:上位感知(pairwise 交互)surrogate 能否让真峰进可达区。

假设(F-851790B5):AAV 7.53 天花板 = 加性 surrogate 表达力上限,非数据/预算——cold-start
(HD≤2)本就含单/双突变实测,S17E×V18A 上位、D0Q 有益单点都在数据里,只是加性模型看不见。

做法:同 cold-start、同门内池(HD≤4 且平均 BLOSUM62≥0),对比
  - additive:Ridge on one-hot(实验二基线)
  - pairwise:Ridge on degree-2 interaction 特征(去常数列后的 one-hot 两两交互 = Potts 式)
看真峰 8.416 的门内预测排名是否从 ~#1283(加性最好)掉进可达区(≤288)。answer-agnostic:
特征与训练只用 cold-start 序列+标签,不用测试峰成分。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

from evolution.datasets import load
from knowledge.validators import load_rules

ROOT = Path(__file__).resolve().parents[1]
_BL = load_rules()["blosum62"]


def _blosum(a, b):
    return 4 if a == b else _BL.get(a, {}).get(b, _BL.get(b, {}).get(a, 0))


def _gate_ok(seq, wt, max_hd=4, blosum_min=0.0):
    sub = [(wt[i], c) for i, c in enumerate(seq) if c != wt[i]]
    if len(sub) > max_hd:
        return False
    if sub and float(np.mean([_blosum(w, c) for w, c in sub])) < blosum_min:
        return False
    return True


def _rank_eval(mean, ypool, gmask, peak_i, budget):
    pz = mean[peak_i]
    rank_all = int((mean > pz).sum()) + 1
    rank_gate = int((mean[gmask] > pz).sum()) + 1
    order = np.argsort(-mean)
    gate_positions = np.where(gmask)[0]
    top_gate = gate_positions[np.argsort(-mean[gate_positions])][:budget]
    return {
        "peak_rank_all": rank_all, "pool_size": int(len(ypool)),
        "peak_rank_gate": rank_gate, "gate_size": int(gmask.sum()),
        "reachable_in_budget": rank_gate <= budget, "budget": budget,
        "spearman_pool": round(float(spearmanr(mean, ypool).correlation), 3),
        "spearman_gate": round(float(spearmanr(mean[gmask], ypool[gmask]).correlation), 3),
        "gate_top_budget_max_fitness": round(float(ypool[top_gate].max()), 3),
        "gate_top_budget_mean_fitness": round(float(ypool[top_gate].mean()), 3),
        "gate_top_budget_strong": int((ypool[top_gate] > 2.6159).sum()),
    }


def scan(budget: int = 288, alpha_add: float = 1.0, alpha_pair: float = 10.0) -> dict:
    spec = load("aav", "one_hot")
    df, wt, fcol = spec.df, spec.wt, spec.fitness_col
    train = df[df.hd <= 2]
    pool = df[df.hd > 2].reset_index(drop=True)
    Xtr = spec.feature_fn(train.seq.tolist())
    ytr = train[fcol].to_numpy()
    Xpool = spec.feature_fn(pool.seq.tolist())
    ypool = pool[fcol].to_numpy()
    gmask = pool.seq.map(lambda s: _gate_ok(s, wt)).to_numpy()
    peak_i = int(np.argmax(ypool))

    out = {"dataset": "aav", "true_peak_fitness": round(float(ypool[peak_i]), 3),
           "true_peak_seq": str(pool.loc[peak_i, "seq"]), "surrogates": {}}

    # additive baseline: Ridge on one-hot
    m = Ridge(alpha=alpha_add).fit(Xtr, ytr)
    out["surrogates"]["additive_ridge_onehot"] = _rank_eval(
        np.asarray(m.predict(Xpool)), ypool, gmask, peak_i, budget)

    # pairwise (Potts-like): drop constant one-hot columns, degree-2 interaction, Ridge
    var = Xtr.var(axis=0)
    keep = var > 1e-8
    Xtr_k, Xpool_k = Xtr[:, keep], Xpool[:, keep]
    poly = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
    Xtr_p = poly.fit_transform(Xtr_k)
    Xpool_p = poly.transform(Xpool_k)
    sc = StandardScaler(with_mean=True)
    Xtr_p = sc.fit_transform(Xtr_p)
    Xpool_p = sc.transform(Xpool_p)
    mp = Ridge(alpha=alpha_pair).fit(Xtr_p, ytr)
    res_pair = _rank_eval(np.asarray(mp.predict(Xpool_p)), ypool, gmask, peak_i, budget)
    res_pair["n_features"] = int(Xtr_p.shape[1])
    res_pair["n_onehot_kept"] = int(keep.sum())
    out["surrogates"]["pairwise_ridge_onehot"] = res_pair

    for name, r in out["surrogates"].items():
        print(f"[{name:26s}] 门内真峰 #{r['peak_rank_gate']}/{r['gate_size']}  "
              f"全池 #{r['peak_rank_all']}  Spearman(pool {r['spearman_pool']}/gate {r['spearman_gate']})  "
              f"{'★★可达!' if r['reachable_in_budget'] else '不可达'}")
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--budget", type=int, default=288)
    p.add_argument("--out", type=Path,
                   default=ROOT / "harness/reports/agentic-v0.4/aav/epistasis_surrogate_scan.json")
    a = p.parse_args(argv)
    res = scan(a.budget)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n")
    print(f"[out] {a.out}")
    return res


if __name__ == "__main__":
    main()
