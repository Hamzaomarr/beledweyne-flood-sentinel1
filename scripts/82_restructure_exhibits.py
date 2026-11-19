"""Restructures the exhibits: 26 tables become 9 main tables (Methods 1 and 2, Results 3 to 9) and 13 supplementary tables, and Figures 4 and 5 are combined.
Reads outputs/results_blocks.json (written by 73) and writes outputs/results_blocks_main.json and outputs/supplement_blocks.json.
Rendering is done by 35_render_results_docx.js. Old numbers refer to the 26 table numbering of the earlier draft."""
import json, os, re, copy
from PIL import Image, ImageDraw, ImageFont
B = r'.'; O = os.path.join(B, 'outputs'); T = os.path.join(O, 'tables')
src = os.path.join(O, 'results_blocks_before_restructure.json')
if not os.path.exists(src): json.dump(json.load(open(os.path.join(O, 'results_blocks.json'), encoding='utf-8')), open(src, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
blocks = json.load(open(src, encoding='utf-8'))
tabs = {x['label']: x for x in blocks if x['t'] == 'tab'}; tb = lambda n: tabs['Table %d.' % n]
cv = json.load(open(os.path.join(T, 'revision_lulc_blockcv.json'), encoding='utf-8')); acc = json.load(open(os.path.join(T, 'lulc_accuracy_vs_consensus.json'), encoding='utf-8'))
f2 = lambda x: '%.2f' % x
# ---------- number mapping, old table number -> new label; old figure number -> new label
TMAP = {4: '3', 5: '3', 6: 'S1', 7: 'S2', 8: '4', 9: '4', 10: 'S3', 11: '5', 12: 'S4', 13: 'S5', 14: '6', 15: 'S6', 16: 'XFIGS1', 17: 'S7', 18: 'S8', 19: 'S9', 20: 'S9', 21: 'S10', 22: '7', 23: 'S11', 24: 'S12', 25: '8', 26: 'S13'}
FMAP = {'2': '2', '3': '3', '4': '4A', '5': '4B', '6': '5', '7': '7'}
def renum(s):
    s = re.sub(r'Table (\d+)', lambda m: 'Table ' + TMAP[int(m.group(1))] if int(m.group(1)) in TMAP else m.group(0), s)
    return re.sub(r'Figure (\d)', lambda m: 'Figure ' + FMAP[m.group(1)] if m.group(1) in FMAP else m.group(0), s)
# ---------- merged main tables
t4, t5 = tb(4), tb(5); area = {r[0]: r[1] for r in t4['rows']}
lc_rows = [[r[0], area[r[0]], r[2], r[3], r[4], r[5], r[6]] for r in t5['rows']]
lc = dict(t='tab', label='Table 3.', title='Land-cover map area and agreement with reference labels',
  header=['Class', 'Mapped area, km²', 'Hold-out points', "Hold-out producer's agreement", "Hold-out user's agreement", "Cross-validation producer's agreement", "Cross-validation user's agreement"],
  rows=lc_rows, widths=[2100, 1100, 950, 1150, 1150, 1300, 1276],
  note='Note. Overall agreement was %s with kappa %s for the hold-out and %s with kappa %s for the cross-validation. Hold-out refers to spatial block 0 and cross-validation to the 5 spatial blocks held out in turn, with 500 points per class, so training points were 500 minus the hold-out points. Agreement is with labels where two existing land-cover products gave the same class. Only 4 hold-out points were built-up, so the cross-validation values are the better guide for that class.' % (f2(acc['overall_accuracy']), f2(acc['kappa']), f2(cv['OA']), f2(cv['kappa'])))
t8, t9 = tb(8), tb(9); assert [r[0] for r in t8['rows']] == [r[0] for r in t9['rows']]
fl = dict(t='tab', label='Table 4.', title='Flagged area and share of the analysed area by land-cover class and date',
  header=['Class', 'Analysed area, km²', '2 November', '14 November', '26 November', '8 December'],
  rows=[[a[0], a[1]] + ['%s / %s%%' % (a[j + 2], b[j + 1]) for j in range(4)] for a, b in zip(t8['rows'], t9['rows'])], widths=[2300, 1400, 1331, 1331, 1331, 1333],
  note='Note. Each cell gives the flagged area in km² and the percentage of the analysed area of the class, separated by a slash.')
t22 = tb(22)
CH = {'Main configuration': 'Mean of 9 and 21 October as pre-event reference, 5 by 5 filter and the rule and masks of Table 2',
      'No dark-surface exclusion': 'The dark-surface cut-off was not applied', 'No terrain mask': 'The HAND and slope limits were not applied and only permanent water was excluded',
      'Pre-event 21 October only': 'The scene of 21 October was the pre-event reference', 'Pre-event 9 October only': 'The scene of 9 October was the pre-event reference',
      'Three by three filter': 'The median filter window was 3 by 3 pixels', 'ΔVV only rule': 'ΔVV alone with a threshold of -2.5 dB was used',
      'Fixed thresholds without filter': 'The rule was -2.0 dB for VV or -1.5 dB for VH against the 21 October scene, without median filtering and without dark-surface exclusion, with the minimum cluster size retained'}
assert set(CH) == {r[0] for r in t22['rows']}
cfg = dict(t='tab', label='Table 7.', title='Flagged area on 14 November under alternative configurations',
  header=['Configuration', 'Change from the main configuration', 'With cluster filter, km²', 'Without cluster filter, km²'],
  rows=[[r[0], CH[r[0]], r[1], r[2]] for r in t22['rows']], widths=[2100, 3626, 1650, 1650],
  note='Note. Values are flagged area on 14 November 2023. HAND, height above nearest drainage. VV, vertical transmit and vertical receive polarisation. VH, vertical transmit and horizontal receive polarisation. ΔVV, post-event minus pre-event VV backscatter in dB.')
# ---------- merged supplementary table S9
a, b = tb(19), tb(20)
s9 = dict(t='tab', label='Table S9.', title='Flagged pixels removed by the minimum cluster size within the scoring masks, in total and by cluster size', header=a['header'],
  rows=a['rows'] + [['§' + h for h in b['header']]] + b['rows'], widths=a['widths'],
  note='Note. The upper rows give the total removed and the lower rows, under their own headings, split by cluster size. Flooded means inside the UNOSAT flood extent. Flooded share is the proportion of the flagged pixels in the size class that lay inside the UNOSAT flood extent. The independent dates are scored outside the calibration extent.')
# ---------- grid table S13 corrected
t26 = copy.deepcopy(tb(26)); rows = t26['rows']
i = [k for k, r in enumerate(rows) if r[0].startswith('Earth Engine, inputs reprojected')][0]
rows[i][0] = 'Earth Engine, inputs reprojected to 10 m, filter run at the 20 m scale, 20 m grid'
j = [k for k, r in enumerate(rows) if r[0] == 'Local Python, 10 m'][0]
rows.insert(j + 1, ['Local Python, 10 m flag layer averaged to 20 m', '51.160'])
rows.insert(j + 2, ['Local Python, inputs sampled at 20 m, 5 by 5 filter spanning 100 m, four sampling offsets', '45.672 to 45.789'])
rows.insert(j + 3, ['Local Python, 10 m inputs, 9 by 9 filter spanning 90 m', '45.579'])
rows.insert(j + 4, ['Local Python, 10 m inputs, 11 by 11 filter spanning 110 m', '44.839'])
t26['note'] = t26['note'] + ' The 5 by 5 pixel median filter spans 50 m on a 10 m grid, 100 m on a 20 m grid and 150 m on a 30 m grid. The 2 added Local Python rows were computed over the same extent without the terrain mask and without the cluster filter.'
# ---------- figures are drawn by script 110 at the printed width and stored in outputs/figures/png
fd = os.path.join(O, 'figures', 'png'); fig45 = os.path.join(fd, 'fig_intensity_persistence_combined.png')
fw = lambda f: round(Image.open(f).width / 300 * 96)
fh = lambda f: round(Image.open(f).height / 300 * 96)
NEWCAP = {'Figure 2.': 'Land-cover map of the study area and UNOSAT analysis extents. Coordinates are in kilometres in the Universal Transverse Mercator zone 38N projection. The solid outline is the Pléiades extent and the dashed outline is the extent shared by the Gaofen-2 and WorldView-2 mapping', 'Figure 3.': 'Flagged flood extent on 14 November and 26 November 2023. A. Flagged area on 14 November. B. Flagged area on 26 November', 'Figure 7.': 'Backscatter difference between the 2 October scenes and area flagged only with the 21 October reference. A. Mean change in VV backscatter from 9 October to 21 October on a 100 m grid. B. Share of each 100 m cell flagged on 14 November only with the 21 October reference, with the outline of the main footprint'}
# ---------- assemble
MAIN = {4: lc, 5: None, 8: fl, 9: None, 22: cfg, 19: None, 20: None}
SUPP_ORDER = []; main_out = []; supp = []
for x in blocks:
    if x['t'] == 'tab':
        n = int(re.match(r'Table (\d+)', x['label']).group(1))
        if n in (4,): main_out.append(lc)
        elif n in (8,): main_out.append(fl)
        elif n == 22: main_out.append(cfg)
        elif n in (5, 9, 20, 3, 16): pass                       # absorbed into 3, 4 and S9
        elif n == 13:
            main_out.append(dict(t='fig', key='fig6', file=os.path.join(fd, 'fig4_validation_vs_unosat.png'), w=fw(os.path.join(fd, 'fig4_validation_vs_unosat.png')), h=fh(os.path.join(fd, 'fig4_validation_vs_unosat.png')), label='Figure 6.', title='Agreement of the radar flag with UNOSAT flood extents on the calibration date and on the 2 independent dates outside the calibration extent, for the final rule, the calibrated rule without the cluster filter and the fixed thresholds. A. Precision. B. Recall. C. Balanced accuracy. D. Cohen\'s kappa. The radar dates differ from the optical mapping dates by 2 to 4 days'))
            y = copy.deepcopy(x); y['label'] = 'Table S5.'; supp.append(y)
        elif n in (11, 14, 25): y = copy.deepcopy(x); y['label'] = 'Table %s.' % TMAP[n]; main_out.append(y)
        elif n == 19: supp.append(s9)
        else:
            y = copy.deepcopy(t26 if n == 26 else x); y['label'] = 'Table S%s.' % TMAP[n][1:]; supp.append(y)
    elif x['t'] == 'fig':
        k = re.match(r'Figure (\d)', x['label']).group(1)
        if k == '4': main_out.append(dict(t='fig', key='fig4', file=fig45, w=fw(fig45), h=fh(fig45), label='Figure 4.', title='Intensity of backscatter change and persistence of the flag. A. Intensity of backscatter change on 14 November 2023. B. Persistence of the flag from 14 November to 8 December 2023'))
        elif k == '5': pass
        else:
            y = copy.deepcopy(x); y['label'] = 'Figure %s.' % FMAP[k]; y['file'] = os.path.join(fd, os.path.basename(x['file'])); y['w'] = fw(y['file']); y['h'] = fh(y['file']); y['title'] = NEWCAP.get(y['label'], y['title']); main_out.append(y)
    else: main_out.append(copy.deepcopy(x))
# brackets in row labels are not used in the manuscript style
for x in main_out + supp:
    if x['t'] == 'tab': x['rows'] = [[c.replace(' (calibration)', ', calibration').replace(' (main)', ', main') for c in r] for r in x['rows']]
# renumber references in text, notes and captions of the main blocks
for x in main_out:
    if x['t'] == 'p': x['x'] = renum(x['x'])
    elif x['t'] == 'tab' and x.get('note') and x['label'] not in ('Table 3.', 'Table 4.', 'Table 7.'): x['note'] = renum(x['note'])
for x in main_out:
    if x['t'] != 'p': continue
    x['x'] = x['x'].replace('Table XFIGS1', 'Figure S1')
    if x['x'].startswith('Against the Pléiades mapping of 12 November'): x['x'] = x['x'].replace('(Table S5)', '(Figure 6 and Table S5)', 1)
    if x['x'].startswith('In the town, the radar and UNOSAT flood extents agreed'): x['x'] += ' The radar images behind this comparison are shown in Figure S2.'
# grid paragraph, explanation of the cause
for x in main_out:
    if x['t'] == 'p' and x['x'].startswith('Over the extent of the town rasters'):
        x['x'] += ' Averaging the 10 m flag layer to 20 m gave 51.160 km², and sampling the inputs at 20 m before the 5 by 5 pixel filter gave 45.672 to 45.789 km² across the four sampling offsets, and the 10 m rule gave 45.579 km² with a 9 by 9 pixel window and 44.839 km² with an 11 by 11 pixel window (Table S13).'
for x in main_out:
    if x['t'] == 'p': x['x'] = x['x'].replace('(Table S13).', '(Table S13).') if x['x'].startswith('Over the extent') else x['x']
json.dump(main_out, open(os.path.join(O, 'results_blocks_main.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for y in supp:
    if y.get('note'): y['note'] = renum(y['note']) if y['label'] != 'Table S9.' else y['note']
supfigs = [dict(t='h', x='Supplementary figures'),
 dict(t='fig', key='figS1', file=os.path.join(fd, 'fig5_severity_justification.png'), w=fw(os.path.join(fd, 'fig5_severity_justification.png')), h=fh(os.path.join(fd, 'fig5_severity_justification.png')), label='Figure S1.', title='Share of reference pixels mapped as flooded by UNOSAT by backscatter change and persistence. A. Flooded share by size of the backscatter change in VV. B. Flooded share by number of dates on which the pixel was flagged. The shares support ordinal classes only, and no water depth was measured or inferred'),
 dict(t='fig', key='figS2', file=os.path.join(fd, 'fig11_sentinel1_before_after_town.png'), w=fw(os.path.join(fd, 'fig11_sentinel1_before_after_town.png')), h=fh(os.path.join(fd, 'fig11_sentinel1_before_after_town.png')), label='Figure S2.', title='Sentinel-1 VV backscatter before and after the flood and its change over Beledweyne. A. VV before the flood, as the mean of 9 and 21 October. B. VV on 14 November. C. Change in VV between the 2 periods. The outline shows the UNOSAT Pléiades flood extent of 12 November')]
sup_blocks = [dict(t='p', x='This file contains the supplementary tables and figures referred to in the Results of the manuscript on the 2023 Deyr flood around Beledweyne, Somalia. Tables are numbered in the order in which they are cited, and the supplementary figures follow the tables.')] + supp + supfigs
json.dump(sup_blocks, open(os.path.join(O, 'supplement_blocks.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('main tables:', [x['label'] for x in main_out if x['t'] == 'tab']); print('main figures:', [x['label'] for x in main_out if x['t'] == 'fig']); print('supp tables:', [x['label'] for x in supp])
