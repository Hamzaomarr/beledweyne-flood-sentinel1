import os, numpy as np, rasterio
from scipy import ndimage as ndi
from pyproj import Transformer
B = r'.'; RAW = os.path.join(B, 'data', 'processed', 'raw10m')
with rasterio.open(os.path.join(RAW, 'lulc.tif')) as s: lulc = s.read(1).astype('uint8'); tr = s.transform
with rasterio.open(os.path.join(RAW, 'domain.tif')) as s: dom = s.read(1).astype(bool)
H, W = lulc.shape
xy = np.load(os.path.join(B, 'data', 'processed', 'diag', 'open_buildings_centroids.npy')); tf = Transformer.from_crs('EPSG:4326', 'EPSG:32638', always_xy=True); X, Y = tf.transform(xy[:, 0], xy[:, 1])
c = ((np.array(X) - tr.c) / 10).astype(int); r = ((tr.f - np.array(Y)) / 10).astype(int); bm = np.zeros((H, W), bool); bm[r, c] = True
d = ndi.distance_transform_edt(~bm) * 10; b = lulc == 3
bins = [0, 50, 100, 250, 500, 1000, 1e9]; h = np.histogram(d[b], bins)[0]; print('mapped built-up pixels by distance to nearest building centroid (m):', dict(zip(['<=50', '50-100', '100-250', '250-500', '500-1000', '>1000'], (100 * h / h.sum()).round(1))), 'km2', (h * 1e-4).round(1))
# where are they: 5 km blocks
bl = 500; rr, cc = np.where(b); import collections
cnt = collections.Counter(zip(rr // bl, cc // bl)); top = cnt.most_common(8); print('top 5 km blocks (row,col):count km2', [(k, round(v * 1e-4, 1)) for k, v in top])
bc = collections.Counter(zip(r // bl, c // bl)); print('buildings in those blocks', [(k, bc.get(k, 0)) for k, _ in top])
# building-centroid density per 5 km block vs built-up km2
tot_b = sum(cnt.values()) * 1e-4; print('total built-up', tot_b)
