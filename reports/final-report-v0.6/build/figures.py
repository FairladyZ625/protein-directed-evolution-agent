from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
R=Path(__file__).resolve().parents[1]; E=R/'evidence'; F=R/'figures'
def load(n):return json.loads((E/(n+'.json')).read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#899aa7','axes.labelcolor':'#263e51','text.color':'#263e51','xtick.color':'#526574','ytick.color':'#526574','axes.titleweight':'bold','svg.fonttype':'none'})
C=['#9aa9b7','#497eaa','#ba9160','#5e9786']; LABEL=['Random','Greedy','Agent, no knowledge','Knowledge agent']; KEYS=['random','greedy','agent_no_knowledge','knowledge_agent']
def save(fig,name):
 fig.savefig(F/(name+'.png'),dpi=300,bbox_inches='tight',facecolor='white');fig.savefig(F/(name+'.svg'),bbox_inches='tight',facecolor='white')
 p=F/(name+'.svg');p.write_text('\n'.join(x.rstrip() for x in p.read_text().splitlines())+'\n');plt.close(fig)
def clean(ax):ax.grid(axis='y',color='#e6edf1',lw=.6);ax.set_axisbelow(True)
# 1: Different metrics illuminate different strengths.
d=load('predictors')['models'];fig,axs=plt.subplots(1,2,figsize=(10.2,3.0))
for ax,key,title in zip(axs,['spearman','mse'],['a  Test rank correlation','b  Test mean squared error']):
 vals=[d[k]['test'][key] for k in d];ax.bar(list(d),vals,color=C[1:],width=.58);ax.set_title(title,loc='left');clean(ax)
 for i,v in enumerate(vals):ax.text(i,v+max(vals)*.035,f'{v:.4f}',ha='center',fontsize=10)
 ax.set_ylim(0,max(vals)*1.23)
fig.tight_layout(w_pad=3);save(fig,'f01_predictors')
# 2 and S1: alpha sweeps, selected by validation.
a=load('alpha');fig,axs=plt.subplots(1,2,figsize=(10.2,3.3))
for ax,prep in zip(axs,['raw','standardized']):
 for feat,col in [('one_hot',C[1]),('esm2',C[3])]:
  row=a[f'{feat}__hd_extrapolation__{prep}'];xs=sorted(row['test_spearman_by_alpha'],key=float);ys=[row['test_spearman_by_alpha'][x] for x in xs]
  ax.plot(list(map(float,xs)),ys,color=col,label=feat.replace('_','-'),lw=2);sel=row['alpha_selected'];ax.scatter(sel,row['test_spearman_at_selected'],c=col,s=55,marker='D',edgecolor='white',zorder=3)
 ax.set(xscale='log',ylim=(0,.46),xlabel='Ridge alpha',ylabel='Test Spearman',title=prep.capitalize());clean(ax);ax.legend(frameon=False)
fig.tight_layout(w_pad=2);save(fig,'f02_alpha')
fig,axs=plt.subplots(2,4,figsize=(10.2,6.5))
order=[f'{f}__{s}__{p}' for f in ['esm2','one_hot'] for s in ['hd_extrapolation','random'] for p in ['raw','standardized']]
for ax,k in zip(axs.flat,order):
 row=a[k];xs=sorted(row['test_spearman_by_alpha'],key=float)
 ax.plot(list(map(float,xs)),[row['test_spearman_by_alpha'][x] for x in xs],color=C[1],label='Test');ax.plot(list(map(float,xs)),[row['val_spearman_by_alpha'][x] for x in xs],color='#9d9f9d',ls='--',label='Validation')
 ax.scatter(row['alpha_selected'],row['test_spearman_at_selected'],c=C[2],zorder=4,s=25);f,s,p=k.split('__');ax.set(xscale='log',title=f'{f}\n{s.replace("hd_extrapolation","HD extrapolation")}\n{p}',xlabel='alpha');ax.tick_params(labelsize=8);ax.title.set_fontsize(9);clean(ax)
axs[0,0].legend(fontsize=8,frameon=False);fig.tight_layout(w_pad=1.5,h_pad=2);save(fig,'fs1_alpha_full')
# Diagram helpers use vector geometry, exact labels and explicit causal/operational boundaries.
def canvas(title,h=4.2):
 fig,ax=plt.subplots(figsize=(10.2,h));ax.set(xlim=(0,10),ylim=(0,h));ax.axis('off');ax.text(.05,h-.12,title,fontsize=15,weight='bold',va='top');return fig,ax
def box(ax,x,y,w,h,title,sub='',col='#e8f1f7',size=10):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.02,rounding_size=.07',facecolor=col,edgecolor='#6c8c9d',lw=.9))
 ax.text(x+w/2,y+h*.64 if sub else y+h/2,title,ha='center',va='center',fontsize=size,weight='bold')
 if sub:ax.text(x+w/2,y+h*.25,sub,ha='center',va='center',fontsize=8)
def arrow(ax,a,b,txt='',dash=False):
 ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'-|>','color':'#6e8490','lw':1.1,'linestyle':'--' if dash else '-'})
 if txt:ax.text((a[0]+b[0])/2,(a[1]+b[1])/2+.08,txt,ha='center',fontsize=8)
