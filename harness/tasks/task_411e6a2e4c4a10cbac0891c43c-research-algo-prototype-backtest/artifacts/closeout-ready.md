## Summary

Implemented isolated CP epistasis and Gaussian VoI-proxy algorithms, a label-isolated AAV replay driver and six meaningful tests. Published the report, JSON trajectories, graph, execution metadata and logs in this task's artifacts. Reconstructed missing data from FLIP; audited 38,265 valid variants, 10,433 cold observations and 9,533 gated candidates. Production model code is unchanged.

## Verification

Six unit tests passed. Fourteen campaigns (96×3 and 48×6; budget 288 each) were each run twice with seed 42; every scientific metric, prediction and selected ID matched exactly. Fact F-460EE98D records the evidence. Best-new VoI did not exceed matched greedy or reach the 8.416205 candidate peak. The inclusive maximum 9.536457 is already in cold start, so inclusive tax is zero. Graph and report were inspected. Independent execution review and owner consent remain pending; no self-review was performed.

## Residual Risk

This is a fixed-factor CP and integer information/trace-reduction proxy, not learned sparse Tucker, verified contact priors or Bellman-optimal VoI. v0.4/v0.5 are explicitly reconstructed quota baselines rather than historical LLM replays. Rank and uncertainty weights are uncalibrated; one seed does not establish general effectiveness. No promotion to the production engine is supported by these negative/null results. Raw source is ignored locally and its SHA256 is recorded for replay.

## Same Mechanism Elsewhere

Mechanism: inconsistent membership of the baseline observation set changes the meaning of a cumulative maximum, and candidate-label-derived thresholds can expose held-back information through diagnostics. Searched for best_so_far, best_new, strong_thr and quantile in agent/auto_researcher.py and evolution/pool_campaign.py. The former's best_so_far reads all measured data including cold start, while _stats in the latter computes maxima over newly queried batches; both calculate a full-dataset quantile. This prototype explicitly reports both utility definitions and fixes the acquisition-visible strong threshold from cold-start labels. Existing production behavior was preserved.
