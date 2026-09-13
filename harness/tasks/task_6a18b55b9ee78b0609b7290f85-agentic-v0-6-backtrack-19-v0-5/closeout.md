## Summary

Merged the agentic v0.6 backtrack capability onto current `origin/main` while preserving the v0.5 default prompt and adaptive acquisition. The merge retains mainline timeout, tool-lock, knowledge-graph, and no-knowledge behavior; adds the full/semi backtrack mode, trajectory state, redirect tool, CLI/output routing, and a byte-level v0.5 prompt regression test. Local commit: `80c9bce79b7b34388af93b9a7ce3725b16a00ebf`.

## Verification

- Assigned packet after rebase: `58 passed, 1 warning in 6.24s`.
- Pre/post default `SYSTEM_PROMPT` diff: empty; SHA-256 `191ae4c066f2441a455cbedd127e518f18778bb49c5477e1609add028bed0409`.
- Reverse control: switching the default paragraph to v0.6 made the byte-identity test fail with exit 1; restoring v0.5 made the packet pass.
- `scripts/check_data_has_code.py`: `agentic-v0.6` ✅.
- `scripts/check_references.py`: `harness/reports/agentic-v0.6/report.md` ✅.
- `origin/main` is an ancestor of HEAD; final diff against it contains only `agent/auto_researcher.py` and `tests/test_auto_researcher_backtrack.py`.
- Promoted fact: `F-E34909AE`.

## Residual Risk

The commercial-LLM AAV seed-42 campaign was intentionally not rerun, so existing experiment outputs were not regenerated. Whole-repository audits still report one unrelated code/data lineage gap (`pkgA-mainline-truth`) and seven unrelated stale references; these are outside this task's execution surface.

## Same Mechanism Elsewhere

Mechanism: versioned experimental data can enter the mainline without the exact feature code that produced it. Search: ran `python3 scripts/check_data_has_code.py`, which checks referenced code paths and commit ancestry across report versions. Finding: agentic-v0.6 is now clean, while the same mechanism remains visible in the unrelated `pkgA-mainline-truth` report as unmerged commit `1bcf2e9b05f594f6323e83bd3e02d057a58ea298`.
