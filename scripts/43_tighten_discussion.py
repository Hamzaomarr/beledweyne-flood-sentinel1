"""Make every empirical statement in the Discussion match what the Results report."""
p = r'.\discussion_source.txt'
t = open(p, encoding='utf-8').read()
def rep(a, b):
    global t
    assert t.count(a) == 1, (t.count(a), a[:80]); t = t.replace(a, b)
rep("but agreement was best in cropland and weakest in built-up land and on bare surfaces, with tree and shrub cover in between (Table 9).", "but recall was generally highest in cropland and lowest in built-up land and on bare surfaces, with grassland, shrubland and tree cover in between (Table 9).")
rep("flagged an implausibly large area, whereas thresholds fitted", "flagged a far larger area, whereas thresholds fitted")
rep("The minimum cluster size used here served that second purpose and removed the scattered flags that otherwise dominated rangeland.", "The minimum cluster size used here served that second purpose, since small scattered clusters made up most of the flagged pixels in the rangeland boxes that were inspected.")
rep("The flooded share of the optical reference rose with both the size of the backscatter fall and the number of dates on which a pixel was flagged, which supports", "The flooded share of the optical reference was higher for larger backscatter falls and for pixels flagged on more dates, which supports")
rep("and the contrast between the town, where flooded pixels were common, and the surrounding rangeland, where they were rare, is the situation in which prevalence matters most.", "and the contrast between a flooded town and the surrounding rangeland, where the radar flagged little, is the situation in which prevalence matters most.")
rep("Because flooded pixels were common in the validated area and rare elsewhere, accuracy figures from the town cannot be carried over to the full-area totals.", "Because the validated area is a flooded town and most of the study area is rangeland where the radar flagged little, accuracy figures from the town cannot be carried over to the full-area totals.")
open(p, 'w', encoding='utf-8', newline='').write(t); print('discussion tightened')
