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
f14u = f14.unmask(0).toByte()
inten = f14u.add(f14.And(dv.lte(-5)).unmask(0).toByte()).add(f14.And(dv.lte(-7)).unmask(0).toByte()).rename('intensity')   # 0 none,1 weak,2 moderate,3 strong; built arithmetically so classes sum to the flood mask
persist = F['2023-11-14'].add(F['2023-11-26']).add(F['2023-12-08']).rename('persistence')   # dates flagged, 0..3

import time, rasterio
from rasterio.merge import merge
# ---- only the intensity chunk is recomputed (other columns of flood_stats_by_landcover.csv come from the run07 pass)
u = lambda m: m.unmask(0).toFloat()
GRID = [20, 0, 480000, 0, -20, 570000]
names = ['intensity1_14Nov', 'intensity2_14Nov', 'intensity3_14Nov']
mm = {'intensity1_14Nov': inten.eq(1), 'intensity2_14Nov': inten.eq(2), 'intensity3_14Nov': inten.eq(3), 'flood_14Nov': f14}
by = {}
for chunk in (names, ['flood_14Nov']):
    stk = ee.Image.cat([u(mm[n]).rename(n) for n in chunk]).multiply(ee.Image.pixelArea().divide(1e6)).addBands(lulc)
    r = stk.reduceRegion(reducer=ee.Reducer.sum().repeat(len(chunk)).group(groupField=len(chunk), groupName='class'),
                         geometry=AOI, crs=CRS, crsTransform=GRID, maxPixels=1e13, tileScale=16).getInfo()
    for g in r['groups']:
        by.setdefault(int(g['class']), {}).update({n: v for n, v in zip(chunk, g['sum'])})
    print('stats chunk', chunk, 'done', flush=True)
st = pd.read_csv(os.path.join(OUT, 'flood_stats_by_landcover.csv'))
for cid, d in by.items():
    for n, v in d.items(): st.loc[st.class_id == cid, 'recheck_' + n if n == 'flood_14Nov' else n] = v
tot = st.class_id != 99
for n in names + ['recheck_flood_14Nov']: st.loc[st.class_id == 99, n] = st.loc[tot, n].sum()
st.to_csv(os.path.join(OUT, 'flood_stats_by_landcover.csv'), index=False)
print(st[['class_name', 'flood_14Nov', 'recheck_flood_14Nov'] + names].round(2).to_string(index=False))
print('sum of intensity classes (all) =', round(st.loc[st.class_id == 99, names].sum(axis=1).iloc[0], 2), ' flood_14Nov (recheck, same pass) =', round(st.loc[st.class_id == 99, 'recheck_flood_14Nov'].iloc[0], 2), flush=True)

# ---- rasters for figures: 30 m, tiled (one band, one tile per request) to stay under the EE memory limit
NX, NY = 4, 4
x0, y0, x1, y1 = 45.00, 4.45, 45.65, 5.05
def fetch_tile(img, box, path):
    for attempt in range(3):
        try:
            url = img.getDownloadURL({'region': ee.Geometry.Rectangle(box), 'scale': 30, 'crs': CRS, 'format': 'GEO_TIFF'})
            r = requests.get(url, timeout=900)
            if r.status_code == 200:
                data = r.content
                if data[:2] == b'PK':
                    z = zipfile.ZipFile(io.BytesIO(data)); data = z.read(z.namelist()[0])
                open(path, 'wb').write(data); return True
            err = r.text[:200]
        except Exception as e: err = str(e)[:200]
        time.sleep(5)
    print('  tile failed', os.path.basename(path), err, flush=True); return False
def fetch(img, name):
    tdir = os.path.join(RASTER_OUT, '_tiles_' + name); os.makedirs(tdir, exist_ok=True); paths = []; ok = True
    for ix in range(NX):
        for iy in range(NY):
            box = [x0 + (x1 - x0) * ix / NX, y0 + (y1 - y0) * iy / NY, x0 + (x1 - x0) * (ix + 1) / NX, y0 + (y1 - y0) * (iy + 1) / NY]
            p = os.path.join(tdir, '%d_%d.tif' % (ix, iy))
            if fetch_tile(img, box, p): paths.append(p)
            else: ok = False
    if not ok: print('DOWNLOAD INCOMPLETE', name, flush=True); return
    srcs = [rasterio.open(p) for p in paths]; arr, tr = merge(srcs); prof = srcs[0].profile
    prof.update(height=arr.shape[1], width=arr.shape[2], transform=tr, compress='deflate')
    out = os.path.join(RASTER_OUT, name + '.tif')
    with rasterio.open(out, 'w', **prof) as dst: dst.write(arr)
    for s_ in srcs: s_.close()
    print('saved', name, arr.shape, round(os.path.getsize(out) / 1e6, 1), 'MB', flush=True)
b = lambda m: m.unmask(0).toByte()
jobs = [('f_14Nov', b(f14)), ('intensity', inten.toByte()), ('lulc', lulc), ('domain', b(domain)), ('perm_water', b(perm)), ('f_2Nov', b(F['2023-11-02'])),
        ('f_26Nov', b(F['2023-11-26'])), ('f_8Dec', b(F['2023-12-08'])), ('persistence', persist.toByte())]
for nm, im in jobs: fetch(im.rename(nm).unmask(0).toByte() if nm == 'lulc' else im.rename(nm), nm)
print('done', flush=True)

