# Delivery verification

## Executed

- `bash -n scripts/install.sh scripts/run_all.sh` exited 0.
- `PYTHON="$(pwd)/.venv/bin/python" PATH="$(pwd)/.venv/bin:$PATH" make smoke` wrote synthetic metrics, plot, event JSONL, SQLite projection (116 events), and README under `tmp/smoke/`.
- `pytest -q tests/test_predictor.py tests/test_campaign.py` returned `15 passed, 1 warning in 24.14s`.
- With the GB1 CSV symlink temporarily renamed in this worktree, `./scripts/run_all.sh` completed smoke and printed the explicit absent-data downgrade; the symlink was restored.
- `EventStore('lab/reports/experiment_log.jsonl').verify()` passed after nine append-only backfill records (24 records total).

Independent manifest check:

```bash
python3 - <<'PY'
import hashlib, json
from pathlib import Path
for manifest in Path('lab/reports').glob('*/manifest.json'):
    if manifest.parent.name not in {'analysis-v0.1', 'workflow-v1.1', 'final-report-v0.3', 'knowledge-ablation', 'pkgA-mainline-truth', 'pkgB-eval-protocol', 'pool-campaign-aav-agentic'}:
        continue
    for relative, expected in json.loads(manifest.read_text()).get('artifacts', {}).items():
        assert hashlib.sha256((manifest.parent / relative).read_bytes()).hexdigest() == expected
print('new manifest hashes verified')
PY
```

## Not verified

- The clean `/tmp` venv install began but the runner's 30-second command ceiling interrupted dependency downloading; it is not claimed as a successful clean-install verification.
- Linux execution and the `--full` PyTorch/fair-esm tier were not run on this macOS host.
- The data-present predictor/campaign branch was not run, to avoid overwriting CEO-owned `workflow-v1.1` campaign outputs.
