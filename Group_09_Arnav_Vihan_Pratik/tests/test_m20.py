import math,time
import numpy as np
import mujoco,pytest
from scene import TrialConfig,build_scene,compile_xml
from legged_control import LEGS,JOINTS,HIPS,NOMINAL,SIDES,inverse_leg,forward_leg,initialize,euler
from hybrid_control import M20Actuation,foot_positions
from m20_rosbot_mapping import M20Map,raycast,normalized_cost,astar,plan_route
from recon_controller import LatencyQueue
from simulation import mission_acceptance
from hazardous_recon_economics import economics

@pytest.fixture(scope='module')
def scene():return build_scene(TrialConfig(mode='flat'))[:2]

def test_authentic_anatomy(scene):
    m,d=scene
    assert (m.nq,m.nv,m.nu,m.nmesh)==(23,22,16,17)
    assert m.body_mass.sum()==pytest.approx(34.525856,abs=.0001)
    assert all(m.body(p+'_wheel').id>0 for p in LEGS)

@pytest.mark.parametrize('i',range(4))
def test_inverse_and_forward_match_actual_mesh_chain(scene,i):
    m,d=scene;initialize(m,d)
    q=inverse_leg(NOMINAL[i]-HIPS[i],SIDES[i],i<2)
    assert np.allclose(forward_leg(q,SIDES[i]),NOMINAL[i]-HIPS[i],atol=1e-6)
    assert np.allclose(d.body(LEGS[i]+'_wheel').xpos-d.qpos[:3],NOMINAL[i],atol=2e-4)

@pytest.mark.parametrize('yaw',[-math.pi,-.7,0,.8,math.pi])
def test_quaternion_yaw(yaw):assert euler([math.cos(yaw/2),0,0,math.sin(yaw/2)])[2]==pytest.approx(yaw)

def test_torque_limits_and_velocity_sign(scene):
    m,d=scene;initialize(m,d);a=M20Actuation(m,d)
    a.target+=100;a.set_brakes(d,['roll']*4);a.apply(d,d.qpos[:3],0,wheel_velocities=[.2]*4)
    assert np.max(abs(d.ctrl[a.aids]))<=76.4
    assert np.all(d.ctrl[a.aids[3::4]]<0)
    assert np.max(abs(d.ctrl[a.aids[3::4]]))<=21.6

def test_time_is_physics_time(scene):
    m,d=scene;initialize(m,d);a=M20Actuation(m,d);before=time.perf_counter()
    for _ in range(100):a.apply(d,d.qpos[:3],0);mujoco.mj_step(m,d)
    assert d.time==pytest.approx(.2)
    assert time.perf_counter()-before>0

def test_ray_ground_and_tall_hazard_not_filtered():
    m=mujoco.MjModel.from_xml_string('<mujoco><worldbody><geom type="plane" size="10 10 .1"/><geom name="tall" type="box" pos="1 0 .5" size=".1 .2 .5"/></worldbody></mujoco>')
    d=mujoco.MjData(m);mujoco.mj_forward(m,d)
    pts,dist,ids,valid=raycast(m,d,[0,0,.5],[[1,0,0],[0,0,-1],[0,0,1]])
    assert dist[0]==pytest.approx(.9);assert dist[1]==pytest.approx(.5);assert not valid[2]
    assert len(pts)==2

def test_grid_measured_aggregation():
    g=M20Map(.1,(0,1,0,1));g.integrate([[.25,.25,.04],[.25,.25,.08]])
    r=g.cell([.25,.25]);assert g.count[r]==2;assert g.mean[r]==pytest.approx(.06);assert g.peak[r]==.08
    before=g.count.sum();g.integrate([]);g.integrate([[-5,-5,1]])
    assert g.count.sum()==before

def test_normalized_cost():
    assert normalized_cost(0,0,0)==0
    assert normalized_cost(math.pi,.5,2)==1
    assert normalized_cost(0,0,.07)==pytest.approx(.15)

def test_unknown_and_blocked_no_path():
    g=M20Map(.1,(0,2,0,2));assert not astar(g,(1,1),(18,18))
    g.count[:]=1;g.mean[:]=0;g.inflated[:,10]=True
    assert not astar(g,(1,1),(18,18))

