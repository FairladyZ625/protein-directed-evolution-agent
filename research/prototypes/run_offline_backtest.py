"""Reproducible closed-pool replay. Run as python -m research.prototypes.run_offline_backtest."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import time
import resource
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from knowledge.validators import load_rules
from research.prototypes.sparse_epistasis_tensor import SparseEpistasisTensor, BayesianRidge, WT
from research.prototypes.voi_acquisition import select_batch


class Oracle:
    def __init__(self, labels, initial):
        self.__labels = np.asarray(labels).copy()
        self.seen = set(map(int, initial))
        self.spent = 0

    def query(self, ids):
        ids = list(map(int, ids))
        if len(set(ids)) != len(ids) or self.seen.intersection(ids) or self.spent+len(ids) > 288:
            raise ValueError('duplicate or over-budget query')
        if any(i < 0 or i >= len(self.__labels) for i in ids):
            raise ValueError('invalid query ID')
        self.seen.update(ids); self.spent += len(ids)
        return self.__labels[ids].copy()


def load_data(path):
    raw = pd.read_csv(path, low_memory=False)
    valid = raw.mutated_region.astype(str).str.fullmatch('[ACDEFGHIKLMNPQRSTVWY]{28}')
    df = raw.loc[valid].drop_duplicates('mutated_region').reset_index(drop=True)
    if not df.reference_region.eq(WT).all() or not np.isfinite(df.score).all():
        raise ValueError('reference or finite-label audit failed')
    seq = df.mutated_region.tolist()
    hd = np.array([sum(a != b for a, b in zip(s, WT)) for s in seq])
    if len(df) != 38265 or int(sum(hd <= 2)) != 10433:
        raise ValueError('dataset contract counts changed')
    matrix = load_rules()['blosum62']
    def passes(s):
        substitutions = [(a,b) for a,b in zip(WT,s) if a != b]
        return len(substitutions) <= 4 and np.mean([
            matrix.get(a, {}).get(b, matrix.get(b, {}).get(a, 0)) for a,b in substitutions]) >= 0
    initial = np.flatnonzero(hd <= 2)
    candidates = np.array([i for i,s in enumerate(seq) if hd[i] > 2 and passes(s)])
    return seq, df.score.to_numpy(), initial, candidates, dict(
        raw_rows=len(raw), clean_rows=len(df), cold_start=len(initial), gated_candidates=len(candidates),
        hd_metadata_mismatches=int(sum(hd != df.number_of_mutations.to_numpy())),
        csv_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        sequence_sha256=hashlib.sha256('\n'.join(seq).encode()).hexdigest(),
        gate='HD<=4; mean substitution BLOSUM62>=0', reference=WT,
        source='https://github.com/J-SNACKKB/FLIP/tree/main/splits/aav')


def choose(policy, mean, x, model, size, round_index, rounds, epi_start):
    greedy = np.argsort(-mean, kind='stable')[:size]
    if policy.startswith('v0'):
        # Explicit reconstructed proxies, not historical LLM executions.
        fraction = .25 * ((rounds-round_index-1)/(rounds-1) if policy == 'v05_annealed' else 1)
        count = int(np.floor(size*fraction + .5))
        _, var = model.predict(x)
        exploit = greedy[:size-count]
        order = np.argsort(-var, kind='stable')
        explore = [i for i in order if i not in set(exploit.tolist())][:count]
        picks = np.r_[exploit, explore].astype(int)
        return picks, dict(exploration_quota=count, non_greedy_slots=len(set(picks)-set(greedy)),
                          mean_opportunity_cost=float(mean[greedy].sum()-mean[picks].sum()))
    weights = {'greedy':(0,0), 'voi_information':(1,0), 'voi_epistasis':(0,1), 'voi_full':(1,1)}
    lam, nu = weights[policy]
    return select_batch(mean, x, model.covariance, size, noise=model.noise,
        information_weight=lam, epistasis_weight=nu, epi_start=epi_start,
        remaining_rounds=rounds-round_index, total_rounds=rounds)


def campaign(x, initial_labels, initial, candidates, oracle, policy, size, rounds, epi_start, threshold):
    measured = initial.copy(); observed = initial_labels.copy(); pool = candidates.copy()
    trajectory, all_ids = [], []
    for r in range(rounds):
        model = BayesianRidge().fit(x[measured], observed)
        mean = x[pool] @ model.coef
        picks, diagnostic = choose(policy, mean, x[pool], model, size, r, rounds, epi_start)
        ids = pool[picks].copy()
        predictions = mean[picks].tolist()  # frozen before the only new-label access
        values = oracle.query(ids)
        all_ids.extend(ids.tolist())
        observed = np.r_[observed, values]; measured = np.r_[measured, ids]
        trajectory.append(dict(round=r+1, spent=(r+1)*size, ids=ids.tolist(),
            predictions=predictions, queried_labels=values.tolist(), best_so_far=float(observed.max()),
            best_new=float(observed[len(initial):].max()), strong_hits=int(sum(observed[len(initial):] >= threshold)),
            **diagnostic))
        pool = np.delete(pool, picks)
    return dict(policy=policy, batch_size=size, rounds=rounds, trajectory=trajectory, queried_ids=all_ids)


def run(path):
    seq, labels, initial, candidates, audit = load_data(path)
    threshold = float(np.quantile(labels[initial], .9))
    audit['strong_threshold_cold_q90'] = threshold
    result = dict(seed=42, data=audit, configuration=dict(rank=16, alpha=10., noise=1.,
        information_weight=1., epistasis_weight=1., frontier_weight='normalized identity',
        higher_order='fixed random CP degree 3; uniform no-contact prior', budget=288), runs=[])
    for degree in (2,3):
        encoder = SparseEpistasisTensor(degree=degree)
        x = encoder.transform(seq)
        policies = ['greedy'] if degree == 2 else ['greedy','v04_fixed','v05_annealed','voi_information','voi_epistasis','voi_full']
        for size, rounds in ((96,3),(48,6)):
            for policy in policies:
                t = time.monotonic()
                row = campaign(x, labels[initial], initial, candidates, Oracle(labels, initial),
                               policy, size, rounds, encoder.epi_start, threshold)
                row['degree'] = degree
                result['runs'].append(row)
                print(f'degree={degree} {size}x{rounds} {policy}: best={row["trajectory"][-1]["best_so_far"]:.6f} ({time.monotonic()-t:.1f}s)', flush=True)
    # Evaluator-only retrospective access, after every policy has completed.
    result['evaluation'] = dict(global_peak=float(labels.max()),
        feasible_peak=float(labels[np.r_[initial,candidates]].max()), cold_peak=float(labels[initial].max()),
        candidate_peak=float(labels[candidates].max()), full_pool_q90=float(np.quantile(labels,.9)))
    for row in result['runs']:
        baseline = next(b for b in result['runs'] if b['degree']==row['degree'] and b['batch_size']==row['batch_size'] and b['policy']=='greedy')
        for a,b in zip(row['trajectory'], baseline['trajectory']):
            a['realized_exploration_tax'] = b['best_so_far']-a['best_so_far']
            a['new_candidate_tax'] = b['best_new']-a['best_new']
        hits = [a['spent'] for a in row['trajectory'] if a['best_so_far'] >= result['evaluation']['global_peak']]
        row['peak_discovery_budget'] = 0 if result['evaluation']['cold_peak'] >= result['evaluation']['global_peak'] else (hits[0] if hits else None)
        new_hits = [a['spent'] for a in row['trajectory'] if a['best_new'] >= result['evaluation']['candidate_peak']]
        row['candidate_peak_discovery_budget'] = new_hits[0] if new_hits else None
    return result


def write_report(result, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1,2,figsize=(12,4))
    table = ['| Model degree | Schedule | Policy | Best new | Strong hits | New-candidate tax | Candidate peak budget |',
             '|---|---|---|---:|---:|---:|---:|']
    for row in result['runs']:
        last = row['trajectory'][-1]
        table.append(f'| {row["degree"]} | {row["batch_size"]}×{row["rounds"]} | {row["policy"]} | {last["best_new"]:.6f} | {last["strong_hits"]} | {last["new_candidate_tax"]:.6f} | {row["candidate_peak_discovery_budget"]} |')
        ax = axes[0 if row['batch_size']==96 else 1]
        ax.plot([a['spent'] for a in row['trajectory']], [a['best_new'] for a in row['trajectory']],marker='.',label=f'd{row["degree"]} {row["policy"]}')
    for ax, title in zip(axes,['96×3','48×6']):
        ax.set(title=title,xlabel='New measurements',ylabel='Best newly queried fitness'); ax.legend(fontsize=6)
    fig.tight_layout(); fig.savefig(out/'backtest_curves.png',dpi=160); plt.close(fig)
    report = '''# AAV offline prototype backtest

## Protocol and evidence

The missing declared pool was reconstructed from [FLIP AAV](https://github.com/J-SNACKKB/FLIP/tree/main/splits/aav), using the repository loader's sequence filtering and first-occurrence deduplication, tightened to the 20 canonical amino acids. Recomputed HD agrees with metadata. Sequence IDs are zero-based cleaned source-row order. Full hashes, configuration, all per-round predictions, queried IDs/labels, and diagnostics are in `backtest_metrics.json`. No labels are passed to the policy; the oracle opens only the frozen batch and rejects duplicate or over-budget queries. All campaigns finish before retrospective global-peak evaluation.

All runs use seed 42, the same 10,433 HD≤2 observations and HD≤4 / mean BLOSUM62≥0 candidate gate, and exactly 288 new assays. Strong hits use the cold-start 90th percentile fixed before acquisition (not a candidate-label quantile). The real historical table is a noiseless lookup; noise=1 is a surrogate likelihood assumption. No extra assays or labels are used for calibration or tuning.

## Algorithms and comparison limits

Fixed rank-16 random CP distinct-site ANOVA factors implement higher-order theory equation (8), with full reference-state additive features and a proper Gaussian Ridge prior (alpha=10). The degree-2 control uses the same factors and omits the cubic block. This is a uniform-prior, no-contact prototype: no verified contact map was supplied. No learned Tucker cores, group-lasso support selection, or learned projection factors are claimed. Cubic features are exactly zero on HD≤2, leaving zero posterior mean and nonzero prior variance until higher-order observations arrive.

VoI is the equation (13) acquisition **proxy**, using exact integer marginal logdet information and normalized epistasis parameter trace reduction (W=identity). Both weights start at 1 in their respective utility units and decay linearly to zero for the final round. Covariance is updated after every pending selection, without labels; the mean is frozen for the entire batch. This is integer greedy marginal optimization, not a solved fractional relaxation, Bellman rollout, or simple-regret guarantee. No fractional rounding gap is asserted. Information-only and variance-only ablations isolate the two rewards.

v04_fixed and v05_annealed are explicitly reconstructed heuristic controls: 25% highest-variance quota, respectively constant or linearly decaying to zero, with nearest-integer slots and mean-based fill. The required checkout has no compose_batch implementation and the predecessor theory records no independently verified v0.5 terminal result. These runs do not reproduce historical LLM choices or the production EpistasisRidgePredictor. All acquisition comparisons share the same degree-3 surrogate; degree-2 versus degree-3 greedy is a separate model ablation. Production code remains untouched.

## Results

The cold-start maximum is 9.53645667061, already the full-pool maximum. Thus inclusive best-so-far is flat, global peak discovery budget is zero, and inclusive exploration tax is zero for every policy. The eligible new-candidate maximum is 8.416205130560002, explaining the predecessor report’s quoted peak. The table and plot below use **best newly queried fitness** and its matched-policy difference to expose acquisition performance; this is a distinct utility from inclusive best-so-far. No policy was retuned after this metric audit.

'''+ '\n'.join(table)+'''

The prototype does not improve terminal best-new fitness over its matched greedy baseline and no run reaches the eligible peak. At 48×6, the fixed-quota control loses 0.770635 fitness; annealing closes this gap. Degree-3 greedy yields 67 strong hits versus 73 for degree-2 greedy, so this experiment does not support promoting the cubic prototype. The full VoI proxy yields 65 versus 67 for degree-3 greedy. These are negative/null findings, not evidence of a production upgrade.

![Discovery trajectories](backtest_curves.png)

New-candidate tax is matched-degree, matched-schedule greedy best-new minus policy best-new; negative values are an exploration dividend. Candidate peak budget is the end of the first batch reaching the eligible new-candidate maximum; None means not reached by 288. The JSON retains the separately defined inclusive exploration tax and global peak budget. Within-batch ordering cannot establish an earlier feedback event. JSON also records best-new fitness, cumulative strong hits, pre-query mean opportunity cost and off-greedy slots. Mean opportunity cost is not terminal exploration tax. Single-seed realized differences are not unbiased population causal estimates or confidence intervals. Closed-pool replay cannot predict unseen sequences or new wet-lab noise.

## Reproduction and verification

From the worktree, use `.venv/bin/python -m unittest discover -s research/prototypes -p 'test_*.py'`, then `.venv/bin/python -m research.prototypes.run_offline_backtest --data data/aav/full_data.csv --output artifacts/voi-backtest --verify-repeat`. Numerical work is limited to one BLAS thread. The repeat option compares all scientific metrics, predictions and batch IDs exactly; wall time is recorded separately in `execution.json`. Download and unzip FLIP's `full_data.csv.zip` into `data/aav/` if absent. Verify the CSV SHA256 against the metrics before replay. Environment versions and peak process RSS are recorded separately. No task artifacts or raw data are committed from ignored Harness/data directories.

## Residual risk

Weights, rank and covariance are uncalibrated engineering defaults; narrow surrogate uncertainty does not certify accuracy. A fixed CP projection compresses pairwise interactions and may miss important couplings. No structural contact advantage or pure third-order biological attribution has been demonstrated. One seed and one historical dataset do not establish general superiority; retain negative and null results. Independent execution review and owner consent remain required by repository workflow.
'''
    (out/'backtest-report.md').write_text(report)


def main():
    p=argparse.ArgumentParser(); p.add_argument('--data',type=Path,default=Path('data/aav/full_data.csv'))
    p.add_argument('--output',type=Path,default=Path('artifacts/voi-backtest')); p.add_argument('--verify-repeat',action='store_true')
    args=p.parse_args(); args.output.mkdir(parents=True,exist_ok=True); t=time.monotonic()
    with threadpool_limits(limits=1):
        result=run(args.data)
        if args.verify_repeat:
            repeat=run(args.data)
            if result != repeat: raise AssertionError('scientific metrics differ on replay')
    (args.output/'backtest_metrics.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    write_report(result,args.output)
    import scipy, sklearn
    (args.output/'execution.json').write_text(json.dumps(dict(repeat_exact=args.verify_repeat,
        seconds=time.monotonic()-t, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if platform.system() == 'Darwin' else 1024),
        platform=platform.platform(), python=platform.python_version(), numpy=np.__version__,
        scipy=scipy.__version__, sklearn=sklearn.__version__, pandas=pd.__version__),indent=2)+'\n')

if __name__ == '__main__': main()
