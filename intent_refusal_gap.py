import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.patches import FancyBboxPatch

fig_width_mm = 210 / 4
fig_width = fig_width_mm / 25.4
fig_height = fig_width * 2.2

fig = plt.figure(figsize=(fig_width, fig_height), dpi=300)
fig.patch.set_facecolor('white')

ax_w = 0.70
ax_l = 0.24
# Three charts, tightly packed
h_chart = 0.22
gap_ab = 0.04   # gap between IAF and IPS (within panel a)
gap_panels = 0.08  # gap between panel a and panel b

# Bottom-up layout
b3 = 0.07                          # ASR bottom
t3 = b3 + h_chart                  # ASR top

b_label_b = t3 + 0.02              # (b) label
b_border_b = t3 + 0.01

b2 = b_label_b + gap_panels        # IPS bottom
t2 = b2 + h_chart

sep_y = t2 + 0.025                 # separator line

b1 = sep_y + 0.025                 # IAF bottom
t1 = b1 + h_chart

a_label_y = t1 + 0.035             # (a) label
title_y = a_label_y + 0.05

ax1 = fig.add_axes([ax_l, b1, ax_w, h_chart])
ax2 = fig.add_axes([ax_l, b2, ax_w, h_chart])
ax3 = fig.add_axes([ax_l, b3, ax_w, h_chart])

gray = '#A0A0A0'
green = '#2E7D32'
x = np.arange(4)
bar_w = 0.30
fs = 2.5
fs_s = 3.0

groups = ['LLaVA-1.6 /\nSIUO', 'LLaVA-1.6 /\nMSSBench', 'Qwen2.5-VL /\nSIUO', 'Qwen2.5-VL /\nMSSBench']

configs = [
    {'ax': ax1, 'base': [41.2,22.2,57.5,21.5], 'plus': [48.8,49.3,65.0,55.5],
     'delta': ['+18.4%','+122.1%','+13.0%','+158.1%'], 'neg': [0,0,0,0],
     'yl': 100, 'yt': [0,20,40,60,80,100], 'ylabel': 'Frequency (%)',
     'title': '■ Intent Awareness Frequency (%)'},
    {'ax': ax2, 'base': [0.8,0.4,1.2,0.4], 'plus': [1.1,1.0,1.4,1.2],
     'delta': ['+37.5%','+150.0%','+16.7%','+200.0%'], 'neg': [0,0,0,0],
     'yl': 3.0, 'yt': [0.0,0.5,1.0,1.5,2.0,2.5,3.0], 'ylabel': 'IPS',
     'title': '■ Intent Perception Score (IPS)'},
    {'ax': ax3, 'base': [65.0,94.7,68.8,85.8], 'plus': [63.8,94.5,73.7,88.2],
     'delta': ['-1.8%','-0.2%','+7.1%','+2.8%'], 'neg': [1,1,0,0],
     'yl': 100, 'yt': [0,20,40,60,80,100], 'ylabel': 'Percent (%)',
     'title': None},
]

