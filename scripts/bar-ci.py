import matplotlib.pyplot as plt
import numpy as np

# Data (one system, three strategies)
strategies = ['Strategy 1', 'Strategy 2', 'Strategy 3']

# Means
single_mean = [22511.0, 3893.8, 1913.4]
multi_mean  = [22973.0, 2683.7, 1802.5]

# 95% CI half-widths = (upper - lower) / 2
single_ci = [
    (25259.751 - 19762.249) / 2,   # Strategy 1
    (4773.353  - 3014.247)  / 2,   # Strategy 2
    (2580.567  - 1246.233)  / 2    # Strategy 3
]
multi_ci = [
    (23645.116 - 22300.884) / 2,   # Strategy 1
    (2881.380  - 2486.020)  / 2,   # Strategy 2
    (2068.493  - 1536.507)  / 2    # Strategy 3
]

# Plot layout
x = np.arange(len(strategies)) * 1.2
width  = 0.28
offset = 0.15

fig, ax = plt.subplots(figsize=(8, 5))

# Colors
single_color = '#5975a4'
multi_color  = '#cc8963'

# Bars (single vs multi)
b1 = ax.bar(x - offset, single_mean, width, yerr=single_ci,
            color=single_color, capsize=4, label='Single-threaded',
            error_kw=dict(ecolor='black', lw=1.6))
b2 = ax.bar(x + offset, multi_mean, width, yerr=multi_ci,
            color=multi_color, capsize=4, label='Multi-threaded',
            error_kw=dict(ecolor='black', lw=1.6))

# Axes and grid
ax.set_ylabel('Bit-Flips')
ax.set_xticks(x)
ax.set_xticklabels(strategies)
ax.set_yticks(np.arange(0, 30001, 5000))
ax.set_ylim(0, 30000)
ax.grid(axis='y', linestyle='--', alpha=0.6)
ax.legend(loc='upper right', fontsize=9)

# Labels above each CI bar
def autolabel(bars, errors):
    pad = 0.01 * max(single_mean)
    for bar, err in zip(bars, errors):
        h = bar.get_height()
        y = h + err + pad
        txt = f'{h:.1f}' if h < 100 else f'{int(h)}'
        ax.text(bar.get_x() + bar.get_width()/2, y, txt,
                ha='center', va='bottom', fontsize=8)

autolabel(b1, single_ci)
autolabel(b2, multi_ci)

plt.tight_layout()
plt.savefig('bitflips_by_strategy.png', dpi=300, bbox_inches='tight')
plt.close()
