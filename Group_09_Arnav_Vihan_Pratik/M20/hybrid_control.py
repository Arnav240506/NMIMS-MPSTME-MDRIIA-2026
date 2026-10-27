"""Torque-limited M20 wheel/leg actuation and measured paired curb executive."""
import math
import numpy as np
import mujoco
from legged_control import LEGS,JOINTS,HIPS,NOMINAL,SIDES,inverse_leg,euler,rotation,wrap

def smooth(p):
    p=float(np.clip(p,0,1));return p*p*(3-2*p)

def foot_positions(data):return np.array([data.body(p+'_wheel').xpos.copy() for p in LEGS])

def foot_contacts(model,data):
    result=np.zeros(4,dtype=bool)
    bodies={model.body(p+'_wheel').id:i for i,p in enumerate(LEGS)}
    for contact in data.contact:
        a,b=int(contact.geom1),int(contact.geom2)
        for robot,other in ((a,b),(b,a)):
            body=int(model.geom_bodyid[robot])
            if body in bodies and model.geom_bodyid[other]==0:result[bodies[body]]=True
    return result

class M20Actuation:
    def __init__(self,model,data):
        self.m=model
        self.qids=np.array([model.joint(n).qposadr[0] for n in JOINTS])
        self.dofs=np.array([model.joint(n).dofadr[0] for n in JOINTS])
        self.aids=np.array([model.actuator(n).id for n in JOINTS])
        self.target=data.qpos[self.qids].copy()
        self.brake_ref=self.target.reshape(4,4)[:,1:].sum(axis=1)
        self.wheel_modes=['hold']*4
        self.ff=np.zeros(16);self.tick=0

    def set_brakes(self,data,modes):
        q=data.qpos[self.qids].reshape(4,4)
        pitch=float(euler(data.qpos[3:7])[1])
        for i in range(4):
            if modes[i]=='hold' and self.wheel_modes[i]!='hold':self.brake_ref[i]=sum(q[i,1:])-pitch
        self.wheel_modes=list(modes)

    def cartesian_targets(self,feet,body,yaw):
        R=rotation(yaw)
        for i in range(4):self.target[i*4:i*4+3]=inverse_leg(R.T@(feet[i]-body)-HIPS[i],SIDES[i],i<2)

    def posture_targets(self,body_height,foot_heights):
        for i in range(4):
            point=NOMINAL[i].copy();point[2]=foot_heights[i]+.093-body_height
            self.target[i*4:i*4+3]=inverse_leg(point-HIPS[i],SIDES[i],i<2)

    def apply(self,data,body_ref,yaw_ref,velocity_ref=(0,0,0),yaw_rate_ref=0.,stance=(0,1,2,3),wheel_velocities=(0,0,0,0),float_swing=True):
        self.tick+=1
        if self.tick%5==1:
            mass=float(self.m.body_mass.sum());att=euler(data.qpos[3:7])
            vel=np.asarray(velocity_ref)
            wrench=np.zeros(6)
            wrench[:2]=120*(np.asarray(body_ref[:2])-data.qpos[:2])+70*(vel[:2]-data.qvel[:2])
            wrench[2]=mass*9.81+650*(body_ref[2]-data.qpos[2])-100*data.qvel[2]
            wrench[3:]=np.array([160,220,120])*np.array([-att[0],-att[1],wrap(yaw_ref-att[2])])-np.array([18,24,18])*(data.qvel[3:6]-[0,0,yaw_rate_ref])
            A=np.zeros((6,3*len(stance)))
            center=data.subtree_com[self.m.body('base_link').id]
            for j,i in enumerate(stance):
                r=data.body(LEGS[i]+'_wheel').xpos-center
                A[:3,j*3:j*3+3]=np.eye(3)
                A[3:,j*3:j*3+3]=[[0,-r[2],r[1]],[r[2],0,-r[0]],[-r[1],r[0],0]]
            forces=(A.T@np.linalg.solve(A@A.T+np.eye(6)*1e-4,wrench)).reshape(-1,3)
            self.ff[:]=0
            for f,i in zip(forces,stance):
                f[2]=np.clip(f[2],0,280);f[:2]=np.clip(f[:2],-.7*f[2],.7*f[2])
                jp=np.zeros((3,self.m.nv));jr=np.zeros_like(jp)
                mujoco.mj_jacBody(self.m,data,jp,jr,self.m.body(LEGS[i]+'_wheel').id)
                self.ff[i*4:i*4+3]=-jp[:,self.dofs[i*4:i*4+3]].T@f
        q=data.qpos[self.qids];dq=data.qvel[self.dofs]
        tau=np.tile([500,800,800,0],4)*(self.target-q)-np.tile([25,40,40,0],4)*dq+data.qfrc_bias[self.dofs]+self.ff
        pitch=float(euler(data.qpos[3:7])[1])
        for i,mode in enumerate(self.wheel_modes):
            j=i*4+3
            if mode=='float':tau[j]=0.
            elif mode=='roll':tau[j]=3*(-wheel_velocities[i]/.09-dq[j])
            else:
                target=self.brake_ref[i]-self.target[i*4+1]-self.target[i*4+2]
                tau[j]=60*(target-q[j])-5*dq[j]-35*pitch-6*data.qvel[4]
        limits=np.tile([76.4,76.4,76.4,21.6],4)
        data.ctrl[self.aids]=np.clip(tau,-limits,limits)
        return data.ctrl[self.aids].copy()

