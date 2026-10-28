"""Reproducible M20 physics runner. Terrain truth is used only by acceptance."""
from pathlib import Path
from dataclasses import asdict
from datetime import datetime,timezone
from collections import Counter
import argparse,csv,hashlib,json,platform,time
import numpy as np
import mujoco
from scene import TrialConfig,build_scene,ROOT,GROUP,MODEL_DIR,VERSION
from telemetry import TrialLogger
from recon_controller import ReconExecutive
from m20_rosbot_mapping import M20Map
from hybrid_control import foot_positions,foot_contacts
from legged_control import LEGS,JOINTS,euler

def utc():return datetime.now(timezone.utc).isoformat()

def source_digest():
    h=hashlib.sha256()
    for p in sorted(MODEL_DIR.glob('*.py')):
        h.update(p.name.encode());h.update(p.read_bytes())
    h.update((MODEL_DIR/'M20.xml').read_bytes())
    for p in sorted((MODEL_DIR/'meshes').glob('*.STL')):h.update(p.read_bytes())
    return h.hexdigest()

def contact_audit(model,data,supports):
    harmful=[];expected=0;forces=np.zeros(4);self_contact=0
    feet={model.body(p+'_wheel').id:i for i,p in enumerate(LEGS)}
    for k,c in enumerate(data.contact):
        a,b=int(c.geom1),int(c.geom2);ba,bb=int(model.geom_bodyid[a]),int(model.geom_bodyid[b])
        if ba and bb:self_contact+=1;continue
        if not (ba or bb):continue
        robot,world=(a,b) if ba else (b,a)
        body=int(model.geom_bodyid[robot]);name=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,world)
        f=np.zeros(6);mujoco.mj_contactForce(model,data,k,f)
        if body in feet and name in supports:
            expected+=1;forces[feet[body]]+=max(0,float(f[0]))
        else:harmful.append((mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_BODY,body),name))
    return harmful,expected,forces,self_contact

def mission_acceptance(goal_reached,rollover,harmful_contacts,requires_climb,climb_verified,tilt_stop):
    return bool(goal_reached and not rollover and harmful_contacts==0 and not tilt_stop and (not requires_climb or climb_verified))

