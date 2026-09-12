"""Proposed five-machine RSI control flow with independent verification."""
from common import plt, box, arrow, save

def main():
    fig,ax=plt.subplots(figsize=(13,8))
    ax.set(xlim=(0,1),ylim=(0,1)); ax.axis('off')
    fig.suptitle('Five-machine RSI | Operational loop and governed improvement',x=.05,ha='left',fontsize=17)
    ax.text(.03,.94,'INNER LOOP / DBTL',weight='bold',fontsize=12,color='#0072B2')
    box(ax,.04,.67,.24,.20,'1  Executor','Design → build → test\nCurrent model + tools',0)
    box(ax,.38,.67,.24,.20,'2  Verifier','Read-only evaluation\nPhysical / contract checks',2)
    box(ax,.72,.67,.24,.20,'3  Controller','Accept / reject / backtrack\nBudget + stopping rules',1)
    arrow(ax,(.29,.77),(.37,.77)); arrow(ax,(.63,.77),(.71,.77))
    ax.plot([.84,.84,.16,.16],[.88,.91,.91,.88],lw=1.2,color='#737373')
    arrow(ax,(.16,.91),(.16,.88))
    box(ax,.20,.43,.60,.12,'Causal ledger: Event → Fact → Decision → Task','Content pins / negative results / provenance / new evidence',6)
    arrow(ax,(.50,.66),(.50,.56),6)
    arrow(ax,(.84,.66),(.76,.56),6)
    ax.text(.03,.035,'OUTER LOOP / PROPOSED META-EVOLUTION',weight='bold',fontsize=12,color='#009E73')
    box(ax,.06,.10,.28,.18,'4  Memory','Retrieve evidence\nCompare competing explanations',6)
    box(ax,.57,.10,.34,.18,'5  Improver','Counterfactual diagnosis\nCandidate patch in shadow sandbox',1)
    arrow(ax,(.30,.42),(.20,.29),6)
    arrow(ax,(.35,.19),(.56,.19),1)
    ax.text(.44,.225,'Evidence',ha='center',fontsize=9)
    arrow(ax,(.74,.29),(.74,.42),1)
    # Governed promotion returns to verifier; no direct improver-to-executor edge.
    ax.plot([.92,.99,.99,.56,.56],[.19,.19,.60,.60,.66],color='#D55E00',lw=1.3,ls='--')
    arrow(ax,(.56,.60),(.56,.66),2)
    ax.text(.96,.36,'Independent regression gate',rotation=90,ha='center',va='center',fontsize=9,color='#D55E00')
    fig.text(.05,.035,'Design proposal, not a claim of deployed autonomous RSI. Failed validation retains the current model; evaluation criteria remain outside patch authority.',fontsize=9)
    fig.subplots_adjust(left=.025,right=.985,bottom=.07,top=.9)
    save(fig,'fig5_five_machine_rsi')

if __name__ == '__main__': main()
