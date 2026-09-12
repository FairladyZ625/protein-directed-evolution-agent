"""Task-owned reproducible matrix; outputs stay in this report directory."""
import argparse
import hashlib
import json
import platform
import subprocess
import time
from pathlib import Path

import numpy as np
import scipy
import sklearn
from agent.auto_researcher import run_autoresearch, _gate_variants
from agent.llm import llm_config
from evolution.datasets import load, AAV_CSV
from events.store import EventStore
from knowledge.validators import load_rules
from models.train_ladder import EpistasisRidgePredictor

OUT = Path(__file__).resolve().parent

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')

def emit(**kw):
    print(json.dumps(kw, ensure_ascii=False), flush=True)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--modes', nargs='+', default=['mean','alternating','full','semi'])
    p.add_argument('--seeds', nargs='+', type=int, default=[42,0,7])
    p.add_argument('--controls', action='store_true')
    a=p.parse_args()
    spec=load('aav','one_hot')
    cfg=llm_config()
    manifest=dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        implementation_sha256=sha('agent/auto_researcher.py'), runner_sha256=sha(__file__),
        data_sha256=sha(AAV_CSV), python=platform.python_version(),numpy=np.__version__,
        scipy=scipy.__version__,sklearn=sklearn.__version__,
        llm_config=None if cfg is None else {k:v for k,v in cfg.items() if k!='api_key'},
        budget=48,n_rounds=6,seeds=a.seeds,modes=a.modes,
        pool=int((spec.df.hd>2).sum()),cold=int((spec.df.hd<=2).sum()),
        surrogate='EpistasisRidgePredictor defaults: fixed split random_state=0, three bootstrap models',
        seed_scope='Acquisition RNG only; cold-start and surrogate bootstrap seeds fixed; LLM randomness not seeded',
        guardrail={'max_hd':4,'blosum_min':0.0})
    dump(OUT/('manifest-'+ '-'.join(a.modes)+'.json'),manifest)
    for mode in a.modes:
        for seed in a.seeds:
            folder=OUT/'aav'/f'{mode}-seed{seed}'
            folder.mkdir(parents=True,exist_ok=True)
            if (folder/'metrics.json').exists():
                raise RuntimeError(f'refusing overwrite {folder}; every trial must be reported')
            store=EventStore(folder/'events.jsonl')
            t=time.monotonic()
            emit(kind='start',mode=mode,seed=seed)
            rep=run_autoresearch(spec,budget=48,n_rounds=6,seed=seed,event_store=store,
                llm=mode in ('full','semi'),backtrack=mode if mode in ('full','semi') else None,
                reference=mode if mode in ('mean','alternating') else 'mean',
                guardrail=True,max_hd=4,blosum_min=0.0,surrogate='epistasis')
            store.verify()
            assert [dict(event_type=e['event_type'],actor=e['actor'],payload=e['payload'])
                    for e in store.iter_events()]==rep['tool_trace']
            rep['evidence']={'events_verified':True,'events_sha256':sha(store.path),
                             'elapsed_seconds':round(time.monotonic()-t,2)}
            dump(folder/'metrics.json',rep)
            trace=rep['tool_trace']
            errors={kind:sum(e['event_type']==kind for e in trace) for kind in
                ['agent.tool.error','agent.llm.round_error','agent.llm.no_test','agent.llm.fallback']}
            emit(kind='result',mode=mode,seed=seed,summary=rep['summary'],
                 llm_used=rep['llm_used'],model=rep['agent_model'],spent=rep['budget_spent'],
                 errors=errors,seconds=rep['evidence']['elapsed_seconds'])
            assert rep['budget_spent']==288 and len(rep['rounds'])==6
            assert all(r['n_nominated']==48 for r in rep['rounds'])
    if a.controls:
        cold=spec.df[spec.df.hd<=2];pool=spec.df[spec.df.hd>2]
        X=spec.feature_fn(cold.seq.tolist());y=cold.fitness.to_numpy()
        fitted=EpistasisRidgePredictor().fit(X,y)
        mean,var=fitted.predict(spec.feature_fn(pool.seq.tolist()))
        b=load_rules()['blosum62']
        allowed,_=_gate_variants(pool.seq.tolist(),wt=spec.wt,max_hd=4,blosum_min=0.,
            blosum_fn=lambda w,c:b.get(w,{}).get(c,b.get(c,{}).get(w,0)))
        gates=set(allowed);seqs=pool.seq.tolist()
        eligible=np.array([i for i,s in enumerate(seqs) if s in gates])
        order=eligible[np.argsort(-mean[eligible],kind='stable')]
        # Post-hoc diagnostic: target identity only located after campaigns finish.
        target=pool.loc[pool.seq.isin(gates)].nlargest(1,'fitness').iloc[0]
        rank=next(r for r,i in enumerate(order,1) if seqs[i]==target.seq)
        shuffled=np.random.default_rng(42).permutation(y)
        null=EpistasisRidgePredictor().fit(X,shuffled)
        ctrl=dict(kind='controls',cv=fitted.val_spearman,shuffle_cv=null.val_spearman,
            shuffle_alpha=null._alpha,gate_pool_size=len(allowed),cold_max=float(y.max()),
            pool_peak=float(target.fitness),posthoc_peak_seq=target.seq,cold_peak_mean_rank=rank)
        dump(OUT/'controls.json',ctrl);emit(**ctrl)
        assert abs(null.val_spearman)<.1 and fitted.val_spearman>.8

if __name__=='__main__':main()
