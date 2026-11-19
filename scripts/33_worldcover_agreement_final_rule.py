"""Agreement with UNOSAT by ESA WorldCover class under the FINAL rule (dark exclusion and 100 pixel minimum cluster), for the calibration mask and the
Gaofen-2 mapping outside the calibration extent. Also writes the resolution-check table. Same masks as scripts 03 and 04."""
import numpy as np, rasterio, geopandas as gpd, glob, os, json, pandas as pd
from rasterio import features
from rasterio.warp import reproject, Resampling
from scipy import ndimage as ndi
BASE = r'.'; RAS = os.path.join(BASE, 'data', 'processed', 'town_rasters'); UN = os.path.join(BASE, 'data', 'raw', 'unosat_FL20231105SOM', 'extracted')
OUT = os.path.join(BASE, 'outputs', 'tables'); P = json.load(open(os.path.join(OUT, 'chosen_parameters.json')))
def rd(n):
    with rasterio.open(os.path.join(RAS, n + '.tif')) as s: return s.read().astype('float32'), s.transform, s.crs
dates = ['20231009', '20231021', '20231102', '20231114', '20231126', '20231208']
s1 = {d: rd('S1_' + d)[0] for d in dates}; _, tr, crs = rd('S1_20231021'); H, W = s1['20231021'].shape[1:]
vall = np.all([np.isfinite(v).all(0) for v in s1.values()], axis=0)
def shp(p): return gpd.read_file(glob.glob(os.path.join(UN, '**', p + '*.shp'), recursive=True)[0])
def burn(g): g = g.to_crs(crs); return features.rasterize([(x, 1) for x in g.geometry if x is not None], out_shape=(H, W), transform=tr, fill=0, dtype='uint8').astype(bool)
PA, PF, PW, PC = [burn(shp('PHR_20231112_' + n + '_Beledweyne')) for n in ['AnalysisExtent', 'FloodExtent', 'WaterExtent', 'CloudObstruction']]; PF &= PA
GA = burn(shp('GF2_20231123_AnalysisExtent_Beledweyne')); GF = burn(shp('GF2_20231123_FloodExtent_Beledweyne')) & GA
wc = np.zeros((H, W), 'uint8')
with rasterio.open(os.path.join(BASE, 'data', 'raw', 'worldcover_2021_v200', 'ESA_WorldCover_10m_2021_v200_N03E045_Map.tif')) as s: reproject(rasterio.band(s, 1), wc, dst_transform=tr, dst_crs=crs, resampling=Resampling.nearest)
k = P['filt']; sm = lambda x: ndi.median_filter(x, size=k, mode='nearest'); pm = (s1['20231009'] + s1['20231021']) / 2
def flag(post): return (((sm(post[0] - pm[0]) <= -P['tVV']) | (sm(post[1] - pm[1]) <= -P['tVH'])) & ~(sm(pm[0]) < P['dark_cutoff'])) & vall
def rm_small(f, mn):
    lab, n = ndi.label(f, structure=np.ones((3, 3))); sz = np.bincount(lab.ravel()); keep = sz >= mn; keep[0] = False; return keep[lab]
f14 = rm_small(flag(s1['20231114']), P['min_cluster_px']); f26 = rm_small(flag(s1['20231126']), P['min_cluster_px'])
M = PA & ~PC & vall & (PF | ~PW); MG = GA & vall & ~PA
names = {10: 'Tree cover', 20: 'Shrubland', 30: 'Grassland', 40: 'Cropland', 50: 'Built-up', 60: 'Bare / sparse vegetation', 80: 'Permanent water bodies'}
rows = []
for c, n in names.items():
    r = dict(worldcover=n)
    for tag, f, m, truth in [('cal', f14, M, PF), ('gf2', f26, MG, GF)]:
        mm = m & (wc == c); p, t = f[mm], truth[mm]; tp = (p & t).sum(); fp = (p & ~t).sum(); fn = (~p & t).sum()
        r[tag + '_px'] = int(mm.sum()); r[tag + '_precision'] = tp / max(tp + fp, 1); r[tag + '_recall'] = tp / max(tp + fn, 1); r[tag + '_ref_flooded_share'] = float(t.mean()) if mm.sum() else np.nan
    rows.append(r)
df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'agreement_by_worldcover_final_rule.csv'), index=False); print(df.round(3).to_string(index=False))
rc = json.load(open(os.path.join(OUT, 'resolution_check.json')))
tab = pd.DataFrame([('Earth Engine, 10 m grid', rc['10']), ('Earth Engine, 20 m grid', rc['20']), ('Earth Engine, 30 m grid', rc['30']),
                    ('Earth Engine, inputs reprojected to 10 m, 20 m grid', rc['ee_inputs_reprojected_10m_on_20m_grid']), ('Local Python, 10 m', 51.163)], columns=['configuration', 'flagged_km2_town_extent'])
tab.to_csv(os.path.join(OUT, 'resolution_check_table.csv'), index=False); print(tab)
