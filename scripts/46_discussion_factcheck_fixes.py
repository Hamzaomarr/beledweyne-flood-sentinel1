"""Fixes from the Discussion fact-check. Each edit reflects a claim that its cited abstract or the Results did not fully support."""
p = r'.\discussion_source.txt'
t = open(p, encoding='utf-8').read()
def rep(a, b):
    global t
    assert t.count(a) == 1, (t.count(a), a[:90]); t = t.replace(a, b)
rep("and reviews of synthetic aperture radar flood mapping identify vegetated and urban areas as where severe limitations remain", "and a review of synthetic aperture radar flood mapping identifies vegetated and urban areas as where severe limitations remain")
rep("A dark-surface exclusion, the simple counterpart of the sand exclusion layers developed there, changed the footprint very little,", "Excluding surfaces that were already dark before the event changed the footprint very little,")
rep("monthly and orbit-related differences have been found to exceed the contrast produced by inundation, and not every", "monthly and orbit-related differences can exceed the contrast produced by inundation, as found in one Chinese catchment, and not every")
rep("A reference scene that differs from later conditions through surface wetness or crop state would therefore inflate or deflate the flagged area,", "A reference scene that differs from later conditions through crop state or other monthly change could therefore inflate or deflate the flagged area,")
rep("flagged a far larger area, whereas thresholds fitted to local optical mapping did not,", "flagged a far larger area at much lower precision, whereas thresholds fitted to local optical mapping did not,")
rep("The minimum cluster size used here served that second purpose,", "A cluster filter served that second purpose here,")
rep("changed the footprint little, which may reflect the flat floodplain setting, whereas in the complex terrain", "changed the footprint little, which means that almost no flagged area lay on steep or elevated ground, whereas in the complex terrain")
rep("Reporting precision, recall, balanced accuracy and kappa together avoids a single verdict, and the contrast between a flooded town and the surrounding rangeland, where the radar flagged little, is the situation in which prevalence matters most.", "Reporting several metrics rather than one matters for that reason, and the contrast between a flooded town and the surrounding rangeland, where the radar flagged little, is a case in which prevalence is likely to matter.")
rep("Reviews of radar flood mapping likewise call for quantitative metrics and high-quality reference data <<10.3390/rs16040656>>.", "A review of radar flood mapping likewise calls for quantitative metrics and high-quality reference data <<10.3390/rs16040656;10.1371/journal.pone.0291908>>.")
rep("have precedent in floodplain indicator frameworks <<10.1016/j.ecolind.2026.115591>>.", "have precedent in a floodplain indicator framework <<10.1016/j.ecolind.2026.115591>>.")
rep("and it should not be extended to settlements elsewhere.", "and it should not be extended to settlements elsewhere. The later date of largest flagged area, and the large share of flagged cropland and built-up area that persisted across all three later dates, suggest a prolonged inundation along the corridor rather than a brief pulse, although the radar revisit leaves the timing of the crest open.")
rep("would also reduce the dependence on the pre-event scene", "may also reduce the dependence on the pre-event scene")
rep("The main contribution of the study is a documented and reproducible radar workflow", "The main contribution of the study is a documented radar workflow")
rep("The flood footprint is credible where inundation was extensive and open, the ordering of land-cover exposure is informative for the river corridor,", "The flood footprint appears credible where inundation was extensive and open, the ordering of land-cover exposure is a useful first description of the river corridor,")
open(p, 'w', encoding='utf-8', newline='').write(t); print('discussion fixes applied')
