"""
Final full-area statistics, computed locally and deterministically from the 10 m rasters exported by script 23.
Order: raw flag (Earth Engine, includes dark-surface exclusion and valid-data condition) -> clip to the study rectangle -> remove 8-connected clusters
smaller than the minimum cluster size -> keep only the analysed area (not permanent water, HAND <= 10 m, slope <= 8 deg) -> sum pixel areas (100 m2 each).
"""
import os, json, numpy as np, pandas as pd, rasterio
from rasterio import features
from scipy import ndimage as ndi
from shapely.geometry import Polygon
from pyproj import Transformer
BASE = r'.'; RAW = os.path.join(BASE, 'data', 'processed', 'raw10m'); OUTR = os.path.join(BASE, 'data', 'processed', 'aoi_rasters10m')
OUT = os.path.join(BASE, 'outputs', 'tables'); P = json.load(open(os.path.join(OUT, 'chosen_parameters.json'))); MIN = int(P['min_cluster_px']); KM2 = 1e-4   # 100 m2 per 10 m pixel
CLASSES = {0: 'Permanent water', 1: 'Cropland', 2: 'Vegetation / rangeland', 3: 'Built-up', 4: 'Bare soil / sand'}
def rd(n):
    with rasterio.open(os.path.join(RAW, n + '.tif')) as s: return s.read(1), s.transform, s.profile
lulc, tr, prof = rd('lulc'); lulc = lulc.astype('uint8'); H, W = lulc.shape
def ring(x0, y0, x1, y1, n=400):
    xs = np.linspace(x0, x1, n); ys = np.linspace(y0, y1, n)
    return list(zip(xs, np.full(n, y0))) + list(zip(np.full(n, x1), ys)) + list(zip(xs[::-1], np.full(n, y1))) + list(zip(np.full(n, x0), ys[::-1]))
tf = Transformer.from_crs('EPSG:4326', 'EPSG:32638', always_xy=True); poly = Polygon([tf.transform(x, y) for x, y in ring(45.00, 4.45, 45.65, 5.05)])
aoi = features.rasterize([(poly, 1)], out_shape=(H, W), transform=tr, fill=0, dtype='uint8').astype(bool)
domain = rd('domain')[0].astype(bool) & aoi; perm = rd('perm')[0].astype(bool)
def cluster_filter(f, mn=MIN):
    lab, n = ndi.label(f, structure=np.ones((3, 3))); sz = np.bincount(lab.ravel()); keep = sz >= mn; keep[0] = False; return keep[lab]
raw = {k: rd('flag_' + k)[0].astype(bool) & aoi for k in ['2Nov', '14Nov', '26Nov', '8Dec']}
print('aoi km2 %.2f, domain km2 %.2f' % (aoi.sum() * KM2, domain.sum() * KM2), flush=True)
# consistency check against the independent local 10 m town implementation (script 15 gave 51.163 km2 without cluster filter and terrain mask)
with rasterio.open(os.path.join(BASE, 'data', 'processed', 'town_rasters', 'S1_20231021.tif')) as s: b = s.bounds
r0, c0 = rasterio.transform.rowcol(tr, b.left, b.top); r1, c1 = rasterio.transform.rowcol(tr, b.right, b.bottom)
print('check, raw 14 Nov flag inside the town raster extent: %.3f km2 (script 15 local numpy: 51.163)' % (raw['14Nov'][r0:r1, c0:c1].sum() * KM2), flush=True)
F = {}
for k, v in raw.items():
    F[k] = cluster_filter(v) & domain; print('flag', k, 'raw %.1f km2 -> clustered in analysed area %.1f km2' % (v.sum() * KM2, F[k].sum() * KM2), flush=True)
dv = rd('dvv14_x100')[0].astype('int32')
i1 = F['14Nov'] & (dv > -500); i2 = F['14Nov'] & (dv <= -500) & (dv > -700); i3 = F['14Nov'] & (dv <= -700)
pers = F['14Nov'].astype('uint8') + F['26Nov'] + F['8Dec']
layers = {'aoi_area': aoi, 'domain_area': domain, 'flood_2Nov': F['2Nov'], 'flood_14Nov': F['14Nov'], 'flood_26Nov': F['26Nov'], 'flood_8Dec': F['8Dec'],
          'intensity1_14Nov': i1, 'intensity2_14Nov': i2, 'intensity3_14Nov': i3, 'persist1': pers == 1, 'persist2': pers == 2, 'persist3': pers == 3}
