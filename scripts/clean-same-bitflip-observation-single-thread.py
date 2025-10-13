#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

def load_json(p: Path):
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Skipping {p}: {e}", file=sys.stderr)
        return None

def write_json(p: Path, data):
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    tmp.replace(p)

def clean_file_across_sweeps(doc: dict):
    """
    Remove duplicate 'addr' across the whole file (all sweeps).
    Keep the first occurrence; drop later ones.
    Update flips.total only.
    Return (changed: bool, file_total: int)
    """
    sweeps = doc.get("sweeps")
    if not isinstance(sweeps, list):
        return False, 0

    seen = set()
    changed = False
    file_total = 0

    for sweep in sweeps:
        flips = sweep.get("flips")
        if not isinstance(flips, dict):
            continue
        details = flips.get("details")
        if not isinstance(details, list):
            # still ensure total reflects what's there
            cur_total = len(details) if isinstance(details, list) else 0
            if flips.get("total") != cur_total:
                flips["total"] = cur_total
                changed = True
            file_total += flips.get("total", 0)
            continue

        new_details = []
        # remove dups within this sweep and across previous sweeps
        local_seen = set()
        for item in details:
            addr = item.get("addr")
            if addr is None:
                # keep items without addr
                if id(item) not in local_seen:
                    new_details.append(item)
                continue
            if addr in local_seen or addr in seen:
                changed = True
                continue
            local_seen.add(addr)
            seen.add(addr)
            new_details.append(item)

        if new_details is not details:
            flips["details"] = new_details

        new_total = len(new_details)
        if flips.get("total") != new_total:
            flips["total"] = new_total
            changed = True

        file_total += new_total

    return changed, file_total

def main():
    ap = argparse.ArgumentParser(
        description="Dedup 'addr' across all sweeps per JSON file, update flips.total only, and write sum.json."
    )
    ap.add_argument("path", help="Folder containing JSON files")
    ap.add_argument("--dry-run", action="store_true", help="Analyze only; do not write changes")
    args = ap.parse_args()

    folder = Path(args.path).resolve()
    if not folder.exists() or not folder.is_dir():
        print(f"Path not found or not a directory: {folder}", file=sys.stderr)
        sys.exit(1)

    json_files = sorted(p for p in folder.glob("*.json") if p.name != "sum.json")
    if not json_files:
        print("No JSON files found.", file=sys.stderr)
        sys.exit(1)

    per_file_totals = []
    for jf in json_files:
        doc = load_json(jf)
        if doc is None:
            continue
        changed, file_total = clean_file_across_sweeps(doc)
        per_file_totals.append(file_total)
        if changed and not args.dry_run:
            write_json(jf, doc)
        print(f"{jf.name}: {'updated' if changed else 'no change'} | sum={file_total}")

    # Write sum.json (simple array of numbers, one per file in the same order)
    sum_path = folder / "sum.json"
    if not args.dry_run:
        with sum_path.open("w", encoding="utf-8") as f:
            json.dump(per_file_totals, f, indent=2)
            f.write("\n")
    print(f"Wrote {'(dry-run) ' if args.dry_run else ''}sum.json with {len(per_file_totals)} totals")

if __name__ == "__main__":
    main()
