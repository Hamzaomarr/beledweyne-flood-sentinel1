"""Second-round (journal) revision analyses on local rasters. Block bootstrap confidence intervals, urban backscatter anomalies, threshold sensitivity,
land-cover accuracy intervals, rainfall between acquisitions, and the spatial distribution of built-up consensus pixels over the spatial blocks."""
import numpy as np, rasterio, geopandas as gpd, glob, os, json, pandas as pd
from rasterio import features
from rasterio.warp import reproject, Resampling
from scipy import ndimage as ndi, stats
BASE = r'.'; RAS = os.path.join(BASE, 'data', 'processed', 'town_rasters'); UN = os.path.join(BASE, 'data', 'raw', 'unosat_FL20231105SOM', 'extracted')
OUT = os.path.join(BASE, 'outputs', 'tables'); DG = os.path.join(BASE, 'data', 'processed', 'diag'); P = json.load(open(os.path.join(OUT, 'chosen_parameters.json')))
def rd(n):
    with rasterio.open(os.path.join(RAS, n + '.tif')) as s: return s.read().astype('float32'), s.transform, s.crs
dates = ['20231009', '20231021', '20231102', '20231114', '20231126', '20231208']
s1 = {d: rd('S1_' + d)[0] for d in dates}; _, tr, crs = rd('S1_20231021'); H, W = s1['20231021'].shape[1:]
vall = np.all([np.isfinite(v).all(0) for v in s1.values()], axis=0)
def shp(p): return gpd.read_file(glob.glob(os.path.join(UN, '**', p + '*.shp'), recursive=True)[0])
def burn(g): g = g.to_crs(crs); return features.rasterize([(x, 1) for x in g.geometry if x is not None], out_shape=(H, W), transform=tr, fill=0, dtype='uint8').astype(bool)
PA, PF, PW, PC = [burn(shp('PHR_20231112_' + n + '_Beledweyne')) for n in ['AnalysisExtent', 'FloodExtent', 'WaterExtent', 'CloudObstruction']]; PF &= PA
GA = burn(shp('GF2_20231123_AnalysisExtent_Beledweyne')); GF = burn(shp('GF2_20231123_FloodExtent_Beledweyne')) & GA
WA = burn(shp('WV2_20231130_AnalysisExtent_BeledweyneCity')); WF = burn(shp('WV2_20231130_FloodExtent_BeledweyneCity')) & WA
wc = np.zeros((H, W), 'uint8')
with rasterio.open(os.path.join(BASE, 'data', 'raw', 'worldcover_2021_v200', 'ESA_WorldCover_10m_2021_v200_N03E045_Map.tif')) as s: reproject(rasterio.band(s, 1), wc, dst_transform=tr, dst_crs=crs, resampling=Resampling.nearest)
k = P['filt']; sm = lambda x: ndi.median_filter(x, size=k, mode='nearest'); pm = (s1['20231009'] + s1['20231021']) / 2
SMV = sm(pm[0])
def dsm(d): return sm(s1[d][0] - pm[0]), sm(s1[d][1] - pm[1])
D14, D26 = dsm('20231114'), dsm('20231126')
def flag(D, tv=P['tVV'], th=P['tVH'], dark=P['dark_cutoff']): return (((D[0] <= -tv) | (D[1] <= -th)) & ~(SMV < dark)) & vall
def rm_small(f, mn=P['min_cluster_px']):
    lab, n = ndi.label(f, structure=np.ones((3, 3))); sz = np.bincount(lab.ravel()); keep = sz >= mn; keep[0] = False; return keep[lab]
f14 = rm_small(flag(D14)); f26 = rm_small(flag(D26))
M = PA & ~PC & vall & (PF | ~PW)
comps = {'Pleiades 12 Nov (calibration)': (f14, M, PF), 'Gaofen-2 23 Nov, whole extent': (f26, GA & vall, GF), 'Gaofen-2 23 Nov, outside calibration extent': (f26, GA & vall & ~PA, GF),
         'WorldView-2 30 Nov, whole extent': (f26, WA & vall, WF), 'WorldView-2 30 Nov, outside calibration extent': (f26, WA & vall & ~PA, WF)}
