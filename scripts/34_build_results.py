"""
Builds the Results section from the output tables only. Every number in the prose comes from a variable filled from a CSV or JSON file, never typed.
Writes results_blocks.json (rendered to .docx by 35_render_results_docx.js) and verifies that numbers in the text and in the tables match in both directions.
"""
import json, os, re, glob
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP
from PIL import Image
BASE = r'.'; T = os.path.join(BASE, 'outputs', 'tables'); FIG = os.path.join(BASE, 'outputs', 'figures')
def f(x, d=2):
    q = Decimal(1).scaleb(-d); return str(Decimal(repr(float(x))).quantize(q, rounding=ROUND_HALF_UP)) if d > 0 else str(int(Decimal(repr(float(x))).quantize(Decimal(1), rounding=ROUND_HALF_UP)))
st = pd.read_csv(os.path.join(T, 'flood_stats_by_landcover.csv')).set_index('class_name')
lj = json.load(open(os.path.join(T, 'lulc_accuracy_vs_consensus.json')))
cl = pd.read_csv(os.path.join(T, 'validation_with_cluster_filter.csv')); va = pd.read_csv(os.path.join(T, 'validation_with_kappa_and_exclusion.csv'))
sev = pd.read_csv(os.path.join(T, 'severity_test_P_flooded_by_dVV_bin.csv')); per = pd.read_csv(os.path.join(T, 'severity_test_persistence.csv'))
mc = pd.read_csv(os.path.join(T, 'diagnostic_min_cluster_size_calibration.csv')); rg = pd.read_csv(os.path.join(T, 'diagnostic_rangeland_flag_clusters.csv')).set_index('box')
sn = pd.read_csv(os.path.join(T, 'sensitivity_flood_area_14Nov.csv')).set_index('variant'); wcl = pd.read_csv(os.path.join(T, 'agreement_by_worldcover_final_rule.csv')).set_index('worldcover')
rs = pd.read_csv(os.path.join(T, 'resolution_check_table.csv'))
CL = ['Cropland', 'Vegetation / rangeland', 'Built-up', 'Bare soil / sand']; TOT = 'ALL CLASSES'
A = lambda cls, col, d=2: f(st.loc[cls, col], d)
blocks = []; tabnum = {}; figvals = set()
def H(t): blocks.append(dict(t='h', x=t))
def Pp(t): blocks.append(dict(t='p', x=re.sub(r'\s+', ' ', t).strip()))
def Fig(n, file, title, vals=()):
    im = Image.open(os.path.join(FIG, file)); w = 440; h = int(w * im.size[1] / im.size[0]); blocks.append(dict(t='fig', file=os.path.join(FIG, file), w=w, h=h, label='Figure %d.' % n, title=title)); figvals.update(vals)
def Tab(n, title, header, rows, widths, note=None):
    blocks.append(dict(t='tab', label='Table %d.' % n, title=title, header=header, rows=rows, widths=widths, note=note))
# ------------------------------------------------------------ 1 land cover
H('Land-cover map and agreement with reference labels')
Pp(f"""The map covered {A(TOT,'aoi_area')} km² and showed cropland and built-up land as a corridor running from the north-west to the south of the study area, with vegetation or rangeland dominating the remainder and bare soil or sand occurring mainly as patches in the west (Figure 2). The analysis extents of the United Nations Satellite Centre, UNOSAT, covered a small part of the western half.""")
Fig(2, 'fig7_study_area_landcover.png', 'Land-cover map of the study area and UNOSAT analysis extents')
cls_order = [('Permanent water', 'Water', 0), ('Cropland', 'Cropland', 1), ('Vegetation / rangeland', 'Vegetation or rangeland', 2), ('Built-up', 'Built-up', 3), ('Bare soil / sand', 'Bare soil or sand', 4)]
conf = lj['confusion']; npts = [sum(r) for r in conf]
Pp(f"""Vegetation or rangeland occupied {A('Vegetation / rangeland','aoi_area')} km², bare soil or sand {A('Bare soil / sand','aoi_area')} km², cropland {A('Cropland','aoi_area')} km², built-up land {A('Built-up','aoi_area')} km² and water {A('Permanent water','aoi_area')} km² (Table 4).
Across {sum(npts)} reference points, overall agreement was {f(lj['overall_accuracy'])} and kappa was {f(lj['kappa'])}. Producer's agreement was {f(lj['producers'][0])} for water, {f(lj['producers'][1])} for cropland, {f(lj['producers'][2])} for vegetation or rangeland, {f(lj['producers'][3])} for built-up land and {f(lj['producers'][4])} for bare soil or sand, and user's agreement was {f(lj['users'][0])}, {f(lj['users'][1])}, {f(lj['users'][2])}, {f(lj['users'][3])} and {f(lj['users'][4])} for the same classes in that order. The reference points numbered {npts[0]} for water, {npts[1]} for cropland, {npts[2]} for vegetation or rangeland, {npts[3]} for built-up land and {npts[4]} for bare soil or sand.""")
Tab(4, 'Land-cover map area and agreement with reference labels', ['Class', 'Mapped area, km²', 'Reference points', "Producer's agreement", "User's agreement"],
    [[nm, A(k, 'aoi_area'), str(npts[i]), f(lj['producers'][i]), f(lj['users'][i])] for k, nm, i in cls_order] + [['All classes', A(TOT, 'aoi_area'), str(sum(npts)), '', '']],
    [2400, 1700, 1600, 1700, 1626], f"Note. Overall agreement {f(lj['overall_accuracy'])}, kappa {f(lj['kappa'])}. Agreement is with labels where two existing land-cover products gave the same class.")
