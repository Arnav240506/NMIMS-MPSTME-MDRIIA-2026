"""M20 Cartesian diagonal-pair gait; physical joint torques and contact only."""
import math
import numpy as np
import mujoco

LEGS=('fl','fr','hl','hr')
JOINTS=tuple(f'{leg}_{part}_joint' for leg in LEGS for part in ('hipx','hipy','knee','wheel'))
HIPS=np.array([[.3141,.0685,0],[.3141,-.0685,0],[-.3141,.0685,0],[-.3141,-.0685,0]])
NOMINAL=np.array([[.3141,.2735,-.43],[.3141,-.2735,-.43],[-.3141,.2735,-.43],[-.3141,-.2735,-.43]])
SIDES=np.array([1,-1,1,-1])

def wrap(a):return math.atan2(math.sin(a),math.cos(a))

def euler(q):
    w,x,y,z=q
    return np.array([math.atan2(2*(w*x+y*z),1-2*(x*x+y*y)),
        math.asin(float(np.clip(2*(w*y-z*x),-1,1))),math.atan2(2*(w*z+x*y),1-2*(y*y+z*z))])

def rotation(yaw):
    c,s=math.cos(yaw),math.sin(yaw)
    return np.array([[c,-s,0],[s,c,0],[0,0,1.]])

def forward_leg(q,side):
    a,h,k=q
    x=.25*math.sin(h)+.25*math.sin(h+k)
    z=-.25*math.cos(h)-.25*math.cos(h+k)
    y=side*.158076
    c,s=math.cos(a),math.sin(a)
    return np.array([x,c*y+s*z,-s*y+c*z])

def inverse_leg(target,side,front=True):
    x,y,z=map(float,target);offset=side*.158076
    zleg=-math.sqrt(max(y*y+z*z-offset*offset,.02**2))
    roll=wrap(math.atan2(zleg,offset)-math.atan2(z,y))
    cosine=np.clip((x*x+zleg*zleg-.25**2-.25**2)/(2*.25**2),-.999,.999)
    knee=math.acos(float(cosine))*(1 if front else -1)
    hip=math.atan2(x,-zleg)-math.atan2(.25*math.sin(knee),.25+.25*math.cos(knee))
    return np.array([roll,hip,knee])

def initialize(model,data,crouch=False):
    data.qpos[:]=0;data.qvel[:]=0;data.qpos[:7]=[0,0,.523,1,0,0,0]
    for i,leg in enumerate(LEGS):
        values=inverse_leg(NOMINAL[i]-HIPS[i],SIDES[i],i<2)
        for part,q in zip(('hipx','hipy','knee'),values):data.qpos[model.joint(f'{leg}_{part}_joint').qposadr[0]]=q
        if crouch:
            data.qpos[model.joint(f'{leg}_hipy_joint').qposadr[0]]=-1.1 if i<2 else 1.1
            data.qpos[model.joint(f'{leg}_knee_joint').qposadr[0]]=1.7 if i<2 else -1.7
    mujoco.mj_forward(model,data)
    # Grounding occurs once as an initial-condition placement, never during a trial.
    low=min(data.body(f'{leg}_wheel').xpos[2]-.093 for leg in LEGS)
    data.qpos[2]-=low;mujoco.mj_forward(model,data)

