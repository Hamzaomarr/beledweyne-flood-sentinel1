"""
Test a dark-surface (sand / smooth bare soil) exclusion and add prevalence-robust metrics (balanced accuracy,
Cohen's kappa). The exclusion cut-off is chosen on the CALIBRATION date only (UNOSAT Pleiades 12 Nov vs S1 14 Nov)
and then evaluated, unchanged, on the later independent UNOSAT dates.
"""
import numpy as np, rasterio, geopandas as gpd, glob, os, json, pandas as pd
from rasterio import features
from rasterio.warp import reproject, Resampling
from scipy import ndimage as ndi

BASE = r'.'
RAS = os.path.join(BASE, 'data', 'processed', 'town_rasters')
UN = os.path.join(BASE, 'data', 'raw', 'unosat_FL20231105SOM', 'extracted')
OUT = os.path.join(BASE, 'outputs', 'tables')
P = json.load(open(os.path.join(OUT, 'chosen_parameters.json')))

def rd(n):
    with rasterio.open(os.path.join(RAS, n + '.tif')) as s: return s.read().astype('float32'), s.transform, s.crs
s1 = {d: rd('S1_' + d)[0] for d in ['20231009', '20231021', '20231114', '20231126']}
_, tr, crs = rd('S1_20231021'); H, W = s1['20231021'].shape[1:]
valid = np.all([np.isfinite(v).all(0) for v in s1.values()], axis=0)
def shp(p): return gpd.read_file(glob.glob(os.path.join(UN, '**', p + '*.shp'), recursive=True)[0])
def burn(g):
    g = g.to_crs(crs); return features.rasterize([(x, 1) for x in g.geometry if x is not None], out_shape=(H, W), transform=tr, fill=0, dtype='uint8').astype(bool)
PHR_A, PHR_F, PHR_W, PHR_C = [burn(shp(n)) for n in ['PHR_20231112_AnalysisExtent_Beledweyne', 'PHR_20231112_FloodExtent_Beledweyne', 'PHR_20231112_WaterExtent_Beledweyne', 'PHR_20231112_CloudObstruction_Beledweyne']]
GF_A, GF_F = burn(shp('GF2_20231123_AnalysisExtent_Beledweyne')), burn(shp('GF2_20231123_FloodExtent_Beledweyne'))
WV_A, WV_F = burn(shp('WV2_20231130_AnalysisExtent_BeledweyneCity')), burn(shp('WV2_20231130_FloodExtent_BeledweyneCity'))
PHR_F &= PHR_A; GF_F &= GF_A; WV_F &= WV_A

wc = np.zeros((H, W), 'uint8')
with rasterio.open(os.path.join(BASE, 'data', 'raw', 'worldcover_2021_v200', 'ESA_WorldCover_10m_2021_v200_N03E045_Map.tif')) as s:
    reproject(rasterio.band(s, 1), wc, dst_transform=tr, dst_crs=crs, resampling=Resampling.nearest)

def metrics(pred, truth, m):
    p, t = pred[m], truth[m]
    tp = (p & t).sum(); fp = (p & ~t).sum(); fn = (~p & t).sum(); tn = (~p & ~t).sum(); n = tp + fp + fn + tn
    rec = tp / max(tp + fn, 1); spec = tn / max(tn + fp, 1); prec = tp / max(tp + fp, 1)
    po = (tp + tn) / n; pe = ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / n ** 2
    return dict(precision=prec, recall=rec, specificity=spec, F1=2 * prec * rec / max(prec + rec, 1e-9),
                balanced_acc=(rec + spec) / 2, kappa=(po - pe) / max(1 - pe, 1e-9), OA=po)

def pre_img(k): return {'21Oct': s1['20231021'], '9Oct': s1['20231009']}.get(k, (s1['20231021'] + s1['20231009']) / 2)
def sm(a, k): return ndi.median_filter(a, size=k, mode='nearest') if k > 1 else a
def flood(post, pre, tv, th, k, dark=None):
    dVV = sm(post[0] - pre[0], k); dVH = sm(post[1] - pre[1], k); f = (dVV <= -tv) | (dVH <= -th)
    if dark is not None: f &= ~(sm(pre[0], k) < dark)       # exclude pixels already dark before the flood
    return f

