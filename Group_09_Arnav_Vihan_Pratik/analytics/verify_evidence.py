"""Fail closed if final M20 benchmark evidence is missing or internally inconsistent."""
from pathlib import Path
import sys,json,hashlib
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'M20'))
from simulation import source_digest,mission_acceptance
HERE=Path(__file__).resolve().parent

def verify(folder):
    df=pd.read_csv(folder/'results.csv');design=json.loads((folder/'design.json').read_text());digest=design['source_sha256']
    assert len(df)==2*design['pairs']
    if digest!=source_digest():
        # Historical logs are checked against their actual frozen physical source,
        # never relabelled with the current controller hash after an extension.
        snapshot=folder/'source_snapshot/M20';h=hashlib.sha256()
        for p in sorted(snapshot.glob('*.py')):h.update(p.name.encode());h.update(p.read_bytes())
        h.update((snapshot/'M20.xml').read_bytes())
        for p in sorted((ROOT/'M20/meshes').glob('*.STL')):h.update(p.read_bytes())
        assert h.hexdigest()==digest,'Frozen source is missing or changed'
    checked=[]
    for trial in df.trial_id:
        f=folder/trial;s=json.loads((f/'summary.json').read_text());a=np.load(f/'states.npz');d=pd.read_csv(f/'telemetry.csv')
        assert s['source_sha256']==digest
        assert len(d)==len(a['time'])==len(a['qpos'])==len(a['ctrl'])
        assert (a['qpos'].shape[1],a['qvel'].shape[1],a['ctrl'].shape[1])==(23,22,16)
        assert np.isfinite(a['qpos']).all() and np.isfinite(a['ctrl']).all()
        assert np.allclose(d.time_s,a['time']) and np.allclose(d.x_m,a['qpos'][:,0])
        assert np.all(np.diff(d.time_s)>0) and np.allclose(np.diff(d.time_s),.02)
        assert abs(d.time_s.iloc[-1]-s['simulated_s'])<=.021
        assert abs(a['ctrl'][:,[i for i in range(16) if i%4!=3]]).max()<=76.4+1e-9
        assert abs(a['ctrl'][:,3::4]).max()<=21.6+1e-9
        expected=mission_acceptance(s['goal_reached'],s['rollover'],s['harmful_contact_steps'],bool(s['terrain']['step_height_m']),s['climb_verified'],s['tilt_stop'])
        assert s['accepted']==expected
        assert bool(df[df.trial_id==trial].accepted.iloc[0])==s['accepted']
        if s['climb_verified']:assert s['front_pair_air'] and s['rear_pair_air'] and s['front_resupport'] and s['rear_resupport']
        g=np.load(f/'map.npz');assert (g['count']>=0).all() and int(g['count'].sum())==s['ray_hits']
        checked.append({'trial_id':trial,'rows':len(d),'status':s['status'],'accepted':s['accepted'],
            'telemetry_sha256':hashlib.sha256((f/'telemetry.csv').read_bytes()).hexdigest()})
    # Matched XML hashes must agree per seed because policy/latency do not change scene geometry.
    for _,pair in df.groupby('seed'):
        assert set(pair.policy)=={'baseline','shared'}
        paths=[folder/r/'scene.xml' for r in pair.trial_id]
        assert paths[0].read_bytes()==paths[1].read_bytes()
    return checked

def main():
    checked=verify(HERE/'benchmark')
    receipt={'status':'PASS','actual_trials_checked':len(checked),'source_sha256':json.loads((HERE/'benchmark/design.json').read_text())['source_sha256'],
       'current_source_sha256':source_digest(),'historical_source':'benchmark/source_snapshot/M20 when historical digest differs from current source',
       'checks':['Full M20 nq/nv/nu','Actual CSV-to-state identity','Monotonic 20 ms samples',
          'Motor saturation','Primary acceptance recomputation','Measured map hit conservation',
          'Climb liftoff/resupport flags','Matched scene XML identity','No missing trials'],
       'trials':checked}
    (HERE/'evidence_verification.json').write_text(json.dumps(receipt,indent=2));print('PASS:',len(checked),'actual M20 trials verified')

if __name__=='__main__':main()
