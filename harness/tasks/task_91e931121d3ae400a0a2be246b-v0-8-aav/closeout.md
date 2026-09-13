## Summary

Implemented AAV event-stream residual reflexion in commit `a157490141b41168e8aece6b0950978ba0419491`: every measured batch records nomination-time predicted mean/variance beside oracle fitness and residual; a read-only pure parser builds observed-only reflexion cards; an explicit treatment switch injects the prior round's card; a fixed `fitness < 0.2` motif-recurrence metric, timeout provenance, success counters, and a reproducible two-arm runner complete the experiment surface. The legacy `agent.tool.test` payload remains unchanged.

The seed-42 48x6 smoke hit checkpoint 3. Control and treatment nominated the same 288 variants and had identical motif-recurrence trajectories, final cumulative maximum 8.4162, and 157 strong hits. The treatment changed an intermediate redirect call but not measured behaviour, so no prompt tuning or multi-seed expansion was attempted.

## Verification

- Rebased onto `origin/main` `9db6b0d48af912ed4996a8fdf888413312073bff`; `git merge-base --is-ancestor origin/main HEAD` returned 0.
- Post-rebase task-scoped test command passed: `33 passed in 1.73s` for `tests/test_reflexion.py`, `tests/test_auto_researcher_backtrack.py`, `tests/test_auto_researcher_gate.py`, and `tests/test_auto_researcher_compose.py`.
- Reverse mutations made each new detector fail, then restoration returned `tests/test_reflexion.py` to `4 passed`: event selection, positive motif recurrence, negative motif recurrence, and nomination-time prediction capture were each exercised.
- Both smoke streams passed `EventStore.verify()`. Both arms used `LLM_TIMEOUT=240`; each completed 6/6 LLM calls with zero timeouts and zero round errors. Wall time was 221 s control and 268 s treatment.
- Raw streams, metrics, exact prompt injection, two hand-recomputed residuals, hashes, and test transcripts are attached under `artifacts/`; `smoke-1seed.md` was submitted with `ha doc sync --submit --task task_91e931121d3ae400a0a2be246b`.
- Existing `harness/reports/` remained unchanged (`git diff --quiet -- harness/reports/` returned 0).
- Promoted facts: `F-CCC91916` records the unchanged behaviour result; `F-B22B7F95` records the nomination-time prediction invariant and reverse-test evidence.
- Independent review is not performed by this worker and remains pending.

## Residual Risk

The behavioural conclusion is one AAV seed and one stochastic LLM run per arm, not an estimate of a population effect. It is nevertheless the task's pre-registered stop result because every measured nomination and every motif-recurrence value was identical. The parser's `underestimated_hits` ranks positive residuals without an unobserved full-pool threshold, preserving the no-leak boundary but using “hit” as a relative underestimation label rather than a global-top classification. The shared standard-task CI witness remains structurally unavailable per `F-8ED77039`; no CI or workflow configuration was changed.

## Same Mechanism Elsewhere

Mechanism sentence: when labels mutate a model's training state, audit records that compare a decision with its outcome must snapshot the model output before that mutation and retraining.

Search: `rg -n "nomination-time|prediction_timing|test\\.residuals|pred_cache = None|measured.*concat|residual" agent evolution events tests scripts -g '*.py' -g '*.sh'`, followed by inspection of `evolution/pool_campaign.py:120-185` and a second search for `predicted_mean|pre-test|pre_test|nomination`.

Finding: `evolution/pool_campaign.py` also ranks candidates and then appends labels/drops pool rows, but it does not currently emit prediction residuals, so the mechanism would apply if that workflow later adds residual audit records. No change was made because this task explicitly excludes the GB1/workflow line. Existing epistasis residuals in `tests/test_mutation_order.py` are static landscape diagnostics, not online prediction snapshots.
