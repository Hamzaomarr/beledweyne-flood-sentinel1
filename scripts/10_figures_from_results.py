"""
Figures 1-6 drawn ONLY from the saved result tables in outputs/tables (nothing typed in by hand except labels).
Palette: Okabe-Ito colour-blind-safe hues, one fixed colour per land-cover class across all figures.
"""
import os, json, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = r'.'
T = os.path.join(BASE, 'outputs', 'tables'); FIG = os.path.join(BASE, 'outputs', 'figures'); os.makedirs(FIG, exist_ok=True)
INK, MUTED, GRID = '#222222', '#6b6b6b', '#dddddd'
CLS = {'Cropland': '#E69F00', 'Vegetation / rangeland': '#009E73', 'Built-up': '#CC79A7', 'Bare soil / sand': '#8c8c8c'}
BLUE, VERM, SKY = '#0072B2', '#D55E00', '#56B4E9'
plt.rcParams.update({'font.size': 10, 'axes.edgecolor': MUTED, 'axes.labelcolor': INK, 'text.color': INK, 'xtick.color': INK, 'ytick.color': INK,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.6,
                     'axes.axisbelow': True, 'figure.dpi': 100, 'savefig.dpi': 300, 'figure.facecolor': 'white', 'axes.facecolor': 'white'})
def save(fig, n): fig.savefig(os.path.join(FIG, n + '.png'), bbox_inches='tight'); plt.close(fig); print('saved', n)

st = pd.read_csv(os.path.join(T, 'flood_stats_by_landcover.csv'))
cls = st[st.class_name.isin(CLS)].copy(); allr = st[st.class_id == 99].iloc[0]

# ---- Fig 1: flooded area and share by land cover, 14 Nov
fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
order = list(CLS)
v = cls.set_index('class_name').loc[order]
ax[0].barh(order, v.flood_14Nov, color=[CLS[c] for c in order], height=0.6); ax[0].invert_yaxis()
for i, x in enumerate(v.flood_14Nov): ax[0].text(x + 1.5, i, '%.1f' % x, va='center', fontsize=9)
ax[0].set_xlabel('Flagged flooded area, 14 Nov 2023 (km$^2$)'); ax[0].set_xlim(0, v.flood_14Nov.max() * 1.15); ax[0].grid(axis='y', visible=False)
ax[1].barh(order, v.pct_domain_flood_14Nov, color=[CLS[c] for c in order], height=0.6); ax[1].invert_yaxis(); ax[1].set_yticklabels([])
for i, x in enumerate(v.pct_domain_flood_14Nov): ax[1].text(x + 0.8, i, '%.1f%%' % x, va='center', fontsize=9)
ax[1].set_xlabel('Share of the class analysed area flagged (%)'); ax[1].set_xlim(0, v.pct_domain_flood_14Nov.max() * 1.15); ax[1].grid(axis='y', visible=False)
fig.suptitle('Flagged flooding by land-cover class (analysed area = outside permanent water, HAND ≤ 10 m, slope ≤ 8°)', fontsize=10.5, y=1.02)
fig.text(0.01, -0.05, 'Built-up class: 4 hold-out test points only, treat as indicative. Land-cover labels = WorldCover/Dynamic World consensus, not ground truth.', fontsize=8, color=MUTED)
save(fig, 'fig1_flood_by_landcover_14Nov')

# ---- Fig 2: flagged area by date, stacked by class
dates = [('flood_2Nov', '2 Nov'), ('flood_14Nov', '14 Nov'), ('flood_26Nov', '26 Nov'), ('flood_8Dec', '8 Dec')]
fig, ax = plt.subplots(figsize=(7, 4)); bottom = np.zeros(len(dates))
for c in order:
    vals = np.array([cls[cls.class_name == c][k].iloc[0] for k, _ in dates])
    ax.bar([d for _, d in dates], vals, bottom=bottom, color=CLS[c], edgecolor='white', linewidth=1.5, width=0.6, label=c); bottom += vals
