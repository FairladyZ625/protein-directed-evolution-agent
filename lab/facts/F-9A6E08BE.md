# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-9A6E08BE

- Statement: decision_lineage_missing 只对 milestone 与 long_running 生效,standard 任务无需 decision--derives-->task 边即可完成。判据:closeout-readiness.js:58-65 的 lineageOrphan 首行即 taskClass !== milestone 且 !== long_running 时 return false。对照实证:本仓 8 个 status=done 任务全为 standard 且 derives 边 count=0,说明已有任务在零决策边下走完终态。故零门 standard 任务的完成链实为 复审通过 -> review-consent -> complete,另加各自声明的 completionGates。
- Evidence source: packages/cli/dist/kernel/src/domain/closeout-readiness.js:58-65
- Observed at: 2026-09-14T10:45:30.717Z
- Confidence: high
- State: standing

