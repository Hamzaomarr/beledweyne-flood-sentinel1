"""Two-pass edit, leftovers in the Methods generator found by the scan after the first run."""
import re, docx
B = r'.'
p = B + r'\scripts\14_make_methods_docx.js'; t = open(p, encoding='utf-8').read()
for a, b in [('acquired on one calendar day', 'acquired on 1 calendar day'), ('calibrated on one reference date only', 'calibrated on 1 reference date only'), ('on all six dates', 'on all 6 dates'), ('which share one grid', 'which share 1 grid')]:
    assert t.count(a) == 1, (a, t.count(a)); t = t.replace(a, b)
open(p, 'w', encoding='utf-8', newline='').write(t)
d = docx.Document(B + r'\MANUSCRIPT_full.docx'); txt = '\n'.join(q.text for q in d.paragraphs)
for ph in ('United Nations Satellite Centre', 'height above nearest drainage', 'vertical transmit and vertical receive', 'vertical transmit and horizontal receive', 'European Space Agency', 'European Petroleum', 'Climate Hazards'):
    print(ph, [(m.start(), txt[max(0, m.start() - 40):m.start() + 30].replace('\n', ' ')) for m in re.finditer(ph, txt)])
