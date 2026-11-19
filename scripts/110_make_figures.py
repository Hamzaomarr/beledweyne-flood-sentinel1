"""All manuscript and supplementary figures, redrawn from the same data as scripts 10, 12, 13 and 71 and sized for the printed text width of 6.3 inches, so that no text is scaled down in the document.
Rules applied to every figure. Arial at regular weight, hairline axes, no top or right spines, y grid only on charts, no embedded titles or notes, panels labelled A, B, C in the top-left corner,
legends above the figure and set horizontally, space between axis titles and axes, colourblind-safe Okabe-Ito colours with hatches or line styles on charts, PNG at 300 DPI and PDF with embedded fonts in separate subfolders.
Output. outputs/figures/png/<name>.png and outputs/figures/pdf/<name>.pdf. Figures that are not used in the manuscript are not redrawn."""
import os, glob, json, numpy as np, pandas as pd, rasterio, geopandas as gpd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch, FancyBboxPatch
from matplotlib.lines import Line2D
from rasterio import features
from scipy import ndimage as ndi
from pyproj import Transformer

BASE = r'.'
T = os.path.join(BASE, 'outputs', 'tables'); AOI = os.path.join(BASE, 'data', 'processed', 'aoi_rasters10m'); TOWN = os.path.join(BASE, 'data', 'processed', 'town_rasters'); DG = os.path.join(BASE, 'data', 'processed', 'diag')
UN = os.path.join(BASE, 'data', 'raw', 'unosat_FL20231105SOM', 'extracted'); OUT = os.path.join(BASE, 'outputs', 'figures'); PNG = os.path.join(OUT, 'png'); PDF = os.path.join(OUT, 'pdf')
os.makedirs(PNG, exist_ok=True); os.makedirs(PDF, exist_ok=True)
P = json.load(open(os.path.join(T, 'chosen_parameters.json')))
INK, MUTED, GRID = '#222222', '#6b6b6b', '#d9d9d9'
BLUE, VERM, SKY, ORANGE, PINK, GREEN, GREY = '#0072B2', '#D55E00', '#56B4E9', '#E69F00', '#CC79A7', '#009E73', '#8c8c8c'
W = 6.3
plt.rcParams.update({'font.family': 'Arial', 'font.weight': 'normal', 'font.size': 7.5, 'axes.labelsize': 8, 'axes.titleweight': 'normal', 'axes.labelweight': 'normal', 'xtick.labelsize': 7, 'ytick.labelsize': 7,
                     'legend.fontsize': 7.5, 'text.color': INK, 'axes.labelcolor': INK, 'xtick.color': INK, 'ytick.color': INK, 'axes.edgecolor': INK, 'axes.linewidth': 0.5,
                     'xtick.major.width': 0.5, 'ytick.major.width': 0.5, 'xtick.major.size': 2.5, 'ytick.major.size': 2.5, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': False, 'grid.color': GRID, 'grid.linewidth': 0.4, 'axes.axisbelow': True, 'figure.facecolor': 'white', 'axes.facecolor': 'white', 'savefig.facecolor': 'white',
                     'hatch.linewidth': 0.5, 'pdf.fonttype': 42, 'ps.fonttype': 42, 'savefig.dpi': 300, 'axes.unicode_minus': True})
def save(fig, name):
    fig.savefig(os.path.join(PNG, name + '.png'), dpi=300, bbox_inches='tight', pad_inches=0.05)
    fig.savefig(os.path.join(PDF, name + '.pdf'), bbox_inches='tight', pad_inches=0.05); plt.close(fig); print('saved', name, flush=True)
def letter(ax, t): ax.text(0.0, 1.015, t, transform=ax.transAxes, ha='left', va='bottom', fontsize=9, fontweight='normal')
def above(obj, handles, ncol, y=1.0, **kw): return obj.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, y), ncol=ncol, frameon=False, columnspacing=1.2, handlelength=1.5, handletextpad=0.5, **kw)
def above_axes(fig, axs, handles, ncol, pad_in=0.3):
    # legend centred above a group of equal-aspect panels, placed from their drawn positions so that the gap to the panels stays small
    fig.canvas.draw()
    for a in axs: a.apply_aspect()
    pos = [a.get_position() for a in axs]; yt = max(q.y1 for q in pos); xc = (min(q.x0 for q in pos) + max(q.x1 for q in pos)) / 2
    return fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(xc, yt + pad_in / fig.get_figheight()), ncol=ncol, frameon=False, columnspacing=1.2, handlelength=1.5, handletextpad=0.5)
