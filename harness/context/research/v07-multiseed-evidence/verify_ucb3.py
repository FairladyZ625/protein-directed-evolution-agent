"""Fresh, uncached DataFrame replay of the positive UCB beta=3 result."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from agent.auto_researcher import _gate_variants
from evolution.datasets import load
from evolution.pool_campaign import _blosum_lookup
from models.train_ladder import EpistasisRidgePredictor

P = Path(__file__).resolve().parent
with threadpool_limits(limits=1):
    spec = load('aav', 'one_hot')
    measured = spec.df[spec.df.hd <= 2].copy()
    pool = spec.df[spec.df.hd > 2].copy()
    allowed, _ = _gate_variants(pool.seq, wt=spec.wt, max_hd=4,
                               blosum_min=0., blosum_fn=_blosum_lookup())
    allowed = set(allowed)
    saved = json.loads((P/'trials/ucb3-00.json').read_text())
    acquired = []
    for rnd in range(6):
        model = EpistasisRidgePredictor().fit(
            spec.feature_fn(measured.seq.tolist()), measured.fitness.to_numpy())
        mu, var = model.predict(spec.feature_fn(pool.seq.tolist()))
        ranked = np.argsort(-(mu + 3.0*np.sqrt(np.maximum(var, 0))))
        ranked = [i for i in ranked if pool.iloc[i].seq in allowed][:48]
        candidates = pool.iloc[ranked].seq.tolist()
        batch = pool[pool.seq.isin(candidates)].copy()
        assert batch.index.tolist() == saved['rounds'][rnd]['row_ids']
        assert batch.fitness.tolist() == saved['rounds'][rnd]['measured_fitness']
        acquired.extend(batch.fitness.tolist())
        measured = pd.concat([measured, batch], ignore_index=True)
        pool = pool.drop(batch.index)
        print(json.dumps(dict(round=rnd+1, exact_batch_match=True,
                              cum_max=max(acquired))), flush=True)
    result = dict(uncached_replay=True, matched_batches=6, matched_candidates=288,
                  maximum=max(acquired),
                  strong=int(sum(v >= np.quantile(spec.df.fitness, .9) for v in acquired)))
    (P/'ucb3-uncached-verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)
