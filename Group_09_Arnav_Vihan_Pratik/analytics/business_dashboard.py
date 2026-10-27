"""Live CSBS assumptions and sensitivity graphs; no currency or field-savings claim."""
from pathlib import Path
import argparse,json
import numpy as np
from hazardous_recon_economics import economics,queue_model

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--headless',action='store_true')
    p.add_argument('--out',type=Path,default=Path(__file__).resolve().parents[1]/'docs/figures/capstone_business')
    a=p.parse_args()
    import matplotlib
    if a.headless:matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.widgets import Slider,Button
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white'})
    fig,axes=plt.subplots(2,2,figsize=(12.8,8.2))
    fig.subplots_adjust(left=.08,right=.96,top=.84,bottom=.23,hspace=.5,wspace=.30)
    fig.suptitle('M20 Group 09 CSBS Business Model',fontsize=18,fontweight='bold',y=.97)
    fig.text(.5,.925,'Planning assumptions | No measured plant savings | Edit inputs and explain the change',ha='center',fontsize=11)
    status=fig.text(.5,.875,'',ha='center',fontsize=10)
    axes_sl=[fig.add_axes([.17,.145,.68,.025]),fig.add_axes([.17,.10,.68,.025]),fig.add_axes([.17,.055,.68,.025])]
    sliders=[Slider(axes_sl[0],'Operating parity',.05,1.2,valinit=.22),
             Slider(axes_sl[1],'Capital parity',0.,1.,valinit=.30),
             Slider(axes_sl[2],'Requests / week',0.,14.,valinit=8.)]
    reset_ax=fig.add_axes([.87,.008,.09,.03]);reset=Button(reset_ax,'Reset')
    def draw(_=None):
        op,cap,lam=[s.val for s in sliders];e=economics(op,capex_parity=cap);q=queue_model(lam)
        ks=np.linspace(.05,1.2,240);pay=[economics(k,capex_parity=cap)['P_payback'] for k in ks]
        for ax in axes.ravel():ax.clear();ax.grid(alpha=.2)
        ax=axes[0,0];ax.plot(ks,[np.nan if v is None else v for v in pay],color='#247c86')
        ax.axhline(1,color='#9c5b41',ls='--',label='Lifetime break-even');ax.axvline(1,color='#777',ls=':')
        if e['P_payback'] is not None:ax.scatter([op],[e['P_payback']],color='#9c5b41',zorder=3)
        ax.set(xlabel='Operating parity kappa',ylabel='Normalized payback P',title='Capital and five-year lifetime',ylim=(0,2.));ax.legend(fontsize=8)
        ax=axes[0,1];ax.plot(ks,1-ks,color='#735882');ax.axhline(0,color='#777',ls='--');ax.scatter([op],[e['NCRI']],color='#9c5b41',zorder=3)
        ax.set(xlabel='Operating parity kappa',ylabel='NCRI = 1 - kappa',title='Relative cost reduction scenario')
        ax=axes[1,0];rhos=np.linspace(0,.95,150)
        ax.plot(rhos,[queue_model(r*12)['Wq_work_hours'] for r in rhos],color='#247c86')
        if q['stable']:ax.scatter([q['rho']],[q['Wq_work_hours']],color='#9c5b41',zorder=3)
        ax.set(xlabel='Utilization rho = lambda / mu',ylabel='Queue waiting in working hours',title='M/M/1 | service 12/week | 40-hour week',xlim=(0,1.))
        ax=axes[1,1];hours=np.array([218.4,312.,405.6]);ax.bar(['-30%','Base','+30%'],hours/2080,color=['#b7c9ce','#247c86','#b7c9ce'])
        for i,h in enumerate(hours):ax.text(i,h/2080+.006,f'{h:g} h/year',ha='center',fontsize=9)
        ax.set(ylabel='Reallocated FTE',title='Assumed labor reallocation',ylim=(0,.24))
        paytext='No finite positive payback' if e['payback_months'] is None else f'Payback {e["payback_months"]:.3f} months | P {e["P_payback"]:.4f}'
        qtext=f'Wq {q["Wq_work_hours"]:.3f} working hours' if q['stable'] else 'Unstable queue: no finite steady-state delay'
        status.set_text(f'{paytext} | NCRI {e["NCRI"]:.3f} | {qtext}')
        fig.canvas.draw_idle()
    for slider in sliders:slider.on_changed(draw)
    reset.on_clicked(lambda event:[s.reset() for s in sliders]);draw()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(a.out.with_suffix('.png'),dpi=180);fig.savefig(a.out.with_suffix('.pdf'))
    a.out.with_suffix('.json').write_text(json.dumps({'base_case':economics(),'queue':queue_model(),
        'source':'hazardous_recon_economics.py; every business input is an explicit scenario assumption',
        'relations':['P = capital parity / (lifetime years * net annual savings parity)','NCRI = 1 - kappa','M/M/1 Wq = lambda / (mu * (mu-lambda))','FTE = reclaimed annual hours / 2080']},indent=2))
    if not a.headless:plt.show()
    else:plt.close(fig)

if __name__=='__main__':main()
