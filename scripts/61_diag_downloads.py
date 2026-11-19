"""Small diagnostic downloads for the revision: (1) MERIT Hydro HAND missing-data mask on a 90 m grid, (2) Sentinel-1 VV and VH on a 100 m grid (10 m pixels averaged in dB, 10 x 10) for four dates,
(3) CHIRPS daily rainfall averaged over the study rectangle. All aligned to the 10 m analysis grid (origin 498000 E, 560000 N)."""
import ee, io, zipfile, requests, os, json, numpy as np, rasterio
ee.Initialize(project='YOUR_EARTH_ENGINE_PROJECT')
B = r'.'; OUT = os.path.join(B, 'data', 'processed', 'diag'); os.makedirs(OUT, exist_ok=True)
CRS = 'EPSG:32638'; REG = ee.Geometry.Rectangle([498000, 490000, 574000, 560000], CRS, False)
AOI = ee.Geometry.Rectangle([45.00, 4.45, 45.65, 5.05])
def dl(img, name, scale, w, h):
    url = img.getDownloadURL(dict(region=REG, crs=CRS, crsTransform=[scale, 0, 498000, 0, -scale, 560000], dimensions='%dx%d' % (w, h), format='GEO_TIFF'))
    r = requests.get(url, timeout=900); print(r.status_code, r.text[:500] if r.status_code != 200 else '', flush=True); r.raise_for_status(); p = os.path.join(OUT, name + '.tif'); open(p, 'wb').write(r.content)
    with rasterio.open(p) as s: print(name, s.shape, s.count, s.dtypes[0], flush=True)
hnd = ee.Image('MERIT/Hydro/v1_0_1').select('hnd')
if not os.path.exists(os.path.join(OUT, 'hand_missing_90m.tif')): dl(hnd.mask().Not().rename('hand_missing').toByte(), 'hand_missing_90m', 90, 845, 778)
col = (ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(AOI).filter(ee.Filter.eq('instrumentMode', 'IW')).filter(ee.Filter.eq('relativeOrbitNumber_start', 35)).filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING')))
bands = []
for d, n in [('2023-10-09', 'o09'), ('2023-10-21', 'o21'), ('2023-11-02', 'n02'), ('2023-11-14', 'n14')]:
    im = col.filterDate(d, ee.Date(d).advance(1, 'day')).mosaic().select(['VV', 'VH']).rename([n + '_VV', n + '_VH'])
    im = im.reproject(CRS, [10, 0, 498000, 0, -10, 560000]).reduceResolution(ee.Reducer.mean(), False, 256).reproject(CRS, [100, 0, 498000, 0, -100, 560000])
    bands.append(im)
dl(ee.Image.cat(bands).toFloat(), 's1_100m_means', 100, 760, 700)
ch = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY').filterDate('2023-09-15', '2023-11-16')
def f(i): return ee.Feature(None, dict(date=i.date().format('YYYY-MM-dd'), mm=i.reduceRegion(ee.Reducer.mean(), AOI, 5566, maxPixels=1e9).get('precipitation')))
rows = ch.map(f).getInfo()['features']; r = [(x['properties']['date'], x['properties']['mm']) for x in rows]
json.dump(r, open(os.path.join(OUT, 'chirps_daily_mm.json'), 'w')); print(len(r), 'chirps days', flush=True)