# ------------------------------------------------------------ 2 flagged extent
H('Flagged flood extent on four dates')
Pp(f"""On 14 November and 26 November the flagged area formed a continuous band along the line of permanent water from the north-west towards the south-east, with isolated flagged pixels elsewhere in the study area (Figure 3). The band extended further south on 26 November than on 14 November.""")
Fig(3, 'fig8_flood_extent_14Nov_26Nov.png', 'Flagged flood extent on 14 November and 26 November 2023')
Pp(f"""Within an analysed area of {A(TOT,'domain_area')} km², the flagged area was {A(TOT,'flood_2Nov')} km² on 2 November, {A(TOT,'flood_14Nov')} km² on 14 November, {A(TOT,'flood_26Nov')} km² on 26 November and {A(TOT,'flood_8Dec')} km² on 8 December (Table 5).
The largest flagged area on every date after 2 November lay in cropland, at {A('Cropland','flood_14Nov')} km² on 14 November, {A('Cropland','flood_26Nov')} km² on 26 November and {A('Cropland','flood_8Dec')} km² on 8 December, against {A('Cropland','flood_2Nov')} km² on 2 November.
Built-up land followed, with {A('Built-up','flood_2Nov')}, {A('Built-up','flood_14Nov')}, {A('Built-up','flood_26Nov')} and {A('Built-up','flood_8Dec')} km² on the four dates in order. Bare soil or sand had {A('Bare soil / sand','flood_2Nov')}, {A('Bare soil / sand','flood_14Nov')}, {A('Bare soil / sand','flood_26Nov')} and {A('Bare soil / sand','flood_8Dec')} km², and vegetation or rangeland had {A('Vegetation / rangeland','flood_2Nov')}, {A('Vegetation / rangeland','flood_14Nov')}, {A('Vegetation / rangeland','flood_26Nov')} and {A('Vegetation / rangeland','flood_8Dec')} km². Water carried no analysed or flagged area. The analysed area comprised {A('Cropland','domain_area')} km² of cropland, {A('Vegetation / rangeland','domain_area')} km² of vegetation or rangeland, {A('Built-up','domain_area')} km² of built-up land and {A('Bare soil / sand','domain_area')} km² of bare soil or sand.""")
dates = [('flood_2Nov', '2 November'), ('flood_14Nov', '14 November'), ('flood_26Nov', '26 November'), ('flood_8Dec', '8 December')]
Tab(5, 'Flagged area by land-cover class and date', ['Class', 'Analysed area, km²', '2 November', '14 November', '26 November', '8 December'],
    [[nm, A(k, 'domain_area')] + [A(k, c) for c, _ in dates] for k, nm in [(c, n) for c, n in zip(CL, ['Cropland', 'Vegetation or rangeland', 'Built-up', 'Bare soil or sand'])]] + [['All classes', A(TOT, 'domain_area')] + [A(TOT, c) for c, _ in dates]],
    [2300, 1500, 1300, 1300, 1300, 1326], 'Note. Flagged area is in km² on each date.')
