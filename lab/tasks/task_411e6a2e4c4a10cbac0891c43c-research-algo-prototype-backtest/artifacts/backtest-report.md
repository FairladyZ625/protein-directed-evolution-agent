# AAV offline prototype backtest

## Protocol and evidence

The missing declared pool was reconstructed from [FLIP AAV](https://github.com/J-SNACKKB/FLIP/tree/main/splits/aav), using the repository loader's sequence filtering and first-occurrence deduplication, tightened to the 20 canonical amino acids. Recomputed HD agrees with metadata. Sequence IDs are zero-based cleaned source-row order. Full hashes, configuration, all per-round predictions, queried IDs/labels, and diagnostics are in `backtest_metrics.json`. No labels are passed to the policy; the oracle opens only the frozen batch and rejects duplicate or over-budget queries. All campaigns finish before retrospective global-peak evaluation.

All runs use seed 42, the same 10,433 HD≤2 observations and HD≤4 / mean BLOSUM62≥0 candidate gate, and exactly 288 new assays. Strong hits use the cold-start 90th percentile fixed before acquisition (not a candidate-label quantile). The real historical table is a noiseless lookup; noise=1 is a surrogate likelihood assumption. No extra assays or labels are used for calibration or tuning.

## Algorithms and comparison limits

Fixed rank-16 random CP distinct-site ANOVA factors implement higher-order theory equation (8), with full reference-state additive features and a proper Gaussian Ridge prior (alpha=10). The degree-2 control uses the same factors and omits the cubic block. This is a uniform-prior, no-contact prototype: no verified contact map was supplied. No learned Tucker cores, group-lasso support selection, or learned projection factors are claimed. Cubic features are exactly zero on HD≤2, leaving zero posterior mean and nonzero prior variance until higher-order observations arrive.

VoI is the equation (13) acquisition **proxy**, using exact integer marginal logdet information and normalized epistasis parameter trace reduction (W=identity). Both weights start at 1 in their respective utility units and decay linearly to zero for the final round. Covariance is updated after every pending selection, without labels; the mean is frozen for the entire batch. This is integer greedy marginal optimization, not a solved fractional relaxation, Bellman rollout, or simple-regret guarantee. No fractional rounding gap is asserted. Information-only and variance-only ablations isolate the two rewards.

v04_fixed and v05_annealed are explicitly reconstructed heuristic controls: 25% highest-variance quota, respectively constant or linearly decaying to zero, with nearest-integer slots and mean-based fill. The required checkout has no compose_batch implementation and the predecessor theory records no independently verified v0.5 terminal result. These runs do not reproduce historical LLM choices or the production EpistasisRidgePredictor. All acquisition comparisons share the same degree-3 surrogate; degree-2 versus degree-3 greedy is a separate model ablation. Production code remains untouched.

## Results

The cold-start maximum is 9.53645667061, already the full-pool maximum. Thus inclusive best-so-far is flat, global peak discovery budget is zero, and inclusive exploration tax is zero for every policy. The eligible new-candidate maximum is 8.416205130560002, explaining the predecessor report’s quoted peak. The table and plot below use **best newly queried fitness** and its matched-policy difference to expose acquisition performance; this is a distinct utility from inclusive best-so-far. No policy was retuned after this metric audit.

| Model degree | Schedule | Policy | Best new | Strong hits | New-candidate tax | Candidate peak budget |
|---|---|---|---:|---:|---:|---:|
| 2 | 96×3 | greedy | 7.828968 | 74 | 0.000000 | None |
| 2 | 48×6 | greedy | 7.828968 | 73 | 0.000000 | None |
| 3 | 96×3 | greedy | 7.828968 | 65 | 0.000000 | None |
| 3 | 96×3 | v04_fixed | 7.828968 | 51 | 0.000000 | None |
| 3 | 96×3 | v05_annealed | 7.828968 | 56 | 0.000000 | None |
| 3 | 96×3 | voi_information | 7.828968 | 65 | 0.000000 | None |
| 3 | 96×3 | voi_epistasis | 7.828968 | 65 | 0.000000 | None |
| 3 | 96×3 | voi_full | 7.828968 | 65 | 0.000000 | None |
| 3 | 48×6 | greedy | 7.828968 | 67 | 0.000000 | None |
| 3 | 48×6 | v04_fixed | 7.058332 | 59 | 0.770635 | None |
| 3 | 48×6 | v05_annealed | 7.828968 | 65 | 0.000000 | None |
| 3 | 48×6 | voi_information | 7.828968 | 65 | 0.000000 | None |
| 3 | 48×6 | voi_epistasis | 7.828968 | 67 | 0.000000 | None |
| 3 | 48×6 | voi_full | 7.828968 | 65 | 0.000000 | None |

The prototype does not improve terminal best-new fitness over its matched greedy baseline and no run reaches the eligible peak. At 48×6, the fixed-quota control loses 0.770635 fitness; annealing closes this gap. Degree-3 greedy yields 67 strong hits versus 73 for degree-2 greedy, so this experiment does not support promoting the cubic prototype. The full VoI proxy yields 65 versus 67 for degree-3 greedy. These are negative/null findings, not evidence of a production upgrade.

![Discovery trajectories](backtest_curves.png)

New-candidate tax is matched-degree, matched-schedule greedy best-new minus policy best-new; negative values are an exploration dividend. Candidate peak budget is the end of the first batch reaching the eligible new-candidate maximum; None means not reached by 288. The JSON retains the separately defined inclusive exploration tax and global peak budget. Within-batch ordering cannot establish an earlier feedback event. JSON also records best-new fitness, cumulative strong hits, pre-query mean opportunity cost and off-greedy slots. Mean opportunity cost is not terminal exploration tax. Single-seed realized differences are not unbiased population causal estimates or confidence intervals. Closed-pool replay cannot predict unseen sequences or new wet-lab noise.

## Reproduction and verification

From the worktree, use `.venv/bin/python -m unittest discover -s research/prototypes -p 'test_*.py'`, then `.venv/bin/python -m research.prototypes.run_offline_backtest --data data/aav/full_data.csv --output artifacts/voi-backtest --verify-repeat`. Numerical work is limited to one BLAS thread. The repeat option compares all scientific metrics, predictions and batch IDs exactly; wall time is recorded separately in `execution.json`. Download and unzip FLIP's `full_data.csv.zip` into `data/aav/` if absent. Verify the CSV SHA256 against the metrics before replay. Environment versions and peak process RSS are recorded separately. No task artifacts or raw data are committed from ignored Harness/data directories.

## Residual risk

Weights, rank and covariance are uncalibrated engineering defaults; narrow surrogate uncertainty does not certify accuracy. A fixed CP projection compresses pairwise interactions and may miss important couplings. No structural contact advantage or pure third-order biological attribution has been demonstrated. One seed and one historical dataset do not establish general superiority; retain negative and null results. Independent execution review and owner consent remain required by repository workflow.
