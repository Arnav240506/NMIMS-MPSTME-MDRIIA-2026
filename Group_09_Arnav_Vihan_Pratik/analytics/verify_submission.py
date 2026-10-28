"""Verify the current group-only archive."""
from pathlib import Path
import argparse,json
from package_capstone import verify
if __name__ == "__main__":
    p=argparse.ArgumentParser();p.add_argument("--archive",type=Path,required=True)
    print(json.dumps(verify(p.parse_args().archive),indent=2))