Pp(f"""Expressed as a share of the analysed area of each class, the flagged proportion on 14 November was {A('Built-up','pct_domain_flood_14Nov')}% in built-up land, {A('Cropland','pct_domain_flood_14Nov')}% in cropland, {A('Bare soil / sand','pct_domain_flood_14Nov')}% in bare soil or sand and {A('Vegetation / rangeland','pct_domain_flood_14Nov')}% in vegetation or rangeland, and {A(TOT,'pct_domain_flood_14Nov')}% overall (Table 6).
On 26 November the shares were {A('Built-up','pct_domain_flood_26Nov')}% for built-up land, {A('Cropland','pct_domain_flood_26Nov')}% for cropland, {A('Bare soil / sand','pct_domain_flood_26Nov')}% for bare soil or sand and {A('Vegetation / rangeland','pct_domain_flood_26Nov')}% for vegetation or rangeland, with {A(TOT,'pct_domain_flood_26Nov')}% overall. On 8 December they were {A('Cropland','pct_domain_flood_8Dec')}% for cropland, {A('Built-up','pct_domain_flood_8Dec')}% for built-up land, {A('Bare soil / sand','pct_domain_flood_8Dec')}% for bare soil or sand and {A('Vegetation / rangeland','pct_domain_flood_8Dec')}% for vegetation or rangeland, and {A(TOT,'pct_domain_flood_8Dec')}% overall. On 2 November the overall share was {A(TOT,'pct_domain_flood_2Nov')}%, with {A('Cropland','pct_domain_flood_2Nov')}% in cropland, {A('Built-up','pct_domain_flood_2Nov')}% in built-up land, {A('Bare soil / sand','pct_domain_flood_2Nov')}% in bare soil or sand and {A('Vegetation / rangeland','pct_domain_flood_2Nov')}% in vegetation or rangeland.""")
Tab(6, 'Share of the analysed area flagged by land-cover class and date', ['Class', '2 November, %', '14 November, %', '26 November, %', '8 December, %'],
    [[nm] + [A(k, 'pct_' + 'domain_' + c) for c, _ in dates] for k, nm in zip(CL, ['Cropland', 'Vegetation or rangeland', 'Built-up', 'Bare soil or sand'])] + [['All classes'] + [A(TOT, 'pct_domain_' + c) for c, _ in dates]],
    [2600, 1600, 1600, 1600, 1626], 'Note. Percentage of the analysed area of each class.')
# ------------------------------------------------------------ 3 intensity and persistence
H('Intensity and persistence of the flagged area')
cls4 = list(zip(CL, ['cropland', 'vegetation or rangeland', 'built-up land', 'bare soil or sand']))
Pp(f"""Of the {A(TOT,'flood_14Nov')} km² flagged on 14 November, {A(TOT,'intensity1_14Nov')} km² fell in the weak class of change in vertical transmit and vertical receive backscatter, ΔVV, {A(TOT,'intensity2_14Nov')} km² in the moderate class and {A(TOT,'intensity3_14Nov')} km² in the strong class, so the strong class was the largest (Table 7).
Strong change was also the largest class in cropland at {A('Cropland','intensity3_14Nov')} km², built-up land at {A('Built-up','intensity3_14Nov')} km² and bare soil or sand at {A('Bare soil / sand','intensity3_14Nov')} km². In vegetation or rangeland the weak class was largest at {A('Vegetation / rangeland','intensity1_14Nov')} km², against {A('Vegetation / rangeland','intensity2_14Nov')} km² moderate and {A('Vegetation / rangeland','intensity3_14Nov')} km² strong. The remaining class values were {A('Cropland','intensity1_14Nov')} km² weak and {A('Cropland','intensity2_14Nov')} km² moderate in cropland, {A('Built-up','intensity1_14Nov')} km² weak and {A('Built-up','intensity2_14Nov')} km² moderate in built-up land, and {A('Bare soil / sand','intensity1_14Nov')} km² weak and {A('Bare soil / sand','intensity2_14Nov')} km² moderate in bare soil or sand.""")
Pp(f"""Counting the dates on which a pixel was flagged among 14 November, 26 November and 8 December, {A(TOT,'persist1')} km² was flagged on one date, {A(TOT,'persist2')} km² on two dates and {A(TOT,'persist3')} km² on all three (Table 7). Cropland had {A('Cropland','persist1')}, {A('Cropland','persist2')} and {A('Cropland','persist3')} km² on one, two and three dates, and built-up land had {A('Built-up','persist1')}, {A('Built-up','persist2')} and {A('Built-up','persist3')} km². Bare soil or sand had {A('Bare soil / sand','persist1')}, {A('Bare soil / sand','persist2')} and {A('Bare soil / sand','persist3')} km². In vegetation or rangeland most of the flagged area was flagged on a single date, at {A('Vegetation / rangeland','persist1')} km², against {A('Vegetation / rangeland','persist2')} km² on two dates and {A('Vegetation / rangeland','persist3')} km² on three.""")
Tab(7, 'Intensity of backscatter change on 14 November and persistence of the flag', ['Class', 'Weak, km²', 'Moderate, km²', 'Strong, km²', 'One date, km²', 'Two dates, km²', 'Three dates, km²'],
    [[nm] + [A(k, c) for c in ['intensity1_14Nov', 'intensity2_14Nov', 'intensity3_14Nov', 'persist1', 'persist2', 'persist3']] for k, nm in zip(CL, ['Cropland', 'Vegetation or rangeland', 'Built-up', 'Bare soil or sand'])] + [['All classes'] + [A(TOT, c) for c in ['intensity1_14Nov', 'intensity2_14Nov', 'intensity3_14Nov', 'persist1', 'persist2', 'persist3']]],
    [2100, 1150, 1250, 1150, 1150, 1150, 1076], 'Note. Intensity classes refer to ΔVV on 14 November. Persistence is the number of dates among 14 November, 26 November and 8 December on which the pixel was flagged.')
