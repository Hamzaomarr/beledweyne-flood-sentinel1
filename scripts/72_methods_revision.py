import re
P = r'.\scripts\14_make_methods_docx.js'
L = open(P, encoding='utf-8').read().split('\n')
def idx(prefix):
    h = [i for i, l in enumerate(L) if l.startswith(prefix)]; assert len(h) == 1, (prefix, h); return h[0]
def rep(old, new):
    global L
    t = '\n'.join(L); assert t.count(old) == 1, (old, t.count(old)); L = t.replace(old, new).split('\n')
rep("whereas flood area statistics covered the full rectangle.", "whereas flood area statistics covered the analysed area within the full rectangle.")
rep("  ['Copernicus DEM', 'COPERNICUS/DEM/GLO30', 'GLO-30, asset marked as superseded by the platform', 'Slope'],\n", "  ['Copernicus DEM', 'COPERNICUS/DEM/GLO30', 'GLO-30, asset marked as superseded by the platform', 'Slope'],\n  ['CHIRPS daily rainfall', 'Earth Engine collection UCSB-CHG/CHIRPS/DAILY', '15 September to 15 November 2023', 'Rainfall between pre-event scenes'],\n  ['Open Buildings', 'GOOGLE/Research/open-buildings/v3/polygons, confidence of at least 0.7', 'Version 3', 'Independent check of the built-up class'],\n")
rep("missing values set to 0 m.", "missing values set to 0 m, and the number of pixels with missing HAND in the study rectangle was counted before this setting was applied.")
ins = []   # (anchor prefix, list of new lines)
ins.append(("K.push(body(['Points were drawn from the consensus pixels", [
 "K.push(body('The classifier design was also evaluated by spatial block cross-validation. Each of the 5 blocks was held out in turn, the classifier was retrained on the other 4 blocks with the same settings, and the error matrices of the 5 folds were summed. This evaluation did not change the map, which came from the classifier trained once on all blocks except block 0. The error matrix of the held-out block 0 and the number of points per class and block were also tabulated.'));",
 "K.push(body(['Agreement with consensus labels does not test the built-up class against independent data, so the map was also compared with the centroids of building footprints from Open Buildings version 3 ', D('10.48550/arXiv.2107.12283'), ' with a model confidence of at least 0.7. Each centroid was assigned the class of the 10 m pixel that contained it, and the distance from every mapped pixel to the nearest centroid was calculated. Building footprints are modelled from satellite imagery, are not field observations and may omit buildings. For each date, flagged area in built-up pixels was tabulated by distance to the nearest building centroid, and the number of buildings whose centroid pixel, or any pixel within 1 pixel, was flagged was counted.']));"]))
ins.append(("K.push(body('The calibrated rule, without the minimum cluster size", [
 "K.push(body('To examine what the minimum cluster size removed, flagged pixels in clusters smaller than the minimum were compared with the UNOSAT flood extent within each scoring mask, in total and in cluster size classes of 1 to 9, 10 to 49 and 50 to 99 pixels, and the flagged area removed from the full-area flag on 14 November was tabulated by land-cover class.'));"]))
ins.append(("K.push(body('The calibrated rule was compared with a fixed-threshold rule", [
 "K.push(body('The area and land-cover composition of each scoring mask were calculated from the final land-cover map, and the share of the analysed area of each class that lay inside any reference extent was calculated from the union of the three analysis extents.'));"]))
ins.append(("K.push(body('The effect of the evaluation grid was checked", [
 "K.push(body(['To examine why the two October reference scenes gave different totals, the mean backscatter of the scenes of 9 October, 21 October, 2 November and 14 November was calculated on a 100 m grid by averaging 10 by 10 pixels of 10 m in dB, and the differences between dates were summarised by land-cover class, weighting each 100 m cell by the fraction of it occupied by analysed pixels of that class. The flagged area obtained with each October reference was compared by class and in space. Daily rainfall averaged over the study rectangle came from CHIRPS ', D('10.1038/sdata.2015.66'), ' and was summed between the dates of the scenes and over the 3 days before each scene. Three alternative pre-event references, the scene of 2 November alone, the mean of 21 October and 2 November, and the mean of the three scenes, were scored against the UNOSAT mapping in the town with the same rule and cluster filter as the main configuration.']));"]))
ins.append(("K.push(body('Area was the number of pixels multiplied by 100", [
 "K.push(body('Four areas were kept apart. The study area was the whole rectangle, the excluded area was the sum of the area classed as permanent water and the area outside the HAND and slope limits, the analysed area was the remainder, and the flagged area was the part of the analysed area that met the flood rule.'));"]))
for pre, new in ins:
    i = idx(pre); L[i + 1:i + 1] = new
open(P, 'w', encoding='utf-8', newline='').write('\n'.join(L)); print('ok')
