"""Adds the revision analyses to outputs/results_blocks.json, then renumbers all Results tables in order of appearance. New text takes every number from the CSV and JSON files written by scripts 64 to 70."""
import json, re, os, numpy as np, pandas as pd, rasterio
from scipy import ndimage as ndi
from pyproj import Transformer
B = r'.'; T = os.path.join(B, 'outputs', 'tables'); DG = os.path.join(B, 'data', 'processed', 'diag')
blocks = json.load(open(os.path.join(B, 'outputs', 'results_blocks_before_revision.json'), encoding='utf-8'))
C = lambda n: pd.read_csv(os.path.join(T, n)); J = lambda n: json.load(open(os.path.join(T, n), encoding='utf-8'))
f2 = lambda x: '%.2f' % x; f1 = lambda x: '%.1f' % x; n0 = lambda x: '%d' % round(x)
# ---- mapped built-up distance to buildings (mapped built-up, not only analysed)
with rasterio.open(os.path.join(B, 'data', 'processed', 'raw10m', 'lulc.tif')) as s: lulc = s.read(1).astype('uint8'); tr = s.transform
H, W = lulc.shape; xy = np.load(os.path.join(DG, 'open_buildings_centroids.npy')); tf = Transformer.from_crs('EPSG:4326', 'EPSG:32638', always_xy=True); X, Y = tf.transform(xy[:, 0], xy[:, 1])
c = ((np.array(X) - tr.c) / 10).astype(int); r = ((tr.f - np.array(Y)) / 10).astype(int); ok = (r >= 0) & (r < H) & (c >= 0) & (c < W); bm = np.zeros((H, W), bool); bm[r[ok], c[ok]] = True
d = ndi.distance_transform_edt(~bm) * 10; b = lulc == 3; p100 = 100 * (d[b] <= 100).mean(); p1k = 100 * (d[b] > 1000).mean(); km1k = (d[b] > 1000).sum() * 1e-4
# ---- tables of numbers
cnt = J('revision_lulc_sample_counts.json'); acc = J('lulc_accuracy_vs_consensus.json'); cv = J('revision_lulc_blockcv.json'); ob = J('revision_builtup_open_buildings.json')
cls = ['Water', 'Cropland', 'Vegetation or rangeland', 'Built-up', 'Bare soil or sand']; K_ = ['0', '1', '2', '3', '4']
cm = np.array(acc['confusion']).astype(int)
bud = C('revision_area_budget.csv'); bcl = C('revision_area_budget_by_class.csv'); hm = J('revision_hand_missing.json')
cov = C('revision_validation_coverage.csv'); cvc = C('revision_validation_coverage_by_class.csv')
crm = C('revision_cluster_removed_vs_reference.csv'); crc = C('revision_cluster_removed_by_class.csv')
oc = C('revision_pre_event_scene_by_class.csv'); bs = C('revision_pre_event_scene_backscatter.csv'); ch = C('revision_chirps_rainfall.csv').set_index('interval').chirps_mm_area_mean; alt = C('revision_alternative_pre_event_references_town.csv')
bd = C('revision_builtup_by_building_distance.csv'); bt = C('revision_buildings_in_flagged_area.csv').set_index('item')
def tab(key, title, header, rows, widths, note=None): return dict(t='tab', key=key, title=title, header=header, rows=rows, widths=widths, **({'note': note} if note else {}))
def hh(x): return dict(t='h', x=x)
def pp(x): return dict(t='p', x=x)
new = {}
# 1. land-cover reliability
tr_c = [cnt['train'][k] for k in K_]; te_c = [cnt['test'][k] for k in K_]
new['lc'] = [hh('Reliability of the land-cover map'),
 pp("The stratified sample drew 500 points for each class. The spatial block split placed %d, %d, %d, %d and %d points in training and %d, %d, %d, %d and %d in the hold-out for water, cropland, vegetation or rangeland, built-up land and bare soil or sand in that order (Table {T:sample}). Nearly all built-up points lay in blocks assigned to training, so the built-up values in Table 4 rest on 4 points. Of these, 1 was mapped as built-up and 3 as vegetation or rangeland, and 12 cropland hold-out points were mapped as built-up, which gives the producer's and user's agreement of 0.25 and 0.06 (Table {T:cm}). When each block was held out in turn, agreement with the consensus labels over %d points was %s overall with kappa %s, and the producer's and user's agreement for built-up land were %s and %s on 500 points (Table {T:sample}). All of these values measure agreement with labels on which WorldCover and Dynamic World agreed and not accuracy against field observation." % (*tr_c, *te_c, cv['n'], f2(cv['OA']), f2(cv['kappa']), f2(cv['producers'][3]), f2(cv['users'][3]))),
 tab('sample', 'Sample distribution and agreement with reference labels by class', ['Class', 'Training points', 'Hold-out points', 'Hold-out producer\'s agreement', 'Hold-out user\'s agreement', 'Cross-validation producer\'s agreement', 'Cross-validation user\'s agreement'],
     [[cls[i], str(tr_c[i]), str(te_c[i]), f2(acc['producers'][i]), f2(acc['users'][i]), f2(cv['producers'][i]), f2(cv['users'][i])] for i in range(5)] + [['All classes', str(sum(tr_c)), str(sum(te_c)), '', '', '', '']], [2100, 1050, 1050, 1200, 1200, 1250, 1176],
     'Note. Hold-out refers to spatial block 0 and cross-validation to the 5 spatial blocks held out in turn, with 500 points per class. Agreement is with labels where two existing land-cover products gave the same class.'),
 tab('cm', 'Error matrix of the held-out points', ['Reference class'] + cls + ['Total'], [[cls[i]] + [str(v) for v in cm[i]] + [str(cm[i].sum())] for i in range(5)] + [['Total'] + [str(v) for v in cm.sum(0)] + [str(cm.sum())]], [2000, 900, 1100, 1500, 1000, 1300, 1226],
     'Note. Rows are reference labels and columns are mapped classes for the 373 hold-out points.')]
