#!/usr/bin/env python3
"""
Evaluate each bank across N JSON runs (default: 7).
Each JSON file should look like:
{
  "0": {"channel": 0, "avg_timing": ...},
  "1": {"channel": 1, "avg_timing": ...},
  ...
  "31": {"channel": 0, "avg_timing": ...}
}

What this script does (per BANK):
- Collect the 0/1 labels from all runs.
- Majority label (ALL consensus), with tie handling.
- Count how many runs match the consensus (agreement_count and rate).
- Count zeros/ones, and compute label entropy.
- Leave-one-out stability: for each run, compare its label to the majority of the other runs.

It also makes basic Matplotlib plots:
- Heatmap: banks × runs labels (0/1).
- Bar: agreement rate per bank.
- Scatter: entropy vs agreement rate.

Usage:
  python Channel-Analyzer.py --pattern "ch-b-exp*.json" --outdir results
"""

import argparse
import glob
import json
import math
import os
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ----------------- helpers -----------------

def read_runs(pattern: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Read all JSONs matching 'pattern'.
    Returns:
      channels_df: [banks x runs] int {0,1}
      timings_df:  [banks x runs] float (NaN if missing)
    """
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files match pattern: {pattern}")

    channels = {}
    timings = {}

    for f in files:
        run = os.path.splitext(os.path.basename(f))[0]  # e.g., ch-b-exp1
        with open(f, "r") as fh:
            data = json.load(fh)
        for bank_str, rec in data.items():
            b = int(bank_str)
            ch = rec.get("channel", None)
            tm = rec.get("avg_timing", np.nan)
            if ch is None:
                raise ValueError(f"Missing 'channel' for bank {b} in {f}")
            channels.setdefault(b, {})[run] = int(ch)
            timings.setdefault(b, {})[run] = tm

    ch_df = pd.DataFrame.from_dict(channels, orient="index").sort_index()
    tm_df = pd.DataFrame.from_dict(timings, orient="index").sort_index()
    ch_df = ch_df.apply(pd.to_numeric, errors="coerce").astype("Int64")
    tm_df = tm_df.apply(pd.to_numeric, errors="coerce")
    return ch_df, tm_df


def majority_vote(vec: np.ndarray) -> Optional[int]:
    """Return majority in {0,1}; None for tie or empty."""
    v = vec[~np.isnan(vec)]
    if v.size == 0:
        return None
    zeros = np.sum(v == 0)
    ones  = np.sum(v == 1)
    if zeros > ones:
        return 0
    if ones > zeros:
        return 1
    return None


def shannon_entropy(vec: np.ndarray) -> float:
    """Entropy of binary labels in bits."""
    v = vec[~np.isnan(vec)]
    if v.size == 0:
        return float("nan")
    p1 = np.mean(v == 1)
    p0 = 1 - p1
    ent = 0.0
    for p in (p0, p1):
        if p > 0:
            ent -= p * math.log2(p)
    return ent


# ----------------- main eval per bank -----------------

def eval_per_bank(ch_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Build per-bank metrics and leave-one-out agreement matrix.
    Returns:
      bank_metrics: DataFrame with per-bank results
      loo_agree:   DataFrame [banks x runs] of 1/0/NaN (run matches majority of others?)
    """
    runs = list(ch_df.columns)
    banks = list(ch_df.index)

    # ALL consensus per bank
    all_cons = ch_df.apply(lambda row: majority_vote(row.to_numpy(dtype=float)), axis=1)

    # Agreement vs ALL (per bank, across runs)
    agree_matrix = pd.DataFrame(index=banks, columns=runs, dtype="float")
    for b in banks:
        c = all_cons.loc[b]
        if pd.isna(c):
            agree_matrix.loc[b, :] = np.nan
        else:
            agree_matrix.loc[b, :] = (ch_df.loc[b, :].astype(float).to_numpy() == float(c)).astype(float)

    agreement_count = agree_matrix.sum(axis=1, skipna=True)
    agreement_rate  = agreement_count / len(runs)

    # Counts and entropy
    zeros = (ch_df == 0).sum(axis=1)
    ones  = (ch_df == 1).sum(axis=1)
    entropy = ch_df.apply(lambda row: shannon_entropy(row.to_numpy(dtype=float)), axis=1)

    # Leave-one-out agreement per bank×run
    loo_agree = pd.DataFrame(index=banks, columns=runs, dtype="float")
    for r in runs:
        others = ch_df.drop(columns=[r])
        for b in banks:
            mv = majority_vote(others.loc[b, :].to_numpy(dtype=float))
            if mv is None or pd.isna(ch_df.loc[b, r]):
                loo_agree.loc[b, r] = np.nan
            else:
                loo_agree.loc[b, r] = float(ch_df.loc[b, r] == mv)

    tie_flag = all_cons.isna()

    bank_metrics = pd.DataFrame({
        "majority_label": all_cons,
        "agreement_count": agreement_count.astype("Int64"),
        "agreement_rate": agreement_rate,
        "zeros": zeros.astype("Int64"),
        "ones": ones.astype("Int64"),
        "entropy_bits": entropy,
        "tie_on_majority": tie_flag
    }).sort_index()

    return bank_metrics, loo_agree


def make_plots(outdir: str, ch_df: pd.DataFrame, bank_metrics: pd.DataFrame) -> None:
    os.makedirs(outdir, exist_ok=True)

    # Heatmap: labels per bank × run
    plt.figure()
    plt.imshow(ch_df.to_numpy(dtype=float), aspect="auto", interpolation="nearest")
    plt.xlabel("Runs")
    plt.ylabel("Banks")
    plt.title("Channel labels (0/1) per bank × run")
    plt.xticks(ticks=range(len(ch_df.columns)), labels=list(range(len(ch_df.columns))))
    plt.yticks(ticks=range(len(ch_df.index)), labels=ch_df.index.tolist())
    plt.colorbar()
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "heatmap_labels.png"))
    plt.close()

    # Bar: agreement rate per bank
    plt.figure()
    plt.bar(ch_df.index.astype(int), bank_metrics["agreement_rate"].to_numpy())
    plt.xlabel("Bank")
    plt.ylabel("Agreement rate across runs")
    plt.title("Per-bank agreement vs ALL")
    plt.ylim(0, 1)
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "bar_agreement_rate.png"))
    plt.close()

    # Scatter: entropy vs agreement rate
    plt.figure()
    x = bank_metrics["entropy_bits"].to_numpy()
    y = bank_metrics["agreement_rate"].to_numpy()
    plt.scatter(x, y)
    plt.xlabel("Entropy (bits)")
    plt.ylabel("Agreement rate")
    plt.title("Uncertainty vs agreement (per bank)")
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "scatter_entropy_vs_agreement.png"))
    plt.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", type=str, default="ch-b-exp*.json",
                    help="Glob for input files, e.g., 'ch-b-exp*.json'")
    ap.add_argument("--outdir", type=str, default="results",
                    help="Directory to save CSVs and plots")
    args = ap.parse_args()

    ch_df, tm_df = read_runs(args.pattern)

    # Core eval per bank
    bank_metrics, loo_agree = eval_per_bank(ch_df)

    # Save tables
    os.makedirs(args.outdir, exist_ok=True)
    ch_df.to_csv(os.path.join(args.outdir, "labels_bank_x_run.csv"))
    bank_metrics.to_csv(os.path.join(args.outdir, "bank_metrics.csv"))
    loo_agree.to_csv(os.path.join(args.outdir, "leave_one_out_agreement.csv"))

    # Plots
    make_plots(args.outdir, ch_df, bank_metrics)

    # Console summary: show most unstable banks first
    print("Files loaded:", len(ch_df.columns))
    print("Banks:", len(ch_df.index))
    print("\nWorst banks by agreement rate:")
    print(
        bank_metrics.sort_values("agreement_rate", ascending=True)
                    .head(10)[["majority_label","agreement_count","agreement_rate","zeros","ones","tie_on_majority"]]
    )


if __name__ == "__main__":
    main()
