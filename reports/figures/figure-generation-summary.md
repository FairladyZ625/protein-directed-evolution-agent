# Figure generation summary

Task: task_a4fe196cee3fd986f1e8a213a4

## Delivery

Five Matplotlib figures, each as PNG at 300 DPI and editable vector SVG, in `reports/figures/`. Reproducible scripts: `scripts/figures/`; pinned measurements: `artifacts/figures_data/`. Both `reports/scientific_report_v1.0.md` and `reports/explainer_for_humans.html` embed all five figures. The latest concurrent HTML layout and figure cards were preserved, with captions aligned to measured data.

## Verification

- `python scripts/figures/generate_all.py`: successful; full stdout in `reports/figures/generation.log`.
- `python scripts/figures/verify_figures.py`: passed, 13 snapshot hashes, 91 round endpoints, cumulative budgets and maxima, summaries, PNG DPI, pure vector SVG structure, and ten PNG links across two documents.
- All five rendered images inspected visually; diagram routes and legends adjusted to avoid label overlap.
- A headless Chrome screenshot attempt returned a blank image with macOS display-link errors. Browser-level page visual verification is therefore not claimed; decoded PNGs, SVG structure and embedding paths were verified independently.
- Environment: Python 3.13.2, Matplotlib 3.11.1, NumPy 2.5.3.
- Canonical promoted fact: F-DB694B6C.

| PNG | Pixels | DPI |
|---|---|---|
| reports/figures/fig1_agent_architecture.png | 4200 × 2100 | 299.999 |
| reports/figures/fig2_gb1_convergence.png | 3600 × 1650 | 299.999 |
| reports/figures/fig3_epistasis_landscape.png | 3900 × 1950 | 299.999 |
| reports/figures/fig4_aav_exploration_tax.png | 4800 × 1800 | 299.999 |
| reports/figures/fig5_five_machine_rsi.png | 3900 × 2400 | 299.999 |

SVG counterparts exist for every PNG; file hashes are in `reports/figures/verification.json`.

## Evidence-driven changes to the requested narrative

The task's extracted JSON directory was absent. Original metrics were recovered from canonical Harness reports and the v0.5/v0.7 experiment worktrees. Each snapshot records its source path and SHA-256; the extractor is committed.

The manifest's GB1 campaign_llm has knowledge-agent and greedy round-2 hits (not a round-1 knowledge-agent hit). campaign_easy has greedy ending at 8.045152 but uses a different cold start and deterministic hypotheses. Figure 2 keeps these conditions in separate panels; table 3, associated prose and abstract were corrected to the available records.

AAV uses actual consumed budgets: v0.2 284; other displayed runs 288, including uneven v0.4 agent batches. v0.5 ends at 6.5309. Only v0.7 alternating seed42 hits 8.4162 at 192 queries; seed0/7 stop at 7.829. All mean seeds are shown as identical. Version gaps are descriptive, not an isolated causal exploration-tax estimate. 8.4162 is a newly queried candidate reference, not the full-dataset maximum.

## Residual scope

Figure 3 is an analytic additive-versus-pairwise schematic, with arbitrary coordinates and units and a separately sourced AAV target annotation. Fitted AAV interaction coefficients were unavailable; no measured 3D landscape, physical spin-glass energy, high-order interaction estimate or target location is invented. Figure 5 is a proposed control architecture. Other claims and references in the upstream report and theoretical appendices were not audited by this visual-engineering task.

The task branch retains the deliverable commit for independent execution review and owner consent; no self-review, merge or remote publication is performed. During closeout the shared Harness daemon went offline (socket missing); artifact registration returned daemon_start_runtime_forbidden. The fact was promoted before that outage. Canonical report assets were synchronized after checking source hashes and merging concurrent HTML changes. The task-package artifact registration, closeout sync and submission remain pending daemon recovery.