# 2. area accounting
ar = bud.set_index('item'); tot = ar.loc['Study area (rectangle)', 'km2']; pw = ar.loc['Excluded as permanent water']; te = ar.loc['Excluded by HAND or slope limits (outside permanent water)']; el = ar.loc['Eligible analysed area']
bc = bcl.set_index('class')
new['area'] = [hh('Study area, exclusions and analysed area'),
 pp("Of the %s km² of the study area, %s km² or %s%% was excluded as permanent water and %s km² or %s%% by the HAND and slope limits outside permanent water, which left an analysed area of %s km² or %s%% (Table {T:area}). The terrain limits removed %s km² of vegetation or rangeland, %s km² of bare soil or sand, %s km² of cropland and %s km² of built-up land. Flagged areas and class shares in the later sections refer to the analysed area. No pixel of the study rectangle had a missing HAND value, so setting missing values to 0 m changed no pixel, and the MERIT Hydro grid held %d pixels with a HAND of exactly 0 m inside the rectangle, all of them valid observations." % (f2(tot), f2(pw.km2), f2(pw.pct_of_study_area), f2(te.km2), f2(te.pct_of_study_area), f2(el.km2), f2(el.pct_of_study_area), f2(bc.loc['Vegetation or rangeland', 'terrain_excluded_km2']), f2(bc.loc['Bare soil or sand', 'terrain_excluded_km2']), f2(bc.loc['Cropland', 'terrain_excluded_km2']), f2(bc.loc['Built-up', 'terrain_excluded_km2']), 65656)),
 tab('area', 'Study area, excluded area and analysed area by land-cover class', ['Class', 'Mapped area, km²', 'Permanent water excluded, km²', 'Terrain excluded, km²', 'Analysed area, km²'],
     [[k, f2(bc.loc[k, 'mapped_km2']), f2(bc.loc[k, 'perm_water_excluded_km2']), f2(bc.loc[k, 'terrain_excluded_km2']), f2(bc.loc[k, 'analysed_km2'])] for k in cls] + [['All classes', f2(tot), f2(pw.km2), f2(te.km2), f2(el.km2)]], [2500, 1650, 1800, 1650, 1426],
     'Note. Terrain excluded is the area outside the HAND and slope limits that was not permanent water. HAND, height above nearest drainage.')]
