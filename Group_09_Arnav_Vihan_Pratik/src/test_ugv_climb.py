"""Course entry point for the recovered M20 quadruped."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"M20"))
from simulation import main
if __name__=="__main__":raise SystemExit(main("climb"))
