"""Dataset registry for the pool-based campaign: each loader returns a DatasetSpec.

Adding a harder landscape = adding one loader here. Raw data files are gitignored
(large); see each loader's docstring for the source and download.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from evolution.pool_campaign import DatasetSpec

ROOT = Path(__file__).resolve().parents[1]
AA = "ACDEFGHIKLMNPQRSTVWY"
_LUT = {c: i for i, c in enumerate(AA)}


def one_hot_encoder(length: int):
    """Length-agnostic one-hot: fixed-length substitution strings -> (N, length*20)."""
    def enc(seqs: list[str]) -> np.ndarray:
        x = np.zeros((len(seqs), length * 20), dtype=float)
        for r, s in enumerate(seqs):
            for p, c in enumerate(s):
                j = _LUT.get(c)
                if j is not None:
                    x[r, p * 20 + j] = 1.0
        return x
    return enc


def esm_encoder(name: str, seqs_all: list[str]):
    """Cached ESM-2 embedder over the mutated-region strings (see features/esm2.py).

    Embeddings are computed once for every sequence in the dataset and cached to
    lab/reports/cache/esm_<name>.npz, then looked up per call.
    """
    from evolution.results_layout import CACHE
    cache = CACHE / f"esm_{name}.npz"
    cache.parent.mkdir(parents=True, exist_ok=True)
    table: dict[str, np.ndarray] = {}
    if cache.exists():
        z = np.load(cache, allow_pickle=True)
        table = {s: v for s, v in zip(z["seqs"], z["emb"])}
    missing = [s for s in dict.fromkeys(seqs_all) if s not in table]
    if missing:
        from features.esm2 import ESM2Embedder
        emb = ESM2Embedder().transform(missing)
        for s, v in zip(missing, emb):
            table[s] = np.asarray(v, dtype=np.float32)
        alls = list(table)
        np.savez_compressed(cache, seqs=np.array(alls, dtype=object),
                            emb=np.stack([table[s] for s in alls]))

    def enc(seqs: list[str]) -> np.ndarray:
        return np.stack([table[s] for s in seqs])
    return enc


# ---------------------------------------------------------------- AAV (FLIP) ---
AAV_WT = "DEEEIRTTNPVATEQYGSVSTNLQRGNR"  # VP1 window 561-588 (P03135)
AAV_CSV = ROOT / "data" / "aav" / "full_data.csv"


def load_aav(feature: str = "one_hot") -> DatasetSpec:
    """FLIP AAV capsid (Bryant et al. 2021). Source: J-SNACKKB/FLIP splits/aav/full_data.csv.zip.

    Clean substitution subset only (28-aa mutated region, no indel/stop/designed);
    fitness = `score`; hd = `number_of_mutations`.
    """
    if not AAV_CSV.exists():
        raise FileNotFoundError(f"missing {AAV_CSV}; download FLIP splits/aav/full_data.csv.zip and unzip")
    raw = pd.read_csv(AAV_CSV, low_memory=False)
    mr = raw["mutated_region"].astype(str)
    clean = mr.str.len().eq(len(AAV_WT)) & mr.str.match(r"^[A-Z]+$") & ~mr.str.contains(r"\*")
    df = raw[clean][["mutated_region", "score", "number_of_mutations"]].copy()
    df = df.rename(columns={"mutated_region": "seq", "score": "fitness", "number_of_mutations": "hd"})
    df = df.drop_duplicates("seq").reset_index(drop=True)
    feat = (one_hot_encoder(len(AAV_WT)) if feature == "one_hot"
            else esm_encoder("aav", df.seq.tolist()))
    return DatasetSpec(name=f"aav[{feature}]", df=df, wt=AAV_WT, feature_fn=feat)


# -------------------------------------------------------- avGFP (ProteinGym) ---
AVGFP_CSV = ROOT / "data" / "avgfp" / "avgfp.csv"


def load_avgfp(feature: str = "esm2") -> DatasetSpec:
    """avGFP (Sarkisyan 2016), via ProteinGym DMS. Expects a csv with a mutated
    sequence column and a fitness column (normalised by the loader). 238-aa, variable
    substitution count — ESM-2 recommended."""
    if not AVGFP_CSV.exists():
        raise FileNotFoundError(f"missing {AVGFP_CSV}; place the ProteinGym avGFP DMS csv here")
    raw = pd.read_csv(AVGFP_CSV)
    seq_col = next(c for c in ("mutated_sequence", "sequence", "seq") if c in raw.columns)
    fit_col = next(c for c in ("DMS_score", "fitness", "score", "target") if c in raw.columns)
    raw[seq_col] = raw[seq_col].astype(str).str.upper()
    mutant_col = next((c for c in ("mutant", "mutation", "mutations") if c in raw.columns), None)
    wt_rows = raw[mutant_col].astype(str).str.upper().isin(("WT", "WILD_TYPE", "WILDTYPE")) if mutant_col else None
    if wt_rows is None or not wt_rows.any():
        raise ValueError("avGFP CSV must contain an explicit WT row in mutant/mutation/mutations")
    wt_values = raw.loc[wt_rows, seq_col].drop_duplicates()
    if len(wt_values) != 1:
        raise ValueError("avGFP CSV contains inconsistent WT sequences")
    wt = wt_values.iloc[0]
    df = raw[[seq_col, fit_col]].rename(columns={seq_col: "seq", fit_col: "fitness"})
    valid = df.seq.str.len().eq(len(wt)) & df.seq.str.match(r"^[ACDEFGHIKLMNPQRSTVWY]+$")
    df = df.loc[valid].copy()
    df["fitness"] = pd.to_numeric(df["fitness"], errors="coerce")
    df = df.dropna(subset=["fitness"])
    df["hd"] = [sum(a != b for a, b in zip(s, wt)) for s in df.seq]
    df = df.drop_duplicates("seq").reset_index(drop=True)
    feat = (one_hot_encoder(len(wt)) if feature == "one_hot" else esm_encoder("avgfp", df.seq.tolist()))
    return DatasetSpec(name=f"avgfp[{feature}]", df=df, wt=wt, feature_fn=feat)


REGISTRY = {"aav": load_aav, "avgfp": load_avgfp}


def load(dataset: str, feature: str) -> DatasetSpec:
    return REGISTRY[dataset](feature=feature)
