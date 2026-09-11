# Protein Directed Evolution Agent (GB1)

A small **ML-guided virtual directed-evolution** system on the GB1 fitness landscape:
train a fitness predictor from measured mutation data, then let a modular five-role
agent propose successive rounds of mutations, using the real measured landscape as a
"virtual wet-lab" oracle. It compares **random / model-greedy / LLM-agent /
knowledge-enhanced-agent** strategies over several rounds and analyses where they
succeed and fail.

The full experimental report (8 sections, PDF) is at **[`reports/report.pdf`](reports/report.pdf)**.

## Dataset

- **GB1** (protein G domain B1, 56 aa), 4 combinatorial sites V39/D40/G41/V54 — Wu et al. 2016
  (*eLife*). Wild type `VDGV` (fitness normalised to 1.0); global optimum `FWAA` = **8.762** (HD=4).
- The landscape has **149,361 measured variants** out of 20⁴ = 160,000 possible combinations;
  the remaining **10,639 are genuinely missing measurements**. All strategies nominate and
  evaluate strictly within the 149,361 measured variants — this limitation is reported, not hidden.
- The raw 44 MB `four_mutations_full_data.csv` is **not committed**. Place it under `data/`
  (source: <https://doi.org/10.7554/eLife.16965.024>) and run `make data` to validate it. Automatic
  download is intentionally disabled — the script never fabricates data.

## Fitness predictor

Three-level ladder with a shared `fit → predict(mean, var)` interface and a 5-seed deep ensemble
for uncertainty (`models/train_ladder.py`): one-hot + Ridge, gradient boosting, and an MLP; features
are one-hot (80-dim) or ESM-2 650M embeddings (1280-dim). Metrics: Spearman (primary), Pearson, MSE, Top-k.

| feature × split | Ridge | GBoost | MLP |
|---|---|---|---|
| one-hot × random | 0.484 | 0.474 | 0.389 |
| ESM-2 × random | 0.493 | 0.377 | 0.491 |
| one-hot × HD-extrapolation (train HD≤2 → test HD≥3) | 0.358 | 0.354 | 0.278 |
| ESM-2 × HD-extrapolation | 0.404 | 0.352 | **0.493** |

Spearman on a held-out set. On the harder HD-extrapolation split one-hot degrades sharply while
ESM-2 generalises noticeably better — the main argument for a protein language model here.

## Five-role LLM agent

`agent/pipeline.py` is a modular pipeline with Pydantic-validated I/O per role; the LLM is confined
to two injectable ports, everything else is deterministic and auditable:

1. **Data Analyst** — summarises per-site substitution fitness from the training pool.
2. **Hypothesis Generator** *(LLM port)* — proposes the substitutions worth combining; falls back to
   a deterministic top-k-per-site generator when no LLM is configured or a call fails.
3. **Mutation Designer** — enumerates a combinatorial library (≤1 substitution per site).
4. **Fitness Evaluator** — scores candidates with the predictor `(mean, var)`.
5. **Scientific Critic** *(LLM port + knowledge rules)* — validates/accepts/rejects with reasons; the
   `no_knowledge` switch disables the knowledge gate for ablation.

The LLM port uses an OpenAI-compatible pool via `agent/llm.py`, reading credentials from a local
`.env` (see `.env.example`; never committed). With no key or on any error it degrades to the
deterministic path, so **the project runs fully offline**; every round records whether it used the
live LLM or the fallback.

## Four-strategy campaign

`evolution/campaign.py` runs all four strategies under **one budget** (96/round × 3 rounds), **one
oracle** (measured-table lookup, never a model score) and **one nomination space** (the 149,361 measured
variants). To evaluate difficulty honestly there are three cold-start regimes:

- `--cold-start random` (**easy**): dense random seed pool (≈98% already HD≥3).
- `--cold-start low_hd` (**hard**, default recommended): seed only from HD≤2, extrapolate outward to HD≥3.
- `--cold-start low_hd --max-cold-hd 1` (**sparse**): seed from just the 77 single mutants.

Hard (HD≤2 extrapolation) regime, seed 42:

| strategy | cumulative max fitness | strong (≥4) | beneficial hits |
|---|---|---|---|
| random | 5.08 | 1 | 7 |
| greedy (Ridge, full-space) | 8.762 | 43 | 154 |
| agent (no knowledge) | **8.762** | **56** | **187** |
| knowledge agent (UCB + BLOSUM prior) | **8.762** | **57** | **190** |

**Honest finding:** GB1's 4-site landscape is itself *tractable* — even from only 77 single mutants,
the model-based strategies reach the global optimum by round 2, while random stays far away. So
"reaching the peak" is not the discriminator; the meaningful differences are **sample efficiency** and
**batch yield**, where the agent's focused library consistently beats plain greedy. The
knowledge enhancement is a light prior (marginal here). See `reports/report.pdf` §6–7 for the full
analysis, including a real library-truncation bug we found and fixed.

## Knowledge enhancement & auditable trails

`knowledge/` holds amino-acid properties, BLOSUM62 grading, mutation-count / stop-codon rules
(`rules.yaml`), validators, and a small `networkx` triple graph. The knowledge agent adds UCB
exploration (`mean + λ·√var`) plus a BLOSUM62 conservativeness prior; `--no-knowledge` ablates both.

`events/` is an append-only, chained-SHA-256 event log (+ SQLite projection + replay CLI): every
campaign step and agent role is recorded and `verify()`-able. Separately, **every experiment run**
appends an immutable entry to the master ledger `reports/experiment_log.jsonl` (command, params, git
commit, artifact SHA-256, summary) — a complete, tamper-evident history.

## Interactive demo

`app/demo.py` — a single-file **Streamlit** dashboard (read-only): ① four-strategy comparison with a
cold-start regime selector, ② five-role reasoning replay from the event stream (with in-page hash-chain
verification), ③ a live playground that scores any 4-site variant and runs one agent round to recommend
top-k mutations.

```bash
streamlit run app/demo.py     # or: make demo
```

## Setup & run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make data                                            # validate the local GB1 csv
make test                                            # unit tests
python -m models.evaluate_all                         # predictor ladder comparison -> reports/predictor_metrics.json
python -m evolution.campaign --cold-start low_hd      # four-strategy campaign (hard regime)
streamlit run app/demo.py                             # interactive demo
cp .env.example .env                                  # optional: add an LLM pool key, then add --use-llm
```

## Layout

```
data/         GB1 loader/validator, three-pool split, manifest
features/     one-hot and ESM-2 feature extraction (cached)
models/       predictor ladder + metrics
agent/        five-role pipeline + injectable LLM port
evolution/    mutation parsing, random baseline, four-strategy campaign, experiment ledger
knowledge/    mutation rules + knowledge graph + validators
events/       auditable event-stream kernel
app/          Streamlit interactive demo
reports/      metrics, figures, event streams, experiment ledger, report.pdf
tests/        unit tests
```

## External resources

GB1 dataset (Wu et al. 2016 / *eLife*); ESM-2 (`fair-esm`, `esm2_t33_650M_UR50D`); scikit-learn / PyTorch.
The LLM agent calls an OpenAI-compatible model pool through an injectable port (credentials in a local,
uncommitted `.env`); all external model/data use is declared in the report.