class CrawlController:
    def __init__(self,model,data,step_time=.8,clearance=.09):
        self.model=model;self.dt=float(model.opt.timestep)
        self.qids=np.array([model.joint(n).qposadr[0] for n in JOINTS])
        self.dofs=np.array([model.joint(n).dofadr[0] for n in JOINTS])
        self.aids=np.array([model.actuator(n).id for n in JOINTS])
        self.target=data.qpos[self.qids].copy()
        self.hub_reference=self.target.reshape(4,4)[:,1:3].sum(axis=1)
        self.feet=np.array([data.body(p+'_wheel').xpos.copy() for p in LEGS])
        self.body_plan=data.qpos[:3].copy();self.yaw_plan=float(euler(data.qpos[3:7])[2])
        self.step_time=step_time;self.clearance=clearance;self.phase=0.;self.step_index=0
        self.swing_start=self.feet[0].copy();self.swing_end=self.feet[0].copy()
        self.started=False;self.swing_leg=-1;self.swing_prepared=False
        self.swing_legs=()
        self.swing_starts=self.feet.copy();self.swing_ends=self.feet.copy()
        self.v_filtered=0.;self.w_filtered=0.
        self.tick=0;self.force_tau=np.zeros(16)

    def servo(self,data):
        kp=np.tile([450,650,650,60],4);kd=np.tile([22,35,35,5],4)
        tau=kp*(self.target-data.qpos[self.qids])-kd*data.qvel[self.dofs]+data.qfrc_bias[self.dofs]+self.force_tau
        limits=np.tile([76.4,76.4,76.4,21.6],4)
        data.ctrl[self.aids]=np.clip(tau,-limits,limits)

    def update(self,data,v,w,height_at=None):
        self.tick+=1
        if self.tick%5!=1:
            self.servo(data)
            return self.target.copy(),self.swing_leg
        dt=self.dt*5
        if data.time<1.:v=w=0.
        self.v_filtered+=float(np.clip(v-self.v_filtered,-.12*dt,.12*dt))
        self.w_filtered+=float(np.clip(w-self.w_filtered,-.5*dt,.5*dt))
        active=(abs(self.v_filtered)>.003 or abs(self.w_filtered)>.01)
        if data.time<1.:active=False
        if active:self.started=True
        moving=self.started and (active or self.phase>1e-8)
        yaw=float(euler(data.qpos[3:7])[2])
        self.body_plan[:2]+=rotation(self.yaw_plan)[:2,0]*self.v_filtered*dt
        # Bounded setpoint error prevents a runaway reference on blocked terrain.
        self.body_plan[:2]=data.qpos[:2]+np.clip(self.body_plan[:2]-data.qpos[:2],-.10,.10)
        self.yaw_plan+=self.w_filtered*dt
        self.yaw_plan=yaw+float(np.clip(wrap(self.yaw_plan-yaw),-.22,.22))
        self.body_plan[2]=.523+float(np.mean(self.feet[:,2]-.093))
        offset=np.zeros(3)
        foot_targets=self.feet.copy()
        self.swing_leg=-1
        self.swing_legs=()
        if moving:
            pair=((0,3),(1,2))[self.step_index%2]
            phase=self.phase/self.step_time
            if .25<=phase<=.75:
                self.swing_legs=pair;self.swing_leg=pair[0]
                if not self.swing_prepared:
                    for leg in pair:
                        self.swing_starts[leg]=self.feet[leg].copy()
                        future_yaw=self.yaw_plan+self.w_filtered*self.step_time*.75
                        center=self.body_plan.copy()+rotation(self.yaw_plan)[:,0]*self.v_filtered*self.step_time*.75
                        target=center+rotation(future_yaw)@NOMINAL[leg]
                        terrain=float(height_at(target[:2])) if height_at else 0.
                        target[2]=terrain+.093
                        self.swing_ends[leg]=target
                    self.swing_prepared=True
                p=(phase-.25)/.5;s=p*p*(3-2*p)
                for leg in pair:
                    foot_targets[leg]=(1-s)*self.swing_starts[leg]+s*self.swing_ends[leg]
                    foot_targets[leg,2]+=self.clearance*math.sin(math.pi*p)
            elif phase>.75 and self.swing_prepared:
                for leg in pair:self.feet[leg]=self.swing_ends[leg].copy();foot_targets[leg]=self.feet[leg]
            self.phase+=dt
            if self.phase>=self.step_time-1e-10:
                self.phase=0.;self.step_index+=1;self.swing_prepared=False
        body_target=self.body_plan+rotation(self.yaw_plan)@offset
        for i in range(4):
            body_local=rotation(self.yaw_plan).T@(foot_targets[i]-body_target)-HIPS[i]
            q=inverse_leg(body_local,SIDES[i],i<2)
            self.target[i*4:i*4+3]=q
            # Counter-rotate the hub as the knee/hip moves: no commanded rolling cruise.
            self.target[i*4+3]=self.hub_reference[i]-q[1]-q[2]
        tau=np.zeros(16)
        # Allocate an actual contact-force wrench through stance-leg Jacobians.
        # Nothing is applied to the floating base; these remain joint torques.
        stance=[i for i in range(4) if i not in self.swing_legs]
        mass=float(self.model.body_mass.sum())
        wrench=np.zeros(6)
        velocity=rotation(self.yaw_plan)[:,0]*self.v_filtered
        wrench[:2]=120*(self.body_plan[:2]-data.qpos[:2])+60*(velocity[:2]-data.qvel[:2])
        wrench[2]=mass*9.81+500*(self.body_plan[2]-data.qpos[2])-80*data.qvel[2]
        attitude=euler(data.qpos[3:7])
        wrench[3:]=np.array([120,180,100])*np.array([-attitude[0],-attitude[1],wrap(self.yaw_plan-attitude[2])])-np.array([15,20,15])*data.qvel[3:6]
        A=np.zeros((6,3*len(stance)))
        center=data.subtree_com[self.model.body('base_link').id]
        for j,i in enumerate(stance):
            r=data.body(LEGS[i]+'_wheel').xpos-center
            A[:3,j*3:j*3+3]=np.eye(3)
            A[3:,j*3:j*3+3]=np.array([[0,-r[2],r[1]],[r[2],0,-r[0]],[-r[1],r[0],0]])
        forces=(A.T@np.linalg.solve(A@A.T+np.eye(6)*1e-4,wrench)).reshape(-1,3)
        for force,i in zip(forces,stance):
            force[2]=np.clip(force[2],0,240)
            force[:2]=np.clip(force[:2],-.7*force[2],.7*force[2])
            jac=np.zeros((3,self.model.nv));jacr=np.zeros_like(jac)
            mujoco.mj_jacBody(self.model,data,jac,jacr,self.model.body(LEGS[i]+'_wheel').id)
            tau[i*4:i*4+3]-=jac[:,self.dofs[i*4:i*4+3]].T@force
        self.force_tau=tau
        self.servo(data)
        return self.target.copy(),self.swing_leg
