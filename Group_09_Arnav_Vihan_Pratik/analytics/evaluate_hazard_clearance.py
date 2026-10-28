"""Post-hoc 10 Hz geometry clearance audit of captured physical states."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import sys,json,csv
import numpy as np,mujoco
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'M20'))
from scene import compile_xml
HERE=Path(__file__).resolve().parent

def evaluate(folder):
    folder=Path(folder);s=json.loads((folder/'summary.json').read_text());a=np.load(folder/'states.npz')
    m=compile_xml((folder/'scene.xml').read_text());d=mujoco.MjData(m)
    robot=np.flatnonzero((m.geom_bodyid>0)&(m.geom_group==1))
    hazards=[m.geom(n).id for n in s['terrain']['hazards']]
    closest=10.;when=None
    for i in range(0,len(a['time']),5):
        d.qpos[:]=a['qpos'][i];mujoco.mj_forward(m,d)
        for r in robot:
            for h in hazards:
                distance=float(mujoco.mj_geomDistance(m,d,int(r),h,10.,None))
                if distance<closest:closest=distance;when=float(a['time'][i])
    return {'trial_id':s['trial_id'],'sampled_min_hazard_clearance_m':closest,'sample_time_s':when,
        'sampling_hz':10,'hazards':'barrier/tank only; expected step/rubble supports excluded'}

if __name__=='__main__':
    folders=sorted(p.parent for p in (HERE/'benchmark').glob('*/summary.json'))
    with ProcessPoolExecutor(max_workers=4) as pool:rows=list(pool.map(evaluate,folders))
    with (HERE/'benchmark/geometry_clearance.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    (HERE/'benchmark/geometry_clearance_receipt.json').write_text(json.dumps({'trials':len(rows),'method':'Native mj_geomDistance at recorded 10 Hz poses; sample minimum, not continuous-time swept clearance','support_geometries_excluded':True},indent=2))
    print('Actual geometry clearance evaluated for',len(rows),'trials')
