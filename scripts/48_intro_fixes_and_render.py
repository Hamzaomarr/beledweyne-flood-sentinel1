"""Final corrections to the Introduction text after matching each statement to its abstract, then a check of the mechanical requirements."""
import re, os
B = r'.'
p = os.path.join(B, 'introduction_source.txt'); t = open(p, encoding='utf-8').read()
def rep(a, b):
    global t
    assert t.count(a) == 1, (t.count(a), a[:80]); t = t.replace(a, b)
rep("with overall accuracies above 94% at validated test sites", "with overall accuracies of at least 94% at validated test sites")
rep("Reviews conclude that automation and robustness have largely been achieved", "A review concludes that automation and robustness have largely been achieved")
rep("and open land-cover products allow exposure to be summarised by class where field data are lacking.", "and open land-cover products offer a way to summarise exposure by class where field data are lacking.")
if len(re.findall(r'\bSAR\b', re.sub(r'synthetic aperture radar, SAR,', '', t))) == 0:
    rep("synthetic aperture radar, SAR, provides", "synthetic aperture radar provides"); print('SAR abbreviation removed, it was not used again')
open(p, 'w', encoding='utf-8', newline='').write(t); print('introduction corrected')