rows = []
for c, nm in CLASSES.items():
    m = lulc == c; rows.append(dict(class_id=c, class_name=nm, **{k: float((v & m).sum() * KM2) for k, v in layers.items()}))
st = pd.DataFrame(rows); tt = st.drop(columns=['class_name']).sum(); tt['class_id'] = 99; tt['class_name'] = 'ALL CLASSES'; st = pd.concat([st, pd.DataFrame([tt])], ignore_index=True)
for c in ['flood_2Nov', 'flood_14Nov', 'flood_26Nov', 'flood_8Dec']: st['pct_domain_' + c] = 100 * st[c] / st['domain_area'].replace(0, np.nan)
st.to_csv(os.path.join(OUT, 'flood_stats_by_landcover.csv'), index=False); print(st.round(2).to_string(index=False), flush=True)
a = st[st.class_id == 99].iloc[0]; print('check: intensity sum %.3f vs flood_14Nov %.3f' % (a.intensity1_14Nov + a.intensity2_14Nov + a.intensity3_14Nov, a.flood_14Nov), flush=True)
# sensitivity (14 Nov)
dom_nt = ~perm & aoi
var = {'main (calibrated)': F['14Nov'], 'no dark exclusion': cluster_filter(rd('v_nodark')[0].astype(bool) & aoi) & domain, 'no HAND/slope mask': cluster_filter(raw['14Nov']) & dom_nt,
       'pre = 21 Oct only': cluster_filter(rd('v_pre21')[0].astype(bool) & aoi) & domain, 'pre = 9 Oct only': cluster_filter(rd('v_pre9')[0].astype(bool) & aoi) & domain,
       '3x3 filter': cluster_filter(rd('v_3x3')[0].astype(bool) & aoi) & domain, 'dVV-only rule (-2.5 dB)': cluster_filter(rd('v_dvvonly')[0].astype(bool) & aoi) & domain,
       'paper-style fixed -2.0/-1.5, no filter': cluster_filter(rd('v_paper')[0].astype(bool) & aoi) & domain}
sdf = pd.DataFrame({'variant': list(var), 'flooded_km2_14Nov': [float(v.sum() * KM2) for v in var.values()]})
# the same variants without the cluster filter, for the Methods comparison
nof = {'main (calibrated)': raw['14Nov'] & domain, 'no dark exclusion': rd('v_nodark')[0].astype(bool) & aoi & domain, 'no HAND/slope mask': raw['14Nov'] & dom_nt,
       'pre = 21 Oct only': rd('v_pre21')[0].astype(bool) & aoi & domain, 'pre = 9 Oct only': rd('v_pre9')[0].astype(bool) & aoi & domain, '3x3 filter': rd('v_3x3')[0].astype(bool) & aoi & domain,
       'dVV-only rule (-2.5 dB)': rd('v_dvvonly')[0].astype(bool) & aoi & domain, 'paper-style fixed -2.0/-1.5, no filter': rd('v_paper')[0].astype(bool) & aoi & domain}
sdf['flooded_km2_14Nov_no_cluster_filter'] = [float(nof[k].sum() * KM2) for k in sdf.variant]
sdf.to_csv(os.path.join(OUT, 'sensitivity_flood_area_14Nov.csv'), index=False); print(sdf.round(1).to_string(index=False), flush=True)
# rasters for the figures (same names script 12 reads), clustered and masked
def save(nm, arr):
    p = dict(prof, count=1, dtype='uint8', compress='deflate', nodata=None)
    with rasterio.open(os.path.join(OUTR, nm + '.tif'), 'w', **p) as d: d.write(arr.astype('uint8'), 1)
inten = np.zeros((H, W), 'uint8'); inten[i1] = 1; inten[i2] = 2; inten[i3] = 3
save('lulc', np.where(aoi, lulc, 0)); save('domain', domain); save('perm_water', perm & aoi); save('f_14Nov', F['14Nov']); save('f_26Nov', F['26Nov']); save('intensity', inten); save('persistence', pers)
print('rasters saved', flush=True)