def rd(p):
    with rasterio.open(p) as s: return s.read(1), s
def ext(s): b = s.bounds; return [b.left / 1e3, b.right / 1e3, b.bottom / 1e3, b.top / 1e3]
def deco(ax, e, lab=True, xlab='Easting, km', ylab='Northing, km'):
    ax.set_xlim(e[0], e[1]); ax.set_ylim(e[2], e[3]); ax.set_aspect('equal'); ax.tick_params(labelsize=7)
    if lab: ax.set_xlabel(xlab, labelpad=6); ax.set_ylabel(ylab, labelpad=6)
def scalebar(ax, e, km, fy=0.05):
    x0 = e[0] + (e[1] - e[0]) * 0.05; y0 = e[2] + (e[3] - e[2]) * fy
    ax.plot([x0, x0 + km], [y0, y0], color=INK, lw=2.2, solid_capstyle='butt'); ax.text(x0 + km / 2, y0 + (e[3] - e[2]) * 0.015, '%d km' % km, ha='center', fontsize=7, color=INK)
def north(ax, e):
    x = e[1] - (e[1] - e[0]) * 0.07; y = e[3] - (e[3] - e[2]) * 0.15; dy = (e[3] - e[2]) * 0.07
    ax.annotate('', xy=(x, y + dy), xytext=(x, y), arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.0)); ax.text(x, y + dy * 1.15, 'N', ha='center', fontsize=8)
def shp(p): return gpd.read_file(glob.glob(os.path.join(UN, '**', p + '*.shp'), recursive=True)[0])
DS = 4   # the 10 m rasters are drawn at 40 m, which is finer than the 300 DPI output resolves at this size

# ============================================================ Figure 1, workflow
fig, ax = plt.subplots(figsize=(W, 5.3)); ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')
def box(x, y, w, h, t, fc='#ffffff'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.3,rounding_size=1.2', fc=fc, ec='#333333', lw=0.6)); ax.text(x + w / 2, y + h / 2, t, ha='center', va='center', fontsize=7)
def arrow(x1, y1, x2, y2): ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='-|>', color='#333333', lw=0.7, mutation_scale=7))
G = '#eeeeee'; C = [12, 37, 62, 87]; Wd = 22
for c, t in zip(C, ['Sentinel-2 composite\nand consensus\nland-cover labels', 'Sentinel-1\nVV and VH\n6 dates', 'UNOSAT optical\nflood mapping', 'Surface water,\nHAND and\nelevation data']): box(c - Wd / 2, 83, Wd, 14, t, G)
for c, t in zip(C, ['Random Forest\nland-cover map', 'Backscatter change,\nthreshold rule and\ncluster filter', 'Calibration on the\nPléiades mapping\nof 12 November', 'Permanent water,\nHAND and slope\nmasks']):
    box(c - Wd / 2, 62, Wd, 14, t); arrow(c, 83, c, 76.6)
arrow(C[2] - Wd / 2, 69, C[1] + Wd / 2 + 0.6, 69)
box(26, 41, 72, 12, 'Flagged flood extent for 4 post-event dates'); arrow(C[1], 62, C[1], 53.6); arrow(C[3], 62, C[3], 53.6)
for c, t in zip(C[1:], ['Intensity and\npersistence classes', 'Accuracy assessment\non independent\nreference dates', 'Sensitivity analyses']): box(c - Wd / 2, 20, Wd, 14, t); arrow(c, 41, c, 34.6)
box(1, 2, 60, 11, 'Flagged area by land-cover class'); arrow(C[0], 62, C[0], 13.6); arrow(C[1], 20, C[1], 13.6)
save(fig, 'fig_methods_workflow')

