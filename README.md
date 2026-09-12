# Protein Directed-Evolution Agent

This repository is a small, reproducible virtual directed-evolution testbed. It
keeps the original complete **GB1** landscape as a compact integration path and
uses the FLIP **AAV** pool as the current scientific mainline. Candidates are
selected by an algorithm, then evaluated only by lookup in the corresponding
measured landscape; a prediction is never reported as a wet-lab result.

The current result source is [the checked-in Markdown summary](reports/current-results.md).
The final 3–5 page PDF is produced separately; no placeholder PDF is included here.

## Main result

The AAV result has two deliberately separate objectives and two opposite best
policies. For **many strong variants**, pure exploitation/greedy is best
(`strong=166`). For finding the single in-pool global peak, uncertainty-heavy
UCB (`β=3`) reaches fitness **8.4162** deterministically in **30/30** runs.
The autonomous LLM decision policy matched neither result. This is a result
about this constructed, finite AAV pool—not a claim of general protein-design
performance.

## Environment and data

- Python **3.11+**; install the pinned dependencies in `requirements.txt`.
- The smoke path is CPU-only and uses a committed synthetic 16-variant GB1
  landscape. It needs no model download, network access, or 44 MB source CSV.
- Full GB1 evaluation needs `data/four_mutations_full_data.csv` from
  [Wu et al. 2016](https://doi.org/10.7554/eLife.16965.024). It is intentionally
  not committed; `make data` validates a file that you place there and never
  downloads or fabricates it.
- Full predictor evaluation can use CPU one-hot features or cached ESM-2
  embeddings. ESM-2 is practical on Apple MPS when available, but is materially
  slower and more memory-intensive than the CPU smoke path.
- The AAV source is the FLIP AAV split (`full_data.csv`); it is likewise local
  input, not committed data.

## Quick start: clean-clone smoke

```bash
git clone <repository-url>
cd protein-directed-evolution-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make smoke
```

`make smoke` runs all four strategies for two rounds over the committed,
complete 16-variant fixture. It exercises the measured-table oracle, the
five-role pipeline, the knowledge/no-knowledge acquisition split, and
reproducibility without requiring either full dataset.

## Full local-data commands

```bash
make data                         # validate local GB1 CSV only; does not download
make train                        # executable predictor evaluation entry point
make campaign                     # GB1 four-strategy campaign (requires full GB1 CSV)
make demo                         # Streamlit dashboard (requires local datasets)
```

`make train` invokes `python -m models.evaluate_all`, which is the executable
predictor-evaluation entry point. It writes generated output under the local
`harness/reports/` tree; those run artifacts are not a required clean-clone
input. An optional live LLM requires a local `.env`; otherwise the code follows
its deterministic fallback path.

## Layout

```
data/         local-data validators and source notes
features/     one-hot and ESM-2 feature extraction
models/       predictor ladder and executable evaluation entry point
agent/        five-role pipeline and optional LLM port
evolution/    campaigns, measured-table oracle, and experiment ledger
knowledge/    mutation rules, graph, and validators
events/       append-only SHA-256 event stream
app/          read-only Streamlit dashboard
tests/        unit tests plus the committed smoke fixture
reports/      checked-in current-result Markdown source
```

## Provenance

The optional LLM port resolves its actual model ID at runtime and records that
resolved value in run provenance. Historical v0.4 material carries a correction
for the previously displayed model alias; orchestration-agent configuration
names are not experimental-model provenance.
