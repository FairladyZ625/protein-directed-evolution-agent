# Execution exe_008dbb396ccd9bcc361b29eb5d

Managed by `ha task start/submit`; hand edits are rejected.

- Task: task_411e6a2e4c4a10cbac0891c43c
- Iteration: 0
- State: accepted
- Claimed: 2026-09-12T05:49:17.981Z
- Submitted: 2026-09-12T05:59:35.596Z
- Closed: 2026-09-12T09:17:16.591Z
- Commit: 87af8ba97c05ce3a2b37e836a3c965524e0bcba6
- Completion claim: Delivery commit: 87af8ba97c05ce3a2b37e836a3c965524e0bcba6.

Implemented isolated CP epistasis and Gaussian VoI-proxy algorithms, a label-isolated AAV replay driver and six meaningful tests. Published the report, JSON trajectories, graph, execution metadata and logs in this task's artifacts. Reconstructed missing data from FLIP; audited 38,265 valid variants, 10,433 cold observations and 9,533 gated candidates. Production model code is unchanged.
- Reviews: rev-ceo-voi-01/approved
- Selected review: rev-ceo-voi-01
- Consent: consent-e78d40d5dc12d683169b9395
- Checker witnesses: pending
- Code-doc witness: pending

## Deliverables

- artifacts/voi-backtest-run.log
- artifacts/voi-backtest/backtest-report.md
- artifacts/voi-backtest/backtest_curves.png
- artifacts/voi-backtest/backtest_metrics.json
- artifacts/voi-backtest/closeout-ready.md
- artifacts/voi-backtest/execution.json
- artifacts/voi-tests.log
- research/prototypes/run_offline_backtest.py
- research/prototypes/sparse_epistasis_tensor.py
- research/prototypes/test_prototypes.py
- research/prototypes/voi_acquisition.py

## Outputs

- none

## Verification

- Six unit tests passed. Fourteen campaigns (96×3 and 48×6; budget 288 each) were each run twice with seed 42; every scientific metric, prediction and selected ID matched exactly. Fact F-460EE98D records the evidence. Best-new VoI did not exceed matched greedy or reach the 8.416205 candidate peak. The inclusive maximum 9.536457 is already in cold start, so inclusive tax is zero. Graph and report were inspected. Independent execution review and owner consent remain pending; no self-review was performed.

## Known gaps

- This is a fixed-factor CP and integer information/trace-reduction proxy, not learned sparse Tucker, verified contact priors or Bellman-optimal VoI. v0.4/v0.5 are explicitly reconstructed quota baselines rather than historical LLM replays. Rank and uncertainty weights are uncalibrated; one seed does not establish general effectiveness. No promotion to the production engine is supported by these negative/null results. Raw source is ignored locally and its SHA256 is recorded for replay.
- Mechanism: inconsistent membership of the baseline observation set changes the meaning of a cumulative maximum, and candidate-label-derived thresholds can expose held-back information through diagnostics. Searched for best_so_far, best_new, strong_thr and quantile in agent/auto_researcher.py and evolution/pool_campaign.py. The former's best_so_far reads all measured data including cold start, while _stats in the latter computes maxima over newly queried batches; both calculate a full-dataset quantile. This prototype explicitly reports both utility definitions and fixes the acquisition-visible strong threshold from cold-start labels. Existing production behavior was preserved.

## Residual risks

- This is a fixed-factor CP and integer information/trace-reduction proxy, not learned sparse Tucker, verified contact priors or Bellman-optimal VoI. v0.4/v0.5 are explicitly reconstructed quota baselines rather than historical LLM replays. Rank and uncertainty weights are uncalibrated; one seed does not establish general effectiveness. No promotion to the production engine is supported by these negative/null results. Raw source is ignored locally and its SHA256 is recorded for replay.
- Mechanism: inconsistent membership of the baseline observation set changes the meaning of a cumulative maximum, and candidate-label-derived thresholds can expose held-back information through diagnostics. Searched for best_so_far, best_new, strong_thr and quantile in agent/auto_researcher.py and evolution/pool_campaign.py. The former's best_so_far reads all measured data including cold start, while _stats in the latter computes maxima over newly queried batches; both calculate a full-dataset quantile. This prototype explicitly reports both utility definitions and fixes the acquisition-visible strong threshold from cold-start labels. Existing production behavior was preserved.
