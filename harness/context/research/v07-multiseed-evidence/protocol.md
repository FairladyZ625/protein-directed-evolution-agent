# Locked protocol before matrix completion

- Parent Mission is the execution contract; no dedicated canonical task ID supplied.
- AAV local CSV, one-hot; original EpistasisRidgePredictor defaults (three variance bootstrap models), original gate and fixed cold-start; 48 x 6.
- Acquisition seeds 0..29, all retained. No test-label-based configuration selection.
- mean; alternating mean/diverse (mean + 3 sqrt(var) + U[0,1)); UCB beta 0.5/1/2/3; marginal Gaussian Thompson approximation.
- Peak is the unmeasured-pool maximum, obtained only in audit, never in acquisition. Strong threshold follows legacy 90th percentile of ALL clean data; metric only.
- Wilson two-sided 95% intervals. One-sided exact binomial test H0:p<=1/3 only for stochastic methods; Holm across the two stochastic methods. Mean/UCB seed repeats have one unique deterministic trajectory and do not establish independent n=30 evidence.
- Greedy strong superiority: full distributions, per-seed win/tie/loss, one-sided sign tests for each stochastic comparison, Holm across those two comparisons. No inference from deterministic duplicates.
- Final max distribution includes min/Q1/median/Q3/max, mean/SD, full value frequencies. All per-seed records and per-round nominations retained.
- Fixed code/data/cold-start: inference is conditional acquisition-RNG reliability on this one pool, not independent landscapes/model fits.
- Runtime scheduling pilot interrupted before any full trial completed, solely to distribute work among three single-thread processes; its stdout/manifest retained in scheduling-pilot. No acquisition parameters changed.
- Cache key is the ordered measured row IDs; remaining pool is determined by those IDs. Exact fixed-model predictions reused, not approximated. Three workers; all 210 requested seed/configuration combinations execute their six nomination steps.
- Controls: positive/shuffled cold-start CV; replay legacy seed42 top10 and metrics; reconstruct all nominations from saved predictions and RNG; product and data SHA256 preservation.
- No network, LLM, product edits, full pytest suite, CI, publication or branch-history rewrite.
