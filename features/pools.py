"""Reproducible GB1 pools and the model-selection evaluation protocol.

The committed 5,000/50,000/94,361 pools remain the stable outer split.  Model
selection subdivides the 5,000-row historical pool into fit and validation
roles; query-test is available for iterative diagnostics, while holdout stays
untouched until the final evaluation.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from evolution.random_baseline import EXPECTED_ROWS, WT, build_cold_start_pool, load_landscape

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "data" / "pools"
TRAIN_SIZE = 5_000
QUERY_SIZE = 50_000
SEED = 42
VALIDATION_SIZE = 1_000
VALIDATION_SEED = 42


@dataclass(frozen=True)
class PoolSplit:
    train_pool: pd.DataFrame
    query_pool: pd.DataFrame
    holdout: pd.DataFrame

    def sizes(self) -> dict[str, int]:
        return {"train_pool": len(self.train_pool), "query_pool": len(self.query_pool), "holdout": len(self.holdout)}


@dataclass(frozen=True)
class EvaluationProtocol:
    """Four explicit roles layered over the stable three-pool split."""

    train: pd.DataFrame
    validation: pd.DataFrame
    query_test: pd.DataFrame
    holdout: pd.DataFrame

    def sizes(self) -> dict[str, int]:
        return {name: len(getattr(self, name)) for name in ("train", "validation", "query_test", "holdout")}


def split_train_validation(
    frame: pd.DataFrame,
    *,
    validation_size: int,
    seed: int = VALIDATION_SEED,
    keep_variants: tuple[str, ...] = (WT,),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a historical frame without letting required controls enter validation."""
    if validation_size <= 0 or validation_size >= len(frame):
        raise ValueError("validation_size must leave non-empty train and validation sets")
    required = set(keep_variants)
    missing = required - set(frame["Variants"])
    if missing:
        raise ValueError(f"required train variants missing: {sorted(missing)}")
    eligible = np.flatnonzero(~frame["Variants"].isin(required).to_numpy())
    if validation_size > len(eligible):
        raise ValueError("validation_size leaves no room for required train variants")
    rng = np.random.default_rng(seed)
    validation_indices = np.sort(rng.choice(eligible, size=validation_size, replace=False))
    is_validation = np.zeros(len(frame), dtype=bool)
    is_validation[validation_indices] = True
    train = frame.iloc[np.flatnonzero(~is_validation)].reset_index(drop=True)
    validation = frame.iloc[validation_indices].reset_index(drop=True)
    return train, validation


def build_evaluation_protocol(
    split: PoolSplit,
    *,
    validation_size: int = VALIDATION_SIZE,
    seed: int = VALIDATION_SEED,
) -> EvaluationProtocol:
    """Assign train/validation/query-test/holdout roles without changing outer pools."""
    train, validation = split_train_validation(
        split.train_pool, validation_size=validation_size, seed=seed
    )
    return EvaluationProtocol(
        train=train,
        validation=validation,
        query_test=split.query_pool.copy(),
        holdout=split.holdout.copy(),
    )


def build_hd_extrapolation_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return the leakage-resistant GB1 extrapolation split (HD <=2 / >=3).

    This deliberately does not sample: every validated landscape row belongs to
    exactly one side, making results reproducible and directly comparable.
    """
    required = {"Variants", "HD", "Fitness"}
    if not required.issubset(df.columns) or len(df) != EXPECTED_ROWS:
        raise ValueError("HD split requires the validated 149,361-variant landscape")
    train = df.loc[df["HD"] <= 2, ["Variants", "HD", "Fitness"]].reset_index(drop=True)
    test = df.loc[df["HD"] >= 3, ["Variants", "HD", "Fitness"]].reset_index(drop=True)
    if train.empty or test.empty:
        raise ValueError("HD split produced an empty partition")
    return train, test


def build_three_pools(df: pd.DataFrame, *, seed: int = SEED, train_size: int = TRAIN_SIZE,
                      query_size: int = QUERY_SIZE) -> PoolSplit:
    if len(df) != EXPECTED_ROWS or not df["Variants"].is_unique:
        raise ValueError("three-pool split requires the validated 149,361-variant landscape")
    if train_size + query_size >= len(df):
        raise ValueError("train_size + query_size must leave a non-empty holdout")
    rng = np.random.default_rng(seed)
    train = build_cold_start_pool(df, rng, size=train_size)
    if WT not in set(train["Variants"]):
        raise AssertionError("WT must be present in train_pool")
    remaining = df.loc[~df["Variants"].isin(train["Variants"])].reset_index(drop=True)
    query_indices = np.sort(rng.choice(len(remaining), size=query_size, replace=False))
    query = remaining.iloc[query_indices].reset_index(drop=True)
    holdout = remaining.drop(index=query_indices).reset_index(drop=True)
    columns = ["Variants", "HD", "Fitness"]
    return PoolSplit(train[columns], query[columns], holdout[columns])


def write_three_pools(split: PoolSplit, directory: Path = DEFAULT_DIR) -> dict[str, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, frame in (("train_pool", split.train_pool), ("query_pool", split.query_pool), ("holdout", split.holdout)):
        path = directory / f"{name}.csv"
        frame.to_csv(path, index=False)
        paths[name] = path
    return paths


def load_three_pools(directory: Path = DEFAULT_DIR) -> PoolSplit:
    frames = {name: pd.read_csv(directory / f"{name}.csv") for name in ("train_pool", "query_pool", "holdout")}
    return PoolSplit(**frames)


def main() -> None:
    split = build_three_pools(load_landscape(), seed=SEED)
    paths = write_three_pools(split)
    print({**split.sizes(), "paths": {name: str(path) for name, path in paths.items()}})


if __name__ == "__main__":
    main()
