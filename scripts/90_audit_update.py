"""Updates the fact-check audit with the rows checked after the exhibit restructure, recomputes the totals and writes MANUSCRIPT_FULL_factcheck_audit.docx and outputs/full_audit_rows_v2.json.
Earlier rows are carried over unchanged. Table numbers inside them follow the earlier 26 table numbering, and the mapping to the current numbers is printed in the document."""
import json, re, collections, docx
from docx.shared import Pt, Cm
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
B = r'.'
A, PA, UN, MI, IN, UV = 'Accurate', 'Partially accurate', 'Unsupported', 'Misleading', 'Incorrect', 'Unable to verify'
old = json.load(open(B + r'\outputs\full_audit_rows.json', encoding='utf-8'))['rows']
FIXED = ' Fixed in the manuscript.'
new = [
('Title', 'Title', 'Mapping the 2023 Deyr flood in Beledweyne, Somalia, using Sentinel-1: Optical validation and sensitivity of flood extent estimates', 'none', A,
 'MANUSCRIPT_full.docx against abstract_source.txt. The manuscript file carried this title while the source file and front matter still held an earlier title, so a rebuild would have reverted it. abstract_source.txt now uses this title.', 'n/a',
 'Content matches the title, which describes optical validation and sensitivity. The title colon is part of the title and was left.'),
('Methods', 'Table 2, relation column', 'Pre-event reference, filter window, VV threshold and VH threshold were fixed before the independent dates were scored', 'none', A,
 'Methods, Sentinel-1 flood detection: the combined rule setting with the highest F1 score was selected before any later date was scored', 'n/a', 'Matches the text.'),
('Methods', 'Table 2, relation column', 'Dark-surface exclusion was added after the independent dates had been scored once, chosen on the calibration date, and the dates were then scored again', 'none', A,
 'Methods: after the later dates had been scored once, a dark-surface cut-off was selected on the calibration date and the later dates were then scored again. Script 04 ran after script 03', 'n/a', 'Matches the text and the script order.'),
('Methods', 'Table 2, relation column', 'Minimum cluster size was added after the independent dates had been scored twice, chosen on the calibration date, then scored a third time', 'none', A,
 'Methods: cluster size added after the first full-area run, selected on the calibration date, later dates scored a third time', 'n/a', 'Matches the text.'),
('Methods', 'Table 2, relation column', 'Permanent water threshold is a fixed choice, not tuned on any scored date', 'none', A,
 'Scripts 03 to 05 contain no use of the surface water occurrence layer, which first appears in scripts 06 and 07 with the fixed threshold of 75%', 'n/a', 'No tuning step is recorded.'),
('Methods', 'Table 2, relation column', 'HAND limit, slope limit and intensity classes were derived from reference pixels that include the Gaofen-2 independent date', 'none', A,
 'Methods: the HAND limit is the maximum among pixels UNOSAT mapped as flooded in the Pléiades and Gaofen-2 products, the slope limit is the 99th percentile of the same pixels, and the intensity bins were tabulated for the Pléiades and the Gaofen-2 pairs', 'n/a',
 'Accurate but it limits how independent the Gaofen-2 date is. Stated in the table so readers can judge. See Priority issues.'),
('Results', 'Table 3', 'Land-cover map area, hold-out and cross-validation agreement by class, overall 0.90 with kappa 0.86 for the hold-out and 0.90 with kappa 0.87 for the cross-validation', 'none', A,
 'lulc_accuracy_vs_consensus.json overall_accuracy 0.8981, kappa 0.8648. revision_lulc_blockcv.json OA 0.8988, kappa 0.8735. Class values trace to the same files', 'n/a', 'All values trace. Merged from two earlier tables.'),
('Results', 'Table 3 note', 'Training points were 500 minus the hold-out points', 'none', A, 'Training 417, 375, 408, 496, 431 and hold-out 83, 125, 92, 4, 69, each pair sums to 500', 'n/a', 'Matches.'),
('Results', 'Table 4', 'Flagged area and share of the analysed area by class and date', 'none', A,
 'flood_stats_by_landcover.csv. Every cell traced, for example built-up 78.40 km² and 40.37% on 14 November, all classes 225.84 km² and 6.12%', 'n/a',
 'Merged from two earlier tables. Brackets in the cells were replaced by a slash to follow the manuscript style.' + FIXED),
('Results', 'Table 7', 'Alternative configurations with their definitions and results', 'none', A,
 'sensitivity_flood_area_14Nov.csv and the definitions of the earlier Methods Table 3. For example 225.8, 573.8 and 185.1 km² with the cluster filter', 'n/a', 'Definitions and values match. Merged from two earlier tables.'),
('Results', 'Figure 6 legend', 'Agreement with UNOSAT on the calibration date and on the two independent dates for three rules', 'none', PA,
 'validation_with_kappa_and_exclusion.csv. The independent dates are scored outside the calibration extent', 'n/a',
 'The earlier legend did not say that the independent dates are scored outside the calibration extent. Added.' + FIXED),
('Results', 'Figure 6 bars', 'Bar values for precision, recall, balanced accuracy and kappa', 'none', A,
 'Final rule Pléiades 0.72, 0.70, 0.79, 0.58 and Gaofen-2 0.92, 0.56, 0.76, 0.53 match the text and Table S5', 'n/a', 'All bar labels match the text.'),
('Results', 'Figure S1', 'Flooded share by backscatter drop and by number of dates flagged', 'none', A,
 'severity_test_P_flooded_by_dVV_bin.csv and severity_test_persistence.csv. Persistence shares 0.12, 0.41, 0.62, 0.83 and 0.27, 0.81, 0.92, 0.92 match the Results text', 'n/a', 'Matches.'),
('Results', 'Figure S2', 'VV before, after and change over Beledweyne with the UNOSAT Pléiades 12 November flood extent', 'none', A,
 'Panels use the mean of 9 and 21 October, 14 November and the difference. Outline is the Pléiades flood extent', 'n/a',
 'The UNOSAT analysis extent is not drawn, so large decreases outside the outline can be misread. Kept in the supplement for that reason.'),
('Results', 'Figure 4 legend', 'Intensity on 14 November, panel a, and persistence from 14 November to 8 December, panel b', 'none', A,
 'Two earlier figures combined, legends of both panels unchanged', 'n/a', 'Matches.'),
('Results', 'Effect of the evaluation grid', 'Flagged area 51.163 km² at 10 m, 45.741 at 20 m and 45.002 at 30 m, and the added local results 51.160, 45.672 to 45.789, 45.579 and 44.839 km²', 'none', A,
 'resolution_check.json and grid_window_test.json written by script 81', 'n/a', 'All traced.'),
('Results', 'Effect of the evaluation grid', 'The paragraph also described the checks and explained the cause of the decrease (before correction)', 'none', MI,
 'Section boundary. The method sentence and the interpretation belonged in the Methods and the Discussion', 'n/a',
 'Results keep the numbers only. The method sentence is in the Methods and the explanation is in the Discussion.' + FIXED),
('Methods', 'Sensitivity analyses', 'Local 10 m flag layer averaged to 20 m, inputs sampled at 20 m with 4 offsets, windows of 9 by 9 and 11 by 11 pixels, and the Earth Engine run still filtered at the 20 m scale', 'none', A,
 'scripts 15 and 81. In script 15 the focal median is applied after the reprojection, so it runs at the output scale', 'n/a', 'Matches the scripts.'),
('Discussion', 'Limitations', 'The area over the town extent fell from 51.2 to 45.7 km² when the grid was coarsened from 10 m to 20 m, not through counting but through the ground size of the 5 by 5 pixel window, since the 10 m rule gave 45.6 km² with a 9 by 9 pixel window', 'none', A,
 'resolution_check.json 51.163 and 45.741. grid_window_test.json averaged to 20 m 51.1595, window 9 gives 45.5786, window 11 gives 44.8387', 'n/a',
 'Supported by a controlled test. The earlier sentence said only that a coarser grid changed the area and did not give a cause.' + FIXED),
('Results', 'Table S13', 'Row labelled Earth Engine, inputs reprojected to 10 m, 20 m grid, 45.725 km² (before correction)', 'none', MI,
 'Script 15 applies focalMedian after the reprojection, so the filter ran at the 20 m scale and the row did not isolate the grid', 'n/a', 'Relabelled to say that the filter ran at the 20 m scale. Value unchanged.' + FIXED),
('Results', 'Table S5 and text', 'Agreement table moved to the supplement with unchanged values', 'none', A, 'All values trace to validation_with_kappa_and_exclusion.csv', 'n/a', 'The chart in Figure 6 shows the independent dates outside the calibration extent, the table keeps the whole-extent rows.'),
('Results', 'Pre-event reference scenes', 'Of the area flagged with the 9 October reference, 96.4% lay inside the main footprint, and 96.5% of the main footprint lay inside the 21 October footprint', 'none', A,
 'revision_nested_footprints.json from script 86 gives 96.42% and 96.45%', 'n/a', 'Recomputed this round and now stored.'),
('Results', 'Coverage of the reference mapping', '99.37% of the analysed vegetation or rangeland lay outside every reference extent', 'none', A, 'Derived as 100 minus 0.63%, the share inside the union, from revision_validation_coverage_by_class.csv', 'n/a', 'Derived value.'),
('Results', 'Study area, exclusions', 'The MERIT Hydro grid held 65656 pixels with a HAND of exactly 0 m', 'none', UV,
 'The count comes from the console output of script 65, an Earth Engine call that is not stored in a file, and cannot be recomputed offline', 'n/a', 'Stated as in the earlier audit. Store the count in a file when the script is next run.'),
('Results', 'Effect of the evaluation grid', 'The exported 10 m flag layer gave 51.123 km² over the town extent', 'none', A, 'Recomputed from the raw 14 November export in script 37 and carried over from the earlier audit', 'n/a', 'Not stored in a table file.'),
('Whole manuscript', 'DOI format', 'Every DOI shows only its number and links to https://doi.org/ followed by the DOI', 'none', A,
 'MANUSCRIPT_full.docx contains 70 hyperlinks and 37 unique DOIs. The visible text equals the DOI in every link, no https text is left, and no author-year text sits beside a DOI', 'n/a', 'Checked on the rebuilt file.'),
('Whole manuscript', 'DOI resolution', 'All 37 DOIs resolve and none is retracted', 'none', A,
 'Crossref returned metadata for 36 DOIs and DataCite for 10.48550/arXiv.2107.12283, the Open Buildings preprint by Sirko et al. 2021. Crossref lists no retraction. The only update notice is the author correction to Rogers et al. 2025', 'yes',
 'Retraction Watch was not queried. Correction content was not read, as in the earlier audit.'),
('Whole manuscript', 'Numeric trace', 'Every number in the Abstract, Results, table cells, table notes and supplementary tables traces to the files in outputs/tables', 'none', A,
 'Script 85 traced all numbers except the 4 values listed in the rows above, each of which is explained', 'n/a', 'Rounding is half up at the printed precision.'),
('Whole manuscript', 'Style', 'No colons, semicolons, dashes or parentheses outside table and figure citations', 'none', IN,
 'Merged Table 4 cells had brackets, and some table row labels had brackets, introduced in the restructure', 'n/a', 'Cells use a slash and row labels use commas.' + FIXED),
('Whole manuscript', 'Style', 'Colons in the title, the structured Abstract labels and the Keywords line', 'none', PA,
 'Present before the restructure and part of the structured abstract format', 'n/a', 'Left unchanged. Remove them if the journal does not use a structured abstract.'),
('Whole manuscript', 'Cross-references', 'Every table and figure citation points to an existing exhibit in order of first appearance', 'none', A,
 'Captions run Figure 1, Tables 1 and 2, Figure 2, Table 3, Figure 3, Tables 4 and 5, Figures 4 to 6, Tables 6 and 7, Figure 7 and Table 8. Supplementary Tables S1 to S13 and Figures S1 and S2 are cited', 'n/a',
 'The Discussion now cites Table 6 and the Methods cite Table 7.'),
]
rows = [list(r) + [''] * (8 - len(r)) for r in new]
carried = [r for r in old]
allrows = [['Carried over'] + r for r in carried] + [['This round'] + r for r in rows]
cnt = collections.Counter(r[5] for r in allrows)
summary = 'Total claims checked: %d | Accurate: %d | Partially accurate: %d | Unsupported: %d | Misleading: %d | Incorrect: %d | Unable to verify: %d | Retracted/fabricated: 0' % (len(allrows), cnt[A], cnt[PA], cnt[UN], cnt[MI], cnt[IN], cnt[UV])
print(summary); print('this round only:', dict(collections.Counter(r[4] for r in new)), len(new))
json.dump(dict(summary=summary, rows=[r[1:] for r in allrows], this_round=len(new)), open(B + r'\outputs\full_audit_rows_v2.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
# ---------------- document
d = docx.Document(); s = d.sections[0]; s.orientation = WD_ORIENT.LANDSCAPE; s.page_width, s.page_height = s.page_height, s.page_width
for m in ('left_margin', 'right_margin', 'top_margin', 'bottom_margin'): setattr(s, m, Cm(1.5))
st = d.styles['Normal']; st.font.name = 'Cambria'; st.font.size = Pt(8.5); st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Cambria')
def shade(cell, col):
    tcPr = cell._tc.get_or_add_tcPr(); sh = OxmlElement('w:shd'); sh.set(qn('w:val'), 'clear'); sh.set(qn('w:fill'), col); tcPr.append(sh)
def para(t, b=False, size=None):
    p = d.add_paragraph(); r = p.add_run(t); r.bold = b
    if size: r.font.size = Pt(size)
    return p
para('Fact-check audit of the full manuscript and supplementary material', True, 13)
para('Audit of MANUSCRIPT_full.docx and MANUSCRIPT_Supplementary_tables.docx. The 319 rows of the earlier audit are carried over for text that did not change. %d rows were added after the exhibit restructure and the numeric, DOI and style checks were repeated on the rebuilt files.' % len(new))
para(summary, True)
para('Method and limits. Statements about the study were checked against the scripts in scripts/, the tables in outputs/tables and the figure files. Statements about other studies were checked against the abstract and the Crossref, OpenAlex or DataCite record, because full texts were not read. A claim whose source could not be reached is marked Unable to verify. Statuses of earlier rows describe the text before the correction noted in the last column. Table numbers inside the earlier rows follow the earlier numbering of 26 tables, which maps to the current numbers as follows.')
mp = {4: '3', 5: '3', 6: 'S1', 7: 'S2', 8: '4', 9: '4', 10: 'S3', 11: '5', 12: 'S4', 13: 'S5', 14: '6', 15: 'S6', 16: 'Figure S1', 17: 'S7', 18: 'S8', 19: 'S9', 20: 'S9', 21: 'S10', 22: '7', 23: 'S11', 24: 'S12', 25: '8', 26: 'S13'}
para('; '.join('earlier Table %d to %s' % (k, v if v.startswith('Fig') else 'Table ' + v) for k, v in mp.items()) + '. Earlier Figure 4 and 5 are now Figure 4 panels a and b, earlier Figure 6 is Figure 5 and earlier Figure 7 is Figure 7, and Figure 6 is the former chart fig4_validation_vs_unosat.')
hdr = ['Round', 'Section', 'Location', 'Claim', 'Citation', 'Status', 'Source and evidence', 'Citation supports', 'Notes and fix']
def add_table(rs, title):
    para(title, True, 11)
    t = d.add_table(rows=1, cols=len(hdr)); t.style = 'Table Grid'
    for i, h in enumerate(hdr):
        c = t.rows[0].cells[i]; c.text = ''; r = c.paragraphs[0].add_run(h); r.bold = True; shade(c, 'D9D9D9')
    for r_ in rs:
        cells = t.add_row().cells
        for i, v in enumerate(r_): cells[i].text = str(v)
        col = {A: 'E2F0D9', PA: 'FFF2CC', UN: 'F8CBAD', MI: 'F8CBAD', IN: 'F8CBAD', UV: 'DDEBF7'}.get(r_[5]);
        if col: shade(cells[5], col)
    for row in t.rows:
        for i, w in enumerate([1.6, 1.8, 2.2, 5.6, 2.6, 1.9, 6.2, 1.5, 4.8]): row.cells[i].width = Cm(w)
add_table([r for r in allrows if r[0] == 'This round'], 'Rows checked this round')
para('Priority issues', True, 11)
for t in [
 '1. Independence of the Gaofen-2 date. The HAND limit, the slope limit and the intensity classes were derived partly from Gaofen-2 reference pixels, and the dark-surface cut-off and the cluster size were added after the independent dates had been scored. The final accuracy on the Gaofen-2 and WorldView-2 dates is therefore a held-out test with some post hoc refinement, not an untouched validation. Table 2 now states this. The Abstract and Discussion should keep calling it a test outside the calibration area and not an independent validation without qualification.',
 '2. The grid table row. The earlier Table S13 row for inputs reprojected to 10 m did not isolate the grid, because the filter ran at the 20 m scale. It is relabelled and a controlled window test now explains the 51.2 to 45.7 km² difference.',
 '3. A section boundary error in the Results grid paragraph, now corrected, and brackets in table cells that came in with the restructure, now corrected.',
 '4. Built-up exposure. Only 4 hold-out points were built-up, so the 0.25 and 0.06 agreement cannot support any statement, and the cross-validation values of 0.81 and 0.88 are the better guide. The flagged built-up share of 40.37% describes mapped built-up pixels, and most of them lay more than 500 m from a building centroid.',
 '5. Citation checks of the Introduction and Discussion rest on abstracts and metadata, not on full texts. Specific thresholds or per-class results quoted from other studies, if any, should be checked by the authors against the full papers.',
 '6. Unable to verify. The count of 65656 pixels with HAND 0 m, the content of the author correction to Rogers et al. 2025, the possible self-citation of Ali et al. 2026, and the placeholders for the data archive and approval status.',
 '7. Style. Colons remain in the title, the structured Abstract labels and the Keywords line. Remove them if the journal does not use a structured abstract.']: para(t)
para('No fabricated references, no retracted papers and no broken DOIs were found.', True)
add_table([r for r in allrows if r[0] == 'Carried over'], 'Rows carried over from the earlier audit, text unchanged')
d.save(B + r'\MANUSCRIPT_FULL_factcheck_audit.docx'); print('saved')
