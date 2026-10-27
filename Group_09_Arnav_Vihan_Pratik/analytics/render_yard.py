# Presentation variant: includes noncolliding warehouse/yard decorative group 3.
# Physical states and benchmark engine remain unchanged.
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'M20'))
"""Render captured physical states; never animates or overwrites experimental results."""
from pathlib import Path
import argparse,json
import numpy as np,pandas as pd,mujoco,cv2,imageio.v2 as imageio
from scene import compile_xml
from m20_rosbot_mapping import M20Map

def label(image,text,x=16,y=30,scale=.65,color=(240,245,248)):
    cv2.putText(image,text,(x,y),cv2.FONT_HERSHEY_SIMPLEX,scale,color,1,cv2.LINE_AA)

def map_panel(grid,trajectory,path,cost=False):
    z=grid.cost if cost else grid.mean
    normalized=np.clip(z/(3 if cost else .30),0,1)
    pic=cv2.applyColorMap((np.nan_to_num(normalized)*255).astype('uint8'),cv2.COLORMAP_TURBO)
    pic=cv2.cvtColor(pic,cv2.COLOR_BGR2RGB);pic[~grid.known]=[32,42,52]
    pic[grid.inflated]=[180,66,58]
    def points(xys):return np.array([[grid.cell(p)[1],grid.cell(p)[0]] for p in xys],dtype='int32')
    if len(path)>1:cv2.polylines(pic,[points(path)],False,(255,225,65),1)
    if len(trajectory)>1:cv2.polylines(pic,[points(trajectory)],False,(50,245,200),1)
    if len(trajectory):cv2.circle(pic,tuple(points(trajectory[-1:])[0]),4,(255,255,255),-1)
    pic=np.flipud(pic).copy();pic=cv2.resize(pic,(640,360),interpolation=cv2.INTER_NEAREST)
    cv2.rectangle(pic,(0,0),(640,39),(17,27,37),-1)
    label(pic,'TRAVERSABILITY + A*' if cost else 'MEASURED ELEVATION + TRAJECTORY',y=26)
    b=grid.bounds
    label(pic,f'x: {b[0]:g}..{b[1]:g} m | y: {b[2]:g}..{b[3]:g} m | grid: {grid.resolution:g} m',x=12,y=345,scale=.45)
    return pic

