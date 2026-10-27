"""Actual recovered M20 anatomy and seeded industrial reconnaissance fixtures."""
from pathlib import Path
from dataclasses import dataclass,asdict
import xml.etree.ElementTree as ET
import numpy as np
import mujoco
from legged_control import initialize

MODEL_DIR=Path(__file__).resolve().parent
GROUP=MODEL_DIR.parent
ROOT=GROUP.parent
VERSION='m20-capstone-v4-500hz'

@dataclass(frozen=True)
class TrialConfig:
    seed:int=42
    mode:str='mission'
    policy:str='shared'
    latency_s:float=.35
    duration_s:float=50.
    speed_m_s:float=.35
    timestep:float=.002
    roughness_m:float=0.
    initial_y_jitter_m:float=0.
    initial_yaw_jitter_rad:float=0.
    def __post_init__(self):
        if self.mode not in ('flat','walk','climb','avoid','mission','blocked','tilt','slope','course','course_blocked','course_climb'):raise ValueError('Unknown scenario')
        if self.policy not in ('shared','baseline'):raise ValueError('Unknown policy')
        if self.duration_s<=0 or self.latency_s<0 or not 0<self.speed_m_s<=.5:raise ValueError('Invalid time/speed')
        if not 0<=self.roughness_m<=.01 or not 0<=self.initial_y_jitter_m<=.05 or not 0<=self.initial_yaw_jitter_rad<=.05:
            raise ValueError('Invalid terrain or initial-state perturbation')
        if self.timestep!=.002:raise ValueError('The verified capstone protocol requires 2 ms physics steps')

def mesh_assets():
    return {f'meshes/{p.name}':p.read_bytes() for p in (MODEL_DIR/'meshes').glob('*.STL')}

def compile_xml(xml):return mujoco.MjModel.from_xml_string(xml,assets=mesh_assets())