fig,ax=canvas('Five roles and the actual GB1 selection path',4.3)
for x,t,sub,col in [(0.1,'Data Analyst','Measured-data summary','#e8f1f7'),(2.1,'Hypothesis','Substitution menu / LLM','#e5f1e8'),(4.1,'Designer','Combinatorial library','#e8f1f7'),(6.1,'Evaluator','Mean + variance','#e8f1f7')]:box(ax,x,2.65,1.65,.8,t,sub,col)
for x in [.1,2.1,4.1]:arrow(ax,(x+1.65,3.05),(x+2,3.05))
box(ax,8.1,2.65,1.7,.8,'Critic','Rule decisions + notes','#f5ecdf');arrow(ax,(7.75,3.05),(8.1,3.05))
box(ax,5.8,1.25,2,.75,'Batch selector','Mean / UCB + BLOSUM');arrow(ax,(6.9,2.65),(6.9,2),'All scored candidates')
box(ax,8.1,1.25,1.7,.75,'Event log','Role-level records','#eeebf5');arrow(ax,(8.95,2.65),(8.95,2),'Audit',True)
box(ax,3.1,1.25,1.8,.75,'Oracle lookup','Frozen nominations','#f5ecdf');arrow(ax,(5.8,1.62),(4.9,1.62))
box(ax,.1,1.25,2.1,.75,'Update measured set','Refit in next round');arrow(ax,(3.1,1.62),(2.2,1.62));arrow(ax,(1.1,2),(1.1,2.65))
ax.text(.1,.6,'Critic decisions are recorded; the frozen GB1 selector reads candidates, not accepted.',fontsize=10,color='#966d3b')
ax.text(.1,.25,'Solid arrows: executed data path    Dashed arrow: audit record',fontsize=9)
save(fig,'f03_workflow')
fig,ax=canvas('Three distinct channels of cross-round information',3.8)
for y,label,steps,col in [(2.25,'Statistical learning',['Observed labels','Fit surrogate','Next batch'], '#e8f1f7'),(1.25,'GB1 language interface',['Current menu','One-shot call','Hypothesis'], '#e5f1e8'),(.25,'AAV autonomous path',['Message history','Tools + state','Updated history'], '#f4eddf')]:
 ax.text(.1,y+.37,label,fontsize=10,weight='bold');
 for x,t in zip([2.4,5.1,7.8],steps):box(ax,x,y,2.05,.75,t,col=col)
 arrow(ax,(4.45,y+.38),(5.1,y+.38));arrow(ax,(7.15,y+.38),(7.8,y+.38))