pre = pre_img(P['pre']); k = P['filt']; tv, th = P['tVV'], P['tVH']
cal_mask = PHR_A & ~PHR_C & valid & (PHR_F | ~PHR_W)

rows = []
for dark in [None, -14, -15, -16, -17, -18, -19, -20, -22]:
    m = metrics(flood(s1['20231114'], pre, tv, th, k, dark), PHR_F, cal_mask); m.update(split='calibration PHR 12Nov', dark_cutoff=dark); rows.append(m)
cal = pd.DataFrame(rows)
print('Calibration: pre-flood-dark exclusion (VV_pre < cutoff dB is removed)')
print(cal[['dark_cutoff', 'precision', 'recall', 'F1', 'balanced_acc', 'kappa']].round(3).to_string(index=False))
# choose by Cohen's kappa (less prevalence-sensitive than F1), calibration only
best = cal.sort_values('kappa', ascending=False).iloc[0]
dark_sel = None if pd.isna(best.dark_cutoff) else float(best.dark_cutoff)
print('\nChosen exclusion (max kappa on calibration):', dark_sel)

# paper-style fixed thresholds also under kappa for comparison
res = []
for ref_name, F, A, post in [('PHR 12Nov (calibration)', PHR_F, cal_mask, s1['20231114']),
                             ('GF2 23Nov (all)', GF_F, GF_A & valid, s1['20231126']),
                             ('GF2 23Nov (outside calib. extent)', GF_F, GF_A & valid & ~PHR_A, s1['20231126']),
                             ('WV2 30Nov (all)', WV_F, WV_A & valid, s1['20231126']),
                             ('WV2 30Nov (outside calib. extent)', WV_F, WV_A & valid & ~PHR_A, s1['20231126'])]:
    for nm, args in {'calibrated rule, no exclusion': (pre, tv, th, k, None),
                     'calibrated rule + dark exclusion': (pre, tv, th, k, dark_sel),
                     'fixed -2.0/-1.5 (paper values)': (pre_img('21Oct'), 2.0, 1.5, 1, None),
                     'fixed -2.0/-1.5 + dark exclusion': (pre_img('21Oct'), 2.0, 1.5, 1, dark_sel)}.items():
        pr, a, b, kk, d = args
        m = metrics(flood(post, pr, a, b, kk, d), F, A); m.update(reference=ref_name, rule=nm, ref_flood_km2=(F & A).sum() / 1e4); res.append(m)
R = pd.DataFrame(res); R.to_csv(os.path.join(OUT, 'validation_with_kappa_and_exclusion.csv'), index=False)
print(R[['reference', 'rule', 'precision', 'recall', 'F1', 'balanced_acc', 'kappa']].round(3).to_string(index=False))

# by WorldCover class for the later date (where does recall fail?)
f_cal = flood(s1['20231126'], pre, tv, th, k, dark_sel)
names = {10: 'tree', 20: 'shrub', 30: 'grass', 40: 'crop', 50: 'built-up', 60: 'bare', 80: 'water'}
bk = []
for c, n in names.items():
    m = GF_A & valid & ~PHR_A & (wc == c)
    if m.sum() < 500: continue
    t = GF_F[m]; p = f_cal[m]
    bk.append(dict(worldcover=n, px=int(m.sum()), ref_flooded_share=t.mean(), pred_flooded_share=p.mean(), recall=(p & t).sum() / max(t.sum(), 1), precision=(p & t).sum() / max(p.sum(), 1)))
bk = pd.DataFrame(bk); bk.to_csv(os.path.join(OUT, 'validation_GF2_by_worldcover.csv'), index=False)
print('\nGF2 23 Nov vs S1 26 Nov outside calibration extent, by WorldCover class:')
print(bk.round(3).to_string(index=False))
json.dump(dict(P, dark_cutoff=dark_sel), open(os.path.join(OUT, 'chosen_parameters.json'), 'w'), indent=2)