# 3. buildings
sh = ob['share_in_class']; n_b = ob['n_buildings']; nr = ob['pct_of_class_pixels_within_m_of_a_building']; bdi = bd.set_index('group'); g_in, g_mid, g_far, g_all = bd.group.tolist()
bti = lambda k: int(bt.loc[k, 'count']); btp = lambda k: bt.loc[k, 'pct_of_analysed_area_buildings']
new['bld'] = [hh('Built-up land and building footprints'),
 pp("Of %d building centroids from Open Buildings, %s%% fell in pixels mapped as built-up, %s%% in vegetation or rangeland, %s%% in bare soil or sand, %s%% in cropland and %s%% in water (Table {T:ob}). In the other direction, %s%% of the mapped built-up area lay within 100 m of a building centroid, and %s%% of it, or %s km², lay more than 1 km from any centroid." % (n_b, f1(sh['Built-up']), f1(sh['Vegetation or rangeland']), f2(sh['Bare soil or sand']), f2(sh['Cropland']), f2(sh['Water']), f1(p100), f1(p1k), f1(km1k))),
 tab('ob', 'Building centroids and mapped land-cover class', ['Mapped class', 'Building centroids', 'Share of centroids, %', 'Pixels within 100 m of a centroid, %'],
     [[k, str(ob['counts'][k]), f2(sh[k]), f2(nr[k]['100'])] for k in cls] + [['All classes', str(n_b), '100.00', '']], [2900, 1900, 2000, 2226], 'Note. Open Buildings version 3 centroids with a model confidence of at least 0.7.'),
 pp("Within the analysed area, built-up pixels within 100 m of a building had a flagged share of %s%% on 14 November and %s%% on 26 November, against %s%% and %s%% at 100 to 500 m and %s%% and %s%% beyond 500 m (Table {T:bd}). Of the %s km² of built-up land flagged on 14 November, %s km² lay more than 500 m from a building centroid. Of the %d buildings in the analysed area, %d or %s%% had a flagged centroid pixel on 14 November, %d or %s%% on 26 November and %d or %s%% on 8 December, and 1195 were flagged on all 3 dates. Counting a flagged pixel within 1 pixel gave %d, %d and %d buildings, or %s%%, %s%% and %s%%." % (
   f2(bdi.loc[g_in, 'share14_pct']), f2(bdi.loc[g_in, 'share26_pct']), f2(bdi.loc[g_mid, 'share14_pct']), f2(bdi.loc[g_mid, 'share26_pct']), f2(bdi.loc[g_far, 'share14_pct']), f2(bdi.loc[g_far, 'share26_pct']), f2(bdi.loc[g_all, 'flagged14_km2']), f2(bdi.loc[g_far, 'flagged14_km2']),
   bti('Buildings in the analysed area'), bti('Buildings with centroid pixel flagged on 14Nov'), f2(btp('Buildings with centroid pixel flagged on 14Nov')), bti('Buildings with centroid pixel flagged on 26Nov'), f2(btp('Buildings with centroid pixel flagged on 26Nov')), bti('Buildings with centroid pixel flagged on 8Dec'), f2(btp('Buildings with centroid pixel flagged on 8Dec')),
   bti('Buildings with a flagged pixel within 1 pixel on 14Nov'), bti('Buildings with a flagged pixel within 1 pixel on 26Nov'), bti('Buildings with a flagged pixel within 1 pixel on 8Dec'), f2(btp('Buildings with a flagged pixel within 1 pixel on 14Nov')), f2(btp('Buildings with a flagged pixel within 1 pixel on 26Nov')), f2(btp('Buildings with a flagged pixel within 1 pixel on 8Dec')))),
 tab('bd', 'Flagged area in built-up pixels by distance to the nearest building centroid', ['Built-up pixels', 'Analysed area, km²', 'Flagged 14 November, km²', 'Flagged 26 November, km²', 'Share 14 November, %', 'Share 26 November, %'],
     [[g.replace('Built-up pixels ', '').replace('All built-up pixels in the analysed area', 'All built-up pixels'), f2(bdi.loc[g, 'analysed_km2']), f2(bdi.loc[g, 'flagged14_km2']), f2(bdi.loc[g, 'flagged26_km2']), f2(bdi.loc[g, 'share14_pct']), f2(bdi.loc[g, 'share26_pct'])] for g in bd.group], [2400, 1250, 1350, 1350, 1250, 1126],
     'Note. Distance is to the nearest Open Buildings version 3 centroid with a model confidence of at least 0.7.')]
