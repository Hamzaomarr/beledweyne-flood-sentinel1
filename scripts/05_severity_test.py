"""
Does the size of the SAR backscatter drop carry information about inundation, so that an ordinal
severity class is justified? Test: P(UNOSAT optical says flooded | dVV bin), and whether a persistence count
(number of post-event dates flagged flooded) relates to UNOSAT-flooded probability.
Only the town extents covered by UNOSAT can be used. No water depth is available, so nothing here is depth.
"""
import numpy as np, rasterio, geopandas as gpd, glob, os, json, pandas as pd
from rasterio import features
from scipy import ndimage as ndi
BASE = r'.'
RAS = os.path.join(BASE, 'data', 'processed', 'town_rasters'); UN = os.path.join(BASE, 'data', 'raw', 'unosat_FL20231105SOM', 'extracted')
OUT = os.path.join(BASE, 'outputs', 'tables'); P = json.load(open(os.path.join(OUT, 'chosen_parameters.json')))
def rd(n):
    with rasterio.open(os.path.join(RAS, n + '.tif')) as s: return s.read().astype('float32'), s.transform, s.crs
dates = ['20231009', '20231021', '20231102', '20231114', '20231126', '20231208']
s1 = {d: rd('S1_' + d)[0] for d in dates}; _, tr, crs = rd('S1_20231021'); H, W = s1['20231021'].shape[1:]
valid = np.all([np.isfinite(v).all(0) for v in s1.values()], axis=0)
def shp(p): return gpd.read_file(glob.glob(os.path.join(UN, '**', p + '*.shp'), recursive=True)[0])
def burn(g):
    g = g.to_crs(crs); return features.rasterize([(x, 1) for x in g.geometry if x is not None], out_shape=(H, W), transform=tr, fill=0, dtype='uint8').astype(bool)
PA, PF, PW, PC = [burn(shp(n)) for n in ['PHR_20231112_AnalysisExtent_Beledweyne', 'PHR_20231112_FloodExtent_Beledweyne', 'PHR_20231112_WaterExtent_Beledweyne', 'PHR_20231112_CloudObstruction_Beledweyne']]
GA, GF = burn(shp('GF2_20231123_AnalysisExtent_Beledweyne')), burn(shp('GF2_20231123_FloodExtent_Beledweyne'))
PF &= PA; GF &= GA
k = P['filt']; sm = lambda a: ndi.median_filter(a, size=k, mode='nearest')
pre = (s1['20231009'] + s1['20231021']) / 2
dVV = {d: sm(s1[d][0] - pre[0]) for d in dates[2:]}; dVH = {d: sm(s1[d][1] - pre[1]) for d in dates[2:]}
darkpre = sm(pre[0]) < P['dark_cutoff'] if P.get('dark_cutoff') is not None else np.zeros((H, W), bool)
def rm_small(f, mn):
    if not mn or mn <= 1: return f
    lab, n = ndi.label(f, structure=np.ones((3, 3))); sz = np.bincount(lab.ravel()); keep = sz >= mn; keep[0] = False; return keep[lab]
flag = {d: rm_small(((dVV[d] <= -P['tVV']) | (dVH[d] <= -P['tVH'])) & ~darkpre, P.get('min_cluster_px')) for d in dates[2:]}   # minimum cluster size added after script 19

# 1) P(flooded | dVV bin)
bins = [(-99, -12), (-12, -9), (-9, -7), (-7, -5), (-5, -4), (-4, -3), (-3, -2), (-2, 0), (0, 99)]
rows = []
for nm, d, A, F in [('PHR 12Nov vs S1 14Nov', '20231114', PA & ~PC & valid & (PF | ~PW), PF), ('GF2 23Nov vs S1 26Nov', '20231126', GA & valid & ~PA, GF)]:
    for lo, hi in bins:
        m = A & (dVV[d] > lo) & (dVV[d] <= hi)
        rows.append(dict(pair=nm, dVV_bin='(%s, %s]' % (lo if lo > -99 else '-inf', hi if hi < 99 else '+inf'), px=int(m.sum()), P_unosat_flooded=F[m].mean() if m.sum() else np.nan))
t1 = pd.DataFrame(rows); t1.to_csv(os.path.join(OUT, 'severity_test_P_flooded_by_dVV_bin.csv'), index=False)
print(t1.round(3).to_string(index=False))

# 2) persistence: number of post-event dates (14 Nov, 26 Nov, 8 Dec) flagged
cnt = flag['20231114'].astype(int) + flag['20231126'].astype(int) + flag['20231208'].astype(int)
rows = []
for nm, A, F in [('PHR 12Nov', PA & ~PC & valid & (PF | ~PW), PF), ('GF2 23Nov outside PHR', GA & valid & ~PA, GF)]:
    for c in range(4):
        m = A & (cnt == c); rows.append(dict(ref=nm, dates_flagged=c, px=int(m.sum()), P_unosat_flooded=F[m].mean() if m.sum() else np.nan))
t2 = pd.DataFrame(rows); t2.to_csv(os.path.join(OUT, 'severity_test_persistence.csv'), index=False)
print('\nPersistence (dates flagged among 14 Nov, 26 Nov, 8 Dec):'); print(t2.round(3).to_string(index=False))

# 3) how does flagged-area evolve in the town box? (relative, same rule, for orientation only)
for d in dates[2:]:
    print(d, 'flagged share of valid pixels in GF2 analysis box: %.3f' % flag[d][GA & valid].mean())
