import sys, os, json, copy, shutil
sys.path.insert(0, os.path.dirname(__file__))
import docx
from docx.oxml.ns import qn
from docx.shared import Emu
import docedit as E
from docedit import q
B = r'.'; REV = os.path.join(B, 'Revision')
SRC = os.path.join(REV, 'MANUSCRIPT_full.docx'); OUT = os.path.join(REV, 'Manuscript_revised_colored.docx')
d = docx.Document(SRC); part = d.part; body = d.element.body
ch = list(body.iterchildren()); P = lambda i: ch[i]
def chk(i, start):
    t = E.ptext(ch[i]); assert t.startswith(start), (i, t[:60], start)
# reference paragraphs by index (checked)
chk(12, 'Methods: Sentinel-1'); chk(13, 'Results: Flagged'); chk(14, 'Conclusion: A locally'); chk(38, 'The classifier design'); chk(47, 'Permanent water'); chk(49, 'Flagged pixels of 14'); chk(52, 'True positives')
chk(56, 'The Earth Engine run'); chk(62, 'No formal sample'); chk(64, 'Analyses used'); chk(69, 'The map covered'); chk(76, 'The stratified sample'); chk(78, 'Of the 4780.81'); chk(97, 'Against the Pl')
chk(105, 'Note. Gaofen-2'); chk(115, 'The flagged area of 14 November was'); chk(132, 'The high flagged'); chk(134, 'In built-up areas'); chk(136, 'Rainfall estimates'); chk(139, 'Apparent accuracy'); chk(140, 'The reference flood'); chk(141, 'The flood rule was'); chk(145, 'Radar mapping'); chk(146, 'Radar flood totals'); chk(157, 'The Sentinel-1 scenes')
NORMAL = ch[28]   # a Normal body paragraph used as template for new paragraphs
D = lambda x: ('doi', x)
# ------------------------------------------------------------------ ABSTRACT
E.insert_after(part, P(12), 'of the 4780.81 km² study area.', [' The detection thresholds, filter window and pre-event reference were fixed on the calibration date before any independent scoring, whereas the dark-surface exclusion, the cluster filter and the terrain limits were refined afterwards.'], 'R1', 'R1-2a', 'Abstract, Methods')
E.replace(part, P(13), 'recall 0.56 and kappa 0.53', ['recall 0.56 (95% confidence interval 0.47 to 0.63) and kappa 0.53 (0.44 to 0.61)'], 'R1', 'R1-2e', 'Abstract, Results')
E.insert_after(part, P(14), 'and totals depended on the pre-event scene and filtering.', [' Agreement on the independent dates is conditional on refinements made after they were first scored, and a single orbit with a 12-day repeat could not resolve the flood peak.'], 'R1', 'R1-2a, R1-2h', 'Abstract, Conclusion')
# ------------------------------------------------------------------ METHODS
# typographical error in the building footprint sentence
E.replace(part, P(38), 'thContinental-Scale Building Detection from High Resolution Satellite Imagerye', ['the'], 'R2', 'R2-7', 'Methods, Land-cover mapping, fourth paragraph', kind='typo')
E.append(part, P(38), [' The number of built-up consensus pixels in each cell of 0.05° was also counted in Earth Engine to show how they were distributed over the 5 blocks. Confidence intervals at the 95% level were calculated for the agreement measures as Wilson intervals ', D('10.1080/01621459.1927.10502953'), ', or as exact binomial intervals ', D('10.1093/biomet/26.4.404'), ' where a measure rested on fewer than 30 points, in keeping with the recommendation to report the uncertainty of accuracy estimates ', D('10.1016/j.rse.2014.02.015'), '. To examine the effect of sample size, the cross-validation was repeated with caps of 100, 250 and 1000 points per class and with 2 further random seeds at 500 points per class.'], 'R1', 'R1-2d, R1-2j', 'Methods, Land-cover mapping')
E.append(part, P(47), [' To test whether the use of Gaofen-2 pixels affected the result, the HAND and slope limits were also derived from the flooded pixels of the Pléiades product alone, and the analysed area and the flagged area were recomputed with the HAND limit obtained in this way.'], 'R1', 'R1-2a', 'Methods, Terrain and permanent-water masks')
E.replace(part, P(49), 'and not water depth, which was not measured', ['and not water depth or flood severity, neither of which was measured'], 'R1', 'R1-2g', 'Methods, Intensity and persistence classes')
E.append(part, P(49), [' Persistence counts the dates on which a pixel was flagged and is not a measure of how long it was inundated, because the dates were 12 days apart and the state of a pixel between them is unknown.'], 'R1', 'R1-2g', 'Methods, Intensity and persistence classes')
E.replace(part, P(52), 'No confidence intervals or hypothesis tests were calculated.', ['Confidence intervals that allow for spatial autocorrelation were obtained by grouping the pixels of each scoring mask into square blocks of 1 km and resampling whole blocks with replacement 2000 times ', D('10.1214/aos/1176347265'), ', and the 2.5th and 97.5th percentiles of precision, recall, balanced accuracy and kappa over the resamples were taken as the 95% interval. Blocks of 500 m and 2 km were used to check how far the interval depended on block size, and the difference in kappa between the final rule and the fixed thresholds was bootstrapped in the same way. No hypothesis tests were calculated.'], 'R1', 'R1-2e', 'Methods, Reference data and accuracy assessment')
# new paragraphs in Sensitivity analyses, after the rainfall paragraph
p_a = E.new_par_after(part, P(56), NORMAL, ['Sensitivity to the detection thresholds was checked by varying the VV threshold from 3.0 to 5.0 dB and the VH threshold from 1.5 to 3.5 dB, one at a time in steps of 0.5 dB, with the dark-surface exclusion and the minimum cluster size retained. Each setting was scored against the Pléiades mapping on the calibration date and against the Gaofen-2 mapping outside the calibration extent.'], 'R1', 'R1-2c', 'Methods, Sensitivity analyses')
p_b = E.new_par_after(part, p_a, NORMAL, ['To examine the effect of the 2 to 4 day offsets between the optical and radar dates, daily rainfall averaged over the study rectangle was summed between each optical acquisition and the radar date it was compared with. The radar flag was also scored against the 3 optical mappings over the area shared by their analysis extents, so that the same ground was compared on every date, and the change in the flooded reference area between optical dates over that shared area was calculated.'], 'R2', 'R2-4', 'Methods, Sensitivity analyses')
p_c = E.new_par_after(part, p_b, NORMAL, ['To examine whether floodwater raised backscatter in built-up land, the share of pixels with median-filtered ΔVV above +3 dB was calculated for WorldCover built-up pixels inside and outside the UNOSAT flood extent. This was done for the Pléiades and 14 November pair and for the Gaofen-2 and 26 November pair outside the calibration extent, with flooded cropland as a comparison class.'], 'R2', 'R2-5b', 'Methods, Sensitivity analyses')
E.replace(part, P(62), 'No formal sample size calculation was performed.', ['No formal power calculation was performed, and the cap of 500 points per class was judged by the precision it gives.'], 'R1', 'R1-2j', 'Methods, Sample size')
E.replace(part, P(62), 'The cap was a fixed choice and was not tuned or tested for sensitivity.', ['The cap was a fixed choice. The 95% interval of a proportion estimated from 500 points is 0.03 either side at an agreement of 0.90 and 0.04 either side at 0.50, and its effect on the cross-validated agreement was tested with caps of 100, 250 and 1000 points per class.'], 'R1', 'R1-2j', 'Methods, Sample size')
E.insert_after(part, P(62), 'determined by the extents of the UNOSAT products.', [' For the accuracy against UNOSAT, precision was judged from block bootstrap intervals, because the number of independent blocks and not the number of pixels limits it, and no minimum number of blocks was set in advance.'], 'R1', 'R1-2j', 'Methods, Sample size')
E.replace(part, P(64), 'The scripts and output tables are available from the author on reasonable request.', ['The processing scripts, the output tables and the derived flag and land-cover rasters are archived in a public repository on Zenodo with a persistent identifier [Zenodo DOI to be inserted], together with a read-me file that lists the scripts in the order of their numbers and the inputs that each one reads. In outline, the workflow has 4 steps, which are building the land-cover map and the water and terrain masks, calculating the filtered backscatter change against the mean of the 2 pre-event scenes, applying the 2 thresholds with the dark-surface exclusion and the minimum cluster size, and tabulating flagged area by land-cover class.'], 'R1', 'R1-2i, R2-6', 'Methods, Software and reproducibility')
# ------------------------------------------------------------------ RESULTS
E.insert_after(part, P(69), 'Overall agreement with the 373 hold-out points was 0.90', [' (95% confidence interval 0.86 to 0.93)'], 'R1', 'R1-2d', 'Results, Land-cover map and agreement with consensus labels')
E.append(part, P(76), [' The built-up consensus pixels were concentrated in space. Three of the 168 cells of 0.05° held 91.0% of the 107638 built-up consensus pixels and fell in blocks 2, 3 and 4, whereas block 0 held 1014 of them, or 0.94%, which is the share that gives about 5 of 500 points (Table S14).'], 'R2', 'R2-3', 'Results, Reliability of the land-cover map')
E.append(part, P(76), [' The 95% confidence interval of overall agreement was 0.86 to 0.93 for the hold-out and 0.89 to 0.91 for the cross-validation, and that of the built-up producer’s agreement was 0.01 to 0.81 on the 4 hold-out points against 0.77 to 0.84 in the cross-validation (Table S15). Cross-validated overall agreement was 0.89, 0.89, 0.90 and 0.92 with caps of 100, 250, 500 and 1000 points per class, and 0.90, 0.91 and 0.90 for 3 random seeds at 500 points per class (Table S16).'], 'R1', 'R1-2d, R1-2j', 'Results, Reliability of the land-cover map')
E.append(part, P(78), [' The HAND limit derived from the Pléiades flooded pixels alone was 4.7 m and the slope limit was again 8 degrees. With the HAND limit of 4.7 m the analysed area fell from 3692.49 km² to 2863.12 km², whereas the flagged area changed from 225.84 to 222.65 km² on 14 November and from 275.09 to 271.90 km² on 26 November. The flagged share of the analysed area on 14 November was then 28.30% in cropland, 40.66% in built-up land, 1.33% in vegetation or rangeland and 5.01% in bare soil or sand (Table S17).'], 'R1', 'R1-2a, R2-2', 'Results, Study area, exclusions and analysed area')
E.insert_after(part, P(97), 'and 0.56, 0.85, 0.63 and 0.26 for the fixed thresholds.', [' The 95% block bootstrap interval was 0.59 to 0.81 for recall and 0.47 to 0.67 for kappa on the calibration date, and 0.47 to 0.63 for recall, 0.88 to 0.96 for precision and 0.44 to 0.61 for kappa for the Gaofen-2 mapping outside the calibration extent (Table S18). The kappa of the final rule exceeded that of the fixed thresholds by 0.44 (0.37 to 0.51) on the calibration date and by 0.27 (0.18 to 0.35) for the Gaofen-2 mapping outside the calibration extent. The interval widened with block size, and for kappa outside the calibration extent it spanned 0.47 to 0.58 with blocks of 500 m and 0.39 to 0.66 with blocks of 2 km.'], 'R1', 'R1-2e', 'Results, Agreement with UNOSAT optical flood mapping')
p_r1 = E.new_par_after(part, P(105), NORMAL, ['Built-up pixels inside the UNOSAT flood extent showed positive backscatter change more often than the decrease that the rule requires. Among WorldCover built-up pixels inside the flood extent, 22.6% had a median-filtered ΔVV above +3 dB on the Pléiades pair and 20.4% on the Gaofen-2 pair outside the calibration extent, against 14.3% of built-up pixels outside the flood extent on the Pléiades pair (Table S19). The mean ΔVV of the flooded built-up pixels was +1.30 and +1.53 dB, and only 1.4% and 0.7% of them fell by 4 dB or more, whereas flooded cropland had a mean ΔVV of -7.29 and -5.46 dB. The Gaofen-2 comparison group outside the flood extent held only 64 pixels and was not interpreted.'], 'R2', 'R2-5b', 'Results, Agreement with UNOSAT optical flood mapping')
p_r2 = E.new_par_after(part, p_r1, NORMAL, ['Rainfall averaged over the study rectangle was 7.7 mm between the Pléiades acquisition and 14 November, none between the Gaofen-2 acquisition and 26 November and none between 26 and 30 November, whereas 107.8 mm fell between 14 and 23 November, mostly from 15 to 18 November (Figure S3). Over the 42.0 km² shared by the 3 analysis extents, the area mapped as flooded by UNOSAT was 13.9 km² on 12 November, 29.3 km² on 23 November and 31.5 km² on 30 November, of which 13.8 km² of the first was also flooded on 23 November, whereas the radar flagged 13.6 km² on 14 November and 13.3 km² on 26 November (Table S20). Recall over this shared area was 0.70 against the Pléiades mapping, 0.45 against Gaofen-2 and 0.42 against WorldView-2, and precision was 0.72, 0.98 and 0.99.'], 'R2', 'R2-4', 'Results, Agreement with UNOSAT optical flood mapping')
E.append(part, P(115), [' Moving the VV threshold between 3.0 and 5.0 dB changed kappa between 0.574 and 0.580 on the calibration date and between 0.513 and 0.562 for the Gaofen-2 mapping outside the calibration extent, and moving the VH threshold between 1.5 and 3.5 dB changed them between 0.542 and 0.580 and between 0.496 and 0.557. The flagged area over the town raster extent ranged from 43.1 to 47.2 km² across the VV thresholds and from 39.7 to 58.1 km² across the VH thresholds, against 44.6 km² for the calibrated setting (Table S21).'], 'R1', 'R1-2c', 'Results, Sensitivity of the flagged area')
# ------------------------------------------------------------------ DISCUSSION
E.append(part, P(132), [' Two checks bound the reliability of the built-up exposure. The class was mapped consistently against the consensus labels, with cross-validated producer’s and user’s agreement of 0.81 and 0.88, but 38.3% of it lay more than 1 km from any building and radar recall in it was between 0.07 and 0.26, so the flagged built-up area indicates exposure of the floodplain surface and not of settlements.'], 'R1', 'R1-2f', 'Discussion, third paragraph')
E.append(part, P(134), [' In the UNOSAT flood extent, 22.6% of built-up pixels on the Pléiades pair and 20.4% on the Gaofen-2 pair rose by more than 3 dB, against 14.3% outside it on the Pléiades pair. A double-bounce increase was therefore present but affected a minority of flooded built-up pixels. The mean change was positive, at +1.30 and +1.53 dB, so increases and decreases largely offset each other and a rule based on decreases misses these pixels.'], 'R2', 'R2-5b', 'Discussion, fifth paragraph')
E.insert_after(part, P(136), 'a multi-date reference would probably be more stable than a single scene.', [' The mean of the 2 October scenes was retained as the main reference for 3 reasons. It was the setting selected on the calibration date before any independent date was scored, the footprint it gave lay between those of the 2 single-scene references, and it limits the influence of either scene. It also contains the 21 October scene, which followed 40.3 mm of rain in the previous 3 days and was brighter than the 9 October scene by 1.77 dB, so the main totals are likely to carry some effect of that scene and should be read together with Tables 7 and 8.'], 'R2', 'R2-5a', 'Discussion, seventh paragraph')
E.replace(part, P(139), 'and not as measures of flood magnitude', ['and not as measures of flood depth, severity or duration'], 'R1', 'R1-2g', 'Discussion, tenth paragraph')
E.replace(part, P(139), 'Ordinal severity classes built on', ['Ordinal classes built on'], 'R1', 'R1-2g', 'Discussion, tenth paragraph')
E.insert_after(part, P(140), 'because of the spatial block split.', [' This arose because 91.0% of the built-up consensus pixels lay in 3 cells of 0.05° around the town, which fell in blocks 2, 3 and 4, and block 0 held only 0.94% of them, so a random sample of 500 points gave about 5 to block 0. A design that spreads the points of each class evenly over the blocks, or that assigns whole cells to folds so that every fold holds built-up pixels, would give a more representative hold-out for that class. The cross-validation, in which every block was held out once, already gave the more stable estimate, and the classifier behind the map was trained on 496 of the 500 built-up points.'], 'R2', 'R2-3', 'Discussion, eleventh paragraph')
E.append(part, P(140), [' The confidence intervals reported here describe sampling variability within the scored areas, treated as blocks of 1 km, and they do not extend to the 99.37% of the analysed vegetation or rangeland that lay outside every reference extent. Land-cover uncertainty was not propagated into the class totals, which are map areas not corrected for classification error, and with a cross-validated cropland user’s agreement of 0.80 and built-up producer’s agreement of 0.81 the class-level totals carry classification uncertainty in addition to the flood mapping uncertainty.'], 'R1', 'R1-2b, R1-2d', 'Discussion, eleventh paragraph')
p_d = E.new_par_after(part, P(140), NORMAL, ['The 2 to 4 day offsets between the optical and radar dates add uncertainty that these data cannot remove. Recall fell from 0.70 on the calibration date to 0.56 outside the calibration extent, but over the same 42.0 km² footprint it also fell, to 0.45 against Gaofen-2 and 0.42 against WorldView-2, while the area mapped as flooded by UNOSAT more than doubled from 13.9 to 29.3 km² and the radar flagged area stayed near 13.5 km². Rainfall averaged over the study rectangle was 107.8 mm between 14 and 23 November, so expansion of the flooded area before the later optical dates is likely to account for part of the lower recall, with the radar rule missing the added area. The Gaofen-2 image preceded its radar date by 3 days and the WorldView-2 image followed it by 4 days, yet recall outside the calibration extent was 0.56 and 0.55 and 29.1 of the 29.3 km² mapped as flooded on 23 November was still flooded on 30 November, so changes within a few days of the radar date were small. The data cannot separate expansion of the flood from sensor limits as the cause of the lower recall. The band extending further south on 26 November than on 14 November (Figure 3) is consistent with downstream progression of the flood, but the study holds no gauge or discharge record to confirm it.'], 'R2', 'R2-4', 'Discussion, twelfth paragraph')
E.insert_after(part, P(141), 'All of this may flatter the reported agreement.', [' The distinction matters for reading the results. The pre-event reference, filter window and thresholds were fixed a priori on the calibration date, whereas the dark-surface exclusion, the minimum cluster size, the terrain limits and the intensity classes were refinements made after inspection of independent dates, so the agreement on those dates is conditional on them. Deriving the terrain limits from the Pléiades pixels alone gave a HAND limit of 4.7 m and left the flagged area at 222.65 km² on 14 November and 271.90 km² on 26 November, within 1.5% of the main totals.'], 'R1', 'R1-2a, R2-2', 'Discussion, thirteenth paragraph')
E.insert_after(part, P(141), 'need not be the date of peak inundation', [', and rainfall averaged over the study rectangle was concentrated from 15 to 18 November, between the acquisitions of 14 and 26 November, so a crest could have passed between those acquisitions unobserved'], 'R1', 'R1-2h', 'Discussion, thirteenth paragraph')
# ------------------------------------------------------------------ CONCLUSION AND DECLARATIONS
E.append(part, P(145), [' Agreement on the independent dates is conditional, because the thresholds, filter window and pre-event reference were fixed before independent scoring whereas the dark-surface exclusion, the cluster filter and the terrain limits were refined afterwards, and the confidence intervals remained wide, for example 0.47 to 0.63 for recall outside the calibration extent.'], 'R1', 'R1-2a, R1-2e, R2-2', 'Conclusion, first paragraph')
E.append(part, P(146), [' A single orbit with a 12-day repeat could not resolve the flood peak.'], 'R1', 'R1-2h', 'Conclusion, second paragraph')
E.replace(part, P(157), 'The derived flood extents and analysis code are available from the corresponding author on reasonable request', ['The derived flood extents, land-cover map, output tables and analysis code are archived in a public repository on Zenodo [Zenodo DOI to be inserted]'], 'R1', 'R1-2i, R2-6', 'Declarations, Availability of data and materials')

