"""Shared 9-color palette, typography and PNG/SVG export."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'reports/figures'
COLORS = ['#0072B2', '#009E73', '#D55E00', '#CC79A7', '#56B4E9', '#E69F00', '#5B5F97', '#737373', '#222222']
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.titlesize': 12,
    'axes.labelsize': 10, 'axes.spines.top': False, 'axes.spines.right': False,
    'axes.linewidth': .8, 'lines.linewidth': 2, 'svg.fonttype': 'none',
    'savefig.facecolor': 'white', 'figure.facecolor': 'white'})

def data(key):
    return json.loads((ROOT / 'artifacts/figures_data' / f'{key}.json').read_text())

def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ('png', 'svg'):
        path = OUT / f'{name}.{ext}'
        fig.savefig(path, dpi=300, metadata={'Creator': 'Scientific figures: reproducible Matplotlib'}) if ext == 'svg' else fig.savefig(path, dpi=300)
        if ext == 'svg':
            path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines()) + '\n')
        print(path.relative_to(ROOT))
    plt.close(fig)

def box(ax, x, y, w, h, title, body='', color=0):
    c = COLORS[color]
    ax.add_patch(FancyBboxPatch((x,y), w,h, boxstyle='round,pad=0.012,rounding_size=0.018',
                              facecolor=c+'12', edgecolor=c, linewidth=1.3))
    ax.text(x+w/2, y+h*.68 if body else y+h/2, title, ha='center', va='center', weight='bold', fontsize=11, color=c)
    if body:
        ax.text(x+w/2, y+h*.30, body, ha='center', va='center', fontsize=9, linespacing=1.5)

def arrow(ax, a, b, color=7, style='-', rad=0):
    ax.add_patch(FancyArrowPatch(a,b, arrowstyle='-|>', mutation_scale=12,
                               color=COLORS[color], lw=1.2, linestyle=style,
                               connectionstyle=f'arc3,rad={rad}'))

def curve(ax, rows, label, color, marker='o', linestyle='-'):
    ax.plot([r['spent_after'] for r in rows], [r['cum_top10_max'] for r in rows],
            label=label, color=COLORS[color], marker=marker, linestyle=linestyle,
            markersize=6, markerfacecolor='white', drawstyle='steps-post')
    ax.grid(axis='y', alpha=.2)
    ax.set_xlabel('Newly measured variants (cumulative)')
    ax.set_ylabel('Best newly measured fitness')
