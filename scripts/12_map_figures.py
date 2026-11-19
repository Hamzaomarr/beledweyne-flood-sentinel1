"""
Map figures from the real rasters only (no basemap tiles, nothing drawn by hand).
 fig7  land cover + UNOSAT analysis extents (study area)
 fig8  flagged flood extent 14 Nov and 26 Nov
 fig9  intensity classes, 14 Nov
 fig10 persistence (dates flagged)
 fig11 Sentinel-1 VV before / after / change in the town, with UNOSAT 12 Nov flood outline
 fig12 agreement map in the town: radar flag 14 Nov vs UNOSAT Pleiades 12 Nov (calibration date)
"""
import os, glob, json, numpy as np, rasterio, geopandas as gpd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from rasterio import features
from scipy import ndimage as ndi

BASE = r'.'
AOI = os.path.join(BASE, 'data', 'processed', 'aoi_rasters10m'); TOWN = os.path.join(BASE, 'data', 'processed', 'town_rasters')
UN = os.path.join(BASE, 'data', 'raw', 'unosat_FL20231105SOM', 'extracted'); FIG = os.path.join(BASE, 'outputs', 'figures')
P = json.load(open(os.path.join(BASE, 'outputs', 'tables', 'chosen_parameters.json')))
INK, MUTED = '#222222', '#6b6b6b'
plt.rcParams.update({'font.size': 9, 'text.color': INK, 'axes.labelcolor': INK, 'xtick.color': INK, 'ytick.color': INK, 'axes.edgecolor': MUTED,
                     'savefig.dpi': 300, 'figure.facecolor': 'white'})
def save(fig, n):
    try: fig.savefig(os.path.join(FIG, n + '.png'), bbox_inches='tight'); print('saved', n, flush=True)
    except Exception as e: print('could not save', n, str(e)[:80], flush=True)
    plt.close(fig)
def rd(p):
    with rasterio.open(p) as s: return s.read(1), s
def ext(s): b = s.bounds; return [b.left / 1e3, b.right / 1e3, b.bottom / 1e3, b.top / 1e3]
def deco(ax, e, lab=True):
    ax.set_xlim(e[0], e[1]); ax.set_ylim(e[2], e[3]); ax.set_aspect('equal')
    ax.tick_params(labelsize=7)
    if lab: ax.set_xlabel('Easting (km, UTM 38N)', fontsize=8); ax.set_ylabel('Northing (km, UTM 38N)', fontsize=8)
def scalebar(ax, e, km, fy=0.05):
    x0 = e[0] + (e[1] - e[0]) * 0.05; y0 = e[2] + (e[3] - e[2]) * fy
    ax.plot([x0, x0 + km], [y0, y0], color=INK, lw=3, solid_capstyle='butt'); ax.text(x0 + km / 2, y0 + (e[3] - e[2]) * 0.012, '%d km' % km, ha='center', fontsize=8, color=INK)
def north(ax, e):
    x = e[1] - (e[1] - e[0]) * 0.06; y = e[3] - (e[3] - e[2]) * 0.14; dy = (e[3] - e[2]) * 0.07
    ax.annotate('', xy=(x, y + dy), xytext=(x, y), arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.5)); ax.text(x, y + dy * 1.15, 'N', ha='center', fontsize=9, fontweight='bold')
def shp(p): return gpd.read_file(glob.glob(os.path.join(UN, '**', p + '*.shp'), recursive=True)[0])

lulc, s = rd(os.path.join(AOI, 'lulc.tif')); EI = ext(s);
from pyproj import Transformer
_tf = Transformer.from_crs('EPSG:4326', 'EPSG:32638', always_xy=True); _c = [_tf.transform(x, y) for x, y in [(45.00, 4.45), (45.65, 4.45), (45.65, 5.05), (45.00, 5.05)]]
E = [min(c[0] for c in _c) / 1e3, max(c[0] for c in _c) / 1e3, min(c[1] for c in _c) / 1e3, max(c[1] for c in _c) / 1e3]   # axis limits = study rectangle
dom = rd(os.path.join(AOI, 'domain.tif'))[0].astype(bool); perm = rd(os.path.join(AOI, 'perm_water.tif'))[0].astype(bool)
ext_layers = {'Pléiades 12 Nov': ('PHR_20231112_AnalysisExtent_Beledweyne', '#000000'), 'GF-2 23 Nov = WorldView-2 30 Nov (identical box)': ('WV2_20231130_AnalysisExtent_BeledweyneCity', '#0072B2')}
LC = ['#0072B2', '#E69F00', '#009E73', '#CC79A7', '#8c8c8c']; LCN = ['Water', 'Cropland', 'Vegetation / rangeland', 'Built-up', 'Bare soil / sand']

