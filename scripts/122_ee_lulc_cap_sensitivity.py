"""Sensitivity of the land-cover spatial block cross-validation to the per-class point cap (sample size) and to the sampling seed."""
import ee, json, os, numpy as np
ee.Initialize(project='YOUR_EARTH_ENGINE_PROJECT')
B = r'.'; OUT = os.path.join(B, 'outputs', 'tables')
AOI = ee.Geometry.Rectangle([45.00, 4.45, 45.65, 5.05])
def mask_s2(i):
    scl = i.select('SCL'); ok = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(11)); return i.updateMask(ok).select(['B2', 'B3', 'B4', 'B8', 'B11']).divide(10000)
s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(AOI).filterDate('2023-01-01', '2023-03-15').filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)).map(mask_s2)
comp = s2.median().clip(AOI); comp = comp.addBands([comp.normalizedDifference(['B8', 'B4']).rename('NDVI'), comp.normalizedDifference(['B3', 'B11']).rename('MNDWI'), comp.normalizedDifference(['B11', 'B8']).rename('NDBI')])
FEATS = ['B2', 'B3', 'B4', 'B8', 'B11', 'NDVI', 'MNDWI', 'NDBI']
wc = ee.ImageCollection('ESA/WorldCover/v200').first().select('Map'); dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterBounds(AOI).filterDate('2023-01-01', '2023-03-15').select('label').mode()
wc5 = wc.remap([10, 20, 30, 40, 50, 60, 80], [2, 2, 2, 1, 3, 4, 0]); dw5 = dw.remap([0, 1, 2, 4, 5, 6, 7], [0, 2, 2, 1, 2, 3, 4]); cons = wc5.updateMask(wc5.eq(dw5)).rename('label')
def blk(f):
    c = f.geometry().coordinates(); return f.set('blk', ee.Number(c.get(0)).divide(0.05).floor().add(ee.Number(c.get(1)).divide(0.05).floor()).mod(5))
def stats(cm):
    n = cm.sum(); po = np.trace(cm) / n; pe = (cm.sum(0) * cm.sum(1)).sum() / n ** 2
    return dict(OA=po, kappa=(po - pe) / (1 - pe), built_prod=cm[3, 3] / cm[3].sum(), built_user=cm[3, 3] / cm[:, 3].sum(), crop_prod=cm[1, 1] / cm[1].sum(), crop_user=cm[1, 1] / cm[:, 1].sum(), n=int(n))
res = []
for cap, seed in [(100, 42), (250, 42), (500, 42), (1000, 42), (500, 1), (500, 2)]:
    pts = cons.addBands(comp.select(FEATS)).stratifiedSample(numPoints=0, classBand='label', region=AOI, scale=10, seed=seed, classValues=[0, 1, 2, 3, 4], classPoints=[cap] * 5, geometries=True, tileScale=4).map(blk)
    cm_sum = np.zeros((5, 5))
    for k in range(5):
        tr_, te_ = pts.filter(ee.Filter.neq('blk', k)), pts.filter(ee.Filter.eq('blk', k))
        rf = ee.Classifier.smileRandomForest(numberOfTrees=500, seed=42).train(tr_, 'label', FEATS)
        cm_sum += np.array(te_.classify(rf).errorMatrix('label', 'classification', [0, 1, 2, 3, 4]).array().getInfo())
    r = stats(cm_sum); r.update(cap=cap, seed=seed); res.append(r); print(r, flush=True)
    json.dump(res, open(os.path.join(OUT, 'revision2_lulc_cap_sensitivity.json'), 'w'), indent=1)
