"""Two-pass edit, part 1. Source files and the Methods generator. Number words become numerals, abbreviations are defined once in the comma form, repeated definitions in table notes are removed,
the title loses its colon and terminology is made consistent. Every replacement must match exactly once."""
import os
B = r'.'
def edit(path, pairs):
    t = open(path, encoding='utf-8').read()
    for a, b in pairs:
        assert t.count(a) == 1, (os.path.basename(path), a[:70], t.count(a)); t = t.replace(a, b)
    open(path, 'w', encoding='utf-8', newline='').write(t)
edit(B + r'\abstract_source.txt', [
 ('TITLE=Mapping the 2023 Deyr flood in Beledweyne, Somalia, using Sentinel-1: Optical validation and sensitivity of flood extent estimates', 'TITLE=Optical validation and sensitivity of Sentinel-1 flood extent estimates for the 2023 Deyr flood in Beledweyne, Somalia'),
 ('calibrated on one town', 'calibrated on 1 town'), ('images from six dates', 'images from 6 dates'), ('calibrated on one date against', 'calibrated on 1 date against'), ('tested on two later maps', 'tested on 2 later maps'),
 ('Reference mapping covered 0.63% of analysed rangeland.', 'Reference mapping covered 0.63% of the analysed vegetation or rangeland.')])
edit(B + r'\introduction_source.txt', [
 ('at two test sites', 'at 2 test sites'), ('where one multi-frequency radar study', 'where 1 multi-frequency radar study'), ('optical mapping of one town', 'optical mapping of 1 town'),
 ('The United Nations Satellite Centre produced optical flood mapping', 'The United Nations Satellite Centre, UNOSAT, produced optical flood mapping')])
edit(B + r'\discussion_source.txt', [
 ('as found in one Chinese catchment', 'as found in 1 Chinese catchment'), ('obtained with the three references were nested', 'obtained with the 3 references were nested'),
 ('A mean of three scenes behaved much like the main reference, so adding one scene did not settle', 'A mean of 3 scenes behaved much like the main reference, so adding 1 scene did not settle'),
 ('acquired two to four days away', 'acquired 2 to 4 days away'), ('The three products together covered', 'The 3 products together covered'), ('about two thirds of the analysed area', 'about 66% of the analysed area'),
 ('where two existing products agreed', 'where 2 existing products agreed'), ('that two land-cover products both labelled', 'that 2 land-cover products both labelled'), ('across all three later dates', 'across all 3 later dates'),
 ('two later refinements', '2 later refinements'), ('was calibrated on one date', 'was calibrated on 1 date'), ('from the two October reference scenes', 'from the 2 October reference scenes'), ('in place of two scenes', 'in place of 2 scenes'),
 ('produced by the United Nations Satellite Centre for calibration', 'produced by UNOSAT for calibration'), ('in vertical transmit and vertical receive polarisation automatically', 'in VV polarisation automatically'),
 ('masks based on height above nearest drainage and slope', 'masks based on HAND and slope'), ('conditional on analytic choices', 'conditional on analyst choices')])
