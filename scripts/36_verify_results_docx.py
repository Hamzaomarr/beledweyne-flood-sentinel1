"""Independent check. Reads MANUSCRIPT_Results.docx tables back and compares every cell with the source CSV or JSON values, rounded half-up at the table precision."""
import docx, json, os, re, pandas as pd
from decimal import Decimal, ROUND_HALF_UP
B = r'.'; T = os.path.join(B, 'outputs', 'tables')
def r(x, d=2): return str(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP))
d = docx.Document(os.path.join(B, 'MANUSCRIPT_Results.docx'))
tabs = {}
_all = [[[c.text for c in row.cells] for row in t.rows][1:] for t in d.tables]; _map = {int(k): v for k, v in json.load(open(os.path.join(B, 'outputs', 'table_renumbering.json'))).items()}   # old table number -> number after the revision
for old, new in _map.items(): tabs[old] = _all[new - 4]
st = pd.read_csv(os.path.join(T, 'flood_stats_by_landcover.csv')).set_index('class_name'); lj = json.load(open(os.path.join(T, 'lulc_accuracy_vs_consensus.json')))
cl = pd.read_csv(os.path.join(T, 'validation_with_cluster_filter.csv')); va = pd.read_csv(os.path.join(T, 'validation_with_kappa_and_exclusion.csv'))
sn = pd.read_csv(os.path.join(T, 'sensitivity_flood_area_14Nov.csv')).set_index('variant'); mc = pd.read_csv(os.path.join(T, 'diagnostic_min_cluster_size_calibration.csv')).set_index('min_cluster_px')
sev = pd.read_csv(os.path.join(T, 'severity_test_P_flooded_by_dVV_bin.csv')); per = pd.read_csv(os.path.join(T, 'severity_test_persistence.csv'))
bad = 0; n = 0
def eq(tab, row, col, expect):
    global bad, n; n += 1; got = tabs[tab][row][col]
    if got != expect: bad += 1; print('MISMATCH table', tab, 'row', row, 'col', col, 'doc', got, 'source', expect)
cls = ['Cropland', 'Vegetation / rangeland', 'Built-up', 'Bare soil / sand']
for i, c in enumerate(cls):                                        # Table 5, 6, 7
    for j, col in enumerate(['domain_area', 'flood_2Nov', 'flood_14Nov', 'flood_26Nov', 'flood_8Dec']): eq(5, i, 1 + j, r(st.loc[c, col]))
    for j, col in enumerate(['pct_domain_flood_2Nov', 'pct_domain_flood_14Nov', 'pct_domain_flood_26Nov', 'pct_domain_flood_8Dec']): eq(6, i, 1 + j, r(st.loc[c, col]))
    for j, col in enumerate(['intensity1_14Nov', 'intensity2_14Nov', 'intensity3_14Nov', 'persist1', 'persist2', 'persist3']): eq(7, i, 1 + j, r(st.loc[c, col]))
for j, col in enumerate(['domain_area', 'flood_2Nov', 'flood_14Nov', 'flood_26Nov', 'flood_8Dec']): eq(5, 4, 1 + j, r(st.loc['ALL CLASSES', col]))
for j, col in enumerate(['pct_domain_flood_2Nov', 'pct_domain_flood_14Nov', 'pct_domain_flood_26Nov', 'pct_domain_flood_8Dec']): eq(6, 4, 1 + j, r(st.loc['ALL CLASSES', col]))
for j, col in enumerate(['intensity1_14Nov', 'intensity2_14Nov', 'intensity3_14Nov', 'persist1', 'persist2', 'persist3']): eq(7, 4, 1 + j, r(st.loc['ALL CLASSES', col]))
for i, c in enumerate(['Permanent water'] + cls[:0]): pass
order4 = ['Permanent water', 'Cropland', 'Vegetation / rangeland', 'Built-up', 'Bare soil / sand']                      # Table 4
for i, c in enumerate(order4): eq(4, i, 1, r(st.loc[c, 'aoi_area'])); eq(4, i, 2, str(sum(lj['confusion'][i]))); eq(4, i, 3, r(lj['producers'][i])); eq(4, i, 4, r(lj['users'][i]))
refs = ['PHR 12Nov (calibration)', 'GF2 23Nov (all)', 'GF2 23Nov (outside calib. extent)', 'WV2 30Nov (all)', 'WV2 30Nov (outside calib. extent)']      # Table 8
rowi = 0
for src, rule in [(cl, 'min cluster 100 px'), (cl, 'no cluster filter'), (va, 'fixed -2.0/-1.5 (paper values)')]:
    for ref in refs:
        x = src[(src.reference == ref) & (src.rule == rule)].iloc[0]
        for j, c in enumerate(['precision', 'recall', 'balanced_acc', 'kappa']): eq(8, rowi, 2 + j, r(x[c]))
        rowi += 1
variants = ['main (calibrated)', 'no dark exclusion', 'no HAND/slope mask', 'pre = 21 Oct only', 'pre = 9 Oct only', '3x3 filter', 'dVV-only rule (-2.5 dB)', 'paper-style fixed -2.0/-1.5, no filter']   # Table 13
for i, v in enumerate(variants): eq(13, i, 1, r(sn.loc[v, 'flooded_km2_14Nov'], 1)); eq(13, i, 2, r(sn.loc[v, 'flooded_km2_14Nov_no_cluster_filter'], 1))
for i, k in enumerate(mc.index): eq(11, i, 1, r(mc.loc[k, 'kappa'], 3)); eq(11, i, 2, r(mc.loc[k, 'precision'])); eq(11, i, 3, r(mc.loc[k, 'recall'])); eq(11, i, 4, r(mc.loc[k, 'flagged_km2']))
pl = sev[sev.pair.str.startswith('PHR')].P_unosat_flooded.tolist(); pg = sev[sev.pair.str.startswith('GF2')].P_unosat_flooded.tolist()      # Table 10
for i in range(9): eq(10, i, 1, r(pl[i])); eq(10, i, 2, r(pg[i]))
pp = per[per.ref == 'PHR 12Nov'].P_unosat_flooded.tolist(); pq = per[per.ref.str.startswith('GF2')].P_unosat_flooded.tolist()
for i in range(4): eq(10, 9 + i, 1, r(pp[i])); eq(10, 9 + i, 2, r(pq[i]))
print('table cells compared with source files:', n, '| mismatches:', bad)
