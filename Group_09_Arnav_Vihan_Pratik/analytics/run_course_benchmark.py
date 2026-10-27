"""Execute a separate, matched dense-course extension without replacing the study."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import sys,argparse,json,csv
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'M20'))
from scene import TrialConfig
from simulation import run_trial,source_digest

def worker(job):
    config,out=job
    run_trial(config,out,quiet=True)
    return json.loads((out/'summary.json').read_text(encoding='utf-8'))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path)
    p.add_argument('--combined',action='store_true',help='Two consecutive physical terrace climbs after three barrier detours; descriptive shared-controller seed checks plus one baseline')
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--pairs',type=int,default=12)
    a=p.parse_args()
    a.out=a.out or Path(__file__).resolve().parent/('climbing_course' if a.combined else 'obstacle_course')
    if a.out.exists():raise SystemExit('Choose a NEW --out folder; existing experimental evidence is never overwritten.')
    if not 1<=a.pairs<=50:raise SystemExit('--pairs must be between 1 and 50')
    a.out.mkdir(parents=True)
    seeds=[42]+list(range(2026,2026+a.pairs-1))
    configs=[TrialConfig(seed=seed,mode='course',policy=policy,latency_s=[.05,.35,.8,1.2][i%4],duration_s=100.,speed_m_s=.30)
        for i,seed in enumerate(seeds) for policy in ('baseline','shared')]
    configs += [TrialConfig(seed=seed,mode='course_blocked',duration_s=40.,speed_m_s=.30) for seed in [42,2026]]
    if a.combined:
        configs=[TrialConfig(seed=seed,mode='course_climb',duration_s=180.,speed_m_s=.30) for seed in seeds]
        configs.append(TrialConfig(seed=42,mode='course_climb',policy='baseline',duration_s=180.,speed_m_s=.30))
    jobs=[(c,a.out/f'{i:02d}_{c.mode}_{c.seed}_{c.policy}') for i,c in enumerate(configs)]
    digest=source_digest()
    (a.out/'design.json').write_text(json.dumps({'source_sha256':digest,'pairs':0 if a.combined else a.pairs,'seeds':seeds,
        'scope':'Descriptive multi-seed combined detour and two-climb extension; single illustrative baseline; no inferential paired comparison' if a.combined else 'Separate dense obstacle-course extension, not pooled with the original 50-pair study',
        'baseline':'Delayed deterministic reactive driver; not a human operator',
        'shared':'Measured ideal-ray grid; unknown blocked; A* replanning; M20 physical joint actuation',
        'blocked_fixtures':0 if a.combined else 2,'trials':[c.__dict__ for c in configs]},indent=2),encoding='utf-8')
    summaries=[]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for f in as_completed([pool.submit(worker,j) for j in jobs]):
            s=f.result();summaries.append(s)
            print(f'{len(summaries)}/{len(jobs)} {s["trial_id"]}: {s["status"]}; accepted={s["accepted"]}; contacts={s["harmful_contact_steps"]}',flush=True)
    if source_digest()!=digest or any(s['source_sha256']!=digest for s in summaries):raise RuntimeError('Physical source changed during experiment')
    summaries.sort(key=lambda s:s['trial_id'])
    (a.out/'summaries.json').write_text(json.dumps(summaries,indent=2),encoding='utf-8')
    rows=[]
    for s in summaries:
        row={k:v for k,v in s.items() if isinstance(v,(str,int,float,bool)) or v is None};row.update(s['config']);rows.append(row)
    with (a.out/'results.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    print('COMPLETE: all actual course trials collected; inspect acceptance rather than batch exit status.')

if __name__=='__main__':main()
