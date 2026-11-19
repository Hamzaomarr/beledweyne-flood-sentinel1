import sys, os, json, copy
sys.path.insert(0, os.path.dirname(__file__))
import pandas as pd, numpy as np, docx
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Inches
import docedit as E
from docedit import q
B = r'.'; REV = os.path.join(B, 'Revision'); T = os.path.join(B, 'outputs', 'tables')
d = docx.Document(os.path.join(REV, 'MANUSCRIPT_Supplementary_materials.docx')); body = d.element.body; ch = list(body.iterchildren())
assert E.ptext(ch[38]).startswith('Table S13') and E.ptext(ch[40]).startswith('Note.') and E.ptext(ch[41]).startswith('Supplementary figures')
title_t, tbl_t, note_t = ch[38], ch[39], ch[40]
f2 = lambda x: '%.2f' % x; f3 = lambda x: '%.3f' % x
def rpr_of(p):
    r = p.find(q('r')); return None if r is None else r.find(q('rPr'))
def title_par(label, text, src):
    p = copy.deepcopy(title_t)
    for k in list(p.attrib): del p.attrib[k]
    runs = p.findall(q('r')); assert len(runs) >= 2, len(runs)
    for r in runs[2:]: p.remove(r)
    for r, t in zip(runs[:2], (label, ' ' + text)):
        E.set_t(r, t); rp = r.find(q('rPr'))
        if rp is None: rp = OxmlElement('w:rPr'); r.insert(0, rp)
        for c in rp.findall(q('color')): rp.remove(c)
        c = OxmlElement('w:color'); c.set(qn('w:val'), E.COL[src]); rp.append(c)
    return p
def note_par(text, src):
    p = copy.deepcopy(note_t)
    for k in list(p.attrib): del p.attrib[k]
    runs = p.findall(q('r'))
    for r in runs[1:]: p.remove(r)
    r = runs[0]; E.set_t(r, text); rp = r.find(q('rPr'))
    if rp is None: rp = OxmlElement('w:rPr'); r.insert(0, rp)
    for c in rp.findall(q('color')): rp.remove(c)
    c = OxmlElement('w:color'); c.set(qn('w:val'), E.COL[src]); rp.append(c)
    return p
def make_table(widths, header, rows, src):
    hdr = header if isinstance(header[0], list) else [header]
    tbl = OxmlElement('w:tbl'); tbl.append(copy.deepcopy(tbl_t.tblPr))
    pr = tbl.tblPr; lay = OxmlElement('w:tblLayout'); lay.set(qn('w:type'), 'fixed'); pr.find(q('tblBorders')).addnext(lay)
    pr.find(q('tblW')).set(qn('w:w'), str(sum(widths)))
    grid = OxmlElement('w:tblGrid')
    for w in widths: g = OxmlElement('w:gridCol'); g.set(qn('w:w'), str(w)); grid.append(g)
    tbl.append(grid)
    allrows = hdr + rows; nh = len(hdr)
    for ri, row in enumerate(allrows):
        tr = OxmlElement('w:tr'); trpr = OxmlElement('w:trPr'); trpr.append(OxmlElement('w:cantSplit'))
        if ri < nh: trpr.append(OxmlElement('w:tblHeader'))
        tr.append(trpr); col = 0
        for val in row:
            span = 1
            if isinstance(val, tuple): val, span = val
            wsum = sum(widths[col:col + span]); col += span
            tc = OxmlElement('w:tc'); tcpr = OxmlElement('w:tcPr'); w = OxmlElement('w:tcW'); w.set(qn('w:type'), 'dxa'); w.set(qn('w:w'), str(wsum)); tcpr.append(w)
            if span > 1: gs = OxmlElement('w:gridSpan'); gs.set(qn('w:val'), str(span)); tcpr.append(gs)
            mar = OxmlElement('w:tcMar')
            for side, v in (('top', 50), ('left', 70), ('bottom', 50), ('right', 70)):
                m = OxmlElement('w:' + side); m.set(qn('w:type'), 'dxa'); m.set(qn('w:w'), str(v)); mar.append(m)
            tcpr.append(mar); bd = OxmlElement('w:tcBorders')
            if ri == 0:
                b = OxmlElement('w:top'); b.set(qn('w:val'), 'single'); b.set(qn('w:sz'), '8'); b.set(qn('w:space'), '0'); b.set(qn('w:color'), '000000'); bd.append(b)
            if ri == nh - 1:
                b = OxmlElement('w:bottom'); b.set(qn('w:val'), 'single'); b.set(qn('w:sz'), '4'); b.set(qn('w:space'), '0'); b.set(qn('w:color'), '000000'); bd.append(b)
            if ri == len(allrows) - 1:
                for old in bd.findall(q('bottom')): bd.remove(old)
                b = OxmlElement('w:bottom'); b.set(qn('w:val'), 'single'); b.set(qn('w:sz'), '8'); b.set(qn('w:space'), '0'); b.set(qn('w:color'), '000000'); bd.append(b)
            if len(bd): tcpr.append(bd)
            tc.append(tcpr)
            for line in (val if isinstance(val, list) else [val]):
                p = OxmlElement('w:p'); ppr = OxmlElement('w:pPr'); ps = OxmlElement('w:pStyle'); ps.set(qn('w:val'), 'TableText'); ppr.append(ps); p.append(ppr)
                if str(line) != '': p.append(E.mk_run(str(line), None, E.COL[src]))
                tc.append(p)
            tr.append(tc)
        tbl.append(tr)
    return tbl
