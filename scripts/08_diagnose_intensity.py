"""
Full-area analysis (Earth Engine, executed from Python). Uses parameters calibrated in 03/04 and tests from 05.
Option (b) land cover: labels = pixels where ESA WorldCover 2021 and Dynamic World (Jan-Mar 2023 mode) AGREE.
All accuracy figures are therefore agreement with that consensus, NOT ground truth.
"""
import ee, json, os, io, zipfile, requests, numpy as np, pandas as pd
ee.Initialize(project='YOUR_EARTH_ENGINE_PROJECT')
BASE = r'.'
OUT = os.path.join(BASE, 'outputs', 'tables'); RASTER_OUT = os.path.join(BASE, 'data', 'processed', 'aoi_rasters')
os.makedirs(OUT, exist_ok=True); os.makedirs(RASTER_OUT, exist_ok=True)
P = json.load(open(os.path.join(OUT, 'chosen_parameters.json')))
print('parameters:', P)
AOI = ee.Geometry.Rectangle([45.00, 4.45, 45.65, 5.05]); CRS = 'EPSG:32638'
CLASSES = {0: 'Permanent water', 1: 'Cropland', 2: 'Vegetation / rangeland', 3: 'Built-up', 4: 'Bare soil / sand'}

# ------------------------------------------------------------------ land cover (option b)
def mask_s2(i):
    scl = i.select('SCL'); ok = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(11))
    return i.updateMask(ok).select(['B2', 'B3', 'B4', 'B8', 'B11']).divide(10000)
s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(AOI).filterDate('2023-01-01', '2023-03-15')
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)).map(mask_s2))
n_s2 = s2.size().getInfo(); print('S2 scenes in composite:', n_s2)
comp = s2.median().clip(AOI)
comp = comp.addBands([comp.normalizedDifference(['B8', 'B4']).rename('NDVI'),
                      comp.normalizedDifference(['B3', 'B11']).rename('MNDWI'),
                      comp.normalizedDifference(['B11', 'B8']).rename('NDBI')])
FEATS = ['B2', 'B3', 'B4', 'B8', 'B11', 'NDVI', 'MNDWI', 'NDBI']

wc = ee.ImageCollection('ESA/WorldCover/v200').first().select('Map')
dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterBounds(AOI).filterDate('2023-01-01', '2023-03-15').select('label').mode()
wc5 = wc.remap([10, 20, 30, 40, 50, 60, 80], [2, 2, 2, 1, 3, 4, 0])
dw5 = dw.remap([0, 1, 2, 4, 5, 6, 7], [0, 2, 2, 1, 2, 3, 4])
consensus = wc5.updateMask(wc5.eq(dw5)).rename('label')
pts = consensus.addBands(comp.select(FEATS)).stratifiedSample(
    numPoints=0, classBand='label', region=AOI, scale=10, seed=42, classValues=[0, 1, 2, 3, 4],
    classPoints=[500] * 5, geometries=True, tileScale=4)
def blk(f):
    c = f.geometry().coordinates()
    return f.set('blk', ee.Number(c.get(0)).divide(0.05).floor().add(ee.Number(c.get(1)).divide(0.05).floor()).mod(5))
pts = pts.map(blk)
train, test = pts.filter(ee.Filter.neq('blk', 0)), pts.filter(ee.Filter.eq('blk', 0))
print('train per class', train.aggregate_histogram('label').getInfo()); print('test per class (spatial hold-out blocks)', test.aggregate_histogram('label').getInfo())
rf = ee.Classifier.smileRandomForest(numberOfTrees=500, seed=42).train(train, 'label', FEATS)
lulc = comp.select(FEATS).classify(rf).rename('lulc').toByte()
cm = test.classify(rf).errorMatrix('label', 'classification', [0, 1, 2, 3, 4])
acc = dict(overall_accuracy=cm.accuracy().getInfo(), kappa=cm.kappa().getInfo(),
           producers=np.array(cm.producersAccuracy().getInfo()).ravel().tolist(),
           users=np.array(cm.consumersAccuracy().getInfo()).ravel().tolist(), confusion=cm.array().getInfo(),
           note='Agreement with WorldCover/DynamicWorld consensus labels on spatially blocked hold-out, NOT ground truth')