for i, (k, _) in enumerate(dates): ax.text(i, bottom[i] + 4, '%.0f' % allr[k], ha='center', fontsize=9, fontweight='bold')
ax.set_ylabel('Flagged flooded area (km$^2$)'); ax.set_ylim(0, bottom.max() * 1.12); ax.grid(axis='x', visible=False)
ax.legend(frameon=False, fontsize=8.5, loc='upper left'); ax.set_title('Flagged area at the four post-event Sentinel-1 dates (one orbit, 12-day revisit)', fontsize=10.5)
fig.text(0.01, -0.06, 'The 12-day revisit cannot resolve the flood crest; the largest flagged area (26 Nov) is not necessarily the peak.', fontsize=8, color=MUTED)
save(fig, 'fig2_flagged_area_over_time')

# ---- Fig 3: sensitivity of the 14 Nov total
sd = pd.read_csv(os.path.join(T, 'sensitivity_flood_area_14Nov.csv'))
main = sd.loc[sd.variant == 'main (calibrated)', 'flooded_km2_14Nov'].iloc[0]
fig, ax = plt.subplots(figsize=(8, 4.2)); XMAX = 650
for i, (n, x) in enumerate(zip(sd.variant, sd.flooded_km2_14Nov)):
    col = BLUE if n.startswith('main') else (VERM if n.startswith('paper') else SKY)
    ax.barh(i, min(x, XMAX), color=col, height=0.6)
    ax.text(min(x, XMAX) + 8, i, ('%.0f' % x) + (' (bar cut at %d)' % XMAX if x > XMAX else ''), va='center', fontsize=9)
ax.set_yticks(range(len(sd))); ax.set_yticklabels(sd.variant); ax.invert_yaxis(); ax.set_xlim(0, XMAX + 130); ax.grid(axis='y', visible=False)
ax.axvline(main, color=MUTED, lw=1, ls='--'); ax.set_xlabel('Flagged flooded area, 14 Nov 2023 (km$^2$)')
ax.set_title('How much the 14 Nov total depends on analyst choices', fontsize=10.5)
save(fig, 'fig3_sensitivity_flood_total')

# ---- Fig 4: validation against UNOSAT optical flood polygons
va = pd.read_csv(os.path.join(T, 'validation_with_kappa_and_exclusion.csv'))
vc = pd.read_csv(os.path.join(T, 'validation_with_cluster_filter.csv')); vc = vc[vc.rule.str.startswith('min cluster')].copy(); vc['rule'] = 'final'
va = pd.concat([va, vc[[c for c in va.columns if c in vc.columns]]], ignore_index=True)
rules = {'final': ('Final rule with 100 pixel cluster filter', BLUE), 'calibrated rule + dark exclusion': ('Calibrated rule, no cluster filter', SKY), 'fixed -2.0/-1.5 (paper values)': ('Fixed -2.0 / -1.5 dB, no filter', VERM)}
refs = [('PHR 12Nov (calibration)', 'Pléiades 12 Nov\n(calibration)'), ('GF2 23Nov (outside calib. extent)', 'GF-2\n23 Nov\n(indep.)'), ('WV2 30Nov (outside calib. extent)', 'WV-2\n30 Nov\n(indep.)')]
mets = [('precision', 'Precision'), ('recall', 'Recall'), ('balanced_acc', 'Balanced accuracy'), ('kappa', "Cohen's kappa")]
fig, axs = plt.subplots(1, 4, figsize=(12, 3.8), sharey=True)
for a, (m, ml) in zip(axs, mets):
    for j, (rk, (rl, col)) in enumerate(rules.items()):
        vals = [va[(va.reference == r) & (va.rule == rk)][m].iloc[0] for r, _ in refs]
        xs = np.arange(len(refs)) + (j - 1) * 0.27
        a.bar(xs, vals, width=0.25, color=col, label=rl)
        for x, y in zip(xs, vals): a.text(x, y + 0.015, '%.2f' % y, ha='center', fontsize=6.5)
    a.set_xticks(range(len(refs))); a.set_xticklabels([l for _, l in refs], fontsize=7.5); a.set_title(ml, fontsize=10); a.set_ylim(0, 1.05); a.grid(axis='x', visible=False)
