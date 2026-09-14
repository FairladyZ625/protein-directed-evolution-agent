"""Post-hoc audit only; never imported by the acquisition runner."""
import json
from collections import Counter
from pathlib import Path
from events.store import EventStore

OUT=Path(__file__).resolve().parent
controls=json.loads((OUT/'controls.json').read_text())
peak=controls['pool_peak']
rows=[]
for p in sorted((OUT/'aav').glob('*/metrics.json')):
    if p.parent.name.startswith('pilot-'):
        continue
    rep=json.loads(p.read_text());trace=rep['tool_trace']
    store=EventStore(p.with_name('events.jsonl'));store.verify()
    acquisitions={e['payload']['round']:e['payload'] for e in trace if e['event_type']=='agent.acquisition'}
    fills={e['payload']['round']:i for i,e in enumerate(trace) if e['event_type']=='agent.llm.no_test'}
    acquisition_positions={e['payload']['round']:i for i,e in enumerate(trace) if e['event_type']=='agent.acquisition'}
    measurements={e['payload']['round']:e['payload'] for e in trace if e['event_type']=='agent.measurements'}
    assert len(acquisitions)==len(measurements)==6
    byround=[];seen=set();previous_history=[]
    for rnd,measurement in measurements.items():
        acq=acquisitions[rnd]
        audit={c['seq']:c for c in acq['candidates']}
        measured=dict(measurement['results'])
        assert len(measured)==48 and set(measured)==set(audit)
        assert not (set(measured)&seen)
        seen.update(measured)
        if rep['backtrack']=='semi':
            should_explore=(len(previous_history)>=3 and previous_history[-1]<=previous_history[-3])
            assert acq['forced']==should_explore
            if should_explore:
                assert acq['action']['n_exploit']==0 and acq['action']['n_explore']==48
            else:
                assert set(c['mean_rank'] for c in audit.values())==set(range(1,49))
        previous_history=measurement['top10_max_history']
        best=max(measured,key=measured.get)
        hits=[s for s,f in measured.items() if abs(f-peak)<1e-8]
        driver='llm' if rep['llm_used'] else 'deterministic'
        if rnd in fills:
            staged_by_harness=any(e['event_type'] in ('agent.tool.explore_batch','agent.tool.compose_batch')
                                  for e in trace[fills[rnd]+1:acquisition_positions[rnd]])
            driver=('harness_policy_fill' if staged_by_harness or not acq['action']
                    else 'harness_test_of_staged_batch')
        byround.append(dict(round=rnd,action=acq['action'],forced=acq['forced'],
            driver=driver,
            batch_best=measured[best],best_mean_rank=audit[best]['mean_rank'],
            peak_ranks=[audit[s]['mean_rank'] for s in hits],
            selected_mean_rank_max=max(c['mean_rank'] for c in audit.values()),
            rounds_since_improvement=measurement['rounds_since_improvement']))
    errors={k:sum(e['event_type']==k for e in trace) for k in
        ['agent.tool.error','agent.llm.round_error','agent.llm.no_test','agent.llm.fallback']}
    rows.append(dict(run=p.parent.name,seed=rep['seed'],mode=rep['backtrack'] or rep['reference'],
        curve=rep['summary']['cum_top10_max_curve'],max=rep['summary']['final_cum_top10_max'],
        strong=rep['summary']['final_cum_n_strong'],spent=rep['budget_spent'],
        hit_peak=any(r['peak_ranks'] for r in byround),llm_used=rep['llm_used'],model=rep['agent_model'],
        errors=errors,rounds=byround,events=len(trace),chain_verified=True))
(OUT/'matrix-summary-final.json').write_text(json.dumps(rows,indent=2)+'\n')
for r in rows:print(json.dumps(r))