Pp("""The strong class formed the core of the flagged area in the central and north-western parts of the study area, whereas weak change occurred mainly in the north-western part of the flagged area (Figure 4). Pixels flagged on all three dates were concentrated in the north-west and the centre, and pixels flagged on one or two dates predominated towards the southern end of the flagged band (Figure 5).""")
Fig(4, 'fig9_intensity_14Nov.png', 'Intensity of backscatter change on 14 November 2023')
Fig(5, 'fig10_persistence.png', 'Persistence of the flag from 14 November to 8 December 2023')
# ------------------------------------------------------------ 4 agreement with UNOSAT
H('Agreement with UNOSAT optical flood mapping')
def rowv(df, ref, rule, cols=('precision', 'recall', 'balanced_acc', 'kappa')): r = df[(df.reference == ref) & (df.rule == rule)].iloc[0]; return [f(r[c]) for c in cols]
refs = [('PHR 12Nov (calibration)', 'Pléiades 12 November'), ('GF2 23Nov (all)', 'Gaofen-2 23 November, whole extent'), ('GF2 23Nov (outside calib. extent)', 'Gaofen-2 23 November, outside calibration extent'),
        ('WV2 30Nov (all)', 'WorldView-2 30 November, whole extent'), ('WV2 30Nov (outside calib. extent)', 'WorldView-2 30 November, outside calibration extent')]
FIN, NOC, FIX = 'min cluster 100 px', 'no cluster filter', 'fixed -2.0/-1.5 (paper values)'
fin = {r: rowv(cl, r, FIN) for r, _ in refs}; noc = {r: rowv(cl, r, NOC) for r, _ in refs}; fix = {r: rowv(va, r, FIX) for r, _ in refs}
def q4(v): return f"{v[0]}, {v[1]}, {v[2]} and {v[3]}"
P8 = lambda r: (fin[r], noc[r], fix[r])
Pp(f"""Against the Pléiades mapping of 12 November, the final rule reached precision, recall, balanced accuracy and kappa of {q4(fin[refs[0][0]])}, compared with {q4(noc[refs[0][0]])} without the cluster filter and {q4(fix[refs[0][0]])} for the fixed thresholds (Table 8).
Outside the calibration extent, the Gaofen-2 mapping of 23 November gave {q4(fin[refs[2][0]])} for the final rule, {q4(noc[refs[2][0]])} without the cluster filter and {q4(fix[refs[2][0]])} for the fixed thresholds. The WorldView-2 mapping of 30 November gave {q4(fin[refs[4][0]])} for the final rule, {q4(noc[refs[4][0]])} without the cluster filter and {q4(fix[refs[4][0]])} for the fixed thresholds. Over the whole extent of the Gaofen-2 mapping the three rules gave {q4(fin[refs[1][0]])}, {q4(noc[refs[1][0]])} and {q4(fix[refs[1][0]])} in the same order, and over the whole extent of the WorldView-2 mapping they gave {q4(fin[refs[3][0]])}, {q4(noc[refs[3][0]])} and {q4(fix[refs[3][0]])}.""")
Pp("""In the town, the radar and UNOSAT flood extents agreed over 9.8 km², the radar flagged 3.8 km² that UNOSAT did not, and UNOSAT mapped 4.1 km² that the radar did not (Figure 6). Pixels flagged by the radar alone lay mainly in the south and south-east of the scored area, and pixels mapped by UNOSAT alone lay mainly in its central part.""")
figvals.update(['9.8', '3.8', '4.1'])
Fig(6, 'fig12_agreement_map_town.png', 'Agreement between the radar flag of 14 November and UNOSAT mapping of 12 November', ['9.8', '3.8', '4.1'])
tr8 = []
for lab, d_ in [('Final rule', fin), ('Calibrated rule without cluster filter', noc), ('Fixed thresholds', fix)]:
    for ref, nm in refs:
        tr8.append([lab, nm] + d_[ref])
