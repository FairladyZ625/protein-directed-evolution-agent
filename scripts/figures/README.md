# Scientific report figures

Run from any directory with Python, Matplotlib, NumPy and Pillow installed:

```sh
python scripts/figures/generate_all.py
python scripts/figures/verify_figures.py
```

Outputs are five PNGs (300 DPI), five SVGs with editable text, and a verification JSON in `reports/figures/`. A single shared nine-color palette and DejaVu Sans typography are defined in `common.py`. Markers and line styles distinguish overlapping curves without relying on color alone. No smoothing, synthetic replicates, confidence intervals or interpolation of unobserved measurements is used; step segments connect actual recorded batch endpoints. Metrics exclude cold-start incumbents.

## Data provenance

The task's proposed `artifacts/figures_data/` was absent at dispatch. `extract_data.py` recovered 13 metric snapshots from existing campaign artifacts. `provenance.json` pins original files and extracted snapshots with SHA-256. Only machine metric fields are retained; free-text LLM summaries are not measurement evidence. To re-extract in the original multi-worktree workspace:

```sh
python scripts/figures/extract_data.py --source-root /path/to/canonical/repository
```

Rendering needs only the committed snapshots, not those source worktrees. Verification checks snapshot integrity, cumulative budget accounting, monotonic maxima, summary agreement, image dimensions/DPI, SVG structure and all five figure links in both presentation documents.

## Interpretation and corrections

- Figure 1 is a structured conceptual view of `agent/pipeline.py`, two injectable LLM ports, domain gates and `events/store.py`. SHA-256 chaining is tamper-evident, not a signature or an absolute immutability guarantee.
- Figure 2a follows the manifest's `campaign_llm` source (low-HD cold start); Figure 2b shows `campaign_easy` separately (random cold start, deterministic hypotheses). Neither recorded campaign supports the report's first-round knowledge-agent hit. Both reach FWAA at round 2; only the easy campaign's greedy remains at 8.045152. Different regimes must not be spliced into one curve.
- Figure 3 is a clearly labeled analytic schematic: `0.35*x + 0.25*y` versus `0.35*x + 0.25*y + 1.6*x*y`. No fitted Potts coefficients or numerical AAV surface were supplied. Coordinates and coefficients have arbitrary units and are not experimental data. The D0Q+S17E+V18A measured target (8.4162) is separate from the schematic. Pairwise geometry does not establish higher-order interactions or a physical spin-glass energy surface.
- Figure 4 uses actual `spent_after` budgets, including v0.2's 284 and v0.4's uneven agent batches. v0.5 ends at 6.5309. The v0.4 deterministic run reaches 8.4162 at 192 queries; v0.7 alternating does so in only seed42, while seeds 0/7 end at 7.829. All three mean runs are identical. Version differences are descriptive gaps, not a controlled causal estimate of exploration tax. The 8.4162 reference is a newly queried candidate peak, not the full dataset maximum (cold-start incumbents can exceed it).
- Figure 5 is a proposed RSI design. Shadow patches return to independent verification before controller-authorized use; no deployment or proof of immunity to evaluation gaming is implied.

The report snapshot and HTML explainer include corrections adjacent to the figures. Their broader literature claims and theoretical appendices are outside this figure-generation task and have not been revalidated.