json.dump(acc, open(os.path.join(OUT, 'lulc_accuracy_vs_consensus.json'), 'w'), indent=2)
print('LULC OA %.3f kappa %.3f' % (acc['overall_accuracy'], acc['kappa']))

# ------------------------------------------------------------------ SAR flood
col = (ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(AOI).filter(ee.Filter.eq('instrumentMode', 'IW'))
       .filter(ee.Filter.eq('relativeOrbitNumber_start', 35)).filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING')))
def s1d(d): return col.filterDate(d, ee.Date(d).advance(1, 'day')).mosaic().select(['VV', 'VH'])
S = {d: s1d(d) for d in ['2023-10-09', '2023-10-21', '2023-11-02', '2023-11-14', '2023-11-26', '2023-12-08']}
pre_mean = S['2023-10-09'].add(S['2023-10-21']).divide(2)
def med(i, r): return i.focalMedian(radius=r, kernelType='square', units='pixels') if r > 0 else i

def flood(post, pre, tv, th, r, dark):
    dvv, dvh = med(post.select('VV').subtract(pre.select('VV')), r), med(post.select('VH').subtract(pre.select('VH')), r)
    f = dvv.lte(-tv).Or(dvh.lte(-th))
    if dark is not None: f = f.And(med(pre.select('VV'), r).gte(dark))
    return f, dvv

r_main = P['filt'] // 2          # 5x5 window -> radius 2 px
hand = ee.Image('MERIT/Hydro/v1_0_1').select('hnd').unmask(0)
dem = ee.ImageCollection('COPERNICUS/DEM/GLO30').select('DEM').mosaic().setDefaultProjection('EPSG:4326', None, 30.9)
slope = ee.Terrain.slope(dem)
jrc = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('occurrence').unmask(0)
HAND_MAX, SLOPE_MAX = 10, 8      # data-derived: max HAND of UNOSAT-flooded pixels = 10 m; slope p99 = 8.2 deg (script 03)
perm = lulc.eq(0).Or(jrc.gte(75))
terrain_ok = hand.lte(HAND_MAX).And(slope.lte(SLOPE_MAX))
domain = perm.Not().And(terrain_ok)
sarvalid = S['2023-10-21'].select('VV').mask().And(S['2023-11-14'].select('VV').mask())

F = {}; DVV = {}
for d in ['2023-11-02', '2023-11-14', '2023-11-26', '2023-12-08']:
    f, dvv = flood(S[d], pre_mean, P['tVV'], P['tVH'], r_main, P['dark_cutoff']); F[d] = f.And(domain).And(sarvalid); DVV[d] = dvv
f14 = F['2023-11-14']
# intensity classes of radar change on 14 Nov, from script 05 (P(flooded) plateaus beyond ~-7 dB): 1: > -5, 2: -5..-7, 3: <= -7
dv = DVV['2023-11-14']
inten = ee.Image(0).where(f14, 1).where(f14.And(dv.lte(-5)), 2).where(f14.And(dv.lte(-7)), 3).rename('intensity')
persist = F['2023-11-14'].add(F['2023-11-26']).add(F['2023-12-08']).rename('persistence')   # dates flagged, 0..3


import time
SUB = ee.Geometry.Rectangle([45.20, 4.70, 45.35, 4.85])
GRID = [20, 0, 480000, 0, -20, 570000]
sa = ee.Image.pixelArea().divide(1e6)
u = lambda m: m.unmask(0).toFloat()
dv_le5 = dv.lte(-5); dv_le7 = dv.lte(-7)
bands = {'f14': f14, 'inten_gt0': inten.gt(0), 'i1': inten.eq(1), 'i2': inten.eq(2), 'i3': inten.eq(3),
         'f14_and_ge5': f14.And(dv_le5), 'f14_and_ge7': f14.And(dv_le7), 'f14_dvmasked': f14.And(dv.mask()), 'f14_notdvmask': f14.And(dv.mask().Not())}
stk = ee.Image.cat([u(v).rename(k) for k, v in bands.items()]).multiply(sa)
r = stk.reduceRegion(reducer=ee.Reducer.sum(), geometry=SUB, crs=CRS, crsTransform=GRID, maxPixels=1e13, tileScale=8).getInfo()
for k, v in r.items(): print(k, round(v, 3))
print('i1+i2+i3 =', round(r['i1'] + r['i2'] + r['i3'], 3))
