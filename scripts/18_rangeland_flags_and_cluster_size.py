"""
Diagnostic. (1) What do the 10 m flags look like in rangeland far from the town? Two 10 km boxes are exported from Earth Engine at 10 m
(raw flag with the calibrated rule, smoothed dVV and dVH, HAND, slope, WorldCover) and the connected-cluster sizes are tabulated.
(2) In the town (calibration date only), how do precision and recall change if flagged clusters smaller than N pixels are removed?
Nothing here is a final result; it informs whether a minimum cluster size should be added to the method.
"""
import ee, json, os, io, zipfile, requests, numpy as np, pandas as pd, rasterio, geopandas as gpd, glob
from rasterio import features
from scipy import ndimage as ndi
ee.Initialize(project='YOUR_EARTH_ENGINE_PROJECT')
BASE = r'.'; OUT = os.path.join(BASE, 'outputs', 'tables'); P = json.load(open(os.path.join(OUT, 'chosen_parameters.json')))
SAMPLES = os.path.join(BASE, 'data', 'processed', 'rangeland_samples'); os.makedirs(SAMPLES, exist_ok=True)
CRS = 'EPSG:32638'
AOI = ee.Geometry.Rectangle([45.00, 4.45, 45.65, 5.05])
col = (ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(AOI).filter(ee.Filter.eq('instrumentMode', 'IW'))
       .filter(ee.Filter.eq('relativeOrbitNumber_start', 35)).filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING')))
def s1d(d): return col.filterDate(d, ee.Date(d).advance(1, 'day')).mosaic().select(['VV', 'VH'])
S = {d: s1d(d) for d in ['2023-10-09', '2023-10-21', '2023-11-14']}
pre = S['2023-10-09'].add(S['2023-10-21']).divide(2); post = S['2023-11-14']; r = P['filt'] // 2
med = lambda i: i.focalMedian(radius=r, kernelType='square', units='pixels')
dvv = med(post.select('VV').subtract(pre.select('VV'))); dvh = med(post.select('VH').subtract(pre.select('VH')))
flag = dvv.lte(-P['tVV']).Or(dvh.lte(-P['tVH'])).And(med(pre.select('VV')).gte(P['dark_cutoff']))
valid = S['2023-10-21'].select('VV').mask().And(S['2023-11-14'].select('VV').mask())
hand = ee.Image('MERIT/Hydro/v1_0_1').select('hnd').unmask(0)
dem = ee.ImageCollection('COPERNICUS/DEM/GLO30').select('DEM').mosaic().setDefaultProjection('EPSG:4326', None, 30.9)
wc = ee.ImageCollection('ESA/WorldCover/v200').first().select('Map')
stack = ee.Image.cat([flag.And(valid).unmask(0).rename('flag'), dvv.rename('dvv'), dvh.rename('dvh'), hand.rename('hand'), ee.Terrain.slope(dem).rename('slope'), wc.rename('wc')]).toFloat()
boxes = {'east_rangeland': [545000, 535000, 555000, 545000], 'southwest_rangeland': [503000, 495000, 513000, 505000]}
def fetch(name, b):
    reg = ee.Geometry.Rectangle(b, CRS, False)
    url = stack.getDownloadURL({'region': reg, 'scale': 10, 'crs': CRS, 'format': 'GEO_TIFF'})
    rr = requests.get(url, timeout=900); rr.raise_for_status(); data = rr.content
    if data[:2] == b'PK': data = zipfile.ZipFile(io.BytesIO(data)).read(zipfile.ZipFile(io.BytesIO(data)).namelist()[0])
    p = os.path.join(SAMPLES, name + '.tif'); open(p, 'wb').write(data); return p
rows = []
for nm, b in boxes.items():
    p = os.path.join(SAMPLES, nm + '.tif')
    if not os.path.exists(p): p = fetch(nm, b)
    with rasterio.open(p) as s: a = s.read().astype('float32')
    fl = a[0] > 0.5; dv = a[1]; hd = a[3]; sl = a[4]; w = a[5]
    lab, n = ndi.label(fl, structure=np.ones((3, 3))); sizes = ndi.sum(fl, lab, index=np.arange(1, n + 1)).astype(int)
    tot = int(fl.sum()); inside = (hd <= 10) & (sl <= 8)
    def share(lo, hi): m = (sizes >= lo) & (sizes < hi); return float(sizes[m].sum() / max(tot, 1))
    rows.append(dict(box=nm, px=int(fl.size), flagged_px=tot, flagged_share=tot / fl.size, n_clusters=int(n), median_cluster_px=float(np.median(sizes)) if n else 0,
                     share_in_clusters_lt10=share(1, 10), share_lt50=share(1, 50), share_lt200=share(1, 200), share_ge1000=share(1000, 10 ** 9),
                     flagged_with_HAND_le10_slope_le8=float((fl & inside).sum() / max(tot, 1)), median_dVV_flagged=float(np.median(dv[fl])) if tot else np.nan,
                     median_HAND_flagged=float(np.median(hd[fl])) if tot else np.nan, share_flagged_wc_grass_shrub_tree=float(np.isin(w[fl], [10, 20, 30]).mean()) if tot else np.nan))
rg = pd.DataFrame(rows); rg.to_csv(os.path.join(OUT, 'diagnostic_rangeland_flag_clusters.csv'), index=False); print(rg.round(3).T.to_string(), flush=True)

# ---- (2) town, calibration date only: effect of a minimum cluster size
RAS = os.path.join(BASE, 'data', 'processed', 'town_rasters'); UN = os.path.join(BASE, 'data', 'raw', 'unosat_FL20231105SOM', 'extracted')
def rd(n):
    with rasterio.open(os.path.join(RAS, n + '.tif')) as s: return s.read().astype('float32'), s.transform, s.crs
dates = ['20231009', '20231021', '20231102', '20231114', '20231126', '20231208']
s1 = {d: rd('S1_' + d)[0] for d in dates}; _, tr, crs = rd('S1_20231021'); H, W = s1['20231021'].shape[1:]
vall = np.all([np.isfinite(v).all(0) for v in s1.values()], axis=0)
def shp(p): return gpd.read_file(glob.glob(os.path.join(UN, '**', p + '*.shp'), recursive=True)[0])
def burn(g): g = g.to_crs(crs); return features.rasterize([(x, 1) for x in g.geometry if x is not None], out_shape=(H, W), transform=tr, fill=0, dtype='uint8').astype(bool)
PA, PF, PW, PC = [burn(shp('PHR_20231112_' + n + '_Beledweyne')) for n in ['AnalysisExtent', 'FloodExtent', 'WaterExtent', 'CloudObstruction']]; PF &= PA
k = P['filt']; sm = lambda x: ndi.median_filter(x, size=k, mode='nearest')
pm = (s1['20231009'] + s1['20231021']) / 2; p14 = s1['20231114']
f = (((sm(p14[0] - pm[0]) <= -P['tVV']) | (sm(p14[1] - pm[1]) <= -P['tVH'])) & ~(sm(pm[0]) < P['dark_cutoff'])) & vall
M = PA & ~PC & vall & (PF | ~PW)
def sc(pred):
    p, t = pred[M], PF[M]; tp = (p & t).sum(); fp = (p & ~t).sum(); fn = (~p & t).sum(); tn = (~p & ~t).sum(); n = tp + fp + fn + tn
    rec = tp / max(tp + fn, 1); spec = tn / max(tn + fp, 1); prec = tp / max(tp + fp, 1); po = (tp + tn) / n; pe = ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / n ** 2
    return dict(precision=prec, recall=rec, balanced_acc=(rec + spec) / 2, kappa=(po - pe) / max(1 - pe, 1e-9), flagged_km2=(tp + fp) / 1e4)
lab, n = ndi.label(f, structure=np.ones((3, 3))); sizes = np.bincount(lab.ravel()); sizes[0] = 0
out = []
for mn in [1, 5, 10, 20, 50, 100, 200, 500]:
    keep = sizes >= mn; keep[0] = False; r_ = sc(keep[lab]); r_['min_cluster_px'] = mn; out.append(r_)
ct = pd.DataFrame(out)[['min_cluster_px', 'precision', 'recall', 'balanced_acc', 'kappa', 'flagged_km2']]
ct.to_csv(os.path.join(OUT, 'diagnostic_min_cluster_size_calibration.csv'), index=False); print('\nTown, calibration date (Pleiades 12 Nov vs S1 14 Nov), min cluster size:'); print(ct.round(3).to_string(index=False), flush=True)