# 4. coverage
cv_ = cov.set_index('mask'); mnames = cov['mask'].tolist(); u = cv_.loc['Union of all three products']; cvc_ = cvc.set_index('class')
sh_in = {m: cv_.loc[m, 'pct_inside_analysed_area'] for m in mnames}
new['cov'] = [hh('Coverage of the reference mapping'),
 pp("The calibration scoring mask covered %s km², and the Gaofen-2 and WorldView-2 analysis extents each covered %s km², of which %s km² lay outside the calibration extent (Table {T:cov}). Together the three products covered %s km², or %s%% of the study area, and %s%% of the union lay inside the analysed area. The union held %s km² of cropland, %s km² of built-up land, %s km² of bare soil or sand, %s km² of vegetation or rangeland and %s km² of water. The part of it inside the analysed area was %s%% of the analysed cropland, %s%% of the analysed built-up land, %s%% of the analysed bare soil or sand and %s%% of the analysed vegetation or rangeland, so %s%% of the analysed vegetation or rangeland, which made up %s%% of the analysed area, lay outside every reference extent." % (
   f2(cv_.loc[mnames[0], 'area_km2']), f2(cv_.loc[mnames[1], 'area_km2']), f2(cv_.loc[mnames[2], 'area_km2']), f2(u.area_km2), f2(u.pct_of_study_area), f2(u.pct_inside_analysed_area), f2(u['km2_Cropland']), f2(u['km2_Built-up']), f2(u['km2_Bare soil or sand']), f2(u['km2_Vegetation or rangeland']), f2(u['km2_Water']),
   f2(cvc_.loc['Cropland', 'pct_of_analysed_inside_extent']), f2(cvc_.loc['Built-up', 'pct_of_analysed_inside_extent']), f2(cvc_.loc['Bare soil or sand', 'pct_of_analysed_inside_extent']), f2(cvc_.loc['Vegetation or rangeland', 'pct_of_analysed_inside_extent']), f2(100 - cvc_.loc['Vegetation or rangeland', 'pct_of_analysed_inside_extent']), f2(100 * 2438.28 / 3692.49))),
 tab('cov', 'Area and land-cover composition of the reference masks', ['Mask', 'Area, km²', 'Share of study area, %', 'Cropland, km²', 'Vegetation or rangeland, km²', 'Built-up, km²', 'Bare soil or sand, km²', 'Water, km²'],
     [[m.replace('Pleiades', 'Pléiades').replace('Calibration, ', 'Calibration scoring mask, ').replace(' scoring mask scoring mask', ' scoring mask'), f2(cv_.loc[m, 'area_km2']), f2(cv_.loc[m, 'pct_of_study_area']), f2(cv_.loc[m, 'km2_Cropland']), f2(cv_.loc[m, 'km2_Vegetation or rangeland']), f2(cv_.loc[m, 'km2_Built-up']), f2(cv_.loc[m, 'km2_Bare soil or sand']), f2(cv_.loc[m, 'km2_Water'])] for m in mnames], [2400, 850, 1000, 950, 1150, 900, 950, 826],
     'Note. Land-cover composition is from the final map. The calibration scoring mask is the Pléiades mask used for calibration.')]
