"""Add 10.1007/s44274-026-00937-4 to the Introduction. To stay within 12 unique DOIs, the Westerhoff 2013 citation is dropped and its clause merged into the Landuyt statement."""
import re, os
B = r'.'
p = os.path.join(B, 'introduction_source.txt'); t = open(p, encoding='utf-8').read()
def rep(a, b):
    global t
    assert t.count(a) == 1, (t.count(a), a[:90]); t = t.replace(a, b)
NEW = '10.1007/s44274-026-00937-4'
rep("Flooding affects more people than any other environmental hazard, and the number of people living where floods occur is large and still growing <<10.1038/s41586-021-03695-w;10.1038/s41467-022-30727-4;10.1038/s41467-025-56654-8>>.",
    "Flooding affects more people than any other environmental hazard, the number of people living where floods occur is large and still growing, and the toll of water-related hazards keeps rising where adaptive capacity is limited <<10.1038/s41586-021-03695-w;10.1038/s41467-022-30727-4;10.1038/s41467-025-56654-8;" + NEW + ">>.")
rep("Backscatter thresholds depend on the surface and on the radar geometry, so some automated methods calibrate to local conditions, and the best method has been shown to depend on the area studied and the intended use <<10.5194/hess-17-651-2013;10.1109/TGRS.2018.2860054>>. ", "")
rep("and its own comparison across flood events and lakes in the United Kingdom and Ireland found that accuracy and robustness differed between methods <<10.1109/TGRS.2018.2860054>>.",
    "and its own comparison across flood events and lakes in the United Kingdom and Ireland found that accuracy and robustness differed between methods and that the most suitable method depended on the area studied and the intended use <<10.1109/TGRS.2018.2860054>>.")
rep("These questions matter because estimates of exposure are used to prioritise flood adaptation and mitigation, so the reliability of a local radar-derived estimate has practical consequences <<10.1038/s41467-022-30727-4;10.1038/s41586-021-03695-w>>.",
    "These questions matter because estimates of exposure are used to prioritise flood adaptation, early warning and mitigation, so the reliability of a local radar-derived estimate has practical consequences <<10.1038/s41467-022-30727-4;10.1038/s41586-021-03695-w;" + NEW + ">>.")
open(p, 'w', encoding='utf-8', newline='').write(t)
g = re.findall(r'<<([^>]+)>>', t); d = [x for s in g for x in s.split(';')]; plain = re.sub(r'<<[^>]+>>', '', t)
print('unique DOIs', len(set(x.lower() for x in d)), '| per statement', [len(s.split(';')) for s in g], '| words', len(plain.split()), '| Westerhoff still present:', 'hess-17-651' in t)
