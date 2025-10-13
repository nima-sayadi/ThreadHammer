#!/usr/bin/env python3
"""

Expect JSON of the form:
[
  { "mode": "single_thread", "bitflips": [12,15,10,14,11,13] },
  { "mode": "multi_thread",  "bitflips": [30,28,32,29,31,27] }
]

Usage:
    python precise-analyzer data.json [modeA modeB]
If mode names are provided, those two are compared; otherwise the first two entries are used.
"""
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

def mean_ci(x, conf=0.95):
    x = np.asarray(x, dtype=float)
    n = len(x)
    mean = x.mean()
    if n > 1:
        s = x.std(ddof=1)
        t = stats.t.ppf(1 - (1-conf)/2, df=n-1)
        se = s / np.sqrt(n)
        lo = mean - t*se
        hi = mean + t*se
    else:
        s = 0.0
        lo = hi = mean
    return mean, lo, hi, s, n

def variance_ci(x, conf=0.95):
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n < 2:
        return np.nan, np.nan, np.nan
    var = x.var(ddof=1)
    alpha = 1 - conf
    chi2_lo = stats.chi2.ppf(alpha/2, df=n-1)
    chi2_hi = stats.chi2.ppf(1 - alpha/2, df=n-1)
    lo = (n-1)*var / chi2_hi
    hi = (n-1)*var / chi2_lo
    return var, lo, hi

def bootstrap_var_ratio(a, b, nboot=5000, seed=0, conf=0.95):
    rng = np.random.RandomState(seed)
    ratios = []
    a = np.asarray(a)
    b = np.asarray(b)
    for _ in range(nboot):
        ra = rng.choice(a, size=len(a), replace=True)
        rb = rng.choice(b, size=len(b), replace=True)
        va = ra.var(ddof=1)
        vb = rb.var(ddof=1)
        ratios.append(vb / va if va > 0 else np.inf)
    arr = np.array(ratios)
    lo, hi = np.percentile(arr, [100*(1-conf)/2, 100*(1-(1-conf)/2)])
    return arr, lo, hi

def load_json(path):
    with open(path, 'r') as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise SystemExit("JSON must be a top-level list of mode objects.")
    parsed = {}
    for obj in data:
        if 'mode' not in obj or 'bitflips' not in obj:
            raise SystemExit("Each object must have 'mode' and 'bitflips' fields.")
        parsed[obj['mode']] = list(obj['bitflips'])
    return parsed

def main(path, strat_a=None, strat_b=None):
    groups = load_json(path)
    keys = list(groups.keys())
    if len(keys) < 2:
        raise SystemExit("Need at least two strategies in the JSON.")
    if strat_a and strat_b:
        if strat_a not in groups or strat_b not in groups:
            raise SystemExit(f"Requested strategies not found. Available: {keys}")
        a_key, b_key = strat_a, strat_b
    else:
        a_key, b_key = keys[0], keys[1]

    a = np.asarray(groups[a_key], dtype=float)
    b = np.asarray(groups[b_key], dtype=float)

    mean_a, lo_a, hi_a, s_a, n_a = mean_ci(a)
    mean_b, lo_b, hi_b, s_b, n_b = mean_ci(b)
    var_a, var_lo_a, var_hi_a = variance_ci(a)
    var_b, var_lo_b, var_hi_b = variance_ci(b)

    print(f"Mode '{a_key}': n={n_a}, mean={mean_a:.3f}, 95% CI=[{lo_a:.3f}, {hi_a:.3f}], var={var_a:.3f}, 95% CI=[{var_lo_a:.3f}, {var_hi_a:.3f}]")
    print(f"Mode '{b_key}': n={n_b}, mean={mean_b:.3f}, 95% CI=[{lo_b:.3f}, {hi_b:.3f}], var={var_b:.3f}, 95% CI=[{var_lo_b:.3f}, {var_hi_b:.3f}]")

    # Levene test for difference in variance (robust)
    lev_stat, lev_p = stats.levene(a, b, center='median')
    print(f"\nLevene test (median center): stat={lev_stat:.3f}, p={lev_p:.4f}")
    if lev_p < 0.05:
        print("=> Variances differ significantly (p < 0.05).")
    else:
        print("=> No significant variance difference (p >= 0.05).")

    # variance ratio and bootstrap CI (b / a)
    ratio = var_b / var_a if var_a > 0 else np.inf
    reduction_pct = (1 - ratio) * 100
    boot_arr, boot_lo, boot_hi = bootstrap_var_ratio(a, b, nboot=5000)
    print(f"\nVariance ratio ({b_key}/{a_key}) = {ratio:.3f}")
    print(f"Relative reduction = {reduction_pct:.1f}% (positive => reduction)")
    print(f"Bootstrap 95% CI for variance ratio = [{boot_lo:.3f}, {boot_hi:.3f}]")

    # mean CI plot
    order = [a_key, b_key]
    means = [mean_a, mean_b]
    lo_err = [mean_a - lo_a, mean_b - lo_b]
    hi_err = [hi_a - mean_a, hi_b - mean_b]
    fig, ax = plt.subplots(figsize=(6,4))
    ax.errorbar(range(2), means, yerr=[lo_err, hi_err], fmt='o', capsize=6)
    ax.set_xticks(range(2))
    ax.set_xticklabels(order)
    ax.set_ylabel('Bit flips per run')
    ax.set_title('Mean bit flips with 95% CI')
    for i,k in enumerate(order):
        ax.text(i, means[i], f" n={len(groups[k])}", va='bottom', ha='center', fontsize=8)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('ci_plot.png', dpi=200)
    print("\nPlot saved to ci_plot.png")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python precise-analyzer.py data.json [modeA modeB]")
        sys.exit(1)
    path = sys.argv[1]
    modeA = sys.argv[2] if len(sys.argv) > 2 else None
    modeB = sys.argv[3] if len(sys.argv) > 3 else None
    main(path, modeA, modeB)