anchor = ch[40]; added = []
def add(label, text, widths, header, rows, note, src, cid):
    global anchor
    tp = title_par(label, text, src); tb = make_table(widths, header, rows, src); npar = note_par(note, src)
    anchor.addnext(tp); tp.addnext(tb); tb.addnext(npar); anchor = npar
    E.LOG.append(dict(src=src, comment=cid, location=label, kind='new supplementary table', old='', new=text + ' ' + note))
# ---- S14 consensus pixels by block
cb = pd.read_csv(os.path.join(T, 'revision2_consensus_pixels_by_block.csv')); names = {0: 'Water', 1: 'Cropland', 2: 'Vegetation or rangeland', 3: 'Built-up', 4: 'Bare soil or sand'}
rows = [[names[int(r['cls'])]] + ['%d' % r[str(k)] for k in range(5)] + ['%d' % r['total']] for _, r in cb.iterrows()]
bu = cb[cb.cls == 3].iloc[0]; rows.append(['Built-up, share of class, %'] + [f2(100 * bu[str(k)] / bu['total']) for k in range(5)] + ['100.00'])
add('Table S14.', 'Land-cover consensus pixels by spatial block', [2400, 1100, 1100, 1100, 1100, 1100, 1126], ['Class', 'Block 0', 'Block 1', 'Block 2', 'Block 3', 'Block 4', 'All blocks'], rows,
    'Note. Counts are 10 m pixels where WorldCover and Dynamic World gave the same class, over the study rectangle. A block is the remainder after division by 5 of the sum of the integer parts of longitude and latitude, each divided by 0.05°. Block 0 was held out for testing.', 'R2', 'R2-3')
# ---- S15 land-cover accuracy intervals
lc = pd.read_csv(os.path.join(T, 'revision2_lulc_accuracy_ci.csv')); cls = ['Water', 'Cropland', 'Vegetation or rangeland', 'Built-up', 'Bare soil or sand']
def cell_(s, m, c):
    r = lc[(lc.set == s) & (lc.measure == m) & (lc.cls == c)].iloc[0]; return [f2(r.est), f2(r.lo) + ' to ' + f2(r.hi)]
H, C = 'hold-out (block 0)', '5-fold spatial block cross-validation'
rows = []
for c in cls: rows.append([c, cell_(H, 'Producer', c), cell_(H, 'User', c), cell_(C, 'Producer', c), cell_(C, 'User', c)])
rows.append(['All classes', cell_(H, 'Overall', 'All'), '', cell_(C, 'Overall', 'All'), ''])
add('Table S15.', 'Agreement of the land-cover map with consensus labels and 95% confidence intervals', [2500, 1630, 1630, 1633, 1633], ['Class', 'Hold-out producer’s agreement', 'Hold-out user’s agreement', 'Cross-validation producer’s agreement', 'Cross-validation user’s agreement'], rows,
    'Note. Each cell gives the estimate and, below it, the 95% confidence interval. Intervals are Wilson intervals, or exact binomial intervals where fewer than 30 points were available. In the All classes row the producer’s columns give overall agreement. The hold-out rests on 373 points and the cross-validation on 2500 points.', 'R1', 'R1-2d')
