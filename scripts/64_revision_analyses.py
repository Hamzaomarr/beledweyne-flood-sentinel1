"""Revision analyses answering reviewer comments. All numbers come from the existing 10 m rasters, the town rasters, and three small diagnostic downloads (script 61/62/63)."""
import os, json, glob, numpy as np, pandas as pd, rasterio, geopandas as gpd
from rasterio import features
from scipy import ndimage as ndi
from shapely.geometry import Polygon
from pyproj import Transformer
B = r'.'; RAW = os.path.join(B, 'data', 'processed', 'raw10m'); DG = os.path.join(B, 'data', 'processed', 'diag'); OUT = os.path.join(B, 'outputs', 'tables')
RAS = os.path.join(B, 'data', 'processed', 'town_rasters'); UN = os.path.join(B, 'data', 'raw', 'unosat_FL20231105SOM', 'extracted')
P = json.load(open(os.path.join(OUT, 'chosen_parameters.json'))); MIN = int(P['min_cluster_px']); KM2 = 1e-4
CL = {1: 'Cropland', 2: 'Vegetation or rangeland', 3: 'Built-up', 4: 'Bare soil or sand'}; CL0 = {0: 'Water', **CL}
def rd(n):
    with rasterio.open(os.path.join(RAW, n + '.tif')) as s: return s.read(1), s.transform
lulc, tr = rd('lulc'); lulc = lulc.astype('uint8'); H, W = lulc.shape
tf = Transformer.from_crs('EPSG:4326', 'EPSG:32638', always_xy=True)
def ring(x0, y0, x1, y1, n=400):
    xs = np.linspace(x0, x1, n); ys = np.linspace(y0, y1, n)
    return list(zip(xs, np.full(n, y0))) + list(zip(np.full(n, x1), ys)) + list(zip(xs[::-1], np.full(n, y1))) + list(zip(np.full(n, x0), ys[::-1]))
poly = Polygon([tf.transform(x, y) for x, y in ring(45.00, 4.45, 45.65, 5.05)])
aoi = features.rasterize([(poly, 1)], out_shape=(H, W), transform=tr, fill=0, dtype='uint8').astype(bool)
dom = rd('domain')[0].astype(bool) & aoi; perm = rd('perm')[0].astype(bool)
def cf(f, mn=MIN):
    lab, n = ndi.label(f, structure=np.ones((3, 3))); sz = np.bincount(lab.ravel()); keep = sz >= mn; keep[0] = False; return keep[lab]
res = {}
# ---------------------------------------------------------------- 1. area budget
tot = aoi.sum() * KM2; pw = (aoi & perm).sum() * KM2; terr = (aoi & ~perm & ~dom).sum() * KM2; el = dom.sum() * KM2
print('overlap domain&perm', (dom & perm).sum())
bud = pd.DataFrame([['Study area (rectangle)', tot, 100.0], ['Excluded as permanent water', pw, 100 * pw / tot], ['Excluded by HAND or slope limits (outside permanent water)', terr, 100 * terr / tot], ['Eligible analysed area', el, 100 * el / tot]], columns=['item', 'km2', 'pct_of_study_area'])
bud.to_csv(os.path.join(OUT, 'revision_area_budget.csv'), index=False); print(bud.round(2).to_string(index=False))
rows = []
for c, nm in CL0.items():
    m = (lulc == c) & aoi; rows.append([nm, m.sum() * KM2, (m & perm).sum() * KM2, (m & ~perm & ~dom).sum() * KM2, (m & dom).sum() * KM2])
pd.DataFrame(rows, columns=['class', 'mapped_km2', 'perm_water_excluded_km2', 'terrain_excluded_km2', 'analysed_km2']).to_csv(os.path.join(OUT, 'revision_area_budget_by_class.csv'), index=False)
print(pd.DataFrame(rows, columns=['class', 'mapped', 'perm', 'terrain', 'analysed']).round(2).to_string(index=False))
# ---------------------------------------------------------------- 2. HAND missing
with rasterio.open(os.path.join(DG, 'hand_missing_90m.tif')) as s: hm90 = s.read(1).astype(bool)
hm = np.repeat(np.repeat(hm90, 9, 0), 9, 1)[:H, :W]
raw14 = rd('flag_14Nov')[0].astype(bool) & aoi; raw26 = rd('flag_26Nov')[0].astype(bool) & aoi
F14 = cf(raw14) & dom; F26 = cf(raw26) & dom
hr = dict(missing_km2_in_study_area=(hm & aoi).sum() * KM2, missing_pct_of_study_area=100 * (hm & aoi).sum() / aoi.sum(), missing_in_analysed_area_km2=(hm & dom).sum() * KM2,
          missing_in_permanent_water_km2=(hm & aoi & perm).sum() * KM2, flagged14_in_missing_km2=(F14 & hm).sum() * KM2, flagged26_in_missing_km2=(F26 & hm).sum() * KM2,
          analysed_without_missing_km2=(dom & ~hm).sum() * KM2, flagged14_without_missing_km2=(F14 & ~hm).sum() * KM2, flagged26_without_missing_km2=(F26 & ~hm).sum() * KM2,
          missing_pixels_10m=int((hm & aoi).sum()))
