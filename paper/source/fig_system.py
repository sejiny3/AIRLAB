"""Fig: the task pipeline, where only the pick step differs between the three modes."""
import matplotlib
matplotlib.use('Agg')
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import matplotlib.pyplot as plt

plt.rcParams.update({'font.family': 'Times New Roman', 'font.size': 8})
INK, MUTED, SHARED = '#1b1b1a', '#6b6a64', '#f0efec'
fig, ax = plt.subplots(figsize=(3.15, 3.15))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')


def box(x, y, w, h, text, fill=SHARED, edge=MUTED, weight='normal'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=1.5', fc=fill, ec=edge, lw=0.7))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', color=INK, fontweight=weight, linespacing=1.15)


def arrow(p, q):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle='-|>', mutation_scale=7, lw=0.7, color=INK, shrinkA=0, shrinkB=0))


box(14, 90, 72, 8, 'Task planner (LLM or scripted plan)')
box(14, 76, 72, 8, 'Navigation to the table (Nav2)')
box(14, 62, 72, 8, 'Line-up on the box marker (ArUco servo)')
arrow((50, 90), (50, 84))
arrow((50, 76), (50, 70))

ax.add_patch(FancyBboxPatch((1, 15), 98, 41, boxstyle='round,pad=0,rounding_size=1.5', fc='white', ec=INK, lw=0.9,
                            linestyle=(0, (4, 3))))
ax.text(50, 52.5, 'Pick step: the only part that differs', ha='center', va='center', color=INK, fontweight='bold')
cols = [(3, 'IK mode', 'Marker pose\n+ IK and motion\nplanning\n(MoveIt)', 'Laptop CPU', '#cde2fb'),
        (35, 'CNN policy', 'Two images, text,\njoint angles → joint\ntargets, 10 Hz', 'Laptop CPU', '#cde2fb'),
        (67, 'π0.5 policy', 'Two images, text,\njoint angles → joint\ntargets, 5 steps\nper reply', 'Remote GPU\n(tunnel)', '#fbdccd')]
for x, name, body, where, fill in cols:
    box(x, 33, 30, 16, body, fill='white')
    ax.text(x + 15, 29.5, name, ha='center', va='center', color=INK, fontweight='bold')
    box(x + 3, 18, 24, 8.5, where, fill=fill, edge=MUTED)

box(14, 2, 72, 8, 'Place on the table spot (MoveIt)')
arrow((50, 62), (50, 56))
arrow((50, 15), (50, 10))
fig.subplots_adjust(0, 0, 1, 1)
fig.savefig('fig_system.png', dpi=300)
print('saved')