edit(B + r'\conclusion_source.txt', [('depend on analytical choices', 'depend on analyst choices')])
edit(B + r'\scripts\74_discussion_revision.py', [('(Table 6)', '(Table 6)')]) if False else None
# Methods generator
edit(B + r'\scripts\14_make_methods_docx.js', [
 ('from the United Nations Satellite Centre, hereafter UNOSAT, and tabulation', 'from UNOSAT and tabulation'),
 ('zone 38N projection, EPSG code 32638.', 'zone 38N projection with European Petroleum Survey Group code 32638.'),
 ('drainage, hereafter HAND, was 10 m or less', 'drainage, HAND, was 10 m or less'),
 ('receive polarisation, termed VV, and in vertical transmit and horizontal receive polarisation, termed VH.', 'receive polarisation, VV, and in vertical transmit and horizontal receive polarisation, VH.'),
 ('Six dates were used. The scenes of 9 October', 'The analysis used 6 dates. The scenes of 9 October'),
 ('Three acquisitions covering Beledweyne were used, a Pléiades image', 'The reference mapping used 3 acquisitions covering Beledweyne, a Pléiades image'),
 ('The attribute dates of two layers', 'The attribute dates of 2 layers'), ('the six Sentinel-1 dates were exported at 10 m resolution in the EPSG code 32638 projection', 'the 6 Sentinel-1 dates were exported at 10 m resolution in the projection with code 32638'),
 ('Reference labels were derived from two existing products. The classes of ESA WorldCover 2021', 'Reference labels were derived from 2 existing products. The classes of WorldCover 2021'),
 ('were recoded to five, with tree cover', 'were recoded to 5, with tree cover'), ('where the two recoded products agreed', 'where the 2 recoded products agreed'),
 ('Eight predictors were used, namely reflectance in bands B2, B3, B4, B8 and B11 and three spectral indices.', 'The model used 8 predictors, namely reflectance in bands B2, B3, B4, B8 and B11 and 3 spectral indices.'),
 ('trained on the eight predictors', 'trained on the 8 predictors'),
 ('difference images, termed ΔVV and ΔVH, were smoothed', 'difference images, ΔVV and ΔVH, were smoothed'),
 ('belonged to an eight-connected cluster', 'belonged to an 8-connected cluster'), ('by eight-connected labelling', 'by 8-connected labelling'),
 ('The grid search covered three pre-event references', 'The grid search covered 3 pre-event references'), ('their mean, three window sizes of 1, 3 and 5 pixels', 'their mean, 3 window sizes of 1, 3 and 5 pixels'),
 ('in two 10 km rangeland boxes, in each of which', 'in 2 rangeland boxes of 10 km by 10 km, in each of which'), ('on one fixed grid in 64 tiles', 'on 1 fixed grid in 64 tiles'),
 ('assigned to three intensity classes', 'assigned to 3 intensity classes'), ('for the two independent dates results were calculated', 'for the 2 independent dates results were calculated'),
 ('from the union of the three analysis extents', 'from the union of the 3 analysis extents'), ('recomputed under seven alternative configurations', 'recomputed under 7 alternative configurations'),
 ('To examine why the two October reference scenes', 'To examine why the 2 October reference scenes'), ('came from CHIRPS ', 'came from the Climate Hazards Group InfraRed Precipitation with Station data '),
 ("Three alternative pre-event references, the scene of 2 November alone, the mean of 21 October and 2 November, and the mean of the three scenes, were scored against the UNOSAT mapping in the town with the same rule and cluster filter as the main configuration.",
  "The analysis also scored 3 alternative pre-event references, the scene of 2 November alone, the mean of 21 October and 2 November, and the mean of the 3 scenes, against the UNOSAT mapping in the town with the same rule and cluster filter as the main configuration."),
 ('for a 10 m pixel in the EPSG code 32638 projection', 'for a 10 m pixel in the projection with code 32638'), ('Four areas were kept apart.', 'The analysis kept 4 areas apart.'),
 ('assessed on two other dates', 'assessed on 2 other dates'), ('fitted on one date', 'fitted on 1 date'), ('Only one Sentinel-1 orbit', 'Only 1 Sentinel-1 orbit'),
 ("'Six dates from 9 October to 8 December 2023'", "'6 dates from 9 October to 8 December 2023'"), ("['ESA WorldCover',", "['European Space Agency WorldCover',"), ("['Copernicus DEM',", "['Copernicus digital elevation model',"),
 ("['CHIRPS daily rainfall',", "['Climate Hazards Group InfraRed Precipitation with Station data daily rainfall',"), ("'Eight-connected clusters of at least 100 flagged pixels'", "'8-connected clusters of at least 100 flagged pixels'"),
 ("K.push(note('Note. HAND, height above nearest drainage. UNOSAT, United Nations Satellite Centre. DEM, digital elevation model.'));\n", ''),
 ("K.push(note('Note. VV, vertical transmit and vertical receive polarisation. VH, vertical transmit and horizontal receive polarisation. ΔVV and ΔVH, post-event minus pre-event backscatter in dB. HAND, height above nearest drainage. UNOSAT, United Nations Satellite Centre.'));\n", '')])
print('part 1 done')
