"""ESM-2 masked-token entropy analysis for GB1 and AAV.

This module is deliberately analysis-only.  Its outputs must not be used to
filter candidates, select training observations, or drive an acquisition rule.
"""
from __future__ import annotations

import argparse
from collections.abc import Callable
import hashlib
import json
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from evolution.datasets import AAV_WT
from evolution.mutations import AMINO_ACIDS, GB1_WT_SEQUENCE, MUTABLE_POSITIONS
from features.esm2 import DEFAULT_CACHE_DIR, MODEL_NAME

ROOT = Path(__file__).resolve().parents[1]
ProbabilityBackend = Callable[[str], np.ndarray]


def shannon_entropy(probabilities: np.ndarray) -> np.ndarray:
    """Return Shannon entropy (nats) along the last axis.

    Rows must be finite, non-negative probability distributions.  Zero-mass
    entries contribute zero, as required by the limiting definition.
    """
    p = np.asarray(probabilities, dtype=np.float64)
    if p.ndim == 0 or p.shape[-1] == 0:
        raise ValueError("probabilities must have a non-empty amino-acid axis")
    if not np.all(np.isfinite(p)) or np.any(p < 0):
        raise ValueError("probabilities must be finite and non-negative")
    if not np.allclose(p.sum(axis=-1), 1.0, atol=1e-6):
        raise ValueError("probabilities must sum to one")
    terms = np.zeros_like(p)
    np.log(p, out=terms, where=p > 0)
    return -np.sum(p * terms, axis=-1)


def conservation_ranks(entropy: np.ndarray) -> np.ndarray:
    """Rank positions from most conserved (lowest entropy), starting at one."""
    values = np.asarray(entropy, dtype=float)
    order = np.argsort(values, kind="stable")
    ranks = np.empty(len(values), dtype=int)
    ranks[order] = np.arange(1, len(values) + 1)
    return ranks


class ESM2ConservationAnalyzer:
    """Compute and cache per-position masked ESM-2 amino-acid probabilities."""

    def __init__(self, cache_dir: Path = DEFAULT_CACHE_DIR, *, device: str | None = None,
                 batch_size: int = 8, backend: ProbabilityBackend | None = None) -> None:
        self.cache_dir = Path(cache_dir)
        self.device = device
        self.batch_size = batch_size
        self.backend = backend

    def probabilities(self, sequence: str, *, use_cache: bool = True) -> np.ndarray:
        sequence = sequence.strip().upper()
        if not sequence or any(aa not in AMINO_ACIDS for aa in sequence):
            raise ValueError("sequence must contain only standard amino acids")
        payload = json.dumps(
            {"model": MODEL_NAME, "sequence": sequence, "kind": "masked-token-probabilities-v1"},
            separators=(",", ":"),
        )
        key = hashlib.sha256(payload.encode()).hexdigest()[:20]
        path = self.cache_dir / f"{MODEL_NAME}-conservation-{key}.npz"
        if use_cache and path.exists():
            with np.load(path, allow_pickle=False) as cached:
                if str(cached["sequence"].item()) == sequence:
                    return cached["probabilities"].astype(np.float64)
        backend = self.backend or self._fair_esm_backend
        probabilities = np.asarray(backend(sequence), dtype=np.float64)
        expected = (len(sequence), len(AMINO_ACIDS))
        if probabilities.shape != expected:
            raise ValueError(f"ESM backend returned {probabilities.shape}; expected {expected}")
        # Validation here also prevents corrupt values entering the persistent cache.
        shannon_entropy(probabilities)
        if use_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=self.cache_dir, suffix=".npz", delete=False) as handle:
                temporary = Path(handle.name)
            try:
                np.savez_compressed(temporary, sequence=np.asarray(sequence),
                                    amino_acids=np.asarray(list(AMINO_ACIDS)),
                                    probabilities=probabilities.astype(np.float32))
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
        return probabilities

    def _fair_esm_backend(self, sequence: str) -> np.ndarray:
        try:
            import esm
            import torch
        except ImportError as exc:
            raise RuntimeError("fair-esm and torch are required; no conservation fallback is allowed") from exc

        device = self.device or ("mps" if torch.backends.mps.is_available() else "cpu")
        loader = getattr(esm.pretrained, MODEL_NAME)
        model, alphabet = loader()
        model = model.eval().to(device)
        converter = alphabet.get_batch_converter()
        aa_indices = torch.tensor([alphabet.get_idx(aa) for aa in AMINO_ACIDS], device=device)
        rows: list[np.ndarray] = []
        for start in range(0, len(sequence), self.batch_size):
            positions = range(start, min(start + self.batch_size, len(sequence)))
            batch = []
            for position in positions:
                masked = list(sequence)
                masked[position] = "<mask>"
                batch.append((str(position), "".join(masked)))
            _, _, tokens = converter(batch)
            tokens = tokens.to(device)
            with torch.inference_mode():
                logits = model(tokens, repr_layers=[], return_contacts=False)["logits"]
                for row, position in enumerate(positions):
                    aa_logits = logits[row, position + 1].index_select(0, aa_indices)
                    rows.append(torch.softmax(aa_logits, dim=-1).float().cpu().numpy())
        return np.stack(rows)


