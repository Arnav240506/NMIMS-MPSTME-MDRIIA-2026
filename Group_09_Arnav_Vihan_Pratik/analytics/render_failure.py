"""A real retained failure frame, selected from recorded states at contact onset."""
from pathlib import Path
import sys,json
import numpy as np,pandas as pd,mujoco,cv2,imageio.v2 as imageio
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'M20'))
from scene import compile_xml
HERE=Path(__file__).resolve().parent

def render(folder,name,when=None):
    s=json.loads((folder/'summary.json').read_text());df=pd.read_csv(folder/'telemetry.csv');a=np.load(folder/'states.npz')
    if when is None:
        indices=np.flatnonzero(df.harmful_contact_steps.to_numpy()>0);i=int(indices[0]) if len(indices) else len(df)-1
    else:i=int(np.argmin(abs(df.time_s.to_numpy()-when)))
    m=compile_xml((folder/'scene.xml').read_text());d=mujoco.MjData(m);d.qpos[:]=a['qpos'][i];d.qvel[:]=a['qvel'][i];mujoco.mj_forward(m,d)
    o=mujoco.MjvOption();o.geomgroup[1]=0;o.geomgroup[3]=1;c=mujoco.MjvCamera();c.lookat[:]=d.qpos[:3];c.distance=2.3;c.azimuth=45;c.elevation=-20
    with mujoco.Renderer(m,height=720,width=1280) as renderer:renderer.update_scene(d,camera=c,scene_option=o);pic=renderer.render().copy()
    cv2.rectangle(pic,(0,0),(1280,90),(22,24,32),-1)
    cv2.putText(pic,f'RETAINED FAILURE | {s["trial_id"]}',(20,32),cv2.FONT_HERSHEY_SIMPLEX,.8,(250,224,205),1,cv2.LINE_AA)
    cv2.putText(pic,f't={df.time_s.iloc[i]:.2f} s | outcome: {s["status"]} | accepted: false | actual recorded MuJoCo state',(20,66),cv2.FONT_HERSHEY_SIMPLEX,.55,(235,240,245),1,cv2.LINE_AA)
    imageio.imwrite(HERE.parent/'docs/figures'/name,pic)
    return {'trial_id':s['trial_id'],'recorded_sample':i,'time_s':float(df.time_s.iloc[i]),'summary_status':s['status']}

if __name__=='__main__':
    cases=[render(HERE/'benchmark/26_avoid_1026_baseline','failure_baseline_contact.png'),
           render(HERE/'benchmark/43_mission_1043_shared','failure_shared_pair_liftoff.png',when=49.2)]
    (HERE/'failure_frame_receipts.json').write_text(json.dumps(cases,indent=2))
