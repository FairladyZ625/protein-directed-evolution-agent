from pathlib import Path
import json,gzip,hashlib,math
R=Path(__file__).resolve().parents[1];E=R/'evidence'
def load(n):return json.loads((E/n).read_text())
def digest(x):return hashlib.sha256(x).hexdigest()
sources=load('sources.json')
for row in sources['inputs']:
 assert digest((R/row['snapshot']).read_bytes())==row['sha256'],row
arms={a:[json.loads(l) for l in gzip.open(E/f'v08-{a}.events.jsonl.gz','rt')] for a in ['control','reflexion']}
batches={};audit={'snapshot_count':len(sources['inputs']),'v08':{}}
for a,ev in arms.items():
 batches[a]={};n=0
 for x in ev:
  if x['event_type']!='agent.tool.test.residuals':continue
  rr=x['payload']['records'];assert len(rr)==48
  for z in rr:assert math.isclose(z['residual'],z['measured_fitness']-z['predicted_mean'],abs_tol=1e-10)
  seqs=sorted(z['seq'] for z in rr);assert len(set(seqs))==48;n+=len(seqs)
  batches[a][x['round_id']]={'sha256':digest(('\n'.join(seqs)+'\n').encode()),'count':len(seqs)}
 assert n==288
 comp=[x['payload'] for x in ev if x['event_type']=='agent.tool.compose_batch']
 assert all(x['allocation_source']=='v06_pure_exploit_default' and x['requested_exploit_ratio']==x['exploit_ratio']==1 for x in comp)
 audit['v08'][a]={'batches':batches[a],'compose_events':len(comp),'redirects':[{'round':x['round_id'],'signature_size':x['payload']['signature_size']} for x in ev if x['event_type']=='agent.tool.redirect_batch'],'timeout_s':next(x['payload']['llm_timeout_s'] for x in ev if x['event_type']=='agent.llm.model')}
assert batches['control']==batches['reflexion'];audit['v08']['all_six_sequence_sets_equal']=True
aud=load('event-audit.json');audit['gb1_actual_queries']={}
for reg in ['hard','llm']:
 audit['gb1_actual_queries'][reg]={k:sum(x['n'] for x in aud[reg]['nominations'] if x['strategy']==k) for k in ['agent_no_knowledge','knowledge_agent']}
assert audit['gb1_actual_queries']=={'hard':{'agent_no_knowledge':288,'knowledge_agent':288},'llm':{'agent_no_knowledge':105,'knowledge_agent':197}}
layout=load('layout-check.json');assert len(layout)==18
assert all(not x['bad'] and all(i['ok'] for i in x['images']) for x in layout),'Layout overflow / missing image'
audit['layout_pages']=len(layout);audit['layout_overflow']=0
import fitz
pdf=fitz.open(R/'scientific_report_v0.6_two_column.pdf');assert len(pdf)==18
assert all(p.get_text().strip() for p in pdf);audit['pdf_pages']=len(pdf)
assert len(list((R/'figures').glob('*.png')))==13
(E/'verification.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'verified_sources':len(sources['inputs']),'PDF_pages':len(pdf),'figures':13,'V08_equal_batches':6,'overflow':0}))
