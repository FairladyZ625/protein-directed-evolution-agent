from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#8895a5','axes.labelcolor':'#25364a','text.color':'#25364a','xtick.color':'#526274','ytick.color':'#526274','axes.titleweight':'bold','svg.fonttype':'none'})
colors=['#9ca8b4','#5186b3','#be9365','#60998c']
def save(fig,name):
 fig.savefig(ROOT/'figures'/f'{name}.png',dpi=320,bbox_inches='tight',facecolor='white')
 fig.savefig(ROOT/'figures'/f'{name}.svg',bbox_inches='tight',facecolor='white')
 svg=ROOT/'figures'/f'{name}.svg'
 svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
 plt.close(fig)
s=json.loads((ROOT/'evidence/gb1_summary.json').read_text())['summary']
keys=['random','greedy','agent_no_knowledge','knowledge_agent']; labels=['Random','Greedy','Agent, no knowledge','Knowledge agent']
fig,axs=plt.subplots(1,2,figsize=(10.4,3.65),gridspec_kw={'width_ratios':[1.15,1]})
for k,c,lab,m in zip(keys,colors,labels,['o','s','^','D']):
 axs[0].plot([96,192,288],s[k]['cum_top10_max_curve'],marker=m,color=c,label=lab,lw=1.7,ms=5,alpha=.9)
axs[0].set(xticks=[96,192,288],ylim=(0,10),xlabel='New measurements',ylabel='Best newly measured fitness',title='a  Best fitness')
axs[0].axhline(8.761966,color='#a8b2bb',lw=.8,ls='--');axs[0].grid(axis='y',color='#e9edf1');axs[0].legend(loc='lower right',fontsize=8,frameon=False)
vals=[s[k]['total_beneficial_hits'] for k in keys]
axs[1].barh(np.arange(4),vals,color=colors,height=.55);axs[1].set(yticks=np.arange(4),yticklabels=['Random','Greedy','No knowledge','Knowledge'],xlim=(0,205),xlabel='Variants with fitness > 1.0',title='b  Beneficial yield');axs[1].invert_yaxis()
for i,v in enumerate(vals):axs[1].text(v+3,i,str(v),va='center',fontsize=11)
fig.tight_layout(w_pad=2);save(fig,'fig2_gb1')
# fixed AAV summary, keyed by configuration; deterministic point values vs random mean/SD.
rows=[('Pure mean',7.829,0,166,0,'deterministic'),('UCB 0.5',6.5309,0,153,0,'deterministic'),('UCB 1',6.5309,0,151,0,'deterministic'),('UCB 2',6.5309,0,139,0,'deterministic'),('UCB 3',8.4162,0,128,0,'deterministic'),('Alternating',7.8681,.1490,148.73,3.49,'random'),('Marginal TS',7.3017,.6684,140.03,6.06,'random')]
(ROOT/'evidence/aav_plot_data.json').write_text(json.dumps(rows,indent=2))
fig,axs=plt.subplots(1,2,figsize=(10.4,3.6),sharey=True)
for i,(n,m,sd,y,ysd,kind) in enumerate(rows):
 c='#60998c' if n=='UCB 3' else ('#9a86b5' if kind=='random' else '#5186b3');marker='D' if kind=='random' else 'o'
 axs[0].errorbar(m,i,xerr=sd or None,fmt=marker,color=c,ms=7,capsize=3,lw=1.4)
 axs[1].errorbar(y,i,xerr=ysd or None,fmt=marker,color=c,ms=7,capsize=3,lw=1.4)
axs[0].set(yticks=range(7),yticklabels=[r[0] for r in rows],xlabel='Best newly measured fitness',xlim=(5.9,8.85),title='a  Maximum fitness');axs[0].invert_yaxis();axs[0].axvline(8.416205,color='#a8b2bb',ls='--',lw=1)
axs[1].set(xlabel='Strong variants (fitness ≥ 2.6159)',xlim=(115,175),title='b  Strong-variant yield')
for ax in axs:ax.grid(axis='x',color='#e9edf1');ax.set_axisbelow(True)
fig.tight_layout(w_pad=2);save(fig,'fig4_aav')
# Hasse-style genotype graph, edges encode one substitution, not an observed trajectory.
v=json.loads((ROOT/'evidence/epistasis.json').read_text())['values']
fig,(ax,bx)=plt.subplots(1,2,figsize=(10.4,3.5),gridspec_kw={'width_ratios':[1.65,1]})
positions={'WT':(0,1),'A':(1,2),'B':(1,1),'C':(1,0),'AB':(2,2),'AC':(2,1),'BC':(2,0),'ABC':(3,1)}
bits={'WT':0,'A':1,'B':2,'C':4,'AB':3,'AC':5,'BC':6,'ABC':7}
for a in positions:
 for b in positions:
  if bits[b].bit_count()==bits[a].bit_count()+1 and bits[a]&bits[b]==bits[a]:
   ax.plot([positions[a][0],positions[b][0]],[positions[a][1],positions[b][1]],color='#cbd3da',lw=1,zorder=1)
for name,(x,y) in positions.items():
 missing=v[name] is None;fc='#f7eee4' if missing else ('#dfeee8' if name=='ABC' else '#e8f0f7');ec='#b3895f' if missing else '#6b8ca6'
 ax.add_patch(FancyBboxPatch((x-.32,y-.24),.64,.48,boxstyle='round,pad=.03,rounding_size=.055',facecolor=fc,edgecolor=ec,linestyle='--' if missing else '-',zorder=2))
 ax.text(x,y+.07,name,ha='center',va='center',weight='bold',fontsize=10,zorder=3)
 ax.text(x,y-.1,'Unmeasured' if missing else f'{v[name]:.3f}',ha='center',va='center',fontsize=8.3,zorder=3)
ax.set(xlim=(-.5,3.5),ylim=(-.48,2.5));ax.axis('off');ax.set_title('a  Observed local genotypes',loc='left')
add=v['A']+v['B']+v['C']-2*v['WT'];gap=v['ABC']-add
bx.bar([0,1],[add,v['ABC']],color=['#8aa9c1','#74a393'],width=.55)
bx.set(xticks=[0,1],xticklabels=['Additive\nexpectation','Observed\nABC'],ylabel='Fitness',ylim=(0,10.3),title='b  Non-additive difference');bx.grid(axis='y',color='#e9edf1');bx.set_axisbelow(True)
for i,val in enumerate([add,v['ABC']]):bx.text(i,val+.12,f'{val:.3f}',ha='center',fontsize=10)
bx.text(.5,9.6,f'Difference = {gap:.6f}',ha='center',fontsize=10)
fig.tight_layout(w_pad=2);save(fig,'fig3_epistasis')
assert abs(add-6.315428)<1e-8 and abs(gap-2.100777)<1e-8
print('3 data figures generated; additive arithmetic verified')