for c in configs:
    ax = c['ax']
    yl = c['yl']
    ax.bar(x-bar_w/2, c['base'], bar_w, color=gray, edgecolor='white', lw=0.2, zorder=3)
    ax.bar(x+bar_w/2, c['plus'], bar_w, color=green, edgecolor='white', lw=0.2, zorder=3)
    ax.set_ylim(0, yl)
    ax.set_yticks(c['yt'])
    ax.set_ylabel(c['ylabel'], fontsize=fs_s, fontweight='bold', labelpad=1)
    ax.set_xticks(x)
    ax.set_xticklabels(groups, fontsize=fs, linespacing=0.85)
    ax.tick_params(axis='y', labelsize=fs, pad=0.5, length=1)
    ax.tick_params(axis='x', length=0, pad=0.5)
    ax.set_xlim(-0.55, 3.55)
    ax.grid(axis='y', alpha=0.15, lw=0.2, zorder=0)
    ax.set_axisbelow(True)
    for s in ax.spines.values():
        s.set_linewidth(0.3)
    if c['title']:
        ax.set_title(c['title'], fontsize=fs_s, fontweight='bold', color='#1a237e', loc='left', pad=1.5)
    for i in range(4):
        bv, pv = c['base'][i], c['plus'][i]
        ax.text(x[i]-bar_w/2, bv+yl*0.01, f'{bv:.1f}', ha='center', va='bottom',
                fontsize=fs, fontweight='bold', color='#444')
        ax.text(x[i]+bar_w/2, pv+yl*0.01, f'{pv:.1f}', ha='center', va='bottom',
                fontsize=fs, fontweight='bold', color=green)
        top = max(bv, pv)
        is_neg = c['neg'][i]
        dc = '#E53935' if is_neg else '#4CAF50'
        dbg = '#FFEBEE' if is_neg else '#E8F5E9'
        ax.annotate(f'Δ {c["delta"][i]}', xy=(x[i], top+yl*0.08),
                    fontsize=fs-0.3, ha='center', va='bottom', color=dc, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.1', facecolor=dbg, edgecolor='none', alpha=0.8))

ax3.yaxis.label.set_color('#E53935')

for ax in [ax1, ax2, ax3]:
    for label in ax.get_xticklabels():
        txt = label.get_text()
        if 'SIUO' in txt and 'MSSBench' not in txt:
            label.set_color('#1565C0')
        elif 'MSSBench' in txt:
            label.set_color('#880E4F')

# Title
fig.text(0.06, title_y + 0.02, 'Intent-Refusal Gap', fontsize=5.5, fontweight='bold', va='top')
fig.text(0.06, title_y - 0.015, 'Intent perception improves, while ASR changes little.',
         fontsize=fs, va='top', color='#555', style='italic')

lp = [mpatches.Patch(facecolor=gray, label='Baseline'),
      mpatches.Patch(facecolor=green, label='+Intent Prompt')]
fig.legend(handles=lp, loc='upper right', fontsize=fs, frameon=True, fancybox=True,
           edgecolor='#ccc', bbox_to_anchor=(0.95, title_y + 0.02), ncol=1,
           handlelength=0.6, handleheight=0.5, labelspacing=0.2)

# (a) label
fig.text(0.06, a_label_y, '(a)', fontsize=fs_s+0.5, fontweight='bold', color='#1565C0',
         bbox=dict(boxstyle='round,pad=0.12', facecolor='#E3F2FD', edgecolor='#90CAF9', lw=0.4))
fig.text(0.20, a_label_y, 'Intent Perception', fontsize=fs_s+0.5, fontweight='bold', color='#1565C0')

# (b) label
fig.text(0.06, b_label_b + 0.01, '(b)', fontsize=fs_s+0.5, fontweight='bold', color='#E53935',
         bbox=dict(boxstyle='round,pad=0.12', facecolor='#FFEBEE', edgecolor='#EF9A9A', lw=0.4))
fig.text(0.20, b_label_b + 0.01, 'Attack Success Rate (ASR, %)', fontsize=fs_s+0.5, fontweight='bold', color='#E53935')

# Borders
a_top = a_label_y + 0.02
a_bot = b2 - 0.02
b_top = b_label_b + 0.035
b_bot = 0.02
for yt, yb, clr in [(a_top, a_bot, '#90CAF9'), (b_top, b_bot, '#EF9A9A')]:
    fig.add_artist(FancyBboxPatch((0.03, yb), 0.95, yt-yb, boxstyle='round,pad=0.005',
                                   transform=fig.transFigure, facecolor='none', edgecolor=clr,
                                   lw=0.4, clip_on=False, zorder=0))

# Separator line between IAF and IPS
fig.add_artist(plt.Line2D([0.06, 0.92], [sep_y, sep_y], transform=fig.transFigure,
                           color='#1565C0', lw=0.3))

out = '/home/user/cc/intent_refusal_gap'
fig.savefig(f'{out}.pdf', dpi=300, bbox_inches='tight', pad_inches=0.02)
fig.savefig(f'{out}.png', dpi=300, bbox_inches='tight', pad_inches=0.02)
print('Done')
