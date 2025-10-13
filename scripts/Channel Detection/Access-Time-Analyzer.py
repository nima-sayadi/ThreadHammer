#!/usr/bin/env python3
"""
Plot histogram(s) of avg_timing values from ch-b-exp*.json files.

- Uses a fixed bin width (default 20) for precise X-axis steps.
- Sets X-axis ticks to the same step as bin width.
- Rotates X-axis tick labels vertically (90°) for clarity.
"""

import argparse
import glob
import json
import os
from math import floor, ceil

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def load_timings(pattern: str) -> pd.DataFrame:
    """Load avg_timing values into a DataFrame [banks x runs]."""
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files match pattern: {pattern}")

    timings = {}
    for f in files:
        run = os.path.splitext(os.path.basename(f))[0]
        with open(f, "r") as fh:
            data = json.load(fh)
        for bank_str, rec in data.items():
            bank = int(bank_str)
            timings.setdefault(bank, {})[run] = rec.get("avg_timing", None)

    df = pd.DataFrame.from_dict(timings, orient="index").sort_index()
    df = df.apply(pd.to_numeric, errors="coerce")
    return df


def bin_edges(values: np.ndarray, bin_width: float) -> np.ndarray:
    """Build clean bin edges aligned to bin_width."""
    vmin = float(np.nanmin(values))
    vmax = float(np.nanmax(values))
    start = bin_width * floor(vmin / bin_width)
    end = bin_width * ceil(vmax / bin_width)
    eps = max(1e-9, (end - start) * 1e-9)
    return np.arange(start, end + bin_width + eps, bin_width)


def plot_hist(data: np.ndarray, bins: np.ndarray, title: str,
              outpath: str, figsize: tuple, dpi: int, bin_width: float) -> None:
    plt.figure(figsize=figsize)
    plt.hist(data, bins=bins, edgecolor="black")
    plt.xlabel("Access time (avg_timing)")
    plt.ylabel("Count")
    plt.title(f"{title} (bin width={bin_width})")

    ax = plt.gca()
    ax.xaxis.set_major_locator(ticker.MultipleLocator(base=bin_width))
    for label in ax.get_xticklabels():
        label.set_rotation(90)  # vertical ticks
        label.set_ha("center")

    plt.tight_layout()
    plt.savefig(outpath, dpi=dpi)
    plt.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", type=str, default="ch-b-exp*.json",
                    help="Glob for input files, e.g. 'ch-b-exp*.json'")
    ap.add_argument("--outdir", type=str, default="timing_plots",
                    help="Output directory")
    ap.add_argument("--bin-width", type=float, default=20.0,
                    help="Fixed bin width for histograms (same units as avg_timing)")
    ap.add_argument("--figsize", type=float, nargs=2, default=(8.0, 5.0),
                    help="Figure size: WIDTH HEIGHT (inches)")
    ap.add_argument("--dpi", type=int, default=300,
                    help="Image DPI")
    args = ap.parse_args()

    tm_df = load_timings(args.pattern)
    os.makedirs(args.outdir, exist_ok=True)

    # Combined histogram
    all_vals = tm_df.to_numpy().ravel()
    all_vals = all_vals[~np.isnan(all_vals)]
    if all_vals.size == 0:
        raise ValueError("No avg_timing values found.")

    bins_all = bin_edges(all_vals, args.bin_width)
    plot_hist(all_vals, bins_all, "Histogram of access times (all runs)",
              os.path.join(args.outdir, "hist_access_times_all.png"),
              tuple(args.figsize), args.dpi, args.bin_width)

    # Per-run histograms
    for run in tm_df.columns:
        vals = tm_df[run].dropna().to_numpy()
        if vals.size == 0:
            continue
        bins_run = bin_edges(vals, args.bin_width)
        plot_hist(vals, bins_run, f"Histogram of access times: {run}",
                  os.path.join(args.outdir, f"hist_access_times_{run}.png"),
                  tuple(args.figsize), args.dpi, args.bin_width)

    print(f"Saved histograms to {args.outdir} with bin_width={args.bin_width}, dpi={args.dpi}.")


if __name__ == "__main__":
    main()
