# Protein Directed Evolution Agent — GB1 × AAV

*[中文版 / Chinese version](README.zh-CN.md)*

A small **ML-guided virtual directed-evolution** system on two real deep-mutational-scanning
landscapes. Train a fitness predictor from measured mutation data, let an agent propose successive
rounds of mutations, and use the real measured landscape as a "virtual wet-lab" oracle — never a
model score. Two datasets, two independent agent architectures, one auditable event kernel.

The full experimental report is at
**[`reports/final-report-v0.6/scientific_report_v0.6_two_column.pdf`](reports/final-report-v0.6/scientific_report_v0.6_two_column.pdf)**
(markdown source: [`reports/final-report-v0.6/report.md`](reports/final-report-v0.6/report.md)).

## The headline result: the tool contract sets the ceiling on agent autonomy

The sharpest finding here is not about the model. Under one tool contract, injecting the previous
round's prediction residuals into the agent's prompt changed **nothing**: reflexion-on and
reflexion-off produced **byte-identical batches**, 48/48 variants × 6 rounds, under two different
acquisition policies. The agent read the evidence, discussed the lethal motifs in its summary, and
nominated exactly the same candidates.

That was not a model failure. Reading the code showed the cause was the **shape of the contract**:
`exploit_ratio` is a scalar, and **no value of a scalar can express "do not pick candidates carrying
N21D"**. The one actionable entry point did not exist, so the reflexion card's action constraint was
unactionable by construction and could only be honoured in prose.

Adding a motif-level exclusion parameter (plus removing a prompt clause that discouraged setting the
ratio, plus releasing an exploitation floor) changed the outcome immediately — **same model, same
seed, same injected text**:

| | v0.8 contract | v0.9 contract |
|---|---|---|
| agent set `exploit_ratio` itself | **0 / 20 calls** | **11 / 11 calls** |
| batches diverge with reflexion on vs off | **no** (6/6 rounds identical) | **yes**, widening each round (r1 46/48 → r6 8/48) |
| lethal-motif recurrence, late rounds | 13.9% | **6.2%** |

Every motif the agent excluded was traceable to residual evidence injected earlier — 20 exclusions,
zero fabricated. It also excluded only 20 of the 34 motifs the evidence flagged, i.e. it chose rather
than blanket-filtered.

**Caveats, stated up front:** single seed (42); the contract is a *compound* treatment (prompt +
floor + exclusion entry) and this work did not separate their individual contributions; the strong-hit
differences (158 / 153 / 160) are too small to be an effect size. Replication under a second protocol,
and one earlier claim it falsified, are in
[`reports/final-report-v0.6/v07-handoff-02-protocol-and-chapter8.md`](reports/final-report-v0.6/v07-handoff-02-protocol-and-chapter8.md).

## Repository layout: two trees, two jobs

- **`reports/`** — the *report authoring* tree: `final-report-v0.x/` holds each report version's
  markdown, figures, build scripts and rendered PDF.
- **`harness/reports/`** — the *experiment artifact* tree: one self-contained folder per research
  cycle, named `<line>-v<version>/` (see `evolution/results_layout.py`, the single source of truth for
  this layout). Current method lines: `workflow-v1.2` (delivery pipeline on GB1), `agentic-v0.7`
  (autonomous researcher on AAV), `v09-contract` / `v09-contract-b12` (the tool-contract factorials),
  `analysis-v0.1` (read-only analyses over already-measured data). A revision digest for the report
  writer lives at [`harness/reports/REPORT-HANDOFF.md`](harness/reports/REPORT-HANDOFF.md).

## Datasets

### GB1 — protein G domain B1, 4 combinatorial sites

- 56 aa protein, variable sites V39/D40/G41/V54 — Wu et al. 2016 (*eLife*).
  Wild type `VDGV` (fitness normalised to 1.0); global optimum `FWAA` = **8.762** (HD=4).
- **149,361 measured variants** out of 20⁴ = 160,000 possible combinations; the remaining
  **10,639 are genuinely missing measurements**. All strategies nominate and evaluate strictly within
  the measured set — this limitation is reported, not hidden.
