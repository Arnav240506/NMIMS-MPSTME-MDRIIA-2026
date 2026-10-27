"""Fully decode the new native-state course clips and check representative frames."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np,cv2
from verify_media import video_info,frame

def main():
    p=argparse.ArgumentParser();p.add_argument('trial',type=Path);a=p.parse_args();trial=a.trial.resolve()
    receipt=json.loads((trial/'render_receipt.json').read_text());state=np.load(trial/'states.npz')
    expected=(len(state['time'])+4)//5
    rows=[video_info(trial/name) for name in ['robot_3d.mp4','hud.mp4','course_showcase.mp4']]
    assert all(r['decoded_frames']==expected and r['fps']==10 for r in rows)
    errors=[]
    for name,png in [('robot_3d.mp4','frame_0000.png'),('course_showcase.mp4','course_0000.png')]:
        image=cv2.imread(str(trial/png));assert image is not None
        error=float(np.abs(image.astype(float)-frame(trial/name,0).astype(float)).mean());assert error<10;errors.append(error)
    result={'status':'PASS','source_trial_id':receipt['source_trial_id'],'decoded_videos':rows,
        'first_frame_mean_pixel_errors':errors,'expected_frames_from_50Hz_states':expected,
        'source_sha256':{name:hashlib.sha256((trial/name).read_bytes()).hexdigest() for name in ['states.npz','scene.xml','summary.json','plans.json']},
        'interpretation':'Native MuJoCo physical-state replay; overlays are measurements and time-matched recorded online plans. No video is claimed to be a new live trial.'}
    (trial/'media_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
