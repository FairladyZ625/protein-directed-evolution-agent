"""Reconstruct every nomination from saved pre-measurement predictions and RNG."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

from evolution.datasets import load
from evolution.pool_campaign import _blosum_lookup
from agent.auto_researcher import _gate_variants

OUT = Path(__file__).resolve().parent
module = importlib.util.spec_from_file_location('multiseed', OUT/'run.py')
runner = importlib.util.module_from_spec(module)
module.loader.exec_module(runner)
spec = load('aav', 'one_hot')
seqs = spec.df.seq.to_numpy()
truth = spec.df.fitness.to_numpy()
cold = np.flatnonzero(spec.df.hd.to_numpy() <= 2)
pool = np.flatnonzero(spec.df.hd.to_numpy() > 2)
allowed, _ = _gate_variants(seqs[pool], wt=spec.wt, max_hd=4,
                           blosum_min=0., blosum_fn=_blosum_lookup())
gate = np.isin(seqs, allowed)
rounds = 0
for path in sorted((OUT/'trials').glob('*.json')):
    row = json.loads(path.read_text())
    rng = np.random.default_rng(row['seed'])
    measured, remaining = cold.copy(), pool.copy()
    for rnd, record in enumerate(row['rounds']):
        key = hashlib.sha256(np.asarray(measured, dtype=np.int64).tobytes()).hexdigest()
        with np.load(OUT/'cache'/f'{key}.npz') as z:
            picks = runner.select(row['method'], rnd, z['mean'], z['var'], gate[remaining], rng)
            ids = remaining[np.sort(picks)]
            np.testing.assert_array_equal(ids, record['row_ids'])
            np.testing.assert_array_equal(z['mean'][np.sort(picks)], record['predicted_mean'])
            np.testing.assert_array_equal(z['var'][np.sort(picks)], record['predicted_var'])
            assert record['cv'] == float(z['cv']) and record['alpha'] == float(z['alpha'])
        np.testing.assert_array_equal(truth[ids], record['measured_fitness'])
        assert len(ids) == 48 and gate[ids].all() and not np.isin(ids, measured).any()
        measured = np.concatenate([measured, ids])
        remaining = remaining[~np.isin(remaining, ids)]
        rounds += 1
assert rounds == 1260
print(json.dumps(dict(verified_rounds=rounds, verified_nominations=rounds*48,
                      all_candidates_reconstructed_from_predictions_and_rng=True,
                      oracle_labels_checked_after_nomination=True)))
