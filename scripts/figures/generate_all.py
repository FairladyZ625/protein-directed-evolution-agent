"""Render all five figures without external services or model training."""
from plot_fig1_architecture import main as fig1
from plot_fig2_gb1_convergence import main as fig2
from plot_fig3_epistasis_landscape import main as fig3
from plot_fig4_exploration_tax import main as fig4
from plot_fig5_cybernetic_loop import main as fig5

if __name__ == '__main__':
    for render in (fig1,fig2,fig3,fig4,fig5): render()
