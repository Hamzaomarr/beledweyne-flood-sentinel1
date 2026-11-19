"""Automated re-verification of checkable claims in MANUSCRIPT_Methods.docx against the scripts, parameter file, installed packages and Crossref."""
import re, json, glob, os, sys, urllib.request, urllib.parse, importlib.metadata as md, docx
B = r'.'
d = docx.Document(os.path.join(B, 'MANUSCRIPT_Methods.docx'))
body = [p.text for p in d.paragraphs]; cells = [c.text for t in d.tables for r in t.rows for c in r.cells]
full = '\n'.join(body + cells); P = json.load(open(os.path.join(B, 'outputs', 'tables', 'chosen_parameters.json')))
scripts = {os.path.basename(p): open(p, encoding='utf-8-sig').read() for p in glob.glob(os.path.join(B, 'scripts', '*.py'))}
s07 = scripts['07_stats_fixedgrid_and_rasters.py']; allpy = '\n'.join(scripts.values())
res = []
def chk(name, ok, detail=''): res.append((name, bool(ok), detail))
# parameters
chk('VV threshold -4.0', f"-{P['tVV']:.1f} dB" in full, P['tVV']); chk('VH threshold -2.5', f"-{P['tVH']:.1f} dB" in full, P['tVH'])
chk('dark cut-off -16', f"-{abs(P['dark_cutoff']):.0f} dB" in full, P['dark_cutoff']); chk('window 5 by 5', '5 by 5' in full and P['filt'] == 5, P['filt'])
chk('minimum cluster 100', '100 flagged pixels' in full and P['min_cluster_px'] == 100, P['min_cluster_px'])
chk('dVV-only threshold -2.5', 'threshold of -2.5 dB' in full and P['dVV_only']['tVV'] == 2.5, P['dVV_only'])
# dates and windows
for dt in ['9 October', '21 October', '2 November', '14 November', '26 November', '8 December']: chk('S1 date ' + dt, dt in full)
chk('S1 dates in script 07', all(x in s07 for x in ['2023-10-09', '2023-10-21', '2023-11-02', '2023-11-14', '2023-11-26', '2023-12-08']))
chk('S2 window 1 Jan to 14 Mar', '1 January to 14 March 2023' in full and "'2023-01-01', '2023-03-15'" in s07, 'filterDate end exclusive')
chk('cloud below 20%', 'below 20%' in full and 'CLOUDY_PIXEL_PERCENTAGE' in s07 and 'lt' in s07)
chk('SCL classes 3,8,9,10,11', all(f'neq({k})' in s07 for k in [3, 8, 9, 10, 11]))
# assets, seeds, trees, sampling
for a in ['COPERNICUS/S1_GRD', 'COPERNICUS/S2_SR_HARMONIZED', 'ESA/WorldCover/v200', 'GOOGLE/DYNAMICWORLD/V1', 'JRC/GSW1_4/GlobalSurfaceWater', 'MERIT/Hydro/v1_0_1', 'COPERNICUS/DEM/GLO30']:
    chk('asset ' + a, a in full and a in allpy)
