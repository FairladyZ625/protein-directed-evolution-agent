#!/usr/bin/env bash
# Reproduce the delivery spine, preferring a useful offline demonstration on clean clones.
set -euo pipefail

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$repo_root"

if [ ! -x .venv/bin/python ]; then
  printf '%s\n' "Missing .venv/bin/python. Run ./scripts/install.sh first." >&2
  exit 1
fi

venv_python="$(pwd)/.venv/bin/python"
run_make() {
  PYTHON="$venv_python" PATH="$(dirname "$venv_python"):$PATH" make "$@"
}

printf '%s\n' '[run-all] 1/3 smoke: synthetic, offline; outputs go to tmp/smoke/'
run_make smoke

if [ ! -f data/four_mutations_full_data.csv ]; then
  printf '%s\n' '[run-all] GB1 CSV is absent: completed the self-contained smoke path only.'
  printf '%s\n' '[run-all] For predictor and four-strategy GB1 results, place data/four_mutations_full_data.csv as described in data/README.md, then rerun.'
  exit 0
fi

printf '%s\n' '[run-all] 2/3 predictor: measured GB1; outputs go to harness/reports/workflow-v1.0/gb1/'
"$venv_python" -m models.train_ladder --feature one_hot

printf '%s\n' '[run-all] 3/3 campaign: four strategies on measured GB1; outputs go to harness/reports/workflow-v1.1/gb1/'
"$venv_python" -m evolution.campaign --cold-start low_hd

printf '%s\n' '[run-all] complete: smoke, predictor, and four-strategy campaign finished.'
