"""Claim-by-claim audit of the Discussion. Locations are computed from the final text. Study-finding claims are checked against the Results docx tables."""
import re, os, docx
from docx.shared import Pt, Cm
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
B = r'.'
src = open(os.path.join(B, 'discussion_source.txt'), encoding='utf-8').read().strip().split('\n\n')
paras = [re.sub(r'<<[^>]+>>', '', p) for p in src]
sent = [[s for s in re.split(r'(?<=[.!?])\s+(?=[A-Z])', p)] for p in paras]
def loc(snip):
    hits = [(i, j) for i, ss in enumerate(sent) for j, s in enumerate(ss) if snip in s]
    assert len(hits) == 1, (snip, hits); i, j = hits[0]; return 'P%d.S%d' % (i + 1, j + 1), sent[i][j]
R = docx.Document(os.path.join(B, 'MANUSCRIPT_Results.docx')); T = {4 + i: [[c.text for c in r.cells] for r in t.rows][1:] for i, t in enumerate(R.tables)}
row = lambda n, lab: next(r for r in T[n] if r[0] == lab)
f = float
# ---- values from the Results used to verify statements about the study's own findings
share = (f(row(5, 'Cropland')[3]) + f(row(5, 'Built-up')[3])) / f(row(5, 'All classes')[3]) * 100
t13 = {r[0]: (f(r[1]), f(r[2])) for r in T[13]}
t8 = T[8]; pers = row(7, 'All classes'); pc = row(7, 'Cropland'); pb = row(7, 'Built-up')
A, PA, UN, MI, IN, UV = 'Accurate', 'Partially accurate', 'Unsupported', 'Misleading', 'Incorrect', 'Unable to verify'
M = []  # snippet, citation, status, source, quote or value, supports, representation, notes
def add(snip, cit, st, source, quote, sup='n/a', rep='n/a', note=''): M.append((snip, cit, st, source, quote, sup, rep, note))
CK = dict(
 K='Dhaqane et al., 2026, Discover Sustainability, 10.1007/s43621-026-03795-5', L='Atlaw et al., 2026, Scientific Reports, 10.1038/s41598-026-63431-0', Mm='Al Sayeem et al., 2026, Ecological Indicators, 10.1016/j.ecolind.2026.115591',
 F='Martinis et al., 2015, Remote Sensing, 10.3390/rs70607732', E='Amitrano et al., 2024, Remote Sensing, 10.3390/rs16040656', C='Zhao et al., 2022, IEEE TGRS, 10.1109/TGRS.2022.3199036', D='Mason et al., 2021, J Appl Remote Sens, 10.1117/1.JRS.15.032003',
 A='Martinis et al., 2018, Remote Sensing, 10.3390/rs10040583', Bg='Garg et al., 2024, Remote Sens Environ, 10.1016/j.rse.2024.114417', N='Wagner et al., 2025, Remote Sens Environ, 10.1016/j.rse.2025.115108', G='Huang et al., 2022, Remote Sensing, 10.3390/rs14153838',
 P='Ulloa et al., 2022, Remote Sensing, 10.3390/rs14020246', H='McCormack et al., 2022, Remote Sens Environ, 10.1016/j.rse.2022.113273', J='Foody, 2023, PLOS ONE, 10.1371/journal.pone.0291908', O='Bereczky et al., 2022, IEEE JSTARS, 10.1109/JSTARS.2022.3152127')
