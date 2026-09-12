"""AAV recorded trajectories; version comparison is not a paired causal estimate."""
from common import plt, data, curve, save

def main():
    fig, axes = plt.subplots(1, 3, figsize=(16,6))
    for key,label,c,m in [('aav_v01','v0.1 agent',7,'o'),('aav_v02','v0.2 gated agent',0,'s'),
                          ('aav_v04','v0.4 agent',2,'^'),('aav_v05','v0.5 agent',3,'D'),
                          ('aav_greedy','v0.4 deterministic',1,'v')]:
        curve(axes[0],data(key)['rounds'],label,c,m)
    axes[0].set(title='a  Observed version trajectories',ylim=(1,9))
    axes[0].legend(fontsize=8,frameon=False,loc='lower right')
    for seed,c,m in [(0,0,'o'),(7,3,'s'),(42,1,'D')]:
        curve(axes[1],data(f'aav_alternating_{seed}')['rounds'],f'Alternating: seed {seed}',c,m, '--' if seed==7 else '-')
    curve(axes[1],data('aav_mean_42')['rounds'],'Mean: seeds 0, 7, 42 (identical)',7,'^',':')
    axes[1].set(title='b  v0.7: all recorded seeds',ylim=(7.25,8.65))
    axes[1].annotate('Seed 42: 8.4162\nat 192 measurements',xy=(192,8.4162),xytext=(68,8.55),
                     fontsize=9,arrowprops={'arrowstyle':'->','color':'#555555'})
    axes[1].legend(fontsize=8,frameon=False,loc='lower right')
    keys=['aav_v04','aav_v05','aav_mean_42','aav_alternating_0','aav_alternating_7','aav_alternating_42']
    labels=['v0.4 agent','v0.5 agent','v0.7 mean (all)','v0.7 alt. seed 0','v0.7 alt. seed 7','v0.7 alt. seed 42']
    gap=[data('aav_greedy')['summary']['final_cum_top10_max']-data(k)['summary']['final_cum_top10_max'] for k in keys]
    axes[2].barh(labels,gap,color=['#D55E00','#CC79A7','#737373','#0072B2','#CC79A7','#009E73'],height=.6)
    axes[2].invert_yaxis()
    for i,v in enumerate(gap): axes[2].text(v+.03,i,f'{v:.4f}',va='center',fontsize=9)
    axes[2].set(title='c  Final gap to v0.4 reference',xlabel='8.4162 − final best fitness',xlim=(0,2.3))
    axes[2].grid(axis='x',alpha=.2)
    for ax in axes[:2]:
        ax.set_xticks([48,96,144,192,240,288])
        ax.axhline(8.4162,color='#999999',ls=':',lw=1)
    fig.suptitle('AAV | Exploration allocation and backtracking outcomes',fontsize=17,x=.05,ha='left')
    fig.text(.05,.045,'New queries only; cold-start incumbents excluded. v0.2 spends 284 measurements; other displayed runs spend 288.\nVersion gaps are descriptive, not isolated causal exploration-tax estimates. v0.7 alternating reaches 8.4162 in 1 of 3 seeds.',fontsize=10)
    fig.subplots_adjust(left=.055,right=.98,bottom=.23,top=.84,wspace=.53)
    save(fig,'fig4_aav_exploration_tax')

if __name__ == '__main__': main()
