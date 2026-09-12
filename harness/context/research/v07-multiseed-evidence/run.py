"""Read-only product analysis. Run from repository root with PYTHONPATH=.

Only acquisition RNG varies across seeds. No oracle labels enter select().
Predictions are memoized by ordered measured row IDs (same fixed model).
"""
import argparse
import hashlib
import json
import platform
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import scipy
import sklearn
from scipy.stats import binomtest, norm
from threadpoolctl import threadpool_limits

from agent.auto_researcher import _gate_variants, run_autoresearch
from evolution.datasets import AAV_CSV, load
from evolution.pool_campaign import _blosum_lookup
from models.train_ladder import EpistasisRidgePredictor

OUT = Path(__file__).resolve().parent
METHODS = ('mean', 'alternating', 'ucb0.5', 'ucb1', 'ucb2', 'ucb3', 'thompson_gaussian')


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def emit(**obj):
    print(json.dumps(obj), flush=True)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def select(method, rnd, mean, var, eligible, rng):
    """Pure acquisition: predictions + gate only; no labels or peak identity."""
    sd = np.sqrt(np.maximum(var, 0))
    if method == 'mean' or (method == 'alternating' and rnd % 2 == 0):
        score = mean
    elif method == 'alternating':
        score = mean + 3 * sd + rng.random(len(mean))
    elif method.startswith('ucb'):
        score = mean + float(method[3:]) * sd
    elif method == 'thompson_gaussian':
        # Marginal Gaussian approximation, NOT a correlated posterior function draw.
        score = mean + sd * rng.standard_normal(len(mean))
    else:
        raise ValueError(method)
    order = np.argsort(-score)  # match legacy list_pool, including tie policy
    return order[eligible[order]][:48]


def wilson(k, n):
    z = norm.ppf(.975)
    p = k / n
    center = (p + z*z/(2*n))/(1+z*z/n)
    radius = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/(1+z*z/n)
    return [float(max(0, center-radius)), float(min(1, center+radius))]