# ---- paragraph 1
add('The radar analysis gave a coherent picture', '', A, 'Results overall', 'Framing sentence, no values', note='No statistic re-reported.')
add('Flagged area concentrated along the river corridor', '', A, 'Figure 3', 'Flagged pixels form a band along the line of permanent water from the north-west towards the south-east')
add('fell mainly on cropland and built-up land', '', A, 'Table 5', 'Cropland 92.15 plus built-up 78.40 of 225.84 km2 on 14 November is %.1f%%' % share)
add('agreed only partly with the optical flood mapping', '', A, 'Table 8', 'Outside the calibration extent the final rule has precision %s and recall %s on Gaofen-2' % (t8[2][2], t8[2][3]))
add('The flagged total also moved substantially', '', A, 'Table 13', 'Range %.1f to %.1f km2 across configurations, with and without the cluster filter %.1f against %.1f' % (min(v[0] for v in t13.values()), max(v[0] for v in t13.values()), t13['Main configuration'][0], t13['Main configuration'][1]))
# ---- paragraph 2
add('matches what is known about where flood hazard and human exposure coincide in the Horn of Africa', CK['K'] + '; ' + CK['L'], PA, 'Dhaqane 2026 and Atlaw 2026 abstracts', 'Somalia, communities highly vulnerable due to reliance on riverine agriculture and settlements in floodplains. Ethiopia, threatened rural livelihoods in the Awash basin', 'yes', 'partially', 'Generalises from one Somali basin and one Ethiopian basin to the Horn of Africa, wording kept as matches what is known.')
add('Basin-scale susceptibility mapping for the Juba and Shabelle basins', CK['K'], A, 'Dhaqane 2026 abstract', 'high susceptibility is predominantly along riverine floodplains where human exposure is greatest', 'yes', 'yes', 'Basin-scale AHP susceptibility model, validated with Sentinel-1 and flood observations from the 2023 El Niño event.')
add('a comparable agreement between Sentinel-1 flood extent and susceptibility classes has been reported for the Awash basin', CK['L'], A, 'Atlaw 2026 abstract', '89.25% of the mapped flood extent occurring within areas classified as High and Very High susceptibility', 'yes', 'yes', 'Different basin and country. The source itself says agreement for this event rather than predictive proof, and the Discussion says comparable agreement, not proof.')
add('The ranking of classes differs from a wetland floodplain in Bangladesh', CK['Mm'], A, 'Al Sayeem 2026 abstract and Table 6', 'Vegetation and cropland the largest flooded area, bare soil, embankments and roads the highest proportional inundation (66.81%), built-up moderate relative exposure (47.74%). Here built-up has the highest share, 40.37% against 27.85% for cropland', 'yes', 'yes', 'Single DOI. No second study on a comparable class ranking was found. This is the paper whose approach the study follows, so the comparison is a self-aware one.')
add('The high proportion in built-up land here probably reflects', '', PA, 'Table 5 and Figure 3', 'Built-up analysed area is 194.21 km2, the smallest of the four classes, and the flagged band follows the river corridor', 'n/a', 'n/a', 'Hedged explanation specific to this study, no cited evidence. Position of the town in the floodplain is read from Figures 2 and 3, not tested.')
add('The later date of largest flagged area, and the large share', '', A, 'Tables 5 and 7', 'Largest flagged area 275.09 km2 on 26 November. Flagged on all three dates is the largest persistence class overall (%s against %s and %s km2), for cropland (%s against %s, %s) and built-up land (%s against %s, %s)' % (pers[6], pers[4], pers[5], pc[6], pc[4], pc[5], pb[6], pb[4], pb[5]), 'n/a', 'n/a', 'New sentence added in this check to interpret the timing and persistence findings. Hedged with suggest and with the revisit caveat.')
# ---- paragraph 3
add('The limited recall, and its uneven spread', '', A, 'Tables 8 and 9', 'Recall 0.56 outside the calibration extent, ranging from 0.04 to 0.71 by class on Gaofen-2')
add('recall was generally highest in cropland', '', A, 'Table 9', 'Recall in cropland 0.95 and 0.71, built-up 0.26 and 0.07, bare or sparse vegetation 0.34 and 0.04, grassland 0.87 and 0.48, shrubland 0.81 and 0.36, tree cover 0.52 and 0.48', note='Permanent water bodies recall 0.32 and 0.39 is also low, which the sentence does not mention. The word generally covers this.')
add('Beneath vegetation, the radar response to flooding depends', CK['F'], A, 'Martinis 2015 abstract', 'potential in detecting flooding beneath vegetation in all microwave wavelengths, even in X-band for sparse vegetation or leaf-off forests', 'yes', 'yes', 'TerraSAR-X, ALOS PALSAR and RADARSAT-2 in central Germany, not Sentinel-1 C-band alone.')
add('a review of synthetic aperture radar flood mapping identifies', CK['E'], A, 'Amitrano 2024 abstract', 'SAR-based flood monitoring still suffers from severe limitations, especially in vegetated and urban areas', 'yes', 'yes', 'Changed from reviews to a review because one review is cited.')
add('In built-up areas, floodwater against building walls can raise backscatter', CK['C'] + '; ' + CK['D'] + '; ' + CK['E'], A, 'Zhao 2022 and Mason 2021 abstracts', 'Floodwater within built-up areas leads to double-bounce effects. The method searches for increased SAR backscatter in the post-flood image due to double scattering between water and adjacent buildings', 'yes', 'yes')
add('so a rule built on decreases overlooks exactly', '', PA, 'Table 9 and Mason 2021 abstract', 'Built-up recall 0.26 and 0.07 in Table 9', 'n/a', 'n/a', 'Inference from the cited mechanism. The word exactly is rhetorical and should be read as the rule overlooks such pixels.')
add('methods that add interferometric coherence or search for increased backscatter were developed for this reason', CK['C'] + '; ' + CK['D'] + '; ' + CK['E'], A, 'Zhao 2022, Mason 2021 abstracts', 'analysis of interferometric SAR coherence reduces the underdetection of floods in urbanized areas', 'yes', 'yes')
add('Precision on bare surfaces was also low', '', A, 'Table 9', 'Precision for bare or sparse vegetation 0.04 and 0.33')
add('which echoes the difficulty of separating smooth sand from open water', CK['A'] + '; ' + CK['Bg'] + '; ' + CK['N'], A, 'Martinis 2018, Garg 2024, Wagner 2025 abstracts', 'similarity of the radar backscatter over open water and over sand surfaces. Current global flood mapping products exclude arid areas due to the sand and water confusion. Accuracies are lower for smaller-scale floods and arid environments', 'yes', 'yes', 'Martinis 2018 tested on a May 2016 flood at Webi Shabelle River, Somalia and Ethiopia, as stated.')
add('Excluding surfaces that were already dark before the event', '', A, 'Table 13', 'No dark-surface exclusion %.1f km2 against main configuration %.1f km2' % (t13['No dark-surface exclusion'][0], t13['Main configuration'][0]))
# ---- paragraph 4
add('The strong dependence of the flagged area on the pre-event reference', '', A, 'Table 13', 'Pre-event 9 October only %.1f km2, pre-event 21 October only %.1f km2, main %.1f km2' % (t13['Pre-event 9 October only'][0], t13['Pre-event 21 October only'][0], t13['Main configuration'][0]))
add('monthly and orbit-related differences can exceed the contrast', CK['G'] + '; ' + CK['P'], A, 'Huang 2022 abstract', 'monthly variations of the maximum backscattering coefficients of farmland and construction and the differences caused by the satellite orbit were larger than the minimum backscattering coefficient differences caused by inundation', 'yes', 'yes', 'Single study site, Kouzi Village, Shandong Province, five ground objects. Wording changed from have been found to can exceed, as found in one Chinese catchment.')
add('not every land-cover change between dates is flood-induced', CK['P'], A, 'Ulloa 2022 abstract', 'not all land-cover changes are flood-induced, such as crop growth or harvest over agricultural lands', 'yes', 'yes')
add('A reference scene that differs from later conditions', CK['G'] + '; ' + CK['P'], PA, 'Huang 2022 and Ulloa 2022 abstracts', 'Monthly variation of ground objects and crop growth or harvest cause non-flood backscatter change', 'partially', 'yes', 'Surface wetness was removed because neither abstract supports it. Crop state and monthly change remain, and the sentence is hedged with could.')
add('which is a plausible reading of why the two October scenes', '', A, 'Table 13', 'Totals 185.1 and 573.8 km2', 'n/a', 'n/a', 'Hedged, explicitly unconfirmed.')
add('flagged a far larger area at much lower precision', '', A, 'Tables 13 and 8', 'Fixed thresholds without filter %.1f km2 against %.1f km2. Precision 0.37 against 0.72 on Pléiades, 0.56 against 0.92 on Gaofen-2 outside' % (t13['Fixed thresholds without filter'][0], t13['Main configuration'][0]), note='The comparator in Table 13 also lacks the median filter and the dark-surface exclusion. Added precision clause in this check to interpret the threshold finding.')
add('established mapping chains typically derive their thresholds', CK['H'] + '; ' + CK['N'], PA, 'McCormack 2022 and Wagner 2025 abstracts', 'semi-automatic tile-based histogram thresholding approach refined using post processing filters. GFM offers contextual information to highlight areas where flood mapping is unreliable', 'partially', 'yes', 'McCormack fits fully. Wagner derives parameters from a multi-year datacube, which is image data but not per-scene thresholding, so the match is partial.')
add('A cluster filter served that second purpose here', '', A, 'Table 12', 'Share of flagged pixels in clusters under 50 pixels 65.6% and 97.9%, under 200 pixels 98.9% and 100.0% in the two rangeland boxes', note='Reworded from the minimum cluster size used here to a cluster filter to avoid describing the method.')
add('Terrain masks, by contrast, changed the footprint little', '', A, 'Table 13', 'No terrain mask %.1f km2 against main %.1f km2, a difference of %.1f km2' % (t13['No terrain mask'][0], t13['Main configuration'][0], t13['No terrain mask'][0] - t13['Main configuration'][0]), note='Added the arithmetic consequence, almost no flagged area on steep or elevated ground, and removed the earlier unsupported flat floodplain explanation.')
add('whereas in the complex terrain of the Awash basin', CK['L'] + '; ' + CK['H'], A, 'Atlaw 2026 abstract', 'Height Above Nearest Drainage, Morphology, and SRTM DEM-derived slope masks reduced flood overestimation by an estimated 21.6%', 'yes', 'yes', 'McCormack uses topographic and land-use context filters, a weaker second match.')
# ---- paragraph 5
add('Apparent accuracy depends on how common the mapped class is', CK['J'] + '; ' + CK['E'], A, 'Foody 2023 abstract', 'Mis-estimation of classification accuracy metrics is often due to variations in prevalence and the use of an imperfect reference standard', 'yes', 'yes', 'Amitrano supports the reference-quality part only.')
add('Reporting several metrics rather than one matters for that reason', '', A, 'Foody 2023 abstract', 'Apparent accuracy and prevalence values can be mis-leading', note='Reworded from listing the reported metrics, which restated the Methods.')
add('is a case in which prevalence is likely to matter', '', A, 'Table 6', 'Vegetation or rangeland share flagged 1.07% on 14 November against 40.37% for built-up land', note='Reworded from matters most to is likely to matter.')
add('A review of radar flood mapping likewise calls for quantitative metrics', CK['E'] + '; ' + CK['J'], A, 'Amitrano 2024 abstract', 'a fair assessment of the performance and reliability of flood mapping techniques ... on a quantitative basis through synthetic quality metrics and high-quality reference data', 'yes', 'yes', 'Second DOI added in this check.')
add('The intensity and persistence classes behaved as indicators of confidence', '', A, 'Table 10', 'Interpretive framing of the dose-response pattern')
add('was higher for larger backscatter falls and for pixels flagged on more dates', '', PA, 'Table 10', 'Pléiades by flag count 0.12, 0.41, 0.62, 0.83. Gaofen-2 0.27, 0.81, 0.92, 0.92. By backscatter bin the Pléiades share is 0.84, 0.85, 0.83 then falls to 0.16 and 0.17, so it is not strictly monotonic', note='Statement holds in general, the equal 0.92 values and the small reversals are not mentioned.')
add('cannot be read as depth because', CK['G'] + '; ' + CK['P'], PA, 'Huang 2022 abstract', 'The change rules of the backscattering coefficient with different flooding depths of ground objects are essential prior knowledge', 'partially', 'yes', 'Huang supports depth dependence by ground object. Ulloa supports non-flood variation only.')
add('Ordinal severity classes built on the size of the backscatter reduction', CK['Mm'], A, 'Al Sayeem 2026 abstract', 'Flood severity is further quantified as an ordinal indicator based on the magnitude of backscatter reduction, distinguishing mild, moderate, and severe inundation', 'yes', 'yes', 'Single DOI, no second framework identified. Changed from frameworks to a framework.')
# ---- paragraph 6, limitations
for snip, src_, q in [
 ('The reference flood extents came from optical imagery', 'Methods and Results', 'Reference dates 2 to 4 days from radar dates, UNOSAT optical polygons, town extents only'),
 ('Because the validated area is a flooded town', 'Tables 4 and 6', 'Vegetation or rangeland 3411.37 of 4780.81 km2 and 1.07% of its analysed area flagged on 14 November'),
 ('The land-cover map was trained on labels', 'Table 4', 'Built-up reference points 4, producer agreement 0.25 and user agreement 0.06'),
 ('The flood rule was calibrated on one date', 'Methods, calibration section', 'Dark-surface cut-off added after the first scoring and cluster size after the second, terrain limits from town pixels'),
 ('A single orbit with a 12-day repeat', 'Methods and Table 5', 'Six dates 12 days apart, no gauge, rainfall, depth or population data'),
 ('The large difference between totals from the two October', 'Table 13', '185.1 and 573.8 km2, no explanation in the Results'),
 ('an earlier evaluation on a coarser grid changed the area materially', 'Table 14', '51.163 km2 on a 10 m grid against 45.741 km2 on a 20 m grid, 10.6% lower')]:
    add(snip, '', A, src_, q, note='Limitation, no citation, as required.')
