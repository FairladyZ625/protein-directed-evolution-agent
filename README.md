# Protein Directed Evolution Agent (GB1)

A small **ML-guided virtual directed-evolution** system on the GB1 fitness landscape:
train a fitness predictor from measured mutation data, then let a modular agent propose
successive rounds of mutations, using the real measured landscape as a "virtual wet-lab"
oracle. The goal is to compare **random / model-greedy / LLM-agent / knowledge-enhanced-agent**
strategies over several rounds and analyse where they succeed and fail.

> **Status: work in progress.** The data pipeline, fitness-predictor ladder, an auditable
> event-stream kernel, and the mutation knowledge base are implemented and tested. The
> five-role LLM agent, the four-strategy closed-loop campaign, and the interactive demo
> are under active development.

## Dataset

- **GB1** (protein G domain B1, 56 aa), 4 combinatorial sites V39/D40/G41/V54 — Wu et al. 2016
  (*eLife*), packaged with FLIP-derived sequence/split columns.
- The landscape has **149,361 measured variants** out of the 20⁴ = 160,000 possible
  combinations; the remaining **10,639 are genuinely missing measurements** (not a complete
  combinatorial table). All strategies therefore nominate and evaluate strictly within the
  149,361 measured variants, and this limitation is reported rather than hidden.
- The raw 44 MB `four_mutations_full_data.csv` is **not committed**. Place it under `data/`
  (source: <https://doi.org/10.7554/eLife.16965.024>) and run `make data` to validate it and
  write `data/gb1_manifest.json` (SHA-256, row count, WT fitness). Automatic download is
  intentionally disabled — the script never fabricates data.

## Fitness predictor

Three-level ladder with a shared `fit → predict(mean, var)` interface and a 5-seed deep
ensemble for uncertainty (`models/train_ladder.py`): one-hot + Ridge (L1), ESM-2 650M
embeddings + gradient boosting (L2), and an MLP (L3). Metrics: Spearman (primary), Pearson,
MSE, Top-k hit rate.

Honest feature × split comparison (`models/evaluate_all.py`, mean over an ensemble):

| feature × split | Ridge | GBoost | MLP |
|---|---|---|---|
| one-hot × random | 0.484 | 0.474 | 0.389 |
| ESM-2 × random | 0.493 | 0.377 | 0.491 |
| one-hot × HD-extrapolation (train HD≤2 → test HD≥3) | 0.358 | 0.354 | 0.278 |
| ESM-2 × HD-extrapolation | 0.404 | 0.352 | **0.493** |

Spearman on a held-out set. On the harder HD-extrapolation split (predicting higher-order
mutants from low-order ones) one-hot degrades sharply while ESM-2 embeddings generalise
noticeably better — the main argument for using a protein language model here.

## Auditable event stream

`events/` is a minimal append-only event log (chained SHA-256 + fsync), a SQLite projection,
and a replay CLI. Every campaign step is recorded so the agent's reasoning can be replayed and
the run is tamper-evident (`verify()` reports the first broken link).

## Mutation knowledge base

`knowledge/` holds amino-acid physicochemical properties, BLOSUM62 conservative/radical
grading, mutation-count limits and stop-codon guards (`rules.yaml`), validators, and a small
`networkx` triple graph. A `--no-knowledge` switch supports the with/without ablation.

## Setup & run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make test        # unit tests
make baseline    # strategy ① random-mutation baseline over 3 rounds
```

(`make train` / `make campaign` / `make demo` land with the predictor, closed-loop, and demo
milestones.)

## Layout

```
data/         GB1 loader/validator, three-pool split, manifest
evolution/    mutation parsing, random baseline, (campaign — WIP)
features/     one-hot and ESM-2 feature extraction (cached)
models/       predictor ladder + metrics
events/       auditable event-stream kernel
knowledge/    mutation rules + knowledge graph
reports/      metrics tables and figures
tests/        unit tests
```

## External resources

GB1 dataset (Wu et al. 2016 / FLIP); ESM-2 (`fair-esm`); scikit-learn / PyTorch. The LLM agent
uses a commercial LLM API; any external model or data use is declared in the project report.
