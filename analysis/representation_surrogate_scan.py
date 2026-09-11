"""实验二诊断:表征 × 代理模型 → 门内真峰的可达性。

v0.2 证明门禁追平 greedy 7.53 但破不了顶,因为 one_hot+Ridge 把真峰 8.42 排在门内
#2418(288 预算够不着)。本脚本回答一个可证伪的问题:换 ESM-2 表征 + 更强代理模型,
能否把真峰的门内预测排名拉进可达区(~budget)?这是决定实验二有没有破顶希望的地基,
在跑任何 LLM campaign 之前先算清(确定性、便宜)。

对每个 (feature, surrogate):用 cold-start(HD<=2)拟合、预测门内池(HD<=4 且平均
BLOSUM62>=0),输出真峰门内排名 + pool Spearman + 真峰是否进 top-budget。
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from evolution.datasets import load
from knowledge.validators import load_rules

ROOT = Path(__file__).resolve().parents[1]
_BL = load_rules()["blosum62"]


def _blosum(a: str, b: str) -> int:
    if a == b:
        return 4
    return _BL.get(a, {}).get(b, _BL.get(b, {}).get(a, 0))


def _gate_ok(seq: str, wt: str, max_hd: int = 4, blosum_min: float = 0.0) -> bool:
    subs = [(wt[i], c) for i, c in enumerate(seq) if i < len(wt) and c != wt[i]]
    if len(subs) > max_hd:
        return False
    if subs and float(np.mean([_blosum(w, c) for w, c in subs])) < blosum_min:
        return False
    return True


def _fit_predict(surrogate: str, Xtr, ytr, Xpool, standardize: bool):
    """Return predicted mean over Xpool for the named surrogate."""
    if standardize:
        mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-8
        Xtr = (Xtr - mu) / sd
        Xpool = (Xpool - mu) / sd
    if surrogate == "ridge":
        from sklearn.linear_model import Ridge
        m = Ridge(alpha=1.0).fit(Xtr, ytr)
        return m.predict(Xpool)
    if surrogate == "knn":
        from sklearn.neighbors import KNeighborsRegressor
        m = KNeighborsRegressor(n_neighbors=10, weights="distance").fit(Xtr, ytr)
        return m.predict(Xpool)
    if surrogate == "hgb":
        from sklearn.ensemble import HistGradientBoostingRegressor
        m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05,
                                          max_depth=6, random_state=0).fit(Xtr, ytr)
        return m.predict(Xpool)
    if surrogate == "mlp":
        from sklearn.neural_network import MLPRegressor
        m = MLPRegressor(hidden_layer_sizes=(256, 64), alpha=1e-3, max_iter=300,
                         random_state=0).fit(Xtr, ytr)
        return m.predict(Xpool)
    raise ValueError(surrogate)


def scan(features=("one_hot", "esm2"), surrogates=("ridge", "knn", "hgb"),
         budget: int = 288) -> dict:
    from scipy.stats import spearmanr
    rows = []
    for feat in features:
        spec = load("aav", feat)
        df, wt, fcol = spec.df, spec.wt, spec.fitness_col
        train = df[df.hd <= 2]
        pool = df[df.hd > 2].reset_index(drop=True)
        Xtr = spec.feature_fn(train.seq.tolist())
        ytr = train[fcol].to_numpy()
        Xpool = spec.feature_fn(pool.seq.tolist())
        ypool = pool[fcol].to_numpy()
        gmask = pool.seq.map(lambda s: _gate_ok(s, wt)).to_numpy()
        gidx = np.where(gmask)[0]
        peak_i = int(np.argmax(ypool))  # true peak position in pool
        peak_in_gate = bool(gmask[peak_i])
        std = (feat == "esm2")
        for sur in surrogates:
            t0 = time.time()
            try:
                mean = np.asarray(_fit_predict(sur, Xtr, ytr, Xpool, standardize=std))
            except Exception as exc:  # noqa: BLE001
                rows.append({"feature": feat, "surrogate": sur, "error": str(exc)[:120]})
                continue
            rank_all = int((mean > mean[peak_i]).sum()) + 1
            rank_gate = (int((mean[gidx] > mean[peak_i]).sum()) + 1) if peak_in_gate else None
            sp = float(spearmanr(mean, ypool).correlation)
            sp_gate = float(spearmanr(mean[gidx], ypool[gidx]).correlation)
            reachable = (rank_gate is not None and rank_gate <= budget)
            rows.append({
                "feature": feat, "surrogate": sur,
                "peak_rank_all": rank_all, "pool_size": int(len(pool)),
                "peak_rank_gate": rank_gate, "gate_size": int(len(gidx)),
                "reachable_in_budget": reachable, "budget": budget,
                "spearman_pool": round(sp, 3), "spearman_gate": round(sp_gate, 3),
                "fit_predict_sec": round(time.time() - t0, 1),
            })
            print(f"[{feat:7s} × {sur:5s}] 门内真峰 #{rank_gate}/{len(gidx)}  "
                  f"全池 #{rank_all}/{len(pool)}  Spearman(pool {sp:.3f}/gate {sp_gate:.3f})  "
                  f"{'★可达' if reachable else '不可达'}  ({time.time()-t0:.0f}s)")
    return {"dataset": "aav", "true_peak_fitness": 8.416, "gate": "HD<=4 & mean BLOSUM62>=0",
            "budget": budget, "rows": rows}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--features", nargs="+", default=["one_hot", "esm2"])
    p.add_argument("--surrogates", nargs="+", default=["ridge", "knn", "hgb"])
    p.add_argument("--budget", type=int, default=288)
    p.add_argument("--out", type=Path,
                   default=ROOT / "harness/reports/agentic-v0.3/aav/surrogate_scan.json")
    a = p.parse_args(argv)
    res = scan(tuple(a.features), tuple(a.surrogates), a.budget)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n")
    print(f"\n[out] {a.out}")
    return res


if __name__ == "__main__":
    main()
