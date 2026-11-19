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

_flood_raw = flood
MINCL = int(P['min_cluster_px'])
def flood(post, pre, tv, th, r, dark):
    f, dvv = _flood_raw(post, pre, tv, th, r, dark)
    f = f.And(S['2023-10-21'].select('VV').mask().And(S['2023-11-14'].select('VV').mask()))
    f = f.selfMask().connectedPixelCount(200, True).gte(MINCL).unmask(0)      # remove 8-connected clusters smaller than MINCL pixels
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


# ======================================================================================================
# TILED 10 m STATISTICS. Each tile is aligned to the 10 m UTM grid (origin 480000 E, 570000 N) so no pixel is counted twice.
# ======================================================================================================
import time, glob, rasterio
from concurrent.futures import ThreadPoolExecutor, as_completed
TDIR = os.path.join(BASE, 'outputs', 'tiles10m_cluster'); os.makedirs(TDIR, exist_ok=True)
GRID10 = [10, 0, 480000, 0, -10, 570000]
u = lambda m: m.unmask(0).toFloat()
area_km2 = ee.Image.pixelArea().divide(1e6)
metrics = {
    'aoi_area': ee.Image(1), 'domain_area': domain, 'flood_2Nov': F['2023-11-02'], 'flood_14Nov': f14,
    'flood_26Nov': F['2023-11-26'], 'flood_8Dec': F['2023-12-08'],
    'intensity1_14Nov': inten.eq(1), 'intensity2_14Nov': inten.eq(2), 'intensity3_14Nov': inten.eq(3),
    'persist1': persist.eq(1), 'persist2': persist.eq(2), 'persist3': persist.eq(3),
}
names = list(metrics.keys())
variants = {}
f, _ = flood(S['2023-11-14'], pre_mean, P['tVV'], P['tVH'], r_main, P['dark_cutoff']); variants['main (calibrated)'] = (f, domain)
f, _ = flood(S['2023-11-14'], pre_mean, P['tVV'], P['tVH'], r_main, None); variants['no dark exclusion'] = (f, domain)
f, _ = flood(S['2023-11-14'], pre_mean, P['tVV'], P['tVH'], r_main, P['dark_cutoff']); variants['no HAND/slope mask'] = (f, perm.Not())
f, _ = flood(S['2023-11-14'], S['2023-10-21'], P['tVV'], P['tVH'], r_main, P['dark_cutoff']); variants['pre = 21 Oct only'] = (f, domain)
f, _ = flood(S['2023-11-14'], S['2023-10-09'], P['tVV'], P['tVH'], r_main, P['dark_cutoff']); variants['pre = 9 Oct only'] = (f, domain)
f, _ = flood(S['2023-11-14'], pre_mean, P['tVV'], P['tVH'], 1, P['dark_cutoff']); variants['3x3 filter'] = (f, domain)
f, _ = flood(S['2023-11-14'], pre_mean, P['dVV_only']['tVV'], 99, r_main, P['dark_cutoff']); variants['dVV-only rule (-2.5 dB)'] = (f, domain)
f, _ = flood(S['2023-11-14'], S['2023-10-21'], 2.0, 1.5, 0, None); variants['paper-style fixed -2.0/-1.5, no filter'] = (f, domain)
vnames = list(variants.keys())
stackA = ee.Image.cat([u(metrics[n]).rename(n) for n in names]).multiply(area_km2).addBands(lulc)
stackS = ee.Image.cat([u(f_.And(m_).And(sarvalid)).rename('v%d' % i) for i, (f_, m_) in enumerate(variants.values())]).multiply(area_km2)
redA = ee.Reducer.sum().repeat(len(names)).group(groupField=len(names), groupName='class')

XS = list(range(498000, 574001, 19000)); YS = list(range(490000, 560001, 17500))
tiles = [(i, j, XS[i], YS[j], XS[i + 1], YS[j + 1]) for i in range(len(XS) - 1) for j in range(len(YS) - 1)]
def tile_geom(t):
    rect = ee.Geometry.Rectangle([t[2], t[3], t[4], t[5]], 'EPSG:32638', False)
    return AOI.intersection(rect, ee.ErrorMargin(1))
