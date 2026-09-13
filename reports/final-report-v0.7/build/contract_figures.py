from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];d=json.loads((R/'evidence/contract-audit.json').read_text());A=d['arms']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#899aa7','text.color':'#263e51','axes.labelcolor':'#263e51','xtick.color':'#526574','ytick.color':'#526574','svg.fonttype':'none'})
C=['#497eaa','#5e9786','#ba9160','#9aa9b7']
def clean(ax):ax.grid(axis='y',color='#e6edf1',lw=.6);ax.set_axisbelow(True)
def save(fig,name):
 fig.tight_layout(w_pad=2);fig.savefig(R/'figures'/f'{name}.png',dpi=300,bbox_inches='tight',facecolor='white');fig.savefig(R/'figures'/f'{name}.svg',bbox_inches='tight',facecolor='white');p=R/'figures'/f'{name}.svg';p.write_text('\n'.join(z.rstrip() for z in p.read_text().splitlines())+'\n');plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(10.2,3.4),gridspec_kw={'width_ratios':[1.15,1]})
x=np.arange(1,7)
for k,label,col in [('v09_v08','v08 contract',C[0]),('v09_v09','v09 contract',C[1])]:
 y=d['pairs'][k]['overlap'];ax[0].plot(x,y,marker='o',lw=2,color=col,label=label)
 for xx,yy in zip(x,y):ax[0].text(xx,yy+(1.4 if k=='v09_v08' else -4),str(yy),ha='center',fontsize=9,color=col)
ax[0].axvspan(.7,1.5,color='#edf0f3',zorder=0);ax[0].axvline(1.5,color='#899aa7',ls=':',lw=1);ax[0].text(1.6,20,'Residual cards\nstart at round 2',fontsize=8,color='#71828b');ax[0].set(xlim=(.7,6.3),ylim=(0,54),xticks=x,xlabel='Round',ylabel='Shared sequences / 48',title='a  Reflection on vs off: batch overlap');ax[0].legend(loc='lower left',frameon=False,fontsize=8)
keys=['v09_v08_off','v09_v08_on','v09_v09_off','v09_v09_on'];labels=['v08\noff','v08\non','v09\noff','v09\non'];xx=np.arange(4)
for j,(metric,label,col) in enumerate([('explicit_requests','Explicit ratio',C[0]),('exclusion_calls','Motif exclusions',C[1])]):
 vals=[100*A[k][metric]/len(A[k]['composes']) for k in keys];pos=xx+(j-.5)*.34;ax[1].bar(pos,vals,.32,label=label,color=col)
 for x0,k,v in zip(pos,keys,vals):ax[1].text(x0,v+3,f'{A[k][metric]}/{len(A[k]["composes"])}',ha='center',fontsize=8)
ax[1].set(xticks=xx,xticklabels=labels,ylim=(0,130),ylabel='Share of compose calls (%)',title='b  Observed use of tool arguments');ax[1].legend(frameon=False,fontsize=8,loc='upper left')
for a in ax:clean(a)
save(fig,'f14_contract_behavior')
fig,ax=plt.subplots(1,2,figsize=(10.2,3.3))
rows=A['v09_v09_on']['exclusion_rows'];ev=[z['evidence_count'] for z in rows];ex=[z['excluded_count'] for z in rows]
ax[0].plot(x,ev,marker='s',color=C[0],label='In prior injected cards');ax[0].plot(x,ex,marker='o',color=C[1],label='Requested exclusions')
for xx,yy in zip(x,ex):ax[0].text(xx,yy-2.6,str(yy),ha='center',color=C[1],fontsize=8)
ax[0].set(xticks=x,ylim=(-4,max(ev)+5),xlabel='Round',ylabel='Distinct substitution motifs',title='a  Exclusions and available evidence');ax[0].legend(frameon=False,fontsize=8)
for key,col,lab in [('v09_v09_off',C[0],'Reflection off'),('v09_v09_on',C[1],'Reflection on')]:
 cs=A[key]['composes'];ys=[next((c['exploit_ratio'] for c in cs if c['round']==r),np.nan) for r in range(1,7)];ax[1].plot(x,ys,marker='o',color=col,label=lab)
ax[1].axvspan(.7,1.5,color='#edf0f3',zorder=0);ax[1].set(xlim=(.7,6.3),xticks=x,ylim=(.7,1.01),xlabel='Round',ylabel='Effective exploit ratio',title='b  v09 contract: executed allocation');ax[1].legend(frameon=False,fontsize=8);ax[1].text(3,.72,'Gap at round 5: redirect instead of compose',fontsize=7,ha='center',color='#70808b')
for a in ax:clean(a)
save(fig,'f15_evidence_actions')
print('Produced two contract-study data figures; evidence counts',ev,'exclusions',ex)
# Budget comparison: collapse exactly overlapping fitness curves; never imply equal batches.
if 'v09b12_v09_on' in A:
 fig,axs=plt.subplots(1,2,figsize=(10.2,3.25),sharey=True)
 for ax,prefix,title in zip(axs,['v09','v09b12'],['a  48 per round (288 total)','b  12 per round (72 total)']):
  groups={}
  for mode in ['v08','v09']:
   for state in ['off','on']:
    k=f'{prefix}_{mode}_{state}';curve=tuple(np.round(A[k]['best_curve'],8));groups.setdefault(curve,[]).append((mode,state))
  for j,(curve,keys) in enumerate(groups.items()):
   label='All four arms' if len(keys)==4 else f'{keys[0][0]} contract (off/on)' if len(keys)==2 and keys[0][0]==keys[1][0] else ' / '.join(f'{m} {s}' for m,s in keys)
   ax.plot(range(1,7),curve,color=C[j],marker=['o','s'][j%2],label=label,lw=2)
  ax.axhline(8.41620513,color='#8e9da7',ls=':',lw=.9);ax.set(xticks=range(1,7),xlabel='Round',title=title,ylim=(5.4,8.85));ax.legend(frameon=False,fontsize=8,loc='lower right');clean(ax)
 axs[0].set_ylabel('Best new measured fitness')
 save(fig,'f16_budget_comparison')
 print('Produced budget-comparison figure')