- The raw 44 MB `four_mutations_full_data.csv` is **not committed**. Place it under `data/`
  (source: <https://doi.org/10.7554/eLife.16965.024>) and run `make data` to validate it. Automatic
  download is intentionally disabled — the script never fabricates data.

### AAV — adeno-associated virus capsid, 28-aa window

- Wild type `DEEEIRTTNPVATEQYGSVSTNLQRGNR` (measured fitness −0.918); **38,265 measured variants**.
- The campaign splits by Hamming distance: **cold start HD≤2 (10,433 variants)** stands for "already
  completed experiments"; **candidate pool HD>2 (27,832 variants)** is the unknown space the agent
  nominates from.
- **A setup fact worth stating explicitly:** the candidate pool's true maximum is **8.416205**, while
  the cold start already contains a higher incumbent, **9.536457** — the global optimum of the whole
  table sits at HD=2. Exactly **zero** pool candidates exceed it. So "the agent never beat the
  incumbent" is a property of the split, not an agent failure, and must not be reported as one.

## Fitness predictor

Three-level ladder with a shared `fit → predict(mean, var)` interface and a 5-seed deep ensemble for
uncertainty (`models/train_ladder.py`): one-hot + Ridge, gradient boosting, and an MLP; features are
one-hot (80-dim) or ESM-2 650M embeddings (1280-dim). Metrics: Spearman (primary), Pearson, MSE, Top-k
hit rate, plus an explicit `high_fitness_analysis.top_1pct_recall`.

| feature × split | Ridge | GBoost | MLP |
|---|---|---|---|
| one-hot × random | 0.484 | 0.474 | 0.389 |
| ESM-2 × random | 0.493 | 0.377 | 0.491 |
| one-hot × HD-extrapolation (train HD≤2 → test HD≥3) | 0.358 | 0.354 | 0.278 |
| ESM-2 × HD-extrapolation | 0.404 | 0.352 | **0.493** |

Spearman on a held-out set. On the harder HD-extrapolation split one-hot degrades sharply while ESM-2
generalises noticeably better — the main argument for a protein language model here. For AAV the
campaigns use a **pairwise-interaction (epistasis-aware) surrogate**, which moved the true peak's
predicted rank from #2,776 to #429 — additive features place it beyond any 288-nomination budget.

## Two agent lines

The repository contains **two independent agent architectures**. They share the event kernel and the
knowledge base but have no cross-imports, and they answer different questions.

### 1. Five-role workflow line — `agent/pipeline.py` + `evolution/campaign.py` (GB1)

A modular pipeline with Pydantic-validated I/O per role; the LLM is confined to two injectable ports,
everything else is deterministic and auditable:

1. **Data Analyst** — summarises per-site substitution fitness from the training pool.
2. **Hypothesis Generator** *(LLM port)* — proposes the substitutions worth combining; falls back to a
   deterministic top-k-per-site generator when no LLM is configured or a call fails.
3. **Mutation Designer** — enumerates a combinatorial library (≤1 substitution per site).
4. **Fitness Evaluator** — scores candidates with the predictor `(mean, var)`.
5. **Scientific Critic** *(LLM port + knowledge rules)* — validates/accepts/rejects with reasons; the
   `no_knowledge` switch disables the knowledge gate for ablation.

### 2. Autonomous researcher line — `agent/auto_researcher.py` (AAV)

A genuine tool-calling agent (pydantic-ai) that keeps `message_history` across rounds and decides for
itself what to call: `analyze_measured`, `predict`, `list_pool`, `compose_batch`, `redirect_batch`,
`check_knowledge`, `test_composed_batch`. It owns the acquisition ratio and — under the v0.9 contract
— a residue-level `exclude_motifs` entry point. This is the line the contract experiment runs on.

The LLM port uses an OpenAI-compatible pool via `agent/llm.py`, reading credentials from a local
`.env` (see `.env.example`; never committed). With no key or on any error it degrades to the
deterministic path, so **the project runs fully offline**; every round records whether it used the
live LLM or the fallback.

## Four-strategy campaign

`evolution/campaign.py` runs all four strategies under **one budget**, **one oracle** (measured-table
lookup, never a model score) and **one nomination space**. Three cold-start regimes evaluate difficulty
honestly:

- `--cold-start random` (**easy**): dense random seed pool (≈98% already HD≥3).
- `--cold-start low_hd` (**hard**, default recommended): seed only from HD≤2, extrapolate to HD≥3.
- `--cold-start low_hd --max-cold-hd 1` (**sparse**): seed from just the 77 single mutants.

Hard (HD≤2 extrapolation) regime, seed 42:

| strategy | cumulative max fitness | strong (≥4) | beneficial hits |
|---|---|---|---|
| random | 5.08 | 1 | 7 |
| greedy (Ridge, full-space) | 8.762 | 43 | 154 |
| agent (no knowledge) | **8.762** | **56** | **187** |
| knowledge agent (UCB + BLOSUM prior) | **8.762** | **57** | **190** |

**Honest finding:** GB1's 4-site landscape is itself *tractable* — even from only 77 single mutants,
model-based strategies reach the global optimum by round 2, while random stays far away. So "reaching
the peak" is not the discriminator; the meaningful differences are **sample efficiency** and **batch
yield**. The same saturation appears on AAV: all eight contract arms reached the pool's true maximum
by round 2 of 6, meaning **67% of the budget was spent after the answer was already found**. Halving
the per-round budget pushed that to round 4 (33% wasted) but did not remove it. **A saturated metric
has no discriminating power** — the campaigns therefore also report lethal-motif recurrence, which
does not saturate.

## Knowledge enhancement & auditable trails

`knowledge/` holds amino-acid properties, BLOSUM62 grading, mutation-count / stop-codon rules
(`rules.yaml`), validators, and a small `networkx` triple graph implementing
`has_property` / `occurs_at` / `contains` / `improves` / `changes_to`. The knowledge agent adds UCB
exploration (`mean + λ·√var`) plus a BLOSUM62 conservativeness prior; `--no-knowledge` ablates both.

`events/` is an append-only, chained-SHA-256 event log (+ SQLite projection + replay CLI): every
campaign step and agent tool call is recorded and `verify()`-able, including per-variant
nomination-time predictions and residuals (`campaign.oracle.residuals`,
`agent.tool.test.residuals`). Separately, **every experiment run** appends an immutable entry to the
master ledger [`harness/reports/experiment_log.jsonl`](harness/reports/experiment_log.jsonl)
(command, params, git commit, artifact SHA-256, summary).

**Honest scope note:** that ledger covers the main closed-loop experiments. It does not yet cover
every historical run — the `analysis-v0.1` line and some early `agentic` versions are not registered.
Treat it as a partial, append-only spine; each version folder's own `manifest.json` and per-run
`metrics.json` are authoritative for that run.

## Interactive dashboard

`app/demo.py` — a single-file **Streamlit** dashboard (read-only) with two top-level views.

**🔬 Experiment dashboard** — six tabs:

| tab | content | line |
|---|---|---|
| ① four-strategy comparison | cumulative top-10 true fitness under one budget, cold-start regime selector, optional multi-seed ±1σ band for random | GB1 |
| ② five-role reasoning replay | T4 event stream with in-page hash-chain verification, replayed per (strategy, round) | GB1 |
| ③ live playground | (a) score a variant (b) **enter a wild type and get an automatic one-round recommendation** | GB1 |
| ④ key-position concentration & combination rationales | per-strategy top-k residue distributions; the agent's combination rationales with measured single-position gains (`evidence_source` vs `narrative_source` kept separate — the deterministic fallback narrative is never presented as LLM reasoning) | GB1 |
| ⑤ mutation order · conservation · alpha sweep | single/double/multi-point comparison, ESM-2 per-position conservation (with its **negative result** stated), Ridge alpha sweep | ⑤-a AAV, rest GB1 |
| ⑥ agent tool contract | the v0.9 factorial: does changing the contract make the same model nominate differently — batch-divergence table, lethal-motif recurrence, and an audit of excluded motifs against injected evidence | AAV |

**🛰️ Research timeline** — how the system itself evolved: the cognitive turns per generation, the
evidence available at the time, and the conclusions that were later overturned.

Every panel degrades honestly: a missing artifact shows which file is absent and the exact command
that regenerates it — never a silent blank, never a crash.

```bash
streamlit run app/demo.py     # or: make demo
```

## Setup & run

For a clean Linux or macOS clone, the recommended first run is two commands:

```bash
./scripts/install.sh       # Python 3.11+, offline smoke/demo/test tier; no torch or data download
./scripts/run_all.sh       # always runs smoke; runs predictor + GB1 campaign when the CSV is present
```

The first command creates `.venv` and installs the same scientific stack used by the self-contained CI
tests, plus the offline agent runtime required by the smoke path. It deliberately does not install
PyTorch or download data. Use `./scripts/install.sh --full` to add PyTorch and fair-esm for local
ESM-2 extraction; the GB1 CSV remains a separate, explicit download described in
[`data/README.md`](data/README.md). `run_all.sh` prints a clear downgrade notice and finishes after
smoke when that CSV is absent.

Manual entry points:

```bash
# First command for a clean clone: no CSV, ESM cache, or API key required.
make smoke                                            # synthetic small landscape -> tmp/smoke/
make test                                             # self-contained tests (same set as CI)
make data                                             # validate a locally supplied full GB1 CSV
python -m models.evaluate_all                         # predictor ladder + standardisation ablation
python -m models.alpha_sweep                          # answer-agnostic alpha selection per feature
python -m evolution.campaign --cold-start low_hd      # GB1 four-strategy campaign (hard regime)
python -m agent.auto_researcher --dataset aav --guardrail \
    --surrogate epistasis --backtrack semi            # AAV autonomous researcher
scripts/run_v09_contract.sh tmp/v09 42                # the tool-contract 2x2 (4 arms, ~25 min)
python3 scripts/compare_v08_arms.py tmp/v09           # arm comparison: batch divergence + recurrence
streamlit run app/demo.py                             # interactive dashboard
cp .env.example .env                                  # optional: add an LLM pool key, then --use-llm
```

`make smoke` is the recommended first run. It executes the data → predictor → five-role agent →
four-strategy campaign path on a fixed, synthetic 16-variant landscape and writes a labelled CSV,
metrics, event stream, SQLite read projection, plot, and README to `tmp/smoke/`. It uses the offline
deterministic LLM fallback. **Its synthetic small-scale numbers are only a reproducibility
demonstration and must not be compared with the formal results.**

## Layout

```
data/             GB1/AAV loaders + validators, three-pool split, manifest
features/         one-hot and ESM-2 feature extraction (cached), conservation entropy
models/           predictor ladder + metrics + alpha sweep
agent/            five-role pipeline (GB1) and autonomous tool-calling researcher (AAV)
evolution/        mutation parsing, random baseline, four-strategy campaign, experiment ledger
knowledge/        mutation rules + knowledge graph + validators + ablation
events/           auditable event-stream kernel, residual reflexion
analysis/         read-only analyses (mutation order, ESM zero-shot scan)
app/              Streamlit dashboard (experiment view + research-timeline view)
scripts/          install, run_all, smoke, factorial runners, reference checker
reports/          report authoring tree (final-report-v0.x: markdown, figures, build, PDF)
harness/reports/  experiment artifacts, one folder per cycle + experiment ledger
tests/            unit tests (the CI set is self-contained: no CSV, no network, no API key)
```

## External resources

GB1 dataset (Wu et al. 2016 / *eLife*); AAV deep mutational scanning data; ESM-2 (`fair-esm`,
`esm2_t33_650M_UR50D`); scikit-learn / PyTorch. The LLM agent calls an OpenAI-compatible model pool
through an injectable port (credentials in a local, uncommitted `.env`); all external model/data use
is declared in the report.
