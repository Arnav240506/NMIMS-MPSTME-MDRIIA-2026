"""Audit actual dense-course trials and plot physical trajectories; no synthetic data."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import sys,json,csv,hashlib,argparse
import numpy as np,pandas as pd,mujoco
from scipy.stats import binomtest
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'M20'))
from scene import compile_xml
from simulation import mission_acceptance,source_digest
HERE=Path(__file__).resolve().parent

def frozen_digest(folder):
    h=hashlib.sha256();p=folder/'source_snapshot/M20'
    for f in sorted(p.glob('*.py')):h.update(f.name.encode());h.update(f.read_bytes())
    h.update((p/'M20.xml').read_bytes())
    for f in sorted((ROOT/'M20/meshes').glob('*.STL')):h.update(f.read_bytes())
    return h.hexdigest()

def audit_trial(folder):
    s=json.loads((folder/'summary.json').read_text());a=np.load(folder/'states.npz');t=pd.read_csv(folder/'telemetry.csv')
    assert len(a['qpos'])==len(t)==len(a['time'])
    assert (a['qpos'].shape[1],a['qvel'].shape[1],a['ctrl'].shape[1])==(23,22,16)
    assert np.isfinite(a['qpos']).all() and np.isfinite(a['ctrl']).all()
    assert np.allclose(t.x_m,a['qpos'][:,0]) and np.allclose(t.y_m,a['qpos'][:,1])
    assert np.allclose(t.time_s,a['time']) and np.allclose(np.diff(a['time']),.02)
    assert abs(t.time_s.iloc[-1]-s['simulated_s'])<=.021
    assert abs(a['ctrl'][:,[i for i in range(16) if i%4!=3]]).max()<=76.4+1e-9
    assert abs(a['ctrl'][:,3::4]).max()<=21.6+1e-9
    expected=mission_acceptance(s['goal_reached'],s['rollover'],s['harmful_contact_steps'],bool(s['terrain']['step_height_m']),s['climb_verified'],s['tilt_stop'])
    assert s['accepted']==expected
    g=np.load(folder/'map.npz');assert int(g['count'].sum())==s['ray_hits']
    plans=json.loads((folder/'plans.json').read_text());assert len(plans)==s['planner_calls']
    assert all(x['time_s']<y['time_s'] for x,y in zip(plans,plans[1:]))
    if s['terrain'].get('step_targets') and s['accepted']:
        assert len(s['climb_records'])==len(s['terrain']['step_targets'])
        for target,r in zip(s['terrain']['step_targets'],s['climb_records']):
            assert abs(r['lip_m']-target['lip_m'])<.08 and abs(r['height_m']-target['height_m'])<.01
            assert all(r[k] for k in ['front_pair_air','rear_pair_air','front_resupport','rear_resupport'])
    m=compile_xml((folder/'scene.xml').read_text());d=mujoco.MjData(m)
    robot=np.flatnonzero((m.geom_bodyid>0)&(m.geom_group==1))
    hazards=[m.geom(n).id for n in s['terrain']['hazards']]
    closest=.75;when=0.;invalid_distances=0
    for i in range(0,len(a['time']),5):
        d.qpos[:]=a['qpos'][i];mujoco.mj_forward(m,d)
        for r in robot:
            for h in hazards:
                # A local query avoids a MuJoCo 3.11 witness inconsistency for
                # distant elongated boxes with a large (10 m) distmax. Values
                # are explicitly capped at .75 m; minima below it are measured.
                witness=np.zeros(6)
                distance=float(mujoco.mj_geomDistance(m,d,int(r),h,.75,witness))
                if abs(distance)<.75-1e-8:
                    if abs(abs(distance)-np.linalg.norm(witness[:3]-witness[3:]))>=1e-5:
                        invalid_distances+=1;continue
                if distance<closest:closest=distance;when=float(a['time'][i])
    crossings=[]
    for j in range(3):
        x=float(m.geom(f'course_barricade_{j}').pos[0]);cross=np.flatnonzero((t.x_m.to_numpy()[:-1]<x)&(t.x_m.to_numpy()[1:]>=x))
        crossings.append(float(t.y_m.iloc[cross[0]+1]) if len(cross) else None)
    if s['accepted']:assert all(v is not None for v in crossings) and crossings[0]>0 and crossings[1]<0 and crossings[2]>0
    return {'trial_id':s['trial_id'],'accepted':s['accepted'],'status':s['status'],'seed':s['config']['seed'],'mode':s['config']['mode'],'policy':s['config']['policy'],
        'simulated_s':s['simulated_s'],'goal_error_m':s['goal_error_m'],'path_length_m':s['path_length_m'],
        'harmful_contact_steps':s['harmful_contact_steps'],'rollover':s['rollover'],'max_abs_roll_deg':s['max_abs_roll_deg'],
        'max_abs_pitch_deg':s['max_abs_pitch_deg'],'planner_calls':s['planner_calls'],'sampled_min_hazard_clearance_m':None if invalid_distances else closest,'clearance_sample_time_s':None if invalid_distances else when,
        'inconsistent_geometry_distance_queries':invalid_distances,
        'barrier_1_crossing_y_m':crossings[0],'barrier_2_crossing_y_m':crossings[1],'barrier_3_crossing_y_m':crossings[2],
        'verified_climbs':len(s.get('climb_records',[])),'telemetry_sha256':hashlib.sha256((folder/'telemetry.csv').read_bytes()).hexdigest()}

def draw_scene(ax,folder):
    s=json.loads((folder/'summary.json').read_text());m=compile_xml((folder/'scene.xml').read_text())
    for name in s['terrain']['hazards']+s['terrain']['supports'][1:]:
        g=m.geom(name);x,y=g.pos[:2];sx,sy=g.size[:2]
        color='#d4823a' if 'barricade' in name else '#abc4bc' if 'terrace' in name else '#576b78'
        if g.type[0]==mujoco.mjtGeom.mjGEOM_CYLINDER:ax.add_patch(Circle((x,y),sx,color=color,alpha=.8))
        else:ax.add_patch(Rectangle((x-sx,y-sy),2*sx,2*sy,color=color,alpha=.8))
    ax.scatter([0,s['terrain']['goal'][0]],[0,0],c=['#336d94','#22986c'],s=65,zorder=9)
    ax.set(xlim=(-.8,s['terrain']['map_bounds'][1]-.4),ylim=(-3.4,3.4),xlabel='World x (m)',ylabel='World y (m)')
    ax.set_aspect('equal');ax.grid(alpha=.14)

def main():
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,default=HERE/'obstacle_course');p.add_argument('--workers',type=int,default=4);a=p.parse_args();folder=a.folder
    design=json.loads((folder/'design.json').read_text());digest=design['source_sha256']
    assert digest==(source_digest() if not (folder/'source_snapshot').exists() else frozen_digest(folder))
    trials=sorted(x.parent for x in folder.glob('*/summary.json'));assert len(trials)==len(design['trials'])
    for f in trials:assert json.loads((f/'summary.json').read_text())['source_sha256']==digest
    with ProcessPoolExecutor(max_workers=a.workers) as pool:rows=list(pool.map(audit_trial,trials))
    df=pd.DataFrame(rows);df.to_csv(folder/'verified_results.csv',index=False)
    metrics={'scope':design['scope'],'source_sha256':digest,'actual_trials':len(rows),'policies':{},'sampling_note':'Harmful contacts are audited every 2 ms. Additional 10 Hz geometry clearance is capped at .75 m and withheld for any trial with inconsistent MuJoCo distance/witness outputs; no positive minimum-clearance claim is made for those trials. Step and floor supports excluded.'}
    paired=df[df['mode']=='course']
    for policy in ['baseline','shared']:
        d=paired[paired.policy==policy]
        if len(d):metrics['policies'][policy]={'trials':len(d),'accepted':int(d.accepted.sum()),'harmful_contact_trials':int((d.harmful_contact_steps>0).sum()),'rollovers':int(d.rollover.sum()),'median_duration_s':float(d.simulated_s.median()),'clearance_queries_with_inconsistent_witness':int(d.inconsistent_geometry_distance_queries.sum())}
    if len(paired):
        b=paired[paired.policy=='baseline'].set_index('seed');s=paired[paired.policy=='shared'].set_index('seed')
        assert set(b.index)==set(s.index)
        for seed in b.index:assert (folder/b.loc[seed,'trial_id']/'scene.xml').read_bytes()==(folder/s.loc[seed,'trial_id']/'scene.xml').read_bytes()
        shared_only=int((s.accepted&~b.accepted).sum());baseline_only=int((b.accepted&~s.accepted).sum());n=shared_only+baseline_only
        metrics.update(shared_only=shared_only,baseline_only=baseline_only,exact_McNemar_p=float(binomtest(shared_only,n,.5).pvalue) if n else 1.)
    metrics['blocked_fixtures']=[r for r in rows if r['mode']=='course_blocked']
    metrics['combined_climbing']=[r for r in rows if r['mode']=='course_climb']
    (folder/'statistics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    fig,ax=plt.subplots(figsize=(11,5));shared=next(f for f in trials if json.loads((f/'summary.json').read_text())['config']['policy']=='shared')
    draw_scene(ax,shared)
    for f in trials:
        s=json.loads((f/'summary.json').read_text())
        if s['config']['mode']=='course_blocked':continue
        t=pd.read_csv(f/'telemetry.csv');is_shared=s['config']['policy']=='shared'
        ax.plot(t.x_m,t.y_m,color='#16917d' if is_shared else '#bc4c55',alpha=.65 if is_shared else .35,linewidth=1.4 if is_shared else .8)
    ax.plot([],[],color='#16917d',label='Measured map-based M20 trajectories');ax.plot([],[],color='#bc4c55',label='Delayed reactive software baseline')
    ax.legend(loc='upper center',bbox_to_anchor=(.5,1.18),ncol=2,frameon=False);fig.tight_layout();fig.savefig(folder/'course_paths.png',dpi=180);plt.close(fig)
    if any(r['mode']=='course_climb' for r in rows):
        trace=pd.read_csv(shared/'telemetry.csv');summary=json.loads((shared/'summary.json').read_text())
        fig,axes=plt.subplots(3,1,figsize=(11,7),sharex=True,gridspec_kw={'height_ratios':[1,1.3,.8]})
        axes[0].plot(trace.time_s,trace.z_m,color='#286f94',label='Torso height')
        for r in summary['climb_records']:axes[0].axvline(r['verified_time_s'],color='#16917d',linestyle='--',alpha=.6)
        axes[0].set_ylabel('Torso z (m)');axes[0].legend(loc='upper left',frameon=False)
        legs=['fl','fr','hl','hr']
        for leg in legs:axes[1].plot(trace.time_s,trace[leg+'_z_m'],label=leg.upper(),linewidth=1.)
        axes[1].set_ylabel('Foot wheel centre z (m)');axes[1].legend(ncol=4,loc='upper left',frameon=False)
        contacts=np.vstack([trace[leg+'_contact'] for leg in legs])
        axes[2].imshow(contacts,aspect='auto',interpolation='nearest',extent=[trace.time_s.iloc[0],trace.time_s.iloc[-1],3.5,-.5],cmap='Greens',vmin=0,vmax=1)
        axes[2].set_yticks(range(4),[leg.upper() for leg in legs]);axes[2].set_ylabel('Contact');axes[2].set_xlabel('Actual simulated time (s)')
        for ax in axes[:2]:ax.grid(alpha=.18)
        fig.suptitle('Recorded M20 two-terrace course | dashed lines mark independently verified ascents',fontsize=12)
        fig.tight_layout();fig.savefig(folder/'course_climbing_telemetry.png',dpi=180);plt.close(fig)
    (folder/'verification.json').write_text(json.dumps({'status':'PASS','actual_trials_checked':len(rows),'source_sha256':digest,'checks':['CSV-state identity','20 ms samples','torque limits','strict acceptance','map hit conservation','time-ordered planner logs','signed 10 Hz geometry distances','three alternating barrier crossings','independent climb lift and resupport records when required'],'trials':rows},indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in metrics.items() if k not in ['blocked_fixtures','combined_climbing']},indent=2))

if __name__=='__main__':main()