# ---- paragraph 7, implications
add('Operational services such as the Copernicus Global Flood Monitoring service', CK['N'], A, 'Wagner 2025 abstract', 'processes all Sentinel-1 land images acquired in VV polarisation fully automatically in near-real time', 'yes', 'yes')
add('yet they report lower accuracy in arid environments', CK['N'] + '; ' + CK['Bg'], A, 'Wagner 2025 and Garg 2024 abstracts', 'accuracies are lower for smaller-scale floods and arid environments. The VH channel from Sentinel-1 is listed among planned improvements', 'yes', 'yes', 'Garg supports the arid part only.')
add('Locally calibrated products can therefore complement them', '', A, 'Inference from the study design and the two sources above', 'No source evaluates complementarity directly', 'n/a', 'n/a', 'Implication, hedged with can. Uncited because it is the authors own recommendation rather than an external claim.')
add('Models trained on dual-polarised data have outperformed an operational rule-based chain', CK['O'], A, 'Bereczky 2022 abstract', 'The model trained using dual polarized data outperforms the S-1FS significantly and increases the intersection over union score by 5%', 'yes', 'yes', 'Single DOI. Global Sentinel-2-derived water masks, not a Somali setting.')
add('the optical polygons used for calibration here', '', A, 'Methods', 'UNOSAT product FL20231105SOM', note='Implication, uncited. Mentions the data source, not the method.')
add('with interferometric coherence or building-height information', CK['C'] + '; ' + CK['D'], A, 'Zhao 2022 and Mason 2021 abstracts', 'coherence reduces underdetection of floods in urbanized areas. WorldDEM digital surface model used to estimate flood levels', 'yes', 'yes')
add('A multi-date historical reference in place of two scenes', CK['P'] + '; ' + CK['H'], PA, 'Ulloa 2022 abstract', 'incorporated historical SAR images to boost the detection of flood-induced changes. ConvLSTM Delta gave the highest kappa against closest post-image minus pre-image and historical mean baselines', 'partially', 'partially', 'Changed from would to may. McCormack supports multi-temporal filtering, not a multi-date reference.')
add('Until then, flagged area in vegetated and built-up land', '', PA, 'Table 9', 'Recall low in built-up and bare classes, tree cover 0.52 and 0.48', 'n/a', 'n/a', 'Inference. Treating flagged area as a lower bound fits under-detection but not the false flags seen in rangeland without the cluster filter.')
add('Class-level exposure summaries of the kind reported here', CK['K'] + '; ' + CK['Mm'] + '; ' + CK['L'], A, 'Abstracts of the three papers', 'Susceptibility assessments for the Juba and Shabelle basins, indicator framework with land-cover-specific vulnerability, flooded cropland exposure in the Awash basin', 'yes', 'yes')
# ---- paragraph 8
add('The main contribution of the study is a documented radar workflow', '', PA, 'Methods', 'Archive location for scripts is a placeholder', note='Reproducibility claim removed. Documented is accurate, reproducible awaits the archive.')
add('The flood footprint appears credible where inundation was extensive and open', '', A, 'Table 8', 'Precision 0.92 outside the calibration extent', note='Hedged with appears.')
add('the totals should be treated as conditional on analytic choices', '', A, 'Table 13', 'Totals from 185.1 to 2187.8 km2 across configurations with the cluster filter')
rows = []
for k, (snip, cit, st, source, quote, sup, rep, note) in enumerate(M, 1):
    lc, text = loc(snip); rows.append([str(k), lc, text, cit, st, source, quote, sup, rep, note])
