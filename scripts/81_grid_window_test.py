"""Separates the effect of counting flagged pixels on a coarser grid from the effect of the ground size of the 5 by 5 median window (town raster extent, 14 November,
rule without terrain mask and without cluster filter). Results are stored in outputs/tables/grid_window_test.json."""
import json, os, numpy as np, rasterio
from scipy import ndimage as ndi
BASE = r'.'
P = json.load(open(os.path.join(BASE, 'outputs', 'tables', 'chosen_parameters.json')))
RAS = os.path.join(BASE, 'data', 'processed', 'town_rasters')
def rd(n):
    with rasterio.open(os.path.join(RAS, n + '.tif')) as s: return s.read().astype('float32')
a9, a21, a14 = rd('S1_20231009'), rd('S1_20231021'), rd('S1_20231114')
k = P['filt']; sm = lambda a: ndi.median_filter(a, size=k, mode='nearest')
def flag(b9, b21, b14):
    pm = (b9 + b21) / 2
    dV = sm(b14[0] - pm[0]); dH = sm(b14[1] - pm[1]); dark = sm(pm[0]) < P['dark_cutoff']
    fl = ((dV <= -P['tVV']) | (dH <= -P['tVH'])) & ~dark
    return fl & np.isfinite(b21[0]) & np.isfinite(b14[0]) & np.isfinite(b9[0])
with np.errstate(invalid='ignore'): f = flag(a9, a21, a14)
res = {'flag_10m_km2': float(f.sum() / 1e4)}
h, w = (f.shape[0] // 2) * 2, (f.shape[1] // 2) * 2; f2 = f[:h, :w]
res['flag_10m_averaged_to_20m_km2'] = float(f2.reshape(h // 2, 2, w // 2, 2).mean(axis=(1, 3)).sum() * 400 / 1e6)
res['flag_10m_subsampled_20m_km2_by_offset'] = [float(f2[dy::2, dx::2].sum() * 400 / 1e6) for dy in (0, 1) for dx in (0, 1)]
res['inputs_sampled_at_20m_filter_5x5_km2_by_offset'] = []
for dy in (0, 1):
    for dx in (0, 1):
        with np.errstate(invalid='ignore'): fl2 = flag(*[x[:, dy::2, dx::2] for x in (a9, a21, a14)])
        res['inputs_sampled_at_20m_filter_5x5_km2_by_offset'].append(float(fl2.sum() * 400 / 1e6))
res['window_at_10m_km2_by_window_pixels'] = {}
for kk in (3, 5, 9, 11):
    sm = lambda a, kk=kk: ndi.median_filter(a, size=kk, mode='nearest')
    with np.errstate(invalid='ignore'): res['window_at_10m_km2_by_window_pixels'][str(kk)] = float(flag(a9, a21, a14).sum() / 1e4)
json.dump(res, open(os.path.join(BASE, 'outputs', 'tables', 'grid_window_test.json'), 'w'), indent=1); print(json.dumps(res, indent=1))
