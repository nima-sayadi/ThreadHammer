import json
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import matplotlib.ticker as ticker
from pathlib import Path

file_paths = glob.glob('./*.json')
# skip sum.json
file_paths = [p for p in file_paths if Path(p).name != 'sum.json']

bit_flip_counts = []

# Loop through all JSON files and count total bit flips in each
for file in file_paths:
    with open(file) as f:
        data = json.load(f)

        total_bit_flips = 0
        for sweep in data['sweeps']:
            total_bit_flips += sweep['flips']['total']

        bit_flip_counts.append(total_bit_flips)
        print(f"{file}: {total_bit_flips} bit flips")

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
plt.ylim(1000, 7000 + 1000)
plt.errorbar(df['Run'], df['Bit Flips'], fmt='o', label='Bit Flips per Run')
plt.axhline(mean_flips, color='red', linestyle='--', label=f'Mean: {mean_flips:.2f}')
plt.fill_between(df['Run'], ci[0], ci[1], color='blue', alpha=0.2, label=f'{int(confidence*100)}% CI')
plt.xlabel('Run Number')
plt.ylabel('Total Number of Bit Flips')
plt.title('Confidence Interval for Total Bit Flips Across Experiments')
plt.legend()
plt.tight_layout()
plt.savefig("plot.png")
