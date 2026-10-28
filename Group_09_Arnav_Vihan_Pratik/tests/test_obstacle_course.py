"""Regression checks for the expanded scene and its actual sensor failure mode."""
import numpy as np
import mujoco
import pytest
from scene import TrialConfig,build_scene
from m20_rosbot_mapping import M20Map,raycast

def test_ray_hits_nearby_floor_far_from_world_origin():
    m=mujoco.MjModel.from_xml_string('<mujoco><worldbody><geom type="plane" size="20 20 .1"/></worldbody></mujoco>')
    d=mujoco.MjData(m);mujoco.mj_forward(m,d)
    pts,dist,ids,valid=raycast(m,d,[8.5,0,.65],[[0,0,-1]],max_range=5.)
    assert valid[0] and dist[0]==pytest.approx(.65)
    assert pts[0,0]==pytest.approx(8.5)

def test_sensor_range_still_rejects_far_hits():
    m=mujoco.MjModel.from_xml_string('<mujoco><worldbody><geom type="plane" size="20 20 .1"/></worldbody></mujoco>')
    d=mujoco.MjData(m);mujoco.mj_forward(m,d)
    assert not raycast(m,d,[8.5,0,6],[[0,0,-1]],max_range=5.)[3][0]

def test_course_has_real_collision_obstacles_and_authentic_robot():
    m,d,s=build_scene(TrialConfig(mode='course'))
    assert (m.nq,m.nv,m.nu,m.nmesh)==(23,22,16,17)
    assert len(s['hazards'])==16
    assert s['step_height_m']==0
    for name in s['hazards']:
        assert m.geom(name).contype[0] and m.geom(name).group[0]==0
    assert s['goal']==[8.6,0.]
    assert s['map_resolution_m']==.05

def test_course_seed_geometry_deterministic_and_policy_matched():
    a=build_scene(TrialConfig(mode='course',seed=2026))[2]
    b=build_scene(TrialConfig(mode='course',seed=2026,policy='baseline'))[2]
    c=build_scene(TrialConfig(mode='course',seed=2027))[2]
    assert a['xml']==b['xml'] and a['xml']!=c['xml']

def test_closed_gate_is_physical_and_seals_yard():
    m,d,s=build_scene(TrialConfig(mode='course_blocked'))
    gate=m.geom('course_closed_gate')
    assert gate.contype[0] and gate.size[1]>=3.12
    assert len(s['hazards'])==17

def test_course_scans_goal_when_robot_advances():
    m,d,s=build_scene(TrialConfig(mode='course'))
    # Sensor-only fixture: position a stationary test robot near the exit.
    d.qpos[:3]=[7.5,1.2,.53];mujoco.mj_forward(m,d)
    g=M20Map(s['map_resolution_m'],s['map_bounds'])
    for _ in range(32):g.scan(m,d)
    assert g.known[g.cell(s['goal'])]
    assert not g.inflated[g.cell(s['goal'])]

def test_combined_course_requires_two_real_terrace_ascents():
    m,d,s=build_scene(TrialConfig(mode='course_climb'))
    assert s['step_targets']==[{'lip_m':9.3,'height_m':.08},{'lip_m':12.1,'height_m':.16}]
    assert len(s['hazards'])==20 and s['goal']==[13.5,0.]
    assert all(name in s['supports'] for name in ['climb_terrace_0','climb_terrace_1'])
    assert m.geom('climb_terrace_0').size[2]==pytest.approx(.04)
    assert m.geom('climb_terrace_1').size[2]==pytest.approx(.08)

def test_second_terrace_detected_relative_to_current_support_height():
    g=M20Map(.05,(0,5,-1,1))
    xx,yy=np.meshgrid(g.xs,g.ys)
    points=np.column_stack([xx.ravel(),yy.ravel(),np.where(xx>3,.16,.08).ravel()])
    g.integrate(points);g.update_cost()
    lip,height=g.detect_step([2,0],ground_height=.08)
    assert lip==pytest.approx(3,abs=.06) and height==pytest.approx(.16)

@pytest.mark.parametrize('x,z,ground,expected_lip,expected_height',[(8.4,.525,0.,9.3,.08),(11.4,.605,.08,12.1,.16)])
def test_measured_edge_error_below_fifteen_mm_in_sensor_fixtures(x,z,ground,expected_lip,expected_height):
    m,d,s=build_scene(TrialConfig(mode='course_climb'))
    # Stationary sensor fixtures at known support levels, not locomotion evidence.
    d.qpos[:3]=[x,.1,z];mujoco.mj_forward(m,d)
    g=M20Map(s['map_resolution_m'],s['map_bounds'])
    for _ in range(32):g.scan(m,d)
    lip,height=g.detect_step(d.qpos[:2],ground,conservative_lip=True)
    # Finite beam sampling need not hit the mathematical edge exactly. Reject
    # the old full-cell (50 mm) bias while allowing <15 mm sampling error.
    assert lip==pytest.approx(expected_lip,abs=.015)
    assert height==pytest.approx(expected_height,abs=.005)
