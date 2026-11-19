import os, json, glob, numpy as np, pandas as pd, rasterio, geopandas as gpd
from rasterio import features
from scipy import ndimage as ndi
from pyproj import Transformer
B = r'.'; RAW = os.path.join(B, 'data', 'processed', 'raw10m'); DG = os.path.join(B, 'data', 'processed', 'diag'); OUT = os.path.join(B, 'outputs', 'tables')
RAS = os.path.join(B, 'data', 'processed', 'town_rasters'); UN = os.path.join(B, 'data', 'raw', 'unosat_FL20231105SOM', 'extracted'); P = json.load(open(os.path.join(OUT, 'chosen_parameters.json'))); MIN = int(P['min_cluster_px'])
with rasterio.open(os.path.join(RAW, 'lulc.tif')) as s: lulc = s.read(1).astype('uint8'); tr = s.transform
H, W = lulc.shape; CL0 = {0: 'Water', 1: 'Cropland', 2: 'Vegetation or rangeland', 3: 'Built-up', 4: 'Bare soil or sand'}
# ------------------------------------------------ independent check of built-up against Open Buildings v3 centroids (confidence >= 0.7)
xy = np.load(os.path.join(DG, 'open_buildings_centroids.npy')); tf = Transformer.from_crs('EPSG:4326', 'EPSG:32638', always_xy=True); X, Y = tf.transform(xy[:, 0], xy[:, 1])
c = ((np.array(X) - tr.c) / 10).astype(int); r = ((tr.f - np.array(Y)) / 10).astype(int); ok = (r >= 0) & (r < H) & (c >= 0) & (c < W); r, c = r[ok], c[ok]
cls_at = lulc[r, c]; n = len(r); rows = [[CL0[k], int((cls_at == k).sum()), 100 * (cls_at == k).mean()] for k in CL0]
bm = np.zeros((H, W), bool); bm[r, c] = True; dist = ndi.distance_transform_edt(~bm) * 10   # metres to the nearest building centroid
near = {}
for k in CL0:
    m = lulc == k; near[k] = {d: float((dist[m] <= d).mean() * 100) for d in (30, 50, 100)}
ob = dict(n_buildings=int(n), share_in_class=dict(zip([CL0[k] for k in CL0], [x[2] for x in rows])), counts=dict(zip([CL0[k] for k in CL0], [x[1] for x in rows])),
          pct_of_class_pixels_within_m_of_a_building={CL0[k]: near[k] for k in CL0}, builtup_km2=float((lulc == 3).sum() * 1e-4))
# share of buildings with a built-up pixel within 30 m / 50 m
bb = lulc == 3; d_b = ndi.distance_transform_edt(~bb) * 10; ob['pct_buildings_within_m_of_builtup_pixel'] = {d: float((d_b[r, c] <= d).mean() * 100) for d in (0, 30, 50, 100)}
json.dump(ob, open(os.path.join(OUT, 'revision_builtup_open_buildings.json'), 'w'), indent=1); print(json.dumps(ob, indent=1))
# ------------------------------------------------ alternative pre-event baselines, town rasters
def rdt(n):
    with rasterio.open(os.path.join(RAS, n + '.tif')) as s: return s.read().astype('float32'), s.transform, s.crs
dates = ['20231009', '20231021', '20231102', '20231114', '20231126', '20231208']; s1 = {d: rdt('S1_' + d)[0] for d in dates}; _, ttr, tcrs = rdt('S1_20231021'); th, tw = s1['20231021'].shape[1:]
vall = np.all([np.isfinite(v).all(0) for v in s1.values()], axis=0)
def shp(p): return gpd.read_file(glob.glob(os.path.join(UN, '**', p + '*.shp'), recursive=True)[0])
def burn(g): g = g.to_crs(tcrs); return features.rasterize([(x, 1) for x in g.geometry if x is not None], out_shape=(th, tw), transform=ttr, fill=0, dtype='uint8').astype(bool)
PA, PF, PW, PC = [burn(shp('PHR_20231112_' + nm + '_Beledweyne')) for nm in ['AnalysisExtent', 'FloodExtent', 'WaterExtent', 'CloudObstruction']]; PF &= PA
GA = burn(shp('GF2_20231123_AnalysisExtent_Beledweyne')); GF = burn(shp('GF2_20231123_FloodExtent_Beledweyne')) & GA
WA = burn(shp('WV2_20231130_AnalysisExtent_BeledweyneCity')); WF = burn(shp('WV2_20231130_FloodExtent_BeledweyneCity')) & WA
Mc = PA & ~PC & vall & (PF | ~PW); k = P['filt']; sm = lambda x: ndi.median_filter(x, size=k, mode='nearest')
def rm_small(f, mn=MIN):
    lab, n_ = ndi.label(f, structure=np.ones((3, 3))); sz = np.bincount(lab.ravel()); keep = sz >= mn; keep[0] = False; return keep[lab]
def sc(pred, truth, m):
    p, t = pred[m], truth[m]; tp = (p & t).sum(); fp = (p & ~t).sum(); fn = (~p & t).sum(); tn = (~p & ~t).sum(); nn = tp + fp + fn + tn
    rec = tp / max(tp + fn, 1); prec = tp / max(tp + fp, 1); po = (tp + tn) / nn; pe = ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / nn ** 2
    return prec, rec, (po - pe) / max(1 - pe, 1e-9)
refs = {'Mean of 9 and 21 October (main)': (s1['20231009'] + s1['20231021']) / 2, '9 October only': s1['20231009'], '21 October only': s1['20231021'], '2 November only': s1['20231102'],
        'Mean of 9 October, 21 October and 2 November': (s1['20231009'] + s1['20231021'] + s1['20231102']) / 3, 'Mean of 21 October and 2 November': (s1['20231021'] + s1['20231102']) / 2}
rows = []
for nm, pm in refs.items():
    fl = lambda post: rm_small((((sm(post[0] - pm[0]) <= -P['tVV']) | (sm(post[1] - pm[1]) <= -P['tVH'])) & ~(sm(pm[0]) < P['dark_cutoff'])) & vall)
    f14, f26 = fl(s1['20231114']), fl(s1['20231126']); a = sc(f14, PF, Mc); g = sc(f26, GF, GA & vall & ~PA); w = sc(f26, WF, WA & vall & ~PA)
    rows.append([nm, (f14 & Mc).sum() * 1e-4, a[0], a[1], a[2], (f26 & GA & vall & ~PA).sum() * 1e-4, g[0], g[1], g[2], w[2]])
alt = pd.DataFrame(rows, columns=['reference', 'flagged_km2_calibration_mask', 'prec_cal', 'rec_cal', 'kappa_cal', 'flagged_km2_GF2_outside', 'prec_GF2', 'rec_GF2', 'kappa_GF2', 'kappa_WV2'])
alt.to_csv(os.path.join(OUT, 'revision_alternative_pre_event_references_town.csv'), index=False); print(alt.round(3).to_string(index=False))
