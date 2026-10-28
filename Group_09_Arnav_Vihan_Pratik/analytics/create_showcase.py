"""Concatenate actual native-rendered walking/mission footage and render an actual-state poster."""
from pathlib import Path
import sys,json
import numpy as np,mujoco,cv2,imageio.v2 as imageio
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'M20'))
from scene import compile_xml
HERE=Path(__file__).resolve().parent;DOC=HERE.parent/'docs';OUT=DOC/'showcase'

def main():
    OUT.mkdir(exist_ok=True);mission=HERE/'demo_runs/m20_mission';walk=HERE/'demo_runs/m20_walk'
    summary=json.loads((mission/'summary.json').read_text());fps=10;frames=0
    with imageio.get_writer(OUT/'M20_showcase.mp4',fps=fps,codec='libx264',quality=8,macro_block_size=None) as writer:
        for folder in [walk,mission]:
            reader=imageio.get_reader(folder/'robot_3d.mp4')
            for frame in reader:writer.append_data(frame);frames+=1
            reader.close()
        card=np.full((720,1280,3),(13,23,33),dtype='uint8')
        lines=['M20 | VERIFIED SIMULATION EVIDENCE',
            '4 articulated legs | 12 leg motors + 4 wheeled feet',
            f'Seed 42 mission: {summary["simulated_s"]:.2f} simulated s | harmful contacts: {summary["harmful_contact_steps"]}',
            '8 cm step: front pair, torso transfer, rear pair, all-foot support',
            '100 actual physics trials / 50 matched environments',
            'Ideal ray sensing + true pose | no measured human workload',
            'AI-assisted project; student review and individual defense required']
        for i,line in enumerate(lines):cv2.putText(card,line,(60,130+i*70),cv2.FONT_HERSHEY_SIMPLEX,.75 if i else 1.0,(230,241,245),1,cv2.LINE_AA)
        for _ in range(6*fps):writer.append_data(card);frames+=1
    # Different camera pose reveals the warehouse scenery; robot state is unchanged.
    state=np.load(mission/'states.npz');i=int(np.argmin(abs(state['time']-41.5)))
    m=compile_xml((mission/'scene.xml').read_text());d=mujoco.MjData(m);d.qpos[:]=state['qpos'][i];d.qvel[:]=state['qvel'][i];mujoco.mj_forward(m,d)
    opt=mujoco.MjvOption();opt.geomgroup[1]=0;opt.geomgroup[3]=1;cam=mujoco.MjvCamera();cam.lookat[:]=d.qpos[:3]+[0,0,-.10];cam.distance=2.6;cam.azimuth=45;cam.elevation=-17
    with mujoco.Renderer(m,height=720,width=1280) as renderer:
        renderer.update_scene(d,camera=cam,scene_option=opt);poster=renderer.render().copy()
    cv2.rectangle(poster,(0,0),(1280,105),(13,23,33),-1)
    cv2.putText(poster,'M20 | HAZARDOUS TERRAIN RECONNAISSANCE',(30,45),cv2.FONT_HERSHEY_SIMPLEX,.9,(232,244,246),1,cv2.LINE_AA)
    cv2.putText(poster,'Actual MuJoCo state | paired-leg climb | industrial inspection yard',(30,81),cv2.FONT_HERSHEY_SIMPLEX,.60,(87,220,192),1,cv2.LINE_AA)
    imageio.imwrite(DOC/'figures/video_poster.png',poster)
    receipt={'duration_s':frames/fps,'frames':frames,'fps':fps,'clips':[str((f/'robot_3d.mp4').relative_to(HERE.parent)) for f in [walk,mission]],
       'edits':'Full walking and full mission clips at original 10 fps plus 6 s factual end card; no generated robot frames',
       'poster_time_s':float(state['time'][i]),'poster':'Actual recorded M20 qpos/qvel with alternate native MuJoCo camera',
       'no_public_post':True}
    (OUT/'showcase_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(receipt)

if __name__=='__main__':main()
