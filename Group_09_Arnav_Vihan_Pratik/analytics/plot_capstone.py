"""Regenerate final-study figures exclusively from retained measured CSVs."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'docs/figures'
def main():
    folder=HERE/'capstone_500hz';df=pd.read_csv(folder/'capstone_real_trials.csv');OUT.mkdir(exist_ok=True)
    trial=folder/'01_32000_shared'
    schema=json.loads((trial/'telemetry_schema.json').read_text())
    d=pd.concat([pd.read_csv(trial/f['path'],low_memory=False) for f in schema['files']])
    ref=np.asarray(schema['path_m'])
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(1,2,figsize=(10,3.1),layout='constrained')
    ax[0].plot(ref[:,0],ref[:,1],'--',color='#999999',label='Fixed evaluation path')
    ax[0].plot(d.x_m,d.y_m,color='#0b6b81',lw=1.5,label='Actual seed 32000')
    ax[0].set(xlabel='x (m)',ylabel='y (m)',title='Measured route and independent reference');ax[0].legend(fontsize=8);ax[0].grid(alpha=.2)
    ax[1].boxplot([df[df.policy==p].goal_error_m for p in ['baseline','shared']],tick_labels=['Reactive baseline','Map + transfer'],showmeans=True)
    ax[1].set(ylabel='Terminal XY goal error (m)',title='30 independent runs per policy');ax[1].grid(axis='y',alpha=.2)
    for ext in ['png','pdf']:fig.savefig(OUT/f'capstone_results.{ext}',dpi=180)
    plt.close(fig)
    fig,ax=plt.subplots(2,1,figsize=(4.6,4.5),layout='constrained')
    ax[0].plot(ref[:,0],ref[:,1],'--',color='gray',label='Evaluation reference')
    ax[0].plot(d.x_m,d.y_m,color='#0b6b81',label='Actual seed 32000')
    ax[0].set(xlabel='x (m)',ylabel='y (m)');ax[0].legend(fontsize=8)
    ax[1].boxplot([df[df.policy==p].goal_error_m for p in ['baseline','shared']],tick_labels=['Reactive baseline','Map + transfer'],showmeans=True)
    ax[1].set(ylabel='Final goal error (m)',title='30 independent trials per policy')
    for a in ax:a.grid(alpha=.2)
    fig.savefig(OUT/'capstone_results_paper.pdf');plt.close(fig)
    fig,ax=plt.subplots(figsize=(6.5,3.2));ax.set(xlim=(0,10),ylim=(0,6));ax.axis('off')
    boxes=[(2,5,'Remote goal / delayed intent'),(7.7,5,'MuJoCo M20 / contacts'),(2,3,'50 Hz ideal rays + true pose\n5 cm course elevation grid'),(7.7,3,'A* / docking / paired transfer\nlocal contact and tilt gates'),(5,.9,'500 Hz torque-limited leg/hub control\n500 Hz scientific CSV; 50 Hz replay')]
    for x,y,label in boxes:ax.text(x,y,label,ha='center',va='center',fontsize=10,bbox=dict(boxstyle='round',fc='#edf3f5',ec='#456b80'))
    for xy,xytext in [((7.5,3.5),(2,4.6)),((2,3.5),(7.7,4.6)),((6,3),(3.6,3)),((5,1.5),(7.7,2.5)),((7.7,4.6),(5,.9))]:ax.annotate('',xy=xy,xytext=xytext,arrowprops=dict(arrowstyle='->',color='#456b80'))
    fig.tight_layout();fig.savefig(OUT/'capstone_system_architecture.pdf');plt.close(fig)
    d=pd.read_csv(HERE/'capstone_checks/pilot_42/telemetry.csv')
    fig,ax=plt.subplots(2,1,figsize=(6.4,4),sharex=True,layout='constrained')
    ax[0].plot(d.time_s,d.z_m,label='Torso z')
    for leg in ['fl','fr','hl','hr']:ax[0].plot(d.time_s,d[leg+'_z_m']-.093,label=leg+' foot bottom',lw=.8)
    ax[0].set(ylabel='Height (m)');ax[0].legend(ncol=3,fontsize=7)
    ax[1].plot(d.time_s,d.max_torque_Nm,color='#0b6b81');ax[1].axhline(76.4,ls='--',color='gray')
    ax[1].set(xlabel='Simulated time (s)',ylabel='Max |torque| (N m)')
    for a in ax:a.grid(alpha=.2)
    for ext in ['png','pdf']:fig.savefig(OUT/f'capstone_climb_telemetry.{ext}',dpi=180)
    plt.close(fig)
    fig,ax=plt.subplots(1,2,figsize=(10,3),layout='constrained')
    from hazardous_recon_economics import economics,queue_model
    k=np.linspace(.05,.95,100)
    ax[0].plot(k,[economics(operating_parity=x)['P_payback'] for x in k],label='Lifetime payback fraction')
    ax[0].plot(k,1-k,label='NCRI');ax[0].axhline(1,ls=':',color='gray');ax[0].legend(fontsize=8)
    ax[0].set(xlabel='Assumed operating parity κ',ylabel='Dimensionless',title='Capital 0.30; lifetime 5 years')
    rho=np.linspace(.05,.95,100)
    ax[1].plot(rho,[queue_model(arrival_per_week=12*r)['Wq_work_hours'] for r in rho])
    ax[1].scatter([2/3],[20/3],color='orange');ax[1].set(xlabel='Assumed utilization ρ',ylabel='Queue wait (working hours)',title='M/M/1; μ = 12/week; 40 h/week')
    for a in ax:a.grid(alpha=.2)
    for ext in ['png','pdf']:fig.savefig(OUT/f'capstone_economics_small.{ext}',dpi=180)
    plt.close(fig)
if __name__=='__main__':main()
