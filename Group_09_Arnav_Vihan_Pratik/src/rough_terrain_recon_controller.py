"""Course API exports; full M20 body, four articulated legs and wheeled feet.
E064 review: M20/scene.py, legged_control.py, hybrid_control.py
E070 review: M20/m20_rosbot_mapping.py
E073 review: M20/recon_controller.py and analytics/hazardous_recon_economics.py
These are review responsibilities, not evidence of student authorship.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'M20'))
from scene import TrialConfig,build_scene
from recon_controller import ReconExecutive,LatencyQueue
from m20_rosbot_mapping import M20Map,astar,plan_route
from simulation import run_trial,mission_acceptance
