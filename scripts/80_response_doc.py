import docx
from docx.shared import Pt, Cm
from docx.enum.section import WD_ORIENT
B = r'.'
D = docx.Document(); s = D.sections[0]; s.orientation = WD_ORIENT.LANDSCAPE; s.page_width, s.page_height = Cm(29.7), Cm(21); 
for m in ('left_margin', 'right_margin', 'top_margin', 'bottom_margin'): setattr(s, m, Cm(1.8))
st = D.styles['Normal']; st.font.name = 'Cambria'; st.font.size = Pt(10)
h = D.add_paragraph(); r = h.add_run('Response to the major comments'); r.bold = True; r.font.size = Pt(14)
D.add_paragraph('New analyses were run on the existing 10 m rasters, the town rasters and four small downloads (HAND missing mask, 100 m Sentinel-1 means, CHIRPS rainfall, Open Buildings centroids). The main pipeline, thresholds and land-cover map were not changed, so every earlier flagged area is unchanged. Table numbers refer to the revised MANUSCRIPT_full.docx.')
rows = [
('1. Land-cover validation, built-up class',
 'The text already said agreement was with consensus labels. The Results now explain why the hold-out had 4 built-up points (nearly all built-up points fell in training blocks) and give the sample distribution (Table 5) and the error matrix (Table 6). A 5-fold spatial block cross-validation of the same classifier design gives overall 0.90, kappa 0.87 and built-up producer and user agreement of 0.81 and 0.88 on 500 points. A comparison with 62829 Open Buildings centroids (Tables 10 and 11) found that 75.4% of centroids fall in mapped built-up pixels, but only 12.6% of the mapped built-up area lies within 100 m of a centroid and 59.7% of the analysed built-up area is more than 500 m from any centroid. The flagged share is 18.35% within 100 m of a building and 47.26% beyond 500 m. Only 8.76% of buildings had a flagged centroid pixel on 14 November.',
 'The reviewer was right and the problem is larger than the 4 points. The built-up exposure share (40.37%) is dominated by mapped built-up pixels that are far from buildings. The Abstract, Discussion and Conclusion now call built-up exposure indicative and probably an overstatement for settlements. Open Buildings is a modelled product that may omit structures and is not field data, and what the far-from-building pixels are was not examined. No field reference exists.'),
('2. Pre-event reference sensitivity',
 'The extra area flagged with 21 October is mostly rangeland (69.7% of 355.93 km², Table 23, Figure 7). The three footprints are nested. The 21 October and 2 November scenes agree with each other (-0.05 dB in VV) and 9 October is darker than both by 1.7 to 1.8 dB in every class (Table 24). CHIRPS shows no rain in the 3 days before 9 October and 40.3 and 48.7 mm before 21 October and 2 November. Alternative references in the town (Table 25) show that a mean of three scenes behaves like the main reference. The Discussion and Abstract present totals as conditional estimates.',
 'The earlier suggestion that 21 October was the odd scene is reversed, 9 October differed. Rainfall as the cause is plausible but untested because no soil moisture data were used and CHIRPS is a coarse product. The diagnostics do not show which reference is correct for flooding. A multi-date baseline of more than the 2 pre-event scenes was not possible with this orbit.'),
('3. Validation coverage',
 'Table 15 gives area and land-cover composition of each reference mask. The three products together cover 126.06 km², 2.64% of the study area, and 0.63% of the analysed vegetation or rangeland, which is 66.03% of the analysed area. The Discussion states that the rule is not validated across the whole study area and that town accuracy cannot be carried to full-area totals.',
 'No independent reference exists outside the town, so this limitation is acknowledged, not resolved.'),
('4. Cluster filter',
 'Within the scoring masks the removed pixels were flooded 18.8% to 30.9% of the time against 46.9% prevalence on the independent dates (Tables 19 and 20), so some genuine flooding is removed, 1.6% to 2.0% of the reference flood area. Clusters of 50 to 99 pixels were flooded at least as often as the mask. Over the full area the filter removed 170.54 km², 81.7% of it in rangeland (Table 21). The 100 pixel size comes from the selection rule on the calibration date, the smallest size within 0.005 kappa of the best, and the rangeland boxes motivated testing a filter. The Discussion now says that kappa improvement does not prove all removed clusters were false and that fragmented flooding is probably underestimated.',
 'Rangeland, where most removed area lies, has no reference, so the choice cannot be tested there.'),
('5. Missing HAND values',
 'No pixel of the study rectangle has a missing HAND value, checked by an Earth Engine mask count and a 90 m download, so setting missing values to 0 m changed nothing. 65656 pixels of the MERIT Hydro grid have a HAND of exactly 0 m and are valid values.',
 'The Methods keep the 0 m setting and state that the count was made before it was applied.'),
('6. Area reporting',
 'Table 7 and the Abstract now separate the study area (4780.81 km²), permanent water excluded (21.29 km², 0.45%), terrain excluded (1067.02 km², 22.32%), the analysed area (3692.49 km², 77.24%) and the flagged area. The Methods define the four quantities.',
 'None.'),
]
t = D.add_table(rows=1, cols=3); t.style = 'Table Grid'
for i, c in enumerate(['Comment', 'What was done and where', 'What remains']): t.rows[0].cells[i].text = c; t.rows[0].cells[i].paragraphs[0].runs[0].bold = True
for a, b, c in rows:
    cells = t.add_row().cells; cells[0].text = a; cells[1].text = b; cells[2].text = c
for row in t.rows:
    for i, w in enumerate([4, 14, 7.5]): row.cells[i].width = Cm(w)
D.save(B + r'\RESPONSE_TO_REVIEWER_major_comments.docx'); print('ok')