def test_no_diagonal_corner_cut():
    g=M20Map(.1,(0,.3,0,.3));g.count[:]=1;g.inflated[:]=True
    g.inflated[0,0]=g.inflated[1,1]=False
    assert not astar(g,(0,0),(1,1))

def test_inflation_and_measured_step():
    m,d,meta=build_scene(TrialConfig(mode='mission'));g=M20Map()
    for _ in range(64):g.scan(m,d)
    lip,height=g.detect_step(d.qpos[:2]);assert abs(lip-meta['step_lip_m'])<.04
    assert height==pytest.approx(.08,abs=.005)
    assert g.inflated.sum()>g.unsafe.sum()>0
    path,status=plan_route(g,d.qpos[:2],[2.24,0]);assert len(path)>1
    assert abs(path[:,1]).max()>.6

def test_latency_fifo_schedule():
    q=LatencyQueue(.35);q.send(0,(1,2));q.send(.1,(3,4))
    assert q.receive(.349)==(0,0);assert q.receive(.35)==(1,2);assert q.receive(.45)==(3,4)
    with pytest.raises(ValueError):q.send(.05,(0,0))
    with pytest.raises(ValueError):LatencyQueue(-1)

def test_deterministic_scene_and_no_unbounded_friction():
    a=build_scene(TrialConfig(seed=18))[2];b=build_scene(TrialConfig(seed=18))[2]
    assert a['xml']==b['xml'];assert .75<=a['friction']<=1.15
    c=build_scene(TrialConfig(seed=19))[2];assert a['xml']!=c['xml']

@pytest.mark.parametrize('bad',[(False,False,0,False,False,False),(True,True,0,False,False,False),(True,False,1,False,False,False),(True,False,0,True,False,False),(True,False,0,False,False,True)])
def test_negative_acceptance(bad):assert not mission_acceptance(*bad)

def test_positive_acceptance():assert mission_acceptance(True,False,0,True,True,False)

def test_economics():
    e=economics();assert e['kappa']==.22;assert e['payback_months']==pytest.approx(12*.3/.78)
    assert e['delta_FTE']==.15;assert economics(1.)['payback_months'] is None
    with pytest.raises(ValueError):economics(reclaimed_value_parity=0)
    with pytest.raises(ValueError):economics(operating_parity=float('nan'))

@pytest.mark.parametrize('kwargs',[{'latency_s':-1},{'speed_m_s':0},{'mode':'car'}])
def test_invalid_configuration(kwargs):
    with pytest.raises(ValueError):TrialConfig(**kwargs)

def test_tilt_stop_latched_and_drive_zero():
    from recon_controller import ReconExecutive
    cfg=TrialConfig(mode='tilt');m,d,meta=build_scene(cfg);d.time=3.
    c=ReconExecutive(m,d,cfg,meta['goal']);g=M20Map();c.navigation_tick(d,g)
    assert c.tilt_stop and c.v==0 and c.w==0
    d.qpos[3:7]=[1,0,0,0];mujoco.mj_forward(m,d);c.navigation_tick(d,g)
    assert c.tilt_stop and c.v==0

def test_actual_map_to_torque_smoke(tmp_path):
    from simulation import run_trial
    s=run_trial(TrialConfig(mode='flat',duration_s=3.2),tmp_path/'smoke',quiet=True)
    a=np.load(tmp_path/'smoke/states.npz')
    assert s['simulated_s']==pytest.approx(3.2)
    assert s['ray_hits']>0 and s['planner_calls']>0
    assert a['qpos'][-1,0]>.10
    assert a['ctrl'].shape[1]==16
    assert not s['accepted']  # A short smoke run cannot reach the 3 m mission goal.

@pytest.mark.parametrize('relative',['M20/M20_hazardous_terrain.xml','models/hazardous_terrain_ugv.xml'])
def test_saved_scene_paths_compile_portably(relative):
    from scene import GROUP
    model=mujoco.MjModel.from_xml_path(str(GROUP/relative))
    assert (model.nq,model.nv,model.nu,model.nmesh)==(23,22,16,17)
