import json
import argparse
from pathlib import Path
import sys

def check_holds(wall_dir: Path):
    config_path = wall_dir / "config.json"
    holds_path = wall_dir / "output/data/holds.json"

    if not config_path.exists():
        print(f"⚠️  Warning: Config file not found for wall '{wall_dir.name}'. Skipping check.", file=sys.stderr)
        return

    if not holds_path.exists():
        print(f"⚠️  Warning: Holds data file not found for wall '{wall_dir.name}'. Skipping check.", file=sys.stderr)
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    with open(holds_path, 'r', encoding='utf-8') as f:
        detected_holds = json.load(f).keys()

    wall_name = config.get("wall_name", wall_dir.name)
    valid_ranges = config.get("valid_hold_ranges", [])
    
    if not valid_ranges:
        print(f"ℹ️  Info: No 'valid_hold_ranges' defined for wall '{wall_name}'. Skipping check.")
        return

    print(f"\n--- Checking Missing Holds for Wall: {wall_name} ---")

    expected_holds = set()
    for start, end in valid_ranges:
        for i in range(start, end + 1):
            expected_holds.add(str(i))
            
    detected_set = set(str(h) for h in detected_holds)
    missing_holds = sorted(list(expected_holds - detected_set), key=int)

    if not missing_holds:
        print("✅  Success! All expected holds were detected.")
    else:
        print(f"🚨  Error: Found {len(missing_holds)} missing holds!")
        print("Missing hold numbers:", ", ".join(map(str, missing_holds)))
        # To fail the CI job, uncomment the next line
        # sys.exit(1)

    print("-" * (38 + len(wall_name)))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Check for missing holds for one or more climbing walls.")
    parser.add_argument(
        "wall_dirs",
        nargs='*',
        default=[],
        help="Specific wall directories to check (e.g., walls/spray_wall). If empty, checks all directories inside 'walls/'."
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]
    walls_root = project_root / "walls"

    if args.wall_dirs:
        target_dirs = [project_root / d for d in args.wall_dirs]
    else:
        target_dirs = [d for d in walls_root.iterdir() if d.is_dir()]

    if not target_dirs:
        print("No wall directories found to check.", file=sys.stderr)
        sys.exit(0)
        
    print(f"Found {len(target_dirs)} wall(s) to process.")
    for wall_dir in target_dirs:
        check_holds(wall_dir)
