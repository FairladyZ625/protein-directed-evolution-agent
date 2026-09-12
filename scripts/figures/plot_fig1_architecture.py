"""Structured five-role architecture; two controlled LLM ports."""
from common import plt, box, arrow, save

def main():
    fig,ax=plt.subplots(figsize=(14,7))
    ax.set(xlim=(0,1),ylim=(0,1)); ax.axis('off')
    fig.suptitle('Controlled scientific agent | Five roles, two LLM ports',x=.05,ha='left',fontsize=18)
    box(ax,.02,.65,.16,.19,'Data Analyst','Measured pool\nSingle-site statistics',0)
    box(ax,.22,.65,.17,.19,'Hypothesis\nGenerator','LLM port 1 / rule citations',1)
    box(ax,.43,.65,.16,.19,'Mutation\nDesigner','Code / combinations',0)
    box(ax,.63,.65,.16,.19,'Fitness\nEvaluator','Surrogate ensemble',0)
    box(ax,.83,.65,.15,.19,'Scientific Critic','LLM port 2\n+ hard constraints',1)
    for a,b in [(.18,.22),(.39,.43),(.59,.63),(.79,.83)]: arrow(ax,(a,.745),(b,.745))
    box(ax,.23,.34,.30,.16,'Gate 1: candidate shaping','Hamming distance + BLOSUM constraints',5)
    arrow(ax,(.38,.51),(.5,.64),5)
    box(ax,.63,.34,.34,.16,'Gate 2: deterministic veto','Reject violations before measurement',2)
    arrow(ax,(.905,.64),(.905,.51),2)
    box(ax,.02,.34,.16,.16,'Measure + learn','Accepted batch only',0)
    # Measurement route passes below gate 1 to avoid implying gate 2 feeds gate 1.
    ax.plot([.62,.58,.58,.10,.10],[.42,.42,.28,.28,.33],color='#737373',lw=1.2)
    arrow(ax,(.1,.29),(.1,.34))
    arrow(ax,(.1,.51),(.1,.64),0)
    box(ax,.10,.05,.80,.13,'Append-only causal event ledger','Role outputs / decisions / measurements | SHA-256 hash chain: tamper-evident',6)
    ax.plot([.10,.98],[.91,.91],color='#5B5F97',lw=1,ls=':')
    for x in (.10,.305,.51,.71,.905):
        ax.plot([x,x],[.855,.91],color='#5B5F97',lw=1,ls=':')
    ax.plot([.98,.995,.995,.92],[.91,.91,.115,.115],color='#5B5F97',lw=1,ls=':')
    arrow(ax,(.94,.115),(.915,.115),6,':')
    fig.text(.05,.03,'Architecture schematic. Controlled ports may use deterministic fallbacks; hash chaining detects tampering, not absolute immutability.',fontsize=9)
    fig.subplots_adjust(left=.025,right=.985,bottom=.08,top=.90)
    save(fig,'fig1_agent_architecture')

if __name__ == '__main__': main()