# ============================================================ study-area maps
lulc, s = rd(os.path.join(AOI, 'lulc.tif')); EI = ext(s)
_tf = Transformer.from_crs('EPSG:4326', 'EPSG:32638', always_xy=True); _c = [_tf.transform(x, y) for x, y in [(45.00, 4.45), (45.65, 4.45), (45.65, 5.05), (45.00, 5.05)]]
E = [min(c[0] for c in _c) / 1e3, max(c[0] for c in _c) / 1e3, min(c[1] for c in _c) / 1e3, max(c[1] for c in _c) / 1e3]
dom = rd(os.path.join(AOI, 'domain.tif'))[0].astype(bool); perm = rd(os.path.join(AOI, 'perm_water.tif'))[0].astype(bool)
LC = [BLUE, ORANGE, GREEN, PINK, GREY]; LCN = ['Water', 'Cropland', 'Vegetation or rangeland', 'Built-up', 'Bare soil or sand']
# ---- Figure 2
fig, ax = plt.subplots(figsize=(W, 5.9)); ax.imshow(lulc[::DS, ::DS], cmap=ListedColormap(LC), vmin=0, vmax=4, extent=EI, interpolation='nearest')
for p, ls in (('PHR_20231112_AnalysisExtent_Beledweyne', '-'), ('WV2_20231130_AnalysisExtent_BeledweyneCity', '--')):
    g = shp(p).to_crs(s.crs); g['geometry'] = g.geometry.scale(1e-3, 1e-3, origin=(0, 0)); g.boundary.plot(ax=ax, color='#000000', lw=1.0, ls=ls, aspect=None)
deco(ax, E); scalebar(ax, E, 10); north(ax, E)
h = [Patch(color=c, label=n) for c, n in zip(LC, LCN)] + [Line2D([0], [0], color='#000000', lw=1.0, ls='-', label='UNOSAT extent, Pléiades 12 November'), Line2D([0], [0], color='#000000', lw=1.0, ls='--', label='UNOSAT extent, Gaofen-2 23 November and WorldView-2 30 November')]
above(ax, h, 3, y=1.02); save(fig, 'fig7_study_area_landcover')
# ---- Figure 3
f14 = rd(os.path.join(AOI, 'f_14Nov.tif'))[0]; f26 = rd(os.path.join(AOI, 'f_26Nov.tif'))[0]
def floodmap(ax, f):
    img = np.zeros(f.shape, 'uint8'); img[~dom] = 1; img[perm] = 2; img[f.astype(bool)] = 3
    ax.imshow(img[::DS, ::DS], cmap=ListedColormap(['#f2f2f2', '#c9c9c9', BLUE, VERM]), vmin=0, vmax=3, extent=EI, interpolation='nearest'); deco(ax, E)
fig, axs = plt.subplots(1, 2, figsize=(W, 3.7), sharey=True); fig.subplots_adjust(wspace=0.12, top=0.84)
floodmap(axs[0], f14); floodmap(axs[1], f26); axs[1].set_ylabel(''); scalebar(axs[0], E, 10); north(axs[1], E); letter(axs[0], 'A'); letter(axs[1], 'B')
above_axes(fig, axs, [Patch(color=VERM, label='Flagged, radar backscatter drop'), Patch(color=BLUE, label='Permanent water'), Patch(facecolor='#f2f2f2', edgecolor='#999999', label='Analysed, not flagged'),
            Patch(color='#c9c9c9', label='Excluded, HAND above 10 m or slope above 8°')], 2); save(fig, 'fig8_flood_extent_14Nov_26Nov')
# ---- Figure 4, intensity and persistence
inten = rd(os.path.join(AOI, 'intensity.tif'))[0]; pers = rd(os.path.join(AOI, 'persistence.tif'))[0]
fig, axs = plt.subplots(2, 1, figsize=(W, 8.3)); fig.subplots_adjust(hspace=0.42, top=0.93, bottom=0.05)
axs[0].imshow(inten[::DS, ::DS], cmap=ListedColormap(['#f2f2f2', '#fdd49e', '#fc8d59', '#b30000']), vmin=0, vmax=3, extent=EI, interpolation='nearest'); deco(axs[0], E); scalebar(axs[0], E, 10); north(axs[0], E)
above(axs[0], [Patch(color='#fdd49e', label='Weak change, drop below 5 dB'), Patch(color='#fc8d59', label='Moderate, 5 to 7 dB'), Patch(color='#b30000', label='Strong, 7 dB or more'), Patch(color='#f2f2f2', label='Not flagged')], 2, y=1.07)
axs[1].imshow(pers[::DS, ::DS], cmap=ListedColormap(['#f2f2f2', '#c6dbef', '#6baed6', '#08519c']), vmin=0, vmax=3, extent=EI, interpolation='nearest'); deco(axs[1], E); scalebar(axs[1], E, 10); north(axs[1], E)
above(axs[1], [Patch(color='#c6dbef', label='Flagged on 1 of 3 dates'), Patch(color='#6baed6', label='Flagged on 2 of 3 dates'), Patch(color='#08519c', label='Flagged on all 3 dates'), Patch(color='#f2f2f2', label='Not flagged')], 2, y=1.07)
letter(axs[0], 'A'); letter(axs[1], 'B'); save(fig, 'fig_intensity_persistence_combined')

