"""
Sentence-level fact-check of MANUSCRIPT_Results.docx. Each numeric sentence is matched against the cells of the tables in the same document, in the order the sentence states them.
Tables are separately verified against the CSV/JSON outputs by 36_verify_results_docx.py. Values that come from figures or logs are recomputed here from the rasters.
Writes outputs/results_factcheck_rows.json for the audit document.
"""
import docx, re, json, os, numpy as np, rasterio, geopandas as gpd, glob
from rasterio import features
from scipy import ndimage as ndi
B = r'.'
d = docx.Document(os.path.join(B, 'MANUSCRIPT_Results.docx'))
paras = [(p.text, p.style.name) for p in d.paragraphs]
TB = {}
for i, t in enumerate(d.tables): TB[4 + i] = [[c.text for c in row.cells] for row in t.rows][1:]
def row(n, label): return next(r for r in TB[n] if r[0] == label)
sents = []; section = ''
for txt, sty in paras:
    if sty.startswith('Heading'): section = txt; continue
    if re.match(r'(Figure|Table) \d+\.|Note\.', txt) or not txt.strip() or txt == 'Results': continue
    for s in re.split(r'(?<=[.!?])\s+(?=[A-Z])', txt): sents.append((section, s))
def nums(s):
    s = s.replace('Gaofen-2', 'Gaofen').replace('WorldView-2', 'WorldView')
    s = re.sub(r'\b(?:Figure|Table) \d+\b', ' ', s)
    s = re.sub(r'\b\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December)\b', ' ', s)
    s = re.sub(r'(?:below|above|between)\s+-?\d+(?:\s+and\s+-?\d+)?\s+dB', ' ', s)
    s = re.sub(r'\b10 km\b|\b10 m\b|\b20 m\b|\b30 m\b|\b3 by 3\b|fewer than \d+ pixels|of 5, 10, 20, 50, 100, 200 and 500 pixels', ' ', s)
    return re.findall(r'-?\d+(?:\.\d+)?', s)
def find(snippet):
    m = [x for x in sents if snippet in x[1]]; assert len(m) == 1, (snippet, len(m)); return m[0]
rows = []
def check(code, snippet, expected, source, note=''):
    sec, s = find(snippet); got = nums(s); ok = got == [str(e) for e in expected]
    rows.append(dict(id=code, section=sec, claim=s, status='Accurate' if ok else 'Incorrect', source=source, value='; '.join(str(e) for e in expected) if ok else 'text %s vs source %s' % (got, expected), correct='yes' if ok else 'no', belongs='yes', note=note))
    if not ok: print('MISMATCH', code, got, expected)
