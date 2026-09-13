from pathlib import Path
import json,gzip,hashlib,math,re
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
rep=load('gb1_llm_replication.json')
audit['gb1_replication_queries']={k:sum(x['n_nominated'] for x in rep['strategies'][k]['rounds']) for k in ['agent_no_knowledge','knowledge_agent']}
assert list(audit['gb1_replication_queries'].values())==[5,5]
manuscript=(R/'report.md').read_text()
expected_pages=len(manuscript.split('<!-- PAGE -->'))
expected_titles=['背景与问题定义','数据集介绍','适应度预测模型','LLM Agent 设计','知识增强方法','虚拟定向进化实验结果','失败案例分析','改进建议与未来拓展']
actual_titles=re.findall(r'^## [1-8]　(.+)$',manuscript,re.M)
assert actual_titles==expected_titles
audit['assignment_chapters']=actual_titles
assert '内环执行与外环改进' in manuscript and '独立回归门' in manuscript
active_images=re.findall(r'!\[[^\n]*\]\((figures/[^)]+)\)',manuscript)
assert len(active_images)==17 and len(set(active_images))==17
assert sum('_imagegen.png' in x for x in active_images)==4
for row in load('imagegen-prompts.json')['outputs']:
 assert digest((R/row['path']).read_bytes())==row['sha256']
layout=load('layout-check.json');assert len(layout)==expected_pages
assert all(not x['bad'] and all(i['ok'] for i in x['images']) for x in layout),'Layout overflow / missing image'
audit['layout_pages']=len(layout);audit['layout_overflow']=0
import fitz
pdf=fitz.open(R/'scientific_report_v0.7_two_column.pdf');assert len(pdf)==expected_pages
assert all(p.get_text().strip() for p in pdf);audit['pdf_pages']=len(pdf)
github='https://github.com/FairladyZ625/protein-directed-evolution-agent'
assert any(l.get('uri')==github for l in pdf[0].get_links())
from bs4 import BeautifulSoup
soup=BeautifulSoup((R/'scientific_report_v0.7_two_column.html').read_text(),'html.parser')
math_count=len(soup.find_all('math'));assert math_count>=30
assert len(load('formula-inventory.json')['display_blocks'])==14
audit['mathml_elements']=math_count
audit['github_link_on_first_page']=True
audit['active_figures']=len(active_images)
audit['generated_diagrams']=4
assert all((R/p).is_file() for p in active_images)
assert '附录 K.7' in manuscript and '附录 I' in manuscript
new=load('contract-audit.json')
assert new['pairs']['v09_v09']['overlap']==[46,42,37,25,26,8]
assert all(x['budget']==x['batch_n']*6 for x in new['arms'].values())
assert new['first_round_divergence_precedes_first_injection']
assert len(new['arms'])==12
assert new['pairs']['v09b12_v09']['overlap']==[12,12,9,6,7,7]
assert new['pairs']['v09b12_v08']['overlap']==[12]*6
assert new['arms']['v09b12_v09_on']['recurrence']['late']==new['arms']['v09b12_v09_off']['recurrence']['late']==1/36
audit['contract_study']={'arms':len(new['arms']),'n_seeds':1,'v09_pair_overlap':new['pairs']['v09_v09']['overlap'],'first_round_pre_injection':True}
import pandas as pd
domain=pd.read_csv(E/'aav-domain/cleaned.csv.gz')
cold=domain[domain.number_of_mutations<=2];pool=domain[domain.number_of_mutations>2]
assert (len(domain),len(cold),len(pool))==(38265,10433,27832)
assert (pool.score>cold.score.max()).sum()==0 and (cold.score>pool.score.max()).sum()==3
audit['aav_domain']={'cleaned':len(domain),'cold':len(cold),'candidate':len(pool),'candidate_max':float(pool.score.max()),'cold_above_candidate_max':3}
(E/'verification.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'verified_sources':len(sources['inputs']),'PDF_pages':len(pdf),'figures':len(active_images),'V08_equal_batches':6,'overflow':0}))