class PairClimbController:
    """Receives a measured lip/height; completes front pair, pull and rear pair.

    It does not read terrain geometry or override the floating-base state.
    """
    def __init__(self,model,data,lip,height,ground_height=0.,rear_body_clearance=.35,rear_landing_offset=.06):
        self.m=model;self.a=M20Actuation(model,data)
        self.lip=float(lip);self.height=float(height)
        self.ground=float(ground_height);self.rear_body_clearance=float(rear_body_clearance)
        self.rear_landing_offset=float(rear_landing_offset)
        self.state='APPROACH';self.t0=float(data.time);self.anchors=foot_positions(data)
        self.body_start=data.qpos[:3].copy();self.yaw=float(euler(data.qpos[3:7])[2])
        self.failure=None;self.completed=False;self.transitions=[]

    def change(self,data,state):
        self.state=state;self.t0=float(data.time);self.anchors=foot_positions(data)
        self.body_start=data.qpos[:3].copy();self.transitions.append((float(data.time),state))

    def update(self,data):
        t=float(data.time)-self.t0;feet=foot_positions(data);target_feet=self.anchors.copy()
        body=data.qpos[:3].copy();body[2]=.523+self.ground
        modes=['hold']*4;vel=np.zeros(3);wheel=[0.]*4;stance=(0,1,2,3)
        if self.state=='APPROACH':
            body[:2]=data.qpos[:2];body[2]=.523+self.ground
            self.a.posture_targets(body[2],[self.ground]*4)
            speed=0. if data.time<1 else .22 if self.lip-float(feet[:2,0].mean())>.28 else .08
            modes=['roll']*4;wheel=[speed]*4;vel[0]=speed
            if self.lip-float(feet[:2,0].mean())<=.115:self.change(data,'PACK_REAR_STANCE')
            elif t>9.:self.failure='approach_timeout'
        elif self.state=='PACK_REAR_STANCE':
            p=smooth(t/1.8)
            target_feet[2:,0]+=.16*p
            body=self.body_start.copy()
            self.a.cartesian_targets(target_feet,body,self.yaw)
            modes=['hold','hold','roll','roll']
            wheel[2:]=[.16/1.8,.16/1.8]
            if t>=1.8:self.change(data,'SHIFT_TO_REAR')
        elif self.state=='SHIFT_TO_REAR':
            p=smooth(t/2.)
            com_offset=data.subtree_com[self.m.body('base_link').id]-data.qpos[:3]
            target=self.body_start.copy();target[0]=float(self.anchors[2:,0].mean())-com_offset[0]
            target[2]=.32+self.ground
            body=(1-p)*self.body_start+p*target
            self.a.cartesian_targets(target_feet,body,self.yaw)
            if t>=2.:self.change(data,'FRONT_PAIR_STEP')
        elif self.state=='FRONT_PAIR_STEP':
            p=min(t/1.,1.);s=smooth(p)
            com_offset=data.subtree_com[self.m.body('base_link').id]-data.qpos[:3]
            body=self.body_start.copy();body[0]=float(self.anchors[2:,0].mean())-com_offset[0]+.015;body[2]=.32+self.ground
            for i in (0,1):
                end=self.anchors[i].copy();end[0]=self.lip+.06;end[2]=self.height+.093
                target_feet[i]=(1-s)*self.anchors[i]+s*end
                target_feet[i,2]+=.10*math.sin(math.pi*p)
            self.a.cartesian_targets(target_feet,body,self.yaw)
            modes=['float','float','hold','hold'];stance=(2,3)
            if t>=1. and all(foot_contacts(self.m,data)[:2]) and min(feet[:2,0])>self.lip-.005:
                self.change(data,'TORSO_RISE')
            elif t>3.:self.failure='front_pair_contact_timeout'
        elif self.state=='TORSO_RISE':
            p=smooth(t/2.)
            goal=self.body_start.copy();goal[0]=float(self.anchors[:,0].mean());goal[1]=float(self.anchors[:,1].mean());goal[2]=.523+(self.ground+self.height)/2
            body=(1-p)*self.body_start+p*goal
            self.a.cartesian_targets(target_feet,body,self.yaw)
            if t>=2.:self.change(data,'BODY_ADVANCE')
        elif self.state=='BODY_ADVANCE':
            body[:2]=data.qpos[:2];body[2]=.523+(self.ground+self.height)/2
            self.a.posture_targets(body[2],[self.height,self.height,self.ground,self.ground])
            speed=.12
            modes=['roll']*4;wheel=[speed]*4;vel[0]=speed
            if self.lip-float(feet[2:,0].mean())<=.115:self.change(data,'SHIFT_TO_FRONT')
            if t>9.:self.failure='body_advance_timeout'
        elif self.state=='SHIFT_TO_FRONT':
            p=smooth(t/2.)
            com_offset=data.subtree_com[self.m.body('base_link').id]-data.qpos[:3]
            goal=self.body_start.copy();goal[0]=float(self.anchors[:2,0].mean())-com_offset[0]-.025;goal[2]=self.rear_body_clearance+self.height
            body=(1-p)*self.body_start+p*goal
            self.a.cartesian_targets(target_feet,body,self.yaw)
            if t>=2.:self.change(data,'REAR_PAIR_STEP')
        elif self.state=='REAR_PAIR_STEP':
            transfer_time=1.
            p=min(t/transfer_time,1.);s=smooth(p)
            com_offset=data.subtree_com[self.m.body('base_link').id]-data.qpos[:3]
            body=self.body_start.copy();body[0]=float(self.anchors[:2,0].mean())-com_offset[0]-.025;body[2]=self.rear_body_clearance+self.height
            for i in (2,3):
                end=self.anchors[i].copy();end[0]=self.lip+self.rear_landing_offset;end[2]=self.height+.093
                target_feet[i]=(1-s)*self.anchors[i]+s*end
                target_feet[i,2]+=.10*math.sin(math.pi*p)
            self.a.cartesian_targets(target_feet,body,self.yaw)
            modes=['hold','hold','float','float'];stance=(0,1)
            if t>=transfer_time and all(foot_contacts(self.m,data)[2:]) and min(feet[2:,0])>self.lip-.005:
                self.change(data,'SETTLE')
            elif t>3.:self.failure='rear_pair_contact_timeout'
        elif self.state=='SETTLE':
            p=smooth(t/2.)
            goal=self.body_start.copy();goal[0]=float(self.anchors[:,0].mean());goal[1]=float(self.anchors[:,1].mean());goal[2]=.523+self.height
            body=(1-p)*self.body_start+p*goal
            self.a.cartesian_targets(target_feet,body,self.yaw)
            if t>=3.:self.completed=True
        self.a.set_brakes(data,modes)
        self.a.apply(data,body,self.yaw,vel,stance=stance,wheel_velocities=wheel)
        return self.state
