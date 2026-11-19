import ee, json, os
ee.Initialize(project='YOUR_EARTH_ENGINE_PROJECT')
B = r'.'; OUT = os.path.join(B, 'data', 'processed', 'diag')
AOI = ee.Geometry.Rectangle([45.00, 4.45, 45.65, 5.05])
ch = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY').filterDate('2023-09-15', '2023-11-16')
print('chirps images', ch.size().getInfo())
def f(i): return ee.Feature(None, dict(date=i.date().format('YYYY-MM-dd'), mm=i.reduceRegion(ee.Reducer.mean(), AOI, 5566, maxPixels=1e9).get('precipitation')))
rows = ch.map(f).getInfo()['features']; r = [(x['properties']['date'], x['properties'].get('mm')) for x in rows]
json.dump(r, open(os.path.join(OUT, 'chirps_daily_mm.json'), 'w')); print(len(r)); print(r[:3], r[-3:])
