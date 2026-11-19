"""
Calibrate Sentinel-1 flood thresholds against UNOSAT optical flood polygons (Beledweyne town), then test on
independent dates. Everything is computed from the downloaded rasters / shapefiles.

Calibration : UNOSAT Pleiades 12 Nov 2023  vs  S1 14 Nov 2023 (pre = 21 Oct / 9 Oct / their median)
Validation  : UNOSAT GF-2  23 Nov 2023 and WorldView-2 30 Nov 2023  vs  S1 26 Nov 2023, scored only
              OUTSIDE the calibration (Pleiades) analysis extent so the area is also independent.
"""
import numpy as np, rasterio, geopandas as gpd, glob, os, json
from rasterio import features
from rasterio.warp import reproject, Resampling
from scipy import ndimage as ndi

BASE = r'.'
RAS = os.path.join(BASE, 'data', 'processed', 'town_rasters')
UN = os.path.join(BASE, 'data', 'raw', 'unosat_FL20231105SOM', 'extracted')
OUT = os.path.join(BASE, 'outputs', 'tables'); os.makedirs(OUT, exist_ok=True)

def rd(name):
    with rasterio.open(os.path.join(RAS, name + '.tif')) as s:
        return s.read().astype('float32'), s.profile, s.transform, s.crs, s.nodata
def shp(pat):
    return gpd.read_file(glob.glob(os.path.join(UN, '**', pat + '*.shp'), recursive=True)[0])

s1 = {}
for d in ['20231009', '20231021', '20231102', '20231114', '20231126', '20231208']:
    a, prof, tr, crs, nd = rd('S1_' + d)
    s1[d] = a                      # (2,H,W): VV, VH in dB
H, W = s1['20231021'].shape[1:]
print('grid', H, 'x', W, 'crs', crs, 'nodata', nd)
valid_all = np.all([np.isfinite(v).all(0) for v in s1.values()], axis=0)

def burn(gdf):
    g = gdf.to_crs(crs)
    return features.rasterize([(geom, 1) for geom in g.geometry if geom is not None], out_shape=(H, W),
                              transform=tr, fill=0, dtype='uint8', all_touched=False).astype(bool)

# ---- reference masks
ref = {}
for tag, ae, fl, wa, cl in [
    ('PHR_20231112', 'PHR_20231112_AnalysisExtent_Beledweyne', 'PHR_20231112_FloodExtent_Beledweyne',
     'PHR_20231112_WaterExtent_Beledweyne', 'PHR_20231112_CloudObstruction_Beledweyne'),
    ('GF2_20231123', 'GF2_20231123_AnalysisExtent_Beledweyne', 'GF2_20231123_FloodExtent_Beledweyne', None, None),
    ('WV2_20231130', 'WV2_20231130_AnalysisExtent_BeledweyneCity', 'WV2_20231130_FloodExtent_BeledweyneCity', None, None)]:
    A = burn(shp(ae)); F = burn(shp(fl)) & A
    C = burn(shp(cl)) if cl else np.zeros_like(A)
    Wt = burn(shp(wa)) if wa else np.zeros_like(A)
    ref[tag] = dict(analysis=A, flood=F, cloud=C, water=Wt)
    print(tag, 'analysis km2 %.1f' % (A.sum() / 1e4), 'flood km2 %.2f' % (F.sum() / 1e4), 'cloud km2 %.2f' % (C.sum() / 1e4))

# ---- ancillary: WorldCover (for stratifying results only) and terrain
wc_path = os.path.join(BASE, 'data', 'raw', 'worldcover_2021_v200', 'ESA_WorldCover_10m_2021_v200_N03E045_Map.tif')
wc = np.zeros((H, W), 'uint8')
with rasterio.open(wc_path) as s:
    reproject(rasterio.band(s, 1), wc, dst_transform=tr, dst_crs=crs, resampling=Resampling.nearest)
terr, _, _, _, _ = rd('terrain_HAND_slope_elev')   # HAND, slope, elev

# ---- scoring helpers
def conf(pred, truth, mask):
    p, t = pred[mask], truth[mask]
    tp = int((p & t).sum()); fp = int((p & ~t).sum()); fn = int((~p & t).sum()); tn = int((~p & ~t).sum())
    prec = tp / max(tp + fp, 1); rec = tp / max(tp + fn, 1)
    f1 = 2 * prec * rec / max(prec + rec, 1e-9); iou = tp / max(tp + fp + fn, 1)
    oa = (tp + tn) / max(tp + fp + fn + tn, 1)
    return dict(tp=tp, fp=fp, fn=fn, tn=tn, precision=prec, recall=rec, F1=f1, IoU=iou, OA=oa)

