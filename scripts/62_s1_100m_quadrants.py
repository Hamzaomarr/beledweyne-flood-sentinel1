"""Sentinel-1 VV and VH on a 100 m grid (10 m pixels averaged in dB), fetched in 4 quadrants per date because a single request exceeds the Earth Engine memory limit."""
import ee, requests, os, numpy as np, rasterio, json, io
ee.Initialize(project='YOUR_EARTH_ENGINE_PROJECT')
B = r'.'; OUT = os.path.join(B, 'data', 'processed', 'diag'); CRS = 'EPSG:32638'
AOI = ee.Geometry.Rectangle([45.00, 4.45, 45.65, 5.05])
col = (ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(AOI).filter(ee.Filter.eq('instrumentMode', 'IW')).filter(ee.Filter.eq('relativeOrbitNumber_start', 35)).filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING')))
W, H = 760, 700; arr = {}
for d, n in [('2023-10-09', 'o09'), ('2023-10-21', 'o21'), ('2023-11-02', 'n02'), ('2023-11-14', 'n14')]:
    im = col.filterDate(d, ee.Date(d).advance(1, 'day')).mosaic().select(['VV', 'VH'])
    for r0 in (0, 350):
        for c0 in (0, 380):
            x0 = 498000 + c0 * 100; y0 = 560000 - r0 * 100
            reg = ee.Geometry.Rectangle([x0, y0 - 35000, x0 + 38000, y0], CRS, False)
            a = im.reproject(CRS, [10, 0, 498000, 0, -10, 560000]).reduceResolution(ee.Reducer.mean(), False, 256).reproject(CRS, [100, 0, 498000, 0, -100, 560000])
            url = a.toFloat().getDownloadURL(dict(region=reg, crs=CRS, crsTransform=[100, 0, x0, 0, -100, y0], dimensions='380x350', format='NPY'))
            r = requests.get(url, timeout=900)
            if r.status_code != 200: print('FAIL', d, r0, c0, r.text[:200], flush=True); continue
            z = np.load(io.BytesIO(r.content), allow_pickle=True)
            for b in ('VV', 'VH'):
                arr.setdefault(n + '_' + b, np.full((H, W), np.nan, 'float32'))[r0:r0 + 350, c0:c0 + 380] = z[b]
        print(d, 'rows', r0, 'done', flush=True)
np.savez_compressed(os.path.join(OUT, 's1_100m_means.npz'), **arr); print('saved', list(arr))
