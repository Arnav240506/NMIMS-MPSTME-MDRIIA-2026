"""Predeclared independent final-course experiment; genuine 500 Hz raw CSVs."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from dataclasses import asdict
from datetime import datetime,timezone
import argparse,sys,json,csv,shutil,hashlib
GROUP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(GROUP/'M20'))
from scene import TrialConfig,MODEL_DIR
from simulation import run_trial,source_digest

def worker(job):
    cfg,out=job
    run_trial(cfg,out,quiet=True)
    # The saved JSON normalizes NumPy scalar types, including acceptance bools.
    return json.loads((out/'summary.json').read_text(encoding='utf-8'))

def configurations():
    return [TrialConfig(seed=base+i,mode='course_climb',policy=policy,duration_s=180.,speed_m_s=.30,
                       roughness_m=[0.,.003,.006][i%3],initial_y_jitter_m=.02,initial_yaw_jitter_rad=.02)
            for i in range(30) for policy,base in [('baseline',31000),('shared',32000)]]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=GROUP/'analytics/capstone_500hz')
    p.add_argument('--workers',type=int,default=3);p.add_argument('--resume',action='store_true');a=p.parse_args()
    configs=configurations();digest=source_digest()
    if a.out.exists() and not a.resume:raise SystemExit('Choose a new folder or explicit --resume; completed evidence is not overwritten.')
    a.out.mkdir(parents=True,exist_ok=True)
    design={'created_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':digest,
        'N_per_policy':30,'independent_seeds':True,'primary_metric':'Final XY goal error in m; all failures retained',
        'primary_test':'Two-sided Welch t test, alpha .05; pooled-SD Cohen d and Welch 95% CI',
        'secondary_metrics':['strict mission acceptance','fixed task-path XY cross-track RMSE after 2.4 s','500 Hz integral of all 16 actuator torques squared','harmful contacts','both ascents','duration'],
        'randomization':'Independent non-overlapping policy seed sets. Floor friction U(.75,1.15); barrier offsets U(-.08,.08) m; initial y U(-.02,.02) m; yaw U(-.02,.02) rad. Ten trials per policy at each roughness bound 0/3/6 mm; nonzero tile heights U(bound/2,bound).',
        'reference':'Fixed evaluator-only A* path from actual fixture geometry, with predocking point; never fed to either controller',
        'baseline':'Delayed deterministic reactive driver with identical M20 standing/rolling servo; no map or paired climb; integration-level comparison, not human teleoperation or single-feature ablation',
        'deadline_s':180,'sample_rate_hz':500,'trials':[asdict(c) for c in configs]}
    if a.resume:
        old=json.loads((a.out/'design.json').read_text());assert old['source_sha256']==digest and old['trials']==design['trials']
    else:
        (a.out/'design.json').write_text(json.dumps(design,indent=2),encoding='utf-8')
        snap=a.out/'source_snapshot/M20';snap.mkdir(parents=True)
        for f in [*MODEL_DIR.glob('*.py'),MODEL_DIR/'M20.xml']:shutil.copy2(f,snap/f.name)
        (a.out/'source_snapshot/meshes.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (MODEL_DIR/'meshes').glob('*.STL')},indent=2))
    summaries=[];jobs=[]
    for i,cfg in enumerate(configs):
        dest=a.out/f'{i:02d}_{cfg.seed}_{cfg.policy}'
        if (dest/'summary.json').exists():
            s=json.loads((dest/'summary.json').read_text());assert s['source_sha256']==digest;summaries.append(s)
        elif dest.exists():raise SystemExit(f'Partial trial exists: {dest}; preserve it and choose a new batch folder.')
        else:jobs.append((cfg,dest))
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for f in as_completed([pool.submit(worker,j) for j in jobs]):
            s=f.result();summaries.append(s)
            print(f'{len(summaries)}/60 {s["trial_id"]}: {s["status"]}; accepted={s["accepted"]}; climbs={len(s["climb_records"])}; contacts={s["harmful_contact_steps"]}; samples={s["telemetry_samples"]}',flush=True)
    assert source_digest()==digest and all(s['source_sha256']==digest for s in summaries)
    summaries.sort(key=lambda s:s['trial_id']);rows=[]
    for s in summaries:
        row={k:v for k,v in s.items() if isinstance(v,(str,int,float,bool)) or v is None};row.update(s['config']);rows.append(row)
    with (a.out/'capstone_real_trials.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    (a.out/'summaries.json').write_text(json.dumps(summaries,indent=2),encoding='utf-8')
    print('COMPLETE: 60 independent physical trials retained, including failures.',flush=True)

if __name__=='__main__':main()