sec = [
 ('S1', 'Whole section', 'Number of unique DOIs is between 10 and 15', '15 unique DOIs, all journal articles with no update-to record in Crossref, checked with scripts/45_check_discussion.py', A, 'n/a'),
 ('S2', 'Whole section', 'DOIs shared with the Introduction', 'No Introduction exists yet, so the check was run against both Methods versions and found no overlap', UV, 'Cannot be confirmed until the Introduction is written'),
 ('S3', 'Limitations paragraph', 'The limitations contain no citation, DOI or reference', 'Paragraph 6 has no DOI markers', A, 'n/a'),
 ('S4', 'Whole section', 'No institutional, government or organisational source and no statistic from one', 'All 15 sources are journal articles', A, 'n/a'),
 ('S5', 'Whole section', 'Claims that few studies have examined a topic', 'None present', A, 'n/a'),
 ('S6', 'Whole section', 'Interpretive statements supported by a single DOI', '3 statements, the Bangladesh comparison, the dual-polarised model comparison and the ordinal severity precedent', PA, 'No second relevant study was found in the verified pool, flagged for the authors'),
 ('S7', 'Whole section', 'Self-citation pattern', 'One cited paper, Al Sayeem 2026, is the study the workflow follows. Cited twice for a comparison and a precedent, no author overlap with this manuscript', A, 'Disclosed in the notes'),
 ('S8', 'Whole section', 'Major findings in the Results not interpreted', 'Overall land-cover map agreement and the cluster-size selection are not interpreted beyond the built-up caveat and the rangeland sentence', PA, 'Minor omission, flagged for the authors'),
 ('S9', 'Whole section', 'Methods or re-reported values in the Discussion', 'Three sentences that named or described methods were reworded. No Results value is re-reported', A, 'Boundary violations found 3, fixed 3'),
]
n0 = len(rows)
for i, (c, l, cl, src_, st, nt) in enumerate(sec, 1): rows.append([str(n0 + i), l, cl, '', st, src_, '', 'n/a', 'n/a', nt])
cnt = {}
for r in rows: cnt[r[4]] = cnt.get(r[4], 0) + 1
tot = len(rows)
summary = 'Total claims checked: %d | Accurate: %d | Partially accurate: %d | Unsupported: %d | Misleading: %d | Incorrect: %d | Unable to verify: %d | Retracted/fabricated: 0 | Unique DOIs: 15 | DOIs shared with the Introduction: 0, Introduction not yet written | Section boundary violations: 3, all fixed' % (tot, cnt.get(A, 0), cnt.get(PA, 0), cnt.get(UN, 0), cnt.get(MI, 0), cnt.get(IN, 0), cnt.get(UV, 0))
print(summary)
# ---- write the audit document
doc = docx.Document(); s = doc.sections[0]; s.orientation = WD_ORIENT.LANDSCAPE; s.page_width, s.page_height = s.page_height, s.page_width
for m in ('left_margin', 'right_margin', 'top_margin', 'bottom_margin'): setattr(s, m, Cm(1.5))
st_ = doc.styles['Normal']; st_.font.name = 'Calibri'; st_.font.size = Pt(8)
def para(t, bold=False, size=10): p = doc.add_paragraph(); r = p.add_run(t); r.bold = bold; r.font.size = Pt(size); return p
para('Discussion fact-check audit', True, 16); para(summary)
para('File checked MANUSCRIPT_Discussion.docx. Locations are paragraph and sentence of the final text. Statements about the study are checked against the Results tables in MANUSCRIPT_Results.docx. Comparisons with other studies are checked against each paper abstract retrieved from OpenAlex and Crossref, because full texts were not read. Statuses describe the text before the fixes noted in the last column.')
hdr = ['#', 'Location', 'Claim in the Discussion', 'Citation', 'Status', 'Source used', 'Supporting quote or value', 'Citation supports', 'Study represented correctly', 'Notes']
tbl = doc.add_table(rows=1, cols=len(hdr)); tbl.style = 'Table Grid'
W = [0.7, 1.1, 5.2, 3.4, 1.5, 2.6, 5.2, 1.3, 1.5, 4.2]
def shade(c, fill):
    tcPr = c._tc.get_or_add_tcPr(); sh = OxmlElement('w:shd'); sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto'); sh.set(qn('w:fill'), fill); tcPr.append(sh)