# 5. cluster filter
cr = crm.set_index('reference'); rn = crm.reference.tolist(); rc_ = crc.set_index('class')
sizes = lambda r_, a: (f2(cr.loc[r_, 'km2_%s' % a]), f2(cr.loc[r_, 'flooded_share_%s' % a]))
new['clu'] = [hh('What the cluster filter removed'),
 pp("Within the scoring masks, the filter removed %s km² of flagged area on the calibration date and %s km² on each independent date outside the calibration extent (Table {T:rm1}). Of the removed pixels, %s%%, %s%% and %s%% lay inside the UNOSAT flood extent, against %s%%, %s%% and %s%% of the retained pixels and %s%%, %s%% and %s%% of the whole scoring mask, so the removed pixels were flooded less often than the mask as a whole but not never. They held %s, %s and %s km² of mapped flood, which was %s%%, %s%% and %s%% of the flooded reference area. By cluster size, the flooded share of flagged pixels in clusters of 1 to 9, 10 to 49 and 50 to 99 pixels was %s, %s and %s on the calibration date and %s, %s and %s for the Gaofen-2 mapping outside the calibration extent (Table {T:rm2})." % (
   f2(cr.loc[rn[0], 'removed_km2']), f2(cr.loc[rn[1], 'removed_km2']), f1(100 * cr.loc[rn[0], 'removed_share_flooded']), f1(100 * cr.loc[rn[1], 'removed_share_flooded']), f1(100 * cr.loc[rn[2], 'removed_share_flooded']),
   f1(100 * cr.loc[rn[0], 'kept_share_flooded']), f1(100 * cr.loc[rn[1], 'kept_share_flooded']), f1(100 * cr.loc[rn[2], 'kept_share_flooded']), f1(100 * cr.loc[rn[0], 'reference_prevalence']), f1(100 * cr.loc[rn[1], 'reference_prevalence']), f1(100 * cr.loc[rn[2], 'reference_prevalence']),
   f2(cr.loc[rn[0], 'removed_flooded_km2']), f2(cr.loc[rn[1], 'removed_flooded_km2']), f2(cr.loc[rn[2], 'removed_flooded_km2']), f1(100 * cr.loc[rn[0], 'recall_lost_points']), f1(100 * cr.loc[rn[1], 'recall_lost_points']), f1(100 * cr.loc[rn[2], 'recall_lost_points']),
   sizes(rn[0], '1_9')[1], sizes(rn[0], '10_49')[1], sizes(rn[0], '50_99')[1], sizes(rn[1], '1_9')[1], sizes(rn[1], '10_49')[1], sizes(rn[1], '50_99')[1])),
 tab('rm1', 'Flagged pixels removed by the minimum cluster size within the scoring masks', ['Reference', 'Removed, km²', 'Removed pixels flooded, %', 'Retained pixels flooded, %', 'Mask flooded, %', 'Flooded area removed, km²', 'Reference flood removed, %'],
     [[m.replace('Pleiades', 'Pléiades'), f2(cr.loc[m, 'removed_km2']), f1(100 * cr.loc[m, 'removed_share_flooded']), f1(100 * cr.loc[m, 'kept_share_flooded']), f1(100 * cr.loc[m, 'reference_prevalence']), f2(cr.loc[m, 'removed_flooded_km2']), f1(100 * cr.loc[m, 'recall_lost_points'])] for m in rn], [2500, 900, 1150, 1150, 900, 1200, 1226],
     'Note. Flooded means inside the UNOSAT flood extent. The independent dates are scored outside the calibration extent.'),
 tab('rm2', 'Flooded share of flagged pixels by cluster size removed', ['Reference', '1 to 9 pixels, km²', 'Flooded share', '10 to 49 pixels, km²', 'Flooded share', '50 to 99 pixels, km²', 'Flooded share'],
     [[m.replace('Pleiades', 'Pléiades')] + [v for a in ('1_9', '10_49', '50_99') for v in sizes(m, a)] for m in rn], [2500, 1100, 900, 1150, 900, 1150, 1226], 'Note. Flooded share is the proportion of the flagged pixels in the size class that lay inside the UNOSAT flood extent.'),
 pp("Over the full area, the filter removed %s km² of the %s km² flagged on 14 November without it, which was %s%%, and of this %s km² lay in vegetation or rangeland, %s km² in bare soil or sand, %s km² in cropland and %s km² in built-up land (Table {T:rm3}). The removed share of the unfiltered flagged area was %s%% in vegetation or rangeland, %s%% in bare soil or sand, %s%% in cropland and %s%% in built-up land." % (
   f2(rc_.loc['All classes', 'removed_km2']), f2(rc_.loc['All classes', 'unfiltered_km2']), f1(rc_.loc['All classes', 'removed_pct_of_unfiltered']), f2(rc_.loc['Vegetation or rangeland', 'removed_km2']), f2(rc_.loc['Bare soil or sand', 'removed_km2']), f2(rc_.loc['Cropland', 'removed_km2']), f2(rc_.loc['Built-up', 'removed_km2']),
   f1(rc_.loc['Vegetation or rangeland', 'removed_pct_of_unfiltered']), f1(rc_.loc['Bare soil or sand', 'removed_pct_of_unfiltered']), f1(rc_.loc['Cropland', 'removed_pct_of_unfiltered']), f1(rc_.loc['Built-up', 'removed_pct_of_unfiltered']))),
 tab('rm3', 'Flagged area on 14 November removed by the minimum cluster size, by land-cover class', ['Class', 'Without cluster filter, km²', 'With cluster filter, km²', 'Removed, km²', 'Removed share, %'],
     [[k, f2(rc_.loc[k, 'unfiltered_km2']), f2(rc_.loc[k, 'filtered_km2']), f2(rc_.loc[k, 'removed_km2']), f1(rc_.loc[k, 'removed_pct_of_unfiltered'])] for k in ['Cropland', 'Vegetation or rangeland', 'Built-up', 'Bare soil or sand', 'All classes']], [2700, 1700, 1700, 1500, 1426], 'Note. Values are within the analysed area.')]
