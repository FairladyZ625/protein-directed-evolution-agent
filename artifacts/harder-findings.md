# Harder-landscape findings

## Verified in this run

- Ridge ensemble members now train on deterministic bootstrap resamples (five
  members, seed-indexed), so `predict(X)` returns a non-degenerate epistemic
  variance. The focused test observed `variance_mean > 0` and different values
  across the pool, with replay-identical mean and variance.
- The ESM input path now accepts full amino-acid sequences (AAV/avGFP) while
  preserving the four-residue GB1 shorthand. The focused tests pass.
- AAV ESM campaign could not complete: `fair-esm` installed successfully, but
  the official 650M checkpoint download from `dl.fbaipublicfiles.com` made no
  progress during the observed run and was interrupted. Therefore no AAV ESM
  metrics, event stream, or curve are claimed here.
- avGFP was not run because no `data/avgfp/avgfp.csv` was present. The loader
  now requires an explicit WT row (`mutant`/`mutation`/`mutations` equal to
  `WT`) and rejects inferred longest-sequence WT values.

## Cross-dataset conclusion

There is not yet an evidence-backed agent-vs-greedy comparison for AAV ESM or
avGFP. Existing one-hot AAV conclusions remain outside this run and are not
re-stated as new measurements.

## Next step

Provide the ProteinGym avGFP CSV and complete the ESM-2 checkpoint download (or
use a pre-populated approved cache), then run both pool campaigns and record
the variance min/mean/max emitted in `fitness_evaluator` events.
