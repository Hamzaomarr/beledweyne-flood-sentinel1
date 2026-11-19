"""
Fact-check test: does the Earth Engine flood rule give the same area when the reduction grid is 10 m, 20 m or 30 m,
and does it match the local 10 m numpy implementation used for calibration/validation? Same rule, same box (town raster extent).
"""
import ee, json, os, numpy as np, rasterio
from scipy import ndimage as ndi
ee.Initialize(project='YOUR_EARTH_ENGINE_PROJECT')
BASE = r'.'; P = json.load(open(os.path.join(BASE, 'outputs', 'tables', 'chosen_parameters.json')))
RAS = os.path.join(BASE, 'data', 'processed', 'town_rasters')
with rasterio.open(os.path.join(RAS, 'S1_20231021.tif')) as s: b = s.bounds; CRSS = s.crs.to_string()
ring = [[b.left, b.bottom], [b.right, b.bottom], [b.right, b.top], [b.left, b.top]]
REG = ee.Geometry.Polygon([ring], proj='EPSG:32638', geodesic=False)
col = (ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(REG).filter(ee.Filter.eq('instrumentMode', 'IW'))
       .filter(ee.Filter.eq('relativeOrbitNumber_start', 35)).filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING')))
def s1d(d): return col.filterDate(d, ee.Date(d).advance(1, 'day')).mosaic().select(['VV', 'VH'])
S = {d: s1d(d) for d in ['2023-10-09', '2023-10-21', '2023-11-14']}
print('scenes per date:', {d: col.filterDate(d, ee.Date(d).advance(1, 'day')).size().getInfo() for d in S})
pre = S['2023-10-09'].add(S['2023-10-21']).divide(2); post = S['2023-11-14']
def med(i, r): return i.focalMedian(radius=r, kernelType='square', units='pixels')
r = P['filt'] // 2
dvv = med(post.select('VV').subtract(pre.select('VV')), r); dvh = med(post.select('VH').subtract(pre.select('VH')), r)
f = dvv.lte(-P['tVV']).Or(dvh.lte(-P['tVH'])).And(med(pre.select('VV'), r).gte(P['dark_cutoff']))
valid = S['2023-10-21'].select('VV').mask().And(S['2023-11-14'].select('VV').mask())
img = f.And(valid).unmask(0).toFloat().multiply(ee.Image.pixelArea().divide(1e6)).rename('a')
res = {}
for sc in (10, 20, 30):
    G = [sc, 0, 480000, 0, -sc, 570000]
    res[sc] = img.reduceRegion(reducer=ee.Reducer.sum(), geometry=REG, crs='EPSG:32638', crsTransform=G, maxPixels=1e13, tileScale=8).getInfo()['a']
    print('EE flagged area (no terrain mask) at %d m grid: %.3f km2' % (sc, res[sc]), flush=True)
# explicit 10 m reprojection of the inputs, reduced on the 20 m grid
def at10(i): return i.reproject(crs='EPSG:32638', scale=10)
pre10, post10 = at10(pre), at10(post)
dvv10 = med(post10.select('VV').subtract(pre10.select('VV')), r); dvh10 = med(post10.select('VH').subtract(pre10.select('VH')), r)
f10 = dvv10.lte(-P['tVV']).Or(dvh10.lte(-P['tVH'])).And(med(pre10.select('VV'), r).gte(P['dark_cutoff']))
img10 = f10.And(valid).unmask(0).toFloat().multiply(ee.Image.pixelArea().divide(1e6)).rename('a')
G20 = [20, 0, 480000, 0, -20, 570000]
v = img10.reduceRegion(reducer=ee.Reducer.sum(), geometry=REG, crs='EPSG:32638', crsTransform=G20, maxPixels=1e13, tileScale=8).getInfo()['a']
print('EE flagged area with inputs reprojected to 10 m, reduced on 20 m grid: %.3f km2' % v, flush=True)
# local numpy implementation (the one used for calibration and validation)
def rd(n):
    with rasterio.open(os.path.join(RAS, n + '.tif')) as s: return s.read().astype('float32')
a9, a21, a14 = rd('S1_20231009'), rd('S1_20231021'), rd('S1_20231114')
k = P['filt']; sm = lambda a: ndi.median_filter(a, size=k, mode='nearest')
pm = (a9 + a21) / 2; dV = sm(a14[0] - pm[0]); dH = sm(a14[1] - pm[1]); dark = sm(pm[0]) < P['dark_cutoff']
fl = ((dV <= -P['tVV']) | (dH <= -P['tVH'])) & ~dark; vm = np.isfinite(a21[0]) & np.isfinite(a14[0]) & np.isfinite(a9[0])
print('local numpy 10 m flagged area (same box, no terrain mask): %.3f km2' % ((fl & vm).sum() / 1e4))
json.dump({str(k_): v_ for k_, v_ in res.items()} | {'ee_inputs_reprojected_10m_on_20m_grid': v}, open(os.path.join(BASE, 'outputs', 'tables', 'resolution_check.json'), 'w'), indent=2)
