"""ESM-2 650M mean-pooled embeddings with atomic, keyed NumPy disk caching."""
from __future__ import annotations

from collections.abc import Callable, Sequence
import hashlib
import json
from pathlib import Path
import tempfile

import numpy as np

from evolution.mutations import AMINO_ACIDS, variant_to_sequence

MODEL_NAME = "esm2_t33_650M_UR50D"
FEATURE_DIM = 1280
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE_DIR = ROOT / "features" / "cache"
Backend = Callable[[Sequence[str]], np.ndarray]


def _cache_key(variants: Sequence[str], model_name: str) -> str:
    payload = json.dumps({"model": model_name, "variants": list(variants)}, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()[:20]


class ESM2Embedder:
    """Extract 1280-d embeddings; tests and offline callers may inject a compatible backend."""

    feature_dim = FEATURE_DIM

    def __init__(self, cache_dir: Path = DEFAULT_CACHE_DIR, *, device: str | None = None,
                 batch_size: int = 64, backend: Backend | None = None) -> None:
        self.cache_dir = Path(cache_dir)
        self.device = device
        self.batch_size = batch_size
        self.backend = backend

    def transform(self, variants: Sequence[str], *, use_cache: bool = True) -> np.ndarray:
        normalized = tuple(str(variant).strip().upper() for variant in variants)
        key = _cache_key(normalized, MODEL_NAME)
        path = self.cache_dir / f"{MODEL_NAME}-{key}.npz"
        if use_cache and path.exists():
            with np.load(path, allow_pickle=False) as cached:
                if cached["variants"].tolist() == list(normalized):
                    return cached["embeddings"].astype(np.float32, copy=False)
        embeddings = self._extract(normalized)
        if embeddings.shape != (len(normalized), FEATURE_DIM):
            raise ValueError(f"ESM backend returned {embeddings.shape}; expected {(len(normalized), FEATURE_DIM)}")
        if use_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=self.cache_dir, suffix=".npz", delete=False) as handle:
                temporary = Path(handle.name)
            try:
                np.savez_compressed(temporary, variants=np.asarray(normalized), embeddings=embeddings.astype(np.float16))
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
        return embeddings.astype(np.float32, copy=False)

    def _extract(self, variants: Sequence[str]) -> np.ndarray:
        sequences = []
        for variant in variants:
            if any(aa not in AMINO_ACIDS for aa in variant):
                raise ValueError("sequence contains a non-standard or stop residue")
            sequences.append(variant_to_sequence(variant) if len(variant) == 4 else variant)
        if self.backend is not None:
            return np.asarray(self.backend(sequences), dtype=np.float32)
        return self._fair_esm_backend(sequences)

    def _fair_esm_backend(self, sequences: Sequence[str]) -> np.ndarray:
        import torch
        import esm

        device = self.device or ("mps" if torch.backends.mps.is_available() else "cpu")
        loader = getattr(esm.pretrained, MODEL_NAME)
        model, alphabet = loader()
        model = model.eval().to(device)
        converter = alphabet.get_batch_converter()
        chunks: list[np.ndarray] = []
        for start in range(0, len(sequences), self.batch_size):
            batch_sequences = sequences[start:start + self.batch_size]
            _, _, tokens = converter([(str(start + i), sequence) for i, sequence in enumerate(batch_sequences)])
            tokens = tokens.to(device)
            with torch.inference_mode():
                representations = model(tokens, repr_layers=[33], return_contacts=False)["representations"][33]
            pooled = [representations[i, 1:len(sequence) + 1].mean(0).float().cpu().numpy()
                      for i, sequence in enumerate(batch_sequences)]
            chunks.append(np.stack(pooled))
        return np.concatenate(chunks, axis=0) if chunks else np.empty((0, FEATURE_DIM), dtype=np.float32)
