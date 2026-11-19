"""Probe Earth Engine for the Beledweyne study: what Sentinel-1/-2 scenes actually exist."""
import ee, json
ee.Initialize(project='YOUR_EARTH_ENGINE_PROJECT')

AOI = ee.Geometry.Rectangle([45.00, 4.45, 45.65, 5.05])
TOWN = ee.Geometry.Point([45.2, 4.74])

def s1(start, end):
    return (ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(TOWN)
            .filterDate(start, end).filter(ee.Filter.eq('instrumentMode', 'IW'))
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')))

col = s1('2023-09-01', '2024-01-15')
info = col.map(lambda i: ee.Feature(None, {
    'date': i.date().format('YYYY-MM-dd HH:mm'),
    'pass': i.get('orbitProperties_pass'),
    'relorb': i.get('relativeOrbitNumber_start'),
    'sat': i.get('platform_number'),
    'covers_aoi_pct': i.geometry().intersection(AOI, 100).area(100).divide(AOI.area(100)).multiply(100),
})).getInfo()
print('S1 scenes Sep 2023 - mid Jan 2024 touching the town:')
for f in info['features']:
    p = f['properties']
    print(' ', p['date'], p['pass'], 'orbit', p['relorb'], p['sat'], 'AOI cover %.0f%%' % p['covers_aoi_pct'])

s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(AOI)
      .filterDate('2023-01-01', '2023-03-31'))
d = s2.map(lambda i: ee.Feature(None, {'date': i.date().format('YYYY-MM-dd'),
                                       'tile': i.get('MGRS_TILE'),
                                       'cc': i.get('CLOUDY_PIXEL_PERCENTAGE')})).getInfo()
print('\nS2 L2A Jan-Mar 2023 over AOI:')
for f in d['features']:
    p = f['properties']; print(' ', p['date'], p['tile'], 'cloud %.1f%%' % p['cc'])

dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterBounds(AOI).filterDate('2023-01-01', '2023-03-31')
print('\nDynamic World images Jan-Mar 2023:', dw.size().getInfo())
print('MERIT Hydro HAND band present:', 'hnd' in ee.Image('MERIT/Hydro/v1_0_1').bandNames().getInfo())