# 6. pre-event scenes
oc_ = oc.set_index('class'); bsv = bs[bs.polarisation == 'VV'].set_index(['difference', 'class']); bsh = bs[bs.polarisation == 'VH'].set_index(['difference', 'class'])
d1, d2, d3 = '21 Oct minus 9 Oct', '2 Nov minus 9 Oct', '2 Nov minus 21 Oct'; al = alt.set_index('reference'); rn_ = alt.reference.tolist()
new['pre'] = [hh('Pre-event reference scenes'),
 pp("The flagged areas obtained with the three references were nested. Of the area flagged with the 9 October reference, 96.4%% lay inside the main footprint, and 96.5%% of the main footprint lay inside the area flagged with the 21 October reference. The %s km² flagged with the 21 October reference and not in the main footprint lay mostly in vegetation or rangeland at %s km² or %s%%, followed by bare soil or sand at %s km², cropland at %s km² and built-up land at %s km² (Table {T:pc}). Their locations are shown in Figure 7. The flagged share of the analysed vegetation or rangeland was %s%% with the 9 October reference, %s%% with the mean and %s%% with the 21 October reference." % (
   f2(oc_.loc['All classes', 'pre21_not_main_km2']), f2(oc_.loc['Vegetation or rangeland', 'pre21_not_main_km2']), f1(oc_.loc['Vegetation or rangeland', 'pre21_extra_share_of_total_extra_pct']), f2(oc_.loc['Bare soil or sand', 'pre21_not_main_km2']), f2(oc_.loc['Cropland', 'pre21_not_main_km2']), f2(oc_.loc['Built-up', 'pre21_not_main_km2']),
   f2(oc_.loc['Vegetation or rangeland', 'pre9_pct_of_analysed']), f2(oc_.loc['Vegetation or rangeland', 'main_pct_of_analysed']), f2(oc_.loc['Vegetation or rangeland', 'pre21_pct_of_analysed']))),
 tab('pc', 'Flagged area on 14 November with each October reference, by land-cover class', ['Class', 'Analysed area, km²', '9 October only, km²', 'Mean of both, km²', '21 October only, km²', 'Added by 21 October, km²', '21 October share, %'],
     [[k, f2(oc_.loc[k, 'analysed_km2']), f2(oc_.loc[k, 'pre9_km2']), f2(oc_.loc[k, 'main_km2']), f2(oc_.loc[k, 'pre21_km2']), f2(oc_.loc[k, 'pre21_not_main_km2']), f2(oc_.loc[k, 'pre21_pct_of_analysed'])] for k in ['Cropland', 'Vegetation or rangeland', 'Built-up', 'Bare soil or sand', 'All classes']], [2300, 1050, 1100, 1100, 1100, 1250, 1126],
     'Note. Added by 21 October is the flagged area with the 21 October reference that was not in the main footprint. All values are with the cluster filter.'),
 dict(t='fig', key='fig7', file=os.path.join(B, 'outputs', 'figures', 'fig13_preevent_scene_difference.png'), w=440, h=238, label='Figure 7.', title='Mean change in VV backscatter from 9 October to 21 October on a 100 m grid, panel a, and share of each 100 m cell flagged on 14 November only with the 21 October reference, panel b, with the outline of the main footprint'),
 pp("In VV, the 21 October scene was brighter than the 9 October scene by %s dB on average over the analysed area, by %s dB in vegetation or rangeland and by %s dB in cropland, and %s%% of the 100 m cells were more than 2 dB brighter (Table {T:bs}). The 2 November scene was brighter than 9 October by %s dB and differed from 21 October by %s dB. In VH the 21 October scene was brighter than 9 October by %s dB and 2 November differed from 21 October by %s dB. Rainfall averaged over the study rectangle was %s mm from 15 September to 9 October, %s mm from 10 to 21 October, %s mm from 22 October to 2 November and %s mm from 3 to 14 November, and it was %s, %s, %s and %s mm in the 3 days before 9 October, 21 October, 2 November and 14 November." % (
   f2(bsv.loc[(d1, 'All analysed'), 'mean_dB']), f2(bsv.loc[(d1, 'Vegetation or rangeland'), 'mean_dB']), f2(bsv.loc[(d1, 'Cropland'), 'mean_dB']), f2(bsv.loc[(d1, 'All analysed'), 'pct_cells_above_plus2dB']), f2(bsv.loc[(d2, 'All analysed'), 'mean_dB']), f2(bsv.loc[(d3, 'All analysed'), 'mean_dB']),
   f2(bsh.loc[(d1, 'All analysed'), 'mean_dB']), f2(bsh.loc[(d3, 'All analysed'), 'mean_dB']), f1(ch['15 Sep to 9 Oct']), f1(ch['10 Oct to 21 Oct']), f1(ch['22 Oct to 2 Nov']), f1(ch['3 Nov to 14 Nov']), f1(ch['3 days to 9 Oct']), f1(ch['3 days to 21 Oct']), f1(ch['3 days to 2 Nov']), f1(ch['3 days to 14 Nov']))),
 tab('bs', 'Mean change in VV backscatter between scenes by land-cover class', ['Class', '21 October minus 9 October, dB', '2 November minus 9 October, dB', '2 November minus 21 October, dB', 'Cells above 2 dB for 21 October minus 9 October, %'],
     [[k, f2(bsv.loc[(d1, k), 'mean_dB']), f2(bsv.loc[(d2, k), 'mean_dB']), f2(bsv.loc[(d3, k), 'mean_dB']), f2(bsv.loc[(d1, k), 'pct_cells_above_plus2dB'])] for k in ['Cropland', 'Vegetation or rangeland', 'Built-up', 'Bare soil or sand', 'All analysed']], [2300, 1700, 1700, 1700, 1626],
     'Note. Values are means of 100 m cells weighted by the fraction of each cell occupied by analysed pixels of the class. Positive values mean a brighter later scene.'),
 pp("In the town, the main reference gave kappa of %s on the calibration date and %s and %s on the Gaofen-2 and WorldView-2 mappings outside the calibration extent. The 9 October scene alone gave %s, %s and %s, the 21 October scene alone %s, %s and %s, the 2 November scene alone %s, %s and %s, the mean of 21 October and 2 November %s, %s and %s, and the mean of all three scenes %s, %s and %s (Table {T:alt})." % tuple(f2(al.loc[x, col]) for x in ['Mean of 9 and 21 October (main)', '9 October only', '21 October only', '2 November only', 'Mean of 21 October and 2 November', 'Mean of 9 October, 21 October and 2 November'] for col in ['kappa_cal', 'kappa_GF2', 'kappa_WV2'])),
 tab('alt', 'Agreement of alternative pre-event references with UNOSAT mapping in the town', ['Pre-event reference', 'Flagged area, km²', 'Precision', 'Recall', 'Kappa', 'Kappa Gaofen-2', 'Kappa WorldView-2'],
     [[x, f2(al.loc[x, 'flagged_km2_calibration_mask']), f2(al.loc[x, 'prec_cal']), f2(al.loc[x, 'rec_cal']), f2(al.loc[x, 'kappa_cal']), f2(al.loc[x, 'kappa_GF2']), f2(al.loc[x, 'kappa_WV2'])] for x in rn_], [3000, 900, 1000, 850, 850, 1200, 1226],
     'Note. Flagged area, precision, recall and kappa are for the calibration scoring mask. The Gaofen-2 and WorldView-2 values are kappa outside the calibration extent. All rows use the same thresholds, window, dark-surface exclusion and cluster filter.')]