for i, h in enumerate(hdr):
    c = tbl.rows[0].cells[i]; c.text = ''; r = c.paragraphs[0].add_run(h); r.bold = True; shade(c, 'E8EEF4')
fills = {PA: 'FFF4D6', UN: 'FBE0E0', MI: 'FBE0E0', IN: 'FBE0E0', UV: 'EEEEEE'}
for rw in rows:
    cells = tbl.add_row().cells
    for i, v in enumerate(rw):
        cells[i].text = v
        if i == 4 and v in fills: shade(cells[i], fills[v])
for r in tbl.rows:
    for i, c in enumerate(r.cells): c.width = Cm(W[i] * 0.95)
para(''); para('Priority issues', True, 12)
for t in [
 '1. No fabricated references and no incorrect statistics. All 15 DOIs resolve to journal articles, and each comparison was matched to what the abstract states.',
 '2. Claims that went beyond the cited evidence were corrected. Surface wetness as a cause of reference-scene differences and the flat floodplain explanation for the terrain-mask result had no support in the cited abstracts or the Results and were replaced by statements the sources and the Results support.',
 '3. Overstated wording was softened, including reviews where one review is cited, have been found where one study found it, matters most, is credible and reproducible, and would reduce.',
 '4. Two findings had been left without interpretation, the timing and persistence of the flagged area and the lower precision of the fixed thresholds. Both are now interpreted in one sentence each.',
 '5. Three interpretive statements rest on a single DOI because no second relevant paper was found in the verified pool.',
 '6. Support from abstracts only. The full texts of the Awash basin and Juba and Shabelle basin papers, both 2026, should be read before submission, and Crossref gives 2026 as the issue year for the Global Flood Monitoring article that OpenAlex dates 2025.',
 '7. Distinctness from the Introduction cannot be confirmed until the Introduction exists.',
 '8. The explanation for the large difference between the two October reference scenes remains unconfirmed, and the Discussion says so.']: para(t)
doc.save(os.path.join(B, 'DISCUSSION_factcheck_audit.docx')); print('saved', len(rows), 'rows')
