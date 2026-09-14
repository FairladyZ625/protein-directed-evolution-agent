from pathlib import Path
import json,hashlib,subprocess,gzip
# WARNING: this script regenerates only the BASE snapshot set. evidence/sources.json has
# been extended incrementally since (v0.9 contract evidence, 12x6 runs, supplied documents:
# 114 entries vs the 36 produced here), so running it wholesale TRUNCATES the manifest and
# verify.py then checks a fraction of the sources. Refresh individual entries in place
# instead, or re-add the missing sections before writing sources.json.
ROOT=Path(__file__).resolve().parents[1];repo=ROOT.parents[1];main=Path('/Users/lizeyu/Projects/ai4s-directed-evolution-agent'); paths={}
for reg in ['easy','hard','sparse','llm']:paths[f'gb1_{reg}.json']=f'lab/reports/workflow-v1.1/gb1/campaign_{reg}.metrics.json'
paths.update({'alpha.json':'lab/reports/workflow-v1.0/gb1/predictor_alpha_sweep.json','scaling.json':'lab/reports/workflow-v1.0/gb1/predictor_ladder_scaling_ablation.json','predictors.json':'lab/reports/workflow-v1.1/gb1/predictor_metrics.json','knowledge_components.json':'lab/reports/workflow-v1.1/gb1/knowledge_component_ablation.json','aav_atomic.json':'lab/reports/knowledge-ablation/atomic-seed0/metrics.json','aav_checkpoint.json':'lab/reports/knowledge-ablation/checkpoint-seed0/metrics.json','aav_multiseed.json':'lab/context/research/v07-multiseed-evidence/summary.json','epistasis.json':'reports/final-report-v0.5/evidence/epistasis.json','aav_mechanism.md':'lab/context/research/v07-peak-mechanism.md','multiseed_protocol.md':'lab/context/research/v07-multiseed-robustness.md','handoff.md':'lab/reports/REPORT-HANDOFF.md','v08-proposal-received.md':'reports/v0.8-proposal-event-stream-reflexion.md'})
for ds in ['gb1','aav']:
 for typ in ['mutation_order','conservation']:paths[f'{ds}_{typ}.json']=f'lab/reports/analysis-v0.1/{ds}/{typ}.json'
for f in ['agent/pipeline.py','evolution/campaign.py','agent/auto_researcher.py','agent/llm.py','knowledge/validators.py','knowledge/rules.yaml','events/store.py','models/train_ladder.py','models/alpha_sweep.py','features/conservation.py','analysis/mutation_order.py','app/demo.py']:paths['code/'+f]=f
manifest={'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'inputs':[]}
for dst,src in paths.items():
 source=repo/src
 if not source.exists() and src=='reports/v0.8-proposal-event-stream-reflexion.md': source=main/src
 data=source.read_bytes();f=ROOT/'evidence'/dst;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data)
 manifest['inputs'].append({'path':src,'snapshot':'evidence/'+dst,'sha256':hashlib.sha256(data).hexdigest(),'origin':'frozen checkout' if source.is_relative_to(repo) else 'user-provided working document'})
# Compact reproducible audit of archived GB1 events; only relevant fields are retained.
audit={}
for reg in ['easy','hard','sparse','llm']:
 src=f'lab/reports/workflow-v1.1/gb1/campaign_{reg}.events.jsonl.gz';p=repo/src
 if not p.exists():continue
 dest=ROOT/'evidence'/f'gb1_{reg}.events.jsonl.gz';dest.write_bytes(p.read_bytes())
 manifest['inputs'].append({'path':src,'snapshot':str(dest.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'origin':'frozen checkout'})
 with gzip.open(p,'rt') as f:events=[json.loads(x) for x in f if x.strip()]
 cur=None;scored=[];judged={};rows=[];example=None;critics=[]
 for e in events:
  pay=e['payload'];typ=e['event_type']
  if typ=='campaign.started':cur=e['strategy'];judged={}
  if e['actor']=='data_analyst' and example is None:example={'strategy':cur,'round':e['round_id'],'analyst':pay}
  if e['actor']=='hypothesis_generator' and example and 'hypothesis' not in example:example['hypothesis']=pay
  if e['actor']=='fitness_evaluator':scored=pay.get('candidates',[])
  if e['actor']=='scientific_critic':
   cr=pay['critiques'];judged={c['sequence']:v['accepted'] for c,v in zip(scored,cr)}
   spent=pay.get('llm_critiques_spent',0)
   n_fallback=sum('fallback' in v.get('note','').lower() for v in cr)
   critics.append({'strategy':cur,'round':e['round_id'],'candidates':len(cr),'rejected':sum(not c['accepted'] for c in cr),'llm_attempts':spent,'llm_fallback_notes':n_fallback,'llm_success_notes':max(0,spent-n_fallback)})
  if typ=='campaign.propose.completed':
   picks=pay['variants'];rows.append({'strategy':cur,'round':e['round_id'],'n':len(picks),'n_critic_rejected':sum(judged.get(s) is False for s in picks),'variants':picks})
 audit[reg]={'event_count':len(events),'head_hash':events[-1]['hash'],'nominations':rows,'critic':critics,'example':example}
(ROOT/'evidence/event-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
(ROOT/'evidence/sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('Frozen inputs:',len(manifest['inputs']))
print('LLM round audit:',[{k:v for k,v in x.items() if k!='variants'} for x in audit['llm']['nominations'] if 'agent' in x['strategy']])
