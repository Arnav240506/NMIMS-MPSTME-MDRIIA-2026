"""Fifty matched environments / 100 actual full-M20 simulations; no generated outcomes."""
from pathlib import Path
import sys,json,argparse,csv
from concurrent.futures import ProcessPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'M20'))
from simulation import run_trial,source_digest
from scene import TrialConfig
HERE=Path(__file__).resolve().parent

def design(smoke=False):
    modes=['flat']*10+['climb']*15+['avoid']*15+['mission']*8+['blocked']*2
    if smoke:modes=['flat','climb','mission']
    durations={'flat':20.,'climb':45.,'avoid':55.,'mission':80.,'blocked':22.}
    return [TrialConfig(seed=1000+i,mode=mode,policy=policy,latency_s=[.05,.35,.8,1.2][i%4],
                        duration_s=durations[mode],speed_m_s=.30)
            for i,mode in enumerate(modes) for policy in ('baseline','shared')]

def worker(item):
    config,out=item;run_trial(config,out,quiet=True)
    return json.loads((out/'summary.json').read_text(encoding='utf-8'))

def main():
    p=argparse.ArgumentParser();p.add_argument('--smoke',action='store_true');p.add_argument('--workers',type=int,default=4)
    p.add_argument('--out',type=Path);p.add_argument('--collect-only',action='store_true',help='Validate and aggregate already executed per-trial JSON; never invent or rerun outcomes')
    a=p.parse_args();out=a.out or HERE/('smoke' if a.smoke else 'benchmark')
    out.mkdir(parents=True,exist_ok=True);configs=design(a.smoke);digest=source_digest()
    (out/'design.json').write_text(json.dumps({'source_sha256':digest,'pairs':len(configs)//2,
        'baseline':'Delayed deterministic goal-seeking reactive driver, same M20 standing torque servo; no human operator',
        'shared':'Local true-pose ray-grid A* and paired leg climb; goal supervision; delay only in remote intent channel',
        'trials':[c.__dict__ for c in configs]},indent=2))
    jobs=[(c,out/f'{i//2:02d}_{c.mode}_{c.seed}_{c.policy}') for i,c in enumerate(configs)]
    summaries=[]
    if a.collect_only:
        summaries=[json.loads((j[1]/'summary.json').read_text(encoding='utf-8')) for j in jobs]
        if any(s['config']!=c.__dict__ for s,(c,_) in zip(summaries,jobs)):raise RuntimeError('Trial config mismatch')
    else:
        with ProcessPoolExecutor(max_workers=a.workers) as pool:
            pending={pool.submit(worker,j):j for j in jobs}
            for future in as_completed(pending):
                s=future.result();summaries.append(s)
                print(f'{len(summaries)}/{len(jobs)} {s["trial_id"]}: {s["status"]}; accepted={s["accepted"]}; contacts={s["harmful_contact_steps"]}',flush=True)
    if any(s['source_sha256']!=digest for s in summaries):raise RuntimeError('Source changed during benchmark')
    summaries.sort(key=lambda s:s['trial_id']);(out/'summaries.json').write_text(json.dumps(summaries,indent=2))
    rows=[]
    for s in summaries:
        row={k:v for k,v in s.items() if isinstance(v,(str,int,float,bool)) or v is None}
        row.update(s['config']);rows.append(row)
    with (out/'results.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    print('COMPLETE: actual physics trials',len(rows),'matched pairs',len(rows)//2)

if __name__=='__main__':main()