C = lambda n, lab, *cols: [row(n, lab)[c] for c in cols]
all4 = ['Cropland', 'Vegetation or rangeland', 'Built-up', 'Bare soil or sand']
oa = re.search(r'Overall agreement (\S+), kappa (\S+)\.', ' '.join(p for p, _ in paras)); OA, KP = oa.group(1), oa.group(2)
# ---- 1 land cover
check('R1', 'The map covered', C(4, 'All classes', 1), 'Table 4 all classes, mapped area')
check('R2', 'Vegetation or rangeland occupied', [row(4, 'Vegetation or rangeland')[1], row(4, 'Bare soil or sand')[1], row(4, 'Cropland')[1], row(4, 'Built-up')[1], row(4, 'Water')[1]], 'Table 4 mapped area, classes in the order stated')
check('R3', 'Across 373', [row(4, 'All classes')[2], OA, KP], 'Table 4 all classes reference points, and Table 4 note for overall agreement and kappa')
lab5 = ['Water', 'Cropland', 'Vegetation or rangeland', 'Built-up', 'Bare soil or sand']
check('R4', "Producer's agreement was", [row(4, l)[3] for l in lab5] + [row(4, l)[4] for l in lab5], "Table 4 producer's then user's agreement, water, cropland, vegetation or rangeland, built-up, bare soil or sand")
check('R5', 'The reference points numbered', [row(4, l)[2] for l in lab5], 'Table 4 reference points')
# ---- 2 flagged extent
check('R6', 'Within an analysed area', C(5, 'All classes', 1, 2, 3, 4, 5), 'Table 5 all classes, analysed area then the four dates')
check('R7', 'The largest flagged area on every date', C(5, 'Cropland', 3, 4, 5, 2), 'Table 5 cropland, 14 November, 26 November, 8 December, 2 November')
check('R8', 'Built-up land followed', C(5, 'Built-up', 2, 3, 4, 5), 'Table 5 built-up, four dates in order')
check('R9', 'Bare soil or sand had 0.68', C(5, 'Bare soil or sand', 2, 3, 4, 5) + C(5, 'Vegetation or rangeland', 2, 3, 4, 5), 'Table 5 bare soil or sand then vegetation or rangeland')
check('R10', 'The analysed area comprised', [row(5, 'Cropland')[1], row(5, 'Vegetation or rangeland')[1], row(5, 'Built-up')[1], row(5, 'Bare soil or sand')[1]], 'Table 5 analysed area by class')
check('R11', 'Expressed as a share', [row(6, 'Built-up')[2], row(6, 'Cropland')[2], row(6, 'Bare soil or sand')[2], row(6, 'Vegetation or rangeland')[2], row(6, 'All classes')[2]], 'Table 6, 14 November column')
check('R12', 'On 26 November the shares', [row(6, 'Built-up')[3], row(6, 'Cropland')[3], row(6, 'Bare soil or sand')[3], row(6, 'Vegetation or rangeland')[3], row(6, 'All classes')[3]], 'Table 6, 26 November column')
check('R13', 'On 8 December they were', [row(6, 'Cropland')[4], row(6, 'Built-up')[4], row(6, 'Bare soil or sand')[4], row(6, 'Vegetation or rangeland')[4], row(6, 'All classes')[4]], 'Table 6, 8 December column')
check('R14', 'On 2 November the overall share', [row(6, 'All classes')[1], row(6, 'Cropland')[1], row(6, 'Built-up')[1], row(6, 'Bare soil or sand')[1], row(6, 'Vegetation or rangeland')[1]], 'Table 6, 2 November column')
# ---- 3 intensity and persistence
check('R15', 'Of the 225.84 km² flagged', [row(5, 'All classes')[3]] + C(7, 'All classes', 1, 2, 3), 'Table 5 all classes 14 November, Table 7 all classes weak, moderate, strong')
check('R16', 'Strong change was also', [row(7, 'Cropland')[3], row(7, 'Built-up')[3], row(7, 'Bare soil or sand')[3]], 'Table 7 strong column')
check('R17', 'In vegetation or rangeland the weak class', C(7, 'Vegetation or rangeland', 1, 2, 3), 'Table 7 vegetation or rangeland, weak, moderate, strong')
check('R18', 'The remaining class values', C(7, 'Cropland', 1, 2) + C(7, 'Built-up', 1, 2) + C(7, 'Bare soil or sand', 1, 2), 'Table 7 weak and moderate for cropland, built-up, bare soil or sand')
check('R19', 'Counting the dates', C(7, 'All classes', 4, 5, 6), 'Table 7 all classes, one, two, three dates')
check('R20', 'Cropland had 27.05', C(7, 'Cropland', 4, 5, 6) + C(7, 'Built-up', 4, 5, 6), 'Table 7 persistence for cropland then built-up')
check('R21', 'Bare soil or sand had 11.30', C(7, 'Bare soil or sand', 4, 5, 6), 'Table 7 persistence, bare soil or sand')
check('R22', 'In vegetation or rangeland most', C(7, 'Vegetation or rangeland', 4, 5, 6), 'Table 7 persistence, vegetation or rangeland')
# ---- 4 agreement with UNOSAT
T8 = TB[8]; r8 = lambda i: T8[i][2:6]
check('R23', 'Against the Pléiades mapping of 12 November', r8(0) + r8(5) + r8(10), 'Table 8 rows final rule, without cluster filter, fixed thresholds, Pléiades')
check('R24', 'Outside the calibration extent, the Gaofen-2', r8(2) + r8(7) + r8(12), 'Table 8 Gaofen-2 outside calibration extent, three rules')
check('R25', 'The WorldView-2 mapping of 30 November gave', r8(4) + r8(9) + r8(14), 'Table 8 WorldView-2 outside calibration extent, three rules')
check('R26', 'Over the whole extent of the Gaofen-2', r8(1) + r8(6) + r8(11) + r8(3) + r8(8) + r8(13), 'Table 8 whole-extent rows, Gaofen-2 then WorldView-2, three rules each')
wl = lambda n, c: [row(9, n)[c]]
cls9 = ['Cropland', 'Grassland', 'Shrubland', 'Tree cover', 'Built-up', 'Bare or sparse vegetation', 'Permanent water bodies']
check('R27', 'On the Pléiades date, precision and recall', sum([[row(9, l)[1], row(9, l)[2]] for l in cls9], []), 'Table 9 Pléiades precision and recall by class in the order stated')
check('R28', 'For the Gaofen-2 mapping outside the calibration extent, the corresponding', sum([[row(9, l)[3], row(9, l)[4]] for l in ['Cropland', 'Grassland', 'Shrubland', 'Tree cover', 'Built-up', 'Bare or sparse vegetation', 'Permanent water bodies']], []), 'Table 9 Gaofen-2 precision and recall by class')
# ---- 5 relation to UNOSAT share
T10 = TB[10]
check('R29', 'For the Pléiades and 14 November pair', [T10[i][1] for i in range(9)], 'Table 10 Pléiades column, nine ΔVV bins in order')
check('R30', 'For the Gaofen-2 and 26 November pair', [T10[i][2] for i in range(9)], 'Table 10 Gaofen-2 column, nine ΔVV bins in order')
check('R31', 'Against the Pléiades mapping it was', [T10[i][1] for i in range(9, 13)], 'Table 10 Pléiades column, dates flagged 0 to 3')
check('R32', 'Against the Gaofen-2 mapping outside the Pléiades extent', [T10[i][2] for i in range(9, 13)], 'Table 10 Gaofen-2 column, dates flagged 0 to 3')
# ---- 6 minimum cluster size
T11 = TB[11]
check('R33', 'On the calibration date, kappa rose', [T11[i][1] for i in range(8)], 'Table 11 kappa column, 1 to 500 pixels')
check('R34', 'Over the same sizes', [T11[i][4] for i in range(8)] + [T11[0][2], T11[7][2], T11[0][3], T11[7][3]], 'Table 11 flagged area column, precision first and last, recall first and last')
T12 = TB[12]
check('R35', 'In the unfiltered flag', T12[0][1:6], 'Table 12 eastern rangeland row')
check('R36', 'In a south-western rangeland box', T12[1][1:6], 'Table 12 south-western rangeland row')
# ---- 7 sensitivity
T13 = TB[13]
check('R37', 'The flagged area of 14 November was 225.8', [T13[0][1], T13[0][2]], 'Table 13 main configuration, with and without cluster filter')
check('R38', 'Omitting the dark-surface exclusion', [T13[1][1], T13[2][1], T13[5][1]], 'Table 13 no dark-surface exclusion, no terrain mask, three by three filter')
check('R39', 'The rule using ΔVV alone', [T13[6][1]], 'Table 13 ΔVV only rule')
check('R40', 'Using only the 9 October scene', [T13[4][1], T13[3][1]], 'Table 13 pre-event 9 October only, then 21 October only')
check('R41', 'The fixed thresholds without a median filter', [T13[7][1]], 'Table 13 fixed thresholds without filter')
check('R42', 'Without the cluster filter the same configurations', [T13[1][2], T13[2][2], T13[5][2], T13[6][2], T13[4][2], T13[3][2], T13[7][2]], 'Table 13 without cluster filter column, in the order of the previous sentences')
# ---- 8 grid
T14 = TB[14]
check('R43', 'Over the extent of the town rasters', [T14[0][1], T14[1][1], T14[2][1]], 'Table 14 first three rows')
check('R44', 'With the inputs reprojected', [T14[3][1], T14[4][1]], 'Table 14 reprojected row and local row')
check('R45', 'The exported 10 m flag layer', [T14[5][1]], 'Table 14 exported layer row')
# ---------------------------------------------------------------- independent recomputation of values that do not come from a CSV
P = json.load(open(os.path.join(B, 'outputs', 'tables', 'chosen_parameters.json')))
RAS = os.path.join(B, 'data', 'processed', 'town_rasters'); UN = os.path.join(B, 'data', 'raw', 'unosat_FL20231105SOM', 'extracted')
def rdt(n):
    with rasterio.open(os.path.join(RAS, n + '.tif')) as s: return s.read().astype('float32'), s.transform, s.crs, s.bounds
