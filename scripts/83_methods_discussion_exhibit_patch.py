"""Patches the Methods generator (14) and the Discussion source for the new exhibit numbering.
Table 2 gains a column that states how each choice relates to the independent dates, Table 3 is merged into Results Table 8, and the Discussion cites Table 7."""
import re
B = r'.'
P = B + r'\scripts\14_make_methods_docx.js'; s = open(P, encoding='utf-8').read()
def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:60], s.count(old)); s = s.replace(old, new)
rep("K.push(table([2200, 3900, 2926], ['Parameter', 'Value', 'Basis'], [", "K.push(table([1650, 2350, 2300, 2726], ['Parameter', 'Value', 'Basis', 'Relation to the independent dates'], [")
before = 'Fixed before the independent dates were scored'
rows = {
 "['Pre-event reference', 'Mean of the 9 October and 21 October 2023 dB values', 'Grid search on the calibration date']": before,
 "['Median filter window', '5 by 5 pixels', 'Grid search on the calibration date']": before,
 "['VV threshold', 'ΔVV at most -4.0 dB', 'Grid search on the calibration date']": before,
 "['VH threshold', 'ΔVH at most -2.5 dB', 'Grid search on the calibration date']": before,
 "['Dark-surface exclusion', 'Median-filtered pre-event VV below -16 dB excluded', 'Highest kappa on the calibration date']": 'Added after the independent dates had been scored once, chosen on the calibration date, and the independent dates were then scored again',
 "['Minimum cluster size', 'Eight-connected clusters of at least 100 flagged pixels', 'Smallest size within 0.005 kappa of the highest on the calibration date']": 'Added after the independent dates had been scored twice, chosen on the calibration date, and the independent dates were then scored a third time',
 "['Permanent water', 'Random Forest water class or surface water occurrence of at least 75%', 'Fixed choice, not varied in the sensitivity analysis']": 'Fixed choice, not tuned on any scored date',
 "['HAND limit', 'At most 10 m', 'Maximum HAND of pixels mapped as flooded by UNOSAT']": 'Derived from flooded pixels of the Pléiades and Gaofen-2 products, so it used reference pixels of an independent date',
 "['Slope limit', 'At most 8 degrees', 'Whole degree nearest the 99th percentile of slope of pixels mapped as flooded by UNOSAT']": 'Derived from flooded pixels of the Pléiades and Gaofen-2 products, so it used reference pixels of an independent date',
 "['Intensity classes', 'Weak, ΔVV above -5 dB. Moderate, ΔVV at most -5 dB and above -7 dB. Strong, ΔVV at most -7 dB', 'Proportion of UNOSAT flooded pixels within ΔVV bins']": 'Set after tabulating the Pléiades and the Gaofen-2 pairs, so it used reference pixels of an independent date',
}
for old, txt in rows.items(): rep(old, old[:-1] + ", '" + txt + "']")
rep("and each configuration is defined (Table 3).'));", "and each configuration is defined together with its result (Table 8).'));")
i0 = s.index("K.push(title('Table 3.'"); i1 = s.index("K.push(body('The effect of the evaluation grid was checked")
s = s[:i0] + s[i1:]
open(P, 'w', encoding='utf-8', newline='').write(s)
for p in (B + r'\discussion_source.txt', B + r'\scripts\74_discussion_revision.py'):
    t = open(p, encoding='utf-8').read(); n = t.count('Table 14')
    if p.endswith('.txt'): assert n == 1, n; t = t.replace('(Table 14)', '(Table 7)')
    else: assert 'rep(2, "(Table 9)", "(Table 14)")' in t; t = t.replace('rep(2, "(Table 9)", "(Table 14)")', 'rep(2, "(Table 9)", "(Table 7)")')
    open(p, 'w', encoding='utf-8', newline='').write(t)
print('patched')
