#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

def iter_rep_dirs(root: Path):
    # Only folders that look like rep1, rep2, ...
    for p in sorted(root.iterdir()):
        if p.is_dir() and p.name.startswith("rep") and p.name[3:].isdigit():
            yield p

def load_json(p: Path):
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Skipping {p}: {e}", file=sys.stderr)
        return None

def dump_json(p: Path, data):
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    tmp.replace(p)

def clean_details_within_file(details):
    """Remove duplicates within the same file by exact 'addr' match, keep first."""
    seen_in_file = set()
    cleaned = []
    changed = False
    for item in details:
        addr = item.get("addr")
        if addr is None:
            # Keep items without addr untouched
            cleaned.append(item)
            continue
        if addr in seen_in_file:
            changed = True
            continue
        seen_in_file.add(addr)
        cleaned.append(item)
    return cleaned, changed

def apply_cross_file_filter(details, seen_addrs_cross):
    """Drop any item whose addr has already been kept in prior files of the same folder."""
    filtered = []
    changed = False
    for item in details:
        addr = item.get("addr")
        if addr is None:
            filtered.append(item)
            continue
        if addr in seen_addrs_cross:
            changed = True
            continue
        filtered.append(item)
        seen_addrs_cross.add(addr)
    return filtered, changed

def fix_counts_and_fields(doc):
    """Drop one_to_zero/zero_to_one, recompute flips.total and metadata.total_bitflips."""
    sweeps = doc.get("sweeps")
    if not isinstance(sweeps, list):
        return False
    changed = False
    total_bitflips = 0
    for sweep in sweeps:
        flips = sweep.get("flips")
        if not isinstance(flips, dict):
            continue
        # Remove counters we no longer keep
        if "one_to_zero" in flips:
            flips.pop("one_to_zero", None)
            changed = True
        if "zero_to_one" in flips:
            flips.pop("zero_to_one", None)
            changed = True
        details = flips.get("details")
        if isinstance(details, list):
            new_total = len(details)
            if flips.get("total") != new_total:
                flips["total"] = new_total
                changed = True
            total_bitflips += new_total
    # Update metadata.total_bitflips
    md = doc.get("metadata")
    if isinstance(md, dict):
        if md.get("total_bitflips") != total_bitflips:
            md["total_bitflips"] = total_bitflips
            changed = True
    return changed

def process_file_for_folder_cross_dedup(path: Path, seen_addrs_cross: set):
    data = load_json(path)
    if data is None:
        return False, 0, 0

    changed_any = False
    kept_before = sum(
        len(s.get("flips", {}).get("details", []))
        for s in data.get("sweeps", []) if isinstance(s, dict)
    )

    # Work on each sweep.details
    sweeps = data.get("sweeps")
    if isinstance(sweeps, list):
        new_sweeps = []
        for sweep in sweeps:
            if not isinstance(sweep, dict):
                new_sweeps.append(sweep)
                continue
            flips = sweep.get("flips")
            if not isinstance(flips, dict):
                new_sweeps.append(sweep)
                continue
            details = flips.get("details")
            if not isinstance(details, list):
                new_sweeps.append(sweep)
                continue

            # 1) Dedup within the same file by addr
            details, changed1 = clean_details_within_file(details)
            # 2) Drop items already kept in prior files of the same folder
            details, changed2 = apply_cross_file_filter(details, seen_addrs_cross)

            if changed1 or changed2:
                flips["details"] = details
                changed_any = True

            new_sweeps.append(sweep)
        data["sweeps"] = new_sweeps

    # 3) Drop fields and fix totals
    if fix_counts_and_fields(data):
        changed_any = True

    kept_after = sum(
        len(s.get("flips", {}).get("details", []))
        for s in data.get("sweeps", []) if isinstance(s, dict)
    )

    if changed_any:
        return data, kept_before, kept_after
    else:
        return False, kept_before, kept_after  # no changes

def process_folder(rep_dir: Path, dry_run: bool):
    print(f"\n[DIR] {rep_dir}")
    json_files = sorted([p for p in rep_dir.iterdir() if p.is_file() and p.suffix.lower() == ".json"])
    seen_addrs_cross = set()
    total_removed = 0
    for jf in json_files:
        result, before, after = process_file_for_folder_cross_dedup(jf, seen_addrs_cross)
        removed = before - after
        total_removed += max(0, removed)
        if result is False:
            # no changes
            print(f"  = {jf.name}: kept {after} (no change)")
        else:
            if not dry_run:
                dump_json(jf, result)
            print(f"  * {jf.name}: kept {after}, removed {removed}")
    print(f"[SUM] Removed {total_removed} duplicate entries in {rep_dir.name}")

def main():
    ap = argparse.ArgumentParser(description="Clean bitflip JSON files: dedup within file and across files in each rep* folder.")
    ap.add_argument("root", nargs="?", default=".", help="Root directory (default: current dir)")
    ap.add_argument("--dry-run", action="store_true", help="Analyze only, do not write files")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"Root not found: {root}", file=sys.stderr)
        sys.exit(1)

    any_dir = False
    for rep_dir in iter_rep_dirs(root):
        any_dir = True
        process_folder(rep_dir, args.dry_run)

    if not any_dir:
        print("No rep* folders found.", file=sys.stderr)

if __name__ == "__main__":
    main()
