#!/usr/bin/env python3
import json
from pathlib import Path

def iter_details(doc):
    """Yield each flips.details list in the doc."""
    for sweep in (doc.get("sweeps") or []):
        flips = sweep.get("flips") or {}
        details = flips.get("details")
        if isinstance(details, list):
            yield details

runs = 10  # <- change this
for counter in range(1, runs + 1):
    INPUT_DIR = Path(f"./16MiB-Multi-top4-patterns/rep{counter}")  # <- change this
    total_bitflips = 0

    files = sorted(p for p in INPUT_DIR.glob("*.json")
                   if p.is_file() and p.name != "sum.json")

    for p in files:
        try:
            with p.open("r", encoding="utf-8") as f:
                doc = json.load(f)
        except Exception as e:
            print(f"Skip {p.name}: {e}")
            continue

        for details in iter_details(doc):
            total_bitflips += len(details)

    # Save only the total
    sum_file = INPUT_DIR / "sum.json"
    with sum_file.open("w", encoding="utf-8") as f:
        json.dump({"sum": total_bitflips}, f, indent=2, ensure_ascii=False)

    print(f"REP {counter}: total_bitflips={total_bitflips} -> {sum_file}")