# ------------------------------------------------------------------ TABLES AND FIGURE 5 (reviewer 2 editorial comments)
from docx.oxml import OxmlElement
tabs = d.tables
def table_layout(t, widths, header_rows=1, nowrap_cols=()):
    x = t._tbl; pr = x.tblPr
    for old in pr.findall(q('tblLayout')): pr.remove(old)
    lay = OxmlElement('w:tblLayout'); lay.set(qn('w:type'), 'fixed')
    anchor = pr.find(q('tblBorders'))
    anchor.addnext(lay)
    grid = x.find(q('tblGrid'))
    for g, w in zip(grid.findall(q('gridCol')), widths): g.set(qn('w:w'), str(w))
    for k, tr in enumerate(x.findall(q('tr'))):
        trpr = tr.find(q('trPr'))
        if trpr is None: trpr = OxmlElement('w:trPr'); tr.insert(0, trpr)
        if trpr.find(q('cantSplit')) is None: trpr.append(OxmlElement('w:cantSplit'))
        if k < header_rows and trpr.find(q('tblHeader')) is None: trpr.append(OxmlElement('w:tblHeader'))
        for j, tc in enumerate(tr.findall(q('tc'))):
            tcpr = tc.find(q('tcPr')); tcpr.find(q('tcW')).set(qn('w:w'), str(widths[j]))
            if j in nowrap_cols and k >= header_rows and tcpr.find(q('noWrap')) is None:
                nw = OxmlElement('w:noWrap'); tcpr.find(q('tcW')).addnext(nw)
