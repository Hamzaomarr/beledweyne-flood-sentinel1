"""Workflow diagram for the Methods (describes the method only, no results). Greyscale, straight arrows only."""
import os, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
FIG = r'.\outputs\figures'
fig, ax = plt.subplots(figsize=(8.4, 6.8)); ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')
def box(x, y, w, h, t, fc='#ffffff', fs=8.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.3,rounding_size=1.2', fc=fc, ec='#333333', lw=1)); ax.text(x + w / 2, y + h / 2, t, ha='center', va='center', fontsize=fs)
def arrow(x1, y1, x2, y2): ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='-|>', color='#333333', lw=1))
G = '#eeeeee'; C = [12, 37, 62, 87]; W = 22
# row 1, inputs
for c, t in zip(C, ['Sentinel-2 composite\nand consensus\nland-cover labels', 'Sentinel-1\nVV and VH\nsix dates', 'UNOSAT optical\nflood mapping', 'Surface water,\nHAND and\nelevation data']):
    box(c - W / 2, 83, W, 14, t, G)
# row 2, processing
for c, t in zip(C, ['Random Forest\nland-cover map', 'Backscatter change,\nthreshold rule and\ncluster filter', 'Calibration on the\nPléiades mapping\nof 12 November', 'Permanent water,\nHAND and slope\nmasks']):
    box(c - W / 2, 62, W, 14, t)
    arrow(c, 83, c, 76.6)
arrow(C[2] - W / 2, 69, C[1] + W / 2 + 0.6, 69)
# row 3, flood extent
box(26, 41, 72, 12, 'Flagged flood extent for four post-event dates')
arrow(C[1], 62, C[1], 53.6); arrow(C[3], 62, C[3], 53.6)
# row 4
for c, t in zip(C[1:], ['Intensity and\npersistence classes', 'Accuracy assessment\non independent\nreference dates', 'Sensitivity analyses']):
    box(c - W / 2, 20, W, 14, t); arrow(c, 41, c, 34.6)
# row 5
box(1, 2, 60, 11, 'Flagged area by land-cover class'); arrow(C[0], 62, C[0], 13.6); arrow(C[1], 20, C[1], 13.6)
fig.savefig(os.path.join(FIG, 'fig_methods_workflow.png'), dpi=300, bbox_inches='tight'); print('saved')
