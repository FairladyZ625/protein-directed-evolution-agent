from pathlib import Path
import json,gzip,hashlib,re,math
R=Path(__file__).resolve().parents[1];E=R/'evidence'
def read(n):return json.loads((E/n).read_text())
def digest(seqs):return hashlib.sha256(('\n'.join(sorted(seqs))+'\n').encode()).hexdigest()
def motifs(seq,wt):return {f'{a}{i}{b}' for i,(a,b) in enumerate(zip(wt,seq)) if a!=b}
A={};raw={}
for arm in read('new-experiment-arms.json'):
 key=f"{arm['study']}_{arm['mode']}_{arm['reflection']}";root=E/arm['path'];m=json.loads((root/'metrics.json').read_text());batch_n=m['budget_per_round'];ev=[json.loads(l) for l in gzip.open(root/'events.jsonl.gz','rt')];raw[key]=ev;prev='';batches={};composes=[];cards=[];evidence=set();exclusion_rows=[];wt=m['wild_type'];allrecords=[]
 for j,x in enumerate(ev,1):
  body={k:x[k] for k in ['seq','ts','event_type','round_id','strategy','actor','payload']};h=hashlib.sha256((prev+json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=True)).encode()).hexdigest();assert x['seq']==j and x['prev_hash']==prev and x['hash']==h;prev=h
  payload=x['payload'];rnd=x['round_id'];typ=x['event_type']
  if typ=='agent.reflexion.injected':
   text=payload['prompt_text'];new={mo for mo,over in re.findall(r'([A-Z]\d+[A-Z]) \(over=(\d+), under=\d+\)',text) if int(over)>0};evidence|=new;cards.append({'round':rnd,'source_round':payload['source_round'],'seq':j,'characters':len(text),'sha256':hashlib.sha256(text.encode()).hexdigest(),'evidence_motifs':sorted(new),'cumulative_motifs':sorted(evidence)})
  if typ=='agent.tool.compose_batch':
   z={'round':rnd,'seq':j,**payload};composes.append(z);excluded=set(payload.get('excluded_motifs',[]));exclusion_rows.append({'round':rnd,'excluded':sorted(excluded),'excluded_count':len(excluded),'evidence_count':len(evidence),'not_in_prior_cards':sorted(excluded-evidence),'evidence':sorted(evidence),'n_excluded_candidates':payload.get('n_excluded',0)})
   if arm['reflection']=='on':assert not(excluded-evidence),key
  if typ=='agent.tool.test.residuals':
   records=payload['records'];assert len(records)==batch_n;seqs=[z['seq'] for z in records];assert len(set(seqs))==batch_n
   for z in records:assert math.isclose(z['residual'],z['measured_fitness']-z['predicted_mean'],abs_tol=1e-10)
   active=next((set(z['excluded_motifs']) for z in reversed(composes) if z['round']==rnd and 'excluded_motifs' in z),set());assert all(not(active&motifs(s,wt)) for s in seqs),key
   batches[str(rnd)]={'sequences':sorted(seqs),'hash':digest(seqs),'event_seq':j,'size':len(seqs)};allrecords+=records
 assert len(batches)==6 and len(allrecords)==batch_n*6 and m['budget_spent']==batch_n*6
 strong=sum(z['measured_fitness']>=m['strong_threshold'] for z in allrecords);assert strong==m['summary']['final_cum_n_strong']
 A[key]={'arm':arm,'batch_n':batch_n,'budget':m['budget_spent'],'strong':strong,'peak':m['summary']['final_cum_top10_max'],'top10_mean':m['summary']['final_cum_top10_mean'],'threshold':m['strong_threshold'],'gate_pool':m['gate_pass_pool_size'],'llm_attempts':m['llm_round_attempts'],'llm_successes':m['llm_round_successes'],'timeouts':m['llm_timeout_errors'],'round_errors':m['llm_round_errors'],'timeout_s':m['llm_round_timeout_seconds'],'redirects':m['redirect_rounds'],'stall_flags':m['stall_flag_rounds'],'wall_s':int((root/'wall-seconds.txt').read_text()),'event_count':len(ev),'head_hash':prev,'first_timestamp':ev[0]['ts'],'batches':batches,'composes':composes,'cards':cards,'injected_characters':sum(c['characters'] for c in cards),'explicit_requests':sum(z['allocation_source']=='agent_requested' for z in composes),'exclusion_calls':sum(bool(z.get('excluded_motifs')) for z in composes),'exclusion_rows':exclusion_rows}