# ---- S16 cap sensitivity (runs in columns)
cs = json.load(open(os.path.join(T, 'revision2_lulc_cap_sensitivity.json'), encoding='utf-8-sig'))
hdr = ['Measure'] + ['%d points, seed %d' % (r['cap'], r['seed']) for r in cs]
meas = [('Points tested', lambda r: str(r['n'])), ('Overall agreement', lambda r: f2(r['OA'])), ('Kappa', lambda r: f2(r['kappa'])), ('Built-up producer’s agreement', lambda r: f2(r['built_prod'])), ('Built-up user’s agreement', lambda r: f2(r['built_user'])), ('Cropland producer’s agreement', lambda r: f2(r['crop_prod'])), ('Cropland user’s agreement', lambda r: f2(r['crop_user']))]
rows = [[n] + [fn(r) for r in cs] for n, fn in meas]
add('Table S16.', 'Cross-validated agreement by number of points per class and sampling seed', [2726, 1050, 1050, 1050, 1050, 1050, 1050], hdr, rows,
    'Note. Five-fold spatial block cross-validation of the same classifier design with the same settings. Points per class is the cap on points drawn for each class. The main analysis used 500 points per class and seed 42.', 'R1', 'R1-2j')
# ---- S17 terrain limits from calibration only (settings in columns)
tt = pd.read_csv(os.path.join(T, 'revision2_terrain_from_calibration_only.csv'))
hdr = ['Measure', 'HAND at most 10 m, main limit', 'HAND at most 5 m', 'HAND at most 4.7 m, Pléiades pixels only']
meas = [('Analysed area, km²', 'analysed_km2'), ('Flagged area on 14 November, km²', 'flag14_km2'), ('Flagged area on 26 November, km²', 'flag26_km2'), ('Flagged share on 14 November, cropland, %', 'share14_Cropland'), ('Flagged share on 14 November, built-up, %', 'share14_Built-up'), ('Flagged share on 14 November, vegetation or rangeland, %', 'share14_Vegetation or rangeland'), ('Flagged share on 14 November, bare soil or sand, %', 'share14_Bare soil or sand')]
rows = [[n] + [f2(tt.iloc[i][k]) for i in range(3)] for n, k in meas]
add('Table S17.', 'Analysed area and flagged area with terrain limits derived from the calibration reference only', [3626, 1800, 1800, 1800], hdr, rows,
    'Note. The main limit of 10 m came from the flooded pixels of the Pléiades and Gaofen-2 products. The slope limit was 8 degrees in every column, because the 99th percentile of slope among the Pléiades flooded pixels was 8.16 degrees. Shares are the flagged percentage of the analysed area of each class.', 'R1', 'R1-2a')
# ---- S18 block bootstrap intervals
bb = pd.read_csv(os.path.join(T, 'revision2_block_bootstrap_ci.csv')); rows = []
for _, r in bb.iterrows():
    rows.append([r.comparison, str(int(r.block_m)), str(int(r.n_blocks))] + [[f2(r[m]), f2(r[m + '_lo']) + ' to ' + f2(r[m + '_hi'])] for m in ('precision', 'recall', 'balanced_accuracy', 'kappa')])
fx = pd.read_csv(os.path.join(T, 'revision2_fixed_threshold_ci.csv'))
note = 'Note. Intervals are the 2.5th and 97.5th percentiles of 2000 bootstrap resamples of whole blocks, and block is the side of the square block in metres. Each cell gives the estimate and, below it, the interval. The kappa of the fixed thresholds was ' + ', '.join('%s (%s to %s) for %s' % (f2(r.kappa), f2(r.kappa_lo), f2(r.kappa_hi), ['the calibration date', 'Gaofen-2 outside the calibration extent', 'WorldView-2 outside the calibration extent'][i]) for i, r in fx.iterrows()) + '.'
add('Table S18.', 'Block bootstrap confidence intervals of agreement with UNOSAT flood mapping for the final rule', [2300, 1000, 1000, 1181, 1181, 1182, 1182], ['Comparison', 'Block, m', 'Blocks', 'Precision', 'Recall', 'Balanced accuracy', 'Kappa'], rows, note, 'R1', 'R1-2e')
# ---- S19 positive backscatter anomalies
pa = pd.read_csv(os.path.join(T, 'revision2_urban_positive_anomalies.csv')); rows = []
for _, r in pa.iterrows():
    rows.append(['Pléiades and 14 November' if r.pair.startswith('Pl') else 'Gaofen-2 and 26 November, outside calibration extent', r.wc_class + (', flooded' if r.reference == 'UNOSAT flooded' else ', not flooded'), '%d' % r.pixels, f2(r.mean_dVV), f2(100 * r.share_dVV_gt_plus3), f2(100 * r.share_dVV_le_minus4), f2(100 * r.share_flagged_final)])
