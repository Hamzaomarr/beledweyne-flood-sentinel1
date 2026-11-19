"""Patches 82 so that fig4 (accuracy chart) becomes main Figure 6, Table 13 moves to the supplement (S5), Table 16 is replaced by Figure S1,
and fig11 becomes Figure S2. Also moves the Methods and Discussion references to the new table numbers."""
import os
os.chdir(r'.\scripts')
p = '82_restructure_exhibits.py'; s = open(p, encoding='utf-8').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:50], s.count(a)); s = s.replace(a, b)
rep("TMAP = {4: '3', 5: '3', 6: 'S1', 7: 'S2', 8: '4', 9: '4', 10: 'S3', 11: '5', 12: 'S4', 13: '6', 14: '7', 15: 'S5', 16: 'S6', 17: 'S7', 18: 'S8', 19: 'S9', 20: 'S9', 21: 'S10', 22: '8', 23: 'S11', 24: 'S12', 25: '9', 26: 'S13'}",
    "TMAP = {4: '3', 5: '3', 6: 'S1', 7: 'S2', 8: '4', 9: '4', 10: 'S3', 11: '5', 12: 'S4', 13: 'S5', 14: '6', 15: 'S6', 16: 'XFIGS1', 17: 'S7', 18: 'S8', 19: 'S9', 20: 'S9', 21: 'S10', 22: '7', 23: 'S11', 24: 'S12', 25: '8', 26: 'S13'}")
rep("FMAP = {'2': '2', '3': '3', '4': '4a', '5': '4b', '6': '5', '7': '6'}", "FMAP = {'2': '2', '3': '3', '4': '4a', '5': '4b', '6': '5', '7': '7'}")
rep("label='Table 8.', title='Flagged area on 14 November under alternative", "label='Table 7.', title='Flagged area on 14 November under alternative")
rep("x['label'] not in ('Table 3.', 'Table 4.', 'Table 8.')", "x['label'] not in ('Table 3.', 'Table 4.', 'Table 7.')")
rep("        elif n in (11, 13, 14, 25): y = copy.deepcopy(x)",
    "        elif n == 13:\n            main_out.append(dict(t='fig', key='fig6', file=os.path.join(fd, 'fig4_validation_vs_unosat.png'), w=600, h=268, label='Figure 6.', title='Agreement of the radar flag with UNOSAT flood extents on the calibration date and the two independent dates, for the final rule, the calibrated rule without the cluster filter and the fixed thresholds'))\n            y = copy.deepcopy(x); y['label'] = 'Table S5.'; supp.append(y)\n        elif n in (11, 14, 25): y = copy.deepcopy(x)")
rep("        elif n in (5, 9, 20, 3): pass", "        elif n in (5, 9, 20, 3, 16): pass")
rep("# grid paragraph, explanation of the cause", """for x in main_out:
    if x['t'] != 'p': continue
    x['x'] = x['x'].replace('Table XFIGS1', 'Figure S1')
    if x['x'].startswith('Against the Pléiades mapping of 12 November'): x['x'] = x['x'].replace('(Table S5)', '(Figure 6 and Table S5)', 1)
    if x['x'].startswith('In the town, the radar and UNOSAT flood extents agreed'): x['x'] += ' The radar images behind this comparison are shown in Figure S2.'
# grid paragraph, explanation of the cause""")
rep("sup_blocks = [dict(t='p', x='This file contains the supplementary tables referred to in the Results of the manuscript on the 2023 Deyr flood around Beledweyne, Somalia. Tables are numbered in the order in which they are cited.')] + supp",
"""supfigs = [dict(t='h', x='Supplementary figures'),
 dict(t='fig', key='figS1', file=os.path.join(fd, 'fig5_severity_justification.png'), w=600, h=265, label='Figure S1.', title='Share of reference pixels mapped as flooded by UNOSAT by size of the backscatter drop, panel a, and by number of dates on which the pixel was flagged, panel b'),
 dict(t='fig', key='figS2', file=os.path.join(fd, 'fig11_sentinel1_before_after_town.png'), w=600, h=233, label='Figure S2.', title='Sentinel-1 VV backscatter before and after the flood and its change over Beledweyne, with the UNOSAT Pléiades flood extent of 12 November in orange')]
sup_blocks = [dict(t='p', x='This file contains the supplementary tables and figures referred to in the Results of the manuscript on the 2023 Deyr flood around Beledweyne, Somalia. Tables are numbered in the order in which they are cited, and the supplementary figures follow the tables.')] + supp + supfigs""")
open(p, 'w', encoding='utf-8', newline='').write(s)
t = open('14_make_methods_docx.js', encoding='utf-8').read(); a = '(Table 8).'; assert t.count(a) == 1
open('14_make_methods_docx.js', 'w', encoding='utf-8', newline='').write(t.replace(a, '(Table 7).'))
for f in ('..\\discussion_source.txt', '74_discussion_revision.py'):
    t = open(f, encoding='utf-8').read(); a = '(Table 7)'; assert t.count(a) == 1, (f, t.count(a))
    open(f, 'w', encoding='utf-8', newline='').write(t.replace(a, '(Table 6)'))
print('patched')