def cell(t, r, c): return t._tbl.findall(q('tr'))[r].findall(q('tc'))[c]
NB = '\u00a0'; NH = '\u2011'
# Table 1, rainfall period now runs to 8 December
for tr in tabs[0]._tbl.findall(q('tr')):
    for tc in tr.findall(q('tc')):
        if E.ptext(tc) == '15 September to 15 November 2023':
            E.set_cell(part, tc, [['15 September to 8 December 2023']], 'R2', 'R2-4', 'Table 1, rainfall row')
# Table 2, layout and non-breaking text
t2 = tabs[1]; table_layout(t2, [1500, 2400, 2400, 2726])
rows2 = {E.ptext(tr.findall(q('tc'))[0]): tr for tr in t2._tbl.findall(q('tr'))}
def tc2(label, col): return rows2[label].findall(q('tc'))[col]
E.set_cell(part, tc2('VV threshold', 1), [['ΔVV at most ' + NH + '4.0' + NB + 'dB']], 'R2', 'R2-8', 'Table 2, VV threshold row')
E.set_cell(part, tc2('VH threshold', 1), [['ΔVH at most ' + NH + '2.5' + NB + 'dB']], 'R2', 'R2-8', 'Table 2, VH threshold row')
E.set_cell(part, tc2('Dark-surface exclusion', 1), [['Median-filtered pre-event VV below ' + NH + '16' + NB + 'dB excluded']], 'R2', 'R2-8', 'Table 2, dark-surface exclusion row')
E.set_cell(part, tc2('HAND limit', 1), [['At' + NB + 'most' + NB + '10' + NB + 'm']], 'R2', 'R2-8', 'Table 2, HAND limit row')
E.set_cell(part, tc2('Slope limit', 1), [['At' + NB + 'most' + NB + '8' + NB + 'degrees']], 'R2', 'R2-8', 'Table 2, slope limit row')
E.set_cell(part, tc2('Intensity classes', 1), [['Weak, ΔVV above ' + NH + '5' + NB + 'dB'], ['Moderate, ΔVV at most ' + NH + '5' + NB + 'dB and above ' + NH + '7' + NB + 'dB'], ['Strong, ΔVV at most ' + NH + '7' + NB + 'dB']], 'R2', 'R2-8', 'Table 2, intensity classes row')
# Tables 4 and 7, fixed column widths, repeated header rows and cells that do not wrap
table_layout(tabs[3], [1900, 1250, 1469, 1469, 1469, 1469])
for tr in tabs[3]._tbl.findall(q('tr'))[1:]:
    for tc in tr.findall(q('tc'))[2:]:
        a, b = [s.strip() for s in E.ptext(tc).split('/')]
        E.set_cell(part, tc, [[a], [b]], 'R2', 'R2-9', 'Table 4, date columns')