print('HAND missing', {k: round(float(v), 3) for k, v in hr.items()}); json.dump({k: float(v) for k, v in hr.items()}, open(os.path.join(OUT, 'revision_hand_missing.json'), 'w'), indent=1)
# ---------------------------------------------------------------- 3. validation coverage (town grid)
def rdt(n):
    with rasterio.open(os.path.join(RAS, n + '.tif')) as s: return s.read().astype('float32'), s.transform, s.crs
dates = ['20231009', '20231021', '20231102', '20231114', '20231126', '20231208']
s1 = {d: rdt('S1_' + d)[0] for d in dates}; _, ttr, tcrs = rdt('S1_20231021'); th, tw = s1['20231021'].shape[1:]
r0, c0 = rasterio.transform.rowcol(tr, ttr.c + 0.1, ttr.f - 0.1); assert abs(ttr.c - (tr.c + c0 * 10)) < 1e-6 and abs(ttr.f - (tr.f - r0 * 10)) < 1e-6
vall = np.all([np.isfinite(v).all(0) for v in s1.values()], axis=0)
def shp(p): return gpd.read_file(glob.glob(os.path.join(UN, '**', p + '*.shp'), recursive=True)[0])
def burn(g): g = g.to_crs(tcrs); return features.rasterize([(x, 1) for x in g.geometry if x is not None], out_shape=(th, tw), transform=ttr, fill=0, dtype='uint8').astype(bool)
PA, PF, PW, PC = [burn(shp('PHR_20231112_' + n + '_Beledweyne')) for n in ['AnalysisExtent', 'FloodExtent', 'WaterExtent', 'CloudObstruction']]; PF &= PA
GA = burn(shp('GF2_20231123_AnalysisExtent_Beledweyne')); GF = burn(shp('GF2_20231123_FloodExtent_Beledweyne')) & GA
WA = burn(shp('WV2_20231130_AnalysisExtent_BeledweyneCity')); WF = burn(shp('WV2_20231130_FloodExtent_BeledweyneCity')) & WA
Mc = PA & ~PC & vall & (PF | ~PW)
masks = {'Calibration, Pleiades 12 November scoring mask': Mc, 'Gaofen-2 23 November, whole extent': GA & vall, 'Gaofen-2 23 November, outside calibration extent': GA & vall & ~PA,
         'WorldView-2 30 November, whole extent': WA & vall, 'WorldView-2 30 November, outside calibration extent': WA & vall & ~PA}
masks['Union of all three products'] = Mc | (GA & vall) | (WA & vall)
lt = lulc[r0:r0 + th, c0:c0 + tw]; dt = dom[r0:r0 + th, c0:c0 + tw]; rows = []
for nm, m in masks.items():
    r = dict(mask=nm, area_km2=m.sum() * KM2, pct_of_study_area=100 * m.sum() / aoi.sum(), pct_inside_analysed_area=100 * (m & dt).sum() / m.sum())
    for c, cn in CL0.items(): r['km2_' + cn] = (m & (lt == c)).sum() * KM2
    r['flooded_reference_km2'] = (m & (PF if 'Pleiades' in nm else GF if 'Gaofen' in nm else WF if 'WorldView' in nm else (PF | GF | WF))).sum() * KM2
    rows.append(r)
