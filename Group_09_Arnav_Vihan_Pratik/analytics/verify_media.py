"""Decode all delivered video frames and compare showcase samples with actual source clips."""
from pathlib import Path
import json
import cv2,numpy as np
HERE=Path(__file__).resolve().parent;DOC=HERE.parent/'docs'

def video_info(path):
    cap=cv2.VideoCapture(str(path));assert cap.isOpened(),str(path)
    fps=cap.get(cv2.CAP_PROP_FPS);count=0;shape=None
    while True:
        ok,frame=cap.read()
        if not ok:break
        assert np.isfinite(frame).all();shape=frame.shape;count+=1
    cap.release();return {'path':str(path.relative_to(HERE.parent)),'decoded_frames':count,'fps':fps,'duration_s':count/fps,'shape':shape}

def frame(path,i):
    cap=cv2.VideoCapture(str(path));cap.set(cv2.CAP_PROP_POS_FRAMES,i);ok,a=cap.read();cap.release();assert ok;return a

if __name__=='__main__':
    walk=HERE/'demo_runs/m20_walk/robot_3d.mp4';mission=HERE/'demo_runs/m20_mission/robot_3d.mp4';show=DOC/'showcase/M20_showcase.mp4'
    files=[walk,mission,HERE/'demo_runs/m20_walk/hud.mp4',HERE/'demo_runs/m20_mission/hud.mp4',show]
    rows=[video_info(p) for p in files]
    assert [r['decoded_frames'] for r in rows]==[120,594,120,594,774]
    differences=[float(np.abs(frame(show,30).astype(float)-frame(walk,30)).mean()),
                 float(np.abs(frame(show,120+415).astype(float)-frame(mission,415)).mean())]
    assert max(differences)<10
    receipt={'status':'PASS','source_comparison_mean_pixel_errors':differences,'videos':rows,
       'interpretation':'Complete videos decoded; showcase walking and mission frames match native-rendered source clips within recompression tolerance. Six-second card is editorial text.'}
    (HERE/'media_verification.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