dates = ['20231009', '20231021', '20231102', '20231114', '20231126', '20231208']
s1 = {k: rdt('S1_' + k)[0] for k in dates}; _, tr, crs, bnds = rdt('S1_20231021'); H, W = s1['20231021'].shape[1:]
vall = np.all([np.isfinite(v).all(0) for v in s1.values()], axis=0)
def shp(p): return gpd.read_file(glob.glob(os.path.join(UN, '**', p + '*.shp'), recursive=True)[0])
def burn(g): g = g.to_crs(crs); return features.rasterize([(x, 1) for x in g.geometry if x is not None], out_shape=(H, W), transform=tr, fill=0, dtype='uint8').astype(bool)
PA, PF, PW, PC = [burn(shp('PHR_20231112_' + n + '_Beledweyne')) for n in ['AnalysisExtent', 'FloodExtent', 'WaterExtent', 'CloudObstruction']]; PF &= PA
k = P['filt']; sm = lambda x: ndi.median_filter(x, size=k, mode='nearest'); pm = (s1['20231009'] + s1['20231021']) / 2; p14 = s1['20231114']
fl = (((sm(p14[0] - pm[0]) <= -P['tVV']) | (sm(p14[1] - pm[1]) <= -P['tVH'])) & ~(sm(pm[0]) < P['dark_cutoff'])) & vall
lab, n = ndi.label(fl, structure=np.ones((3, 3))); sz = np.bincount(lab.ravel()); keep = sz >= P['min_cluster_px']; keep[0] = False; fl = keep[lab]
M = PA & ~PC & vall & (PF | ~PW)
tp = (fl & PF & M).sum() / 1e4; fp = (fl & ~PF & M).sum() / 1e4; fn = (~fl & PF & M).sum() / 1e4
got = ['%.1f' % tp, '%.1f' % fp, '%.1f' % fn]
sec, s = find('In the town, the radar and UNOSAT flood extents agreed'); ok = nums(s) == got
rows.append(dict(id='R46', section=sec, claim=s, status='Accurate' if ok else 'Incorrect', source='Recomputed from the town rasters and UNOSAT Pléiades polygons, the same values as the Figure 6 legend', value='agree %s, radar only %s, UNOSAT only %s km2' % tuple(got), correct='yes' if ok else 'no', belongs='yes', note='No table holds these three values. They are traceable only to the Figure 6 legend and to this recomputation.'))
with rasterio.open(os.path.join(B, 'data', 'processed', 'raw10m', 'flag_14Nov.tif')) as s_:
    ras = s_.read(1); r0, c0 = rasterio.transform.rowcol(s_.transform, bnds.left, bnds.top); r1, c1 = rasterio.transform.rowcol(s_.transform, bnds.right, bnds.bottom)