def _experimental_effects(sequences: pd.Series, fitness: pd.Series, wt: str,
                          measured_positions: set[int] | None = None) -> list[dict[str, object]]:
    wt_rows = fitness[sequences.eq(wt)]
    if wt_rows.empty:
        raise ValueError("dataset has no wild-type observation")
    wt_fitness = float(wt_rows.iloc[0])
    effects: list[dict[str, object]] = []
    for position in range(len(wt)):
        measured = measured_positions is None or position in measured_positions
        mask = sequences.str[position].ne(wt[position]) if measured else pd.Series(False, index=sequences.index)
        values = fitness[mask]
        effects.append({
            "position": position + 1,
            "n_mutated_observations": int(mask.sum()),
            "beneficial_fraction": float((values > wt_fitness).mean()) if len(values) else None,
            "max_fitness_gain": float(values.max() - wt_fitness) if len(values) else None,
            "effect_measured": bool(measured and len(values)),
        })
    return effects


def _load_gb1(path: Path) -> tuple[pd.Series, pd.Series, list[dict[str, object]]]:
    frame = pd.read_csv(path, usecols=["Variants", "Fitness"])
    variants = frame["Variants"].astype(str)
    # Reconstruct only the four assayed residues into the canonical 56-aa domain.
    chars = np.tile(np.asarray(list(GB1_WT_SEQUENCE)), (len(frame), 1))
    for column, position in enumerate(MUTABLE_POSITIONS):
        chars[:, position - 1] = variants.str[column].to_numpy()
    sequences = pd.Series(["".join(row) for row in chars])
    fitness = pd.to_numeric(frame["Fitness"])
    effects = _experimental_effects(sequences, fitness, GB1_WT_SEQUENCE,
                                    {position - 1 for position in MUTABLE_POSITIONS})
    return sequences, fitness, effects


def _load_aav(path: Path) -> tuple[pd.Series, pd.Series, list[dict[str, object]]]:
    frame = pd.read_csv(path, usecols=["mutated_region", "score"], low_memory=False)
    sequences = frame["mutated_region"].astype(str)
    clean = sequences.str.len().eq(len(AAV_WT)) & sequences.str.match(r"^[ACDEFGHIKLMNPQRSTVWY]+$")
    frame = frame.loc[clean].drop_duplicates("mutated_region")
    sequences = frame["mutated_region"].astype(str).reset_index(drop=True)
    fitness = pd.to_numeric(frame["score"]).reset_index(drop=True)
    return sequences, fitness, _experimental_effects(sequences, fitness, AAV_WT)


def analyze(dataset: str, data_path: Path, analyzer: ESM2ConservationAnalyzer) -> dict[str, object]:
    wt = GB1_WT_SEQUENCE if dataset == "gb1" else AAV_WT
    _, _, effects = _load_gb1(data_path) if dataset == "gb1" else _load_aav(data_path)
    entropy = shannon_entropy(analyzer.probabilities(wt))
    ranks = conservation_ranks(entropy)
    rows = []
    for position, (aa, value, rank, effect) in enumerate(zip(wt, entropy, ranks, effects), start=1):
        rows.append({"position": position, "wild_type": aa, "entropy_nats": float(value),
                     "conservation_rank": int(rank), **{k: v for k, v in effect.items() if k != "position"}})
    measured = [row for row in rows if row["effect_measured"]]
    correlations = {}
    for metric in ("beneficial_fraction", "max_fitness_gain"):
        result = spearmanr([row["conservation_rank"] for row in measured],
                           [row[metric] for row in measured])
        correlations[f"spearman_rank_vs_{metric}"] = float(result.statistic)
        correlations[f"spearman_rank_vs_{metric}_pvalue"] = float(result.pvalue)
    peak_positions = [1, 18, 19] if dataset == "aav" else []
    return {
        "dataset": dataset,
        "model": MODEL_NAME,
        "entropy_definition": "Shannon entropy in nats over 20 standard amino acids from masked-token probabilities",
        "effect_definition": "all observed variants differing from WT at the position; multi-mutant effects are descriptive and confounded",
        "wild_type_sequence": wt,
        "positions": rows,
        "correlations": correlations,
        "true_peak_positions": [
            {"position": pos, "wild_type": wt[pos - 1], "conservation_rank": int(ranks[pos - 1]),
             "entropy_nats": float(entropy[pos - 1])} for pos in peak_positions
        ],
    }


def _plot(result: dict[str, object], path: Path) -> None:
    import matplotlib.pyplot as plt

    rows = result["positions"]
    positions = [row["position"] for row in rows]
    entropy = [row["entropy_nats"] for row in rows]
    benefit = [np.nan if row["beneficial_fraction"] is None else row["beneficial_fraction"] for row in rows]
    gain = [np.nan if row["max_fitness_gain"] is None else row["max_fitness_gain"] for row in rows]
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    axes[0].bar(positions, entropy, color="#4472C4"); axes[0].set_ylabel("Entropy (nats)")
    axes[1].scatter(positions, benefit, color="#70AD47"); axes[1].set_ylabel("Beneficial fraction")
    axes[2].scatter(positions, gain, color="#ED7D31"); axes[2].set_ylabel("Max fitness gain")
    axes[2].set_xlabel("Sequence position (1-based)")
    fig.suptitle(f"{str(result['dataset']).upper()} ESM-2 conservation and measured effects")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("gb1", "aav"), required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "mps"), default=None)
    args = parser.parse_args()
    result = analyze(args.dataset, args.data, ESM2ConservationAnalyzer(device=args.device))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "conservation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    _plot(result, args.output_dir / "figures" / "conservation.png")


if __name__ == "__main__":
    main()
