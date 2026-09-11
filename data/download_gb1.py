"""Validate the local GB1 landscape and record its provenance; never fabricates data."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evolution.random_baseline import EXPECTED_ROWS, WT, load_landscape

DEFAULT_DATA = ROOT / "data" / "four_mutations_full_data.csv"
DEFAULT_MANIFEST = ROOT / "data" / "gb1_manifest.json"
SOURCE_URL = "https://doi.org/10.7554/eLife.16965.024"


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_local_gb1(path: Path = DEFAULT_DATA) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(
            f"GB1 data not found at {path}. Place the FLIP/Wu 2016 four_mutations_full_data.csv there; "
            "automatic external download is intentionally disabled."
        )
    landscape = load_landscape(path)
    header = pd.read_csv(path, nrows=0).columns.tolist()
    if "sequence" not in header:
        raise ValueError("data contract missing required sequence column")
    return {
        "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": len(landscape),
        "unique_variants": int(landscape["Variants"].nunique()),
        "wt_variant": WT,
        "wt_fitness": float(landscape.loc[landscape["Variants"] == WT, "Fitness"].iloc[0]),
        "expected_rows": EXPECTED_ROWS,
        "source": SOURCE_URL,
        "source_note": "Wu et al. 2016 supplement, packaged with FLIP-derived sequence/split columns",
    }


def write_manifest(path: Path = DEFAULT_DATA, output: Path = DEFAULT_MANIFEST) -> dict[str, object]:
    manifest = validate_local_gb1(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    print(json.dumps(write_manifest(args.path, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