v = '%.3f' % (ras[r0:r1, c0:c1].astype(bool).sum() * 1e-4)
rows.append(dict(id='R47', section='Effect of the evaluation grid', claim='Table 14 row, exported 10 m flag layer, 51.123', status='Accurate' if v == '51.123' else 'Incorrect', source='Recomputed from data/processed/raw10m/flag_14Nov.tif over the town raster extent', value=v + ' km2', correct='yes' if v == '51.123' else 'no', belongs='yes', note='Value previously traceable only to a run log, now recomputed.'))
# ---------------------------------------------------------------- derived and qualitative statements, recomputed from table values
f = lambda x: float(x)
cl = {l: row(5, l) for l in all4}
def top(col, k=0): return sorted(all4, key=lambda l: -f(cl[l][col]))[k]
q = []
q.append(('R48', 'The largest flagged area on every date after 2 November lay in cropland', all(top(c) == 'Cropland' for c in (3, 4, 5)), 'Table 5 columns 14 November, 26 November, 8 December, largest class'))
q.append(('R49', 'Built-up land followed', all(top(c, 1) == 'Built-up' for c in (2, 3, 4, 5)), 'Table 5, second largest class on each of the four dates'))
q.append(('R50', 'flagged proportion on 14 November ... built-up, cropland, bare soil or sand, vegetation or rangeland in descending order', [l for l in sorted(all4, key=lambda l: -f(row(6, l)[2]))] == ['Built-up', 'Cropland', 'Bare soil or sand', 'Vegetation or rangeland'], 'Table 6 14 November column ordering'))
q.append(('R51', 'On 26 November the shares were stated in descending order', [l for l in sorted(all4, key=lambda l: -f(row(6, l)[3]))] == ['Built-up', 'Cropland', 'Bare soil or sand', 'Vegetation or rangeland'], 'Table 6 26 November column ordering'))
q.append(('R52', 'On 8 December the shares were stated in descending order', [l for l in sorted(all4, key=lambda l: -f(row(6, l)[4]))] == ['Cropland', 'Built-up', 'Bare soil or sand', 'Vegetation or rangeland'], 'Table 6 8 December column ordering'))
q.append(('R53', 'so the strong class was the largest', f(row(7, 'All classes')[3]) > f(row(7, 'All classes')[1]) > f(row(7, 'All classes')[2]), 'Table 7 all classes strong, weak, moderate'))
q.append(('R54', 'Strong change was also the largest class in cropland, built-up land and bare soil or sand', all(f(row(7, l)[3]) == max(f(x) for x in row(7, l)[1:4]) for l in ('Cropland', 'Built-up', 'Bare soil or sand')), 'Table 7 weak, moderate, strong by class'))
q.append(('R55', 'In vegetation or rangeland the weak class was largest', f(row(7, 'Vegetation or rangeland')[1]) == max(f(x) for x in row(7, 'Vegetation or rangeland')[1:4]), 'Table 7 vegetation or rangeland'))
vp = [f(x) for x in row(7, 'Vegetation or rangeland')[4:7]]
q.append(('R56', 'In vegetation or rangeland most of the flagged area was flagged on a single date', vp[0] / sum(vp) > 0.5, 'Table 7 persistence columns, one date is %.1f%% of the three persistence values summed' % (100 * vp[0] / sum(vp))))
tot = row(7, 'All classes'); q.append(('R57', 'Arithmetic, weak plus moderate plus strong equals the flagged area of 14 November', abs(f(tot[1]) + f(tot[2]) + f(tot[3]) - f(row(5, 'All classes')[3])) < 0.011, 'Table 7 all classes sum %.2f against Table 5 %.2f' % (f(tot[1]) + f(tot[2]) + f(tot[3]), f(row(5, 'All classes')[3]))))
bad = []
for l in all4 + ['All classes']:
    for ci, pc in zip((2, 3, 4, 5), (1, 2, 3, 4)):
        if abs(100 * f(row(5, l)[ci]) / f(row(5, l)[1]) - f(row(6, l)[pc])) > 0.011 and l != 'All classes': bad.append((l, ci))
        if l == 'All classes' and abs(100 * f(row(5, l)[ci]) / f(row(5, l)[1]) - f(row(6, l)[pc])) > 0.011: bad.append((l, ci))