chk('RF 500 trees seed 42', 'numberOfTrees=500, seed=42' in s07 and '500 trees' in full and 'seed of 42' in full)
chk('sampling 500 per class seed 42 scale 10', 'classPoints=[500] * 5' in s07 and 'seed=42' in s07 and 'scale=10' in s07)
chk('block rule 0.05 mod 5 block 0 test', '0.05' in s07 and 'mod(5)' in s07 and "'blk', 0" in s07)
chk('orbit 35 descending IW', 'relativeOrbitNumber_start' in s07 and "'DESCENDING'" in s07 and "'IW'" in s07 and 'relative orbit 35' in full)
chk('HAND 10, slope 8', 'HAND_MAX, SLOPE_MAX = 10, 8' in s07 and '10 m' in full and '8 degrees' in full)
chk('JRC occurrence 75', 'jrc.gte(75)' in s07 and '75%' in full)
chk('intensity edges -5, -7', 'dv.lte(-5)' in s07 and 'dv.lte(-7)' in s07 and '-5 dB' in full and '-7 dB' in full)
chk('grid origin 480000/570000', '480000' in s07 and '570000' in s07 and '480000 m easting' in full)
chk('minimum cluster candidates', all(str(c) in full for c in [1, 5, 10, 20, 50, 100, 200, 500]) and 'cand = [1, 5, 10, 20, 50, 100, 200, 500]' in scripts['19_validate_with_cluster_filter.py'])
chk('grid search ranges', 'np.arange(0.5, 6.01, 0.25)' in scripts['03_calibrate_thresholds.py'] and 'np.arange(0.5, 4.01, 0.5)' in scripts['03_calibrate_thresholds.py'])
chk('dark candidates -14..-20, -22', '[None, -14, -15, -16, -17, -18, -19, -20, -22]' in scripts['04_sand_exclusion_and_robust_metrics.py'])
chk('severity bin edges', '[(-99, -12), (-12, -9), (-9, -7), (-7, -5), (-5, -4), (-4, -3), (-3, -2), (-2, 0), (0, 99)]' in scripts['05_severity_test.py'])
chk('WorldCover class min 500 px', 'm.sum() < 500' in scripts['04_sand_exclusion_and_robust_metrics.py'] and 'm.sum() < 500' in scripts['03_calibrate_thresholds.py'])
chk('fixed comparator -2.0/-1.5 no filter', "pre_img('21Oct'), 2.0, 1.5, 1, None" in scripts['04_sand_exclusion_and_robust_metrics.py'])
chk('64 tiles 10 m export', 'range(498000, 574001, 9500)' in open(os.path.join(B, 'scripts', '23_export_raw_flags_10m.py'), encoding='utf-8-sig').read() and '64 tiles' in full)
# software versions
for pkg, label in [('earthengine-api', 'earthengine-api'), ('rasterio', 'rasterio'), ('numpy', 'NumPy'), ('scipy', 'SciPy'), ('pandas', 'pandas'), ('geopandas', 'GeoPandas'), ('shapely', 'Shapely'), ('pyproj', 'pyproj'), ('matplotlib', 'Matplotlib')]:
    v = md.version(pkg); chk(f'version {label} {v}', f'{label} {v}' in full, v)
chk('version Python', f'Python {sys.version.split()[0]}' in full, sys.version.split()[0])
# DOIs against Crossref
dois = sorted(set(re.findall(r'10\.\d{4}/[^\s,;)]+', full))); dois = [x.rstrip('.') for x in dois]
for x in dois:
    try:
        w = json.load(urllib.request.urlopen('https://api.crossref.org/works/' + urllib.parse.quote(x), timeout=30))['message']
        chk('DOI ' + x, w.get('type') == 'journal-article' and not w.get('update-to'), (w['title'][0][:60], w['container-title'][0], w['issued']['date-parts'][0][0]))
    except Exception as e: chk('DOI ' + x, False, str(e)[:60])
# boundary scan
leak = re.findall(r'[^.]*\b\d[\d.,]*\s?(?:km²|km2|ha)\b[^.]*\.', '\n'.join(body))
chk('no area results in text', not leak, leak[:2])
pct = sorted(set(re.findall(r'[\d.]+%', '\n'.join(body)))); chk('percent tokens are parameters only (20%, 75%)', set(pct) <= {'20%', '75%'}, pct)
nums = re.findall(r'(?:precision|recall|kappa|accuracy)\s+(?:of|was|were)\s+0\.\d+', '\n'.join(body)); chk('no accuracy values in text', not nums, nums)
# figure/table order
order = [m.group(0) for m in re.finditer(r'\((Figure|Table) \d\)', '\n'.join(body))]; chk('figure and table citation order', order == ['(Figure 1)', '(Table 1)', '(Table 2)', '(Table 3)'], order)
fails = [r for r in res if not r[1]]
for n, ok, dt in res: print(('PASS ' if ok else 'FAIL ') + n + ('' if ok else '  -> ' + str(dt)))
print('\nchecks', len(res), '| passed', len(res) - len(fails), '| failed', len(fails))