def smooth(a, k):
    return ndi.median_filter(a, size=k, mode='nearest') if k > 1 else a

def delta(post, pre, k):
    return smooth(post[0] - pre[0], k), smooth(post[1] - pre[1], k)

def pre_img(kind):
    if kind == '21Oct': return s1['20231021']
    if kind == '9Oct': return s1['20231009']
    return (s1['20231021'] + s1['20231009']) / 2.0   # mean of dB values of two pre-event scenes

# ---- 1. calibration on PHR 12 Nov vs S1 14 Nov
R = ref['PHR_20231112']
score_mask = R['analysis'] & ~R['cloud'] & valid_all & (R['flood'] | ~R['water'])   # flood, or dry land (not any water)
print('\nCalibration pixels: flooded %.2f km2, non-flooded %.2f km2' %
      ((score_mask & R['flood']).sum() / 1e4, (score_mask & ~R['flood']).sum() / 1e4))

rows = []
for pre_kind in ['21Oct', '9Oct', 'mean_9&21Oct']:
    for k in [1, 3, 5]:
        dVV, dVH = delta(s1['20231114'], pre_img(pre_kind), k)
        for t in np.arange(0.5, 6.01, 0.25):
            r = conf(dVV <= -t, R['flood'], score_mask); r.update(rule='dVV', pre=pre_kind, filt=k, tVV=t, tVH=np.nan); rows.append(r)
        for t in np.arange(0.5, 6.01, 0.25):
            r = conf(dVH <= -t, R['flood'], score_mask); r.update(rule='dVH', pre=pre_kind, filt=k, tVV=np.nan, tVH=t); rows.append(r)
        for tv in np.arange(0.5, 4.01, 0.5):
            for th in np.arange(0.5, 4.01, 0.5):
                r = conf((dVV <= -tv) | (dVH <= -th), R['flood'], score_mask); r.update(rule='dVV OR dVH', pre=pre_kind, filt=k, tVV=tv, tVH=th); rows.append(r)
import pandas as pd
cal = pd.DataFrame(rows)
cal.to_csv(os.path.join(OUT, 'calibration_grid_PHR12Nov_vs_S1_14Nov.csv'), index=False)
best = cal.sort_values('F1', ascending=False).groupby('rule').head(1)
print('\nBest F1 per rule (calibration, Pleiades 12 Nov):')
print(best[['rule', 'pre', 'filt', 'tVV', 'tVH', 'precision', 'recall', 'F1', 'IoU', 'OA']].round(3).to_string(index=False))

# Paper-style fixed thresholds (-2.0 dB VV OR -1.5 dB VH), reported only as a comparison, not as our choice
cmp_rows = []
for pre_kind in ['21Oct', '9Oct', 'mean_9&21Oct']:
    dVV, dVH = delta(s1['20231114'], pre_img(pre_kind), 1)
    r = conf((dVV <= -2.0) | (dVH <= -1.5), R['flood'], score_mask); r.update(pre=pre_kind, rule='fixed -2.0/-1.5 OR'); cmp_rows.append(r)
print('\nFixed -2.0 dB VV OR -1.5 dB VH (for comparison only):')
print(pd.DataFrame(cmp_rows)[['pre', 'precision', 'recall', 'F1', 'IoU', 'OA']].round(3).to_string(index=False))

# Otsu on the unlabeled dVV histogram of valid analysed pixels (unsupervised cross-check)
def otsu(x, nb=256):
    h, e = np.histogram(x, bins=nb); c = (e[:-1] + e[1:]) / 2; w0 = np.cumsum(h); w1 = w0[-1] - w0
    m0 = np.cumsum(h * c) / np.maximum(w0, 1); m1 = (np.sum(h * c) - np.cumsum(h * c)) / np.maximum(w1, 1)
    return c[np.argmax(w0 * w1 * (m0 - m1) ** 2)]
dVV21, _ = delta(s1['20231114'], pre_img('21Oct'), 1)
print('\nOtsu threshold on unlabeled dVV (14 Nov - 21 Oct), analysed pixels: %.2f dB' % otsu(dVV21[score_mask]))

