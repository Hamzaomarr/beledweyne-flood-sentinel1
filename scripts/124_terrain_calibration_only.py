"""Terrain limits derived from the calibration (Pleiades) flood pixels only, and the effect on the analysed area and the flagged totals."""
import os, json, numpy as np, pandas as pd, rasterio
from rasterio.warp import reproject, Resampling
from rasterio import features
from scipy import ndimage as ndi
from shapely.geometry import Polygon
from pyproj import Transformer
B = r'.'; RAW = os.path.join(B, 'data', 'processed', 'raw10m'); DG = os.path.join(B, 'data', 'processed', 'diag'); OUT = os.path.join(B, 'outputs', 'tables')
P = json.load(open(os.path.join(OUT, 'chosen_parameters.json'))); MIN = int(P['min_cluster_px']); KM2 = 1e-4
CL = {1: 'Cropland', 2: 'Vegetation or rangeland', 3: 'Built-up', 4: 'Bare soil or sand'}
def rd(n):
    with rasterio.open(os.path.join(RAW, n + '.tif')) as s: return s.read(1), s.transform, s.crs
lulc, tr, crs = rd('lulc'); lulc = lulc.astype('uint8'); H, W = lulc.shape
tf = Transformer.from_crs('EPSG:4326', 'EPSG:32638', always_xy=True)
def ring(x0, y0, x1, y1, n=400):
    xs = np.linspace(x0, x1, n); ys = np.linspace(y0, y1, n)
    return list(zip(xs, np.full(n, y0))) + list(zip(np.full(n, x1), ys)) + list(zip(xs[::-1], np.full(n, y1))) + list(zip(np.full(n, x0), ys[::-1]))
aoi = features.rasterize([(Polygon([tf.transform(x, y) for x, y in ring(45.00, 4.45, 45.65, 5.05)]), 1)], out_shape=(H, W), transform=tr, fill=0, dtype='uint8').astype(bool)
dom = rd('domain')[0].astype(bool) & aoi; perm = rd('perm')[0].astype(bool)
hand = rasterio.open(os.path.join(DG, 'hand_10m.tif')).read(1).astype('float32')
print('HAND range', hand.min(), hand.max(), '| analysed pixels with HAND>10:', int((dom & (hand > 10.001)).sum()), '| analysed with HAND>4.7:', int((dom & (hand > 4.7001)).sum()), '| HAND>10 share of whole aoi', float((aoi & (hand > 10.001)).mean()))
def cf(f):
    lab, n = ndi.label(f, structure=np.ones((3, 3))); sz = np.bincount(lab.ravel()); keep = sz >= MIN; keep[0] = False; return keep[lab]
raw14 = rd('flag_14Nov')[0].astype(bool) & aoi; raw26 = rd('flag_26Nov')[0].astype(bool) & aoi; c14 = cf(raw14); c26 = cf(raw26)
rows = []
for lab, lim in [('HAND at most 10 m (main, derived from Pleiades and Gaofen-2)', None), ('HAND at most 5 m', 5.0), ('HAND at most 4.7 m (maximum of the Pleiades flooded pixels)', 4.7)]:
    d = dom if lim is None else dom & (hand <= lim + 0.0001)
    r = dict(setting=lab, analysed_km2=d.sum() * KM2, flag14_km2=(c14 & d).sum() * KM2, flag26_km2=(c26 & d).sum() * KM2, overall_share14=100 * (c14 & d).sum() / d.sum(), overall_share26=100 * (c26 & d).sum() / d.sum())
    for c, cn in CL.items():
        m = (lulc == c) & d; r['share14_' + cn] = 100 * (c14 & m).sum() / max(m.sum(), 1); r['km2_14_' + cn] = (c14 & m).sum() * KM2; r['analysed_' + cn] = m.sum() * KM2
    rows.append(r)
t = pd.DataFrame(rows); t.to_csv(os.path.join(OUT, 'revision2_terrain_from_calibration_only.csv'), index=False); print(t.round(2).T.to_string())



