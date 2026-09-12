# Protein Directed Evolution Agent (GB1)

A small **ML-guided virtual directed-evolution** system on the GB1 fitness landscape:
train a fitness predictor from measured mutation data, then let a modular five-role
agent propose successive rounds of mutations, using the real measured landscape as a
"virtual wet-lab" oracle. It compares **random / model-greedy / LLM-agent /
knowledge-enhanced-agent** strategies over several rounds and analyses where they
succeed and fail.

The full experimental report is at
**[`reports/final-report-v0.5/scientific_report_v0.5_two_column.pdf`](reports/final-report-v0.5/scientific_report_v0.5_two_column.pdf)**
(markdown source: [`reports/final-report-v0.5/report.md`](reports/final-report-v0.5/report.md)).

Two trees, two jobs — this separation is deliberate:

- **`reports/`** is the *report authoring* tree: `final-report-v0.x/` holds each report version's
  markdown, figures, build scripts and rendered PDF.
- **`harness/reports/`** is the *experiment artifact* tree: one self-contained folder per research
  cycle, named `<line>-v<version>/` (see `evolution/results_layout.py`, which is the single source
  of truth for this layout). Three method lines are current: `workflow-v1.1` (the delivery pipeline
  on GB1), `agentic-v0.7` (the autonomous researcher on AAV), `analysis-v0.1` (read-only analyses
  over already-measured data). A revision digest for the report writer lives at
  [`harness/reports/REPORT-HANDOFF.md`](harness/reports/REPORT-HANDOFF.md).

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
appends an immutable entry to the master ledger
[`harness/reports/experiment_log.jsonl`](harness/reports/experiment_log.jsonl) (command, params, git
commit, artifact SHA-256, summary).

**Honest scope note:** that ledger currently covers the main closed-loop experiments (15 entries).
It does not yet cover every historical run — the `analysis-v0.1` line and some early `agentic`
versions are not registered in it. Treat it as a partial, append-only spine rather than a complete
index; each version folder's own `manifest.json` and the per-run `metrics.json` are authoritative
for that run.

## Interactive demo

`app/demo.py` — a single-file **Streamlit** dashboard (read-only): ① four-strategy comparison with a
cold-start regime selector, ② five-role reasoning replay from the event stream (with in-page hash-chain
verification), ③ a live playground that accepts a four-site GB1 wild type (V39/D40/G41/V54), recomputes
its single-substitution menu, and recommends Top-k mutations with the existing Ridge predictor. Predictions
are labelled as model output (not measurements), and an unmeasured input WT gets an explicit warning. The
dashboard remains read-only: its standard-GB1 one-round campaign trace is held only in memory.

```bash
streamlit run app/demo.py     # or: make demo
```

## Setup & run

For a clean Linux or macOS clone, the recommended first run is two commands:

```bash
./scripts/install.sh       # Python 3.11+, offline smoke/demo/test tier; no torch or data download
./scripts/run_all.sh       # always runs smoke; runs predictor + GB1 campaign when the CSV is present
```

The first command creates `.venv` and installs the same scientific stack used by the
self-contained CI tests, plus the offline agent runtime required by the smoke path.
It deliberately does not install PyTorch or download data. Use
`./scripts/install.sh --full` to add PyTorch and fair-esm for local ESM-2 extraction;
the GB1 CSV remains a separate, explicit download described in
[`data/README.md`](data/README.md). `run_all.sh` prints a clear downgrade notice and
finishes after smoke when that CSV is absent.

Manual entry points remain available:

```bash
# First command for a clean clone: no GB1 CSV, ESM cache, or API key required.
make smoke                                           # synthetic small landscape -> tmp/smoke/
make test                                            # self-contained tests (same set as CI)
make data                                            # validate a locally supplied full GB1 CSV
python -m models.evaluate_all                         # predictor ladder + standardisation ablation
                                                      #   -> harness/reports/workflow-v1.0/gb1/predictor_ladder_scaling_ablation.json
python -m models.alpha_sweep                          # answer-agnostic alpha selection per feature
                                                      #   -> harness/reports/workflow-v1.0/gb1/predictor_alpha_sweep.json
python -m evolution.campaign --cold-start low_hd      # four-strategy campaign (hard regime)
streamlit run app/demo.py                             # interactive demo
cp .env.example .env                                  # optional: add an LLM pool key, then add --use-llm
```

`make smoke` is the recommended first run. It executes the data → predictor → five-role
agent → four-strategy campaign path on a fixed, synthetic 16-variant landscape and writes a
labelled CSV, metrics, event stream, SQLite read projection, plot, and README to `tmp/smoke/`.
It uses the offline deterministic LLM fallback. **Its synthetic small-scale numbers are only a
reproducibility demonstration and must not be compared with the formal GB1 results.** For the
full measured GB1 campaign, obtain `data/four_mutations_full_data.csv` as described in
[`data/README.md`](data/README.md); `make campaign` will otherwise state this requirement and
suggest `make smoke`.

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
reports/      report authoring tree (final-report-v0.x: markdown, figures, build, PDF)
harness/reports/  experiment artifacts, one folder per cycle (<line>-v<version>) + experiment ledger
tests/        unit tests
```

## External resources

GB1 dataset (Wu et al. 2016 / *eLife*); ESM-2 (`fair-esm`, `esm2_t33_650M_UR50D`); scikit-learn / PyTorch.
The LLM agent calls an OpenAI-compatible model pool through an injectable port (credentials in a local,
uncommitted `.env`); all external model/data use is declared in the report.
