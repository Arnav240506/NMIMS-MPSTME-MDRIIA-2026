"""M20 reconnaissance executive: map, A*, delayed intent, paired leg climbing."""
from collections import deque
import math
import numpy as np
from legged_control import LEGS,HIPS,NOMINAL,SIDES,inverse_leg,forward_leg,euler,rotation,wrap,CrawlController
from hybrid_control import M20Actuation,PairClimbController,foot_positions,smooth
from m20_rosbot_mapping import plan_route,forward_clearance

class LatencyQueue:
    def __init__(self,latency_s):
        if not math.isfinite(latency_s) or latency_s<0:raise ValueError('Invalid delay')
        self.delay=latency_s;self.queue=deque();self.current=(0.,0.);self.last=-math.inf
    def send(self,t,cmd):
        if t<self.last:raise ValueError('Nonmonotonic command time')
        self.last=t;self.queue.append((t+self.delay,tuple(cmd)))
    def receive(self,t):
        while self.queue and self.queue[0][0]<=t+1e-10:_,self.current=self.queue.popleft()
        return self.current

def track(position,yaw,path,speed,lookahead=.18):
    if not len(path):return 0.,0.
    nearest=int(np.argmin(np.linalg.norm(path-position,axis=1)))
    ahead=nearest
    while ahead+1<len(path) and np.linalg.norm(path[ahead]-position)<lookahead:ahead+=1
    goal=path[ahead];err=wrap(math.atan2(goal[1]-position[1],goal[0]-position[0])-yaw)
    w=float(np.clip(2.0*err,-.65,.65));v=speed*max(0,math.cos(err))
    if abs(err)>.30:v=0.
    return v,w

def reactive_driver(position,yaw,goal,clearance,speed):
    err=wrap(math.atan2(goal[1]-position[1],goal[0]-position[0])-yaw)
    if clearance<.65:return .07,.65
    return speed*max(.1,math.cos(err)),float(np.clip(2*err,-.65,.65))

