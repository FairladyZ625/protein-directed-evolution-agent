"""Concurrent scheduling of a still-unstarted registered trial; no policy changes."""
import json
import sys
import time
from pathlib import Path

from run_matrix import OUT, dump, emit, sha
from agent.auto_researcher import run_autoresearch
from evolution.datasets import load
from events.store import EventStore

mode, seed = sys.argv[1], int(sys.argv[2])
assert mode in ('full', 'semi') and seed in (42, 0, 7)
folder=OUT/'aav'/f'{mode}-seed{seed}'
folder.mkdir(parents=True, exist_ok=False)
# An explicit INCOMPLETE claim prevents the older serial scheduler from duplicating
# this live trial. It is replaced by real metrics only after all six rounds verify.
dump(folder/'metrics.json', {'status':'running','complete':False,'mode':mode,'seed':seed})
dump(folder/'scheduler.json', {'mode':mode,'seed':seed,'source_sha256':sha('agent/auto_researcher.py'),
    'runner_sha256':sha(__file__),'no_retries':True})
store=EventStore(folder/'events.jsonl');spec=load('aav','one_hot');start=time.monotonic()
emit(kind='start',mode=mode,seed=seed)
rep=run_autoresearch(spec,budget=48,n_rounds=6,seed=seed,event_store=store,
    llm=True,backtrack=mode,reference='mean',guardrail=True,max_hd=4,blosum_min=0.,surrogate='epistasis')
store.verify()
assert [dict(event_type=e['event_type'],actor=e['actor'],payload=e['payload'])
    for e in store.iter_events()]==rep['tool_trace']
assert rep['budget_spent']==288 and len(rep['rounds'])==6
assert all(r['n_nominated']==48 for r in rep['rounds'])
rep['evidence']={'events_verified':True,'events_sha256':sha(store.path),
                'elapsed_seconds':round(time.monotonic()-start,2)}
dump(folder/'metrics.json',rep)
emit(kind='result',mode=mode,seed=seed,summary=rep['summary'],model=rep['agent_model'],
    llm_used=rep['llm_used'],spent=rep['budget_spent'],seconds=rep['evidence']['elapsed_seconds'],
    errors={k:sum(e['event_type']==k for e in rep['tool_trace']) for k in
            ['agent.tool.error','agent.llm.round_error','agent.llm.no_test','agent.llm.fallback']})