# ============================================================ town rasters
def town(d):
    with rasterio.open(os.path.join(TOWN, 'S1_%s.tif' % d)) as s_: return s_.read().astype('float32'), s_
s1 = {d: town(d)[0] for d in ['20231009', '20231021', '20231114']}; _, st = town('20231021'); tr = st.transform; H, Wd_ = s1['20231021'].shape[1:]; ET = ext(st)
pre = (s1['20231009'] + s1['20231021']) / 2; post = s1['20231114']; k = P['filt']; sm = lambda a: ndi.median_filter(a, size=k, mode='nearest')
dVV = sm(post[0] - pre[0]); dVH = sm(post[1] - pre[1]); dark = sm(pre[0]) < P['dark_cutoff']
flag = ((dVV <= -P['tVV']) | (dVH <= -P['tVH'])) & ~dark; valid = np.isfinite(post).all(0) & np.isfinite(pre).all(0)
def rm_small(f_, mn):
    lab_, n_ = ndi.label(f_, structure=np.ones((3, 3))); sz_ = np.bincount(lab_.ravel()); kp_ = sz_ >= mn; kp_[0] = False; return kp_[lab_]
flag = rm_small(flag & valid, int(P['min_cluster_px']))
def burn(g): g = g.to_crs(st.crs); return features.rasterize([(x, 1) for x in g.geometry if x is not None], out_shape=(H, Wd_), transform=tr, fill=0, dtype='uint8').astype(bool)
gA, gF, gW, gC = [shp('PHR_20231112_' + n + '_Beledweyne') for n in ['AnalysisExtent', 'FloodExtent', 'WaterExtent', 'CloudObstruction']]
PA, PF, PW, PC = burn(gA), burn(gF), burn(gW), burn(gC); PF &= PA
# ---- Figure 5, agreement map
cmp_ = np.zeros((H, Wd_), 'uint8'); A = PA & ~PC & valid & (PF | ~PW)
cmp_[A & flag & PF] = 1; cmp_[A & flag & ~PF] = 2; cmp_[A & ~flag & PF] = 3; cmp_[A & ~flag & ~PF] = 4
tp, fp, fn = [(cmp_ == i).sum() for i in (1, 2, 3)]
fig, ax = plt.subplots(figsize=(W, 5.2)); fig.subplots_adjust(top=0.8)
ax.imshow(cmp_, cmap=ListedColormap(['#ffffff', SKY, ORANGE, '#000000', '#e8e8e8']), vmin=0, vmax=4, extent=ET, interpolation='nearest'); bb = gA.to_crs(st.crs).total_bounds / 1e3; EZ = [bb[0] - 0.3, bb[2] + 0.3, bb[1] - 0.3, bb[3] + 0.3]
deco(ax, EZ); scalebar(ax, EZ, 2, fy=0.012); north(ax, EZ)
above(ax, [Patch(color=SKY, label='Agree, flooded in both, %.1f km²' % (tp / 1e4)), Patch(color=ORANGE, label='Radar only, %.1f km²' % (fp / 1e4)), Patch(color='#000000', label='UNOSAT only, missed by radar, %.1f km²' % (fn / 1e4)),
            Patch(color='#e8e8e8', label='Not flooded in either'), Patch(facecolor='white', edgecolor='#999999', label='Not scored, cloud, permanent water or no valid radar')], 2, y=1.02)
save(fig, 'fig12_agreement_map_town')
# ---- Figure S2, before and after
fig, axs = plt.subplots(1, 3, figsize=(W, 2.9), sharey=True); fig.subplots_adjust(top=0.85, wspace=0.5)
for a, im, cm_, lim, lab in [(axs[0], pre[0], 'gray', (-25, 0), 'VV, dB'), (axs[1], post[0], 'gray', (-25, 0), 'VV, dB'), (axs[2], post[0] - pre[0], 'RdBu', (-10, 10), 'Change in VV, dB')]:
    m = a.imshow(np.where(valid, im, np.nan), cmap=cm_, vmin=lim[0], vmax=lim[1], extent=ET, interpolation='nearest'); deco(a, ET, lab=False)
    a.contour(np.linspace(ET[0], ET[1], Wd_), np.linspace(ET[3], ET[2], H), PF.astype(float), levels=[0.5], colors=[VERM], linewidths=0.7)
    cb = fig.colorbar(m, ax=a, fraction=0.046, pad=0.03); cb.set_label(lab, labelpad=4, fontsize=7); cb.ax.tick_params(labelsize=6.5, width=0.5, length=2); cb.outline.set_linewidth(0.5)
    a.set_xlabel('Easting, km', labelpad=5)
