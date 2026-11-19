import ee, json, os, numpy as np, pandas as pd, rasterio
from scipy import ndimage as ndi
from pyproj import Transformer
ee.Initialize(project='YOUR_EARTH_ENGINE_PROJECT')
B = r'.'; OUT = os.path.join(B, 'outputs', 'tables'); RAW = os.path.join(B, 'data', 'processed', 'raw10m')
AOI = ee.Geometry.Rectangle([45.00, 4.45, 45.65, 5.05])
# ---------- 1. five-fold spatial block cross-validation of the same classifier design (every sampled point is tested once)
def mask_s2(i):
    scl = i.select('SCL'); ok = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(11)); return i.updateMask(ok).select(['B2', 'B3', 'B4', 'B8', 'B11']).divide(10000)
s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(AOI).filterDate('2023-01-01', '2023-03-15').filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)).map(mask_s2)
comp = s2.median().clip(AOI); comp = comp.addBands([comp.normalizedDifference(['B8', 'B4']).rename('NDVI'), comp.normalizedDifference(['B3', 'B11']).rename('MNDWI'), comp.normalizedDifference(['B11', 'B8']).rename('NDBI')])
FEATS = ['B2', 'B3', 'B4', 'B8', 'B11', 'NDVI', 'MNDWI', 'NDBI']
wc = ee.ImageCollection('ESA/WorldCover/v200').first().select('Map'); dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterBounds(AOI).filterDate('2023-01-01', '2023-03-15').select('label').mode()
wc5 = wc.remap([10, 20, 30, 40, 50, 60, 80], [2, 2, 2, 1, 3, 4, 0]); dw5 = dw.remap([0, 1, 2, 4, 5, 6, 7], [0, 2, 2, 1, 2, 3, 4]); cons = wc5.updateMask(wc5.eq(dw5)).rename('label')
pts = cons.addBands(comp.select(FEATS)).stratifiedSample(numPoints=0, classBand='label', region=AOI, scale=10, seed=42, classValues=[0, 1, 2, 3, 4], classPoints=[500] * 5, geometries=True, tileScale=4)
def blk(f):
    c = f.geometry().coordinates(); return f.set('blk', ee.Number(c.get(0)).divide(0.05).floor().add(ee.Number(c.get(1)).divide(0.05).floor()).mod(5))
pts = pts.map(blk); cm_sum = np.zeros((5, 5)); per_fold = []
for k in range(5):
    tr_, te_ = pts.filter(ee.Filter.neq('blk', k)), pts.filter(ee.Filter.eq('blk', k))
    rf = ee.Classifier.smileRandomForest(numberOfTrees=500, seed=42).train(tr_, 'label', FEATS)
    cm = te_.classify(rf).errorMatrix('label', 'classification', [0, 1, 2, 3, 4]); a = np.array(cm.array().getInfo()); cm_sum += a; per_fold.append(a.sum(1).tolist()); print('fold', k, a.sum(1).tolist(), flush=True)
def stats(cm):
    n = cm.sum(); po = np.trace(cm) / n; pe = (cm.sum(0) * cm.sum(1)).sum() / n ** 2
    return dict(OA=po, kappa=(po - pe) / (1 - pe), producers=(np.diag(cm) / cm.sum(1)).tolist(), users=(np.diag(cm) / cm.sum(0)).tolist(), n_ref=cm.sum(1).tolist(), n=int(n))
r = stats(cm_sum); r['confusion'] = cm_sum.tolist(); r['per_fold_reference_counts'] = per_fold; json.dump(r, open(os.path.join(OUT, 'revision_lulc_blockcv.json'), 'w'), indent=1)
print({k: (np.round(v, 3).tolist() if isinstance(v, list) else round(v, 3)) for k, v in r.items() if k in ('OA', 'kappa', 'producers', 'users', 'n_ref', 'n')}, flush=True)
# ---------- 2. independent check of the built-up class against Open Buildings v3 centroids
ob = ee.FeatureCollection('GOOGLE/Research/open-buildings/v3/polygons').filterBounds(AOI).filter(ee.Filter.gte('confidence', 0.7)).randomColumn('rc', 7)
xy = []
for i in range(20):
    sl = ob.filter(ee.Filter.And(ee.Filter.gte('rc', i / 20), ee.Filter.lt('rc', (i + 1) / 20)))
    fc = sl.map(lambda f: ee.Feature(None, {'x': ee.List(f.get('longitude_latitude').get('coordinates') if False else f.geometry().centroid(1).coordinates()).get(0), 'y': ee.List(f.geometry().centroid(1).coordinates()).get(1)})).getInfo()['features']
    xy += [(g['properties']['x'], g['properties']['y']) for g in fc]; print('slice', i, len(xy), flush=True)
np.save(os.path.join(B, 'data', 'processed', 'diag', 'open_buildings_centroids.npy'), np.array(xy)); print('buildings', len(xy))
