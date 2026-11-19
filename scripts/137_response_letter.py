import docx, os, re
from docx.shared import Pt, Cm
from docx.oxml.ns import qn
B = r'.'; REV = os.path.join(B, 'Revision')
c = docx.Document(os.path.join(REV, 'comments.docx')); ps = [p.text for p in c.paragraphs]
R1 = [x.strip() for x in ps[1].split('\n') if x.strip()]; L = [x.strip() for x in ps[3].split('\n') if x.strip()]
assert len(R1) == 2 and len(L) == 15, (len(R1), len(L))
big = L[0]; k = big.index(' Sequential parameter tuning')
R2 = [big[:k], big[k + 1:] + '\n' + L[1], L[2] + '\n' + L[3], L[4] + '\n' + L[5], '\n'.join(L[6:9]), L[9], L[11], L[12], L[13], L[14]]
assert L[10] == 'Comments' and L[11].startswith('Line 184') and L[14].startswith('Figure 5')
r1_resp = ['Thank you for the positive assessment and for the clear summary of the concerns. No change was needed for this comment, and each concern is addressed under comment 2.',
 ['Thank you for these helpful points. They were addressed as follows.',
  'Independence of calibration and validation. The terrain limits were also derived from the calibration reference alone and the totals were recomputed, and the Abstract, Discussion and Conclusion now state which steps were fixed before independent scoring and which were refined afterwards. See Methods under Terrain and permanent-water masks, Results under Study area, exclusions and analysed area, the thirteenth paragraph of the Discussion and Table S17. This was addressed together with Reviewer 2, comment 2.',
  'Limited coverage of the optical reference. The Discussion now states that the new intervals do not extend to the areas outside the reference extents. See the eleventh paragraph of the Discussion.',
  'Sensitivity to processing parameters. A sensitivity analysis of the detection thresholds was added. See Methods under Sensitivity analyses, Results under Sensitivity of the flagged area and Table S21.',
  'Land-cover uncertainty. Confidence intervals for the land-cover agreement and a test of the effect of the number of points per class were added. See Methods under Land-cover mapping, Results under Reliability of the land-cover map, the eleventh paragraph of the Discussion and Tables S15 and S16.',
  'Confidence intervals and spatially informed uncertainty. Block bootstrap intervals were added. See Methods under Reference data and accuracy assessment, Results under Agreement with UNOSAT optical flood mapping, the Abstract, the Conclusion and Table S18.',
  'Reliability of built-up exposure. A statement bounding the reliability of the built-up estimates was added to the third paragraph of the Discussion.',
  'Depth, severity and duration. The wording was revised so that backscatter intensity and persistence are not read as depth, severity or duration. See Methods under Intensity and persistence classes and the tenth paragraph of the Discussion.',
  'Sentinel-1 frequency and the flood peak. This limitation is now stated more explicitly in the Abstract, in the thirteenth paragraph of the Discussion and in the Conclusion.',
  'Transparency, script accessibility and simplicity. An outline of the workflow in 4 steps and the archive of the scripts and outputs were added. See Methods under Software and reproducibility and the Availability of data and materials statement. This was addressed together with Reviewer 2, comment 6.',
  'Sample size. The Sample size section now justifies the number of points by the precision it gives and by the sensitivity test, and the formal calculation is stated as not performed. See Methods under Sample size and Results under Reliability of the land-cover map.']]
r2_resp = ['Thank you for the positive assessment and the constructive summary. No change was needed for this comment, and the specific points are addressed below.',
 'Thank you for this important point. The terrain limits were derived from the calibration reference alone and the totals were recomputed, and the distinction between a priori settings and later refinements is now stated in the Abstract, the Discussion and the Conclusion. See Results under Study area, exclusions and analysed area, the thirteenth paragraph of the Discussion and Table S17. This was addressed together with Reviewer 1, comment 2.',
 'Thank you for this comment. The concentration of built-up pixels in a few cells and the value of a block-stratified design are now explained in Results under Reliability of the land-cover map, in the eleventh paragraph of the Discussion and in Table S14. The map was not retrained, because the classifier already used almost all built-up points and the cross-validation gives the more stable estimate, as now noted in the Discussion.',
 'Thank you for this suggestion. The rainfall timeline, a comparison over the area shared by the 3 optical mappings and a discussion of expansion against sensor limits were added. See Methods under Sensitivity analyses, Results under Agreement with UNOSAT optical flood mapping, the twelfth paragraph of the Discussion, Table 1, Table S20 and Figure S3. The data cannot fully separate the 2 causes, and the Discussion says so.',
 'Thank you for these points. The rationale for retaining the mean of the 2 October scenes was added to the seventh paragraph of the Discussion, and the check on positive backscatter change in flooded built-up and cropland pixels was added. See Methods under Sensitivity analyses, Results under Agreement with UNOSAT optical flood mapping, the fifth paragraph of the Discussion and Table S19.',
 'Thank you for this recommendation. The manuscript now states that the scripts, derived outputs and tables are archived in a public repository on Zenodo, with an outline of the workflow. See Methods under Software and reproducibility and the Availability of data and materials statement. This was addressed together with Reviewer 1, comment 2.',
 'Thank you for noting this error. It was corrected in the fourth paragraph of Methods under Land-cover mapping.',
 'Thank you for this comment. Table 2 was reformatted with fixed column widths, a repeated header row, rows kept whole, and the intensity classes set on separate lines.',
 'Thank you for this comment. The layout of Tables 4 and 7 was corrected with fixed column widths, repeated header rows and no breaks inside numbers, and the date columns of Table 4 now show the area above the percentage.',
 'Thank you for noting this. The legend of Figure 5 was redrawn in a single column so that the last entry is shown in full.']
doc = docx.Document(); st = doc.styles['Normal']; st.font.name = 'Cambria'; st.font.size = Pt(12); st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Cambria')
for s in doc.sections: s.left_margin = s.right_margin = Cm(2.5)
def para(t, indent=0, after=6):
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(after); p.paragraph_format.left_indent = Cm(indent)
    lines = t.split('\n')
    for i, l in enumerate(lines):
        r = p.add_run(l)
        if i < len(lines) - 1: r.add_break()
    return p
def block(label, quote, resp, n):
    para(label, after=2); para('Comment: ' + '\u201c' + quote + '\u201d', indent=0.6); 
    if isinstance(resp, list):
        para('Response %d: %s' % (n, resp[0]), after=3)
        for x in resp[1:]: para(x, indent=0.6, after=3)
    else: para('Response %d: %s' % (n, resp), after=12)
para('Reviewer 1', after=8)
for i, (q_, r_) in enumerate(zip(R1, r1_resp), 1): block('Reviewer 1, comment %d' % i, q_, r_, i)
para('Reviewer 2', after=8)
for i, (q_, r_) in enumerate(zip(R2, r2_resp), 1): block('Reviewer 2, comment %d' % i, q_, r_, i)
out = os.path.join(REV, 'Response_to_reviewers.docx'); doc.save(out); print('saved', out, len(R2))