# Recurrence is evaluated against each arm's immediately PREVIOUS measured batch.
for key,z in A.items():
 ev=raw[key];records={x['round_id']:x['payload']['records'] for x in ev if x['event_type']=='agent.tool.test.residuals'};rows=[]
 original=json.loads((E/z['arm']['path']/'metrics.json').read_text());wt=original['wild_type']
 for rnd in range(2,7):
  low={mo for rec in records[rnd-1] if rec['measured_fitness']<original['fatal_fitness_threshold'] for mo in motifs(rec['seq'],wt)}
  k=sum(bool(motifs(rec['seq'],wt)&low) for rec in records[rnd]);n=len(records[rnd]);given=next(x for x in original['motif_recurrence'] if x['round']==rnd)
  assert (k,n)==(given['n_with_previous_lethal_motif'],given['n_candidates'])
  rows.append({'round':rnd,'repeated':k,'n':n,'previous_low_motif_count':len(low)})
 k=sum(x['repeated'] for x in rows);n=sum(x['n'] for x in rows);lk=sum(x['repeated'] for x in rows if x['round']>=4);ln=sum(x['n'] for x in rows if x['round']>=4)
 z['recurrence']={'rows':rows,'repeated':k,'n':n,'pooled':k/n if n else None,'late_repeated':lk,'late_n':ln,'late':lk/ln if ln else None,'window':'previous round measured_fitness < 0.2; any shared substitution'}
 z['best_curve']=[];best=-float('inf');target=8.416205130560002;hit=None
 for rnd in range(1,7):
  best=max(best,max(t['measured_fitness'] for t in records[rnd]));z['best_curve'].append(best)
  if hit is None and best>=target-1e-10:hit=rnd
 z['first_peak_round']=hit
pairs={}

for study,mode in [('v08','v05'),('v08','v06'),('v09','v08'),('v09','v09'),('v09b12','v08'),('v09b12','v09')]:
 off=A[f'{study}_{mode}_off'];on=A[f'{study}_{mode}_on'];overlap=[len(set(off['batches'][str(r)]['sequences'])&set(on['batches'][str(r)]['sequences'])) for r in range(1,7)];pairs[f'{study}_{mode}']={'overlap':overlap,'equal':[off['batches'][str(r)]['hash']==on['batches'][str(r)]['hash'] for r in range(1,7)]}
assert pairs['v08_v05']['overlap']==pairs['v08_v06']['overlap']==pairs['v09_v08']['overlap']==[48]*6
assert pairs['v09_v09']['overlap']==[46,42,37,25,26,8]
assert sum(A[k]['explicit_requests'] for k in A if k.startswith('v08_'))==0
assert sum(len(A[k]['composes']) for k in A if k.startswith('v08_'))==20
assert sum(A[k]['explicit_requests'] for k in A if k.startswith('v09_v09'))==11
assert [z['excluded_count'] for z in A['v09_v09_on']['exclusion_rows']]==[0,2,4,8,13,20]
base_replay=[A['v08_v05_off']['batches'][str(r)]['hash']==A['v09_v08_off']['batches'][str(r)]['hash'] for r in range(1,7)];assert all(base_replay)
positive=[len(set(A['v08_v05_off']['batches'][str(r)]['sequences'])&set(A['v08_v06_off']['batches'][str(r)]['sequences'])) for r in range(1,7)]
# Same generation rule does not imply identical card content or instruction text.
card_matches=[a['sha256']==b['sha256'] for a,b in zip(A['v09_v08_on']['cards'],A['v09_v09_on']['cards'])]
assert A['v09_v09_on']['cards'][0]['round']==2
import ast
import numpy as np
code=(E/'code-v09/agent/auto_researcher.py').read_text()
node=next(n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef) and n.name=='_enforce_exploit_floor')
space={'np':np};exec(compile(ast.Module(body=[node],type_ignores=[]),'frozen-exploit-floor','exec'),space)
r4=space['_enforce_exploit_floor'](.85,.99,4,6);r6=space['_enforce_exploit_floor'](.95,.99,6,6)
assert r4==(.85,.8) and r6==(.95,.9)
agg_node=next(n for n in ast.parse((E/'code-metrics/reflexion.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='summarise_motif_recurrence')
ns={};module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),agg_node],type_ignores=[]);exec(compile(ast.fix_missing_locations(module),'frozen-recurrence-aggregation','exec'),ns)
assert ns['summarise_motif_recurrence']([])['pooled_rate'] is None
for z in A.values():
 rows=[{'round':r['round'],'n_candidates':r['n'],'n_with_previous_lethal_motif':r['repeated']} for r in z['recurrence']['rows']]
 check=ns['summarise_motif_recurrence'](rows);assert check['pooled_rate']==z['recurrence']['pooled'] and check['late_pooled_rate']==z['recurrence']['late']
for key,z in A.items():
 z['check_knowledge_calls']=sum(x['event_type']=='agent.tool.check_knowledge' for x in raw[key])
 assert z['check_knowledge_calls']==0
 for c in z['composes']:
  assert c['n_exploit']==max(0,min(z['batch_n'],round(z['batch_n']*c['exploit_ratio'])))
  assert c['n_explore']==z['batch_n']-c['n_exploit']
assert [x['n_exploit'] for x in A['v09b12_v09_on']['composes']]==[11]*5
assert round(12*.875)==10 and round(11.5)==12
out={'arms':A,'pairs':pairs,'v08_cross_acquisition_overlap':positive,'v08_baseline_reproduced_in_v09':base_replay,'v09_cross_contract_card_hash_matches':card_matches,'first_round_divergence_precedes_first_injection':True,'n_independent_seeds':1,'floor_checks':{'round4_request_085':r4,'round6_request_095':r6}}
(E/'contract-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pairs':pairs,'cross_acquisition_overlap':positive,'card_hash_matches':card_matches,'arms':{k:{f:v[f] for f in ['strong','explicit_requests','exclusion_calls','wall_s','injected_characters','stall_flags']} for k,v in A.items()}},ensure_ascii=False,indent=2))