def run_trial(config,outdir,quiet=False,live=False,realtime=True,hold_viewer=True):
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    started=utc();wall=time.perf_counter();m,d,meta=build_scene(config)
    (out/'scene.xml').write_text(meta.pop('xml'),encoding='utf-8')
    g=M20Map(meta.get('map_resolution_m',.03),meta.get('map_bounds',(-1.2,6.,-3.,3.)));executive=ReconExecutive(m,d,config,meta['goal'])
    qids=executive.a.qids;dofs=executive.a.dofs
    logger=TrialLogger(out,m,d,meta,config)
    viewer=None
    if live:
        import mujoco.viewer as mj_viewer
        viewer=mj_viewer.launch_passive(m,d,show_left_ui=False,show_right_ui=False)
        viewer.cam.distance=3.2;viewer.cam.azimuth=45;viewer.cam.elevation=-24
        viewer.opt.geomgroup[1]=0;viewer.opt.geomgroup[3]=1
    playback_start=time.perf_counter()
    rows=[];qpos=[];qvel=[];ctrl=[];targets=[];events=[];contacts=Counter();plans=[]
    tmax=int(np.ceil(config.duration_s/config.timestep));lastphase='';lastreason=''
    harm_steps=expected_contacts=self_contacts=0;rollover=False;goal_reached=False;climb_verified=False
    standing=[];base_height=None;stable_goal=0;closest=float('inf');interventions=0
    climb_started=False;front_air=rear_air=False;front_resupport=rear_resupport=False
    active_climb=None;climb_records=[];climb_attempts=[]
    last_xy=d.qpos[:2].copy();path_length=energy=0.;max_roll=max_pitch=0.;outcome='timeout'
    for tick in range(tmax):
        if viewer and tick and not viewer.is_running():outcome='user_closed';break
        if tick%10==0:
            g.scan(m,d);executive.navigation_tick(d,g)
            if config.mode.startswith('course') and executive.planner_calls>len(plans):
                plans.append({'time_s':float(d.time),'status':executive.path_status,
                    'position_m':d.qpos[:2].tolist(),'path_m':executive.path.tolist()})
            if executive.reason!=lastreason:
                if executive.reason in ('tilt_stop','no_safe_path','obstacle_stop_replan','post_detour_alignment','measured_step_climb'):interventions+=1
                events.append({'time_s':float(d.time),'kind':'decision','reason':executive.reason})
                lastreason=executive.reason
        if executive.climb and (active_climb is None or active_climb['lip_m']!=executive.climb.lip):
            active_climb={'lip_m':executive.climb.lip,'height_m':executive.climb.height,'ground_m':executive.climb.ground}
            climb_attempts.append({**active_climb,'started_time_s':float(d.time),
                'rear_body_clearance_m':executive.climb.rear_body_clearance,'rear_landing_offset_m':executive.climb.rear_landing_offset})
            front_air=rear_air=front_resupport=rear_resupport=False
        target,_=executive.physics_tick(d)
        if executive.climb:target=executive.climb.a.target.copy()
        mujoco.mj_step(m,d)
        harm,expected,forces,selfc=contact_audit(m,d,meta['supports'])
        harm_steps+=bool(harm);expected_contacts+=expected;self_contacts+=selfc
        contacts.update(f'{a}/{b}' for a,b in harm)
        energy+=float(np.sum(np.abs(d.actuator_force*d.actuator_velocity)))*config.timestep
        roll,pitch,yaw=euler(d.qpos[3:7]);max_roll=max(max_roll,abs(roll));max_pitch=max(max_pitch,abs(pitch))
        rollover|=max(abs(roll),abs(pitch))>np.deg2rad(60) or d.qpos[2]<.16
        feet=foot_positions(d);supported=foot_contacts(m,d)
        logger.sample(d,executive,harm,supported.sum())
        if viewer and tick%10==0:
            viewer.cam.lookat[:]=d.qpos[:3]+[0,0,-.10]
            viewer.set_texts((mujoco.mjtFontScale.mjFONTSCALE_150,mujoco.mjtGridPos.mjGRID_TOPLEFT,
                'LIVE PHYSICS\nMode / policy\nSimulated time\nFSM state\nDecision\nHarmful steps\nVerified climbs\nSaved telemetry',
                f'M20 Group 09\n{config.mode} / {config.policy}\n{d.time:.3f} s\n{executive.phase}\n{executive.reason}\n{harm_steps}\n{len(climb_records)}\n500 Hz actual samples'))
            viewer.sync()
            if realtime:
                wait=d.time-(time.perf_counter()-playback_start)
                if wait>0:time.sleep(min(wait,.02))
        if 2.0<=d.time<=2.4:standing.append(float(d.qpos[2]))
        if base_height is None and d.time>=2.4:base_height=float(np.median(standing)) if standing else .523
        if executive.phase=='FRONT_PAIR_STEP':
            climb_started=True;front_air|=bool(not supported[:2].any() and min(feet[:2,2])>(active_climb['ground_m'] if active_climb else 0)+.13)
        if executive.phase=='TORSO_RISE':front_resupport|=bool(supported[:2].all())
        if executive.phase=='REAR_PAIR_STEP':rear_air|=bool(not supported[2:].any() and min(feet[2:,2])>(active_climb['ground_m'] if active_climb else 0)+.13)
        if executive.phase=='SETTLE':rear_resupport|=bool(supported[2:].all())
        if executive.climb_finished and meta['step_height_m'] and base_height is not None:
            on_step=bool(supported.all() and min(feet[:,0])>(active_climb['lip_m'] if active_climb else meta['step_lip_m'])+.005 and
                np.max(abs(feet[:,2]-((active_climb['height_m'] if active_climb else meta['step_height_m'])+.093)))<.025 and
                d.qpos[2]-base_height>(active_climb['height_m'] if active_climb else meta['step_height_m'])-.025)
            if on_step and front_air and rear_air and front_resupport and rear_resupport and active_climb and not any(r['lip_m']==active_climb['lip_m'] for r in climb_records):
                climb_records.append({**active_climb,'verified_time_s':float(d.time),'front_pair_air':front_air,'rear_pair_air':rear_air,'front_resupport':front_resupport,'rear_resupport':rear_resupport})
            climb_verified=bool(len(climb_records)>=len(meta.get('step_targets',[{}])))
        distance=float(np.linalg.norm(d.qpos[:2]-meta['goal']))
        at_goal=distance<=.22 and (meta['step_height_m']==0 or climb_verified)
        stable_goal=stable_goal+1 if at_goal else 0
        if stable_goal>=int(.4/config.timestep):goal_reached=True
        path_length+=float(np.linalg.norm(d.qpos[:2]-last_xy));last_xy=d.qpos[:2].copy()
        if tick%10==0:
            phase=executive.phase
            if phase!=lastphase:
                events.append({'time_s':float(d.time),'kind':'phase','phase':phase,'xyz_m':d.qpos[:3].tolist()})
                if not quiet:print(f'{d.time:6.2f}s {phase:20} xyz={np.round(d.qpos[:3],3)}',flush=True)
                lastphase=phase
            closest=min(closest,executive.clearance)
            speed=float(np.linalg.norm(d.qvel[:2]));wheel_speed=abs(d.qvel[dofs[3::4]])*.093
            # Global hub angular velocity includes knee/hip motion during stepping.
            hub_speeds=np.array([abs(d.qvel[dofs[i*4+1:i*4+4]].sum())*.093 for i in range(4)])
            longitudinal=float(np.dot(d.qvel[:3],d.body('base_link').xmat.reshape(3,3)[:,0]))
            slip=float(np.mean(np.abs(hub_speeds-abs(longitudinal))/np.maximum(.10,np.maximum(hub_speeds,abs(longitudinal)))))
            row={'time_s':float(d.time),'x_m':d.qpos[0],'y_m':d.qpos[1],'z_m':d.qpos[2],
                 'roll_deg':np.rad2deg(roll),'pitch_deg':np.rad2deg(pitch),'yaw_deg':np.rad2deg(yaw),
                 'vx_m_s':d.qvel[0],'vy_m_s':d.qvel[1],'speed_m_s':speed,'command_v_m_s':executive.v,'command_w_rad_s':executive.w,
                 'clearance_m':executive.clearance,'map_coverage':float(g.known.mean()),'slip_proxy':slip,
                 'max_torque_Nm':float(abs(d.ctrl).max()),'phase':phase,'reason':executive.reason,
                 'harmful_contact_steps':harm_steps,'support_count':int(supported.sum()),'climb_verified':int(climb_verified)}
            for i,leg in enumerate(LEGS):
                for axis,j in zip('xyz',range(3)):row[f'{leg}_{axis}_m']=feet[i,j]
                row[f'{leg}_contact']=int(supported[i]);row[f'{leg}_normal_N']=forces[i]
            rows.append(row);qpos.append(d.qpos.copy());qvel.append(d.qvel.copy());ctrl.append(d.ctrl.copy());targets.append(target.copy())
        if rollover:outcome='rollover';break
        if goal_reached:outcome='goal';break
        if executive.climb and executive.climb.failure:outcome=executive.climb.failure;break
        # Genuine latched stop remains logged for one second, then ends unsuccessfully.
        if executive.tilt_stop and d.time>3.4:outcome='tilt_stop';break
    walking_verified=bool(config.mode=='walk' and d.qpos[0]>.5 and not rollover and harm_steps==0 and all(max(r[f'{leg}_z_m'] for r in rows)>.14 for leg in LEGS))
    accepted=mission_acceptance(goal_reached,rollover,harm_steps,bool(meta['step_height_m']),climb_verified,executive.tilt_stop)
    if config.mode=='walk':
        accepted=walking_verified;outcome='walking_verified' if accepted else 'walking_failed'
    if goal_reached and not accepted:outcome='goal_with_safety_violation'
    logged=logger.close()
    summary={'trial_id':out.name,'config':asdict(config),'model_version':VERSION,'source_sha256':source_digest(),
        'started_utc':started,'finished_utc':utc(),'wall_s':time.perf_counter()-wall,'simulated_s':float(d.time),
        'python':platform.python_version(),'mujoco':mujoco.__version__,'numpy':np.__version__,
        'mass_kg':float(m.body_mass.sum()),'nq':m.nq,'nv':m.nv,'nu':m.nu,
        'terrain':meta,'accepted':accepted,'status':outcome,'goal_reached':goal_reached,'goal_error_m':distance,
        'walking_verified':walking_verified,'climb_records':climb_records,'climb_attempts':climb_attempts,'climb_started':climb_started,'climb_verified':climb_verified,'front_pair_air':front_air,'rear_pair_air':rear_air,
        'front_resupport':front_resupport,'rear_resupport':rear_resupport,'standing_reference_z_m':base_height,
        'final_base_z_m':float(d.qpos[2]),'path_length_m':path_length,'harmful_contact_steps':harm_steps,
        'harmful_contacts':dict(contacts),'expected_support_contacts':expected_contacts,'self_contact_instances':self_contacts,
        'rollover':rollover,'tilt_stop':executive.tilt_stop,'max_abs_roll_deg':np.rad2deg(max_roll),
        'max_abs_pitch_deg':np.rad2deg(max_pitch),'closest_forward_clearance_m':closest,
        'interventions':interventions,'mean_slip_proxy':float(np.mean([r['slip_proxy'] for r in rows])),
        'max_slip_proxy':float(max(r['slip_proxy'] for r in rows)),'map_coverage':float(g.known.mean()),
        'ray_hits':g.total_hits,'planner_calls':executive.planner_calls,'absolute_mechanical_work_J':energy,
        'final_foot_centers_m':feet.tolist(),'final_supports':supported.tolist(),
        'sensing':'ideal ray intersections with true MuJoCo pose; interleaved 50 Hz; cost 10 Hz; plan 5 Hz',
        'telemetry_rate_hz':logged['rate_hz'],'telemetry_samples':logged['samples'],
        'tracking_rmse_m':logged['tracking_rmse_m'],'tracking_samples':logged['tracking_samples'],
        'control_effort_Nm2_s':logged['control_effort_Nm2_s'],
        'reference_definition':logged['reference'],'render_snapshot_rate_hz':50,
        'slip_definition':'kinematic hub-speed discrepancy, not a calibrated contact slip estimator'}
    with (out/'telemetry.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    np.savez_compressed(out/'states.npz',qpos=qpos,qvel=qvel,ctrl=ctrl,targets=targets,time=[r['time_s'] for r in rows])
    g.save(out/'map.npz',executive.last_path)
    (out/'events.json').write_text(json.dumps(events,indent=2),encoding='utf-8')
    if config.mode.startswith('course'):(out/'plans.json').write_text(json.dumps(plans),encoding='utf-8')
    (out/'summary.json').write_text(json.dumps(summary,indent=2,default=lambda o:o.item()),encoding='utf-8')
    if not quiet:print(json.dumps({k:summary[k] for k in ('accepted','status','simulated_s','climb_verified','harmful_contact_steps','goal_error_m')},indent=2))
    if viewer:
        viewer.set_texts((mujoco.mjtFontScale.mjFONTSCALE_150,mujoco.mjtGridPos.mjGRID_TOPLEFT,
            'M20 LIVE RUN ENDED\nMeasured status\nAccepted\nFSM state\nHarmful steps\nVerified climbs\nGoal error\nClose window to exit',
            f'{config.mode}\n{outcome}\n{accepted}\n{executive.phase}\n{harm_steps}\n{len(climb_records)}\n{distance:.3f} m\nLogs saved'))
        while hold_viewer and viewer.is_running():viewer.sync();time.sleep(.03)
        viewer.close()
    return summary

def main(default_mode='mission'):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',default=default_mode);p.add_argument('--policy',default='shared',choices=['shared','baseline'])
    p.add_argument('--seed',type=int,default=42);p.add_argument('--latency',type=float,default=.35)
    p.add_argument('--duration',type=float);p.add_argument('--speed',type=float,default=.30)
    p.add_argument('--out',type=Path,default=GROUP/'analytics/local_runs/latest')
    p.add_argument('--headless',action='store_true');p.add_argument('--viewer',action='store_true');p.add_argument('--record',action='store_true')
    p.add_argument('--live',action='store_true');p.add_argument('--fast',action='store_true');p.add_argument('--no-hold',action='store_true')
    a=p.parse_args()
    if a.duration is None:a.duration=12. if a.mode=='walk' else 180. if a.mode=='course_climb' else 150. if a.mode.startswith('course') else 75.
    config=TrialConfig(a.seed,a.mode,a.policy,a.latency,a.duration,a.speed)
    result=run_trial(config,a.out,live=a.live,realtime=not a.fast,hold_viewer=not a.no_hold)
    if a.record or a.viewer:
        from replay import replay
        replay(a.out,record=a.record,show=a.viewer)
    return 0 if result['accepted'] else 2

if __name__=='__main__':raise SystemExit(main())
