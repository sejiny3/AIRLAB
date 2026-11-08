"""Fig: steps per pick on the same 100 setups, one panel per policy, sharing the x axis."""
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({'font.family': 'Times New Roman', 'font.size': 9, 'axes.linewidth': 0.6})
steps = json.load(open('steps.json'))
INK, MUTED, GRID = '#1b1b1a', '#6b6a64', '#d9d8d3'
SERIES = [('CNN policy', steps['cnn'], '#2a78d6'), ('π0.5 policy', steps['pi05'], '#eb6834')]
bins = np.arange(65.5, 92.5, 2)

fig, axes = plt.subplots(2, 1, figsize=(3.15, 2.5), sharex=True, sharey=True)
for ax, (name, x, color) in zip(axes, SERIES):
    ax.hist(x, bins=bins, color=color, edgecolor='white', linewidth=1.0, zorder=3)
    ax.axvline(77, color=INK, linewidth=0.9, linestyle=(0, (4, 3)), zorder=4)
    ax.grid(axis='y', color=GRID, linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    for side in ('top', 'right', 'left'):
        ax.spines[side].set_visible(False)
    ax.spines['bottom'].set_color(MUTED)
    ax.tick_params(colors=INK, length=2.5, width=0.5, left=False)
    ax.set_ylabel('Episodes', color=INK)
    ax.text(0.985, 0.90, f'{name}\nmean {np.mean(x):.1f}, SD {np.std(x, ddof=1):.1f}', transform=ax.transAxes,
            ha='right', va='top', color=INK)
axes[0].text(77.5, axes[0].get_ylim()[1] * 0.99, 'Expert: 77', ha='left', va='top', color=INK)
axes[1].set_xlabel('Control steps until done (0.1 s per step)', color=INK)
axes[1].set_xlim(65, 92)
fig.tight_layout(pad=0.4, h_pad=0.6)
fig.savefig('fig_steps.png', dpi=300)
print('saved')