axs[0].set_ylabel('Northing, km', labelpad=5)
for a, t in zip(axs, 'ABC'): letter(a, t)
above_axes(fig, axs, [Line2D([0], [0], color=VERM, lw=1.0, label='UNOSAT Pléiades 12 November flood extent')], 1); save(fig, 'fig11_sentinel1_before_after_town')

# ============================================================ Figure 7, pre-event scene difference
Z = np.load(os.path.join(DG, 's1_100m_means.npz')); d = Z['o21_VV'] - Z['o09_VV']; ex = np.load(os.path.join(DG, 'extra21_100m.npy')); mn = np.load(os.path.join(DG, 'main14_100m.npy')); exx = (498, 574, 490, 560)
fig, axs = plt.subplots(1, 2, figsize=(W, 3.5), sharey=True); fig.subplots_adjust(wspace=0.42)
im = axs[0].imshow(d, cmap='RdBu_r', vmin=-4, vmax=4, extent=exx, interpolation='nearest'); cb = fig.colorbar(im, ax=axs[0], fraction=0.046, pad=0.03); cb.set_label('Mean change in VV, dB', labelpad=4)
hb = np.clip(ex, 0, 1); im2 = axs[1].imshow(hb, cmap='YlOrBr', vmin=0, vmax=1, extent=exx, interpolation='nearest'); cb2 = fig.colorbar(im2, ax=axs[1], fraction=0.046, pad=0.03); cb2.set_label('Share of 100 m cell flagged\nonly with the 21 October reference', labelpad=4)
axs[1].contour(np.linspace(498.05, 573.95, mn.shape[1]), np.linspace(559.95, 490.05, mn.shape[0]), mn, levels=[0.05], colors='#333333', linewidths=0.4)
for a, t in zip(axs, 'AB'):
    a.set_xlabel('Easting, km', labelpad=5); a.tick_params(labelsize=7); letter(a, t)
axs[0].set_ylabel('Northing, km', labelpad=5)
for c_ in (cb, cb2): c_.ax.tick_params(labelsize=6.5, width=0.5, length=2); c_.outline.set_linewidth(0.5)
save(fig, 'fig13_preevent_scene_difference')

# ============================================================ Figure 6, accuracy against UNOSAT
va = pd.read_csv(os.path.join(T, 'validation_with_kappa_and_exclusion.csv')); vc = pd.read_csv(os.path.join(T, 'validation_with_cluster_filter.csv')); vc = vc[vc.rule.str.startswith('min cluster')].copy(); vc['rule'] = 'final'
va = pd.concat([va, vc[[c for c in va.columns if c in vc.columns]]], ignore_index=True)
rules = {'final': ('Final rule, 100 pixel cluster filter', BLUE, ''), 'calibrated rule + dark exclusion': ('Calibrated rule, no cluster filter', SKY, '/////'), 'fixed -2.0/-1.5 (paper values)': ('Fixed thresholds, no filter', VERM, 'xxxxx')}
refs = [('PHR 12Nov (calibration)', 'Pléiades\n12 November\ncalibration'), ('GF2 23Nov (outside calib. extent)', 'Gaofen-2\n23 November\nindependent'), ('WV2 30Nov (outside calib. extent)', 'WorldView-2\n30 November\nindependent')]
mets = [('precision', 'Precision'), ('recall', 'Recall'), ('balanced_acc', 'Balanced accuracy'), ('kappa', "Cohen's kappa")]
fig, axs = plt.subplots(2, 2, figsize=(W, 5.6), sharey=True); fig.subplots_adjust(hspace=0.55, wspace=0.12, top=0.88)
for a, (m, ml), t in zip(axs.flat, mets, 'ABCD'):
    for j, (rk, (rl, col, hat)) in enumerate(rules.items()):
        vals = [va[(va.reference == r) & (va.rule == rk)][m].iloc[0] for r, _ in refs]; xs = np.arange(len(refs)) + (j - 1) * 0.28
        a.bar(xs, vals, width=0.26, color=col, edgecolor=INK, linewidth=0.4, hatch=hat, label=rl)
        for x, y in zip(xs, vals): a.text(x, y + 0.015, '%.2f' % y, ha='center', fontsize=6.5)
    a.set_xticks(range(len(refs))); a.set_xticklabels([l for _, l in refs], fontsize=6.5); a.set_ylim(0, 1.08); a.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0]); a.set_ylabel(ml, labelpad=6); a.grid(axis='y'); a.tick_params(axis='x', pad=3); letter(a, t)
