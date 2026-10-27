"""Derive dossier quantities from saved physics; never synthesizes trial outcomes."""
from pathlib import Path
import json,csv,bisect,hashlib
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyBboxPatch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=HERE/'dossier'

def rms_to_path(point,path):
    path=np.asarray(path,float)
    if len(path)==1:return float(np.linalg.norm(point-path[0]))
    a=path[:-1];v=path[1:]-a;den=np.einsum('ij,ij->i',v,v)
    t=np.clip(np.einsum('ij,ij->i',point-a,v)/np.maximum(den,1e-15),0,1)
    return float(np.linalg.norm(point-(a+t[:,None]*v),axis=1).min())

def describe(values):
    a=np.asarray(values,float);return {'N':len(a),'mean':float(a.mean()),'sd':float(a.std(ddof=1)) if len(a)>1 else None}

def main():
    OUT.mkdir(exist_ok=True);rows=[]
    for folder in sorted((HERE/'benchmark').glob('*/summary.json')):
        s=json.loads(folder.read_text());a=np.load(folder.parent/'states.npz');t=a['time']
        assert a['ctrl'].shape==(len(t),16) and np.allclose(np.diff(t),.02)
        effort=float(np.trapezoid(np.sum(a['ctrl']**2,axis=1),t))
        rows.append({'trial_id':s['trial_id'],'policy':s['config']['policy'],'seed':s['config']['seed'],
            'source_sha256':s['source_sha256'],'accepted':s['accepted'],'sampled_torque_squared_Nm2_s':effort,
            'goal_error_m':s['goal_error_m'],'states_sha256':hashlib.sha256((folder.parent/'states.npz').read_bytes()).hexdigest()})
    assert len(rows)==100
    pd.DataFrame(rows).to_csv(OUT/'dossier_real_trials.csv',index=False)
    effort={p:describe([r['sampled_torque_squared_Nm2_s'] for r in rows if r['policy']==p]) for p in ['baseline','shared']}
    tracking=[]
    for file in sorted((HERE/'climbing_course').glob('*/summary.json')):
        s=json.loads(file.read_text())
        if s['config']['policy']!='shared':continue
        plans=json.loads((file.parent/'plans.json').read_text());times=[p['time_s'] for p in plans];data=pd.read_csv(file.parent/'telemetry.csv');dist=[]
        for row in data.itertuples(index=False):
            if row.phase not in ('DETOUR_NAV','CRUISE_MAP','PLATEAU_RECON'):continue
            j=bisect.bisect_right(times,row.time_s)-1
            if j<0 or not plans[j]['path_m']:continue
            dist.append(rms_to_path(np.array([row.x_m,row.y_m]),plans[j]['path_m']))
        assert dist
        tracking.append({'trial_id':s['trial_id'],'seed':s['config']['seed'],'samples':len(dist),
            'navigation_cross_track_RMSE_m':float(np.sqrt(np.mean(np.square(dist)))),
            'telemetry_sha256':hashlib.sha256((file.parent/'telemetry.csv').read_bytes()).hexdigest()})
    assert len(tracking)==6
    trace=pd.read_csv(HERE/'climbing_course/00_course_climb_42_shared/telemetry.csv');row=trace.iloc[np.argmin(abs(trace.time_s-2.3))]
    mass=34.525856;weight=mass*9.81
    force={'time_s':float(row.time_s),'mass_kg':mass,'gravity_m_s2':9.81,'weight_N':weight,
        'measured_foot_normals_N':{leg:float(row[leg+'_normal_N']) for leg in ['fl','fr','hl','hr']},
        'support_count':int(row.support_count),'assumed_symmetric_load_per_foot_N':weight/4,
        'illustrative_quarter_m_moment_Nm':weight/4*.25}
    force['measured_normal_sum_N']=sum(force['measured_foot_normals_N'].values())
    metrics={'source':'Existing actual benchmark and combined-course logs; no new trial outcomes generated',
        'sampled_effort':effort,'effort_definition':'Trapezoidal integral of sum of 16 commanded torques squared over saved 50 Hz samples. Proxy in (N m)^2 s; not energy and not a 500 Hz exact integral. Initial/final unsampled intervals excluded.',
        'navigation_tracking':tracking,'navigation_tracking_summary':describe([x['navigation_cross_track_RMSE_m'] for x in tracking]),
        'tracking_definition':'2D nearest-segment distance to most recent actual online plan, navigation phases only. Replanning resets the reference start near the robot, so this is a rolling-path diagnostic, not independent fixed-reference accuracy. Baseline has no comparable saved path; original 100 trials do not retain full plan histories.',
        'force_snapshot':force,'economic_assumptions':{'operating_parity':.22,'reclaimed_value_parity':1.,'capex_parity':.3,'annual_reclaimed_hours':312.,'annual_full_time_hours':2080.}}
    (OUT/'metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    fig,ax=plt.subplots(figsize=(7.4,2.8));ax.axis('off');ax.set_xlim(-1,1);ax.set_ylim(-.75,.8)
    ax.add_patch(Rectangle((-.58,-.02),1.16,.32,facecolor='#edf2f4',edgecolor='#263e4c',lw=1.5));ax.text(0,.15,'M20 body  |  schematic not to scale',ha='center',fontsize=10)
    ax.annotate('',xy=(0,-.55),xytext=(0,.03),arrowprops={'arrowstyle':'->','color':'#aa4e45','lw':2});ax.text(.03,-.42,f'mg = {weight:.2f} N',fontsize=10,color='#aa4e45')
    for x,leg in zip([-.48,-.26,.26,.48],['hl','hr','fl','fr']):
        ax.annotate('',xy=(x,-.04),xytext=(x,-.43),arrowprops={'arrowstyle':'->','color':'#32718a','lw':1.7})
        ax.text(x,-.62,f'{leg.upper()}\n{force["measured_foot_normals_N"][leg]:.2f} N',ha='center',fontsize=9)
    ax.text(0,.57,f'Actual normal-force snapshot at t={force["time_s"]:.3f} s; sum = {force["measured_normal_sum_N"]:.2f} N',ha='center',fontsize=10)
    fig.tight_layout();fig.savefig(OUT/'free_body_diagram.png',dpi=220);plt.close(fig)
    ks=np.array([.12,.22,.45,.8,1.,1.2]);pay=np.where(ks<1,3.6/np.maximum(1-ks,1e-6),np.nan)
    fig,axes=plt.subplots(1,2,figsize=(9,3.3))
    axes[0].plot(ks,pay,'o-',color='#287786');axes[0].axvline(1,color='#ac5d43',ls='--');axes[0].set(xlabel='Operating parity ratio kappa',ylabel='Illustrative payback (months)',title='Assumed parity sensitivity')
    axes[0].text(1.02,7,'No finite\npositive payback\nat kappa >= 1',fontsize=8)
    axes[1].plot(ks,1-ks,'o-',color='#74587e');axes[1].axhline(0,color='#888',lw=.7);axes[1].set(xlabel='Operating parity ratio kappa',ylabel='1 - kappa (dimensionless)',title='Illustrative net parity margin')
    for ax in axes:ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(OUT/'economic_sensitivity.png',dpi=220);plt.close(fig)
    fig,ax=plt.subplots(figsize=(4.2,2.7));ax.plot(ks[:4],pay[:4],'o-',color='#287786');ax.set(xlabel='Operating parity kappa',ylabel='Payback (months)',title='Illustrative assumed sensitivity');ax.grid(alpha=.2);fig.tight_layout();fig.savefig(OUT/'payback_small.png',dpi=220);plt.close(fig)
    fig,ax=plt.subplots(figsize=(4.2,2.7));ax.barh(['Annual reference capacity','Assumed reclaimed task time'],[2080,312],color=['#afbdc6','#287786']);ax.set_xlabel('Hours per year');ax.set_xlim(0,2400)
    ax.text(2120,0,'2080',va='center',fontsize=9);ax.text(350,1,'312 = 0.15 FTE',va='center',fontsize=9);ax.set_title('Assumption scenario\nNo observed savings',fontsize=10);fig.tight_layout();fig.savefig(OUT/'labour_reallocation.png',dpi=220,bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(6,3));data=[[r['sampled_torque_squared_Nm2_s'] for r in rows if r['policy']==p] for p in ['baseline','shared']]
    ax.boxplot(data,tick_labels=['Delayed baseline','Map and transfer']);ax.set_ylabel('Sampled torque-squared integral\n((N m)^2 s)',fontsize=10);ax.set_title('Original 50 matched environments; all failures retained',fontsize=10);ax.grid(axis='y',alpha=.2);fig.tight_layout();fig.savefig(OUT/'sampled_control_effort.png',dpi=220,bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(4.2,2.7));ax.boxplot([[r['goal_error_m'] for r in rows if r['policy']==p] for p in ['baseline','shared']],tick_labels=['Baseline','Shared']);ax.set_ylabel('Final goal error (m)');ax.set_title('50 trials per policy including failures',fontsize=10);ax.grid(axis='y',alpha=.2);fig.tight_layout();fig.savefig(OUT/'goal_error_boxplot.png',dpi=220);plt.close(fig)
    plans=json.loads((HERE/'climbing_course/00_course_climb_42_shared/plans.json').read_text());snapshot=max((p for p in plans if p['time_s']<=30.002),key=lambda p:p['time_s']);route=np.asarray(snapshot['path_m'])
    fig,ax=plt.subplots(figsize=(4.2,2.7));ax.plot(trace.x_m,trace.y_m,color='#95a1a8',label='Full recorded trajectory',lw=1.);ax.plot(route[:,0],route[:,1],color='#178673',label='Online route near 30 s',lw=1.6);ax.set(xlabel='World x (m)',ylabel='World y (m)',title='Seed 42 measured route context');ax.legend(fontsize=7,loc='upper right',frameon=False);ax.grid(alpha=.2);fig.tight_layout();fig.savefig(OUT/'representative_route.png',dpi=220);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4.4));ax.axis('off');ax.set_xlim(0,10);ax.set_ylim(0,5)
    boxes=[(.2,3.8,2.7,.8,'Actual M20 scene\n16 motors and rigid contacts'),(3.6,3.8,2.7,.8,'Ideal rays + exact pose\n3 cm yard / 5 cm course'),(7,3.8,2.7,.8,'Elevation and risk grid\nunknown cells blocked'),(7,2,2.7,.9,'A* route + docking\npaired terrace transfer'),(3.6,2,2.7,.9,'500 Hz torque servo\n100 Hz wrench allocation'),(.2,2,2.7,.9,'MuJoCo 2 ms step\ncontact audit every step'),(3.6,.2,2.7,.9,'50 Hz CSV and states\n5 Hz recorded route history')]
    for x,y,w,h,text in boxes:ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.04',facecolor='#eef3f5',edgecolor='#35576c'));ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=10)
    for p1,p2 in [((2.95,4.2),(3.55,4.2)),((6.35,4.2),(6.95,4.2)),((8.35,3.75),(8.35,2.95)),((6.95,2.45),(6.35,2.45)),((3.55,2.45),(2.95,2.45)),((1.55,2.95),(1.55,3.75)),((1.55,1.95),(3.55,.65)),((8.35,1.95),(6.35,.65))]:ax.annotate('',xy=p2,xytext=p1,arrowprops={'arrowstyle':'->','color':'#35576c','lw':1.5})
    fig.tight_layout();fig.savefig(OUT/'current_architecture.png',dpi=220);plt.close(fig)
    print(json.dumps({'sampled_effort':effort,'navigation_tracking_summary':metrics['navigation_tracking_summary'],'force_snapshot':force},indent=2))

if __name__=='__main__':main()