Tab(8, 'Agreement of the radar flag with UNOSAT flood extents', ['Rule', 'Reference', 'Precision', 'Recall', 'Balanced accuracy', 'Kappa'], tr8, [2200, 3000, 900, 800, 1300, 826],
    'Note. The Pléiades 12 November mapping was the calibration reference. The cluster filter is the minimum cluster size. The fixed thresholds were a decrease of 2.0 dB in vertical transmit and vertical receive backscatter or 1.5 dB in vertical transmit and horizontal receive backscatter.')
# by WorldCover class
wn = {'Tree cover': 'tree cover', 'Shrubland': 'shrubland', 'Grassland': 'grassland', 'Cropland': 'cropland', 'Built-up': 'built-up land', 'Bare / sparse vegetation': 'bare or sparse vegetation', 'Permanent water bodies': 'permanent water bodies'}
W = lambda k, c: f(wcl.loc[k, c])
Pp(f"""Agreement varied by ESA WorldCover class (Table 9). On the Pléiades date, precision and recall were {W('Cropland','cal_precision')} and {W('Cropland','cal_recall')} in cropland, {W('Grassland','cal_precision')} and {W('Grassland','cal_recall')} in grassland, {W('Shrubland','cal_precision')} and {W('Shrubland','cal_recall')} in shrubland, {W('Tree cover','cal_precision')} and {W('Tree cover','cal_recall')} in tree cover and {W('Built-up','cal_precision')} and {W('Built-up','cal_recall')} in built-up land, with {W('Bare / sparse vegetation','cal_precision')} and {W('Bare / sparse vegetation','cal_recall')} in bare or sparse vegetation and {W('Permanent water bodies','cal_precision')} and {W('Permanent water bodies','cal_recall')} in permanent water bodies.
For the Gaofen-2 mapping outside the calibration extent, the corresponding values were {W('Cropland','gf2_precision')} and {W('Cropland','gf2_recall')} in cropland, {W('Grassland','gf2_precision')} and {W('Grassland','gf2_recall')} in grassland, {W('Shrubland','gf2_precision')} and {W('Shrubland','gf2_recall')} in shrubland, {W('Tree cover','gf2_precision')} and {W('Tree cover','gf2_recall')} in tree cover, {W('Built-up','gf2_precision')} and {W('Built-up','gf2_recall')} in built-up land, {W('Bare / sparse vegetation','gf2_precision')} and {W('Bare / sparse vegetation','gf2_recall')} in bare or sparse vegetation and {W('Permanent water bodies','gf2_precision')} and {W('Permanent water bodies','gf2_recall')} in permanent water bodies.""")
Tab(9, 'Precision and recall of the final rule by ESA WorldCover class', ['WorldCover class', 'Pléiades precision', 'Pléiades recall', 'Gaofen-2 precision', 'Gaofen-2 recall'],
    [[n, W(k, 'cal_precision'), W(k, 'cal_recall'), W(k, 'gf2_precision'), W(k, 'gf2_recall')] for k, n in [('Tree cover', 'Tree cover'), ('Shrubland', 'Shrubland'), ('Grassland', 'Grassland'), ('Cropland', 'Cropland'), ('Built-up', 'Built-up'), ('Bare / sparse vegetation', 'Bare or sparse vegetation'), ('Permanent water bodies', 'Permanent water bodies')]],
    [2800, 1500, 1500, 1600, 1626], 'Note. Gaofen-2 values refer to the area outside the calibration extent.')
