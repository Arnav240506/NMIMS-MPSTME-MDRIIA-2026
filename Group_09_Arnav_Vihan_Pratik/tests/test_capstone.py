import json,csv
import numpy as np
import pytest
from telemetry import project_path,task_reference
from scene import TrialConfig,build_scene
from simulation import run_trial

def test_path_projection_has_known_cross_track_error_and_endpoint():
    p,d2=project_path(np.array([.5,2.]),[[0,0],[1,0]])
    assert np.allclose(p,[.5,0]) and d2==4.
    p,d2=project_path(np.array([2.,0]),[[0,0],[1,0]])
    assert np.allclose(p,[1,0]) and d2==1.

def test_fixed_reference_policy_independent_and_avoids_barriers():
    paths=[]
    for policy in ['baseline','shared']:
        m,d,meta=build_scene(TrialConfig(mode='course_climb',policy=policy))
        path=task_reference(m,d,meta);paths.append(path)
        assert len(path)>5 and np.allclose(path[-1],meta['goal'])
        assert np.max(path[:,1])>1. and np.min(path[:,1])< -1.
    assert np.array_equal(*paths)

def test_500hz_actual_samples_and_effort_recomputed(tmp_path):
    summary=run_trial(TrialConfig(mode='flat',duration_s=3.2),tmp_path/'actual',quiet=True)
    schema=json.loads((tmp_path/'actual/telemetry_schema.json').read_text())
    with (tmp_path/'actual/001_real_trials.csv').open() as f:rows=list(csv.DictReader(f))
    assert len(rows)==schema['samples']==1600
    times=np.array([float(r['time_s']) for r in rows]);assert np.allclose(np.diff(times),.002,atol=1e-12)
    tau=np.array([[float(r[f'tau_{i:02d}_Nm']) for i in range(16)] for r in rows])
    assert np.sum(tau**2)*.002==pytest.approx(summary['control_effort_Nm2_s'],rel=1e-8)
    valid=[r for r in rows if r['tracking_valid']=='1']
    rmse=np.sqrt(np.mean([float(r['error_x_m'])**2+float(r['error_y_m'])**2 for r in valid]))
    assert rmse==pytest.approx(summary['tracking_rmse_m'],rel=1e-7,abs=1e-9)
    assert np.load(tmp_path/'actual/states.npz')['time'].shape==(160,)  # replay only

def test_low_roughness_is_real_seeded_collision_geometry():
    cfg=TrialConfig(mode='course_climb',roughness_m=.006,initial_y_jitter_m=.02,initial_yaw_jitter_rad=.02)
    m,d,meta=build_scene(cfg);m2,d2,meta2=build_scene(cfg)
    assert meta['xml']==meta2['xml'] and np.array_equal(d.qpos,d2.qpos)
    names=[n for n in meta['supports'] if n.startswith('course_low_rubble_')]
    assert len(names)==36 and abs(meta['initial_y_m'])<=.02 and abs(meta['initial_yaw_rad'])<=.02
    for name in names:
        assert m.geom(name).contype[0] and .003<=2*m.geom(name).size[2]<=.006