def build_scene(config):
    rng=np.random.default_rng(config.seed)
    tree=ET.parse(MODEL_DIR/'M20.xml');root=tree.getroot();world=root.find('worldbody')
    root.set('model','M20_hazardous_reconnaissance')
    for old in root.findall('option'):root.remove(old)
    ET.SubElement(root,'option',timestep=str(config.timestep),integrator='implicitfast',gravity='0 0 -9.81',cone='pyramidal')
    ET.SubElement(root,'visual')
    visual=root.findall('visual')[-1]
    ET.SubElement(visual,'global',offwidth='1280',offheight='720')
    ET.SubElement(visual,'headlight',ambient='.45 .45 .47',diffuse='.75 .75 .75')
    ET.SubElement(visual,'quality',shadowsize='2048')
    asset=root.find('asset')
    asset.find("texture[@name='texplane']").set('rgb1','.31 .32 .32')
    asset.find("texture[@name='texplane']").set('rgb2','.34 .35 .35')
    asset.find("material[@name='MatPlane']").set('reflectance','.02')
    asset.find("material[@name='MatPlane']").set('texrepeat','3 3')
    ET.SubElement(asset,'texture',name='yard_sky',type='skybox',builtin='gradient',rgb1='.30 .37 .43',rgb2='.78 .81 .82',width='512',height='2048')
    for name,rgba in [('torso_material','.73 .77 .78 1'),('leg_material','.24 .31 .35 1'),('tire_material','.08 .09 .10 1')]:
        ET.SubElement(asset,'material',name=name,rgba=rgba)
    for i,geom in enumerate(world.iter('geom')):
        if 'class' in geom.attrib:
            if geom.get('class')=='collision':geom.set('name',f'robot_collision_{i}')
            elif geom.get('class')=='visual':
                name=geom.get('mesh','')
                geom.set('material','torso_material' if name=='base_link' else 'tire_material' if 'wheel' in name else 'leg_material')
    for joint in world.iter('joint'):
        joint.set('damping','.2');joint.set('armature','.02')
    body=world.find("body[@name='base_link']")
    ET.SubElement(body,'site',name='recon_lidar',pos='.30 0 .12',size='.008',rgba='.1 .9 .7 1')
    ET.SubElement(body,'camera',name='recon_camera',pos='.37646 0 .03738',xyaxes='0 -1 0 .2079 0 .9781',fovy='60')
    for p in ('fl','fr','hl','hr'):
        ET.SubElement(body.find(f".//body[@name='{p}_wheel']"),'site',name=f'{p}_foot',size='.006',rgba='.9 .5 .1 1')
    friction=float(rng.uniform(.75,1.15))
    floor=world.find("geom[@name='floor']");floor.set('friction',f'{friction} .005 .0001');floor.set('size','12 10 .1')
    hazards=[];supports=['floor'];metadata={'config':asdict(config),'version':VERSION,'friction':friction}
    mode=config.mode
    course=mode.startswith('course')
    lip=1.3 if mode=='climb' else 2.8
    height=.08 if config.seed==42 else float(rng.uniform(.055,.085))
    goal=[2.35,0.] if mode=='climb' else [4.2,0.] if mode=='mission' else [3.,0.]
    if course:goal=[13.5 if mode=='course_climb' else 8.6,0.]
    if mode in ('climb','mission'):
        ET.SubElement(world,'geom',name='rubble_step',type='box',size='1.5 1.65 '+str(height/2),pos=f'{lip+1.5} 0 {height/2}',rgba='.52 .48 .42 1',group='0',friction='1.0 .005 .0001')
        supports.append('rubble_step')
    if mode in ('avoid','mission','blocked'):
        x=1.3+float(rng.uniform(-.10,.10));y=float(rng.uniform(-.15,.15));half_y=float(rng.uniform(.40,.60))
        if mode=='blocked':half_y=3.;y=0.
        ET.SubElement(world,'geom',name='hazard_barrier',type='box',size=f'.10 {half_y} .125',pos=f'{x} {y} .125',rgba='.65 .32 .22 1',group='0')
        hazards.append('hazard_barrier')
    if mode=='slope':
        ET.SubElement(world,'geom',name='slope_fixture',type='box',size='.8 1 .04',pos='1.8 0 .10',euler='0 -.139626 0',rgba='.5 .48 .44 1',group='0')
        supports.append('slope_fixture')
    if mode not in ('flat','walk','tilt','course','course_blocked','course_climb'):
        for i in range(10):
            x=float(rng.uniform(.8,3.8));y=float(rng.uniform(-1.9,1.9));h=float(rng.uniform(.003,.018))
            # Keep the nominal climb docking lane clear; random rubble remains around it.
            if mode in ('climb','mission') and abs(y)<.55:continue
            ET.SubElement(world,'geom',name=f'low_rubble_{i}',type='box',size=f'.07 .09 {h/2}',pos=f'{x} {y} {h/2}',euler=f'0 0 {rng.uniform(-2,2)}',rgba='.48 .46 .41 1',group='0')
            supports.append(f'low_rubble_{i}')
    if not course:
        ET.SubElement(world,'geom',name='storage_tank',type='cylinder',size='.28 .6',pos='3.8 -2.2 .6',rgba='.66 .46 .21 1',group='0')
        hazards.append('storage_tank')
    def decoration(name,**attributes):
        ET.SubElement(world,'geom',name=name,group='3',contype='0',conaffinity='0',**attributes)
    if course:
        metadata.update(map_resolution_m=.05,map_bounds=[-1.2,15.4 if mode=='course_climb' else 10.,-3.4,3.4],
            scene_description='Industrial disaster-response training yard: staggered barricades, drums, crates, tanks and pipe racks')
        # Three alternating obstacles require repeated detours; no route waypoints
        # are supplied to the executive. Jitter changes real collision geometry.
        def box(name,x,y,sx,sy,sz,color):
            ET.SubElement(world,'geom',name=name,type='box',size=f'{sx} {sy} {sz}',pos=f'{x} {y} {sz}',rgba=color,group='0',friction='1 .005 .0001')
            hazards.append(name)
        def cylinder(name,x,y,r,h,color):
            ET.SubElement(world,'geom',name=name,type='cylinder',size=f'{r} {h/2}',pos=f'{x} {y} {h/2}',rgba=color,group='0')
            hazards.append(name)
        jitter=rng.uniform(-.08,.08,3)
        for i,(x,y) in enumerate([(1.8,-.65),(4.3,.65),(6.8,-.65)]):
            box(f'course_barricade_{i}',x,float(y+jitter[i]),.16,1.05,.30,'.76 .37 .13 1')
            for k in range(5):
                decoration(f'barrier_stripe_{i}_{k}',type='box',size='.163 .08 .07',pos=f'{x} {y+jitter[i]-.8+k*.4} .49',rgba='.10 .13 .15 1')
        for i,(x,y) in enumerate([(2.6,2.55),(5.15,-2.55),(7.65,2.5)]):
            cylinder(f'course_drum_{i}',x,y,.22,.78,'.68 .22 .16 1')
            for k,z in enumerate([.12,.66]):decoration(f'drum_band_{i}_{k}',type='cylinder',size='.225 .025',pos=f'{x} {y} {z}',rgba='.88 .76 .39 1')
        for i,(x,y) in enumerate([(.9,-2.5),(3.3,-2.65),(5.6,2.6),(8.6,-2.6)]):
            box(f'course_crate_{i}',x,y,.32,.28,.28,'.48 .37 .23 1')
            for k in [-1,1]:decoration(f'crate_band_{i}_{k}',type='box',size='.325 .025 .282',pos=f'{x} {y+k*.19} .28',rgba='.21 .24 .25 1')
        for i,(x,y) in enumerate([(1.,2.7),(8.7,2.65)]):
            cylinder(f'course_tank_{i}',x,y,.35,1.1,'.24 .43 .48 1')
        for i,(x,y) in enumerate([(3.6,2.75),(6.2,-2.75)]):
            box(f'course_pipe_rack_{i}',x,y,.44,.25,.22,'.26 .31 .35 1')
            for k in range(3):decoration(f'pipe_{i}_{k}',type='cylinder',size='.09 .50',pos=f'{x} {y+(k-1)*.16} .51',euler='0 1.570796 0',rgba='.52 .59 .60 1')
        # Physical boundary rails prevent an unmeasured escape around the arena.
        for i,y in enumerate([-3.15,3.15]):box(f'course_boundary_{i}',7.1 if mode=='course_climb' else 4.5,y,7.7 if mode=='course_climb' else 5.1,.08,.24,'.34 .40 .42 1')
        if mode=='course_climb':
            floor.set('size','18 10 .1')
            for i,(lip,surface) in enumerate([(9.3,.08),(12.1,.16)]):
                ET.SubElement(world,'geom',name=f'climb_terrace_{i}',type='box',size=f'1.65 1.65 {surface/2}',pos=f'{lip+1.65} 0 {surface/2}',rgba='.51 .48 .41 1',group='0',friction='1 .005 .0001')
                supports.append(f'climb_terrace_{i}')
                decoration(f'terrace_lip_mark_{i}',type='box',size='.025 1.65 .001',pos=f'{lip+.03} 0 {surface+.002}',rgba='.96 .69 .17 1')
            for i,(x,y) in enumerate([(11,-2.6),(11,2.6)]):cylinder(f'extension_tank_{i}',x,y,.25,.9,'.25 .45 .48 1')
            for i,y in enumerate([-2.6,2.6]):box(f'extension_crate_{i}',14,y,.32,.28,.28,'.48 .37 .23 1')
        if mode=='course_blocked':box('course_closed_gate',3.3,0,.14,3.12,.5,'.65 .13 .12 1')
        decoration('warehouse_back',type='box',size=f'{7.7 if mode=="course_climb" else 5.2} .10 1.7',pos=f'{7.1 if mode=="course_climb" else 4.5} 3.65 1.7',rgba='.23 .31 .35 1')
        decoration('warehouse_side',type='box',size='.10 3.6 1.7',pos=f'{15.5 if mode=="course_climb" else 10.3} 0 1.7',rgba='.27 .34 .37 1')
        for i in range(13 if mode=='course_climb' else 9):
            decoration(f'warehouse_pillar_{i}',type='box',size='.055 .12 1.74',pos=f'{i*1.2-.3} 3.50 1.74',rgba='.45 .51 .53 1')
        for i in range(4):
            decoration(f'warehouse_window_{i}',type='box',size='.38 .02 .26',pos=f'{i*2.1+1} 3.53 2.35',rgba='.22 .48 .57 1')
        for i in range(30 if mode=='course_climb' else 19):
            for side in [-1,1]:decoration(f'course_lane_{i}_{side}',type='box',size='.14 .025 .001',pos=f'{i*.50} {side*2.95} .002',rgba='.95 .69 .18 1')
        decoration('start_pad',type='box',size='.55 .5 .001',pos='0 0 .002',rgba='.22 .39 .47 1')
        decoration('goal_pad',type='box',size='.45 .5 .001',pos=f'{goal[0]} 0 {.162 if mode=="course_climb" else .002}',rgba='.12 .47 .36 1')
        for i,x in enumerate([-.6,14.5 if mode=='course_climb' else 9.2]):
            decoration(f'inspection_beacon_{i}',type='cylinder',size='.04 .45',pos=f'{x} 1 .45',rgba='.85 .65 .18 1')
            decoration(f'beacon_lamp_{i}',type='sphere',size='.10',pos=f'{x} 1 .95',rgba='.18 .92 .60 1')
        metadata['collision_obstacles']=len(hazards)
    else:
        decoration('warehouse_back',type='box',size='3.3 .1 1.3',pos='2.2 3.3 1.3',rgba='.30 .36 .39 1')
        decoration('warehouse_side',type='box',size='.1 2.0 1.3',pos='5.4 1.4 1.3',rgba='.25 .30 .33 1')
    decoration('goal_marker',type='cylinder',size='.12 .002',pos=f'{goal[0]} {goal[1]} {height+.003 if mode in ("climb","mission") else .163 if mode=="course_climb" else .003}',rgba='.15 .83 .63 1')
    for i in range(8):decoration(f'lane_mark_{i}',type='box',size='.14 .025 .001',pos=f'{i*.55} -2.7 .002',rgba='.9 .65 .15 1')
    for i in range(10):decoration(f'crack_{i}',type='box',size='.16 .003 .0005',pos=f'{rng.uniform(-.4,4.5)} {rng.uniform(-2.5,2.5)} .001',euler=f'0 0 {rng.uniform(-3,3)}',rgba='.16 .17 .17 1')
    if course and config.roughness_m:
        for i in range(36):
            x=float(rng.uniform(.5,8.2));y=float(rng.uniform(-2.,2.));h=float(rng.uniform(.5*config.roughness_m,config.roughness_m))
            name=f'course_low_rubble_{i}'
            ET.SubElement(world,'geom',name=name,type='box',size=f'.11 .10 {h/2}',pos=f'{x} {y} {h/2}',rgba='.42 .43 .41 1',group='0',friction='1 .005 .0001')
            supports.append(name)
    xml=ET.tostring(root,encoding='unicode');model=compile_xml(xml);data=mujoco.MjData(model);initialize(model,data,crouch=config.mode!='walk')
    perturb_y=float(rng.uniform(-config.initial_y_jitter_m,config.initial_y_jitter_m)) if config.initial_y_jitter_m else 0.
    perturb_yaw=float(rng.uniform(-config.initial_yaw_jitter_rad,config.initial_yaw_jitter_rad)) if config.initial_yaw_jitter_rad else 0.
    data.qpos[1]+=perturb_y
    if perturb_yaw:data.qpos[3:7]=[np.cos(perturb_yaw/2),0,0,np.sin(perturb_yaw/2)]
    mujoco.mj_forward(model,data)
    metadata.update(roughness_upper_bound_m=config.roughness_m,initial_y_m=perturb_y,initial_yaw_rad=perturb_yaw)
    if mode=='tilt':
        a=np.deg2rad(32);data.qpos[2]+=.16;data.qpos[3:7]=[np.cos(a/2),np.sin(a/2),0,0];mujoco.mj_forward(model,data)
    metadata.update(goal=goal,step_lip_m=lip if mode in ('climb','mission') else None,
        step_height_m=height if mode in ('climb','mission') else 0.,hazards=hazards,supports=supports,xml=xml)
    if mode=='course_climb':
        metadata.update(step_lip_m=9.3,step_height_m=.16,step_targets=[{'lip_m':9.3,'height_m':.08},{'lip_m':12.1,'height_m':.16}])
    return model,data,metadata

if __name__=='__main__':
    m,d,meta=build_scene(TrialConfig())
    target=MODEL_DIR/'M20_hazardous_terrain.xml'
    target.write_text(meta['xml'],encoding='utf-8')
    # The course's legacy model filename now resolves to the actual M20 anatomy.
    tree=ET.fromstring(meta['xml'])
    for c in tree.findall('compiler'):
        if 'meshdir' in c.attrib:c.set('meshdir','../M20/meshes/')
    (GROUP/'models/hazardous_terrain_ugv.xml').write_text(ET.tostring(tree,encoding='unicode'),encoding='utf-8')
    print('M20 model',m.nq,m.nv,m.nu,'mass',sum(m.body_mass),'generated default yard.')
