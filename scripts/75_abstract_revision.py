p = r'.\abstract_source.txt'
L = open(p, encoding='utf-8').read().strip().split('\n')
new = {
 'Background': "In data-scarce settings it is unclear how far a radar flood rule calibrated on one town can be carried across a floodplain, and how strongly exposure estimates depend on analyst choices.",
 'Methods': "Sentinel-1 radar images from six dates between October and December 2023 mapped the Deyr season flood around Beledweyne, Somalia. A change rule was calibrated on one date against United Nations Satellite Centre optical flood mapping, tested on two later optical maps outside the calibration area, and applied within a 3692.49 km² analysed area of the 4780.81 km² study area. Flagged area was summed by land cover class and checked against building footprints, with sensitivity analyses of the pre-event reference and filtering.",
 'Results': "Flagged area was 225.84 km² on 14 November and 275.09 km² on 26 November. Cropland held the largest flagged area on 14 November at 92.15 km², and built-up land the highest share at 40.37%, but most built-up area lay more than 500 m from any building. Against Gaofen-2 mapping outside the calibration area, precision was 0.92, recall 0.56 and kappa 0.53, against 0.27 for fixed thresholds. Reference mapping covered 0.63% of analysed rangeland. Flagged area ranged from 185.1 to 573.8 km² across the October scenes and was 396.4 km² without cluster filtering against 225.8 km² with it.",
 'Conclusion': "A locally calibrated radar rule appears credible where inundation was extensive, but recall was limited, accuracy beyond the town is untested, built-up exposure is indicative, and totals depended on the pre-event scene and filtering. Exposure estimates should be reported with their sensitivity."}
out = []
for l in L:
    k = l.split('|')[0]; out.append(k + '|' + new[k] if k in new else l)
open(p, 'w', encoding='utf-8', newline='').write('\n'.join(out) + '\n'); print(sum(len(v.split()) for v in new.values()), {k: len(v.split()) for k, v in new.items()})