save(fig,'f04_feedback')
# 5: concentration + conservation; a standalone entropy chart avoids overlapping labels.
c=load('aav_conservation');fig,axs=plt.subplots(1,2,figsize=(10.2,3.3),gridspec_kw={'width_ratios':[1.55,1]})
xs=[p['position_zero_based'] if 'position_zero_based' in p else p['position']-1 for p in c['positions']];ys=[p['entropy_nats'] for p in c['positions']]
axs[0].plot(xs,ys,color=C[1]);axs[0].set(xlabel='Window position (zero-based)',ylabel='Entropy (nats)',title='a  ESM-2 positional entropy',ylim=(1,3.18));clean(axs[0])
for p,lab,offset in zip(c['true_peak_positions'],['D0Q · rank 1','S17E · rank 26','V18A · rank 4'],[(6,18),(-85,-32),(12,-65)]):
 x=p['position_zero_based'];y=p['entropy_nats'];axs[0].scatter(x,y,color=C[2],zorder=3);axs[0].annotate(lab,(x,y),xytext=offset,textcoords='offset points',fontsize=8,arrowprops={'arrowstyle':'-','color':C[2]})
q=load('gb1_easy')['strategies']['knowledge_agent']['topk_concentration']['positions'];vals=[q[str(p)]['dominant_fraction'] for p in [39,40,41,54]]
axs[1].bar(['V39','D40','G41','V54'],vals,color=C[3]);axs[1].set(ylim=(0,1.15),ylabel='Dominant residue fraction',title='b  GB1 selected residues');clean(axs[1])
for i,p in enumerate([39,40,41,54]):axs[1].text(i,vals[i]+.03,q[str(p)]['dominant_residue'],ha='center')
fig.tight_layout(w_pad=2);save(fig,'f05_knowledge')
# 6: three regimes with random mean ± SD and exact per-strategy traces.
fig,axs=plt.subplots(1,3,figsize=(10.2,3.1),sharey=True)
for ax,reg in zip(axs,['easy','hard','sparse']):
 d=load('gb1_'+reg);rs=d['strategies']['random']['multi_seed']['rounds'];m=np.array([r['cum_top10_max_mean'] for r in rs]);sd=np.array([r['cum_top10_max_std'] for r in rs]);ax.plot([1,2,3],m,color=C[0],label=LABEL[0]);ax.fill_between([1,2,3],m-sd,m+sd,color=C[0],alpha=.18)
 for k,col,lab,mark in zip(KEYS[1:],C[1:],LABEL[1:],['s','^','D']):ax.plot([1,2,3],d['summary'][k]['cum_top10_max_curve'],color=col,label=lab,marker=mark,ms=4,lw=1.5)
 ax.axhline(8.761966,ls=':',color='#9eacb5',lw=.8);ax.set(xticks=[1,2,3],xlabel='Round',title=f'{reg.capitalize()} · N0={d["strategies"]["greedy"]["cold_start_pool_size"]:,}',ylim=(0,10));clean(ax)
axs[0].set_ylabel('Best new fitness');axs[2].legend(fontsize=7,frameon=False,loc='lower right');fig.tight_layout(w_pad=1);save(fig,'f06_regimes')
# 7: use real consumption rather than nominal budget as the comparison denominator.
aud=load('event-audit');fig,axs=plt.subplots(1,3,figsize=(10.2,3.1));labs=['No knowledge','Knowledge']
for ax,metric,title in zip(axs,['strong','beneficial','queries'],['a  Strong variants','b  Beneficial variants','c  Actual queries']):
 for j,reg in enumerate(['hard','llm']):
  d=load('gb1_'+reg);vs=[]
  for k in KEYS[2:]:
   vs.append(sum(x['n'] for x in aud[reg]['nominations'] if x['strategy']==k) if metric=='queries' else d['summary'][k]['final_cum_n_strong' if metric=='strong' else 'total_beneficial_hits'])
  xx=np.arange(2)+(j-.5)*.32;ax.bar(xx,vs,width=.3,color=C[1] if j==0 else C[2],label='Deterministic' if j==0 else 'Live LLM')
  for x,v in zip(xx,vs):ax.text(x,v+max(vs)*.04,str(v),ha='center',fontsize=8)
 ax.set(xticks=[0,1],xticklabels=labs,title=title);clean(ax);ax.set_ylim(0,ax.get_ylim()[1]*1.15)
