"""Clip the 10 m map rasters to the study rectangle (45.00-45.65 E, 4.45-5.05 N). The tile download covered a padded UTM rectangle."""
import os, glob, numpy as np, rasterio
from rasterio import features
from shapely.geometry import Polygon
from pyproj import Transformer
D = r'.\data\processed\aoi_rasters10m'
def ring(x0, y0, x1, y1, n=400):
    xs = np.linspace(x0, x1, n); ys = np.linspace(y0, y1, n)
    return list(zip(xs, np.full(n, y0))) + list(zip(np.full(n, x1), ys)) + list(zip(xs[::-1], np.full(n, y1))) + list(zip(np.full(n, x0), ys[::-1]))
tf = Transformer.from_crs('EPSG:4326', 'EPSG:32638', always_xy=True)
poly = Polygon([tf.transform(x, y) for x, y in ring(45.00, 4.45, 45.65, 5.05)])
for p in sorted(glob.glob(os.path.join(D, '*.tif'))):
    with rasterio.open(p) as s:
        a = s.read(1); prof = s.profile; tr = s.transform
    m = features.rasterize([(poly, 1)], out_shape=a.shape, transform=tr, fill=0, dtype='uint8').astype(bool)
    a[~m] = 0
    with rasterio.open(p, 'w', **prof) as d: d.write(a, 1)
    px = abs(tr.a * tr.e) / 1e6; u, c = np.unique(a, return_counts=True)
    print(os.path.basename(p), {int(k): round(float(v) * px, 1) for k, v in zip(u, c)}, flush=True)