h, l = axs[0, 0].get_legend_handles_labels(); above(fig, h, 3, y=0.93); save(fig, 'fig4_validation_vs_unosat')

# ============================================================ Figure S1, severity classes
sv = pd.read_csv(os.path.join(T, 'severity_test_P_flooded_by_dVV_bin.csv')); pr = pd.read_csv(os.path.join(T, 'severity_test_persistence.csv'))
BINL = {'(-inf, -12]': 'below -12', '(-12, -9]': '-12 to -9', '(-9, -7]': '-9 to -7', '(-7, -5]': '-7 to -5', '(-5, -4]': '-5 to -4', '(-4, -3]': '-4 to -3', '(-3, -2]': '-3 to -2', '(-2, 0]': '-2 to 0', '(0, +inf]': 'above 0'}
PN = {'PHR 12Nov vs S1 14Nov': 'Pléiades 12 November against radar 14 November', 'GF2 23Nov vs S1 26Nov': 'Gaofen-2 23 November against radar 26 November'}
RN = {'PHR 12Nov': 'Pléiades 12 November', 'GF2 23Nov outside PHR': 'Gaofen-2 23 November, outside the Pléiades extent'}
fig, axs = plt.subplots(2, 1, figsize=(W, 6.2)); fig.subplots_adjust(hspace=0.62, top=0.93, bottom=0.07)
bins = list(sv.dVV_bin.unique())
for pair, col, mk, ls in zip(sv.pair.unique(), [BLUE, VERM], ['o', 's'], ['-', '--']):
    dd = sv[sv.pair == pair]; axs[0].plot(range(len(dd)), dd.P_unosat_flooded, marker=mk, ms=4, color=col, lw=1.2, ls=ls, label=PN.get(pair, pair))
axs[0].set_xticks(range(len(bins))); axs[0].set_xticklabels([BINL.get(b, b) for b in bins], fontsize=6.5); axs[0].set_xlabel('Change in VV backscatter, post minus pre, dB', labelpad=6)
axs[0].set_ylabel('Flooded share of reference pixels', labelpad=6); axs[0].set_ylim(0, 1.05); axs[0].grid(axis='y'); above(axs[0], axs[0].get_legend_handles_labels()[0], 1, y=1.1) if False else None
axs[0].legend(loc='lower center', bbox_to_anchor=(0.5, 1.1), ncol=2, frameon=False, columnspacing=1.2, handlelength=2.2, fontsize=7)
w = 0.38
for j, (ref, col, hat) in enumerate(zip(pr.ref.unique(), [BLUE, VERM], ['', 'xxxxx'])):
    dd = pr[pr.ref == ref]; xs = dd.dates_flagged + (j - 0.5) * w
    axs[1].bar(xs, dd.P_unosat_flooded, width=w - 0.04, color=col, edgecolor=INK, linewidth=0.4, hatch=hat, label=RN.get(ref, ref))
    for x, y in zip(xs, dd.P_unosat_flooded): axs[1].text(x, y + 0.02, '%.2f' % y, ha='center', fontsize=6.5)
axs[1].set_xticks(range(4)); axs[1].set_xlabel('Number of dates flagged', labelpad=6); axs[1].set_ylabel('Flooded share of reference pixels', labelpad=6); axs[1].set_ylim(0, 1.05); axs[1].grid(axis='y')
axs[1].legend(loc='lower center', bbox_to_anchor=(0.5, 1.1), ncol=2, frameon=False, columnspacing=1.2, handlelength=1.5, fontsize=7)
letter(axs[0], 'A'); letter(axs[1], 'B'); save(fig, 'fig5_severity_justification')