add('Table S19.', 'Backscatter change in WorldCover built-up and cropland pixels by UNOSAT flood status', [1900, 1800, 1000, 1000, 1100, 1100, 1126], ['Pair', 'Class and status', 'Pixels', 'Mean ΔVV, dB', 'ΔVV above +3 dB, %', 'ΔVV at most ' + chr(0x2011) + '4 dB, %', 'Flagged, %'], rows,
    'Note. ΔVV is the median-filtered change in VV against the pre-event mean. Status refers to the UNOSAT flood extent. Pixels are 10 m. Flagged is the share flagged by the final rule. The group of built-up pixels outside the flood extent on the Gaofen-2 pair held 64 pixels and was not interpreted.', 'R2', 'R2-5b')
# ---- S20 same footprint
sf = pd.read_csv(os.path.join(T, 'revision2_same_footprint_dates.csv')); rows = []
for _, r in sf.iterrows(): rows.append([r.pair, f2(r.mask_km2), f2(r.reference_flooded_km2), f2(r.flagged_km2), f2(r.precision), f2(r.recall), f2(r.kappa)])
add('Table S20.', 'Agreement over the area shared by the 3 UNOSAT analysis extents', [2200, 1100, 1300, 1100, 1200, 1050, 1076], ['Pair', 'Scored area, km²', 'Flooded in reference, km²', 'Flagged, km²', 'Precision', 'Recall', 'Kappa'], rows,
    'Note. The same ground was scored on each date with the final rule. Flooded in reference is the area mapped as flooded by UNOSAT. Of the 13.91 km² flooded on 12 November, 13.81 km² was also flooded on 23 November, and of the 29.27 km² flooded on 23 November, 29.10 km² was also flooded on 30 November.', 'R2', 'R2-4')
# ---- S21 thresholds
ts = pd.read_csv(os.path.join(T, 'revision2_threshold_sensitivity.csv')); rows = []
for _, r in ts.iterrows(): rows.append([r.setting, f2(r.flagged_km2_town_14Nov), f2(r.recall_calibration), f2(r.kappa_calibration), f2(r.recall_gf2_outside), f2(r.kappa_gf2_outside)])
add('Table S21.', 'Sensitivity of flagged area and agreement to the detection thresholds', [2326, 1300, 1350, 1350, 1350, 1350], [['Setting', 'Flagged area on 14 November, km²', ('Calibration date', 2), ('Gaofen-2, outside calibration extent', 2)], ['', '', 'Recall', 'Kappa', 'Recall', 'Kappa']], rows,
    'Note. One threshold was varied at a time and the other was kept at its calibrated value, with the dark-surface exclusion and the minimum cluster size retained. Flagged area is over the extent of the town rasters. The calibrated settings are 4.0 dB for VV and 2.5 dB for VH.', 'R1', 'R1-2c')# ---- Figure S3
chk = list(body.iterchildren()); figtitle = [e for e in chk if e.tag == q('p') and E.ptext(e).startswith('Figure S2.')][0]
figpar = figtitle.getprevious(); assert figpar.find('.//' + q('drawing')) is not None
newfig = copy.deepcopy(figpar)
for c_ in list(newfig):
    if c_.tag != q('pPr'): newfig.remove(c_)
for k in list(newfig.attrib): del newfig.attrib[k]
figtitle.addnext(newfig)
para = docx.text.paragraph.Paragraph(newfig, d._body); para.add_run().add_picture(os.path.join(B, 'outputs', 'figures', 'png', 'figS3_rainfall_timeline.png'), width=Inches(6.2))
tp = title_par('Figure S3.', 'Daily rainfall averaged over the study rectangle and the dates of the Sentinel-1 and UNOSAT optical acquisitions', 'R2')
newfig.addnext(tp)
E.LOG.append(dict(src='R2', comment='R2-4', location='Figure S3', kind='new supplementary figure', old='', new='Daily rainfall averaged over the study rectangle and the dates of the Sentinel-1 and UNOSAT optical acquisitions'))
out = os.path.join(REV, 'Supplementary_revised_colored.docx'); d.save(out)
json.dump(E.LOG, open(os.path.join(B, 'outputs', 'change_log_supp.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False); print('saved', out)


