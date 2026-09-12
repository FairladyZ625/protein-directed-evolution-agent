## Summary

Generated the five core scientific figures as 300 DPI PNG and vector SVG in `reports/figures/`, with reproducible source in `scripts/figures/` and 13 source-pinned metric snapshots in `artifacts/figures_data/`. Aligned `reports/scientific_report_v1.0.md` and `reports/explainer_for_humans.html`; preserved concurrent HTML presentation changes and synchronized the canonical report package. GB1 captions now separate cold-start regimes and use recorded round-2 knowledge-agent hits; AAV includes v0.5 and all v0.7 seeds. Delivery is the bound t-scientific-figures branch HEAD.

## Verification

`python scripts/figures/generate_all.py` completed. `python scripts/figures/verify_figures.py` passed: 13 snapshot hashes, 91 recorded batch endpoints, budget accounting, cumulative metrics, five PNG DPI checks, five SVG vector checks, and five image links in each presentation document. All five plots were visually inspected; crossing diagram labels and obscuring legends were corrected. `git diff --cached --check` passed. Promoted fact: F-DB694B6C. Detailed evidence: `reports/figures/figure-generation-summary.md`, `reports/figures/generation.log`, `reports/figures/verification.json`. Independent review and consent are pending; no self-review was performed.

## Residual Risk

Figure 3 is an analytic schematic in arbitrary units, not a fitted AAV or physical spin-glass energy surface. Figure 5 is a proposed design. Version gaps are descriptive rather than isolated causal estimates; only one of three alternating seeds reaches 8.4162. Broader upstream report claims and references were not revalidated. A headless Chrome attempt produced a blank screenshot with macOS display-link errors; browser page visual review is not claimed. The latest HTML references additional upstream timeline screenshots not owned by this task. A transient daemon outage recovered before handoff; task artifacts are registered. Independent execution review and owner consent remain outstanding.

## Same Mechanism Elsewhere

Mechanism: an experiment narrative can mix incomparable conditions or cold-start and newly queried maxima, producing a visually persuasive but unsupported result. Searched the named campaign metric summaries, round records, report figure captions and HTML figure descriptions for round-1 hits and global-maximum language. Found mismatched GB1 regimes in the old figure caption/table and AAV incumbent-versus-new-query confusion in LLM summaries and presentation prose. The extractor now keeps machine metrics and provenance, separates GB1 regimes and excludes cold-start incumbents. Captions identify the limits; broader theoretical claims remain outside this task's audit.
