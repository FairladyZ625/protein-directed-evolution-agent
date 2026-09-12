## Summary

Delivery commit ccbfce6c98a8b9f247b37aee456819c8f703878f implements C+A+B: robust sequence/tool boundaries, held-out `val_spearman` propagation through `surrogate_status`, and CV/round-aware `compose_batch` with exact staged testing. The formal same-protocol v0.5 campaign completed 288/288 measurements with no tool failure, but did not meet the fitness goal: `cum_top10_max=6.5309` versus v0.4 LLM 7.829 and deterministic greedy 8.4162. Per the task's challenge condition, the negative result and post-run mechanism diagnosis are delivered without oracle-informed retuning.

## Verification

`PYTHONPATH=. .venv/bin/python -m pytest tests/test_auto_researcher_gate.py tests/test_epistasis_surrogate.py tests/test_auto_researcher_compose.py -q` returned `14 passed in 2.96s`. `python -m py_compile agent/auto_researcher.py models/train_ladder.py` passed. The formal `gpt-5.6-sol` run reported `llm_used=True`, budget `288/288`, max `6.5309`, cumulative top-10 mean `6.1922`, strong `163`, and gate rejected `0`. `EventStore.verify()` returned `event_chain_verified=true events=25`; event inspection found 0 tool errors, 0 LLM round errors, and 0 no-test fallbacks. The shuffled-label negative control produced held-out Spearman `-0.119960`. Canonical fact: F-F7BC7554.

## Residual Risk

The adaptive formula degraded the primary extreme-fitness objective in the one required dataset/seed/model run, so it must not be presented as a successful optimizer. The post-run counterfactual is diagnostic only: pure-mean rank #45 carried fitness 7.391 and was displaced by the first 42/6 batch. CV is a single fixed 80/20 holdout and is not acquisition-regret calibration. The high-cohesion interface yielded 25 events rather than the requested 50+. The LLM summary conflates a cold-start incumbent with a newly discovered variant, though computed campaign metrics correctly use tested batches only. Finally, the dispatcher task lineage and fetched `origin/main` have no merge-base, so a safe pre-handoff rebase was impossible and was not attempted.

## Same Mechanism Elsewhere

Mechanism sentence: in fixed-budget discrete top-N acquisition, replacing even a small number of candidates near the score cutoff changes the first observed label set and can redirect every later refit. I searched with `rg -n 'predicted_mean|uncertainty|diverse|exploit|explore' agent evolution models tests harness/reports/agentic-v0.[1-5]`. The same mechanism appears in `agent/auto_researcher.py`'s legacy `list_pool` alternatives and is independently foreshadowed by the v0.1 and v0.4 reports' exploration-tax diagnoses; no second adaptive batch composer exists elsewhere in source.
