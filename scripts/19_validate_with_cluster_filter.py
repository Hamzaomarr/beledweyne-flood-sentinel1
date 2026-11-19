"""
Minimum cluster size, chosen on the CALIBRATION date only (Pleiades 12 Nov vs S1 14 Nov): the smallest size whose kappa is within 0.005 of the best
kappa over the candidate sizes. The rule is then scored, unchanged, on the independent dates (Gaofen-2 23 Nov, WorldView-2 30 Nov vs S1 26 Nov).
Clusters are 8-connected groups of flagged pixels, labelled on the whole 10 m town raster before any scoring mask.
"""
import numpy as np, rasterio, geopandas as gpd, glob, os, json, pandas as pd
from rasterio import features
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
GA, GF = burn(shp('GF2_20231123_AnalysisExtent_Beledweyne')), None; GF = burn(shp('GF2_20231123_FloodExtent_Beledweyne')) & GA
WA = burn(shp('WV2_20231130_AnalysisExtent_BeledweyneCity')); WF = burn(shp('WV2_20231130_FloodExtent_BeledweyneCity')) & WA
k = P['filt']; sm = lambda x: ndi.median_filter(x, size=k, mode='nearest'); pm = (s1['20231009'] + s1['20231021']) / 2
def flag(post):
    return (((sm(post[0] - pm[0]) <= -P['tVV']) | (sm(post[1] - pm[1]) <= -P['tVH'])) & ~(sm(pm[0]) < P['dark_cutoff'])) & vall
def rm_small(f, mn):
    if mn <= 1: return f
    lab, n = ndi.label(f, structure=np.ones((3, 3))); sz = np.bincount(lab.ravel()); keep = sz >= mn; keep[0] = False; return keep[lab]
def sc(pred, truth, m):
    p, t = pred[m], truth[m]; tp = (p & t).sum(); fp = (p & ~t).sum(); fn = (~p & t).sum(); tn = (~p & ~t).sum(); n = tp + fp + fn + tn
    rec = tp / max(tp + fn, 1); spec = tn / max(tn + fp, 1); prec = tp / max(tp + fp, 1); po = (tp + tn) / n; pe = ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / n ** 2
    return dict(precision=prec, recall=rec, specificity=spec, F1=2 * prec * rec / max(prec + rec, 1e-9), balanced_acc=(rec + spec) / 2, kappa=(po - pe) / max(1 - pe, 1e-9), IoU=tp / max(tp + fp + fn, 1), OA=po)
f14 = flag(s1['20231114']); M = PA & ~PC & vall & (PF | ~PW)
cand = [1, 5, 10, 20, 50, 100, 200, 500]; kap = {mn: sc(rm_small(f14, mn), PF, M)['kappa'] for mn in cand}
best = max(kap.values()); chosen = min(mn for mn in cand if kap[mn] >= best - 0.005)
print('calibration kappa by min cluster size:', {a: round(b, 3) for a, b in kap.items()}, '| chosen:', chosen)
f26 = flag(s1['20231126']); rows = []
for nm, f, A, truth in [('PHR 12Nov (calibration)', f14, M, PF), ('GF2 23Nov (all)', f26, GA & vall, GF), ('GF2 23Nov (outside calib. extent)', f26, GA & vall & ~PA, GF),
                        ('WV2 30Nov (all)', f26, WA & vall, WF), ('WV2 30Nov (outside calib. extent)', f26, WA & vall & ~PA, WF)]:
    for lab_, mn in [('no cluster filter', 1), ('min cluster %d px' % chosen, chosen)]:
        r = sc(rm_small(f, mn), truth, A); r.update(reference=nm, rule=lab_, flagged_km2=(rm_small(f, mn) & A).sum() / 1e4); rows.append(r)
t = pd.DataFrame(rows); t.to_csv(os.path.join(OUT, 'validation_with_cluster_filter.csv'), index=False)
print(t[['reference', 'rule', 'precision', 'recall', 'balanced_acc', 'kappa', 'IoU']].round(3).to_string(index=False))
json.dump(dict(P, min_cluster_px=int(chosen), min_cluster_rule='smallest size within 0.005 kappa of the best on the Pleiades calibration date, 8-connected'), open(os.path.join(OUT, 'chosen_parameters.json'), 'w'), indent=2)