cov = pd.DataFrame(rows); cov.to_csv(os.path.join(OUT, 'revision_validation_coverage.csv'), index=False); print(cov.round(2).T.to_string())
cls_tot = {c: ((lulc == c) & aoi).sum() * KM2 for c in CL0}; cls_dom = {c: ((lulc == c) & dom).sum() * KM2 for c in CL0}
u = masks['Union of all three products']; rows = []
for c, cn in CL0.items(): rows.append([cn, cls_tot[c], cls_dom[c], (u & (lt == c)).sum() * KM2, (u & dt & (lt == c)).sum() * KM2])
cu = pd.DataFrame(rows, columns=['class', 'mapped_km2', 'analysed_km2', 'inside_any_reference_extent_km2', 'inside_extent_and_analysed_km2']); cu['pct_of_analysed_inside_extent'] = 100 * cu.inside_extent_and_analysed_km2 / cu.analysed_km2.replace(0, np.nan)
cu.to_csv(os.path.join(OUT, 'revision_validation_coverage_by_class.csv'), index=False); print(cu.round(2).to_string(index=False))
# ---------------------------------------------------------------- 4. cluster filter: what was removed
k = P['filt']; sm = lambda x: ndi.median_filter(x, size=k, mode='nearest'); pm = (s1['20231009'] + s1['20231021']) / 2
def flag(post): return (((sm(post[0] - pm[0]) <= -P['tVV']) | (sm(post[1] - pm[1]) <= -P['tVH'])) & ~(sm(pm[0]) < P['dark_cutoff'])) & vall
def lab_sizes(f):
    lab, n = ndi.label(f, structure=np.ones((3, 3))); sz = np.bincount(lab.ravel()); sz[0] = 0; return lab, sz
f14t = flag(s1['20231114']); f26t = flag(s1['20231126']); rows = []
bins = [(1, 9), (10, 49), (50, 99)]
for nm, f, A, truth in [('Pleiades 12 November (calibration)', f14t, Mc, PF), ('Gaofen-2 23 November, outside calibration extent', f26t, GA & vall & ~PA, GF), ('WorldView-2 30 November, outside calibration extent', f26t, WA & vall & ~PA, WF)]:
    lab, sz = lab_sizes(f); size_px = sz[lab]; kept = f & (size_px >= MIN); rem = f & ~kept
    ref_total = (truth & A).sum(); tp_rem = (rem & truth & A).sum(); tp_kept = (kept & truth & A).sum()
    r = dict(reference=nm, removed_km2=(rem & A).sum() * KM2, kept_km2=(kept & A).sum() * KM2, removed_share_flooded=tp_rem / max((rem & A).sum(), 1), kept_share_flooded=tp_kept / max((kept & A).sum(), 1),
             reference_flooded_km2=ref_total * KM2, removed_flooded_km2=tp_rem * KM2, recall_lost_points=tp_rem / ref_total, reference_prevalence=ref_total / A.sum())
    for a, b in bins:
        mm = f & (size_px >= a) & (size_px <= b) & A; r['km2_%d_%d' % (a, b)] = mm.sum() * KM2; r['flooded_share_%d_%d' % (a, b)] = (mm & truth).sum() / max(mm.sum(), 1)
    rows.append(r)
cr = pd.DataFrame(rows); cr.to_csv(os.path.join(OUT, 'revision_cluster_removed_vs_reference.csv'), index=False); print(cr.round(3).T.to_string())
rm = raw14 & dom & ~F14; rows = []
for c, cn in CL.items():
    m = (lulc == c) & dom; rows.append([cn, (raw14 & m).sum() * KM2, (F14 & m).sum() * KM2, (rm & m).sum() * KM2, 100 * (rm & m).sum() / max((raw14 & m).sum(), 1), 100 * (rm & m).sum() / m.sum()])
rows.append(['All classes', (raw14 & dom).sum() * KM2, F14.sum() * KM2, rm.sum() * KM2, 100 * rm.sum() / (raw14 & dom).sum(), 100 * rm.sum() / dom.sum()])
rc = pd.DataFrame(rows, columns=['class', 'unfiltered_km2', 'filtered_km2', 'removed_km2', 'removed_pct_of_unfiltered', 'removed_pct_of_analysed_class']); rc.to_csv(os.path.join(OUT, 'revision_cluster_removed_by_class.csv'), index=False); print(rc.round(2).to_string(index=False))
# ---------------------------------------------------------------- 5. October reference scenes
v21 = rd('v_pre21')[0].astype(bool) & aoi; v9 = rd('v_pre9')[0].astype(bool) & aoi
A21 = cf(v21) & dom; A9 = cf(v9) & dom
print('areas', F14.sum() * KM2, A21.sum() * KM2, A9.sum() * KM2, '| main subset of pre21:', (F14 & A21).sum() / F14.sum(), '| pre9 subset of main:', (A9 & F14).sum() / A9.sum())
rows = []
for c, cn in CL.items():
    m = (lulc == c) & dom; rows.append([cn, m.sum() * KM2, (A9 & m).sum() * KM2, (F14 & m).sum() * KM2, (A21 & m).sum() * KM2, ((A21 & ~F14) & m).sum() * KM2])