# ---- fig7
fig, ax = plt.subplots(figsize=(7.2, 7)); ax.imshow(lulc, cmap=ListedColormap(LC), vmin=0, vmax=4, extent=EI, interpolation='nearest')
for n, (p, c) in ext_layers.items():
    g = shp(p).to_crs(s.crs); g['geometry'] = g.geometry.scale(1e-3, 1e-3, origin=(0, 0)); g.boundary.plot(ax=ax, color=c, lw=1.4, aspect=None)
deco(ax, E); scalebar(ax, E, 10); north(ax, E)
h = [Patch(color=c, label=n) for c, n in zip(LC, LCN)] + [Line2D([0], [0], color=c, lw=1.5, label='UNOSAT extent: ' + n) for n, (_, c) in ext_layers.items()]
ax.legend(handles=h, loc='upper left', bbox_to_anchor=(1.02, 1.0), fontsize=8, frameon=False)
save(fig, 'fig7_study_area_landcover')

# ---- fig8 flood extent, two dates
base = np.where(dom, 0, 1)  # 0 analysed land, 1 excluded
def floodmap(ax, f, title):
    img = np.zeros(f.shape, 'uint8'); img[~dom] = 1; img[perm] = 2; img[f.astype(bool)] = 3
    ax.imshow(img, cmap=ListedColormap(['#f2f2f2', '#c9c9c9', '#0072B2', '#D55E00']), vmin=0, vmax=3, extent=EI, interpolation='nearest')
    deco(ax, E); ax.set_title(title, fontsize=9.5)
fig, axs = plt.subplots(1, 2, figsize=(11, 5.6), sharey=True)
f14 = rd(os.path.join(AOI, 'f_14Nov.tif'))[0]; f26 = rd(os.path.join(AOI, 'f_26Nov.tif'))[0]
floodmap(axs[0], f14, '14 Nov 2023'); floodmap(axs[1], f26, '26 Nov 2023'); axs[1].set_ylabel('')
scalebar(axs[0], E, 10); north(axs[1], E)
fig.legend(handles=[Patch(color='#D55E00', label='Flagged (radar backscatter drop)'), Patch(color='#0072B2', label='Permanent water'), Patch(facecolor='#f2f2f2', edgecolor='#999999', label='Analysed, not flagged'),
                    Patch(color='#c9c9c9', label='Excluded (HAND > 10 m or slope > 8°)')], loc='lower center', ncol=4, fontsize=8, frameon=False, bbox_to_anchor=(0.5, 0.02))
save(fig, 'fig8_flood_extent_14Nov_26Nov')

# ---- fig9 intensity
inten = rd(os.path.join(AOI, 'intensity.tif'))[0]
fig, ax = plt.subplots(figsize=(7.2, 7)); img = np.zeros(inten.shape, 'uint8'); img[~dom] = 0; img[dom] = 0
cm = ListedColormap(['#f2f2f2', '#fdd49e', '#fc8d59', '#b30000']); ax.imshow(inten, cmap=cm, vmin=0, vmax=3, extent=EI, interpolation='nearest')
deco(ax, E); scalebar(ax, E, 10); north(ax, E)
ax.legend(handles=[Patch(color='#fdd49e', label='Weak change (drop < 5 dB)'), Patch(color='#fc8d59', label='Moderate (5 to 7 dB)'), Patch(color='#b30000', label='Strong (7 dB or more)'), Patch(color='#f2f2f2', label='Not flagged')],
          loc='upper left', bbox_to_anchor=(1.02, 1.0), fontsize=8, frameon=False)
save(fig, 'fig9_intensity_14Nov')

# ---- fig10 persistence
pers = rd(os.path.join(AOI, 'persistence.tif'))[0]
fig, ax = plt.subplots(figsize=(7.2, 7)); ax.imshow(pers, cmap=ListedColormap(['#f2f2f2', '#c6dbef', '#6baed6', '#08519c']), vmin=0, vmax=3, extent=EI, interpolation='nearest')
deco(ax, E); scalebar(ax, E, 10); north(ax, E)
ax.legend(handles=[Patch(color='#c6dbef', label='Flagged on 1 of 3 dates'), Patch(color='#6baed6', label='Flagged on 2 of 3 dates'), Patch(color='#08519c', label='Flagged on all 3 (14 Nov, 26 Nov, 8 Dec)'), Patch(color='#f2f2f2', label='Not flagged')],
          loc='upper left', bbox_to_anchor=(1.02, 1.0), fontsize=8, frameon=False)
save(fig, 'fig10_persistence')

# ---- town rasters (10 m)
def town(d):
    with rasterio.open(os.path.join(TOWN, 'S1_%s.tif' % d)) as s: return s.read().astype('float32'), s
