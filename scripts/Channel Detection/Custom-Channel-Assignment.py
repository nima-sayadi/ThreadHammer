# Basically assigns all json files in current directory a fixed threshold and updates the channel information for each bank

#!/usr/bin/env python3
import json
import glob
from pathlib import Path
import argparse

THRESHOLD = 650  # default threshold

def process_file(path: Path, thresh: int) -> None:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Skip {path.name}: failed to read JSON ({e})")
        return

    if not isinstance(data, dict):
        print(f"Skip {path.name}: top-level JSON is not an object")
        return

    for key, obj in data.items():
        if isinstance(obj, dict):
            avg = obj.get("avg_timing", 0)
            try:
                val = int(avg)
            except (TypeError, ValueError):
                val = 0
            obj["channel"] = 1 if val >= thresh else 0

    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        print(f"Updated {path.name}")
    except Exception as e:
        print(f"Failed to write {path.name}: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Update JSON files with channel info based on threshold."
    )
    parser.add_argument(
        "-t", "--threshold", type=int, default=THRESHOLD,
        help=f"Threshold value (default: {THRESHOLD})"
    )
    parser.add_argument(
        "files", nargs="*", default=glob.glob("*.json"),
        help="JSON files to process (default: all *.json in current dir)"
    )

    args = parser.parse_args()

    if not args.files:
        print("No JSON files found.")
        return

    for p in [Path(f) for f in args.files]:
        process_file(p, args.threshold)

if __name__ == "__main__":
    main()