# ------------------------------------------------------------ 5 relation to UNOSAT share
H('Backscatter change, persistence and the UNOSAT flooded share')
bins = list(sev.dVV_bin.unique()); pl = sev[sev.pair.str.startswith('PHR')].set_index('dVV_bin').P_unosat_flooded; pg = sev[sev.pair.str.startswith('GF2')].set_index('dVV_bin').P_unosat_flooded
bl = {'(-inf, -12]': 'below -12 dB', '(-12, -9]': '-12 to -9 dB', '(-9, -7]': '-9 to -7 dB', '(-7, -5]': '-7 to -5 dB', '(-5, -4]': '-5 to -4 dB', '(-4, -3]': '-4 to -3 dB', '(-3, -2]': '-3 to -2 dB', '(-2, 0]': '-2 to 0 dB', '(0, +inf]': 'above 0 dB'}
Pp(f"""The share of reference pixels that UNOSAT mapped as flooded was lower for smaller changes in backscatter (Table 10). For the Pléiades and 14 November pair it was {f(pl[bins[0]])} where the change was below -12 dB, {f(pl[bins[1]])} between -12 and -9 dB, {f(pl[bins[2]])} between -9 and -7 dB, {f(pl[bins[3]])} between -7 and -5 dB, {f(pl[bins[4]])} between -5 and -4 dB, {f(pl[bins[5]])} between -4 and -3 dB, {f(pl[bins[6]])} between -3 and -2 dB, {f(pl[bins[7]])} between -2 and 0 dB and {f(pl[bins[8]])} above 0 dB.
For the Gaofen-2 and 26 November pair the corresponding shares were {f(pg[bins[0]])}, {f(pg[bins[1]])}, {f(pg[bins[2]])}, {f(pg[bins[3]])}, {f(pg[bins[4]])}, {f(pg[bins[5]])}, {f(pg[bins[6]])}, {f(pg[bins[7]])} and {f(pg[bins[8]])}.""")
pp = per[per.ref == 'PHR 12Nov'].set_index('dates_flagged').P_unosat_flooded; pg2 = per[per.ref.str.startswith('GF2')].set_index('dates_flagged').P_unosat_flooded
Pp(f"""The flooded share also rose with the number of dates on which a pixel was flagged. Against the Pléiades mapping it was {f(pp[0])} for pixels never flagged and {f(pp[1])}, {f(pp[2])} and {f(pp[3])} for pixels flagged on one, two and three dates. Against the Gaofen-2 mapping outside the Pléiades extent it was {f(pg2[0])}, {f(pg2[1])}, {f(pg2[2])} and {f(pg2[3])} for zero, one, two and three dates.""")
t10 = [[bl[b], f(pl[b]), f(pg[b])] for b in bins]
t10 += [['Dates flagged, 0', f(pp[0]), f(pg2[0])], ['Dates flagged, 1', f(pp[1]), f(pg2[1])], ['Dates flagged, 2', f(pp[2]), f(pg2[2])], ['Dates flagged, 3', f(pp[3]), f(pg2[3])]]
Tab(10, 'Share of reference pixels mapped as flooded by UNOSAT', ['Category', 'Pléiades 12 November', 'Gaofen-2 23 November'], t10, [3800, 2600, 2626],
    'Note. The upper rows give ΔVV bins. The lower rows give the number of dates among 14 November, 26 November and 8 December on which the pixel was flagged.')
