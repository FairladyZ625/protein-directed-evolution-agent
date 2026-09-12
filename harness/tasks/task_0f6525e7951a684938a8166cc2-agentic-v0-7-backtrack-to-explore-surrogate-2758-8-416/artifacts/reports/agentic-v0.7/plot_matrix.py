"""Export a standalone comparison figure from verified results only."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

out=Path(__file__).resolve().parent
rows=json.loads((out/'matrix-summary-final.json').read_text())
assert len(rows)==12
peak=json.loads((out/'controls.json').read_text())['pool_peak']
fig,axes=plt.subplots(2,2,figsize=(10,6.5),sharex=True,sharey=True)
colors={42:'#0072B2',0:'#D55E00',7:'#009E73'}
styles={42:'-',0:'--',7:':'}
for ax,mode in zip(axes.flat,('mean','alternating','full','semi')):
 for r in rows:
  if r['mode']==mode:
   ax.plot(range(1,7),r['curve'],marker='o',linestyle=styles[r['seed']],
           color=colors[r['seed']],label=f"seed {r['seed']} (strong={r['strong']})")
 ax.axhline(peak,color='#666666',linestyle='--',linewidth=.8)
 ax.set_title(mode);ax.set_xticks(range(1,7));ax.grid(axis='y',alpha=.2)
 ax.legend(fontsize=8,loc='center left' if mode=='full' else 'lower right')
for ax in axes[1]:ax.set_xlabel('Experiment batch (48 measurements)')
for ax in axes[:,0]:ax.set_ylabel('Cumulative max (new tests)')
fig.suptitle('AAV: matched 288-measurement campaigns\nDashed horizontal line: measured candidate-pool maximum',fontsize=12)
fig.tight_layout()
fig.savefig(out/'comparison.png',dpi=160)