# ---- insert
def pos(label): return [i for i, x in enumerate(blocks) if x['t'] == 'tab' and x.get('label') == label][0]
order = [('Table 13.', 'pre'), ('Table 12.', 'clu'), ('Table 9.', 'cov'), ('Table 6.', 'bld'), ('Table 4.', 'area'), ('Table 4.', 'lc')]   # insert from the end; same anchor inserted twice stacks lc before area
for lab, k in order:
    i = pos(lab); blocks[i + 1:i + 1] = new[k]
# keys for old tables and figures
for x in blocks:
    if x['t'] == 'tab' and 'key' not in x: x['key'] = 'o' + re.match(r'Table (\d+)', x['label']).group(1)
# table 4 note
for x in blocks:
    if x['t'] == 'tab' and x['key'] == 'o4': x['note'] += ' Only 4 hold-out points were built-up.'
# number tables in order of appearance, starting at 4
mapping = {}; n = 4
for x in blocks:
    if x['t'] == 'tab': mapping[x['key']] = n; x['label'] = 'Table %d.' % n; n += 1
def fix(s):
    s = re.sub(r'Table (\d+)(?!\d)', lambda m: ('Table %d' % mapping['o' + m.group(1)]) if 4 <= int(m.group(1)) <= 14 and m.group(0) not in () else m.group(0), s) if False else s
    return s
old_to_new = {int(k[1:]): v for k, v in mapping.items() if re.fullmatch(r'o\d+', k)}
def renum(s):
    def sub(m):
        a = int(m.group(1)); return 'Table %d' % old_to_new[a] if a in old_to_new else m.group(0)
    return re.sub(r'Table (\d+)', sub, s)
for x in blocks:
    if x['t'] == 'p' and '{T:' not in x['x']: x['x'] = renum(x['x'])
    if x['t'] in ('p',) and '{T:' in x['x']:
        # new paragraphs: first resolve placeholders, then leave literal references such as Table 4 untouched
        x['x'] = re.sub(r'\{T:(\w+)\}', lambda m: str(mapping[m.group(1)]), x['x'])
    if x['t'] == 'tab' and x.get('note'): x['note'] = renum(x['note']) if not x['key'].startswith('o') else renum(x['note'])
for x in blocks: x.pop('key', None) if x['t'] == 'tab' else None
json.dump(blocks, open(os.path.join(B, 'outputs', 'results_blocks.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(old_to_new, open(os.path.join(B, 'outputs', 'table_renumbering.json'), 'w')); print('old to new table numbers', old_to_new); print('blocks', len(blocks))
