#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
out_root="${1:-$repo_root/tmp/v08-smoke-seed42}"
model="${V08_MODEL:-gpt-5.6-sol}"
mkdir -p "$out_root"

common=(
  --dataset aav
  --feature one_hot
  --guardrail
  --surrogate epistasis
  --budget 48
  --n-rounds 6
  --seed 42
  --model "$model"
  --backtrack semi
  --skip-experiment-log
)

cd "$repo_root"
for arm in control reflexion; do
  start_seconds=$SECONDS
  if [[ "$arm" == "reflexion" ]]; then
    LLM_TIMEOUT=240 PYTHONPATH=. .venv/bin/python -m agent.auto_researcher \
      "${common[@]}" --reflexion --out-dir "$out_root/$arm" \
      2>&1 | tee "$out_root/$arm.stdout.log"
  else
    LLM_TIMEOUT=240 PYTHONPATH=. .venv/bin/python -m agent.auto_researcher \
      "${common[@]}" --out-dir "$out_root/$arm" \
      2>&1 | tee "$out_root/$arm.stdout.log"
  fi
  elapsed_seconds=$((SECONDS - start_seconds))
  printf '%s\n' "$elapsed_seconds" > "$out_root/$arm.wall-seconds.txt"
done
