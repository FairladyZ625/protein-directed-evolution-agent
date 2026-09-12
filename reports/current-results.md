# Current result summary

This Markdown file is the README-linked source for the current experimental
conclusion while the final PDF is prepared separately.

## Scope

Results come from a constructed FLIP-AAV pool: 27,832 candidates outside a
10,433-variant cold start, 288 measurements, an HD≤4 guardrail, and an
EpistasisRidge surrogate. They describe this finite in-silico pool and should
not be generalized to wet-lab protein engineering without additional evidence.

## Decision-relevant conclusion

The objective determines the appropriate policy:

| Objective | Best observed policy | Evidence |
|---|---|---|
| Find many strong variants | Pure exploitation / greedy | `strong=166`, stable over 30 seeds |
| Find the single in-pool global peak | Uncertainty-heavy UCB, β=3 | fitness 8.4162 in deterministic 30/30 runs |

The autonomous LLM decision policy matched neither outcome. Thus a fixed,
objective-aligned acquisition rule outperformed the autonomous decision policy
for both evaluated goals. The peak is below the cold-start incumbent (9.536),
so “finding the pool peak” must not be read as improving on the best initially
known variant.

Source fact: `F-885537A3` (30-seed robustness analysis).