class ReconExecutive:
    def __init__(self,model,data,config,goal):
        self.m=model;self.config=config;self.goal=np.array(goal)
        self.a=M20Actuation(model,data);self.delay=LatencyQueue(config.latency_s)
        self.phase='WAKEUP';self.reason='wakeup';self.path=np.empty((0,2));self.path_status='initializing'
        self.planner_calls=0;self.last_path=self.path.copy();self.climb=None;self.climb_finished=False;self.clear_edge_target=None;self.clear_edge_until=None
        self.step_detection=None;self.last_climb=None;self.docking=False;self.tilt_stop=False;self.v=self.w=0.;self.clearance=5.
        self.stand=np.zeros(16)
        for i in range(4):self.stand[i*4:i*4+3]=inverse_leg(NOMINAL[i]-HIPS[i],SIDES[i],i<2)
        self.crouch=data.qpos[self.a.qids].copy();self.initial_xy=data.qpos[:2].copy()
        self.turn_completed=False;self.turn_start=None;self.turn_anchor=0.;self.pivot_anchor=None
        self.walker=CrawlController(model,data) if config.mode=='walk' else None

    def navigation_tick(self,data,grid):
        roll,pitch,yaw=euler(data.qpos[3:7]);position=data.qpos[:2].copy()
        self.clearance=forward_clearance(self.m,data)
        raw=reactive_driver(position,yaw,self.goal,self.clearance,self.config.speed_m_s)
        if data.time<2.4:raw=(0.,0.)
        self.delay.send(float(data.time),raw);delayed=self.delay.receive(float(data.time))
        if abs(roll)>math.radians(18) or abs(pitch)>math.radians(28):self.tilt_stop=True
        if self.config.mode=='walk':
            self.phase='DIAGONAL_PAIR_WALK';self.v=.07 if not self.tilt_stop else 0.;self.w=0.
            self.reason='walking' if not self.tilt_stop else 'tilt_stop';return
        if data.time<2.4:self.phase='WAKEUP';self.v=self.w=0.;self.reason='wakeup';return
        if self.tilt_stop:
            self.v=self.w=0.;self.reason='tilt_stop';return
        if self.climb:
            self.phase=self.climb.state;self.reason='paired_climb';return
        if self.config.policy=='baseline':
            self.phase='DELAYED_REACTIVE';self.v,self.w=delayed;self.reason='delayed_reactive';return
        if self.config.mode=='course_climb' and not (self.climb_finished and self.clear_edge_until is not None and position[0]<self.clear_edge_until):
            ground=self.last_climb['height_m'] if self.last_climb else 0.
            detected=grid.detect_step(position,ground,conservative_lip=True)
            if detected and (self.last_climb is None or detected[0]>self.last_climb['lip_m']+.5):
                self.step_detection=detected
                if self.climb_finished:
                    self.climb_finished=False;self.docking=False;self.clear_edge_target=None;self.clear_edge_until=None
        if not self.climb_finished and not self.config.mode.startswith('course'):
            detected=grid.detect_step(position)
            if detected and (self.step_detection is None or abs(detected[0]-self.step_detection[0])<.12):self.step_detection=detected
        target=self.goal.copy()
        if self.step_detection and not self.climb_finished:
            lip,height=self.step_detection;target=np.array([lip-.55,0.])
        if self.step_detection and not self.climb_finished and (self.docking or np.linalg.norm(position-target)<.16):
            self.docking=True
            self.phase='DOCK_ALIGN';self.v=0.;self.w=float(np.clip(-2.5*yaw,-.5,.5));self.reason='post_detour_alignment'
            if abs(yaw)<.025 and abs(position[1])<.25:
                self.climb=PairClimbController(self.m,data,*self.step_detection,
                    ground_height=self.last_climb['height_m'] if self.config.mode=='course_climb' and self.last_climb else 0.,
                    rear_body_clearance=.35,
                    rear_landing_offset=.24 if self.config.mode=='course_climb' else .06)
                self.phase='APPROACH';self.reason='measured_step_climb'
            return
        if self.planner_calls==0 or int(round(data.time/.02))%10==0:
            self.path,self.path_status=plan_route(grid,position,target);self.planner_calls+=1
            if len(self.path):self.last_path=self.path.copy()
        self.phase='DETOUR_NAV' if len(self.path) and np.max(abs(self.path[:,1]))>.5 else 'CRUISE_MAP'
        self.v,self.w=track(position,yaw,self.path,self.config.speed_m_s,.35 if self.config.mode.startswith('course') else .18)
        self.reason='local_route'
        if not len(self.path):self.v=self.w=0.;self.reason='no_safe_path'
        elif self.clearance<.20:self.v=0.;self.reason='obstacle_stop_replan'
        elif self.clearance<1.5:self.v*=max(.30,(self.clearance-.2)/1.3);self.reason='obstacle_slow'
        if self.climb_finished:self.phase='PLATEAU_RECON'
        if self.clear_edge_until is not None and position[0]<self.clear_edge_until:
            self.phase='CLEAR_REAR_EDGE';self.v=.15;self.w=float(np.clip(-2*yaw,-.2,.2));self.reason='post_climb_clearance'

    def physics_tick(self,data):
        if self.walker:
            return self.walker.update(data,self.v,self.w)
        if self.climb and not self.tilt_stop:
            state=self.climb.update(data);self.phase=state
            if self.climb.completed:
                self.last_climb={'lip_m':self.climb.lip,'height_m':self.climb.height,'ground_m':self.climb.ground};self.climb_finished=True;self.clear_edge_target=self.climb.a.target.copy();self.clear_edge_until=self.climb.lip+.60;self.climb=None;self.a=M20Actuation(self.m,data);self.phase='PLATEAU_RECON'
            return self.a.target,-1
        roll,pitch,yaw=euler(data.qpos[3:7]);body=data.qpos[:3].copy()
        if data.time<2.4:
            p=smooth(data.time/2.)
            self.a.target=self.crouch+p*(self.stand-self.crouch)
            z=[]
            for i in range(4):z.append(forward_leg(self.a.target[i*4:i*4+3],SIDES[i])[2])
            body[:2]=self.initial_xy;body[2]=.093-float(np.mean(z))
            self.a.set_brakes(data,['hold']*4);self.a.apply(data,body,0.)
        else:
            foot_h=foot_positions(data)[:,2]-.093
            body[2]=.523+float(np.mean(foot_h))
            self.a.target=self.clear_edge_target.copy() if self.clear_edge_until is not None and data.qpos[0]<self.clear_edge_until else self.stand.copy()
            if self.tilt_stop:self.v=self.w=0.
            effective_w=self.w+5*(self.w-data.qvel[5])
            v_eff=self.v
            if abs(self.v)<.01 and abs(self.w)>.02:
                if self.pivot_anchor is None:self.pivot_anchor=body[:2].copy()
                body[:2]=self.pivot_anchor
                heading=rotation(yaw)[:2,0]
                v_eff=float(np.clip(2*np.dot(self.pivot_anchor-data.qpos[:2],heading)-.8*np.dot(data.qvel[:2],heading),-.35,.35))
            else:self.pivot_anchor=None
            left=v_eff-effective_w*.55/2;right=v_eff+effective_w*.55/2
            modes=['roll']*4 if abs(self.v)+abs(self.w)>.002 else ['hold']*4
            self.a.set_brakes(data,modes)
            velocity=rotation(yaw)[:,0]*self.v
            self.a.apply(data,body,yaw+self.w*.25,velocity,self.w,wheel_velocities=(left,right,left,right))
        return self.a.target.copy(),-1