chk(85, 'Note. Each cell')
E.replace(part, P(85), 'and the percentage of the analysed area of the class, separated by a slash', ['and, below it, the percentage of the analysed area of the class'], 'R2', 'R2-9', 'Table 4 note')
table_layout(tabs[6], [1900, 3526, 1800, 1800])
for tr in tabs[6]._tbl.findall(q('tr')):
    tcs = tr.findall(q('tc')); lab = E.ptext(tcs[0])
    if lab.startswith('ΔVV only'):
        E.set_cell(part, tcs[1], [['ΔVV alone with a threshold of ' + NH + '2.5' + NB + 'dB was used']], 'R2', 'R2-9', 'Table 7, ΔVV only rule')
    if lab.startswith('Fixed thresholds'):
        E.set_cell(part, tcs[1], [['The rule was ' + NH + '2.0' + NB + 'dB for VV or ' + NH + '1.5' + NB + 'dB for VH against the 21 October scene, without median filtering and without dark-surface exclusion, with the minimum cluster size retained']], 'R2', 'R2-9', 'Table 7, fixed thresholds row')
E.LOG.append(dict(src='R2', comment='R2-9', location='Tables 4 and 7', kind='layout', old='', new='Fixed column widths, repeated header rows, rows kept whole and no wrapping in numeric cells'))
E.LOG.append(dict(src='R2', comment='R2-8', location='Table 2', kind='layout', old='', new='Fixed column widths, repeated header row and rows kept whole'))
# Figure 5, legend redrawn in a single column so that the last entry is not cut off
newpng = open(os.path.join(B, 'outputs', 'figures', 'png', 'fig12_agreement_map_town_v2.png'), 'rb').read()
import struct
wpx, hpx = struct.unpack('>II', newpng[16:24])
ish = list(d.inline_shapes)[4]; rid = ish._inline.graphic.graphicData.pic.blipFill.blip.embed
d.part.related_parts[rid]._blob = newpng
w_emu = ish.width; ish.height = Emu(int(w_emu * hpx / wpx))
E.LOG.append(dict(src='R2', comment='R2-10', location='Figure 5', kind='figure', old='', new='Legend redrawn in a single column so that the last entry is shown in full'))
d.save(OUT); json.dump(E.LOG, open(os.path.join(B, 'outputs', 'change_log_raw.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False); print('saved', len(E.LOG))






