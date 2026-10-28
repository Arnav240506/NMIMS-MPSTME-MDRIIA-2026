"""Figures from verified M20 telemetry/results; architecture is a method diagram."""
from pathlib import Path
import json
import numpy as np,pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'docs/figures';OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.size':8,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','savefig.bbox':'tight'})

def save(fig,name):
    fig.savefig(OUT/(name+'.png'),dpi=300);fig.savefig(OUT/(name+'.pdf'));plt.close(fig)

def main():
    fig,ax=plt.subplots(figsize=(3.4,1.85));ax.set_xlim(0,10);ax.set_ylim(0,7);ax.axis('off')
    boxes=[(2,6,'Remote goal / delayed intent'),(7.6,6,'MuJoCo M20 / contacts'),(2,3.8,'50 Hz rays + true pose\n3 cm elevation grid'),(7.6,3.8,'A* / docking / paired climb\nlocal safety governor'),(4.8,1.2,'500 Hz torque-limited leg/hub servo\n100 Hz wrench allocation + IK')]
    for x,y,t in boxes:ax.text(x,y,t,ha='center',va='center',bbox=dict(boxstyle='round,pad=.4',fc='#edf4f8',ec='#3a6479'),fontsize=6.4)
    for a,b in [((7.6,5.4),(2.4,4.4)),((3.5,3.8),(5.7,3.8)),((2.9,5.5),(6.5,4.4)),((7.6,3.1),(5.7,1.8)),((5.5,1.8),(8.6,5.4))]:
        ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',color='#405b68',lw=.9))
    ax.text(.1,0,'Sensors: ideal intersections; no ROS nodes or SLAM loop closure',fontsize=6.3)
    save(fig,'figure1_system_architecture')
    folder=HERE/'demo_runs/m20_mission';d=pd.read_csv(folder/'telemetry.csv')
    fig,axs=plt.subplots(4,1,figsize=(3.4,3.0),sharex=True,layout='constrained')
    axs[0].plot(d.time_s,d.z_m,label='base z');axs[0].set_ylabel('Height (m)')
    for leg in ['fl','fr','hl','hr']:axs[1].plot(d.time_s,d[leg+'_z_m']-.093,label=leg)
    axs[1].set_ylabel('Foot bottom\nheight (m)');axs[1].legend(ncol=4,fontsize=5.5,loc='upper left')
    axs[2].plot(d.time_s,d.roll_deg,label='roll');axs[2].plot(d.time_s,d.pitch_deg,label='pitch');axs[2].set_ylabel('Tilt (deg)');axs[2].legend(ncol=2,fontsize=6)
    axs[3].plot(d.time_s,d.max_torque_Nm,color='#d3732d');axs[3].set_ylabel('Peak motor\ntorque (N m)');axs[3].set_xlabel('MuJoCo simulated time (s), mission seed 42')
    save(fig,'figure2_kinematic_telemetry')
    df=pd.read_csv(HERE/'benchmark/results.csv');stats=json.loads((HERE/'benchmark/statistics.json').read_text())
    fig,axs=plt.subplots(1,2,figsize=(3.4,2.05),layout='constrained')
    policies=['baseline','shared'];colors=['#9f5e4c','#278d88']
    rates=[100*df[df.policy==p].accepted.mean() for p in policies]
    axs[0].bar(policies,rates,color=colors,width=.6);axs[0].set_ylim(0,108);axs[0].set_ylabel('Accepted missions (%)')
    for i,p in enumerate(policies):axs[0].text(i,rates[i]+3,f'{stats["policies"][p]["accepted"]}/50',ha='center',fontsize=7)
    axs[1].boxplot([df[df.policy==p].goal_error_m for p in policies],tick_labels=policies,widths=.5,showfliers=True)
    axs[1].set_ylabel('Final goal error (m)')
    for a in axs:a.tick_params(axis='x',labelrotation=20,labelsize=7)
    save(fig,'figure3_comparative_performance')
    a=np.load(folder/'map.npz');fig,ax=plt.subplots(figsize=(3.4,2.5),layout='constrained')
    masked=np.ma.masked_where(a['count']==0,a['mean']);im=ax.imshow(masked,origin='lower',extent=a['bounds'][[0,1,2,3]],vmin=0,vmax=.3,cmap='terrain',aspect='equal')
    ax.plot(d.x_m,d.y_m,color='#2c8d91',label='actual base trajectory');ax.set(xlabel='x (m)',ylabel='y (m)');ax.legend(fontsize=6)
    fig.colorbar(im,ax=ax,label='Measured elevation (m)',shrink=.75)
    save(fig,'figure4_measured_map')
    (OUT/'FIGURE_SOURCES.json').write_text(json.dumps({'figure1':'Implemented module diagram, not experimental data',
       'figure2':str(folder.relative_to(HERE.parent)/'telemetry.csv'),'figure3':'analytics/benchmark/results.csv',
       'figure4':'analytics/demo_runs/m20_mission/map.npz and telemetry.csv','all_data_figures':'MuJoCo simulation only; no human participants'},indent=2))

if __name__=='__main__':main()
