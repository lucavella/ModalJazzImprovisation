import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib import rc


rc('font', family='serif', serif=['Computer Modern'])
rc('text', usetex=True)


# https://forms.gle/NNdGyETiM2gzZQcB7
# https://docs.google.com/spreadsheets/d/15ac17V6DOB5uSdNbDxg8PEZ9yecQAq6b0iRMo7s-ZXQ

results_df = pd.read_csv('./data/results.csv')

enjoy_res = results_df['Do you enjoy jazz music in general?'].eq('Yes').mul(1)
expertise_res = results_df['What is your level of expertise in jazz?']
so_what_res = results_df.iloc[:, 3:8]
little_sunflower_res = results_df.iloc[:, 8:13]


print(f'Jazz enjoyers: mean {np.mean(enjoy_res):.2f}')
print(f'Jazz expertise: mean {np.mean(expertise_res):.2f}, std {np.std(expertise_res):.2f}')


categories = ['Novelty', 'Value', 'Global structure', 'Harmony', 'Rhythm']

so_what_mean = np.mean(so_what_res, axis=0)
so_what_std = np.std(so_what_res, axis=0)
little_sunflower_mean = np.mean(little_sunflower_res, axis=0)
little_sunflower_std = np.std(little_sunflower_res, axis=0)


bar_width = 0.25
x = np.arange(len(categories)) / 1.5
fig, ax = plt.subplots(figsize=(4, 4))

ax.bar(x, so_what_mean, bar_width, label='So What', color=[(0.66, 0.66, 0.66)])
ax.errorbar(x, so_what_mean, so_what_std, fmt='.', capsize=3, color='k')
ax.bar(x + bar_width, little_sunflower_mean, bar_width, label='Little Sunflower', color=[(0.33, 0.33, 0.33)])
ax.errorbar(x + bar_width, little_sunflower_mean, so_what_std, fmt='.', capsize=3, color='k')

ax.set_ylabel('Quality', fontsize=12)
ax.set_xticks(x + bar_width / 2, categories, rotation=60, fontsize=12)
ax.legend(loc='lower right', ncols=2, fontsize=12)
ax.set_ylim(1, 5)
ax.yaxis.set_major_locator(MaxNLocator(integer=True))
fig.tight_layout()
fig.savefig(f'./imgs/results2.svg', format='svg', dpi=600)