axs[0].legend(fontsize=8,frameon=False);fig.tight_layout(w_pad=2);save(fig,'f07_llm')
# 8: AAV knowledge intervention and actual candidate composition.
d=load('aav_atomic')['summary'];fig,axs=plt.subplots(1,3,figsize=(10.2,3.1))
for ax,met,title in zip(axs[:2],['cum_top10_max_mean','strong_mean'],['a  Best new fitness','b  Strong yield']):
 vals=[d['strategies'][k][met] for k in KEYS];ax.bar(range(4),vals,color=C);ax.set(xticks=range(4),xticklabels=['Rand.','Greedy','No K.','With K.'],title=title);clean(ax);ax.set_ylim(0,max(vals)*1.25)
 for i,v in enumerate(vals):ax.text(i,v+max(vals)*.035,f'{v:.2f}' if met.startswith('cum') else f'{v:.0f}',ha='center',fontsize=8)
pair=d['paired_knowledge_ablation'][0]
for k,col,label in [('no_knowledge',C[2],'No knowledge'),('knowledge',C[3],'Knowledge')]:
 vals=pair[k]['hd_counts'];xx=sorted(map(int,vals));axs[2].plot(xx,[vals[str(x)] for x in xx],marker='o',ms=3,color=col,label=label)
axs[2].set(title='c  Nominated mutation orders',xlabel='Hamming distance',ylabel='Variants');axs[2].legend(fontsize=7,frameon=False);clean(axs[2]);fig.tight_layout(w_pad=2);save(fig,'f08_aav_ablation')
# 9: fixed-model AAV comparisons.
d=load('aav_multiseed');order=['mean','ucb0.5','ucb1','ucb2','ucb3','alternating','thompson_gaussian'];names=['Pure mean','UCB 0.5','UCB 1','UCB 2','UCB 3','Alternating','Marginal TS'];fig,axs=plt.subplots(1,2,figsize=(10.2,3.3),sharey=True)
for i,k in enumerate(order):
 row=d[k];ran=row['unique_trajectories']>1;col='#987dab' if ran else (C[3] if k=='ucb3' else C[1])
 for ax,m in zip(axs,['maximum','strong']):ax.errorbar(row[m]['mean'],i,xerr=row[m]['sd'] if ran else None,fmt='D' if ran else 'o',ms=6,color=col,capsize=3)
axs[0].set(yticks=range(7),yticklabels=names,title='a  Best new fitness',xlabel='Fitness');axs[0].invert_yaxis();axs[0].axvline(8.416205,ls=':',color='#9daab4');axs[1].set(title='b  Strong-variant yield',xlabel='Variants');fig.tight_layout(w_pad=3);save(fig,'f09_aav_fixed')
# 10: compare coverage and cross-order generalization; show distribution, not causal claims.
g=load('gb1_mutation_order');a=load('aav_mutation_order');fig,axs=plt.subplots(1,3,figsize=(10.2,3.15))
for ds,col,label in [(g,C[1],'GB1'),(a,C[3],'AAV')]:
 cov=ds['lower_order_coverage_by_order'];vals=[cov[str(x)]['complete_fraction'] for x in [2,3,4]];axs[0].plot([2,3,4],vals,marker='o',color=col,label=label)
axs[0].set(xticks=[2,3,4],xlabel='Mutation order',ylabel='Complete immediate-subset fraction',title='a  Lower-order support',ylim=(0,1.1));axs[0].legend(frameon=False,fontsize=8)
for i,ds in enumerate([g,a]):
 rows=ds['additive_extrapolation'];axs[1].plot([2,3],[r['test_spearman'] for r in rows],marker='o',color=[C[1],C[3]][i],label=['GB1','AAV'][i])