def metr(tp, fp, fn, tn):
    n = tp + fp + fn + tn; prec = tp / max(tp + fp, 1); rec = tp / max(tp + fn, 1); spec = tn / max(tn + fp, 1); po = (tp + tn) / n; pe = ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / n ** 2
    return prec, rec, (rec + spec) / 2, (po - pe) / max(1 - pe, 1e-12)
def block_counts(f, truth, m, bs):
    rr, cc = np.nonzero(m); p = f[rr, cc]; t = truth[rr, cc]; bid = (rr // bs) * (W // bs + 2) + (cc // bs)
    u, inv = np.unique(bid, return_inverse=True); out = np.zeros((len(u), 4))
    for j, v in enumerate([p & t, p & ~t, ~p & t, ~p & ~t]): out[:, j] = np.bincount(inv, weights=v.astype(float), minlength=len(u))
    return out
rng = np.random.default_rng(42); NB = 2000; rows = []
for nm, (f, m, truth) in comps.items():
    for bs in (50, 100, 200):
        bc = block_counts(f, truth, m, bs); tot = bc.sum(0); pt = metr(*tot); nb = len(bc)
        idx = rng.integers(0, nb, size=(NB, nb)); samp = bc[idx].sum(1); bs_m = np.array([metr(*s) for s in samp])
        lo, hi = np.percentile(bs_m, [2.5, 97.5], axis=0)
        # naive pixel-level normal approximation for comparison (kappa via same bootstrap of pixels is costly; use binomial CI for precision and recall)
        r = dict(comparison=nm, block_m=bs * 10, n_blocks=nb)
        for i, nmx in enumerate(['precision', 'recall', 'balanced_accuracy', 'kappa']): r[nmx] = pt[i]; r[nmx + '_lo'] = lo[i]; r[nmx + '_hi'] = hi[i]
        rows.append(r)
ci = pd.DataFrame(rows); ci.to_csv(os.path.join(OUT, 'revision2_block_bootstrap_ci.csv'), index=False)
print(ci[ci.block_m == 1000][['comparison', 'n_blocks', 'precision', 'precision_lo', 'precision_hi', 'recall', 'recall_lo', 'recall_hi', 'kappa', 'kappa_lo', 'kappa_hi']].round(3).to_string(index=False))
print(ci[['comparison', 'block_m', 'kappa', 'kappa_lo', 'kappa_hi', 'recall_lo', 'recall_hi']].round(3).to_string(index=False))
# fixed thresholds (against 21 Oct, no filter) for kappa CI
def fixed(post): return (((s1[post][0] - s1['20231021'][0]) <= -2.0) | ((s1[post][1] - s1['20231021'][1]) <= -1.5)) & vall
fx14, fx26 = fixed('20231114'), fixed('20231126'); rows = []
for nm, (f, m, truth), ff in [(list(comps)[0], comps[list(comps)[0]], fx14), (list(comps)[2], comps[list(comps)[2]], fx26), (list(comps)[4], comps[list(comps)[4]], fx26)]:
    bc = block_counts(ff, truth, m, 100); tot = bc.sum(0); pt = metr(*tot); nb = len(bc); idx = rng.integers(0, nb, size=(NB, nb)); bs_m = np.array([metr(*s) for s in bc[idx].sum(1)]); lo, hi = np.percentile(bs_m, [2.5, 97.5], axis=0)
    # paired difference calibrated minus fixed in kappa
    bc0 = block_counts(f, truth, m, 100); d = np.array([metr(*bc0[i].sum(0))[3] - metr(*bc[i].sum(0))[3] for i in idx[:1000]]); dlo, dhi = np.percentile(d, [2.5, 97.5])
    rows.append(dict(comparison=nm, precision=pt[0], recall=pt[1], balanced_accuracy=pt[2], kappa=pt[3], kappa_lo=lo[3], kappa_hi=hi[3], kappa_diff_vs_final=metr(*bc0.sum(0))[3] - pt[3], diff_lo=dlo, diff_hi=dhi))
fxd = pd.DataFrame(rows); fxd.to_csv(os.path.join(OUT, 'revision2_fixed_threshold_ci.csv'), index=False); print(fxd.round(3).to_string(index=False))
# ---------------------------------------------------------------- positive backscatter anomalies in flooded built-up
rows = []
for nm, D, raw, truth, A in [('Pleiades 12 Nov vs 14 Nov', D14, 'n14', PF, M), ('Gaofen-2 23 Nov vs 26 Nov, outside calibration extent', D26, 'n26', GF, GA & vall & ~PA)]:
    d_raw = (s1['20231114' if raw == 'n14' else '20231126'][0] - pm[0])
    for cls, cn in [(50, 'Built-up'), (40, 'Cropland')]:
        for flooded, lab in [(True, 'UNOSAT flooded'), (False, 'UNOSAT not flooded')]:
            mm = A & (wc == cls) & (truth if flooded else ~truth)
            if mm.sum() == 0: continue
            v = D[0][mm]; vh = D[1][mm]; vr = d_raw[mm]
            rows.append(dict(pair=nm, wc_class=cn, reference=lab, pixels=int(mm.sum()), area_km2=mm.sum() * 1e-4, mean_dVV=float(v.mean()), median_dVV=float(np.median(v)), share_dVV_gt_plus3=float((v > 3).mean()), share_dVV_gt_plus1=float((v > 1).mean()), share_dVV_le_minus4=float((v <= -4).mean()),
                             share_dVH_gt_plus3=float((vh > 3).mean()), share_unfiltered_dVV_gt_plus3=float((vr > 3).mean()), share_flagged_final=float((((f14 if raw == 'n14' else f26))[mm]).mean())))
pa = pd.DataFrame(rows); pa.to_csv(os.path.join(OUT, 'revision2_urban_positive_anomalies.csv'), index=False); print(pa.round(3).to_string(index=False))
# ---------------------------------------------------------------- threshold sensitivity (town extent, final pipeline)
rows = []
def run(tv, th, lab):
    a = rm_small(flag(D14, tv, th)); b = rm_small(flag(D26, tv, th))
    c0 = metr(*block_counts(a, PF, M, 100).sum(0)); c1 = metr(*block_counts(b, GF, GA & vall & ~PA, 100).sum(0))
    rows.append(dict(setting=lab, tVV=tv, tVH=th, flagged_km2_calibration_mask=(a & M).sum() * 1e-4, flagged_km2_town_14Nov=(a & vall).sum() * 1e-4, kappa_calibration=c0[3], recall_calibration=c0[1], precision_calibration=c0[0], kappa_gf2_outside=c1[3], recall_gf2_outside=c1[1], precision_gf2_outside=c1[0]))
for tv in (3.0, 3.5, 4.0, 4.5, 5.0): run(tv, P['tVH'], 'VV threshold %.1f dB' % tv)
for th in (1.5, 2.0, 2.5, 3.0, 3.5): run(P['tVV'], th, 'VH threshold %.1f dB' % th)
ts = pd.DataFrame(rows); ts.to_csv(os.path.join(OUT, 'revision2_threshold_sensitivity.csv'), index=False); print(ts.round(3).to_string(index=False))
# ---------------------------------------------------------------- land-cover accuracy intervals
def wilson(x, n, z=1.96):
    if n == 0: return (np.nan, np.nan)
    p = x / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return c - h, c + h
def cp(x, n, a=0.05):
    lo = 0 if x == 0 else stats.beta.ppf(a / 2, x, n - x + 1); hi = 1 if x == n else stats.beta.ppf(1 - a / 2, x + 1, n - x); return lo, hi
ho = json.load(open(os.path.join(OUT, 'lulc_accuracy_vs_consensus.json'))); cv = json.load(open(os.path.join(OUT, 'revision_lulc_blockcv.json')))
cls = ['Water', 'Cropland', 'Vegetation or rangeland', 'Built-up', 'Bare soil or sand']; rows = []
for tag, cmx in [('hold-out (block 0)', np.array(ho['confusion'])), ('5-fold spatial block cross-validation', np.array(cv['confusion']))]:
    n = cmx.sum(); rows.append(dict(set=tag, measure='Overall', cls='All', x=int(np.trace(cmx)), n=int(n), est=np.trace(cmx) / n, lo=wilson(np.trace(cmx), n)[0], hi=wilson(np.trace(cmx), n)[1]))
    for i, c in enumerate(cls):
        for meas, x, nn in [('Producer', cmx[i, i], cmx[i].sum()), ('User', cmx[i, i], cmx[:, i].sum())]:
            lo, hi = cp(int(x), int(nn)) if nn < 30 else wilson(x, nn); rows.append(dict(set=tag, measure=meas, cls=c, x=int(x), n=int(nn), est=x / nn if nn else np.nan, lo=lo, hi=hi))
lc = pd.DataFrame(rows); lc.to_csv(os.path.join(OUT, 'revision2_lulc_accuracy_ci.csv'), index=False); print(lc.round(3).to_string(index=False))
# ---------------------------------------------------------------- rainfall between acquisitions
c1 = json.load(open(os.path.join(DG, 'chirps_daily_mm.json'))); c2 = json.load(open(os.path.join(DG, 'chirps_daily_mm_nov_dec.json')))
cd = pd.DataFrame(c1 + c2, columns=['date', 'mm']).drop_duplicates('date'); cd['date'] = pd.to_datetime(cd.date); cd = cd.set_index('date').mm
def rs(a, b): return float(cd[(cd.index > pd.Timestamp(a)) & (cd.index <= pd.Timestamp(b))].sum())
rain = {'12 to 14 Nov (UNOSAT Pleiades to Sentinel-1)': rs('2023-11-12', '2023-11-14'), '23 to 26 Nov (Gaofen-2 to Sentinel-1)': rs('2023-11-23', '2023-11-26'), '26 to 30 Nov (Sentinel-1 to WorldView-2)': rs('2023-11-26', '2023-11-30'),
        '14 to 26 Nov (between the Sentinel-1 dates)': rs('2023-11-14', '2023-11-26'), '26 Nov to 8 Dec': rs('2023-11-26', '2023-12-08'), '15 to 23 Nov': rs('2023-11-14', '2023-11-23')}
json.dump(rain, open(os.path.join(OUT, 'revision2_chirps_between_acquisitions.json'), 'w'), indent=1); print(rain); print(cd['2023-11-09':'2023-12-08'].round(1).to_string())
# ---------------------------------------------------------------- built-up consensus pixels over the spatial blocks
cc = json.load(open(os.path.join(OUT, 'revision_consensus_counts_by_cell.json'))); rows = []
for c, d in cc.items():
    for cell, n in d.items():
        i, j = int(cell) // 100, int(cell) % 100; rows.append(dict(cls=int(c), cell=int(cell), i=i + 900, j=j + 89, blk=((i + 900) + (j + 89)) % 5, n=n))
cb = pd.DataFrame(rows); tab = cb.pivot_table(index='cls', columns='blk', values='n', aggfunc='sum', fill_value=0); tab['total'] = tab.sum(1); print(tab)
bu = cb[cb.cls == 3].sort_values('n', ascending=False); bu['share'] = bu.n / bu.n.sum(); bu['cum'] = bu.share.cumsum(); print(bu.head(8)); print('cells with built-up consensus', len(bu), 'cells total', cb.cell.nunique(), 'cells holding 90%:', int((bu.cum < 0.9).sum() + 1))
tab.to_csv(os.path.join(OUT, 'revision2_consensus_pixels_by_block.csv')); bu.to_csv(os.path.join(OUT, 'revision2_builtup_consensus_by_cell.csv'), index=False)