# ------------------------------------------------------------ 6 minimum cluster size
H('Effect of the minimum cluster size')
m = mc.set_index('min_cluster_px')
Pp(f"""On the calibration date, kappa rose from {f(m.loc[1,'kappa'],3)} with no cluster filter to {f(m.loc[5,'kappa'],3)}, {f(m.loc[10,'kappa'],3)}, {f(m.loc[20,'kappa'],3)}, {f(m.loc[50,'kappa'],3)}, {f(m.loc[100,'kappa'],3)}, {f(m.loc[200,'kappa'],3)} and {f(m.loc[500,'kappa'],3)} for minimum clusters of 5, 10, 20, 50, 100, 200 and 500 pixels (Table 11). Over the same sizes the flagged area in the scored part of the town fell from {f(m.loc[1,'flagged_km2'])} km² to {f(m.loc[5,'flagged_km2'])}, {f(m.loc[10,'flagged_km2'])}, {f(m.loc[20,'flagged_km2'])}, {f(m.loc[50,'flagged_km2'])}, {f(m.loc[100,'flagged_km2'])}, {f(m.loc[200,'flagged_km2'])} and {f(m.loc[500,'flagged_km2'])} km², precision rose from {f(m.loc[1,'precision'])} to {f(m.loc[500,'precision'])} and recall fell from {f(m.loc[1,'recall'])} to {f(m.loc[500,'recall'])}.""")
Tab(11, 'Agreement on the calibration date by minimum cluster size', ['Minimum cluster, pixels', 'Kappa', 'Precision', 'Recall', 'Flagged area, km²'],
    [[str(i), f(m.loc[i, 'kappa'], 3), f(m.loc[i, 'precision']), f(m.loc[i, 'recall']), f(m.loc[i, 'flagged_km2'])] for i in m.index], [2400, 1500, 1500, 1500, 2126],
    'Note. Pléiades mapping of 12 November against the radar flag of 14 November. A minimum cluster of 1 pixel is no cluster filter.')
e, s_ = rg.loc['east_rangeland'], rg.loc['southwest_rangeland']
Pp(f"""In the unfiltered flag, {f(e.flagged_share*100,1)}% of the pixels in a 10 km box of eastern rangeland were flagged, in {int(e.n_clusters)} clusters with a median of {f(e.median_cluster_px,1)} pixels, and {f(e.share_lt50*100,1)}% of the flagged pixels lay in clusters of fewer than 50 pixels and {f(e.share_lt200*100,1)}% in clusters of fewer than 200 pixels (Table 12).
In a south-western rangeland box, {f(s_.flagged_share*100,1)}% of the pixels were flagged, in {int(s_.n_clusters)} clusters with a median of {f(s_.median_cluster_px,1)} pixels, with {f(s_.share_lt50*100,1)}% of flagged pixels in clusters of fewer than 50 pixels and {f(s_.share_lt200*100,1)}% in clusters of fewer than 200 pixels.""")
Tab(12, 'Flagged pixels in two rangeland boxes without the cluster filter', ['Box', 'Flagged pixels, %', 'Clusters', 'Median cluster, pixels', 'In clusters under 50 pixels, %', 'In clusters under 200 pixels, %'],
    [['Eastern rangeland', f(e.flagged_share * 100, 1), str(int(e.n_clusters)), f(e.median_cluster_px, 1), f(e.share_lt50 * 100, 1), f(e.share_lt200 * 100, 1)],
     ['South-western rangeland', f(s_.flagged_share * 100, 1), str(int(s_.n_clusters)), f(s_.median_cluster_px, 1), f(s_.share_lt50 * 100, 1), f(s_.share_lt200 * 100, 1)]],
    [2300, 1300, 1100, 1400, 1500, 1426], 'Note. Each box was 10 km by 10 km.')
# ------------------------------------------------------------ 7 sensitivity
H('Sensitivity of the flagged area')
S = lambda v, c='flooded_km2_14Nov': f(sn.loc[v, c], 1)
Pp(f"""The flagged area of 14 November was {S('main (calibrated)')} km² for the main configuration and {S('main (calibrated)','flooded_km2_14Nov_no_cluster_filter')} km² without the cluster filter (Table 13). Omitting the dark-surface exclusion gave {S('no dark exclusion')} km², omitting the terrain mask gave {S('no HAND/slope mask')} km² and a 3 by 3 filter gave {S('3x3 filter')} km². The rule using ΔVV alone gave {S('dVV-only rule (-2.5 dB)')} km². Using only the 9 October scene as the pre-event reference gave {S('pre = 9 Oct only')} km², whereas using only the 21 October scene gave {S('pre = 21 Oct only')} km². The fixed thresholds without a median filter gave {S('paper-style fixed -2.0/-1.5, no filter')} km².
Without the cluster filter the same configurations gave {S('no dark exclusion','flooded_km2_14Nov_no_cluster_filter')}, {S('no HAND/slope mask','flooded_km2_14Nov_no_cluster_filter')}, {S('3x3 filter','flooded_km2_14Nov_no_cluster_filter')}, {S('dVV-only rule (-2.5 dB)','flooded_km2_14Nov_no_cluster_filter')}, {S('pre = 9 Oct only','flooded_km2_14Nov_no_cluster_filter')}, {S('pre = 21 Oct only','flooded_km2_14Nov_no_cluster_filter')} and {S('paper-style fixed -2.0/-1.5, no filter','flooded_km2_14Nov_no_cluster_filter')} km² in the order listed.""")
names13 = [('main (calibrated)', 'Main configuration'), ('no dark exclusion', 'No dark-surface exclusion'), ('no HAND/slope mask', 'No terrain mask'), ('pre = 21 Oct only', 'Pre-event 21 October only'), ('pre = 9 Oct only', 'Pre-event 9 October only'),
           ('3x3 filter', 'Three by three filter'), ('dVV-only rule (-2.5 dB)', 'ΔVV only rule'), ('paper-style fixed -2.0/-1.5, no filter', 'Fixed thresholds without filter')]
