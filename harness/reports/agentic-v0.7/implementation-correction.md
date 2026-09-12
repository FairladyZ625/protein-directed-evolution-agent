# SEMI contract correction, before compliant SEMI runs

Audit of action metadata (not peak selection) found premature mixed exploration:
SEMI seed42 used 34 mean +14 diverse in round3; seed7 used 36 mean +12 diverse in round2,
before the declared two-flat-round condition. This violates the task's "exploit until stagnation"
phase boundary. The initial code only forced exploration after stagnation but left early ratios free.

The three original SEMI processes were stopped. Their complete traces/logs available at cancellation
are retained in aav/pilot-semi-seed42, pilot-semi-seed0, pilot-semi-seed7, with explicit aborted status;
none is silently replaced or counted as a compliant 288-budget result. Their paths are excluded from
matrix-summary by the explicit pilot prefix.

The corrected SEMI implementation requires full predicted-mean batches before stagnation, and full
exploration batches while stalled. The LLM chooses the exploration method, not the phase or amount.
The test tool checks the phase even for direct candidate calls. Improvement restores exploitation.
Tests now explicitly attempt early exploration and direct-test bypass, and verify recovery.
Observed targeted output: 30 passed in 3.29s.

No exploration scores, threshold/patience, gate, data, oracle, model, seeds or budgets changed.
The correction is conditional exclusively on backtrack == semi. Reference and FULL code paths and
prompts are unchanged, so their ongoing runs remain the registered trials; their source hash points
to local commit b661c0d, while corrected SEMI records its own source hash. This is a contract fix,
not selection of better-performing exploratory parameters. The three compliant SEMI runs start only
after these tests and this note are written. No further policy tuning is authorized in this run.

A subsequent targeted offline-fallback check identified that legacy alternating fallback must
also respect SEMI phases. The final source uses compose_batch for SEMI exploitation fills;
FULL/reference and live LLM choice paths are unchanged. Formal SEMI trials were already loaded
with phase enforcement; their recorded source hashes are retained. Where a live trial has a
pre-stagnation harness fill, the candidate ledger must verify it is the same full mean top48.
Final targeted suite adds this offline-fallback regression.
