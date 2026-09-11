"""Deterministic 4 x 20 one-hot features for the GB1 combinatorial sites."""
from __future__ import annotations

from collections.abc import Iterable

import numpy as np

from evolution.mutations import AMINO_ACIDS, validate_variant

FEATURE_DIM = 80
AA_TO_INDEX = {aa: index for index, aa in enumerate(AMINO_ACIDS)}


def encode_one_hot(variants: Iterable[str], *, dtype: np.dtype = np.uint8) -> np.ndarray:
    normalized = [validate_variant(variant) for variant in variants]
    output = np.zeros((len(normalized), FEATURE_DIM), dtype=dtype)
    for row, variant in enumerate(normalized):
        for site, aa in enumerate(variant):
            output[row, site * len(AMINO_ACIDS) + AA_TO_INDEX[aa]] = 1
    return output


class OneHotEncoder:
    feature_dim = FEATURE_DIM

    def fit(self, variants: Iterable[str]) -> "OneHotEncoder":
        list(variants)
        return self

    def transform(self, variants: Iterable[str]) -> np.ndarray:
        return encode_one_hot(variants)

    def fit_transform(self, variants: Iterable[str]) -> np.ndarray:
        return self.transform(variants)
