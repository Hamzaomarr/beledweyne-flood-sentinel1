"""Fixes from the Introduction fact-check. Each edit reflects a statement that its source did not fully support, or a gap claim that was too broad or dated."""
import re, os
B = r'.'
p = os.path.join(B, 'introduction_source.txt'); t = open(p, encoding='utf-8').read()
def rep(a, b):
    global t
    assert t.count(a) == 1, (t.count(a), a[:90]); t = t.replace(a, b)
rep("and a 20% rise in the proportion of the world population living in places that had previously been inundated, as settlement spread into floodplains", "and a 20% rise in the proportion of the population exposed to floods, as people settled in locations where satellites had previously observed inundation")
rep("with overall accuracies of at least 94% at validated test sites", "with overall accuracies of at least 94% at two test sites on the border between Greece and Turkey")
rep("remain much harder to detect", "remain less reliably detected")
rep("so automated methods calibrate to local conditions", "so some automated methods calibrate to local conditions")
rep("yet most published algorithms were presented on a single test case, comparisons between methods are rare, and a comparison across flood events and lakes in the United Kingdom and Ireland found that accuracy and robustness differed between methods", "yet a 2018 assessment noted that most published algorithms had been presented on a single test case and that comparisons between methods were rare, and its own comparison across flood events and lakes in the United Kingdom and Ireland found that accuracy and robustness differed between methods")
rep("Independent reference data are scarce in remote African basins, where one multi-frequency radar study", "Independent reference data can be scarce in remote African basins, where one multi-frequency radar study")
rep("What is less clear is how far a detection rule", "What is less clear for a data-scarce setting like Beledweyne is how far a detection rule")
rep("and open land-cover products offer a way to summarise exposure by class where field data are lacking.", "and open land-cover products were available for summarising exposure by class where field data are lacking.")
rep("would give planners in flood-prone basins a more candid basis for exposure estimates than a single footprint, and it would show which parts", "could give planners in flood-prone basins a more candid basis for exposure estimates than a single footprint, and it could show which parts")
open(p, 'w', encoding='utf-8', newline='').write(t)
plain = re.sub(r'<<[^>]+>>', '', t); print('introduction fixes applied | words', len(plain.split()))