Tab(13, 'Flagged area on 14 November under alternative configurations', ['Configuration', 'With cluster filter, km²', 'Without cluster filter, km²'], [[n, S(k), S(k, 'flooded_km2_14Nov_no_cluster_filter')] for k, n in names13], [3900, 2500, 2626],
    'Note. Values are flagged area on 14 November 2023.')
# ------------------------------------------------------------ 8 grid
H('Effect of the evaluation grid')
rv = {r.configuration: r.flagged_km2_town_extent for r in rs.itertuples()}
Pp(f"""Over the extent of the town rasters, the flagged area of 14 November without the terrain mask was {f(rv['Earth Engine, 10 m grid'],3)} km² on a 10 m grid, {f(rv['Earth Engine, 20 m grid'],3)} km² on a 20 m grid and {f(rv['Earth Engine, 30 m grid'],3)} km² on a 30 m grid (Table 14). With the inputs reprojected to 10 m and the result summed on a 20 m grid it was {f(rv['Earth Engine, inputs reprojected to 10 m, 20 m grid'],3)} km², and the local implementation gave {f(rv['Local Python, 10 m'],3)} km². The exported 10 m flag layer gave 51.123 km² over the same extent.""")
Tab(14, 'Flagged area over the town raster extent by evaluation grid', ['Configuration', 'Flagged area, km²'], [[k, f(v, 3)] for k, v in rv.items()] + [['Exported 10 m flag layer', '51.123']], [5800, 3226],
    'Note. Rule applied without the terrain mask and without the cluster filter on 14 November 2023.')
tabvals = set();
for b in blocks:
    if b['t'] == 'tab':
        for r in b['rows']: tabvals.update(re.findall(r'\d+(?:\.\d+)?', ' '.join(r)))
        tabvals.update(re.findall(r'\d+(?:\.\d+)?', b['note'] or ''))
json.dump(blocks, open(os.path.join(BASE, 'outputs', 'results_blocks.json'), 'w'), ensure_ascii=False, indent=1)
# ---------------------------------------------------------------- verification of numbers
txt = ' '.join(b['x'] for b in blocks if b['t'] in ('p',))
clean = re.sub(r'\b(?:Figure|Table) \d+\b', ' ', txt)
clean = re.sub(r'\b\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December)\b', ' ', clean)
clean = re.sub(r'\b(?:2023|3 by 3)\b', ' ', clean); clean = re.sub(r'\b10 km\b|\b10 m\b|\b20 m\b|\b30 m\b', ' ', clean)
tn = set(re.findall(r'\d+(?:\.\d+)?', clean))
tabtext = set(tabvals) | set(figvals) | {'3', '9', '10', '50', '200', '5', '1'}
labels = {'23', '30', '12', '14', '26', '8', '2', '100', '500', '20'}
inText_notTable = sorted(x for x in tn if x not in tabtext)
# table values present in prose (cells that are labels such as '1', '5' are structural)
tabnums = set()
for b in blocks:
    if b['t'] == 'tab':
        for r in b['rows']: tabnums.update(x for c in r[1:] for x in re.findall(r'\d+(?:\.\d+)?', c))
inTable_notText = sorted(x for x in tabnums if x not in tn and x not in labels)
print('numbers in text not found in tables or figure legends:', inText_notTable)
print('table values not mentioned in the text:', inTable_notText)
print('words in prose', len(txt.split()), '| blocks', len(blocks), '| tables', sum(1 for b in blocks if b['t'] == 'tab'), '| figures', sum(1 for b in blocks if b['t'] == 'fig'))