# distributions
for nm, m in [('flooded (UNOSAT)', score_mask & R['flood']), ('non-flooded (UNOSAT)', score_mask & ~R['flood'])]:
    v = dVV21[m]; print('%-22s dVV mean %.2f sd %.2f  p5 %.2f p50 %.2f p95 %.2f' % (nm, v.mean(), v.std(), *np.percentile(v, [5, 50, 95])))

# ---- 2. choose parameters: best F1 on calibration, chosen BEFORE looking at validation
cho = cal[(cal.rule == 'dVV OR dVH')].sort_values('F1', ascending=False).iloc[0]
cho_vv = cal[(cal.rule == 'dVV')].sort_values('F1', ascending=False).iloc[0]
params = dict(rule='dVV OR dVH', pre=cho.pre, filt=int(cho.filt), tVV=float(cho.tVV), tVH=float(cho.tVH),
              dVV_only=dict(pre=cho_vv.pre, filt=int(cho_vv.filt), tVV=float(cho_vv.tVV)))
json.dump(params, open(os.path.join(OUT, 'chosen_parameters.json'), 'w'), indent=2)
print('\nChosen on calibration only:', params)

# ---- 3. independent validation on later dates, outside the calibration extent
Rc = ref['PHR_20231112']['analysis']
val_rows = []
for tag in ['GF2_20231123', 'WV2_20231130']:
    V = ref[tag]
    m_all = V['analysis'] & valid_all
    m_out = m_all & ~Rc
    for label, m in [('whole extent', m_all), ('outside calibration extent', m_out)]:
        for name, (pk, fk, tv, th) in {'chosen OR rule': (params['pre'], params['filt'], params['tVV'], params['tVH']),
                                       'chosen dVV only': (params['dVV_only']['pre'], params['dVV_only']['filt'], params['dVV_only']['tVV'], None),
                                       'fixed -2.0/-1.5': ('21Oct', 1, 2.0, 1.5)}.items():
            dVV, dVH = delta(s1['20231126'], pre_img(pk), fk)
            pred = (dVV <= -tv) | (dVH <= -th) if th is not None and name != 'chosen dVV only' else (dVV <= -tv)
            r = conf(pred, V['flood'], m); r.update(reference=tag, scope=label, rule=name, ref_flood_km2=(V['flood'] & m).sum() / 1e4)
            val_rows.append(r)
val = pd.DataFrame(val_rows)
val.to_csv(os.path.join(OUT, 'validation_independent_dates.csv'), index=False)
print('\nIndependent validation (S1 26 Nov vs later UNOSAT optical):')
print(val[['reference', 'scope', 'rule', 'ref_flood_km2', 'precision', 'recall', 'F1', 'IoU', 'OA']].round(3).to_string(index=False))

# ---- 4. where does it fail? recall/precision by WorldCover class on the calibration date
dVV, dVH = delta(s1['20231114'], pre_img(params['pre']), params['filt'])
pred = (dVV <= -params['tVV']) | (dVH <= -params['tVH'])
names = {10: 'tree', 20: 'shrub', 30: 'grass', 40: 'crop', 50: 'built-up', 60: 'bare', 80: 'water'}
brk = []
for c, n in names.items():
    m = score_mask & (wc == c)
    if m.sum() < 500: continue
    r = conf(pred, R['flood'], m); r.update(worldcover=n, px=int(m.sum()), ref_flood_share=(R['flood'] & m).sum() / m.sum()); brk.append(r)
bk = pd.DataFrame(brk); bk.to_csv(os.path.join(OUT, 'calibration_by_worldcover_class.csv'), index=False)
print('\nBy WorldCover class (calibration date):')
print(bk[['worldcover', 'px', 'ref_flood_share', 'precision', 'recall', 'F1']].round(3).to_string(index=False))

# terrain statistics of UNOSAT-flooded pixels (to justify HAND / slope masks from data)
fm = (R['flood'] | ref['GF2_20231123']['flood']) & valid_all
for i, nm in [(0, 'HAND (m)'), (1, 'slope (deg)')]:
    v = terr[i][fm]; v = v[np.isfinite(v)]
    print('UNOSAT-flooded pixels %-12s p50 %.2f p95 %.2f p99 %.2f max %.2f' % (nm, *np.percentile(v, [50, 95, 99]), v.max()))
