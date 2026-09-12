"""Analytic schematic, explicitly NOT fitted AAV predictions or physical energies."""
import numpy as np
from common import plt, save, data

def main():
    fig=plt.figure(figsize=(13,6.5))
    x,y=np.meshgrid(np.linspace(-1,1,45),np.linspace(-1,1,45))
    additive=.35*x+.25*y
    pairwise=additive+1.6*x*y  # A two-coordinate interaction term; arbitrary units.
    for i,(z,title,cmap) in enumerate([(additive,'a  Additive surface: a·x + b·y','Blues'),
                                      (pairwise,'b  Pairwise interaction: a·x + b·y + J·xy','PuBuGn')]):
        ax=fig.add_subplot(1,2,i+1,projection='3d')
        ax.plot_surface(x,y,z,cmap=cmap,alpha=.9,linewidth=.15,edgecolor='white',rstride=2,cstride=2)
        ax.set(xlabel='Latent coordinate x',ylabel='Latent coordinate y',zlabel='Schematic score (a.u.)',
               zlim=(-2,2.5),title=title)
        ax.view_init(elev=27,azim=-130)
        ax.set_xticks([-1,0,1]); ax.set_yticks([-1,0,1]); ax.set_zticks([-2,0,2])
    fig.suptitle('Epistasis | Non-additive geometry and an observed AAV target',fontsize=17,x=.05,ha='left')
    target=data('aav_alternating_42')['summary']['final_cum_top10_max']
    fig.text(.07,.14,f'Observed target: D0Q + S17E + V18A  |  QEEEIRTTNPVATEQYGEASTNLQRGNR  |  fitness {target:.4f}',
             fontsize=11,weight='bold',color='#0072B2')
    fig.text(.07,.055,'Both surfaces are analytic illustrations in arbitrary coordinates, not measured or fitted AAV landscapes.\nThe observed target is reported separately: no physical energy, peak coordinates or higher-order coefficients are inferred.',fontsize=10)
    fig.subplots_adjust(left=.025,right=.96,bottom=.25,top=.86,wspace=.12)
    save(fig,'fig3_epistasis_landscape')

if __name__ == '__main__': main()
