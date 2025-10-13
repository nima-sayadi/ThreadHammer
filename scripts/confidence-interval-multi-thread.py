import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import matplotlib.ticker as ticker

bit_flip_counts = []

runs = 10 # <- change this
for count in range(1, runs + 1):
    file = Path(f'./16MiB-Multi-top4-patterns/rep{count}/sum.json') # <- change this
    with open(file) as f:
        data = json.load(f)
        bit_flip_counts.append(data['sum'])
        print(f"REP{count}: {data['sum']} bit flips")

# Convert to pandas DataFrame
df = pd.DataFrame({'Run': range(1, len(bit_flip_counts)+1),
                   'Bit Flips': bit_flip_counts})

# Calculate mean and 95% confidence interval
mean_flips = np.mean(bit_flip_counts)
sem_flips = stats.sem(bit_flip_counts)
confidence = 0.95
ci = stats.t.interval(confidence, len(bit_flip_counts)-1,
                      loc=mean_flips, scale=sem_flips)

# Plot
plt.figure(figsize=(8, 6))
plt.ylim(1000, 10000 + 1000)
plt.errorbar(df['Run'], df['Bit Flips'], fmt='o', label='Bit Flips per Run')
plt.axhline(mean_flips, color='red', linestyle='--', label=f'Mean: {mean_flips:.2f}')
plt.fill_between(df['Run'], ci[0], ci[1], color='blue', alpha=0.2, label=f'{int(confidence*100)}% CI')
plt.xlabel('Run Number')
plt.ylabel('Total Number of Bit Flips')
plt.title('Confidence Interval for Total Bit Flips Across Experiments')
plt.legend()
plt.tight_layout()
plt.savefig("plot.png")
