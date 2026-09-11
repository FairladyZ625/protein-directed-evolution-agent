"""Build committed one-hot and optional ESM caches from generated GB1 pools."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from features.esm2 import ESM2Embedder
from features.one_hot import encode_one_hot
from features.pools import DEFAULT_DIR, load_three_pools

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "features" / "cache"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--esm-pool", choices=("none", "train_pool", "query_pool", "holdout"), default="none")
    parser.add_argument("--device", choices=("cpu", "mps"), default=None)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--pool-dir", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args()
    pools = load_three_pools(args.pool_dir)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    all_variants = np.asarray(
        np.concatenate([pools.train_pool.Variants, pools.query_pool.Variants, pools.holdout.Variants]),
        dtype="U4",
    )
    one_hot_path = CACHE_DIR / "gb1-all-one-hot.npz"
    np.savez_compressed(one_hot_path, variants=all_variants, embeddings=encode_one_hot(all_variants))
    print(f"one-hot {len(all_variants)}x80 -> {one_hot_path} ({one_hot_path.stat().st_size} bytes)")
    if args.esm_pool != "none":
        variants = getattr(pools, args.esm_pool).Variants.tolist()
        embeddings = ESM2Embedder(device=args.device, batch_size=args.batch_size).transform(variants)
        print(f"ESM-2 {embeddings.shape} cached under {CACHE_DIR}")


if __name__ == "__main__":
    main()
