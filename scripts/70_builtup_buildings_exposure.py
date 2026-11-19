import os, json, numpy as np, pandas as pd, rasterio
from scipy import ndimage as ndi
from rasterio import features
from shapely.geometry import Polygon
from pyproj import Transformer
B = r'.'; RAW = os.path.join(B, 'data', 'processed', 'raw10m'); DG = os.path.join(B, 'data', 'processed', 'diag'); OUT = os.path.join(B, 'outputs', 'tables'); MIN = 100; KM2 = 1e-4
def rd(n):
    with rasterio.open(os.path.join(RAW, n + '.tif')) as s: return s.read(1), s.transform
lulc, tr = rd('lulc'); lulc = lulc.astype('uint8'); H, W = lulc.shape; tf = Transformer.from_crs('EPSG:4326', 'EPSG:32638', always_xy=True)
def ring(x0, y0, x1, y1, n=400):
    xs = np.linspace(x0, x1, n); ys = np.linspace(y0, y1, n); return list(zip(xs, np.full(n, y0))) + list(zip(np.full(n, x1), ys)) + list(zip(xs[::-1], np.full(n, y1))) + list(zip(np.full(n, x0), ys[::-1]))
aoi = features.rasterize([(Polygon([tf.transform(x, y) for x, y in ring(45.00, 4.45, 45.65, 5.05)]), 1)], out_shape=(H, W), transform=tr, fill=0, dtype='uint8').astype(bool)
dom = rd('domain')[0].astype(bool) & aoi
def cf(f):
    lab, n = ndi.label(f, structure=np.ones((3, 3))); sz = np.bincount(lab.ravel()); keep = sz >= MIN; keep[0] = False; return keep[lab]
F = {k: cf(rd('flag_' + k)[0].astype(bool) & aoi) & dom for k in ['2Nov', '14Nov', '26Nov', '8Dec']}
xy = np.load(os.path.join(DG, 'open_buildings_centroids.npy')); X, Y = tf.transform(xy[:, 0], xy[:, 1]); c = ((np.array(X) - tr.c) / 10).astype(int); r = ((tr.f - np.array(Y)) / 10).astype(int)
ok = (r >= 0) & (r < H) & (c >= 0) & (c < W); r, c = r[ok], c[ok]; bm = np.zeros((H, W), bool); bm[r, c] = True; d = ndi.distance_transform_edt(~bm) * 10
# 1. flagged share of built-up by distance to a building
b = (lulc == 3) & dom; bins = [(0, 100), (100, 500), (500, 1e9)]; rows = []
for a, z in bins:
    m = b & (d >= a) & (d < z) if a > 0 else b & (d <= z)
    rows.append(['Built-up pixels %s m from a building' % ('within 100' if a == 0 else ('100 to 500' if a == 100 else 'more than 500')), m.sum() * KM2] + [(F[k] & m).sum() * KM2 for k in ['14Nov', '26Nov']] + [100 * (F[k] & m).sum() / max(m.sum(), 1) for k in ['14Nov', '26Nov']])
rows.append(['All built-up pixels in the analysed area', b.sum() * KM2] + [(F[k] & b).sum() * KM2 for k in ['14Nov', '26Nov']] + [100 * (F[k] & b).sum() / b.sum() for k in ['14Nov', '26Nov']])
bd = pd.DataFrame(rows, columns=['group', 'analysed_km2', 'flagged14_km2', 'flagged26_km2', 'share14_pct', 'share26_pct']); bd.to_csv(os.path.join(OUT, 'revision_builtup_by_building_distance.csv'), index=False); print(bd.round(2).to_string(index=False))
# 2. buildings in flagged pixels (centroid pixel, and any flagged pixel within 3 x 3 window)
inan = dom[r, c]; rows = [['Buildings in the study area', len(r)], ['Buildings in the analysed area', int(inan.sum())]]
for k in ['14Nov', '26Nov', '8Dec']:
    f = F[k]; f3 = ndi.binary_dilation(f, structure=np.ones((3, 3))); rows.append(['Buildings with centroid pixel flagged on ' + k, int(f[r, c].sum())]); rows.append(['Buildings with a flagged pixel within 1 pixel on ' + k, int(f3[r, c].sum())])
bt = pd.DataFrame(rows, columns=['item', 'count']); bt['pct_of_analysed_area_buildings'] = [np.nan, 100.0] + [100 * v / inan.sum() for v in bt['count'][2:]]; bt.to_csv(os.path.join(OUT, 'revision_buildings_in_flagged_area.csv'), index=False); print(bt.round(2).to_string(index=False))
pers = F['14Nov'].astype('uint8') + F['26Nov'] + F['8Dec']; print('buildings flagged on all three dates', int((pers[r, c] == 3).sum()))
by_cls = pd.Series(lulc[r, c][F['14Nov'][r, c]]).value_counts().to_dict(); print('buildings flagged 14 Nov by mapped class', by_cls)