def replay(folder,record=True,show=False,fps=10):
    folder=Path(folder);s=json.loads((folder/'summary.json').read_text());state=np.load(folder/'states.npz')
    telemetry=pd.read_csv(folder/'telemetry.csv');m=compile_xml((folder/'scene.xml').read_text());d=mujoco.MjData(m)
    opt=mujoco.MjvOption();opt.geomgroup[1]=0;opt.geomgroup[3]=1
    renderer=mujoco.Renderer(m,height=360,width=640)
    hero=mujoco.Renderer(m,height=720,width=1280)
    course=s['config']['mode'].startswith('course')
    camera=mujoco.MjvCamera();camera.distance=3.1 if course else 2.5;camera.azimuth=45;camera.elevation=-27 if course else -19
    grid=M20Map(s['terrain'].get('map_resolution_m',.03),s['terrain'].get('map_bounds',(-1.2,6.,-3.,3.)))
    traj=[];path=np.load(folder/'map.npz')['path'];writer=hero_writer=course_writer=None
    plans=json.loads((folder/'plans.json').read_text()) if (folder/'plans.json').exists() else []
    plan_index=0
    combined=s['config']['mode']=='course_climb'
    overview=mujoco.MjvCamera();overview.lookat[:]=[7.2 if combined else 4.25,0,.1];overview.distance=16 if combined else 11;overview.azimuth=90;overview.elevation=-65 if combined else -59
    if record:
        writer=imageio.get_writer(folder/'hud.mp4',fps=fps,codec='libx264',quality=8,macro_block_size=None)
        hero_writer=imageio.get_writer(folder/'robot_3d.mp4',fps=fps,codec='libx264',quality=8,macro_block_size=None)
        if course:course_writer=imageio.get_writer(folder/'course_showcase.mp4',fps=fps,codec='libx264',quality=8,macro_block_size=None)
    stride=max(1,round(1/(fps*.02)));frame_count=0
    try:
        for i in range(len(state['time'])):
            d.qpos[:]=state['qpos'][i];d.qvel[:]=state['qvel'][i];d.time=state['time'][i];mujoco.mj_forward(m,d)
            grid.scan(m,d);traj.append(d.qpos[:2].copy())
            if i%stride:continue
            row=telemetry.iloc[i]
            if plans:
                while plan_index+1<len(plans) and plans[plan_index+1]['time_s']<=d.time:plan_index+=1
                path=np.asarray(plans[plan_index]['path_m']).reshape(-1,2) if plans[plan_index]['time_s']<=d.time else np.empty((0,2))
            renderer.update_scene(d,camera='recon_camera',scene_option=opt);rgb=renderer.render().copy()
            renderer.enable_depth_rendering();depth=renderer.render().copy();renderer.disable_depth_rendering()
            dp=cv2.applyColorMap((np.clip(depth/5,0,1)*255).astype('uint8'),cv2.COLORMAP_VIRIDIS);dp=cv2.cvtColor(dp,cv2.COLOR_BGR2RGB)
            for panel,title in [(rgb,'FRONT CAMERA | SIMULATED RGB'),(dp,'FRONT DEPTH | 0..5 m')]:
                cv2.rectangle(panel,(0,0),(640,39),(17,27,37),-1);label(panel,title,y=26)
            canvas=np.full((800,1280,3),(13,23,33),dtype=np.uint8)
            canvas[50:410,:640]=rgb;canvas[50:410,640:]=dp
            canvas[410:770,:640]=map_panel(grid,traj,path)
            canvas[410:770,640:]=map_panel(grid,traj,path,True)
            label(canvas,f'M20 QUADRUPED  |  {row.phase}  |  t={d.time:.1f} s',y=33,scale=.8)
            label(canvas,f'roll {row.roll_deg:+.1f} deg | pitch {row.pitch_deg:+.1f} deg | known {grid.known.mean():.0%} | true-pose mapping | recorded physics replay',y=792,scale=.52)
            camera.lookat[:]=d.qpos[:3]+[0,0,-.12]
            hero.update_scene(d,camera=camera,scene_option=opt);view=hero.render().copy()
            cv2.rectangle(view,(0,0),(1280,70),(13,23,33),-1)
            label(view,'M20 | ARTICULATED QUADRUPED RECONNAISSANCE',y=30,scale=.8)
            label(view,f'{row.phase}  |  MuJoCo physical-state replay  |  t={d.time:.1f} s  |  seed {s["config"]["seed"]}',y=57,scale=.54)
            if record:writer.append_data(canvas);hero_writer.append_data(view)
            if course:
                renderer.update_scene(d,camera=overview,scene_option=opt);over=renderer.render().copy()
                label(over,'COURSE OVERVIEW | actual collision geometry',y=26,scale=.52)
                dashboard=np.full((800,1280,3),(13,23,33),dtype=np.uint8)
                dashboard[65:548,:860]=cv2.resize(view,(860,483))
                dashboard[65:301,860:]=cv2.resize(over,(420,236))
                dashboard[312:548,860:]=cv2.resize(map_panel(grid,traj,path,True),(420,236))
                label(dashboard,'M20 | INDUSTRIAL OBSTACLE AVOIDANCE',y=37,scale=1.)
                label(dashboard,f'{s["terrain"]["collision_obstacles"]} physical obstacles + boundaries | seeded scene {s["config"]["seed"]} | t={d.time:.1f}s',y=580,scale=.68)
                label(dashboard,f'REASON: {row.reason}   |   speed {row.speed_m_s:.2f} m/s   |   forward range {row.clearance_m:.2f} m',y=620,scale=.66)
                label(dashboard,f'Roll {row.roll_deg:+.2f} deg   Pitch {row.pitch_deg:+.2f} deg   |   harmful contact steps {row.harmful_contact_steps}',y=660,scale=.66)
                climbs=sum(r['verified_time_s']<=d.time for r in s.get('climb_records',[]))
                status=f' | verified climbs {climbs}/2' if combined else ''
                label(dashboard,f'Goal error {np.linalg.norm(d.qpos[:2]-s["terrain"]["goal"]):.2f} m | map {grid.known.mean():.0%} | unknown blocked{status}',y=700,scale=.61)
                label(dashboard,'Native MuJoCo recorded physics | time-matched plans in yellow, trajectory in cyan',y=747,scale=.60)
                label(dashboard,'Ideal rays + exact simulation pose | wheeled-foot cruise on the articulated M20 quadruped',y=779,scale=.55)
                if course_writer:course_writer.append_data(dashboard)
                if frame_count in (0,150,300,450,600,750,900,1050,1200):imageio.imwrite(folder/f'course_{frame_count:04d}.png',dashboard)
                if frame_count==0:imageio.imwrite(folder/'course_overview.png',over)
            if frame_count in (0,100,200,400) or (str(row.phase)=='REAR_PAIR_STEP' and not (folder/'paired_climb.png').exists()):
                imageio.imwrite(folder/f'frame_{frame_count:04d}.png',view)
                imageio.imwrite(folder/f'hud_{frame_count:04d}.png',canvas)
                if str(row.phase)=='REAR_PAIR_STEP':imageio.imwrite(folder/'paired_climb.png',view)
            if show:
                cv2.imshow('M20 quadruped | recorded physical states',cv2.cvtColor(view,cv2.COLOR_RGB2BGR))
                cv2.imshow('M20 reconnaissance | RGB depth elevation cost',cv2.cvtColor(canvas,cv2.COLOR_RGB2BGR))
                if cv2.waitKey(round(1000/fps))&255==27:break
            frame_count+=1
    finally:
        renderer.close();hero.close()
        if writer:writer.close();hero_writer.close()
        if course_writer:course_writer.close()
        if show:cv2.destroyAllWindows()
    receipt={'source_trial_id':s['trial_id'],'physical_state_samples':len(state['time']),'rendered_frames':frame_count,'fps':fps,
             'duration_s':frame_count/fps,'rendering':'Native MuJoCo STL meshes; actual recorded qpos/qvel; ideal camera depth',
             'maps':'Recomputed rays from recorded poses; course yellow plans are time-matched to actual online plans.json; legacy yard uses final-path overlay',
             'result':s['status'],'accepted':s['accepted']}
    (folder/'render_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--show',action='store_true');p.add_argument('--no-record',action='store_true')
    a=p.parse_args();print(replay(a.folder,not a.no_record,a.show))
