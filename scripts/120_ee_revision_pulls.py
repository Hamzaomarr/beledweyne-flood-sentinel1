"""Reviewer-driven Earth Engine pulls: CHIRPS daily rainfall 9 Nov-8 Dec, HAND and slope on native grids, consensus built-up counts per 0.05 degree cell."""
import ee, json, os, io, requests, numpy as np
ee.Initialize(project='YOUR_EARTH_ENGINE_PROJECT')
B = r'.'; DG = os.path.join(B, 'data', 'processed', 'diag'); OUT = os.path.join(B, 'outputs', 'tables')
AOI = ee.Geometry.Rectangle([45.00, 4.45, 45.65, 5.05], proj='EPSG:4326', geodesic=False)
# 1. CHIRPS daily mean over the rectangle
ch = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY').filterDate('2023-11-09', '2023-12-09').select('precipitation')
def f(i): return ee.Feature(None, {'d': i.date().format('YYYY-MM-dd'), 'mm': i.reduceRegion(ee.Reducer.mean(), AOI, 5566, maxPixels=1e9).get('precipitation')})
rows = [(x['properties']['d'], x['properties']['mm']) for x in ch.map(f).getInfo()['features']]
json.dump(rows, open(os.path.join(DG, 'chirps_daily_mm_nov_dec.json'), 'w')); print('chirps', len(rows), rows[:3])
# 2. HAND (MERIT, 3 arcsec) and slope (GLO-30, 1 arcsec) on native grids
def dl(img, step, name):
    n_x = int(round(0.65 / step)); n_y = int(round(0.60 / step))
    url = img.getDownloadURL({'region': AOI, 'crs': 'EPSG:4326', 'crsTransform': [step, 0, 45.00, 0, -step, 5.05], 'format': 'GEO_TIFF'})
    r = requests.get(url, timeout=600); r.raise_for_status(); open(os.path.join(DG, name), 'wb').write(r.content); print(name, len(r.content))
hand = ee.Image('MERIT/Hydro/v1_0_1').select('hnd').unmask(0).float()
dl(hand, 3 / 3600, 'hand_native.tif')
dem = ee.ImageCollection('COPERNICUS/DEM/GLO30').select('DEM').mosaic().setDefaultProjection('EPSG:4326', None, 30.9)
dl(ee.Terrain.slope(dem).float(), 1 / 3600, 'slope_native.tif')
# 3. consensus pixel counts per 0.05 degree cell, by class
wc = ee.ImageCollection('ESA/WorldCover/v200').first().select('Map'); dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterBounds(AOI).filterDate('2023-01-01', '2023-03-15').select('label').mode()
wc5 = wc.remap([10, 20, 30, 40, 50, 60, 80], [2, 2, 2, 1, 3, 4, 0]); dw5 = dw.remap([0, 1, 2, 4, 5, 6, 7], [0, 2, 2, 1, 2, 3, 4]); cons = wc5.updateMask(wc5.eq(dw5))
ll = ee.Image.pixelLonLat(); cell = ll.select('longitude').divide(0.05).floor().subtract(900).multiply(100).add(ll.select('latitude').divide(0.05).floor().subtract(89)).rename('cell').toInt()
res = {}
for c in range(5):
    im = cons.eq(c).selfMask().rename('n').addBands(cell)
    g = im.reduceRegion(ee.Reducer.count().group(groupField=1, groupName='cell'), AOI, 10, maxPixels=1e11, tileScale=8).getInfo()['groups']
    res[c] = {int(x['cell']): x['count'] for x in g}; print('class', c, len(res[c]), 'cells', sum(res[c].values()), 'pixels', flush=True)
json.dump(res, open(os.path.join(OUT, 'revision_consensus_counts_by_cell.json'), 'w'))