def run_tile(t):
    path = os.path.join(TDIR, 'tile_%d_%d.json' % (t[0], t[1]))
    if os.path.exists(path): return t, 'cached', 0
    t0 = time.time(); g = tile_geom(t); out = {}
    for attempt in range(3):
        try:
            out['A'] = stackA.reduceRegion(reducer=redA, geometry=g, crs=CRS, crsTransform=GRID10, maxPixels=1e13, tileScale=16).getInfo()
            out['S'] = stackS.reduceRegion(reducer=ee.Reducer.sum(), geometry=g, crs=CRS, crsTransform=GRID10, maxPixels=1e13, tileScale=16).getInfo()
            break
        except Exception as e:
            print('  tile', t[:2], 'attempt', attempt + 1, 'failed:', str(e)[:200], flush=True); time.sleep(10)
    else:
        return t, 'FAILED', time.time() - t0
    json.dump(out, open(path, 'w')); return t, 'ok', time.time() - t0
print('tiles:', len(tiles), flush=True); T0 = time.time()
with ThreadPoolExecutor(max_workers=3) as ex:
    futs = [ex.submit(run_tile, t) for t in tiles]
    for fu in as_completed(futs):
        t, st_, sec = fu.result(); print('tile %d_%d %s in %.0f s, elapsed %.0f min' % (t[0], t[1], st_, sec, (time.time() - T0) / 60), flush=True)

# ---- aggregate
files = sorted(glob.glob(os.path.join(TDIR, 'tile_*.json'))); print('tile files:', len(files), 'of', len(tiles), flush=True)
if len(files) == len(tiles):
    tot = {}; sens = {k: 0.0 for k in vnames}
    for fp in files:
        d = json.load(open(fp))
        for g in d['A'].get('groups', []):
            c = int(g['class']); row = tot.setdefault(c, {n: 0.0 for n in names})
            for n, v in zip(names, g['sum']): row[n] += v
        for i, k in enumerate(vnames): sens[k] += d['S'].get('v%d' % i, 0.0) or 0.0
    old = os.path.join(OUT, 'flood_stats_by_landcover.csv'); oldS = os.path.join(OUT, 'sensitivity_flood_area_14Nov.csv')
    rows = [dict(class_id=c, class_name=CLASSES[c], **v) for c, v in sorted(tot.items())]
    st = pd.DataFrame(rows); tt = st.drop(columns=['class_name']).sum(); tt['class_id'] = 99; tt['class_name'] = 'ALL CLASSES'
    st = pd.concat([st, pd.DataFrame([tt])], ignore_index=True)
    for c in ['flood_2Nov', 'flood_14Nov', 'flood_26Nov', 'flood_8Dec']: st['pct_domain_' + c] = 100 * st[c] / st['domain_area'].replace(0, np.nan)
    st.to_csv(old, index=False); print(st.round(2).to_string(index=False), flush=True)
    chk = st.loc[st.class_id == 99].iloc[0]
    print('check: intensity sum %.3f vs flood_14Nov %.3f' % (chk.intensity1_14Nov + chk.intensity2_14Nov + chk.intensity3_14Nov, chk.flood_14Nov), flush=True)
    sdf = pd.DataFrame({'variant': vnames, 'flooded_km2_14Nov': [sens[k] for k in vnames]}); sdf.to_csv(oldS, index=False); print(sdf.round(1).to_string(index=False), flush=True)
    # consistency check against the town-box test (script 15): expect about 51.163 km2 for the rule without terrain mask on the town raster extent
    with rasterio.open(os.path.join(BASE, 'data', 'processed', 'town_rasters', 'S1_20231021.tif')) as s_: bb = s_.bounds
    REG = ee.Geometry.Polygon([[[bb.left, bb.bottom], [bb.right, bb.bottom], [bb.right, bb.top], [bb.left, bb.top]]], proj='EPSG:32638', geodesic=False)
    fr, _ = flood(S['2023-11-14'], pre_mean, P['tVV'], P['tVH'], r_main, P['dark_cutoff'])
    v = u(fr.And(sarvalid)).multiply(area_km2).rename('a').reduceRegion(reducer=ee.Reducer.sum(), geometry=REG, crs=CRS, crsTransform=GRID10, maxPixels=1e13, tileScale=16).getInfo()['a']
    print('town-box consistency check, pipeline of this script at 10 m: %.3f km2 (script 15 gave 51.163 for the 9+21 Oct mean pre-event reference without terrain mask)' % v, flush=True)
print('done', flush=True)