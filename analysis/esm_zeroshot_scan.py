"""实验二·合法重测:ESM-2 zero-shot 突变效应打分(LM head,非 embedding+回归)。

题目点名蛋白质语言模型(ESM/ProtT5/SaProt)"理解序列规律"。此前我们只把 ESM 当
向量化器(embedding+Ridge/kNN),表现≈one_hot。本脚本测 ESM 的真·预测功能:
zero-shot 掩码边际打分(Meier et al. 2021, ESM-1v),answer-agnostic——只用预训练
模型 + 野生型序列,不看任何 fitness 标签、不看测试峰。

打分:对每个突变位点 i,score += log p(mut_i | context) - log p(wt_i | context),
context 用掩码边际(mask 位点 i 后模型对该位的分布)。两种上下文:
- fragment:仅 28-aa 突变区(AAV_WT)。
- full:全长 AAV2 VP1(P03135,735aa),突变区在 index 560-587——更符合 ESM 用法。

评估:门内(HD<=4 且平均BLOSUM62>=0)池真峰 8.416 的 zero-shot 排名 + Spearman。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from evolution.datasets import load, AAV_WT
from knowledge.validators import load_rules

ROOT = Path(__file__).resolve().parents[1]
_BL = load_rules()["blosum62"]
_AA = "ACDEFGHIKLMNPQRSTVWY"


def _blosum(a, b):
    return 4 if a == b else _BL.get(a, {}).get(b, _BL.get(b, {}).get(a, 0))


def _gate_ok(seq, wt, max_hd=4, blosum_min=0.0):
    sub = [(wt[i], c) for i, c in enumerate(seq) if c != wt[i]]
    if len(sub) > max_hd:
        return False
    if sub and float(np.mean([_blosum(w, c) for w, c in sub])) < blosum_min:
        return False
    return True


def masked_marginals(context_seq: str, window_off: int, window_len: int):
    """Return (window_len, 20-in-33-vocab) log-prob matrix at each window position,
    each computed by masking that position within the full context_seq."""
    import torch
    import esm
    model, alph = esm.pretrained.esm2_t33_650M_UR50D()
    model.eval()
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    model = model.to(dev)
    bc = alph.get_batch_converter()
    _, _, tok = bc([("ctx", context_seq)])
    tok = tok.to(dev)
    tok_idx = {c: alph.get_idx(c) for c in _AA}
    M = np.zeros((window_len, 33), dtype=np.float32)
    CH = 7
    with torch.no_grad():
        for s in range(0, window_len, CH):
            idxs = list(range(s, min(s + CH, window_len)))
            batch = tok.repeat(len(idxs), 1).clone()
            for r, i in enumerate(idxs):
                batch[r, window_off + i + 1] = alph.mask_idx
            lg = torch.log_softmax(model(batch)["logits"], dim=-1)
            for r, i in enumerate(idxs):
                M[i] = lg[r, window_off + i + 1].cpu().numpy()
    return M, tok_idx


def _eval(M, tok_idx, wt, budget):
    def z(seq):
        return float(sum(M[i, tok_idx[c]] - M[i, tok_idx[wt[i]]]
                         for i, c in enumerate(seq) if c != wt[i]))
    spec = load("aav", "one_hot")
    df, fcol = spec.df, spec.fitness_col
    pool = df[df.hd > 2].reset_index(drop=True)
    pool = pool.assign(z=pool.seq.map(z))
    pk = int(pool[fcol].idxmax())
    pz = pool.loc[pk, "z"]
    gp = pool[pool.seq.map(lambda s: _gate_ok(s, wt))].copy()
    rank_gate = int((gp["z"] > pz).sum()) + 1
    top = gp.nlargest(budget, "z")
    return {
        "peak_rank_gate": rank_gate, "gate_size": int(len(gp)),
        "peak_rank_all": int((pool["z"] > pz).sum()) + 1, "pool_size": int(len(pool)),
        "reachable_in_budget": rank_gate <= budget, "budget": budget,
        "spearman_pool": round(float(spearmanr(pool["z"], pool[fcol]).correlation), 3),
        "spearman_gate": round(float(spearmanr(gp["z"], gp[fcol]).correlation), 3),
        "peak_zscore": round(pz, 3),
        "gate_top_budget_max_fitness": round(float(top[fcol].max()), 3),
        "gate_top_budget_mean_fitness": round(float(top[fcol].mean()), 3),
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--budget", type=int, default=288)
    p.add_argument("--out", type=Path,
                   default=ROOT / "harness/reports/agentic-v0.3/aav/esm_zeroshot.json")
    a = p.parse_args(argv)
    wt = AAV_WT
    full = "".join(l.strip() for l in open(ROOT / "data/aav/P03135.fasta")
                   if not l.startswith(">"))
    off = full.find(wt)
    res = {"dataset": "aav", "method": "ESM-2 650M zero-shot masked-marginals",
           "true_peak_fitness": 8.416, "modes": {}}
    # fragment context
    Mf, tf = masked_marginals(wt, 0, len(wt))
    res["modes"]["fragment"] = _eval(Mf, tf, wt, a.budget)
    print("[fragment]", res["modes"]["fragment"])
    # full VP1 context
    Mc, tc = masked_marginals(full, off, len(wt))
    res["modes"]["full_context"] = _eval(Mc, tc, wt, a.budget)
    print("[full_context]", res["modes"]["full_context"])
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n")
    print(f"[out] {a.out}")
    return res


if __name__ == "__main__":
    main()
