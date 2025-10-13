# This script is useful to cleanup the json files that have same bit flips that were observed across multi threads. It is better to use this against experiments where only
# one bank was targeted but multiple threads were deployed.
# !!! This is only useful if only one bank is targeted with multiple-threads !!!
#!/usr/bin/env python3
import json
from pathlib import Path


def extract_pairs_from_details(details):
    pairs = set()
    for d in details:
        ra = (d or {}).get("dram_addr", {})
        row = ra.get("row")
        col = ra.get("col")
        if row is not None and col is not None:
            pairs.add((row, col))
    return pairs

def iter_flips_and_details(doc):
    """Yield (flips_dict, details_list) for each sweep with flips.details."""
    for sweep in (doc.get("sweeps") or []):
        flips = sweep.get("flips") or {}
        details = flips.get("details")
        if isinstance(details, list):
            yield flips, details

runs = 10 # <- change this
for counter in range(1, runs + 1):
    INPUT_DIR = Path(f"../json/results/rep{counter}")   # <- change this
    OUTPUT_DIR = INPUT_DIR / "cleaned"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_flips = 0

    # 1) Load all files and collect per-file sets of (row, col)
    files = sorted([p for p in INPUT_DIR.glob("*.json") if p.is_file()])
    docs = []
    file_pairs = []  # union across all sweeps per file

    for p in files:
        with p.open("r", encoding="utf-8") as f:
            doc = json.load(f)
        docs.append(doc)

        union_pairs = set()
        for _, details in iter_flips_and_details(doc):
            union_pairs |= extract_pairs_from_details(details)
        file_pairs.append(union_pairs)

    # 2) Clean each file; update per-sweep totals; remove counters; update metadata.total_bitflips
    for idx, (p, doc) in enumerate(zip(files, docs)):
        # union of all (row,col) from other files
        others_union = set()
        for j, pairs in enumerate(file_pairs):
            if j != idx:
                others_union |= pairs

        removed_total = 0
        kept_total = 0
        total_bitflips = 0  # will become metadata["total_bitflips"]

        for flips, details in iter_flips_and_details(doc):
            before = len(details)
            details[:] = [
                d for d in details
                if not (
                    isinstance(d, dict)
                    and isinstance(d.get("dram_addr"), dict)
                    and (d["dram_addr"].get("row") is not None)
                    and (d["dram_addr"].get("col") is not None)
                    and ((d["dram_addr"]["row"], d["dram_addr"]["col"]) in others_union)
                )
            ]

            # Update per-sweep totals and remove counters
            flips["total"] = len(details)
            flips.pop("one_to_zero", None)
            flips.pop("zero_to_one", None)

            removed_total += (before - len(details))
            kept_total += len(details)
            total_bitflips += len(details)

        # Update metadata.total_bitflips (sum across all sweeps after cleaning)
        md = doc.get("metadata") or {}
        md["total_bitflips"] = total_bitflips
        doc["metadata"] = md

        out_path = OUTPUT_DIR / p.name
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
        all_flips += kept_total
        print(f"{p.name}: removed {removed_total}, kept {kept_total}, total_bitflips={total_bitflips}. -> {out_path}")

    sum_file = OUTPUT_DIR / "sum.json"
    var = {}
    var["sum"] = all_flips
    with sum_file.open("w", encoding="utf-8") as f:
        json.dump(var, f, indent=2, ensure_ascii=False)
        
    print(f"Done REP {counter}.")
    