"""Native live view of the exact logged capstone engine, with FSM overlays."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'M20'))
from simulation import main
if __name__=='__main__':
    if '--live' not in sys.argv:sys.argv.append('--live')
    raise SystemExit(main(default_mode='course_climb'))