rows.append(['All classes', dom.sum() * KM2, A9.sum() * KM2, F14.sum() * KM2, A21.sum() * KM2, (A21 & ~F14).sum() * KM2])
oc = pd.DataFrame(rows, columns=['class', 'analysed_km2', 'pre9_km2', 'main_km2', 'pre21_km2', 'pre21_not_main_km2']); oc['pre21_extra_share_of_total_extra_pct'] = 100 * oc.pre21_not_main_km2 / oc.pre21_not_main_km2.iloc[-1]
for a in ['pre9', 'main', 'pre21']: oc[a + '_pct_of_analysed'] = 100 * oc[a + '_km2'] / oc.analysed_km2
oc.to_csv(os.path.join(OUT, 'revision_pre_event_scene_by_class.csv'), index=False); print(oc.round(2).to_string(index=False))
Z = np.load(os.path.join(DG, 's1_100m_means.npz')); h100, w100 = Z['o09_VV'].shape
def blk(a): return a[:h100 * 10, :w100 * 10].reshape(h100, 10, w100, 10).mean((1, 3))
fr = {c: blk(((lulc == c) & dom).astype('float32')) for c in CL}
def wmean(d, w):
    ok = np.isfinite(d) & (w > 0); return float((d[ok] * w[ok]).sum() / w[ok].sum()), float(w[ok][d[ok] > 2].sum() / w[ok].sum()), float(w[ok][d[ok] < -2].sum() / w[ok].sum())
pairs = [('21 Oct minus 9 Oct', 'o21', 'o09'), ('2 Nov minus 9 Oct', 'n02', 'o09'), ('2 Nov minus 21 Oct', 'n02', 'o21'), ('14 Nov minus 9 Oct', 'n14', 'o09'), ('14 Nov minus 21 Oct', 'n14', 'o21')]
rows = []
for lab, a, b in pairs:
    for pol in ('VV', 'VH'):
        d = Z[a + '_' + pol] - Z[b + '_' + pol]
        for c, cn in CL.items():
            m, up, dn = wmean(d, fr[c]); rows.append([lab, pol, cn, m, 100 * up, 100 * dn])
        w = sum(fr.values()); m, up, dn = wmean(d, w); rows.append([lab, pol, 'All analysed', m, 100 * up, 100 * dn])
pd.DataFrame(rows, columns=['difference', 'polarisation', 'class', 'mean_dB', 'pct_cells_above_plus2dB', 'pct_cells_below_minus2dB']).to_csv(os.path.join(OUT, 'revision_pre_event_scene_backscatter.csv'), index=False)
bt = pd.DataFrame(rows, columns=['difference', 'polarisation', 'class', 'mean_dB', 'up', 'dn']); print(bt[bt.polarisation == 'VV'].round(2).to_string(index=False))
ch = json.load(open(os.path.join(DG, 'chirps_daily_mm.json'))); cdf = pd.DataFrame(ch, columns=['date', 'mm']); cdf['date'] = pd.to_datetime(cdf.date)
def rsum(a, b): return float(cdf[(cdf.date > a) & (cdf.date <= b)].mm.sum())
rain = [('15 Sep to 9 Oct', rsum('2023-09-14', '2023-10-09')), ('10 Oct to 21 Oct', rsum('2023-10-09', '2023-10-21')), ('22 Oct to 2 Nov', rsum('2023-10-21', '2023-11-02')), ('3 Nov to 14 Nov', rsum('2023-11-02', '2023-11-14')),
        ('3 days to 9 Oct', rsum('2023-10-06', '2023-10-09')), ('3 days to 21 Oct', rsum('2023-10-18', '2023-10-21')), ('3 days to 2 Nov', rsum('2023-10-30', '2023-11-02')), ('3 days to 14 Nov', rsum('2023-11-11', '2023-11-14'))]
pd.DataFrame(rain, columns=['interval', 'chirps_mm_area_mean']).to_csv(os.path.join(OUT, 'revision_chirps_rainfall.csv'), index=False); print(pd.DataFrame(rain, columns=['i', 'mm']).round(1).to_string(index=False))
np.save(os.path.join(DG, 'extra21_100m.npy'), blk((A21 & ~F14).astype('float32')))
np.save(os.path.join(DG, 'main14_100m.npy'), blk(F14.astype('float32')))