q.append(('R58', 'Table 6 shares equal Table 5 flagged area divided by analysed area times 100, all classes and dates', not bad, 'Recomputed from Table 5, mismatches %s' % bad))
p1 = [f(T10[i][1]) for i in range(9)]; p2 = [f(T10[i][2]) for i in range(9)]
q.append(('R59', 'The share ... was lower for smaller changes in backscatter, Pléiades pair', np.mean(p1[:3]) > np.mean(p1[-3:]), 'Table 10, mean of three largest-change bins %.2f against three smallest %.2f' % (np.mean(p1[:3]), np.mean(p1[-3:]))))
q.append(('R60', 'The share ... was lower for smaller changes in backscatter, Gaofen-2 pair', all(a >= b for a, b in zip(p2, p2[1:])), 'Table 10, Gaofen-2 values never increase across the nine bins'))
q.append(('R61', 'The flooded share also rose with the number of dates flagged, both pairs', all(f(T10[i][1]) < f(T10[i + 1][1]) for i in range(9, 12)) and all(f(T10[i][2]) <= f(T10[i + 1][2]) for i in range(9, 12)), 'Table 10, Pléiades strictly increasing, Gaofen-2 non-decreasing with 0.92 at two and three dates'))
kap = [f(T11[i][1]) for i in range(8)]; fa = [f(T11[i][4]) for i in range(8)]
q.append(('R62', 'kappa rose across minimum cluster sizes', all(a <= b for a, b in zip(kap, kap[1:])), 'Table 11, non-decreasing, 0.580 at both 100 and 200 pixels'))
q.append(('R63', 'flagged area fell, precision rose and recall fell across minimum cluster sizes', all(a > b for a, b in zip(fa, fa[1:])) and f(T11[7][2]) > f(T11[0][2]) and f(T11[7][3]) < f(T11[0][3]), 'Table 11'))
for code, claim, ok, src in q:
    rows.append(dict(id=code, section='Derived statement', claim=claim, status='Accurate' if ok else 'Incorrect', source=src, value='', correct='yes' if ok else 'no', belongs='yes', note=''))
    if not ok: print('MISMATCH', code)
json.dump(rows, open(os.path.join(B, 'outputs', 'results_factcheck_rows.json'), 'w'), ensure_ascii=False, indent=1)
print('numeric and derived claims checked:', len(rows), '| incorrect:', sum(1 for r in rows if r['status'] != 'Accurate'))
