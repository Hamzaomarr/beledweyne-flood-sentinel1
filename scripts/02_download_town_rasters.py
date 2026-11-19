"""Download real Sentinel-1 (per date, un-filtered dB), HAND and slope rasters for the UNOSAT analysis area."""
import ee, geopandas as gpd, glob, os, requests, zipfile, io
ee.Initialize(project='YOUR_EARTH_ENGINE_PROJECT')

RAW = r'.\data\raw\unosat_FL20231105SOM\extracted'
OUT = r'.\data\processed\town_rasters'
os.makedirs(OUT, exist_ok=True)

def shp(pat):
    return gpd.read_file(glob.glob(os.path.join(RAW, '**', pat + '*.shp'), recursive=True)[0])

b1 = shp('PHR_20231112_AnalysisExtent_BeledweyneCity').total_bounds
b2 = shp('GF2_20231123_AnalysisExtent_BeledweyneCity').total_bounds
minx, miny = min(b1[0], b2[0]) - 0.01, min(b1[1], b2[1]) - 0.01
maxx, maxy = max(b1[2], b2[2]) + 0.01, max(b1[3], b2[3]) + 0.01
print('download bbox', [round(v, 4) for v in (minx, miny, maxx, maxy)])
region = ee.Geometry.Rectangle([minx, miny, maxx, maxy])
CRS, SCALE = 'EPSG:32638', 10

def fetch(img, name):
    url = img.getDownloadURL({'region': region, 'scale': SCALE, 'crs': CRS, 'format': 'GEO_TIFF'})
    r = requests.get(url, timeout=600); r.raise_for_status()
    path = os.path.join(OUT, name + '.tif')
    if r.content[:2] == b'PK':
        z = zipfile.ZipFile(io.BytesIO(r.content)); n = z.namelist()[0]
        open(path, 'wb').write(z.read(n))
    else:
        open(path, 'wb').write(r.content)
    print('saved', name, round(os.path.getsize(path) / 1e6, 1), 'MB')

col = (ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(region)
       .filter(ee.Filter.eq('instrumentMode', 'IW'))
       .filter(ee.Filter.eq('relativeOrbitNumber_start', 35))
       .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING')))
for d in ['2023-10-09', '2023-10-21', '2023-11-02', '2023-11-14', '2023-11-26', '2023-12-08']:
    nxt = ee.Date(d).advance(1, 'day')
    sub = col.filterDate(d, nxt)
    n = sub.size().getInfo()
    print(d, 'scenes in collection:', n)
    img = sub.select(['VV', 'VH']).mosaic().clip(region)   # mosaic in case the AOI spans two slices
    fetch(img.float(), 'S1_' + d.replace('-', ''))

hand = ee.Image('MERIT/Hydro/v1_0_1').select('hnd').rename('HAND')
dem = ee.ImageCollection('COPERNICUS/DEM/GLO30').select('DEM').mosaic().setDefaultProjection('EPSG:4326', None, 30.9)
slope = ee.Terrain.slope(dem).rename('slope_deg')
elev = dem.rename('elev_m')
fetch(ee.Image.cat([hand, slope, elev]).float().clip(region), 'terrain_HAND_slope_elev')
