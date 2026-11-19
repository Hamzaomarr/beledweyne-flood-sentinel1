"""Recomputes the nesting of the footprints obtained with the 9 October, main and 21 October pre-event references (copy of the setup in script 64) and stores the result."""
import os, json, numpy as np, rasterio
from rasterio import features
from scipy import ndimage as ndi
from shapely.geometry import Polygon
from pyproj import Transformer
B = r'.'; RAW = os.path.join(B, 'data', 'processed', 'raw10m'); OUT = os.path.join(B, 'outputs', 'tables')
P = json.load(open(os.path.join(OUT, 'chosen_parameters.json'))); MIN = int(P['min_cluster_px'])
def rd(n):
    with rasterio.open(os.path.join(RAW, n + '.tif')) as s: return s.read(1), s.transform
lulc, tr = rd('lulc'); H, W = lulc.shape
tf = Transformer.from_crs('EPSG:4326', 'EPSG:32638', always_xy=True)
def ring(x0, y0, x1, y1, n=400):
    xs = np.linspace(x0, x1, n); ys = np.linspace(y0, y1, n)
    return list(zip(xs, np.full(n, y0))) + list(zip(np.full(n, x1), ys)) + list(zip(xs[::-1], np.full(n, y1))) + list(zip(np.full(n, x0), ys[::-1]))
poly = Polygon([tf.transform(x, y) for x, y in ring(45.00, 4.45, 45.65, 5.05)])
aoi = features.rasterize([(poly, 1)], out_shape=(H, W), transform=tr, fill=0, dtype='uint8').astype(bool)
dom = rd('domain')[0].astype(bool) & aoi
def cf(f):
    lab, n = ndi.label(f, structure=np.ones((3, 3))); sz = np.bincount(lab.ravel()); keep = sz >= MIN; keep[0] = False; return keep[lab]
F14 = cf(rd('flag_14Nov')[0].astype(bool) & aoi) & dom; A21 = cf(rd('v_pre21')[0].astype(bool) & aoi) & dom; A9 = cf(rd('v_pre9')[0].astype(bool) & aoi) & dom
r = dict(pre9_inside_main_pct=100 * (A9 & F14).sum() / A9.sum(), main_inside_pre21_pct=100 * (F14 & A21).sum() / F14.sum(), main_km2=F14.sum() * 1e-4, pre21_km2=A21.sum() * 1e-4, pre9_km2=A9.sum() * 1e-4,
         pre21_not_main_km2=(A21 & ~F14).sum() * 1e-4)
json.dump(r, open(os.path.join(OUT, 'revision_nested_footprints.json'), 'w'), indent=1); print(r)
