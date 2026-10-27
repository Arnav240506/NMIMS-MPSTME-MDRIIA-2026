from pathlib import Path
import sys
GROUP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(GROUP/'M20'))
sys.path.insert(0,str(GROUP/'analytics'))
