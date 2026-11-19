import os, json, glob, numpy as np, pandas as pd, rasterio, geopandas as gpd, ee
from rasterio import features
from scipy import ndimage as ndi
ee.Initialize(project='YOUR_EARTH_ENGINE_PROJECT')
B = r'.'; OUT = os.path.join(B, 'outputs', 'tables')
AOI = ee.Geometry.Rectangle([45.00, 4.45, 45.65, 5.05])
# HAND independent check: fraction of unmasked MERIT hnd pixels over the rectangle, and count of exact zeros
hnd = ee.Image('MERIT/Hydro/v1_0_1').select('hnd')
r = hnd.mask().reduceRegion(ee.Reducer.mean(), AOI, 90, maxPixels=1e9).getInfo(); z = hnd.eq(0).selfMask().reduceRegion(ee.Reducer.count(), AOI, 90, maxPixels=1e9).getInfo()
print('HAND unmasked fraction over rectangle:', r, '| pixels with HAND exactly 0:', z, flush=True)
# land-cover sample distribution (same call and seed as the pipeline)
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
pts = pts.map(blk); train, test = pts.filter(ee.Filter.neq('blk', 0)), pts.filter(ee.Filter.eq('blk', 0))
tr_h = train.aggregate_histogram('label').getInfo(); te_h = test.aggregate_histogram('label').getInfo(); al_h = pts.aggregate_histogram('label').getInfo()
print('sampled', al_h, 'train', tr_h, 'test', te_h, flush=True)
json.dump(dict(sampled=al_h, train=tr_h, test=te_h), open(os.path.join(OUT, 'revision_lulc_sample_counts.json'), 'w'))