axs[1].set(xticks=[2,3],xlabel='Test mutation order',ylabel='Test Spearman',title='b  Additive extrapolation',ylim=(.45,.95))
xs=np.arange(1,11);dist=a['distribution_by_order'];med=[dist[str(x)]['fitness_median'] for x in xs];lo=[dist[str(x)]['fitness_q25'] for x in xs];hi=[dist[str(x)]['fitness_q75'] for x in xs]
axs[2].fill_between(xs,lo,hi,color=C[3],alpha=.2);axs[2].plot(xs,med,color=C[3]);axs[2].set(xlabel='Mutation order',ylabel='Measured fitness',title='c  AAV median and IQR')
for ax in axs:clean(ax)
fig.tight_layout(w_pad=2);save(fig,'f10_order')
# 11: measured genotype graph, preserving AB missingness.
v=load('epistasis')['values'];fig,axs=plt.subplots(1,2,figsize=(10.2,3.0),gridspec_kw={'width_ratios':[1.5,1]});ax=axs[0];pos={'WT':(0,1),'A':(1,2),'B':(1,1),'C':(1,0),'AB':(2,2),'AC':(2,1),'BC':(2,0),'ABC':(3,1)};bits={'WT':0,'A':1,'B':2,'C':4,'AB':3,'AC':5,'BC':6,'ABC':7}
for aa in pos:
 for bb in pos:
  if bits[bb].bit_count()==bits[aa].bit_count()+1 and bits[aa]&bits[bb]==bits[aa]:ax.plot([pos[aa][0],pos[bb][0]],[pos[aa][1],pos[bb][1]],c='#c6d1d9',lw=1,zorder=1)
for n,(x,y) in pos.items():
 ax.text(x,y,n+'\n'+('NA' if v[n] is None else f'{v[n]:.3f}'),ha='center',va='center',fontsize=9,bbox={'boxstyle':'round,pad=.5','fc':'#f4eadc' if n=='AB' else '#e6f0f5','ec':'#8da3b1'},zorder=3)
ax.set(xlim=(-.4,3.4),ylim=(-.5,2.5));ax.axis('off');ax.set_title('a  Observed genotypes',loc='left')
add=v['A']+v['B']+v['C']-2*v['WT'];axs[1].bar(['Additive\nexpectation','Observed\nABC'],[add,v['ABC']],color=[C[1],C[3]]);axs[1].set(ylim=(0,10),title='b  Observed minus additive',ylabel='Fitness');clean(axs[1]);axs[1].text(.5,9.3,f'Difference: {v["ABC"]-add:.6f}',ha='center');fig.tight_layout(w_pad=2);save(fig,'f11_epistasis')
# 12: proposed feedback experiment, no fabricated molecular mechanism from residuals.
fig,ax=canvas('V0.8: from residual evidence to executed selection',3.8)
for x,t,sub in [(.1,'Nominated prediction','Before measurement'),(3.5,'Oracle observation','After nomination'),(6.9,'Event pairing','Variant + round + model')]:box(ax,x,2.25,2.7,.8,t,sub)
arrow(ax,(2.8,2.65),(3.5,2.65));arrow(ax,(6.2,2.65),(6.9,2.65))
box(ax,6.9,.75,2.7,.85,'Reflection card','Residuals / rules / budget','#f4eadc');arrow(ax,(8.25,2.25),(8.25,1.6))
box(ax,3.5,.75,2.7,.85,'Researcher agent','History + tools + evidence','#e4f1e8');arrow(ax,(6.9,1.2),(6.2,1.2))
box(ax,.1,.75,2.7,.85,'Next selection','Check executed candidates','#e4f1e8');arrow(ax,(3.5,1.2),(2.8,1.2))
ax.text(.1,.2,'Next factorial study: pure exploitation / quality-aware mix  x  reflection off / on',fontsize=9)
save(fig,'f12_v08')
print('13 figures created (12 main + S1); all charts read frozen evidence')