s1 = {d: town(d)[0] for d in ['20231009', '20231021', '20231114']}; _, st = town('20231021'); tr = st.transform; H, W = s1['20231021'].shape[1:]; ET = ext(st)
pre = (s1['20231009'] + s1['20231021']) / 2; post = s1['20231114']; k = P['filt']
sm = lambda a: ndi.median_filter(a, size=k, mode='nearest')
dVV = sm(post[0] - pre[0]); dVH = sm(post[1] - pre[1]); dark = sm(pre[0]) < P['dark_cutoff']
flag = ((dVV <= -P['tVV']) | (dVH <= -P['tVH'])) & ~dark
valid = np.isfinite(post).all(0) & np.isfinite(pre).all(0)
def rm_small(f_, mn):
    lab_, n_ = ndi.label(f_, structure=np.ones((3, 3))); sz_ = np.bincount(lab_.ravel()); kp_ = sz_ >= mn; kp_[0] = False; return kp_[lab_]
flag = rm_small(flag & valid, int(P['min_cluster_px']))   # same minimum cluster size as the full-area run
def burn(g): g = g.to_crs(st.crs); return features.rasterize([(x, 1) for x in g.geometry if x is not None], out_shape=(H, W), transform=tr, fill=0, dtype='uint8').astype(bool)
gA, gF, gW, gC = [shp('PHR_20231112_' + n + '_Beledweyne') for n in ['AnalysisExtent', 'FloodExtent', 'WaterExtent', 'CloudObstruction']]
PA, PF, PW, PC = burn(gA), burn(gF), burn(gW), burn(gC); PF &= PA

# ---- fig11
fig, axs = plt.subplots(1, 3, figsize=(13, 4.8), sharey=True)
for a, im, t, cm_, lim in [(axs[0], pre[0], 'VV before (mean of 9 and 21 Oct)', 'gray', (-25, 0)), (axs[1], post[0], 'VV after (14 Nov)', 'gray', (-25, 0)), (axs[2], post[0] - pre[0], 'Change in VV (after − before, dB)', 'RdBu', (-10, 10))]:
    m = a.imshow(np.where(valid, im, np.nan), cmap=cm_, vmin=lim[0], vmax=lim[1], extent=ET, interpolation='nearest'); a.set_title(t, fontsize=9); deco(a, ET, lab=False)
    a.contour(np.linspace(ET[0], ET[1], W), np.linspace(ET[3], ET[2], H), PF.astype(float), levels=[0.5], colors=['#D55E00'], linewidths=0.8)
    fig.colorbar(m, ax=a, fraction=0.046, pad=0.02, label='dB')
axs[0].set_ylabel('Northing (km, UTM 38N)', fontsize=8)
for a in axs: a.set_xlabel('Easting (km)', fontsize=8)
fig.legend(handles=[Line2D([0], [0], color='#D55E00', lw=1.5, label='UNOSAT Pléiades 12 Nov flood extent')], loc='lower center', frameon=False, bbox_to_anchor=(0.5, -0.04))
save(fig, 'fig11_sentinel1_before_after_town')

# ---- fig12 agreement map
cmp = np.zeros((H, W), 'uint8'); A = PA & ~PC & valid & (PF | ~PW)
cmp[A & flag & PF] = 1; cmp[A & flag & ~PF] = 2; cmp[A & ~flag & PF] = 3; cmp[A & ~flag & ~PF] = 4
tp, fp, fn = [(cmp == i).sum() for i in (1, 2, 3)]
fig, ax = plt.subplots(figsize=(7.4, 6.4))
ax.imshow(cmp, cmap=ListedColormap(['#ffffff', '#009E73', '#D55E00', '#0072B2', '#e8e8e8']), vmin=0, vmax=4, extent=ET, interpolation='nearest'); bb = gA.to_crs(st.crs).total_bounds / 1e3; EZ = [bb[0] - 0.3, bb[2] + 0.3, bb[1] - 0.3, bb[3] + 0.3]
deco(ax, EZ); scalebar(ax, EZ, 2, fy=0.012); north(ax, EZ)
ax.legend(handles=[Patch(color='#009E73', label='Agree: flooded in both (%.1f km²)' % (tp / 1e4)), Patch(color='#D55E00', label='Radar only (%.1f km²)' % (fp / 1e4)),
                   Patch(color='#0072B2', label='UNOSAT only, missed by radar (%.1f km²)' % (fn / 1e4)), Patch(color='#e8e8e8', label='Not flooded in either'),
                   Patch(facecolor='white', edgecolor='#999999', label='Not scored (cloud, permanent water, no valid radar)')], loc='upper center', bbox_to_anchor=(0.5, -0.12), fontsize=7.5, frameon=False, ncol=2)
save(fig, 'fig12_agreement_map_town')