def distribution(values):
    x = np.asarray(values)
    vals, counts = np.unique(x, return_counts=True)
    return dict(mean=float(x.mean()), sd=float(x.std(ddof=1)),
                quantiles=np.quantile(x, [0, .25, .5, .75, 1]).tolist(),
                frequencies=[dict(value=float(v), count=int(c)) for v, c in zip(vals, counts)])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--worker', type=int)
    args = parser.parse_args()
    start = time.monotonic()
    spec = load('aav', 'one_hot')
    seqs = spec.df.seq.to_numpy()
    y = spec.df.fitness.to_numpy()
    cold = np.flatnonzero(spec.df.hd.to_numpy() <= 2)
    pool = np.flatnonzero(spec.df.hd.to_numpy() > 2)
    allowed, _ = _gate_variants(seqs[pool], wt=spec.wt, max_hd=4,
                               blosum_min=0., blosum_fn=_blosum_lookup())
    gate = np.isin(seqs, allowed)
    assert (len(cold), len(pool), int(gate.sum())) == (10433, 27832, 9533)
    assert len(set(seqs)) == len(seqs) and np.isfinite(y).all()
    X = spec.feature_fn(seqs.tolist())
    files = ['agent/auto_researcher.py', 'models/train_ladder.py',
             'evolution/datasets.py', 'evolution/pool_campaign.py', 'knowledge/validators.py',
             str(AAV_CSV), str(Path(__file__).relative_to(Path.cwd()))]
    manifest = dict(hashes={p: sha(p) for p in files}, python=platform.python_version(),
                    numpy=np.__version__, scipy=scipy.__version__, sklearn=sklearn.__version__,
                    commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                    methods=METHODS, seeds=list(range(30)), rounds=6, batch=48,
                    cold=len(cold), pool=len(pool), gate=int(gate.sum()),
                    seed_scope='acquisition only; CV split 0 and bootstrap 0,1,2 fixed',
                    thompson='independent marginal Normal(mean,var) approximation',
                    inference='exact one-sided p>1/3; Holm across two stochastic methods; deterministic repeats descriptive only')
    if args.verify_only or args.worker is not None:
        old = json.loads((OUT/'manifest.json').read_text())
        assert old['hashes'] == manifest['hashes'], 'source/data changed'
    else:
        if (OUT/'manifest.json').exists():
            raise RuntimeError('Use a fresh output directory; refusing overwrite')
        dump(OUT/'manifest.json', manifest)
    cache = {}
    fits = 0
    (OUT/'cache').mkdir(exist_ok=True)

    def scores(measured, remaining):
        nonlocal fits
        key = hashlib.sha256(np.asarray(measured, dtype=np.int64).tobytes()).hexdigest()
        if key not in cache:
            file = OUT/'cache'/f'{key}.npz'
            if file.exists():
                with np.load(file) as z:
                    cache[key] = (z['mean'], z['var'], float(z['cv']), float(z['alpha']))
            else:
                t = time.monotonic()
                model = EpistasisRidgePredictor().fit(X[measured], y[measured])
                mean, var = model.predict(X[remaining])
                cache[key] = (mean, var, float(model.val_spearman), float(model._alpha))
                temp = file.with_suffix(f'.{os.getpid()}.npz')
                np.savez(temp, mean=mean, var=var, cv=model.val_spearman, alpha=model._alpha)
                os.replace(temp, file)
                fits += 1
                emit(kind='fit', fit=fits, n=len(measured), seconds=round(time.monotonic()-t, 2))
        return cache[key]

    def campaign(method, seed):
        measured, remaining = cold.copy(), pool.copy()
        rng = np.random.default_rng(seed)
        rounds = []
        for rnd in range(6):
            mean, var, cv, alpha = scores(measured, remaining)
            picks = select(method, rnd, mean, var, gate[remaining], rng)
            # Production test() appends rows in POOL order, not acquisition rank order.
            batch = remaining[np.sort(picks)]
            assert len(batch) == len(set(batch)) == 48 and gate[batch].all()
            rounds.append(dict(round=rnd+1, row_ids=batch.tolist(),
                               predicted_mean=mean[np.sort(picks)].tolist(),
                               predicted_var=var[np.sort(picks)].tolist(), cv=cv, alpha=alpha,
                               measured_fitness=y[batch].tolist()))
            # Oracle lookup only after nomination; no unmeasured label enters next fit.
            measured = np.concatenate([measured, batch])
            remaining = remaining[~np.isin(remaining, batch)]
        return dict(method=method, seed=seed, rounds=rounds)

    def audit(row):
        ids = np.array([i for r in row['rounds'] for i in r['row_ids']])
        assert len(ids) == len(set(ids)) == 288 and gate[ids].all()
        assert not np.isin(ids, cold).any()
        for r in row['rounds']:
            assert len(r['row_ids']) == 48
            np.testing.assert_array_equal(r['measured_fitness'], y[r['row_ids']])
        # Evaluation boundary: target discovered from oracle AFTER acquisition ends.
        peak = y[pool].max()
        threshold = float(np.quantile(y, .9))  # existing all-clean-data strong definition
        return dict(method=row['method'], seed=row['seed'],
                    peak_hit=bool(np.any(y[ids] == peak)),
                    cum_top10_max=float(y[ids].max()), strong=int((y[ids] >= threshold).sum()),
                    max_curve=[float(y[ids[:48*(r+1)]].max()) for r in range(6)],
                    selection_hash=hashlib.sha256(ids.tobytes()).hexdigest())

    if args.worker is not None:
        for method in METHODS:
            for seed in range(30):
                stochastic = method in ('alternating', 'thompson_gaussian')
                owner = seed % 3 if stochastic else 0
                if owner != args.worker:
                    continue
                row = campaign(method, seed)
                dump(OUT/'trials'/f'{method}-{seed:02d}.json', row)
                emit(kind='result', **audit(row))
        emit(kind='worker_done', worker=args.worker, fits=fits)
        return
    if args.verify_only:
        rows = [json.loads(p.read_text()) for p in sorted((OUT/'trials').glob('*.json'))]
    else:
        (OUT/'trials').mkdir()
        # Fixed 3 single-thread processes, solely a scheduling change.
        scores(cold, pool)
        workers = []
        for index in range(3):
            log = (OUT/f'worker-{index}.log').open('w')
            proc = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--worker', str(index)],
                                    stdout=log, stderr=subprocess.STDOUT)
            workers.append((proc, log))
        for proc, log in workers:
            assert proc.wait() == 0, f'worker failed: {proc.pid}'
            log.close()
        rows = [json.loads(p.read_text()) for p in sorted((OUT/'trials').glob('*.json'))]
    assert len(rows) == 210
    results = [audit(row) for row in rows]
    summary = {}
    for method in METHODS:
        rs = sorted([r for r in results if r['method'] == method], key=lambda r:r['seed'])
        assert [r['seed'] for r in rs] == list(range(30))
        k = sum(r['peak_hit'] for r in rs)
        summary[method] = dict(hits=k, n=30, rate=k/30, wilson95=wilson(k, 30),
                               unique_trajectories=len(set(r['selection_hash'] for r in rs)),
                               maximum=distribution([r['cum_top10_max'] for r in rs]),
                               strong=distribution([r['strong'] for r in rs]))
        if method in ('alternating', 'thompson_gaussian'):
            summary[method]['p_greater_one_third'] = binomtest(k, 30, 1/3, alternative='greater').pvalue
    ps = sorted((summary[m]['p_greater_one_third'], m) for m in ('alternating', 'thompson_gaussian'))
    prev = 0.
    for i, (p, m) in enumerate(ps):
        prev = max(prev, min(1., (2-i)*p))
        summary[m]['p_holm'] = prev
    greedy = {r['seed']:r['strong'] for r in results if r['method'] == 'mean'}
    for method in METHODS[1:]:
        delta = [greedy[r['seed']]-r['strong'] for r in results if r['method'] == method]
        wins, losses = sum(d>0 for d in delta), sum(d<0 for d in delta)
        summary[method]['greedy_strong_comparison'] = dict(
            delta=distribution(delta), wins=wins, ties=30-wins-losses, losses=losses,
            sign_test_p=(binomtest(wins, wins+losses, .5, alternative='greater').pvalue
                         if method in ('alternating', 'thompson_gaussian') and wins+losses else None))
    for method in ('mean', 'ucb0.5', 'ucb1', 'ucb2', 'ucb3'):
        assert summary[method]['unique_trajectories'] == 1
    if not args.verify_only:
        # Positive/negative control, and independently replay the unmodified product fallback.
        original = EpistasisRidgePredictor().fit(X[cold], y[cold])
        shuffled = EpistasisRidgePredictor().fit(X[cold], np.random.default_rng(42).permutation(y[cold]))
        assert original.val_spearman > .8 and abs(shuffled.val_spearman) < .1
        reference = run_autoresearch(spec, budget=48, n_rounds=6, seed=42, llm=False,
                                    guardrail=True, max_hd=4, blosum_min=0., surrogate='epistasis')
        replay = campaign('alternating', 42)
        replay_eval = audit(replay)
        assert [round(v,4) for v in replay_eval['max_curve']] == [r['cum_top10_max'] for r in reference['rounds']]
        assert replay_eval['strong'] == reference['rounds'][-1]['cum_n_strong']
        for own, ref in zip(replay['rounds'], reference['rounds']):
            own_top = sorted(zip(own['row_ids'], own['measured_fitness']), key=lambda t:-t[1])[:10]
            assert [[seqs[i],round(v,4)] for i,v in own_top] == ref['top10']
        dump(OUT/'reference-seed42.json', dict(replay=replay, product=reference))
        controls = dict(cv=original.val_spearman, shuffle_cv=shuffled.val_spearman,
                        legacy_replay_top10_and_metrics=True, reference_seed42=replay_eval,
                        source_unchanged=all(sha(p)==h for p,h in manifest['hashes'].items()))
        assert controls['source_unchanged']
        dump(OUT/'controls.json', controls)
        dump(OUT/'summary.json', summary)
        dump(OUT/'results.json', results)
    else:
        assert summary == json.loads((OUT/'summary.json').read_text())
    emit(kind='summary', methods=summary)
    emit(kind='verified', trials=len(rows), nominations=len(rows)*288,
         unique_fits=fits, seconds=round(time.monotonic()-start,2))


if __name__ == '__main__':
    with threadpool_limits(limits=1):
        main()