axs[0].set_ylabel('Pixel-level agreement with UNOSAT')
h, l = axs[0].get_legend_handles_labels(); fig.legend(h, l, loc='lower center', ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.1))
fig.suptitle('Radar flood flag vs UNOSAT optical flood polygons (Sentinel-1 date offset 2-4 days; independent dates exclude the calibration extent)', fontsize=10, y=1.03)
save(fig, 'fig4_validation_vs_unosat')

# ---- Fig 5: severity-justification test
sv = pd.read_csv(os.path.join(T, 'severity_test_P_flooded_by_dVV_bin.csv')); pr = pd.read_csv(os.path.join(T, 'severity_test_persistence.csv'))
fig, ax = plt.subplots(1, 2, figsize=(11, 3.9))
bins = list(sv.dVV_bin.unique())
for pair, col in zip(sv.pair.unique(), [BLUE, VERM]):
    d = sv[sv.pair == pair]; ax[0].plot(range(len(d)), d.P_unosat_flooded, marker='o', ms=5, color=col, lw=2, label=pair)
ax[0].set_xticks(range(len(bins))); ax[0].set_xticklabels(bins, rotation=40, ha='right', fontsize=8)
ax[0].set_xlabel('Change in VV backscatter, post minus pre (dB, smoothed)'); ax[0].set_ylabel('Share of pixels that UNOSAT maps as flooded'); ax[0].set_ylim(0, 1)
ax[0].legend(frameon=False, fontsize=8.5, loc='lower left'); ax[0].set_title('Size of backscatter drop vs probability of flooding', fontsize=10)
w = 0.38
for j, (ref, col) in enumerate(zip(pr.ref.unique(), [BLUE, VERM])):
    d = pr[pr.ref == ref]; xs = d.dates_flagged + (j - 0.5) * w
    ax[1].bar(xs, d.P_unosat_flooded, width=w - 0.04, color=col, label=ref)
    for x, y in zip(xs, d.P_unosat_flooded): ax[1].text(x, y + 0.02, '%.2f' % y, ha='center', fontsize=8)
ax[1].set_xticks(range(4)); ax[1].set_xlabel('Post-event dates flagged (of 14 Nov, 26 Nov, 8 Dec)'); ax[1].set_ylim(0, 1.05); ax[1].grid(axis='x', visible=False)
ax[1].legend(frameon=False, fontsize=8.5, loc='upper left'); ax[1].set_title('Persistence of the flag vs probability of flooding', fontsize=10)
fig.text(0.01, -0.16, 'Evidence for ordinal intensity/persistence classes only. No water depth was measured or inferred.', fontsize=8, color=MUTED)
save(fig, 'fig5_severity_justification')

# ---- Fig 6: land-cover confusion matrix (agreement with consensus labels)
acc = json.load(open(os.path.join(T, 'lulc_accuracy_vs_consensus.json')))
names = ['Permanent\nwater', 'Cropland', 'Vegetation /\nrangeland', 'Built-up', 'Bare soil /\nsand']; cm = np.array(acc['confusion'])
fig, ax = plt.subplots(figsize=(6.2, 5.2)); rown = cm / cm.sum(1, keepdims=True)
im = ax.imshow(rown, cmap='Blues', vmin=0, vmax=1); ax.grid(False)
for i in range(5):
    for j in range(5): ax.text(j, i, str(cm[i, j]), ha='center', va='center', color='white' if rown[i, j] > 0.55 else INK, fontsize=10)
ax.set_xticks(range(5)); ax.set_xticklabels(names, fontsize=8); ax.set_yticks(range(5)); ax.set_yticklabels(names, fontsize=8)
ax.set_xlabel('Random Forest map'); ax.set_ylabel('Consensus label (WorldCover and Dynamic World agree)')
ax.set_title('Hold-out agreement: OA %.3f, kappa %.3f\n(spatial blocks; agreement with products, NOT ground truth)' % (acc['overall_accuracy'], acc['kappa']), fontsize=10)
ax.spines[:].set_visible(False); fig.colorbar(im, ax=ax, fraction=0.046, label='Row share')
fig.text(0.01, -0.03, 'Built-up has only 4 hold-out points (1 correct): its accuracy is not estimable.', fontsize=8, color=MUTED)
save(fig, 'fig6_lulc_confusion_matrix')

