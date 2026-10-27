"""500 Hz measured telemetry and an evaluation-only fixed task-path reference.

The static A* reference uses fixture geometry for scoring only. It is never
passed to the controller or its measured map. Nearest-segment projection
measures cross-track deviation, not time-parameterized trajectory accuracy.
"""
from pathlib import Path
import csv,json,hashlib
import numpy as np
from scipy import ndimage
from m20_rosbot_mapping import M20Map,astar

def project_path(point,path):
    path=np.asarray(path,float)
    if len(path)==0:return np.full(2,np.nan),float('nan')
    if len(path)==1:return path[0].copy(),float(np.sum((point-path[0])**2))
    a=path[:-1];v=path[1:]-a;den=np.einsum('ij,ij->i',v,v)
    ratio=np.clip(np.einsum('ij,ij->i',point-a,v)/np.maximum(den,1e-15),0,1)
    projections=a+ratio[:,None]*v
    d2=np.sum((projections-point)**2,axis=1);j=int(np.argmin(d2))
    return projections[j],float(d2[j])

def task_reference(model,data,meta):
    grid=M20Map(.05,meta.get('map_bounds',[-1.2,6.,-3.,3.]))
    grid.count[:]=1;grid.cost[:]=0;xx,yy=np.meshgrid(grid.xs,grid.ys)
    occupied=np.zeros(grid.shape,bool)
    for name in meta['hazards']:
        geom=model.geom(name);x,y=geom.pos[:2];sx,sy=geom.size[:2]
        if int(geom.type[0])==5:  # MuJoCo cylinder
            occupied|=(xx-x)**2+(yy-y)**2<=sx*sx
        else:
            # All scored yard hazards are axis-aligned boxes or cylinders.
            occupied|=(abs(xx-x)<=sx)&(abs(yy-y)<=sy)
    distance=ndimage.distance_transform_edt(~occupied)*grid.resolution
    grid.inflated=distance<=.70
    grid.cost[:]=.3*np.clip((1.2-distance)/1.2,0,1)
    start=data.qpos[:2].copy();goals=[]
    if meta['step_height_m']:
        goals.append(np.array([meta['step_lip_m']-.55,0.]))
    goals.append(np.array(meta['goal']))
    result=[start]
    for goal in goals:
        cells=astar(grid,grid.cell(result[-1]),grid.cell(goal))
        if not cells:return np.empty((0,2))
        result.extend(grid.xy(c) for c in cells[1:]);result.append(goal)
    # Remove duplicate and collinear points without changing the polyline.
    path=np.asarray(result);keep=[0]
    for i in range(1,len(path)-1):
        u=path[i]-path[keep[-1]];v=path[i+1]-path[i]
        if np.linalg.norm(u)<1e-10:continue
        if abs(u[0]*v[1]-u[1]*v[0])>1e-9 or np.dot(u,v)<0:keep.append(i)
    keep.append(len(path)-1)
    return path[keep]

class TrialLogger:
    """Stream real samples to bounded plain CSVs; no interpolation or target data."""
    def __init__(self,out,model,data,meta,config,max_rows=20000):
        self.out=Path(out);self.config=config;self.max_rows=max_rows
        self.path=task_reference(model,data,meta)
        self.rows=0;self.part=0;self.file=None;self.files=[];self.sq_error=0.;self.error_samples=0
        self.effort=0.;self.navigation_effort=0.;self.last_phase='';self.last_reason=''
        self.header=['run_id','seed','time_s','dt_s','x_m','y_m','z_m','qw','qx','qy','qz',
            'vx_m_s','vy_m_s','vz_m_s','wx_rad_s','wy_rad_s','wz_rad_s',
            'reference_x_m','reference_y_m','error_x_m','error_y_m','tracking_valid',
            'command_v_m_s','command_w_rad_s',
            *[f'tau_{i:02d}_Nm' for i in range(model.nu)],
            'effort_cumulative_Nm2_s','phase','reason','event','harmful_contact_step','support_count']
        assert model.nu==16 and np.allclose(model.actuator_gear[:,0],1)
        self.metadata={'rate_hz':1/config.timestep,'sample_timing':'Post-step pose/velocity; actuator force over the preceding 2 ms step',
            'reference':'Fixed offline A* collision-map polyline with docking point; evaluation only, never controller input',
            'metric':'Nearest-segment XY cross-track RMSE after 2.4 s; different run durations and failure rates must also be reported',
            'path_m':self.path.tolist(),'inflation_m':.70,'actuator_names':[model.actuator(i).name for i in range(model.nu)],
            'column_units':'SI; actuator torque N m; effort (N m)^2 s; time s',
            'run_id':self.out.name,'seed':config.seed,'source_of_samples':'Actual mj_step state and actuator_force',
            'numeric_serialization':'Time and dt fixed 6 decimals; measured numeric channels 9 significant digits',
            'max_rows_per_csv':max_rows}

    def sample(self,data,executive,harm,support_count):
        if self.file is None or self.rows%self.max_rows==0:
            if self.file:self.file.close()
            self.part+=1;name=f'{self.part:03d}_real_trials.csv';self.files.append(name)
            self.file=(self.out/name).open('w',newline='',encoding='utf-8')
            self.writer=csv.writer(self.file);self.writer.writerow(self.header)
        dt=self.config.timestep;torques=data.actuator_force.copy()
        self.effort+=float(np.dot(torques,torques))*dt
        ref,d2=project_path(data.qpos[:2],self.path);valid=data.time>=2.4 and np.isfinite(d2)
        if valid:self.sq_error+=d2;self.error_samples+=1;self.navigation_effort+=float(np.dot(torques,torques))*dt
        changed=[]
        if executive.phase!=self.last_phase:changed.append('phase');self.last_phase=executive.phase
        if executive.reason!=self.last_reason:changed.append('decision');self.last_reason=executive.reason
        values=[*data.qpos[:7],*data.qvel[:6],*ref,*(data.qpos[:2]-ref)]
        self.writer.writerow([self.out.name,self.config.seed,f'{data.time:.6f}',f'{dt:.6f}',
            *[f'{v:.9g}' for v in values],int(valid),f'{executive.v:.9g}',f'{executive.w:.9g}',
            *[f'{v:.9g}' for v in torques],f'{self.effort:.12g}',executive.phase,executive.reason,
            '+'.join(changed),int(bool(harm)),int(support_count)])
        self.rows+=1

    def close(self):
        if self.file:self.file.close();self.file=None
        self.metadata.update(samples=self.rows,files=[{'path':n,'sha256':hashlib.sha256((self.out/n).read_bytes()).hexdigest(),'bytes':(self.out/n).stat().st_size} for n in self.files],
            tracking_samples=self.error_samples,tracking_rmse_m=float(np.sqrt(self.sq_error/self.error_samples)) if self.error_samples else None,
            control_effort_Nm2_s=self.effort,navigation_control_effort_Nm2_s=self.navigation_effort)
        (self.out/'telemetry_schema.json').write_text(json.dumps(self.metadata,indent=2),encoding='utf-8')
        return self.metadata
