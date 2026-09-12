"""GB1: separate LLM/low-HD and deterministic/random cold-start campaigns."""
from common import plt, data, curve, save

def main():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
    styles = [('random', 'Random', 7, 'o', '-'), ('greedy', 'Greedy', 0, 's', '-'),
              ('agent_no_knowledge', 'Agent: no knowledge', 2, '^', '--'),
              ('knowledge_agent', 'Knowledge agent', 1, 'D', ':')]
    for ax, key, title in zip(axes, ['gb1_llm','gb1_easy'],
        ['a  LLM campaign / low-HD cold start', 'b  Deterministic / random cold start']):
        d = data(key)
        for k, label, c, m, ls in styles:
            curve(ax, d['strategies'][k]['rounds'], label, c, m, ls)
        ax.axhline(8.761966, color='#999999', ls=':', lw=1)
        ax.set(title=title, xticks=[96,192,288], ylim=(0,9.3))
        ax.legend(loc='lower right', fontsize=7.5, ncol=2, frameon=False)
    fig.suptitle('GB1 | Four strategies across three measurement rounds', fontsize=16, x=.06, ha='left')
    fig.text(.06,.045,'Recorded runs (seed 42); no replicate confidence intervals. Steps join observed round endpoints.\nFWAA = 8.761966. Knowledge agent reaches FWAA at round 2 in both campaigns.', fontsize=9)
    fig.subplots_adjust(left=.07,right=.98,bottom=.23,top=.83,wspace=.25)
    save(fig, 'fig2_gb1_convergence')

if __name__ == '__main__': main()
